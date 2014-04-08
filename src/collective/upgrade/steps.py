import logging
import re

import transaction

from Acquisition import aq_base, aq_parent
from Products.PluginIndexes.FieldIndex import FieldIndex
from Products.ZCatalog.ProgressHandler import ZLogHandler

from Products.CMFCore.utils import getToolByName

from plone.uuid import interfaces as uuid_ifaces
from Products.Archetypes import interfaces as at_ifaces

from collective.upgrade import utils

logger = logging.getLogger('collective.upgrade.steps')

_default_layers = []


def catalogReindex(context):
    catalog = getToolByName(context, 'portal_catalog')
    pgthreshold = catalog._getProgressThreshold()
    handler = (pgthreshold > 0) and ZLogHandler(pgthreshold) or None
    catalog.refreshCatalog(clear=1, pghandler=handler)


def deleteCustomSkinObjs(context, *obj_ids):
    skins = getToolByName(context, 'portal_skins')
    del_ids = [obj_id for obj_id in obj_ids
               if obj_id in skins.custom]
    if not del_ids:
        return

    skins.custom.manage_delObjects(del_ids)
    logger.info(
        'Deleted custom skin objects from %r: %r'
        % (skins.custom, del_ids))


def cleanupSkinLayers(context, remove_layers=_default_layers):
    skins = getToolByName(context, 'portal_skins')
    for theme in skins.getSkinSelections():
        path = skins.getSkinPath(theme)
        layers = path.split(',')
        found = []
        for layer in layers:
            if layer in remove_layers:
                continue
            if hasattr(skins, layer):
                found.append(layer)
                continue
            if remove_layers is not _default_layers:
                raise ValueError(
                    '%r theme layer %r is missing but not listed to be removed'
                    % (theme, layer))

        diff = list(set(layers).difference(found))
        if diff:
            logger.info('Removing layers from theme %r for %r: %r'
                        % (theme, skins, diff))
            skins.addSkinSelection(theme, ','.join(found), test=1)


def uninstallAddOns(context, addons=None):
    """
    Uninstall the given add-ons using the cleanest method possible.

    If no add-ons are specified then all missing add-ons are
    uninstalled.
    """
    qi = getToolByName(context, 'portal_quickinstaller')
    for product in qi.listInstallableProducts(skipInstalled=False):
        addon = product['id']
        if addons is not None:
            if addon not in addons:
                continue
        elif qi.isProductInstallable(addon):
            continue

        qi._getOb(addon).locked = False
        install_profiles = qi.getInstallProfiles(addon)
        uninstall_profiles = [profile for profile in install_profiles
                              if profile.split(':', 1) == 'uninstall']
        setup = getToolByName(context, 'portal_setup')
        if uninstall_profiles:
            profile = uninstall_profiles[0]
            logger.info(
                'Uninstalling the %r add-on for %r using the %r profile'
                % (addon, setup, profile))
            setup.runAllImportStepsFromProfile('profile-%s' % profile)
            qi.manage_delObjects([addon])
        else:
            logger.info('Uninstalling the %r add-on for %r' % (addon, qi))
            qi.uninstallProducts([addon])

        for profile in install_profiles:
            version = setup.getLastVersionForProfile(profile)
            if version == 'unknown':
                # Not installed, no need to remove
                continue
            logger.info('Clearing the %r profile version %r for %r' %
                        (profile, version, setup))
            del setup._profile_upgrade_versions[profile]
            setup._p_changed = True

        assert not qi.isProductInstalled(addon)


class CMFEditionsUpgrader(utils.Upgrader):

    def upgrade(self):
        self.storage = getToolByName(
            self.context, 'portal_historiesstorage', None)
        if self.storage is None:
            self.log('No portal_historiesstorage tool found, '
                     'skipping CMFEditions cleanup')
            return

        from Products.CMFEditions.interfaces.IArchivist import (
            IVersionAwareReference)
        self.reference_iface = IVersionAwareReference

        update_catalogs = getattr(self, 'update_catalogs', None)
        try:
            self.update_catalogs = False
            self.walkVersionObjects()
        finally:
            if update_catalogs is None:
                del self.update_catalogs
            else:
                self.update_catalogs = update_catalogs

    def walkVersionObjects(self):
        repo = self.storage._getZVCRepo()
        self.log('Begin cleaning up CMFEditions objects in %r' % self.storage)
        for history_id in repo._histories:
            history = repo.getVersionHistory(history_id)
            for branch in history.objectValues():
                for version_id in branch.versionIds():
                    version = history.getVersionById(version_id)
                    obj = version._data.getWrappedObject().object
                    self.recurse(obj)

    def recurse(self, obj):
        self.upgradeObj(obj)
        if hasattr(aq_base(obj), 'objectValues'):
            for subobj in obj.objectValues():
                if self.reference_iface.providedBy(subobj):
                    continue
                self.recurse(subobj)


