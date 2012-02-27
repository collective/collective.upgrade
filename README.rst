collective.upgrade
==================

This package provides helpers for upgrading CMF portals, such as Plone
sites, supporting incremental commits, upgrading multiple portals at
once, and a command-line script for upgrading scripts outside the
browser.

Quick Start
-----------

In a buildout with::

    [instance1]
    recipe = plone.recipe.zope2instance
    eggs = ...

Add another part like so::

    parts =
        ...
        zopepy
    ...

    [zopepy]
    recipe = zc.recipe.egg
    eggs =
        ${instance1:eggs}
        collective.upgrade
    interpreter = zopepy

    ...

Then, after running buildout, you can upgrade all Plone portals and
their add-ons with::

    $ bin/upgrade-portals --zope-conf=parts/instance1/etc/zope.conf --log-file=var/log/upgrade.log

Use the `--help` option for more details::

    $ bin/upgrade-portals --help
    Usage: upgrade-portals [options]
    
    Options:
      -h, --help            show this help message and exit
      -l FILE, --log-file=FILE
                            Log upgrade messages, filterd for duplicates, to FILE
      -p PATH, --portal-path=PATH
                            Run upgrades for the portals at the given paths only.
                            May be given multiple times to specify multiple portals.
                            If not given, all CMF portals in the Zope app will be
                            upgraded.
      -z FILE, --zope-conf=FILE
                            The "zope.conf" FILE to use when starting the Zope2 app.
                            Can be omitted when used as a zopectl "run" script.

Incremental Commits
-------------------

Since upgrades are often long running, restarting the upgrade on every
error can make troubleshooting and debugging extremely time
consuming.  It's also unsafe, however, to commit the results of an
upgrade that failed in the middle since there's no way to guarantee of
cleanup the partial execution of an upgrade step.

Fortunately, the upgrade step support for `Products.GenericSetup`
profiles provides a good way to incrementally commit upgrade progress
in a way that much less risky and can save a lot of time in the
upgrade troubleshooting and debugging process.

The core of `collective.upgrade` is a form that supports incremental
upgrading of a portal using generic profiles.  Upgrade starts with
the portal's base profile and then proceeds to upgrade all the other
installed profiles.  While processing each profile, it commits at the
last successful profile version reached but aborting any set of
upgrade steps that did not succeed.

Multiple Portals
----------------

Another form supports upgrading multiple portals at once.  By default
the form will start at the form context and walk the Zope OFS object
tree applying the upgrade to each CMF portal found.  It is also
possible to specify the paths of the portals to upgrade.

It uses the same incremental commit support described above for each
portal and commits after each portal.

Command-line Script
-------------------

This package also provides a runnable script which can be installed
and used to run the multiple portal upgrade process without using the
browser.  This script also logs upgrade messages to a separate log
file filtering for duplicates to make the upgrade process much easier
to monitor and review for any unexpected issues.
