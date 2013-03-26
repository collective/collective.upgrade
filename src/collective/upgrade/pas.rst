================================
Reconciling PAS Users and Groups
================================

Start with a PluggableAuthService user folder with two user plugins
and two group plugins:

    >>> from Products.PluggableAuthService.interfaces.plugins import (
    ...     IUserEnumerationPlugin, IGroupEnumerationPlugin, IPropertiesPlugin)
    >>> from Products.CMFCore.utils import getToolByName
    >>> portal = layer['portal']
    >>> acl_users = getToolByName(portal, 'acl_users')
    >>> acl_users
    <PluggableAuthService at /plone/acl_users>
    >>> dest_users = layer['dest_users']
    >>> source_users = layer['source_users']
    >>> dest_properties = layer['dest_properties']
    >>> dest_groups = layer['dest_groups']
    >>> source_groups = layer['source_groups']
    >>> mutable_properties = layer['mutable_properties']
    >>> source_users
    <UserManager at /plone/acl_users/source_users>
    >>> mutable_properties
    <ZODBMutablePropertyProvider at /plone/acl_users/mutable_properties>
    >>> dest_users
    <UserManager at /plone/acl_users/dest_users>
    >>> dest_properties
    <ZODBMutablePropertyProvider at /plone/acl_users/dest_properties>
    >>> source_groups
    <GroupManager at /plone/acl_users/source_groups>
    >>> dest_groups
    <GroupManager at /plone/acl_users/dest_groups>

Some users and groups have no match in the destination plugins:

    >>> from pprint import pprint as pp
    >>> pp(source_users.enumerateUsers(
    ...     id='foo_source_user_id', exact_match=True))
    ({'editurl': 'source_users/manage_users?user_id=foo_source_user_id',
      'id': 'foo_source_user_id',
      'login': 'foo_source_user_id',
      'pluginid': 'source_users'},)
    >>> dest_users.enumerateUsers(id='foo_source_user_id', exact_match=True)
    ()
    >>> dest_properties.enumerateUsers(fullname='Foo Source User')
    ()

    >>> pp(source_groups.enumerateGroups(
    ...     id='foo_source_group_id', exact_match=True))
    ({'description': None,
      'id': 'foo_source_group_id',
      'members_url': 'source_groups/manage_groups?group_id=foo_source_group_id&assign=1',
      'pluginid': 'source_groups',
      'properties_url': 'source_groups/manage_groups?group_id=foo_source_group_id',
      'title': None},)
    >>> dest_groups.enumerateGroups(id='foo_source_group_id', exact_match=True)
    ()
    >>> dest_groups.enumerateGroups(title='Foo Source Group')
    ()

Some users and groups have a single exact match on ``id`` each in the
destination plugins:

    >>> pp(source_users.enumerateUsers(
    ...     id='grault_source_user_id', exact_match=True))
    ({'editurl': 'source_users/manage_users?user_id=grault_source_user_id',
      'id': 'grault_source_user_id',
      'login': 'grault_source_user_id',
      'pluginid': 'source_users'},)
    >>> pp(dest_users.enumerateUsers(
    ...     id='grault_source_user_id', exact_match=True))
    ({'editurl': 'dest_users/manage_users?user_id=grault_source_user_id',
      'id': 'grault_source_user_id',
      'login': 'grault_source_user_id',
      'pluginid': 'dest_users'},)
    >>> pp(dest_properties.enumerateUsers(fullname='Grault Source User'))
    ({'description': 'Grault Source User',
      'email': '',
      'id': 'grault_source_user_id',
      'login': 'grault_source_user_id',
      'pluginid': 'dest_properties',
      'title': 'Grault Source User'},)

    >>> pp(source_groups.enumerateGroups(
    ...     id='grault_source_group_id', exact_match=True))
    ({'description': None,
      'id': 'grault_source_group_id',
      'members_url': 'source_groups/manage_groups?group_id=grault_source_group_id&assign=1',
      'pluginid': 'source_groups',
      'properties_url': 'source_groups/manage_groups?group_id=grault_source_group_id',
      'title': 'Grault Source Group'},)
    >>> pp(dest_groups.enumerateGroups(
    ...     id='grault_source_group_id', exact_match=True))
    ({'description': None,
      'id': 'grault_source_group_id',
      'members_url': 'dest_groups/manage_groups?group_id=grault_source_group_id&assign=1',
      'pluginid': 'dest_groups',
      'properties_url': 'dest_groups/manage_groups?group_id=grault_source_group_id',
      'title': 'Grault Source Group'},)
    >>> pp(dest_groups.enumerateGroups(title='Grault Source Group'))
    ({'description': None,
      'id': 'grault_source_group_id',
      'members_url': 'dest_groups/manage_groups?group_id=grault_source_group_id&assign=1',
      'pluginid': 'dest_groups',
      'properties_url': 'dest_groups/manage_groups?group_id=grault_source_group_id',
      'title': 'Grault Source Group'},)

