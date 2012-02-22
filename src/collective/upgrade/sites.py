from zope.component import hooks

from collective.upgrade import interfaces


class SitesUpgrader(object):
    """Upgrades multiple sites in an instance."""

    def __call__(self, sites=None):
        if sites is None:
            sites = self.listSites()
            
        for site in sites:
            hooks.setSite(site)
            upgrader = interfaces.IUpgrader(site)
            self.log('Upgrading {0}'.format(site))
            upgrader()
            self.log('Upgraded {0}'.format(site))
