Changelog
=========

0.4 - unreleased
----------------

- No changes


0.3 - 2014-01-30
----------------

- Add export and import steps for reconciling users and groups between
  two PluggableAuthService plugins, such as between existing
  Plone-only users and a newly added LDAP plugin.
  [rpatterson]

- Support Plone 4.3, tolerate a deleted KSS tool
  [rpatterson]


0.2 - 2012-11-14
----------------

- Fix upgrading "Products" namespace profiles without previous version numbers
  [rpatterson]

- Fix upgrade step handling, was skipping steps
  [rpatterson]

- Fix duplicate UUID cleanup
  [rpatterson]

- Move broken object steps into a separate ZCML file, should be
  optional and used with care
  [rpatterson]

- Plone 4.2 compatibility
  [rpatterson]


0.1 - 2012-11-05
----------------

- Initial release.
  [rpatterson]
