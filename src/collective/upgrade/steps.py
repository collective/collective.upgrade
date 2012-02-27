import logging
import re

from Acquisition import aq_base
from Products.PluginIndexes.FieldIndex import FieldIndex

from Products.CMFCore.utils import getToolByName

from collective.upgrade import utils

logger = logging.getLogger('collective.upgrade.steps')


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


def uninstallAddOns(context, addons=None):
    """
    Uninstall the given add-ons using the cleanest method possible.

    If no add-ons are specified then all missing add-ons are
    uninstalled.
    """
    qi = getToolByName(context, 'portal_quickinstaller')
    for product in qi.listInstalledProducts():
        addon = product['id']
        if addons is not None and addon not in addons:
            continue
        elif qi.isProductInstallable(addon):
            continue
        
        qi._getOb(addon).locked = False
        uninstall_profiles = [
            profile for profile in qi.getInstallProfiles(addon)
            if profile.split(':', 1) == 'uninstall']
        if uninstall_profiles:
            profile = uninstall_profiles[0]
            setup = getToolByName(context, 'portal_setup')
            logger.info(
                'Uninstalling the %r add-on for %r using the %r profile'
                % (addon, qi, profile))
            setup.runAllImportStepsFromProfile('profile-%s' % profile)
            qi.manage_delObjects([addon])
        else:
            qi.uninstallProducts([addon])
        assert not qi.isProductInstalled(addon)


class CMFEditionsUpgrader(utils.Upgrader):

    def upgrade(self):
        self.storage = getToolByName(
            self.context, 'portal_historiesstorage', None)
        if self.storage is None:
            self.log('No portal_historiesstorage tool found, '
                     'skipping CMFEditions cleanup')
            return

        from Products.CMFEditions.interfaces.IArchivist import IVersionAwareReference
        self.reference_iface = IVersionAwareReference

        for obj in self.walkVersionObjects():
            self.recurse(obj)

    def walkVersionObjects(self):
        repo = self.storage._getZVCRepo()
        self.log('Begin cleaning up CMFEditions objects in %r' % self.storage)
        for history_id in repo._histories:
            history = repo.getVersionHistory(history_id)
            self.log('Processing history %r' % history)
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
        from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base as BTreeFolder
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
    for uid, rids in uid_index._index.iteritems():
        if isinstance(rids, int) or len(rids) <= 1:
            continue

        objs = []
        for rid in rids:
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
