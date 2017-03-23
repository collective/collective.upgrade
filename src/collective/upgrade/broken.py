# encoding: utf-8

from zope import interface
from zope import component

from ZODB import broken
from ZODB import interfaces as zodb_ifaces

from Acquisition import aq_base, aq_parent
from Products.ZCatalog import ZCatalog

from Products.GenericSetup import utils
from Products.CMFCore.utils import getToolByName

from collective.upgrade import steps


def cleanupBrokenComponents(context):
    """Delete component registrations from missing add-ons."""
    portal = getToolByName(context, 'portal_url').getPortalObject()
    sm = component.getSiteManager(context=portal)
    for reg in list(sm.registeredUtilities()):
        if not isinstance(reg.component, broken.Broken):
            continue

        steps.logger.info('Unregistering broken utility %r in %r' %
                          (reg, portal))
        sm.unregisterUtility(
            component=reg.component, provided=reg.provided,
            name=reg.name)


def cleanupBrokenSetupRegistrations(context):
    """Delete portal_setup registrations from missing add-ons."""
    setup = getToolByName(context, 'portal_setup')
    required = setup.getToolsetRegistry()._required
    for id_, tool in required.items():
        if utils._resolveDottedName(tool['class']) is None:
            steps.logger.info(
                'Unregistering missing required tool %r in %r' % (tool, setup))
            required.pop(id_)
            setup._p_changed = True

    for info in setup.listProfileInfo():
        profile_id = 'profile-' + info['id']
        # Update a broken import step depdendency in the
        # persisent registry which has been fixed in the
        # profile import_steps.xml
        steps.logger.info(
            'Applying profile context %r in %r' % (profile_id, setup))
        setup.applyContextById(profile_id)


class Empty(object):
    pass


def cleanupBrokenTextIndexes(context):
    catalog = getToolByName(context, 'portal_catalog')
    for id_ in catalog.indexes():
        index = catalog._catalog.getIndex(id_)
        if (
                not isinstance(index, broken.Broken) or
                'TextIndex' not in index.__class__.__name__):
            continue

        steps.logger.info('Replacing %r text index in %r' % (index, catalog))
        catalog.manage_delIndex(id_)
        extras = Empty()
        extras.index_type = 'Okapi BM25 Rank'
        extras.lexicon_id = 'plone_lexicon'
        catalog.addIndex(id_, 'ZCTextIndex', extras)


class CleanupBrokenObjects(steps.CMFEditionsUpgrader):

    catalog_ids = ('portal_catalog', 'uid_catalog', 'reference_catalog')
    update_catalogs = True

    def upgrade(self):
        self.upgradeObjects()

        # Cleanup broken CMFEditions versions
        super(CleanupBrokenObjects, self).upgrade()

    def upgradeObjects(self):
        # Clear the catalogs before walking the objects.  Objects will
        # be indexed in the catalogs after being cleaned.
        for zcatalog_id in self.catalog_ids:
            zcatalog = getToolByName(self.context, zcatalog_id, None)
            if zcatalog is not None:
                self.log('Clearing the %r catalog' % zcatalog)
                zcatalog.manage_catalogClear()
            else:
                self.log(
                    'Could not find the %r catalog, skipping.' % zcatalog_id)

        # Some broken objects may be transforms which require special handling
        self.trans_tool = getToolByName(
            self.context, 'portal_transforms', None)

        # Walk all the portal objects fixing problems which might
        # stop the upgrades.
        self.log('Begin cleaning up objects in %r' % self.context)
        self.context.ZopeFindAndApply(
            self.context, search_sub=1, apply_func=self.upgradeObj)

        # There should be no more broken interfaces
        catalog = getToolByName(self.context, 'portal_catalog')
        assert len(catalog(
            object_provides=zodb_ifaces.IBroken.__identifier__)) == 0

    def upgradeObj(self, obj, path=None):
        obj._p_activate()

        if self.delRemovedObj(obj, path):
            # Deleted don't do anything else
            return

        if '__implements__' in obj.__dict__:
            self.log('Deleting __implements__ instance attributre from %r'
                     % obj)
            del obj.__dict__['__implements__']
            obj._p_changed = True

        if zodb_ifaces.IBroken.providedBy(obj):
            self.log('Removing broken interfaces from %r: %r' %
                     (obj, list(interface.directlyProvidedBy(obj))))
            interface.noLongerProvides(obj, zodb_ifaces.IBroken)

        if not self.update_catalogs:
            return
        base = aq_base(obj)

        if (
                not isinstance(obj, ZCatalog.ZCatalog) and
                callable(getattr(base, 'indexObject', None))):
            obj.indexObject()

        if callable(getattr(base, '_updateCatalog', None)):
            obj._updateCatalog(obj)

    def delRemovedObj(self, obj, path=None):
        """Delete broken objects."""
        if not isinstance(obj, broken.Broken):
            return

        if path is None:
            path = '/'.join(obj.getPhysicalPath())
        obj_id = path.rsplit('/', 1)[-1]
        container = aq_parent(obj)

        if aq_base(container) is aq_base(self.trans_tool):
            self.log('Unregistering broken transform: %s' % path)
            self.unmapTransform(container, obj)

        self.log('Deleting broken object: %s' % path)
        container.manage_delObjects([obj_id])
        assert container._getOb(obj_id, None) is None

        return obj_id

    def unmapTransform(self, container, transform):
        """unmap transform from portal_transforms structures"""
        for dest in container._mtmap.itervalues():
            for transforms in dest.itervalues():
                for registered in transforms:
                    if aq_base(registered) is aq_base(transform):
                        transforms.remove(transform)
                        container._p_changed = True


def cleanupBrokenObjects(context):
    upgrader = CleanupBrokenObjects(context)
    upgrader.upgrade()
