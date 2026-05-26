from collective.upgrade import upgrader
from plone.base import interfaces as plone_ifaces
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope import component
from zope import interface

_marker = object()


@interface.implementer(plone_ifaces.INonInstallable)
class HiddenProfiles:
    """
    Exclude utility or upgrade profiles on the Plone add-on control panel.
    """

    def getNonInstallableProducts(self):  # pragma: no cover
        """
        No general packages all of whose profiles to exclude.
        """
        return []

    def getNonInstallableProfiles(self):  # pragma: no cover
        """
        Exclude utility or upgrade profiles on the Plone add-on control panel.
        """
        return [
            "collective.upgrade:blank",
        ]


@component.adapter(plone_ifaces.IPloneSiteRoot)
class PloneUpgrader(upgrader.PortalUpgrader):

    def upgrade(self, **kw):
        # May fix the profile version
        migration = getToolByName(self.context, "portal_migration")
        migration.getInstanceVersion()

        return super().upgrade(**kw)

    def upgradeProfile(self, profile_id, enable_link_integrity_checks=_marker, **kw):
        upgradeProfile = super().upgradeProfile

        registry = component.getUtility(IRegistry)
        orig = registry.get("plone.enable_link_integrity_checks", _marker)
        if enable_link_integrity_checks is not _marker:
            registry["plone.enable_link_integrity_checks"] = (
                enable_link_integrity_checks
            )
        try:
            upgradeProfile(profile_id, **kw)
        finally:
            if enable_link_integrity_checks is not _marker:
                registry["plone.enable_link_integrity_checks"] = orig

    def isProfileInstalled(self, profile_id):
        installed = super().isProfileInstalled(profile_id)
        if installed:
            return installed

        product, profile = profile_id.split(":", 1)
        if product.startswith("Products."):
            product = product[len("Products.") :]
        installer = get_installer(self.context, self.request)
        return installer.is_product_installed(product)
