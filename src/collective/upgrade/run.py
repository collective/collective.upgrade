import sys
import logging
import time
import pprint
import optparse
import pdb

import transaction
import ZODB.serialize
from zodbupdate import update
import zodbupdate.main

from collective.upgrade import interfaces
from collective.upgrade import utils


parser = optparse.OptionParser()
parser.add_option(
    "-l", "--log-file", metavar="FILE", default='upgrade.log',
    help="Log upgrade messages, filterd for duplicates, to FILE")
parser.add_option(
    "-p", "--portal-path", metavar="PATH", action="append",
    help="Run upgrades for the portals at the given paths only.  "
    "May be given multiple times to specify multiple portals.  "
    "If not given, all CMF portals in the Zope app will be upgraded.")
parser.add_option(
    "-z", "--zope-conf", metavar="FILE",
    help='The "zope.conf" FILE to use when starting the Zope2 app. '
    'Can be omitted when used as a zopectl "run" script.')


class UpgradeRunner(utils.Upgrader):

    def __init__(self, app, options):
        from Testing.makerequest import makerequest
        self.app = app = makerequest(app)
        self.upgrader = interfaces.IMultiPortalUpgrader(app)
        self.options = options

    def __call__(self):
        from AccessControl import SpecialUsers
        from AccessControl.SecurityManagement import newSecurityManager
        newSecurityManager(None, SpecialUsers.system)

        self.upgrader(self.options.portal_path)
        self.updateZODB()

    def updateZODB(self):
        """Use zodbupdate to update persistent objects from module aliases"""
        self.commit()
        storage = self.app._p_jar.db().storage

        self.log('Packing ZODB in %r' % storage)
        storage.pack(time.time(), ZODB.serialize.referencesf)

        updater = update.Updater(storage)
        self.log('Updating ZODB in %r' % storage)
        updater()
        implicit_renames = updater.processor.get_found_implicit_rules()
        self.log('zodbupdate found new rules: %s' %
                 pprint.pformat(implicit_renames))


def main(app=None, args=None):
    options, args = parser.parse_args(args)
    if args:
        parser.error('Unrecognized args given: %r' % args)

    if app is None:
        import Zope2
        from App import config
        if config._config is None:
            if not options.zope_conf:
                parser.error(
                    'Must give the "--zope-conf" option when not used as a '
                    'zopectl "run" script.')
            Zope2.configure(options.zope_conf)
        app = Zope2.app()
    elif options.zope_conf:
        parser.error(
            'Do not give the "--zope-conf" option when used as a '
            'zopectl "run" script.')

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    stderr_handler, = [h for h in root.handlers
                       if getattr(h, 'stream', None) is sys.__stderr__]
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.addFilter(zodbupdate.main.duplicate_filter)

    log_file = logging.FileHandler(options.log_file)
    formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            "%Y-%m-%d %H:%M:%S")
    log_file.setFormatter(formatter)
    root.addHandler(log_file)

    runner = UpgradeRunner(app, options)
    try:
        runner()
    except:
        transaction.abort()
        runner.logger.exception('Exception running the upgrades.')
        pdb.post_mortem(sys.exc_info()[2])
        raise


if __name__ == '__main__':
    try:
        main(app)
    except NameError:
        main()
