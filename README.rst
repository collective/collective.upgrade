collective.upgrade
==================

This package provides helpers for upgrading CMF portals, such as Plone
sites, supporting incremental commits, upgrading multiple portals at
once, and a command-line script for upgrading scripts outside the
browser with post-mortem debugging of errors.  Together, these
features greatly reduce the amount of time spent on each iteration of
developing your upgrade steps.

Also included are a number of upgrade steps for cleaning up messy
portals during upgrades including cleaning up broken objects,
components and registrations.

.. contents::

CAUTION
-------

Use of this package will immediately commit changes to your ZODB.
There is no "dry run" option as that is contrary to it's purpose.  As
such, it should *never* be used on a ZODB that has not been backed up
along with the BLOBs *immediately before* use.  Neither should it be
used directly on production as a first attempt at upgrading portals.  

Quick Start
-----------

In a buildout with::

    [instance1]
    recipe = plone.recipe.zope2instance
    eggs = ...

Add another part like so::

    parts =
        ...
        upgrade
    ...

    [instance1]
    ...
    eggs = ...
        collective.upgrade
    http-address = localhost:8080
    ...

    [upgrade]
    recipe = zc.recipe.egg
    eggs = ${instance1:eggs}
    scripts = upgrade-portals
    arguments = args=[
        '--zope-conf', '${instance1:location}/etc/zope.conf',
        '--log-file', '${buildout:directory}/var/log/upgrade.log']
    ...

Then, after running buildout, you can upgrade all Plone portals and
their add-ons and monitor the progress in ``var/log/upgrade.log`` with::

    $ bin/upgrade-portals

Alternatively, you can open the following URL in your browser to
upgrade all portals and the logs of progress will be streamed to
your browser::

    http://localhost:8080/@@collective.upgrade.form?submitted=1

Use the ``--help`` option for more details::

    $ bin/upgrade-portals --help
    usage: upgrade-portals [-h] [-l FILE] [-z FILE] [-d] [-U] [-G PROFILE_ID] [-A]
                           [PATH [PATH ...]]
    
    Upgrade CMF portals in a Zope 2 application using GenericSetup upgrade steps
    
    positional arguments:
      PATH                  Run upgrades for the portals at the given paths only
                            (default: upgrade all CMF portals in the Zope app)
    
    optional arguments:
      -h, --help            show this help message and exit
      -l FILE, --log-file FILE
                            Log upgrade messages, filtered for duplicates, to FILE
      -z FILE, --zope-conf FILE
                            The "zope.conf" FILE to use when starting the Zope2 app.
                            Can be omitted when used as a zopectl "run" script.
      -d, --disable-link-integrity
                            When upgrading a portal using plone.app.linkintegrity,
                            disable it during the upgrade.
      -u, --username
                            Specify username to use during the upgrade (if not
                            provided, a special user will run the upgrade).

    upgrades:
      -U, --skip-portal-upgrade
                            Skip running the upgrade steps for the core Plone
                            baseline profile.
      -G PROFILE_ID, --upgrade-profile PROFILE_ID
                            Run all upgrade steps for the given profile (default:
                            upgrade all installed extension profiles)
      -A, --skip-all-profiles-upgrade
                            Skip running all upgrade steps for all installed
                            extension profiles.


Incremental Commits
-------------------

Since upgrades are often long running, restarting the upgrade on every
error can make troubleshooting and debugging extremely time
consuming.  It's also unsafe, however, to commit the results of an
upgrade that failed in the middle since there's no way to guarantee of
cleanup the partial execution of an upgrade step.

Fortunately, the upgrade step support for ``Products.GenericSetup``
profiles provides a good way to incrementally commit upgrade progress
in a way that much less risky and can save a lot of time in the
upgrade troubleshooting and debugging process.

The core of ``collective.upgrade`` are upgrader classes which support
incremental upgrading of a portal using GenericSetup profiles.
Upgrade starts with the portal's base profile and then proceeds to
upgrade all the other installed profiles.  While processing each
profile, it commits at the last successful profile version reached but
aborting any set of upgrade steps that did not succeed.

