# encoding: utf-8

from zope import interface
from zope import component

from Products.CMFCore.utils import getToolByName

from Products.CMFPlone import interfaces as plone_ifaces

from collective.upgrade import upgrader

_marker = object()


@interface.implementer(plone_ifaces.INonInstallable)
class HiddenProfiles(object):
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
            u"collective.upgrade:blank",
        ]


@component.adapter(plone_ifaces.IPloneSiteRoot)
class PloneUpgrader(upgrader.PortalUpgrader):

    RESOURCE_TOOLS = {'portal_css', 'portal_javascripts', 'portal_kss'}

    def upgrade(self, **kw):
        # May fix the profile version
        migration = getToolByName(self.context, 'portal_migration')
        migration.getInstanceVersion()

        result = super(PloneUpgrader, self).upgrade(**kw)

        # BBB Support for Plone < 5.2
        resource_tools_exist = False
        for resource_tool_id in self.RESOURCE_TOOLS:
            resource_tool = getToolByName(self.context, resource_tool_id, None)
            if resource_tool is not None:
                resource_tool.cookResources()
                resource_tools_exist = True
        if resource_tools_exist:
            self.log('Refreshed resource registries for {0}'.format(
                self.context))

        return result

    def upgradeProfile(self, profile_id,
                       enable_link_integrity_checks=_marker, **kw):
        upgradeProfile = super(PloneUpgrader, self).upgradeProfile

        properties = getToolByName(self.context, 'portal_properties')
        orig = properties.site_properties.getProperty(
            'enable_link_integrity_checks', _marker)
        if enable_link_integrity_checks is not _marker:
            properties.site_properties.manage_changeProperties(
                enable_link_integrity_checks=enable_link_integrity_checks)
        try:
            upgradeProfile(profile_id, **kw)
        finally:
            if enable_link_integrity_checks is not _marker:
                if orig is _marker:
                    properties.site_properties._delPropValue(
                        enable_link_integrity_checks)
                elif hasattr(properties, 'site_properties'):
                    properties.site_properties.manage_changeProperties(
                        enable_link_integrity_checks=orig)

    def isProfileInstalled(self, profile_id):
        installed = super(PloneUpgrader, self).isProfileInstalled(profile_id)
        if installed:
            return installed

        product, profile = profile_id.split(':', 1)
        qi = getToolByName(self.context, 'portal_quickinstaller')
        if product.startswith('Products.'):
            product = product[len('Products.'):]
        return qi.isProductInstalled(product)
