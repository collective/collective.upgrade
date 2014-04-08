import logging

import transaction

from zope import interface
from zope.publisher import browser
from zope import globalrequest

import zodbupdate.main

import Zope2

from collective.upgrade import interfaces

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S")
logger = logging.getLogger('collective.upgrade')


class Upgrader(browser.BrowserView):
    interface.implements(interfaces.IUpgrader)

    logger = logger
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

    def commit(self, note='Checkpointing upgrade'):
        """Commit with a transaction note and log a message."""
        transaction_note(self.context, self.request, note, self.tm)
        self.tm.commit()


def transaction_note(
        context, request=None, note=None, tm=None):
    """Don't add a transaction note if it would exceed the maximum length."""
    if request is None:
        request = globalrequest.getRequest()
    if tm is None:
        tm = Zope2.zpublisher_transactions_manager

    logger.info(note)
    tm.recordMetaData(context, request)
    if note is not None:
        t = transaction.get()
        if (len(t.description) + len(note)) >= 65533:
            logger.warning(
                'Transaction note too large omitting {0!r}'.format(
                    str(note)))
        else:
            t.note(str(note))