Some users and groups have a single close match on other metadata in
the destination plugins:

    >>> pp(source_users.enumerateUsers(
    ...     id='corge_source_user_id', exact_match=True))
    ({'editurl': 'source_users/manage_users?user_id=corge_source_user_id',
      'id': 'corge_source_user_id',
      'login': 'corge_source_user_id',
      'pluginid': 'source_users'},)
    >>> dest_users.enumerateUsers(id='corge_source_user_id', exact_match=True)
    ()
    >>> pp(dest_properties.enumerateUsers(fullname='Corge Source User'))
    ({'description': 'Corge Source User',
      'email': '',
      'id': 'corge_dest_user_id',
      'login': 'corge_dest_user_id',
      'pluginid': 'dest_properties',
      'title': 'Corge Source User'},)

    >>> pp(source_groups.enumerateGroups(
    ...     id='corge_source_group_id', exact_match=True))
    ({'description': None,
      'id': 'corge_source_group_id',
      'members_url': 'source_groups/manage_groups?group_id=corge_source_group_id&assign=1',
      'pluginid': 'source_groups',
      'properties_url': 'source_groups/manage_groups?group_id=corge_source_group_id',
      'title': 'Corge Source Group'},)
    >>> dest_groups.enumerateGroups(
    ...     id='corge_source_group_id', exact_match=True)
    ()
    >>> pp(dest_groups.enumerateGroups(title='Corge Source Group'))
    ({'description': None,
      'id': 'corge_dest_group_id',
      'members_url': 'dest_groups/manage_groups?group_id=corge_dest_group_id&assign=1',
      'pluginid': 'dest_groups',
      'properties_url': 'dest_groups/manage_groups?group_id=corge_dest_group_id',
      'title': 'Corge Source Group'},)

Some users and groups have multiple close matches on other metadata in
the destination plugins:

    >>> pp(source_users.enumerateUsers(
    ...     id='bar_source_user_id', exact_match=True))
    ({'editurl': 'source_users/manage_users?user_id=bar_source_user_id',
      'id': 'bar_source_user_id',
      'login': 'bar_source_user_id',
      'pluginid': 'source_users'},)
    >>> dest_users.enumerateUsers(id='bar_source_user_id', exact_match=True)
    ()
    >>> pp(dest_properties.enumerateUsers(fullname='Bar Source User'))
    ({'description': 'Bar Source User',
      'email': '',
      'id': 'bar_dest_user_id',
      'login': 'bar_dest_user_id',
      'pluginid': 'dest_properties',
      'title': 'Bar Source User'},
     {'description': 'Bar Source User',
      'email': '',
      'id': 'baz_dest_user_id',
      'login': 'baz_dest_user_id',
      'pluginid': 'dest_properties',
      'title': 'Bar Source User'})

    >>> pp(source_groups.enumerateGroups(
    ...     id='bar_source_group_id', exact_match=True))
    ({'description': None,
      'id': 'bar_source_group_id',
      'members_url': 'source_groups/manage_groups?group_id=bar_source_group_id&assign=1',
      'pluginid': 'source_groups',
      'properties_url': 'source_groups/manage_groups?group_id=bar_source_group_id',
      'title': 'Bar Source Group'},)
    >>> dest_groups.enumerateGroups(id='bar_source_group_id', exact_match=True)
    ()
    >>> pp(dest_groups.enumerateGroups(title='Bar Source Group'))
    ({'description': None,
      'id': 'bar_dest_group_id',
      'members_url': 'dest_groups/manage_groups?group_id=bar_dest_group_id&assign=1',
      'pluginid': 'dest_groups',
      'properties_url': 'dest_groups/manage_groups?group_id=bar_dest_group_id',
      'title': 'Bar Source Group'},
     {'description': None,
      'id': 'baz_dest_group_id',
      'members_url': 'dest_groups/manage_groups?group_id=baz_dest_group_id&assign=1',
      'pluginid': 'dest_groups',
      'properties_url': 'dest_groups/manage_groups?group_id=baz_dest_group_id',
      'title': 'Bar Source Group'})

