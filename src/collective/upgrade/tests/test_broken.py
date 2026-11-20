from Acquisition import aq_base
from collective.upgrade import broken
from collective.upgrade.testing import COLLECTIVE_UPGRADE_INTEGRATION_TESTING
from collective.upgrade.tests.helpers import messages
from OFS.Uninstalled import Broken
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from ZODB.broken import persistentBroken
from ZODB.interfaces import IBroken
from zope.component import getSiteManager
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.testing.loggingsupport import InstalledHandler

import unittest


def broken_object(module, name, container=None, id=None):
    """An object whose class is gone, as Zope loads it from the ZODB."""
    obj = persistentBroken(Broken(None, None, (module, name)))()
    obj.__setstate__({"id": id, "title": "Removed"})
    if container is not None:
        container._setOb(id, obj)
        if isinstance(getattr(aq_base(container), "_objects", None), tuple):
            container._objects += ({"id": id, "meta_type": obj.meta_type},)
    return obj


class TestBroken(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        # upgrade steps get portal_setup
        self.setup = self.portal.portal_setup
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def test_cleanupBrokenComponents(self):
        sm = getSiteManager(self.portal)
        utility = broken_object("collective.removed.utility", "Utility")
        sm.registerUtility(utility, Interface, name="collective.removed")
        self.assertIs(
            aq_base(sm.queryUtility(Interface, name="collective.removed")), utility
        )
        broken.cleanupBrokenComponents(self.setup)
        self.assertIsNone(sm.queryUtility(Interface, name="collective.removed"))
        self.assertTrue(
            messages(self.log)[0].startswith("Unregistering broken utility ")
        )

    def test_cleanupBrokenSetupRegistrations(self):
        toolset = self.setup.getToolsetRegistry()
        toolset.addRequiredTool("portal_removed", "collective.removed.tool.RemovedTool")
        self.assertIn("portal_removed", toolset.listRequiredTools())
        broken.cleanupBrokenSetupRegistrations(self.setup)
        self.assertNotIn("portal_removed", toolset.listRequiredTools())
        self.assertIn("portal_catalog", toolset.listRequiredTools())
        log = messages(self.log)
        self.assertTrue(log[0].startswith("Unregistering missing required tool "))
        # then every profile context is applied
        self.assertTrue(
            [
                message
                for message in log
                if message.startswith("Applying profile context ")
                and "'profile-Products.CMFPlone:plone' in " in message
            ]
        )

    def test_cleanupBrokenTextIndexes(self):
        catalog = self.portal.portal_catalog
        catalog._catalog.indexes["SearchableText"] = broken_object(
            "Products.TextIndexNG3.TextIndexNG3", "TextIndexNG3"
        )
        broken.cleanupBrokenTextIndexes(self.setup)
        index = catalog._catalog.getIndex("SearchableText")
        self.assertEqual(index.meta_type, "ZCTextIndex")
        self.assertEqual(index.lexicon_id, "plone_lexicon")
        self.assertTrue(messages(self.log)[0].startswith("Replacing "))

    def test_cleanupBrokenObjects(self):
        document = self.portal[self.portal.invokeFactory("Document", "document")]
        broken_object("collective.removed.tool", "RemovedTool", self.setup, "removed")
        catalog = self.portal.portal_catalog
        self.assertEqual(len(catalog(id="document")), 1)
        # as registered, the step gets portal_setup: only portal_setup is walked and the
        # catalog is left empty
        broken.cleanupBrokenObjects(self.setup)
        self.assertNotIn("removed", self.setup.objectIds())
        self.assertEqual(len(catalog(portal_type="Document")), 0)
        self.assertEqual(len(catalog()), 0)
        self.assertIn(document, self.portal.objectValues())
        # on the portal: the file system skin objects are not persistent
        with self.assertRaises(AttributeError) as cm:
            broken.cleanupBrokenObjects(self.portal)
        self.assertEqual(str(cm.exception), "_p_activate")


class TestCleanupBrokenObjects(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = self.portal[self.portal.invokeFactory("Folder", "folder")]
        self.document = self.folder[self.folder.invokeFactory("Document", "document")]
        self.other = self.portal[self.portal.invokeFactory("Document", "other")]
        self.portal.portal_repository.save(self.document)
        # last: a savepoint can't store new broken objects
        broken_object(
            "collective.removed.content", "RemovedItem", self.folder, "removed"
        )
        self.transforms = getToolByName(self.portal, "portal_transforms")
        self.transform = broken_object(
            "collective.removed.transforms",
            "removed_to_html",
            self.transforms,
            "removed_to_html",
        )
        self.registered = list(list(self.transforms._mtmap.values())[0].values())[0]
        self.registered.append(self.transform)
        self.upgrader = broken.CleanupBrokenObjects(self.folder)
        self.upgrader.trans_tool = self.transforms
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def test_upgrade(self):
        self.upgrader.upgrade()
        self.assertNotIn("removed", self.folder.objectIds())
        log = messages(self.log)
        self.assertTrue(
            [
                message
                for message in log
                if message.startswith(
                    "{}: Begin cleaning up CMFEditions objects in "
                    "<ZVCStorageTool at /plone/portal_historiesstorage".format(
                        self.folder
                    )
                )
            ]
        )
        # the versions are walked without catalog updates
        self.assertTrue(self.upgrader.update_catalogs)

    def test_upgradeObjects(self):
        self.document.title = "Cleaned"
        catalog = self.portal.portal_catalog
        self.assertEqual(len(catalog(id="other")), 1)
        self.upgrader.upgradeObjects()
        self.assertNotIn("removed", self.folder.objectIds())
        # every catalog is cleared, then the walked objects are indexed again
        self.assertEqual(
            [brain.getObject() for brain in catalog(portal_type="Document")],
            [self.document],
        )
        self.assertEqual(catalog(portal_type="Document")[0].Title, "Cleaned")
        self.assertIn(self.other, self.portal.objectValues())
        log = messages(self.log)
        self.assertTrue(
            log[0].startswith(
                f"{self.folder}: Clearing the <CatalogTool at /plone/portal_catalog"
            )
        )

    def test_upgradeObj(self):
        self.document.__dict__["__implements__"] = ()
        alsoProvides(self.document, IBroken)
        self.document.title = "Cleaned"
        self.upgrader.upgradeObj(self.document)
        self.assertNotIn("__implements__", self.document.__dict__)
        self.assertFalse(IBroken.providedBy(self.document))
        self.assertEqual(
            self.portal.portal_catalog(UID=IUUID(self.document))[0].Title, "Cleaned"
        )

    def test_delRemovedObj(self):
        self.assertIsNone(self.upgrader.delRemovedObj(self.document, "/document"))
        # the walk gives the path: the id of a broken object is not readable
        removed = self.folder["removed"]
        self.assertEqual(removed.getId(), "broken")
        self.assertEqual(self.upgrader.delRemovedObj(removed, "/removed"), "removed")
        self.assertNotIn("removed", self.folder.objectIds())
        self.assertEqual(
            messages(self.log), [f"{self.folder}: Deleting broken object: /removed"]
        )
        # a broken transform is unregistered too
        self.upgrader.delRemovedObj(
            self.transforms["removed_to_html"], "/removed_to_html"
        )
        self.assertNotIn("removed_to_html", self.transforms.objectIds())
        self.assertNotIn(self.transform, self.registered)

    def test_unmapTransform(self):
        self.upgrader.unmapTransform(self.transforms, self.transform)
        self.assertNotIn(self.transform, self.registered)
        self.assertIn("removed_to_html", self.transforms.objectIds())
