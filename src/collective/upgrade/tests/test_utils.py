# -*- coding: utf-8 -*-
import io
import logging
import re
import unittest

import transaction
from Acquisition import aq_base
from plone.app.testing import (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,
                               TEST_USER_ID, TEST_USER_NAME,
                               TEST_USER_PASSWORD, login, setRoles)
from zExceptions import Unauthorized
from zodbupdate.main import duplicate_filter
from zope.component import getSiteManager, queryUtility
from zope.component.hooks import setSite
from zope.globalrequest import clearRequest, setRequest
from zope.interface.verify import verifyObject
from zope.testing.loggingsupport import InstalledHandler

from collective.upgrade.interfaces import IUpgrader
from collective.upgrade.ploneupgrader import HiddenProfiles
from collective.upgrade.testing import COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING
from collective.upgrade.tests.helpers import messages, transaction_notes
from collective.upgrade.tests.upgrades import PROFILE_ID
from collective.upgrade.utils import (Upgrader, overrideComponents,
                                      transaction_note)

try:
    from plone.base.interfaces import INonInstallable
except ImportError:  # Plone 4
    from Products.CMFPlone.interfaces import INonInstallable

try:
    from plone.testing.zope import Browser
except ImportError:  # Plone 4
    from plone.testing.z2 import Browser

LINE = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d INFO collective\.upgrade ")


