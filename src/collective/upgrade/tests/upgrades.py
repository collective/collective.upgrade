# -*- coding: utf-8 -*-
"""Test-only upgrade steps: each one records what ran on the portal."""

from persistent.list import PersistentList
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

PROFILE_ID = "collective.upgrade.tests:upgrades"
NOT_INSTALLED_PROFILE_ID = "collective.upgrade.tests:not_installed"
CHECKER_PROFILE_ID = "collective.upgrade.tests:checker"


def link_integrity_checks(portal):
    """Plone 4: site_properties, Plone 6: registry."""
    properties = getToolByName(portal, "portal_properties", None)
    if properties is not None:
        return properties.site_properties.getProperty("enable_link_integrity_checks")
    return getUtility(IRegistry).get("plone.enable_link_integrity_checks")


def runs(portal):
    """(step, profile version when it ran, link integrity checks) tuples."""
    return list(getattr(portal, "_upgrade_test_runs", []))


def record(setup, step, profile_id=PROFILE_ID):
    portal = getToolByName(setup, "portal_url").getPortalObject()
    if getattr(portal, "_upgrade_test_runs", None) is None:
        portal._upgrade_test_runs = PersistentList()
    portal._upgrade_test_runs.append(
        (
            step,
            setup.getLastVersionForProfile(profile_id),
            link_integrity_checks(portal),
        )
    )


def step_1_to_2_a(setup):
    record(setup, "1 to 2 a")


def step_1_to_2_b(setup):
    record(setup, "1 to 2 b")


def step_2_to_3(setup):
    record(setup, "2 to 3")


def step_not_installed(setup):
    record(setup, "not installed", NOT_INSTALLED_PROFILE_ID)


def step_checker(setup):
    record(setup, "checker", CHECKER_PROFILE_ID)


def always_proposed(setup):
    return True
