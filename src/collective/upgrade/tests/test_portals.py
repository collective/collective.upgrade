# -*- coding: utf-8 -*-
import unittest

from plone.app.testing import SITE_OWNER_NAME, login
from zope.testing.loggingsupport import InstalledHandler

from collective.upgrade.ploneupgrader import PloneUpgrader
from collective.upgrade.portals import PortalsUpgrader
from collective.upgrade.testing import COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING
from collective.upgrade.tests.helpers import messages
from collective.upgrade.tests.upgrades import PROFILE_ID


class TestPortalsUpgrader(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.setup = self.portal.portal_setup
        login(self.app, SITE_OWNER_NAME)
        self.upgrader = self.app.restrictedTraverse("@@collective.upgrade.form")
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def test_upgrade(self):
        self.assertIsInstance(self.upgrader, PortalsUpgrader)
        portal = str(self.portal)
        # every portal of the Zope root
        self.upgrader.upgrade()
        self.assertIn("{0}: Upgrading all portals".format(self.app), messages(self.log))
        self.assertIn("{0}: Upgraded {0}".format(portal), messages(self.log))
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        # only the given paths, with the other options
        self.setup.setLastVersionForProfile(PROFILE_ID, "1")
        self.log.clear()
        self.upgrader.upgrade(paths=["plone"], upgrade_all_profiles=False)
        self.assertEqual(
            messages(self.log)[0], "{0}: Upgrading portals: ['plone']".format(self.app)
        )
        self.assertIn("{0}: Upgraded {0}".format(portal), messages(self.log))
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("1",))
        self.upgrader.upgrade(paths=["plone"])
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))

    def test_walkUpgraders(self):
        walked = dict(
            (upgrader.context.getId(), upgrader)
            for upgrader in self.upgrader.walkUpgraders(self.app)
        )
        # the portal, and every other object manager, walked in turn (Plone 4: also
        # Control_Panel)
        self.assertIsInstance(walked["plone"], PloneUpgrader)
        self.assertIsInstance(walked["acl_users"], PortalsUpgrader)
