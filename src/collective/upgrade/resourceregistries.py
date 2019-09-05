"""
BBB support for ResourceRegistries to be removed when support is deprecated.
"""

import os
import contextlib

from Products.GenericSetup import interfaces as setup_ifaces

from Products.ResourceRegistries import interfaces as res_ifaces
from Products.ResourceRegistries.exportimport import resourceregistry
from Products.ResourceRegistries.exportimport import cssregistry
from Products.ResourceRegistries.exportimport import jsregistry

from collective.upgrade import utils


@contextlib.contextmanager
def overrideCSSRegistryNodeAdapter():
    """
    Temporarily override the CSS registry import/export adapter.
    """
    with utils.overrideComponents() as components:
        yield components.registerAdapter(
            factory=cssregistry.CSSRegistryNodeAdapter,
            required=(res_ifaces.ICSSRegistry, setup_ifaces.ISetupEnviron),
            provided=setup_ifaces.IBody)


@contextlib.contextmanager
def overrideJSRegistryNodeAdapter():
    """
    Temporarily override the JS registry import/export adapter.
    """
    with utils.overrideComponents() as components:
        yield components.registerAdapter(
            factory=jsregistry.JSRegistryNodeAdapter,
            required=(res_ifaces.IJSRegistry, setup_ifaces.ISetupEnviron),
            provided=setup_ifaces.IBody)


CSS_FILENAME = os.path.splitext(cssregistry._FILENAME)
CSS_FILENAME = ''.join((CSS_FILENAME[0] + '-bbb', CSS_FILENAME[1]))
CSS_REG_TITLE = ' BBB '.join(cssregistry._REG_TITLE.rsplit(' ', 1))


def importBBBCSSRegistry(context):
    """
    Import deprecated CSS registry storage.

    Useful to clear or otherwise manage the pre-registry resource
    registration method.
    """
    with overrideCSSRegistryNodeAdapter():
        return resourceregistry.importResRegistry(
            context, cssregistry._REG_ID, CSS_REG_TITLE, CSS_FILENAME)


def exportBBBCSSRegistry(context):
    """
    Export deprecated CSS registry storage.
    """
    with overrideCSSRegistryNodeAdapter():
        return resourceregistry.exportResRegistry(
            context, cssregistry._REG_ID, CSS_REG_TITLE, CSS_FILENAME)


JS_FILENAME = os.path.splitext(jsregistry._FILENAME)
JS_FILENAME = ''.join((JS_FILENAME[0] + '-bbb', JS_FILENAME[1]))
JS_REG_TITLE = ' BBB '.join(jsregistry._REG_TITLE.rsplit(' ', 1))


def importBBBJSRegistry(context):
    """
    Import deprecated javascript registry storage.

    Useful to clear or otherwise manage the pre-registry resource
    registration method.
    """
    with overrideJSRegistryNodeAdapter():
        return resourceregistry.importResRegistry(
            context, jsregistry._REG_ID, JS_REG_TITLE, JS_FILENAME)


def exportBBBJSRegistry(context):
    """
    Export deprecated javascript registry storage.
    """
    with overrideJSRegistryNodeAdapter():
        return resourceregistry.exportResRegistry(
            context, jsregistry._REG_ID, JS_REG_TITLE, JS_FILENAME)
