# -*- coding: utf-8 -*-
import io
import tarfile
import unittest

from Products.GenericSetup.interfaces import IBody
from zope.component import queryMultiAdapter

from collective.upgrade.testing import COLLECTIVE_UPGRADE_INTEGRATION_TESTING

try:
    from Products.GenericSetup.context import SetupEnviron
    from Products.ResourceRegistries.exportimport.cssregistry import \
        CSSRegistryNodeAdapter
    from Products.ResourceRegistries.exportimport.jsregistry import \
        JSRegistryNodeAdapter

    from collective.upgrade import resourceregistries
except ImportError:  # Plone 5.2+
    resourceregistries = None


def exported(result, filename):
    tarball = tarfile.open(fileobj=io.BytesIO(result["tarball"]))
    return tarball.extractfile(filename).read().decode("utf-8")


@unittest.skipIf(
    resourceregistries is None, "Products.ResourceRegistries is not installed (Plone 5.2+)"
)
class TestResourceRegistries(unittest.TestCase):

    layer = COLLECTIVE_UPGRADE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.setup = self.portal.portal_setup

    def test_overrideCSSRegistryNodeAdapter(self):
        with resourceregistries.overrideCSSRegistryNodeAdapter():
            adapter = queryMultiAdapter((self.portal.portal_css, SetupEnviron()), IBody)
        self.assertIsInstance(adapter, CSSRegistryNodeAdapter)

    def test_exportBBBCSSRegistry(self):
        result = self.setup.runExportStep("cssregistry-bbb")
        xml = exported(result, "cssregistry-bbb.xml")
        self.assertIn('<object name="portal_css" meta_type="Stylesheets Registry"', xml)
        self.assertIn('<stylesheet ', xml)

    def test_importBBBCSSRegistry(self):
        css = self.portal.portal_css
        self.assertTrue(css.getResources())
        # the blank profile, purging: resets the registry
        self.setup.runImportStepFromProfile(
            "profile-collective.upgrade:blank", "cssregistry-bbb", purge_old=True
        )
        self.assertEqual(list(css.getResources()), [])

    def test_overrideJSRegistryNodeAdapter(self):
        with resourceregistries.overrideJSRegistryNodeAdapter():
            adapter = queryMultiAdapter(
                (self.portal.portal_javascripts, SetupEnviron()), IBody
            )
        self.assertIsInstance(adapter, JSRegistryNodeAdapter)

    def test_exportBBBJSRegistry(self):
        result = self.setup.runExportStep("jsregistry-bbb")
        xml = exported(result, "jsregistry-bbb.xml")
        self.assertIn('<object name="portal_javascripts" meta_type="JavaScripts Registry"', xml)
        self.assertIn('<javascript ', xml)

    def test_importBBBJSRegistry(self):
        js = self.portal.portal_javascripts
        self.assertTrue(js.getResources())
        self.setup.runImportStepFromProfile(
            "profile-collective.upgrade:blank", "jsregistry-bbb", purge_old=True
        )
        self.assertEqual(list(js.getResources()), [])
