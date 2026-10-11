# -*- coding: utf-8 -*-
import unittest

from Products.GenericSetup.interfaces import EXTENSION
from zope.component import queryMultiAdapter

from collective.upgrade.ploneupgrader import PloneUpgrader
from collective.upgrade.portals import PortalsUpgrader
from collective.upgrade.testing import COLLECTIVE_UPGRADE_INTEGRATION_TESTING

BASELINE = "Products.CMFPlone:plone"


def baseline_steps(setup):
    """(source, destination, title) of every step of the Plone baseline profile."""
    steps = []
    for info in setup.listUpgrades(BASELINE, show_old=True):
        for step in info if isinstance(info, list) else [info]:
            steps.append((step["ssource"], step["sdest"], step["title"]))
    return steps


class TestUpgradersZcml(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def test_views(self):
        request = self.layer["request"]
        self.assertIsInstance(
            queryMultiAdapter((self.layer["portal"], request), name="collective.upgrade.form"),
            PloneUpgrader,
        )
        self.assertIsInstance(
            queryMultiAdapter((self.layer["app"], request), name="collective.upgrade.form"),
            PortalsUpgrader,
        )


class TestStepsZcml(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def setUp(self):
        self.setup = self.layer["portal"].portal_setup

    def test_profiles(self):
        info = self.setup.getProfileInfo("collective.upgrade:blank")
        self.assertEqual(info["title"], "Blank import for all steps")
        self.assertEqual(info["type"], EXTENSION)

    def test_steps(self):
        self.assertEqual(
            self.setup.getImportStepMetadata("reconcile_users")["handler"],
            "collective.upgrade.pas.reconcileUsersImport",
        )
        self.assertEqual(
            self.setup.getImportStepMetadata("reconcile_groups")["handler"],
            "collective.upgrade.pas.reconcileGroupsImport",
        )
        self.assertEqual(
            self.setup.getExportStepMetadata("reconcile_users")["handler"],
            "collective.upgrade.pas.reconcileUsersExport",
        )
        self.assertEqual(
            self.setup.getExportStepMetadata("reconcile_groups")["handler"],
            "collective.upgrade.pas.reconcileGroupsExport",
        )

    def test_upgradeSteps(self):
        steps = baseline_steps(self.setup)
        self.assertIn(("4001", "4002", "Migrate CMFEditions folder versions."), steps)
        self.assertIn(("4100", "4101", "Fix duplicate UIDs."), steps)


class TestBrokenZcml(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def test_upgradeSteps(self):
        # opt-in: included by testing.zcml, not by configure.zcml
        expected = [
            ("all", "4001", "Cleanup missing component registrations."),
            ("all", "4001", "Cleanup missing portal_setup registrations."),
            ("all", "4001", "Cleanup broken TextIndexes such as from TextIndexNG."),
            ("all", "4001", "Cleanup broken objects."),
        ]
        steps = baseline_steps(self.layer["portal"].portal_setup)
        self.assertEqual([step for step in steps if step in expected], expected)
