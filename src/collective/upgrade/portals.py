from collective.upgrade import interfaces
from collective.upgrade import utils


class PortalsUpgrader(utils.Upgrader):
    """Upgrades multiple portals in an instance."""

    def upgrade(self, paths=[]):
        if paths:
            upgraders = (
                interfaces.IUpgrader(self.app.restrictedTraverse(path))
                for path in paths)
        else:
            upgraders = self.walkUpgraders(self.context)
                            
        for upgrader in upgraders:
            upgrader.upgrade()

    def walkUpgraders(self, context):
        for obj in context.objectValues():
            upgrader = obj.restrictedTraverse(
                '@@collective.upgrade.form', None)
            if upgrader is not None:
                yield upgrader