In other words, each time a ``collective.upgrade`` upgrader runs, it
will pick up from the last successful profile version reached without
having to repeat what has already succeeded.

To use this upgrader you can simply visit the
``@@collective.upgrade.form?submitted=1`` view on the portal to
upgrade.  Alternatively, you can use the ``upgrade-portals`` console
script described in the `Quick Start`_ section.

Multiple Portals
----------------

Another form supports upgrading multiple portals at once.  By default
the form will start at the form context and walk the Zope OFS object
tree applying the upgrade to each CMF portal found.  It is also
possible to specify the paths of the portals to upgrade.

It uses the same incremental commit support described above for each
portal and commits after each portal and can also be run using the
``@@collective.upgrade.form?submitted=1`` view on the container of the
portals to upgrade or using the console script described in the `Quick
Start`_ section.

Command-line Script
-------------------

This package also provides a runnable script which can be installed
and used to run the multiple portal upgrade process without using the
browser.  The script logs upgrade messages to a separate log file
filtering for duplicates to make the upgrade process much easier to
monitor and review for any unexpected issues.  If the upgrade raises
an exception, the upgrader will abort the transaction and the console
script will invoke ``pdb.post_mortem()`` to allow inspecting the
error.  Together, these features make the console script a much faster
way to iterate through the development of an upgrade procedure.

Use the ``--help`` option of the script or see the  `Quick Start`_
section for details.

Reconciling Users and Groups
----------------------------

Reconcile users and groups between two PluggableAuthService plugins.
Useful, for example, to migrate users and groups from the local
storage plugins to an LDAP plugin added later.

#. The export steps search the destination plugins for users and
   groups that correspond to those in the source plugins.  Use real
   names for search when an exact match on id can't be found.

#. The export step writes a CSV file listing all users and groups from
   the source plugins including those that match exactly on id, those
   that found matches on real names, and those that found no matches.

   This CSV can be edited to add manual matches and can be used as a
   list of users to notify that their logins or passwords may change
   between the source and destination plugins.

#. The import step reads the same CSV file to update:

   * OFS ownership
   * CMF creators
   * local roles
   * group memberships

To use these steps, make sure the destination PAS plugin is the first
activated IUserEnumerationPlugin, IGroupEnumerationPlugin, and
IPropertiesPlugin plugin, then run the ``reconcile_users`` and
``reconcile_groups`` export steps.  The CSV files generated in the
export can then be edited and adjusted until they represent the
changes that should be applied at which point they can be placed
inside a GS import profile and imported to apply the changes.

Upgrade Steps
-------------

This package also registers additional upgrade steps for the Plone 3.*
to 4.0 upgrade which do the following:

  * cleanup broken OFS objects
  * cleanup broken TextIndexes objects
  * cleanup broken component registrations
  * cleanup broken setup registrations
  * cleanup broken cmfeditions versions
  * migrate cmfeditions folder versions to btrees
  * cleanup duplicate UIDs

Registered for the 3.* to 4.0 upgrade by default, these steps can be
registered for any upgrade you might need them for.  If you find that
a particular Plone upgrade is helped by registering one of the
existing steps or a new step, let me know and I'll likely add it to
the registrations in this package.

Including ``experimental.broken`` while running the upgrade steps for
cleaning up broken objects is probably a better idea than not doing
so.  This will be included automatically if you require the
``collective.upgrade [steps]`` extra.

An unregistered upgrade step function,
``collective.upgrade.steps.setDefaultEditor``, can be registered in ZCML
to set the default editor for all users.  It requires
``collective.setdefaulteditor`` which will be included automatically if
you require the ``collective.upgrade [steps]`` extra.

Helper functions are also available in the ``collective.upgrade.steps``
module.  These helpers are all meant to be used when writing your own
upgrades steps.  See the ``collective.upgrade.steps`` source for
details:

  * reset the site to the baseline GenericSetup profile plus default extensions
  * delete custom skin objects
  * cleanup missing skin/theme layers
  * uninstall add-ons
  * pack the ZODB pruning old revision history
  * BBB import/export steps for resource registries before the Plone 5 switch to
    using plone.app.registry
