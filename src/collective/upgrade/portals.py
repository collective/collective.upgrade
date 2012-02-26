from zope.component import hooks

from collective.upgrade import interfaces
from collective.upgrade import utils


class PortalsUpgrader(utils.Upgrader):
    """Upgrades multiple portals in an instance."""

    def __call__(self, paths=[]):
        if paths:
            upgraders = (
                interfaces.IUpgrader(self.app.restrictedTraverse(path))
                for path in paths)
        else:
            upgraders = self.walkUpgraders(self.context)
                            
        for upgrader in upgraders:
            portal = upgrader.context
            hooks.setPortal(portal)
            self.log('Upgrading {0}'.format(portal))
            upgrader()
            self.log('Upgraded {0}'.format(portal))

    def walkUpgraders(self, context):
        upgrader = interfaces.IUpgrader(context, None)
        if upgrader is not None:
            yield upgrader
        elif ofs_ifaces.IObjectManager.providedBy(context):
            for obj in context.objectValues():
                for upgrader in self.walkUpgraders(obj)
