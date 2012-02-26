import logging

import transaction

from zope import interface
from zope.publisher import browser

from collective.upgrade import interfaces


class Upgrader(browser.BrowserView):
    interface.implements(interfaces.IUpgrader)

    logger = logging.getLogger('collective.upgrade')
    log_level = logging.INFO
    log_template = '{context}: {msg}'

    def __init__(self, context, request=None):
        super(Upgrader, self).__init__(context, request)

    def __call__(self):
        """Do the actual upgrade work."""
        if self.request.form.get('submitted'):
            self.upgrade()
        return super(Upgrader, self).__call__()

    def upgrade(self):
        raise NotImplemented('Subclasses should override "__call__()"')

    def log(self, msg, level=None, template=None):
        """Log a message using per-upgrader template and level."""
        if level is None:
            level = self.log_level
        if template is None:
            template = self.log_template
        msg = template.format(msg=msg, **self.__dict__)
        self.logger.log(level, msg)

    def commit(self):
        """Commit and log a message"""
        self.log('Committing transaction')
        transaction.commit()