class CMFEditionsFolderMigrator(CMFEditionsUpgrader):

    def upgrade(self):
        from Products.BTreeFolder2.BTreeFolder2 import (
            BTreeFolder2Base as BTreeFolder)
        from plone.app.folder.migration import BTreeMigrationView
        self.folder_class = BTreeFolder
        self.folder_migrator = BTreeMigrationView(self.context, None)

        super(CMFEditionsFolderMigrator, self).upgrade()

    def upgradeObj(self, obj):
        if isinstance(obj, self.folder_class):
            self.folder_migrator.migrate(obj)


def migrateCMFEditionsFolderVersions(context):
    upgrader = CMFEditionsFolderMigrator(context)
    upgrader.upgrade()


copy_id_re = re.compile(r'^copy[0-9]*_of_.*')


def origKey(obj):
    """
    The object is assumed to be the original if:

    - it was created first
    - or it doesn't have an id starting with 'copy_of_'
    - or it has the shortest path
    """
    return (obj.created(),
            copy_id_re.match(obj.getId()),
            len(obj.getPhysicalPath()))


def fixDuplicateUIDs(context):
    """
    Fix duplidate UIDs.

    Try to make an intelligent guess as to which object is the
    original and should keep the UID.  Missing objects are removed
    from the catalog and new UIDs are generated for the rest of the
    objects with the same UID.
    """
    catalog = getToolByName(context, 'portal_catalog')
    ref_catalog = getToolByName(context, 'reference_catalog')
    uid_index = catalog.Indexes._getOb('UID', None)
    if not isinstance(uid_index, FieldIndex.FieldIndex):
        return
    for uid, rids in list(uid_index._index.iteritems()):
        if isinstance(rids, int) or len(rids) <= 1:
            continue

        objs = []
        for rid in list(rids):
            path = catalog.getpath(rid)
            obj = context.unrestrictedTraverse(path, None)
            if obj is None:
                logger.info(
                    'Removing missing object %r from %r' % (path, catalog))
                catalog.uncatalog_object(path)
                continue
            objs.append(obj)
        if not objs:
            continue

        orig = min(objs, key=origKey)
        logger.info('Multiple objects found for UID %r, '
                    'assuming %r is the original' % (uid, orig))
        for obj in objs:
            if aq_base(obj) is aq_base(orig):
                continue
            new_uid = ref_catalog._getUUIDFor(obj)
            obj.reindexObject(idxs=['UID'])
            logger.info('Assigned new UID %r to %r' % (new_uid, obj))


def setDefaultEditor(context, wanted_editor='', dry_run=False):
    """Use the deault editor for all users."""
    from collective.setdefaulteditor.utils import set_editor_for_all
    # Assumes the zope.component.hooks site has already been set
    set_editor_for_all(wanted_editor, dry_run)


class ReferenceTargetCleaner(utils.Upgrader):
    """Walk through all the reference objects and remove those whose
    targets can't be found."""

    def upgrade(self):
        self.ref_catalog = getToolByName(self.context, 'reference_catalog')
        self.context.ZopeFindAndApply(
            self.context, search_sub=1, apply_func=self.upgradeObj)

    def upgradeObj(self, obj, path=None):
        if not at_ifaces.IReferenceable.providedBy(obj):
            return
        for ref in self.ref_catalog.getReferences(obj):
            if ref.getTargetObject() is None:
                ref_id = uuid_ifaces.IUUID(ref)
                self.log('Removing reference %r with missing target: %r'
                         % (ref_id, ref))
                aq_parent(ref)._delOb(ref_id)


def cleanupMissingReferenceTargets(context):
    url = getToolByName(context, 'portal_url')
    upgrader = ReferenceTargetCleaner(url.getPortalObject())
    upgrader.upgrade()


def pack_zodb(context, t=None, days=0):
    """
    Pack the database after upgrades to conserve disk space.
    """
    utils.transaction_note(
        context, note='Committing changes prior to packing the ZODB')
    transaction.commit()
    db = context._p_jar.db()
    db.pack(t, days)
