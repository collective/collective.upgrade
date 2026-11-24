Changelog
=========


.. towncrier release notes start

3.0.1 (unreleased)
------------------

- Nothing changed yet.

Breaking changes:


3.0.0 (2026-11-24)
------------------

- Drop support for Plone <6.2 including the replacement or cleanup of the Archetypes, portal_quickinstaller, resourceregistry, CMFEditionsFolderMigrator, ReferenceTargetCleaner, collective.setdefaulteditor related code, along with the buildout/Makefile development setup (use ``tox``).
  [laulaz, szakitibi] (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)

- Drop support for Python 2 and Python 3 versions older than 3.10.
  [szakitibi] (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)

- Replace ``pkg_resources`` namespace with PEP 420 native namespace. Support Plone 6.2 and 6.3 on Python 3.10+. When you use ``collective.upgrade`` with other packages in the ``collective`` namespace, and you get a ``ModuleNotFoundError``, you may need to install ``horse-with-no-namespace``, or use ``zc.buildout`` 5.
  [szakitibi, remdub] (plone/Products.CMFPlone#3928) (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)


New features:

- Add Plone 6.2 support and tests, fix the remaining Plone 6 incompatibilities, based on the work of @laulaz, @bsuttor, @szakitibi and @remdub.
  [chris-adam] (`#19 <https://github.com/collective/collective.upgrade/issues/19>`_)


Bug fixes:

- Fix missing ``@@plone-addsite`` case for Plone 6.1+ - see plone/Products.CMFPlone#3981.
  [szakitibi] (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)
- Rework CSV import/export to use py3 io, with explicit UTF-8 encoding and close the reader.
  [szakitibi] (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)
- Replace no longer supported ``scripts=["run-portal-upgrades"]`` with ``console_scripts``, fix missing ``Manager`` role.
  [szakitibi] (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)
- Portal_properties is no longer a persistent tool.
  [bsuttor] (`#18 <https://github.com/collective/collective.upgrade/issues/18>`_)


2.0.0 (2026-11-24)
------------------

- Switch to PEP 420 native namespace package.
  [remdub]

- Update classifiers, remove obsolete Plone 4 ``buildout.cfg`` and ``bootstrap.py``.
  [remdub]

- Add Plone 6.1 compatibility, drop Plone 4 / 5 compatibility
  [bsuttor, laulaz, szakitibi]


1.7 (2022-03-01)
----------------

- Add option to enable PDB post-mortem on exception.
  [thokas]


1.6 (2020-03-10)
----------------

- Hide upgrade profiles from Plone add-on control panel.
  [rpatterson]


1.5 (2019-05-06)
----------------

- Bugfix: Fix incremental commits when no source matches the first step.


1.4 (2019-03-31)
----------------

- Bugfix: Fix upgrading all profiles, was running all upgrade steps for all
  profiles that had upgrade steps registered.
  [rpatterson]

- Bugfix: Fix the Zope instance run script argument handling.
  [rpatterson]

- Bugfix: portal_languages is no longer a persistent tool.
  See: https://docs.plone.org/manage/upgrading/version_specific_migration/p4x_to_p5x_upgrade.html#portal-languages-is-now-a-utility
  [bsuttor]


1.3 (2018-04-18)
----------------

- Add zope global request to PortalUpgrader.
  [bsuttor]


1.2 (2017-03-23)
----------------

- Add an upgrade step to reset the site to the baseline GenericSetup profile
  plus default extensions.
  [rpatterson]

- BBB import/export steps for resource registries before the Plone 5 switch to
  using plone.app.registry.
  [rpatterson]

- Added argument to define Zope user id to use.
  [gbastien]

- Complete portal setup : portal_skins, portal_languages, BrowserLayer.
  [gbastien]


1.1 - 2014-05-08
----------------

- Restore Python 2.6 compatibility.
  [rpatterson]


1.0 - 2014-04-21
----------------

- Add an upgrade step for cooking the resource registries.  Useful when
  encountering viewlet errors on the resource registry viewlets after an
  upgrade.
  [@rpatterson]


1.0rc1 - 2014-04-08
-------------------

- Add options for controlling which profiles are upgraded.
  [@rpatterson]

- Migrate from ``optparse`` to ``argparse`` and move portal paths from an
  option to a positional argument.
  [@rpatterson]

- Add an upgrade step function that packs the ZODB.
  [@rpatterson]

- Reduce dependencies by moving some into an 'steps' extras_require.
  [@rpatterson]

- Fix a transaction error when the transaction note becomes too large.
  [@rpatterson]


0.4 - 2014-02-28
----------------

- Fix an import step bug when installing a Plone site into a fresh Zope
  instance.  Fixes #3.  Thanks to @href for the report.  [@rpatterson]


0.3 - 2014-01-30
----------------

- Add export and import steps for reconciling users and groups between
  two PluggableAuthService plugins, such as between existing
  Plone-only users and a newly added LDAP plugin.
  [@rpatterson]

- Support Plone 4.3, tolerate a deleted KSS tool
  [@rpatterson]


0.2 - 2012-11-14
----------------

- Fix upgrading "Products" namespace profiles without previous version numbers
  [@rpatterson]

- Fix upgrade step handling, was skipping steps
  [@rpatterson]

- Fix duplicate UUID cleanup
  [@rpatterson]

- Move broken object steps into a separate ZCML file, should be
  optional and used with care
  [@rpatterson]

- Plone 4.2 compatibility
  [@rpatterson]


0.1 - 2012-11-05
----------------

- Initial release.
  [@rpatterson]
