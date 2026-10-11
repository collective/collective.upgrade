# -*- coding: utf-8 -*-
import unittest

from persistent.list import PersistentList
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, setRoles
from zope.testing.loggingsupport import InstalledHandler

from collective.upgrade.testing import COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING
from collective.upgrade.tests.helpers import messages, transaction_notes
from collective.upgrade.tests.upgrades import (CHECKER_PROFILE_ID,
                                               NOT_INSTALLED_PROFILE_ID,
                                               PROFILE_ID, runs)
from collective.upgrade.upgrader import PortalUpgrader

BASELINE = "Products.CMFPlone:plone"


class TestPortalUpgrader(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.setup = self.portal.portal_setup
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.upgrader = PortalUpgrader(self.portal, self.layer["request"])
        # set by upgrade(), needed to call the other methods directly
        self.upgrader.setup = self.setup
        self.upgrader.base_profile = BASELINE
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def reset(self, version="1"):
        self.setup.setLastVersionForProfile(PROFILE_ID, version)
        self.portal._upgrade_test_runs = PersistentList()
        self.log.clear()

    def test_upgrade(self):
        portal = str(self.portal)
        # default: baseline profile, then every installed profile with pending upgrades
        self.upgrader.upgrade()
        self.assertEqual(
            [step for step, version, checks in runs(self.portal)],
            ["1 to 2 a", "1 to 2 b", "2 to 3"],
        )
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        self.assertEqual(
            self.setup.getLastVersionForProfile(NOT_INSTALLED_PROFILE_ID), "unknown"
        )
        log = messages(self.log)
        self.assertEqual(log[0], "{0}: Upgrading {0}".format(portal))
        self.assertIn("{0}: Nothing to upgrade for profile {1!r}".format(portal, BASELINE), log)
        self.assertEqual(log[-1], "{0}: Upgraded {0}".format(portal))
        # upgrade_portal=False skips the baseline profile
        self.reset()
        self.upgrader.upgrade(upgrade_portal=False)
        self.assertEqual(len(runs(self.portal)), 3)
        self.assertNotIn(
            "{0}: Nothing to upgrade for profile {1!r}".format(portal, BASELINE),
            messages(self.log),
        )
        # only the given profiles
        self.reset()
        self.setup.setLastVersionForProfile(CHECKER_PROFILE_ID, "1")
        self.upgrader.upgrade(upgrade_all_profiles=False, upgrade_profiles=[PROFILE_ID])
        self.assertEqual(len(runs(self.portal)), 3)
        self.assertEqual(self.setup.getLastVersionForProfile(CHECKER_PROFILE_ID), ("1",))
        # nothing but the baseline profile
        self.reset()
        self.upgrader.upgrade(upgrade_all_profiles=False)
        self.assertEqual(runs(self.portal), [])
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("1",))
        # both options
        with self.assertRaises(ValueError) as cm:
            self.upgrader.upgrade(upgrade_profiles=[PROFILE_ID])
        self.assertEqual(
            str(cm.exception), "upgrade_profiles conflicts with upgrade_all_profiles"
        )

    def test_upgradeProfile(self):
        self.upgrader.upgradeProfile(PROFILE_ID)
        # one destination at a time, the version is set after each one
        self.assertEqual(
            [(step, version) for step, version, checks in runs(self.portal)],
            [("1 to 2 a", ("1",)), ("1 to 2 b", ("1",)), ("2 to 3", ("2",))],
        )
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        portal = str(self.portal)
        self.assertEqual(
            messages(self.log),
            [
                "{0}: Upgrading profile {1!r} to '2'".format(portal, PROFILE_ID),
                "{0}: Running upgrade step for profile {1} from 1 to 2: "
                "First step from 1 to 2.".format(portal, PROFILE_ID),
                "{0}: Finished upgrade step for profile {1} from 1 to 2: "
                "First step from 1 to 2.".format(portal, PROFILE_ID),
                "{0}: Running upgrade step for profile {1} from 1 to 2: "
                "Second step from 1 to 2.".format(portal, PROFILE_ID),
                "{0}: Finished upgrade step for profile {1} from 1 to 2: "
                "Second step from 1 to 2.".format(portal, PROFILE_ID),
                "Upgraded profile {0!r} to '2'".format(PROFILE_ID),
                "{0}: Upgrading profile {1!r} to '3'".format(portal, PROFILE_ID),
                "{0}: Running upgrade step for profile {1} from 2 to 3: "
                "Step from 2 to 3.".format(portal, PROFILE_ID),
                "{0}: Finished upgrade step for profile {1} from 2 to 3: "
                "Step from 2 to 3.".format(portal, PROFILE_ID),
                "Upgraded profile {0!r} to '3'".format(PROFILE_ID),
                "{0}: Finished upgrading {1!r} profile".format(portal, PROFILE_ID),
            ],
        )
        # up to date
        self.log.clear()
        self.upgrader.upgradeProfile(PROFILE_ID)
        self.assertEqual(
            messages(self.log),
            ["{0}: Nothing to upgrade for profile {1!r}".format(portal, PROFILE_ID)],
        )

    def test_listUpgrades(self):
        # only the steps up to the next destination
        self.assertEqual(
            [(info["title"], info["dest"]) for info in self.upgrader.listUpgrades(PROFILE_ID)],
            [("First step from 1 to 2", ("2",)), ("Second step from 1 to 2", ("2",))],
        )
        self.reset("2")
        self.assertEqual(
            [(info["title"], info["dest"]) for info in self.upgrader.listUpgrades(PROFILE_ID)],
            [("Step from 2 to 3", ("3",))],
        )
        self.reset("3")
        self.assertEqual(self.upgrader.listUpgrades(PROFILE_ID), [])
        # steps registered for the baseline profile are not proposed on an up-to-date site
        self.assertEqual(self.upgrader.listUpgrades(BASELINE), [])

    def test_flattenUpgrades(self):
        self.assertEqual(
            [info["title"] for info in self.upgrader.flattenUpgrades(PROFILE_ID)],
            ["First step from 1 to 2", "Second step from 1 to 2", "Step from 2 to 3"],
        )
        # GenericSetup lists the steps of a profile that is not installed
        self.assertEqual(
            [info["title"] for info in self.upgrader.flattenUpgrades(NOT_INSTALLED_PROFILE_ID)],
            ["Step of a profile that is not installed"],
        )

    def test_doUpgrades(self):
        self.upgrader.doUpgrades(PROFILE_ID, self.upgrader.listUpgrades(PROFILE_ID))
        self.assertEqual(len(runs(self.portal)), 2)
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("2",))
        # one commit per destination, with a note
        self.assertTrue(
            [
                note
                for note in transaction_notes(self.app)
                if note.endswith("Upgraded profile {0!r} to '2'".format(PROFILE_ID))
            ]
        )
        # a step with a checker doesn't record a version
        self.setup.setLastVersionForProfile(CHECKER_PROFILE_ID, "1")
        with self.assertRaises(ValueError) as cm:
            self.upgrader.doUpgrades(
                CHECKER_PROFILE_ID, self.upgrader.listUpgrades(CHECKER_PROFILE_ID)
            )
        self.assertIn(
            "finished for profile {0!r} but no new version '2' recorded.".format(
                CHECKER_PROFILE_ID
            ),
            str(cm.exception),
        )
        self.assertEqual(runs(self.portal)[-1][0], "checker")
        self.assertEqual(self.setup.getLastVersionForProfile(CHECKER_PROFILE_ID), ("1",))

    def test_upgradeExtensions(self):
        self.upgrader.upgradeExtensions([BASELINE, NOT_INSTALLED_PROFILE_ID, PROFILE_ID])
        # the baseline and the profiles that are not installed are skipped
        self.assertEqual(
            [step for step, version, checks in runs(self.portal)],
            ["1 to 2 a", "1 to 2 b", "2 to 3"],
        )
        self.assertNotIn(BASELINE, " ".join(messages(self.log)))

    def test_isProfileInstalled(self):
        self.assertTrue(self.upgrader.isProfileInstalled(PROFILE_ID))
        self.assertTrue(self.upgrader.isProfileInstalled(BASELINE))
        self.assertFalse(self.upgrader.isProfileInstalled(NOT_INSTALLED_PROFILE_ID))