class TestUpgrader(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.upgrader = Upgrader(self.portal, self.request)
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)
        duplicate_filter.seen.clear()

    def browser(self, user=None, password=None):
        browser = Browser(self.app)
        browser.handleErrors = False
        if user is not None:
            browser.addHeader("Authorization", "Basic {0}:{1}".format(user, password))
        return browser

    def test___call__(self):
        portal = str(self.portal)
        # the log is streamed to the response (read from the response of a direct
        # call: the Plone 4 test browser only reads the body, not the stream)
        response = self.request.response
        response.stdout = io.BytesIO()
        self.request.form["submitted"] = "1"
        view = self.portal.restrictedTraverse("@@collective.upgrade.form")
        self.assertIs(view(), response)
        self.assertNotIn("submitted", self.request.form)
        self.assertTrue(response.getHeader("Content-Type").startswith("text/plain"))
        lines = [
            LINE.sub("", line)
            for line in response.stdout.getvalue().decode("utf-8").splitlines()
            if LINE.match(line)
        ]
        self.assertEqual(lines[0], "{0}: Upgrading {0}".format(portal))
        self.assertIn(
            "{0}: Nothing to upgrade for profile 'Products.CMFPlone:plone'".format(portal),
            lines,
        )
        self.assertIn(
            "{0}: Running upgrade step for profile {1} from 2 to 3: "
            "Step from 2 to 3.".format(portal, PROFILE_ID),
            lines,
        )
        self.assertIn("{0}: Upgraded {0}".format(portal), lines)
        self.assertEqual(
            self.portal.portal_setup.getLastVersionForProfile(PROFILE_ID), ("3",)
        )
        # the duplicate filter is process-wide: a message already reported since
        # the instance started is never streamed again
        self.portal.portal_setup.setLastVersionForProfile(PROFILE_ID, "1")
        response.stdout = io.BytesIO()
        self.request.form["submitted"] = "1"
        view()
        self.assertFalse(
            [
                line
                for line in response.stdout.getvalue().decode("utf-8").splitlines()
                if LINE.match(line)
            ]
        )
        self.assertEqual(
            self.portal.portal_setup.getLastVersionForProfile(PROFILE_ID), ("3",)
        )
        # through the publisher: a Manager runs the pending upgrades
        self.portal.portal_setup.setLastVersionForProfile(PROFILE_ID, "1")
        transaction.commit()
        url = self.portal.absolute_url() + "/@@collective.upgrade.form"
        browser = self.browser(TEST_USER_NAME, TEST_USER_PASSWORD)
        browser.open(url + "?submitted=1")
        self.assertTrue(browser.headers["Content-Type"].startswith("text/plain"))
        self.assertEqual(
            self.portal.portal_setup.getLastVersionForProfile(PROFILE_ID), ("3",)
        )
        # the form keys are passed to the upgrade
        self.portal.portal_setup.setLastVersionForProfile(PROFILE_ID, "1")
        transaction.commit()
        browser.open(url + "?submitted=1&upgrade_all_profiles:boolean=")
        self.assertEqual(
            self.portal.portal_setup.getLastVersionForProfile(PROFILE_ID), ("1",)
        )
        # no form: submitted is required
        with self.assertRaises(KeyError):
            browser.open(url)
        # a Member and Anonymous are refused
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        transaction.commit()
        with self.assertRaises(Unauthorized):
            self.browser(TEST_USER_NAME, TEST_USER_PASSWORD).open(url + "?submitted=1")
        with self.assertRaises(Unauthorized):
            self.browser().open(url + "?submitted=1")
        # the Zope root upgrades every portal, for the site owner only
        root_url = self.app.absolute_url() + "/@@collective.upgrade.form?submitted=1"
        self.browser(SITE_OWNER_NAME, SITE_OWNER_PASSWORD).open(root_url)
        self.assertEqual(
            self.portal.portal_setup.getLastVersionForProfile(PROFILE_ID), ("3",)
        )
        with self.assertRaises(Unauthorized):
            self.browser(TEST_USER_NAME, TEST_USER_PASSWORD).open(root_url)
        with self.assertRaises(Unauthorized):
            self.browser().open(root_url)

    def test_upgrade(self):
        verifyObject(IUpgrader, self.upgrader)
        with self.assertRaises(NotImplementedError):
            self.upgrader.upgrade()

    def test_log(self):
        portal = str(self.portal)
        self.upgrader.log("Hello")
        self.upgrader.log("Careful", level=logging.WARNING, template="{msg}!")
        self.assertEqual(
            [(record.levelno, record.getMessage()) for record in self.log.records],
            [(logging.INFO, "{0}: Hello".format(portal)), (logging.WARNING, "Careful!")],
        )

    def test_commit(self):
        # ZODB records a transaction only when an object changed
        self.portal.setTitle("Upgraded")
        self.upgrader.commit()
        self.portal.setTitle("Upgraded again")
        self.upgrader.commit("Upgraded the news")
        notes = transaction_notes(self.app)
        self.assertEqual(notes[-2], "/plone\nCheckpointing upgrade")
        self.assertEqual(notes[-1], "/plone\nUpgraded the news")
        self.assertEqual(messages(self.log), ["Checkpointing upgrade", "Upgraded the news"])


class TestUtils(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRequest(self.layer["request"])
        self.addCleanup(clearRequest)
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)

    def test_transaction_note(self):
        transaction_note(self.portal, note="Upgraded the news")
        self.assertEqual(transaction.get().description, "/plone\nUpgraded the news")
        # a note exceeding the maximum length is omitted
        transaction_note(self.portal, note="x" * 65533)
        self.assertEqual(transaction.get().description, "/plone\nUpgraded the news\n/plone")
        self.assertTrue(
            messages(self.log)[-1].startswith("Transaction note too large omitting 'xxx")
        )
        self.assertEqual(self.log.records[-1].levelno, logging.WARNING)

    def test_overrideComponents(self):
        setSite(self.portal)
        site_manager = getSiteManager()
        utility = HiddenProfiles()
        with overrideComponents() as components:
            components.registerUtility(utility, INonInstallable, name="tests")
            self.assertIs(queryUtility(INonInstallable, name="tests"), utility)
            self.assertIsNot(aq_base(getSiteManager()), aq_base(site_manager))
        self.assertIsNone(queryUtility(INonInstallable, name="tests"))
        self.assertIs(aq_base(getSiteManager()), aq_base(site_manager))
