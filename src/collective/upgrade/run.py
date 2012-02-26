import os
import sys
import logging
import time
import pprint
import pdb

import ZODB.serialize
from zodbupdate import update
import zodbupdate.main

from AccessControl import SpecialUsers
from AccessControl.SecurityManagement import newSecurityManager
from Testing.ZopeTestCase.utils import makerequest

from collective.upgrade import interfaces
from collective.upgrade import utils


class UpgradeRunner(utils.Upgrader):

    def __init__(self, app):
        self.app = app = makerequest(app)
        self.upgrader = interfaces.IUpgrader(app)

    def __call__(self):
        newSecurityManager(None, SpecialUsers.system)
        self.upgrader()
        self.updateZODB()

    def updateZODB(self):
        """Use zodbupdate to update persistent objects from module aliases"""
        self.commit(self.app)
        storage = self.app._p_jar.db().storage

        self.log('Packing ZODB in %r' % storage)
        storage.pack(time.time(), ZODB.serialize.referencesf)

        updater = update.Updater(storage)
        self.log('Updating ZODB in %r' % storage)
        updater()
        implicit_renames = updater.processor.get_found_implicit_rules()
        self.log('zodbupdate found new rules: %s' %
                 pprint.pformat(implicit_renames))


def main():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    stdout_handler = root.handlers[0]
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(zodbupdate.main.duplicate_filter)
    root.addHandler(logging.FileHandler(
        os.path.join('var', 'log', 'upgrade.log'), mode='w'))
    runner = UpgradeRunner(app)
    try:
        runner()
    except:
        runner.logger.exception('Exception running the upgrades.')
        pdb.post_mortem(sys.exc_info()[2])
        raise


if __name__ == '__main__':
    main()
        