Some users and groups do not match with their equivalents in the
destination plugin:

    >>> pp(source_users.enumerateUsers(
    ...     id='qux_source_user_id', exact_match=True))
    ({'editurl': 'source_users/manage_users?user_id=qux_source_user_id',
      'id': 'qux_source_user_id',
      'login': 'qux_source_user_id',
      'pluginid': 'source_users'},)
    >>> dest_users.enumerateUsers(id='qux_source_user_id', exact_match=True)
    ()
    >>> dest_properties.enumerateUsers(fullname='Qux Source User')
    ()
    >>> pp(dest_users.enumerateUsers(
    ...     id='qux_dest_user_id', exact_match=True))
    ({'editurl': 'dest_users/manage_users?user_id=qux_dest_user_id',
      'id': 'qux_dest_user_id',
      'login': 'qux_dest_user_id',
      'pluginid': 'dest_users'},)

    >>> pp(source_groups.enumerateGroups(
    ...     id='qux_source_group_id', exact_match=True))
    ({'description': None,
      'id': 'qux_source_group_id',
      'members_url': 'source_groups/manage_groups?group_id=qux_source_group_id&assign=1',
      'pluginid': 'source_groups',
      'properties_url': 'source_groups/manage_groups?group_id=qux_source_group_id',
      'title': None},)
    >>> dest_groups.enumerateGroups(id='qux_source_group_id', exact_match=True)
    ()
    >>> dest_groups.enumerateGroups(title='Qux Source Group')
    ()
    >>> pp(dest_groups.enumerateGroups(
    ...     id='qux_dest_group_id', exact_match=True))
    ({'description': None,
      'id': 'qux_dest_group_id',
      'members_url': 'dest_groups/manage_groups?group_id=qux_dest_group_id&assign=1',
      'pluginid': 'dest_groups',
      'properties_url': 'dest_groups/manage_groups?group_id=qux_dest_group_id',
      'title': None},)

Some users and groups from the source plugin with matches having
different ``id`` values in the destination plugin own CMF objects
with: source group plugin memberships, ``OFS.owner.Owned`` owners,
local roles, and CMF creators:

    >>> source_groups.getGroupMembers('grault_source_group_id')
    ('corge_source_user_id',)
    >>> portal.corge_doc
    <ATDocument at /plone/corge_doc>
    >>> portal.corge_doc.getOwner()
    <PloneUser 'corge_source_user_id'>
    >>> pp(portal.corge_doc.get_local_roles())
    (('corge_source_group_id', ('Reviewer',)),
     ('corge_source_user_id', ('Owner',)))
    >>> portal.corge_doc.Creator()
    'corge_source_user_id'


Exporting Mappings
==================

