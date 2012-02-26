import logging

import transaction


class Upgrader(object):

    logger = logging.getLogger('collective.upgrade')
    log_level = logging.INFO
    log_template = '{context}: {msg}'

    def __init__(self, context):
        self.context = context

    def __call__(self):
        """Do the actual upgrade work."""
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
