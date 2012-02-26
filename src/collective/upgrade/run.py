import os
import sys
import logging
import pdb

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
        
