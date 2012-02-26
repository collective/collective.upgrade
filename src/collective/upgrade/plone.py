from zope import component

from Products.CMFCore.utils import getToolByName

from Products.CMFPlone import interfaces as plone_ifaces

from collective.upgrade import upgrader


class PloneUpgrader(upgrader.PortalUpgrader):
    component.adapts(plone_ifaces.IPloneSiteRoot)

    def __call__(self):
        # May fix the profile version
        migration = getToolByName(self.context, 'portal_migration')
        migration.getInstanceVersion()

        return super(PloneUpgrader, self).__call__()

    def isProfileInstalled(self, profile_id):
        installed = super(PloneUpgrader, self).isProfileInstalled(profile_id)
        if installed:
            return installed

        product, profile = profile_id.split(':', 1)
        qi = getToolByName(self.portal, 'portal_quickinstaller')
        return qi.isProductInstalled(product)
