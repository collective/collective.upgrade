import sys
import logging
import argparse
import pdb

import transaction
import zodbupdate.main

from collective.upgrade import utils


parser = argparse.ArgumentParser()
parser.add_argument(
    "-l", "--log-file", metavar="FILE", default='upgrade.log',
    help="Log upgrade messages, filtered for duplicates, to FILE")
parser.add_argument(
    "-p", "--portal-path", metavar="PATH", action="append",
    help="Run upgrades for the portals at the given paths only.  "
    "May be given multiple times to specify multiple portals.  "
    "If not given, all CMF portals in the Zope app will be upgraded.")
parser.add_argument(
    "-z", "--zope-conf", metavar="FILE",
    help='The "zope.conf" FILE to use when starting the Zope2 app. '
    'Can be omitted when used as a zopectl "run" script.')
parser.add_argument(
    "-d", "--disable-link-integrity", action="store_true",
    help='When upgrading a portal using plone.app.linkintegrity, '
    'disable it during the upgrade.')


def main(app=None, args=None):
    full_args = args
    if args is not None:
        full_args = args + sys.argv[1:]
    args = parser.parse_args(full_args)

    if app is None:
        import Zope2
        from App import config
        if config._config is None:
            if not args.zope_conf:
                parser.error(
                    'Must give the "--zope-conf" option when not used as a '
                    'zopectl "run" script.')
            Zope2.configure(args.zope_conf)
        app = Zope2.app()
    elif args.zope_conf:
        parser.error(
            'Do not give the "--zope-conf" option when used as a '
            'zopectl "run" script.')

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    stderr_handler, = [h for h in root.handlers
                       if getattr(h, 'stream', None) is sys.__stderr__]
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.addFilter(zodbupdate.main.duplicate_filter)

    log_file = logging.FileHandler(args.log_file)
    log_file.addFilter(zodbupdate.main.duplicate_filter)
    log_file.setFormatter(utils.formatter)
    root.addHandler(log_file)

    kw = dict(paths=args.portal_paths)
    if args.disable_link_integrity:
        kw['enable_link_integrity_checks'] = False

    from AccessControl import SpecialUsers
    from AccessControl.SecurityManagement import newSecurityManager
    newSecurityManager(None, SpecialUsers.system)
    from Testing.makerequest import makerequest
    app = makerequest(app)

    runner = app.restrictedTraverse('@@collective.upgrade.form')
    try:
        runner.upgrade(**kw)
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
