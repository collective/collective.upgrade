# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

import transaction
from OFS.Folder import Folder
from OFS.Image import manage_addFile
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, setRoles
from plone.uuid.interfaces import ATTRIBUTE_NAME, IUUID
from Products.CMFCore.utils import getToolByName
from ZODB.DB import DB
from ZODB.FileStorage import FileStorage
from zope.globalrequest import clearRequest, setRequest
from zope.testing.loggingsupport import InstalledHandler

from collective.upgrade import steps
from collective.upgrade.testing import COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING
from collective.upgrade.tests.helpers import messages
from collective.upgrade.tests.upgrades import PROFILE_ID


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
        document = self.portal[self.portal.invokeFactory("Document", "document", title="Old")]
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
            messages(self.log), ["Deleted custom skin objects from {0!r}: []".format(custom)]
        )

    def test_cleanupSkinLayers(self):
        skins = self.portal.portal_skins
        for theme in skins.getSkinSelections():
            skins.addSkinSelection(theme, skins.getSkinPath(theme) + ",collective_removed")
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
            "{0!r} theme layer 'collective_removed' is missing but not listed to be "
            "removed".format(theme),
        )

    def test_uninstallAddOns(self):
        qi = getToolByName(self.portal, "portal_quickinstaller")
        qi.installProduct("plone.session")
        self.assertTrue(qi.isProductInstalled("plone.session"))
        self.assertNotEqual(self.setup.getLastVersionForProfile("plone.session:default"), "unknown")
        steps.uninstallAddOns(self.setup, addons=["plone.session"])
        self.assertFalse(qi.isProductInstalled("plone.session"))
        self.assertEqual(self.setup.getLastVersionForProfile("plone.session:default"), "unknown")
        self.assertTrue(
            [
                message
                for message in messages(self.log)
                if message.startswith("Uninstalling the 'plone.session' add-on for ")
            ]
        )

    def test_migrateCMFEditionsFolderVersions(self):
        document = self.portal[self.portal.invokeFactory("Document", "document")]
        self.portal.portal_repository.save(document)
        steps.migrateCMFEditionsFolderVersions(self.setup)
        self.assertTrue(
            [
                message
                for message in messages(self.log)
                if " Begin cleaning up CMFEditions objects in " in message
            ]
        )
        self.assertEqual(self.portal.portal_repository.retrieve(document, 0).object.getId(), "document")

    def test_fixDuplicateUIDs(self):
        first = self.portal[self.portal.invokeFactory("Document", "first")]
        copy = self.portal[self.portal.invokeFactory("Document", "copy_of_first")]
        setattr(copy, ATTRIBUTE_NAME, IUUID(first))
        copy.reindexObject(idxs=["UID"])
        # the UID index is a UUIDIndex: nothing is done
        steps.fixDuplicateUIDs(self.setup)
        self.assertEqual(IUUID(copy), IUUID(first))

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
        self.assertTrue(notes[-1].endswith(b"Committing changes prior to packing the ZODB"))
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
        # the base profile is imported first: Plone 4 fails on the Archetypes type
        # infos of a site whose types come from plone.app.contenttypes
        with self.assertRaises(ValueError) as cm:
            steps.resetProfiles(self.setup, extension_profiles=[PROFILE_ID])
        self.assertEqual(str(cm.exception), "undefined property 'content_meta_type'")
        self.assertEqual(
            messages(self.log), ["Importing the 'profile-Products.CMFPlone:plone' base profile"]
        )
        # without extension profiles: the ones selected by default when adding a site
        self.log.clear()
        with self.assertRaises(ValueError):
            steps.resetProfiles(self.setup)
        self.assertEqual(
            messages(self.log), ["Importing the 'profile-Products.CMFPlone:plone' base profile"]
        )