A `GenericSetup`_ export step writes a file that describes the mapping
of users and groups from the source plugin to destination plugins.  By
default, the export step assumes the first IUserEnumerationPlugin,
IGroupEnumerationPlugin, and IPropertiesPlugin are the destination
plugins.

    >>> import StringIO
    >>> import tarfile
    >>> import csv
    >>> from pprint import pformat as pf
    >>> portal_setup = getToolByName(portal, 'portal_setup')
    >>> export_users_result = portal_setup.runExportStep('reconcile_users')
    >>> export_users_tarball = StringIO.StringIO(
    ...     export_users_result['tarball'])
    >>> opened = tarfile.open(fileobj=export_users_tarball)
    >>> export_users_csvfile = opened.extractfile('reconcile_users.csv')
    >>> export_users_mappings = pf(list(csv.DictReader(export_users_csvfile)))
    >>> print export_users_mappings
    [{'Destination Duplicate IDs': 'baz_dest_user_id',
      'Destination ID': 'bar_dest_user_id',
      'Destination Plugin ID': 'dest_properties',
      'Source ID': 'bar_source_user_id',
      'Source Plugin ID': 'source_users'},
     {'Destination Duplicate IDs': '',
      'Destination ID': 'corge_dest_user_id',
      'Destination Plugin ID': 'dest_properties',
      'Source ID': 'corge_source_user_id',
      'Source Plugin ID': 'source_users'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'foo_source_user_id',
      'Source Plugin ID': 'source_users'},
     {'Destination Duplicate IDs': '',
      'Destination ID': 'grault_source_user_id',
      'Destination Plugin ID': 'dest_users',
      'Source ID': 'grault_source_user_id',
      'Source Plugin ID': 'source_users'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'qux_source_user_id',
      'Source Plugin ID': 'source_users'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'test_user_1_',
      'Source Plugin ID': 'source_users'}]

    >>> portal_setup = getToolByName(portal, 'portal_setup')
    >>> export_groups_result = portal_setup.runExportStep('reconcile_groups')
    >>> export_groups_tarball = StringIO.StringIO(
    ...     export_groups_result['tarball'])
    >>> opened = tarfile.open(fileobj=export_groups_tarball)
    >>> export_groups_csvfile = opened.extractfile('reconcile_groups.csv')
    >>> export_groups_mappings = pf(list(
    ...     csv.DictReader(export_groups_csvfile)))
    >>> print export_groups_mappings
    [{'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'Administrators',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'Reviewers',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'Site Administrators',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': 'baz_dest_group_id',
      'Destination ID': 'bar_dest_group_id',
      'Destination Plugin ID': 'dest_groups',
      'Source ID': 'bar_source_group_id',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': 'corge_dest_group_id',
      'Destination Plugin ID': 'dest_groups',
      'Source ID': 'corge_source_group_id',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'foo_source_group_id',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': 'grault_source_group_id',
      'Destination Plugin ID': 'dest_groups',
      'Source ID': 'grault_source_group_id',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'qux_source_group_id',
      'Source Plugin ID': 'source_groups'},
     {'Destination Duplicate IDs': '',
      'Destination ID': '',
      'Destination Plugin ID': '',
      'Source ID': 'AuthenticatedUsers',
      'Source Plugin ID': 'auto_group'}]


Importing Mappings
==================

A `GenericSetup`_ import step reads a file that describes the mapping
of user and group ``id`` values:

    >>> import os
    >>> import collective.upgrade
    >>> print open(os.path.join(
    ...     os.path.dirname(collective.upgrade.__file__),
    ...     'profiles', 'test', 'reconcile_users_groups.csv')).read()
    Source Plugin ID,Source ID,Destination Plugin ID,Destination ID,Destination Duplicate IDs
    mutable_properties,corge_source_user_id,dest_users,corge_dest_user_id,
    mutable_properties,corge_source_user_id,dest_users,bar_dest_user_id,baz_dest_user_id
    mutable_properties,qux_source_user_id,dest_users,qux_dest_user_id,
    source_groups,corge_source_group_id,dest_groups,corge_dest_group_id,
    source_groups,corge_source_group_id,dest_groups,bar_dest_group_id,baz_dest_group_id
    source_groups,qux_source_group_id,dest_users,qux_dest_group_id,
    >>> portal_setup.runImportStepFromProfile(
    ...     'profile-collective.upgrade:test', 'reconcile_users_groups',
    ...     run_dependencies=False)

It applies those changes to: source group plugin memberships,
``OFS.owner.Owned`` owners, local roles, and CMF creators:

    >>> source_groups.getGroupMembers('grault_source_group_id')
    ('corge_dest_user_id',)
    >>> portal.corge_doc
    <ATDocument at /plone/corge_doc>
    >>> portal.corge_doc.getOwner()
    <PloneUser 'corge_dest_user_id'>
    >>> pp(portal.corge_doc.get_local_roles())
    (('corge_dest_group_id', ('Reviewer',)),
     ('corge_dest_user_id', ('Owner',)))
    >>> portal.corge_doc.Creator()
    'corge_dest_user_id'
