# encoding: utf-8

import sys
import logging
import argparse
import pdb  # noqa

import transaction
import zodbupdate.main

from collective.upgrade import utils


parser = argparse.ArgumentParser(
    description='Upgrade CMF portals in a Zope 2 application '
    'using GenericSetup upgrade steps')
parser.add_argument(
    "-l", "--log-file", metavar="FILE", default='upgrade.log',
    help="Log upgrade messages, filtered for duplicates, to FILE")
parser.add_argument(
    "-z", "--zope-conf", metavar="FILE",
    help='The "zope.conf" FILE to use when starting the Zope2 app. '
    'Can be omitted when used as a zopectl "run" script.')
parser.add_argument(
    "-d", "--disable-link-integrity", action="store_true",
    help='When upgrading a portal using plone.app.linkintegrity, '
    'disable it during the upgrade.')
parser.add_argument(
    "-u", "--username", help='Specify username to use during the upgrade '
    '(if not provided, a special user will run the upgrade).')

group = parser.add_argument_group('upgrades')
group.add_argument(
    '-U', '--skip-portal-upgrade', action='store_false', dest='upgrade_portal',
    help='Skip running the upgrade steps for the core Plone baseline profile.')
group.add_argument(
    '-G', '--upgrade-profile', metavar='PROFILE_ID',
    action='append', dest='upgrade_profiles',
    help='Run all upgrade steps for the given profile '
    '(default: upgrade all installed extension profiles)')
group.add_argument(
    '-A', '--skip-all-profiles-upgrade',
    action='store_false', dest='upgrade_all_profiles',
    help='Skip running all upgrade steps '
    'for all installed extension profiles.')

parser.add_argument(
    'portal_paths', metavar='PATH', nargs='*',
    help='Run upgrades for the portals at the given paths only '
    '(default: upgrade all CMF portals in the Zope app)')


def main(app=None, args=None):
    full_args = args
    if args is not None:
        full_args = args + sys.argv[1:]
    args = parser.parse_args(full_args)

    if args.upgrade_profiles:
        args.upgrade_all_profiles = False
    elif not (args.upgrade_portal or args.upgrade_all_profiles):
        parser.error('The supplied options would not upgrade any profiles')

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

    kw = dict(
        paths=args.portal_paths,
        upgrade_portal=args.upgrade_portal,
        upgrade_all_profiles=args.upgrade_all_profiles,
        upgrade_profiles=args.upgrade_profiles)
    if args.disable_link_integrity:
        kw['enable_link_integrity_checks'] = False

    # setup user and REQUEST
    from AccessControl.SecurityManagement import newSecurityManager
    from Testing.makerequest import makerequest
    if args.username:
        acl_users = app.acl_users
        user = acl_users.getUser(args.username)
        if user:
            user = user.__of__(acl_users)
    else:
        from AccessControl import SpecialUsers
        user = SpecialUsers.system

    newSecurityManager(None, user)
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
