# -*- coding: utf-8 -*-
import unittest

from persistent.list import PersistentList
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, setRoles
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from zope.testing.loggingsupport import InstalledHandler

from collective.upgrade.ploneupgrader import HiddenProfiles, PloneUpgrader
from collective.upgrade.testing import (COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING,
                                        COLLECTIVE_UPGRADE_INTEGRATION_TESTING)
from collective.upgrade.tests.helpers import messages
from collective.upgrade.tests.upgrades import (CHECKER_PROFILE_ID,
                                               NOT_INSTALLED_PROFILE_ID,
                                               PROFILE_ID,
                                               link_integrity_checks, runs)

try:
    from plone.base.interfaces import INonInstallable
except ImportError:  # Plone 4
    from Products.CMFPlone.interfaces import INonInstallable

BASELINE = "Products.CMFPlone:plone"


class TestHiddenProfiles(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def test_getNonInstallableProfiles(self):
        utility = getUtility(INonInstallable, name="collective.upgrade")
        self.assertIsInstance(utility, HiddenProfiles)
        self.assertEqual(utility.getNonInstallableProfiles(), ["collective.upgrade:blank"])
        self.assertEqual(utility.getNonInstallableProducts(), [])


class TestPloneUpgrader(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.setup = self.portal.portal_setup
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.upgrader = self.portal.restrictedTraverse("@@collective.upgrade.form")
        # set by upgrade(), needed to call the other methods directly
        self.upgrader.setup = self.setup
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def test_upgrade(self):
        self.assertIsInstance(self.upgrader, PloneUpgrader)
        # a site one Plone version behind: the last Plone upgrade step runs first
        steps = self.setup.listUpgrades(BASELINE, show_old=True)[-1]
        if not isinstance(steps, list):
            steps = [steps]
        self.setup.setLastVersionForProfile(BASELINE, steps[0]["source"])
        self.upgrader.upgrade()
        self.assertEqual(self.setup.getLastVersionForProfile(BASELINE), steps[0]["dest"])
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        log = messages(self.log)
        portal = str(self.portal)
        baseline = log.index(
            "{0}: Upgrading profile {1!r} to {2!r}".format(
                portal, BASELINE, steps[0]["sdest"]
            )
        )
        extension = [
            index
            for index, message in enumerate(log)
            if message.endswith("{0}' to '2'".format(PROFILE_ID))
        ][0]
        self.assertLess(baseline, extension)
        # Plone 4: the resource registries are cooked after the upgrades
        refreshed = "{0}: Refreshed resource registries for {0}".format(portal)
        if getToolByName(self.portal, "portal_css", None) is not None:
            self.assertEqual(log[-1], refreshed)
            self.assertEqual(log[-2], "{0}: Upgraded {0}".format(portal))
        else:
            self.assertNotIn(refreshed, log)
            self.assertEqual(log[-1], "{0}: Upgraded {0}".format(portal))

    def test_upgradeProfile(self):
        orig = link_integrity_checks(self.portal)
        self.assertTrue(orig)
        # disabled during the upgrade, then restored
        self.upgrader.upgradeProfile(PROFILE_ID, enable_link_integrity_checks=False)
        self.assertEqual(
            [checks for step, version, checks in runs(self.portal)], [False, False, False]
        )
        self.assertEqual(link_integrity_checks(self.portal), orig)
        # not given: left as is
        self.setup.setLastVersionForProfile(PROFILE_ID, "1")
        self.portal._upgrade_test_runs = PersistentList()
        self.upgrader.upgradeProfile(PROFILE_ID)
        self.assertEqual(
            [checks for step, version, checks in runs(self.portal)], [orig, orig, orig]
        )
        # restored after an error too
        self.setup.setLastVersionForProfile(CHECKER_PROFILE_ID, "1")
        with self.assertRaises(ValueError):
            self.upgrader.upgradeProfile(
                CHECKER_PROFILE_ID, enable_link_integrity_checks=False
            )
        self.assertFalse(runs(self.portal)[-1][2])
        self.assertEqual(link_integrity_checks(self.portal), orig)

    def test_isProfileInstalled(self):
        self.assertTrue(self.upgrader.isProfileInstalled(PROFILE_ID))
        # Plone 5.2+: only the profile version counts (no quickinstaller fallback): a
        # never applied profile of an installed product is not installed
        self.assertFalse(self.upgrader.isProfileInstalled(NOT_INSTALLED_PROFILE_ID))
