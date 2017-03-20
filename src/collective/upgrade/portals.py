from zope.component.hooks import setSite
from collective.upgrade import utils


class PortalsUpgrader(utils.Upgrader):
    """Upgrades multiple portals in an instance."""

    def upgrade(self, paths=[], **kw):
        if paths:
            upgraders = (
                self.context.restrictedTraverse(
                    path+'/@@collective.upgrade.form')
                for path in paths)
            self.log('Upgrading portals: %r' % paths)
        else:
            upgraders = self.walkUpgraders(self.context)
            self.log('Upgrading all portals')

        for upgrader in upgraders:
            setSite(upgrader.context)
            # initialize portal_skins
            upgrader.context.setupCurrentSkin(self.context.REQUEST)
            # setup language
            upgrader.context.portal_languages(upgrader.context, self.context.REQUEST)
            # Get Plone site object from Zope application server root
            upgrader.upgrade(**kw)

    def walkUpgraders(self, context):
        for obj in context.objectValues():
            upgrader = obj.restrictedTraverse(
                '@@collective.upgrade.form', None)
            if upgrader is not None:
                yield upgrader
