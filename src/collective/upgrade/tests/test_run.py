# -*- coding: utf-8 -*-
import io
import logging
import os
import shutil
import sys
import tempfile
import unittest

from AccessControl.SecurityManagement import getSecurityManager
from persistent.list import PersistentList
from plone.app.testing import SITE_OWNER_NAME
from zodbupdate.main import duplicate_filter
from zope.testing.loggingsupport import InstalledHandler

from collective.upgrade import run
from collective.upgrade.testing import COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING
from collective.upgrade.tests.helpers import messages
from collective.upgrade.tests.upgrades import (CHECKER_PROFILE_ID, PROFILE_ID,
                                               runs)


class TestRun(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.setup = self.portal.portal_setup
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        self.log_file = os.path.join(tmpdir, "upgrade.log")
        # main() expects the stderr handler of a Zope instance
        root = logging.getLogger()
        self.addCleanup(self.restore_logging, root.level, list(root.handlers))
        root.addHandler(logging.StreamHandler(sys.__stderr__))
        duplicate_filter.seen.clear()
        self.log = InstalledHandler("collective.upgrade")
        self.addCleanup(self.log.uninstall)
        self.argv = sys.argv
        self.addCleanup(setattr, sys, "argv", self.argv)

    def restore_logging(self, level, handlers):
        root = logging.getLogger()
        root.setLevel(level)
        for handler in list(root.handlers):
            if handler not in handlers:
                root.removeHandler(handler)
                handler.close()

    def read_log(self):
        with io.open(self.log_file, encoding="utf-8") as log_file:
            return log_file.read()

    def test_main(self):
        portal = str(self.portal)
        # every portal, as the system user
        run.main(self.app, ["-l", self.log_file])
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        self.assertEqual(getSecurityManager().getUser().getUserName(), "System Processes")
        log = messages(self.log)
        self.assertIn("{0}: Upgrading all portals".format(self.app), log)
        self.assertIn("{0}: Upgraded {0}".format(portal), log)
        # the log file stays empty: it shares the duplicate filter of the stderr
        # handler, which gets every message first
        self.assertEqual(self.read_log(), "")
        # -U -G: only the given profile, as the given user, without link integrity
        self.setup.setLastVersionForProfile(PROFILE_ID, "1")
        self.portal._upgrade_test_runs = PersistentList()
        self.log.clear()
        run.main(
            self.app,
            ["-l", self.log_file, "-U", "-G", PROFILE_ID, "-u", SITE_OWNER_NAME, "-d", "plone"],
        )
        self.assertEqual(
            [checks for step, version, checks in runs(self.portal)], [False, False, False]
        )
        self.assertEqual(getSecurityManager().getUser().getUserName(), SITE_OWNER_NAME)
        log = messages(self.log)
        self.assertEqual(log[0], "{0}: Upgrading portals: ['plone']".format(self.app))
        self.assertNotIn("Products.CMFPlone:plone", " ".join(log))
        # an exception aborts the transaction, is logged and raised
        self.setup.setLastVersionForProfile(CHECKER_PROFILE_ID, "1")
        with self.assertRaises(ValueError):
            run.main(self.app, ["-l", self.log_file, "-G", CHECKER_PROFILE_ID])
        self.assertNotIn("checker", [step for step, version, checks in runs(self.portal)])
        self.assertEqual(self.log.records[-1].getMessage(), "Exception running the upgrades.")
        self.assertEqual(self.log.records[-1].levelno, logging.ERROR)
        self.assertIs(self.log.records[-1].exc_info[0], ValueError)
        # options that would not upgrade anything, --zope-conf with an app
        with self.assertRaises(SystemExit):
            run.main(self.app, ["-l", self.log_file, "-U", "-A"])
        with self.assertRaises(SystemExit):
            run.main(self.app, ["-l", self.log_file, "-z", "zope.conf"])

    def test_run(self):
        # bin/instance run bin/run-portal-upgrades [options]
        sys.argv = ["bin/instance", "run", "bin/run-portal-upgrades", "-l", self.log_file]
        run.run(self.app)
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("3",))
        self.assertIn("{0}: Upgrading all portals".format(self.app), messages(self.log))
        self.setup.setLastVersionForProfile(PROFILE_ID, "1")
        run.run(self.app, ["-l", self.log_file, "-A"])
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE_ID), ("1",))
