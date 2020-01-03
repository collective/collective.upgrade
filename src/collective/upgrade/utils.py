# encoding: utf-8

import contextlib
import logging
import transaction

from zope import globalrequest
from zope import interface
from zope.component import hooks
from zope.publisher import browser

import zodbupdate.main

from Acquisition import aq_base
from ZPublisher import utils

from collective.upgrade import interfaces

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S")
logger = logging.getLogger('collective.upgrade')


@interface.implementer(interfaces.IUpgrader)
class Upgrader(browser.BrowserView):

    logger = logger
    log_level = logging.INFO
    log_template = '{context}: {msg}'

    def __init__(self, context, request=None):
        super(Upgrader, self).__init__(context, request)

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
        raise NotImplementedError('Subclasses should override "__call__()"')

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
        transaction_note(self.context, self.request, note)
        transaction.commit()


def transaction_note(context, request=None, note=None):
    """Don't add a transaction note if it would exceed the maximum length."""
    if request is None:
        request = globalrequest.getRequest()

    logger.info(note)
    utils.recordMetaData(context, request)
    if note is not None:
        t = transaction.get()
        if (len(t.description) + len(note)) >= 65533:
            logger.warning(
                'Transaction note too large omitting {0!r}'.format(
                    str(note)))
        else:
            t.note(str(note))


@contextlib.contextmanager
def overrideComponents(obj=None):
    """
    Temporarily override the site manager components registry.

    Useful for registering components that should only be used inside a certain
    block of code.
    """
    from five.localsitemanager import registry

    if obj is None:
        obj = hooks.getSite()

    # Create a new component registry that uses the existing one as its base
    next = obj.getSiteManager()
    components = registry.PersistentComponents('++etc++site', bases=(next,))
    obj.setSiteManager(components)
    components.__parent__ = aq_base(obj)

    # Install the new registry and site
    hooks.setSite(obj)

    # Make the registry available to the calling code
    yield components

    # Restore the previous site manager
    obj.setSiteManager(next)
    hooks.setSite(obj)
