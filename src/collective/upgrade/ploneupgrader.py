from collective.upgrade import upgrader
from plone.base import interfaces as plone_ifaces
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope import component
from zope import interface
from zope.component import getUtility

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

    RESOURCE_TOOLS = {"portal_css", "portal_javascripts", "portal_kss"}

    def upgrade(self, **kw):
        # May fix the profile version
        migration = getToolByName(self.context, "portal_migration")
        migration.getInstanceVersion()

        result = super().upgrade(**kw)

        # BBB Support for Plone < 5.2
        resource_tools_exist = False
        for resource_tool_id in self.RESOURCE_TOOLS:
            resource_tool = getToolByName(self.context, resource_tool_id, None)
            if resource_tool is not None:
                resource_tool.cookResources()
                resource_tools_exist = True
        if resource_tools_exist:
            self.log(f"Refreshed resource registries for {self.context}")

        return result

    def upgradeProfile(self, profile_id, enable_link_integrity_checks=_marker, **kw):
        upgradeProfile = super().upgradeProfile

        registry = getUtility(IRegistry)
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
