Changelog
=========


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
