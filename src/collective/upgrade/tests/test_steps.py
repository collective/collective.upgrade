from collective.upgrade import steps
from collective.upgrade.testing import COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING
from collective.upgrade.tests.helpers import messages
from collective.upgrade.tests.upgrades import PROFILE_ID
from OFS.Folder import Folder
from OFS.Image import manage_addFile
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import ATTRIBUTE_NAME
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.DateRecurringIndex.index import DateRecurringIndex
from Products.GenericSetup.tool import SetupTool
from Products.PluginIndexes.interfaces import IDateRangeIndex
from unittest import mock
from ZODB.DB import DB
from ZODB.FileStorage import FileStorage
from zope.component import getUtility
from zope.globalrequest import clearRequest
from zope.globalrequest import setRequest
from zope.testing.loggingsupport import InstalledHandler

import os
import shutil
import tempfile
import transaction
import unittest


class TestSteps(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        # upgrade steps get portal_setup
        self.setup = self.portal.portal_setup
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        setRequest(self.layer["request"])
        self.addCleanup(clearRequest)
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def test_catalogReindex(self):
        document = self.portal[
            self.portal.invokeFactory("Document", "document", title="Old")
        ]
        catalog = self.portal.portal_catalog
        self.assertEqual(catalog(id="document")[0].Title, "Old")
        document.title = "New"
        steps.catalogReindex(self.setup)
        self.assertEqual(catalog(id="document")[0].Title, "New")

    def test_deleteCustomSkinObjs(self):
        custom = self.portal.portal_skins.custom
        manage_addFile(custom, "logo.png")
        # nothing to delete
        steps.deleteCustomSkinObjs(self.setup, "missing.png")
        self.assertEqual(messages(self.log), [])
        steps.deleteCustomSkinObjs(self.setup, "logo.png", "missing.png")
        self.assertNotIn("logo.png", custom.objectIds())
        # manage_delObjects empties the list before it is logged
        self.assertEqual(
            messages(self.log), [f"Deleted custom skin objects from {custom!r}: []"]
        )

    def test_cleanupSkinLayers(self):
        skins = self.portal.portal_skins
        for theme in skins.getSkinSelections():
            skins.addSkinSelection(
                theme, skins.getSkinPath(theme) + ",collective_removed"
            )
        # missing layers are removed
        steps.cleanupSkinLayers(self.setup)
        for theme in skins.getSkinSelections():
            self.assertNotIn("collective_removed", skins.getSkinPath(theme).split(","))
            self.assertIn("custom", skins.getSkinPath(theme).split(","))
        # only the given layers, a missing layer must be listed
        steps.cleanupSkinLayers(self.setup, remove_layers=["custom"])
        for theme in skins.getSkinSelections():
            self.assertNotIn("custom", skins.getSkinPath(theme).split(","))
        theme = skins.getSkinSelections()[0]
        skins.addSkinSelection(theme, skins.getSkinPath(theme) + ",collective_removed")
        with self.assertRaises(ValueError) as cm:
            steps.cleanupSkinLayers(self.setup, remove_layers=["custom"])
        self.assertEqual(
            str(cm.exception),
            "{!r} theme layer 'collective_removed' is missing but not listed to be "
            "removed".format(theme),
        )

    def test_uninstallAddOns(self):
        installer = get_installer(self.portal)
        installer.install_product("plone.session")
        registry = getUtility(IRegistry)
        self.assertIn("plone.bundles/plone-session.enabled", registry)
        # with its uninstall profile; an add-on that isn't installed is skipped
        steps.uninstallAddOns(self.setup, addons=["plone.session", "plone.app.caching"])
        self.assertFalse(installer.is_product_installed("plone.session"))
        self.assertEqual(
            self.setup.getLastVersionForProfile("plone.session:default"), "unknown"
        )
        self.assertNotIn("plone.bundles/plone-session.enabled", registry)
        self.assertEqual(
            messages(self.log),
            [
                "Uninstalling the 'plone.session' add-on for {!r} using the "
                "'plone.session:uninstall' profile".format(self.setup)
            ],
        )
        # without an uninstall profile: the profile versions are cleared
        self.log.clear()
        steps.uninstallAddOns(self.setup, addons=["collective.upgrade.tests"])
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), "unknown")
        self.assertEqual(
            messages(self.log),
            [
                f"Uninstalling the 'collective.upgrade.tests' add-on for {self.setup!r}",
                f"Clearing the {PROFILE_ID!r} profile version ('1',) for {self.setup!r}",
            ],
        )
        # no add-ons given: the installed ones whose profiles are no longer registered
        self.log.clear()
        self.setup.setLastVersionForProfile("collective.removed:default", "1000")
        steps.uninstallAddOns(self.setup)
        self.assertEqual(
            self.setup.getLastVersionForProfile("collective.removed:default"), "unknown"
        )
        self.assertNotEqual(
            self.setup.getLastVersionForProfile("plone.app.contenttypes:default"),
            "unknown",
        )
        self.assertEqual(
            messages(self.log),
            [
                f"Uninstalling the 'collective.removed' add-on for {self.setup!r}",
                "Clearing the 'collective.removed:default' profile version ('1000',) "
                "for {!r}".format(self.setup),
            ],
        )

    def test_migrateCMFEditionsFolderVersions(self):
        document = self.portal[self.portal.invokeFactory("Document", "document")]
        self.portal.portal_repository.save(document)
        # Plone 5.2+: no plone.app.folder, nothing is migrated
        steps.migrateCMFEditionsFolderVersions(self.setup)
        self.assertEqual(
            messages(self.log),
            [
                f"{self.setup}: No plone.app.folder, skipping the CMFEditions folder migration"
            ],
        )
        self.assertEqual(
            self.portal.portal_repository.retrieve(document, 0).object.getId(),
            "document",
        )

    def test_fixDuplicateUIDs(self):
        first = self.portal[self.portal.invokeFactory("Document", "first")]
        copy = self.portal[self.portal.invokeFactory("Document", "copy_of_first")]
        uid = IUUID(first)
        setattr(copy, ATTRIBUTE_NAME, uid)
        copy.reindexObject(idxs=["UID"])
        # the UID index is a UUIDIndex: nothing is done
        steps.fixDuplicateUIDs(self.setup)
        self.assertEqual(IUUID(copy), uid)
        self.assertEqual(messages(self.log), [])
        # a FieldIndex: the copy gets a new UID
        catalog = self.portal.portal_catalog
        catalog.delIndex("UID")
        catalog.addIndex("UID", "FieldIndex")
        catalog.reindexIndex("UID", None)
        self.assertEqual(len(catalog(UID=uid)), 2)
        # a pasted copy keeps the creation date
        copy.creation_date = first.creation_date
        steps.fixDuplicateUIDs(self.setup)
        self.assertEqual(IUUID(first), uid)
        self.assertNotEqual(IUUID(copy), uid)
        self.assertEqual([brain.getObject() for brain in catalog(UID=uid)], [first])
        self.assertEqual(
            [brain.getObject() for brain in catalog(UID=IUUID(copy))], [copy]
        )
        self.assertEqual(
            messages(self.log),
            [
                "Multiple objects found for UID {!r}, assuming {!r} is the original".format(
                    uid, first
                ),
                f"Assigned new UID {IUUID(copy)!r} to {copy!r}",
            ],
        )

    def test_cleanupMissingReferenceTargets(self):
        # Plone 5.2+: no Archetypes references to clean up
        steps.cleanupMissingReferenceTargets(self.setup)
        self.assertEqual(
            messages(self.log),
            [
                "{}: No Products.Archetypes, skipping the reference targets "
                "cleanup".format(self.portal)
            ],
        )

    def test_pack_zodb(self):
        # a DemoStorage can't be packed: use a FileStorage
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        db = DB(FileStorage(os.path.join(tmpdir, "Data.fs")))
        self.addCleanup(db.close)
        connection = db.open()
        self.addCleanup(connection.close)
        folder = connection.root()["folder"] = Folder("folder")
        transaction.commit()
        folder.title = "New"
        transaction.commit()
        self.assertEqual(len(db.history(folder._p_oid, size=10)), 2)
        # pending changes are committed, then the old revisions are packed
        folder.title = "Newer"
        steps.pack_zodb(folder)
        self.assertEqual(len(db.history(folder._p_oid, size=10)), 1)
        notes = [record.description for record in db.storage.iterator()]
        self.assertTrue(
            notes[-1].endswith(b"Committing changes prior to packing the ZODB")
        )
        self.assertEqual(folder.title, "Newer")

    def test_cookResourceRegisties(self):
        css = getToolByName(self.portal, "portal_css", None)
        if css is not None:  # Plone 4
            css.registerStylesheet("upgraded.css", skipCooking=True)
            self.assertNotIn("upgraded.css", css.concatenatedresources)
        steps.cookResourceRegisties(self.setup)
        if css is not None:
            self.assertIn("upgraded.css", css.concatenatedresources)

    def test_resetProfiles(self):
        base = "Importing the 'profile-Products.CMFPlone:plone' base profile"
        if IDateRangeIndex.implementedBy(DateRecurringIndex):
            # Plone 6.2 (Products.DateRecurringIndex 4): the catalog step of the base
            # profile gives the start and end indexes to the DateRangeIndex importer
            with self.assertRaises(AttributeError) as cm:
                steps.resetProfiles(self.setup, extension_profiles=[PROFILE_ID])
            self.assertEqual(str(cm.exception), "_since_field")
            self.assertEqual(messages(self.log), [base])
        else:
            # Plone 6.1: the base profile, then the extension profiles
            steps.resetProfiles(self.setup, extension_profiles=[PROFILE_ID])
            self.assertEqual(
                messages(self.log),
                [base, f"Importing the {PROFILE_ID!r} extension profile"],
            )
            self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        # without extension profiles: the ones selected by default when adding a site
        with mock.patch.object(SetupTool, "runAllImportStepsFromProfile") as run:
            steps.resetProfiles(self.setup)
        self.assertEqual(
            run.call_args_list,
            [
                mock.call("profile-Products.CMFPlone:plone", purge_old=False),
                mock.call("profile-plone.app.contenttypes:default"),
                mock.call("profile-plone.app.caching:default"),
                mock.call("profile-plonetheme.barceloneta:default"),
            ],
        )
