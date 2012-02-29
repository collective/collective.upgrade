import logging

from zope import interface
from zope.publisher import browser

import zodbupdate.main

import Zope2

from collective.upgrade import interfaces

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S")


class Upgrader(browser.BrowserView):
    interface.implements(interfaces.IUpgrader)

    logger = logging.getLogger('collective.upgrade')
    log_level = logging.INFO
    log_template = '{context}: {msg}'

    def __init__(self, context, request=None):
        super(Upgrader, self).__init__(context, request)
        self.tm = Zope2.zpublisher_transactions_manager

    def __call__(self):
        """Do the actual upgrade work."""
        if self.request.form.pop('submitted'):
            self.request.response.setHeader('Content-Type', 'text/plain')
            handler = logging.StreamHandler(self.request.response)
            handler.addFilter(zodbupdate.main.duplicate_filter)
            handler.setFormatter(formatter)
            root = logging.getLogger()
            root.addHandler(handler)
            try:
                self.upgrade(**self.request.form)
            finally:
                root.removeHandler(handler)
            return self.request.response
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
        self.tm.recordMetaData(self.context, self.request)
        self.tm.commit()
