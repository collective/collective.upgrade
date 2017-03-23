# encoding: utf-8

"""Test fixtures and utilities"""

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles

from zope.configuration import xmlconfig

from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.interfaces.plugins import (
    IUserEnumerationPlugin, IGroupEnumerationPlugin, IPropertiesPlugin)
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces


class UpgradeTesting(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import collective.upgrade
        xmlconfig.file('testing.zcml',
                       collective.upgrade, context=configurationContext)

    def setUpPloneSite(self, portal):
        acl_users = getToolByName(portal, 'acl_users')

        # Add the destination plugins
        plone_pas = acl_users.manage_addProduct['PlonePAS']
        plone_pas.manage_addUserManager('dest_users')
        activatePluginInterfaces(portal, 'dest_users')
        plone_pas.manage_addZODBMutablePropertyProvider('dest_properties')
        activatePluginInterfaces(portal, 'dest_properties')
        plone_pas.manage_addGroupManager('dest_groups')
        activatePluginInterfaces(portal, 'dest_groups')

        # Make them the first plugin to get recognized by default
        plugins = acl_users._getOb('plugins')
        plugins.movePluginsDown(
            IUserEnumerationPlugin,
            [plugin for plugin in plugins.listPluginIds(IUserEnumerationPlugin)
             if plugin != 'dest_users'])
        plugins.movePluginsDown(
            IPropertiesPlugin,
            [plugin for plugin in plugins.listPluginIds(IPropertiesPlugin)
             if plugin != 'dest_properties'])
        plugins.movePluginsDown(
            IGroupEnumerationPlugin,
            [plugin for plugin
             in plugins.listPluginIds(IGroupEnumerationPlugin)
             if plugin != 'dest_groups'])

        # Add the users and groups
        user_plugins = plugins.listPlugins(IUserEnumerationPlugin)
        dest_users = user_plugins[0][1]
        source_users = user_plugins[1][1]
        property_plugins = plugins.listPlugins(IPropertiesPlugin)
        dest_properties = property_plugins[0][1]
        mutable_properties = property_plugins[1][1]
        group_plugins = plugins.listPlugins(IGroupEnumerationPlugin)
        dest_groups = group_plugins[0][1]
        source_groups = group_plugins[1][1]

        source_users.addUser(
            'foo_source_user_id', 'foo_source_user_id', 'secret')

        source_users.addUser(
            'grault_source_user_id', 'grault_source_user_id', 'secret')
        dest_users.addUser(
            'grault_source_user_id', 'grault_source_user_id', 'secret')
        user = acl_users.getUserById('grault_source_user_id')
        propertysheet = dest_properties.getPropertiesForUser(user)
        propertysheet.setProperties(user, dict(fullname='Grault Source User'))
        dest_properties.setPropertiesForUser(user, propertysheet)

        source_users.addUser(
            'corge_source_user_id', 'corge_source_user_id', 'secret')
        user = acl_users.getUserById('corge_source_user_id')
        propertysheet = mutable_properties.getPropertiesForUser(user)
        propertysheet.setProperties(user, dict(fullname='Corge Source User'))
        mutable_properties.setPropertiesForUser(user, propertysheet)
        dest_users.addUser(
            'corge_dest_user_id', 'corge_dest_user_id', 'secret')
        user = acl_users.getUserById('corge_dest_user_id')
        propertysheet = dest_properties.getPropertiesForUser(user)
        propertysheet.setProperties(user, dict(fullname='Corge Source User'))
        dest_properties.setPropertiesForUser(user, propertysheet)

        source_users.addUser(
            'bar_source_user_id', 'bar_source_user_id', 'secret')
        user = acl_users.getUserById('bar_source_user_id')
        propertysheet = mutable_properties.getPropertiesForUser(user)
        propertysheet.setProperties(user, dict(fullname='Bar Source User'))
        mutable_properties.setPropertiesForUser(user, propertysheet)
        dest_users.addUser('bar_dest_user_id', 'bar_dest_user_id', 'secret')
        dest_users.addUser('baz_dest_user_id', 'baz_dest_user_id', 'secret')
        user = acl_users.getUserById('bar_dest_user_id')
        propertysheet = dest_properties.getPropertiesForUser(user)
        propertysheet.setProperties(user, dict(fullname='Bar Source User'))
        dest_properties.setPropertiesForUser(user, propertysheet)
        user = acl_users.getUserById('baz_dest_user_id')
        propertysheet = dest_properties.getPropertiesForUser(user)
        propertysheet.setProperties(user, dict(fullname='Bar Source User'))
        dest_properties.setPropertiesForUser(user, propertysheet)

        source_users.addUser(
            'qux_source_user_id', 'qux_source_user_id', 'secret')
        dest_users.addUser(
            'qux_dest_user_id', 'qux_dest_user_id', 'secret')
        dest_groups.addGroup('qux_dest_group_id')
        source_groups.addGroup('foo_source_group_id')
        source_groups.addPrincipalToGroup(
            'qux_source_user_id', 'foo_source_group_id')

        source_groups.addGroup(
            'grault_source_group_id', title='Grault Source Group')
        source_groups.addPrincipalToGroup(
            'corge_source_user_id', 'grault_source_group_id')
        source_groups.addPrincipalToGroup(
            'corge_source_group_id', 'grault_source_group_id')
        dest_groups.addGroup(
            'grault_source_group_id', title='Grault Source Group')
        source_groups.addGroup(
            'corge_source_group_id', title='Corge Source Group')
        dest_groups.addGroup('corge_dest_group_id', title='Corge Source Group')
        source_groups.addGroup('bar_source_group_id', title='Bar Source Group')
        dest_groups.addGroup('bar_dest_group_id', title='Bar Source Group')
        dest_groups.addGroup('baz_dest_group_id', title='Bar Source Group')
        source_groups.addGroup('qux_source_group_id')

        # Add the content
        setRoles(portal, 'corge_source_user_id', ['Contributor', 'Member'])
        login(portal, 'corge_source_user_id')
        corge_doc = portal[portal.invokeFactory('Document', 'corge_doc')]
        corge_doc.manage_addLocalRoles('corge_source_group_id', ('Reviewer',))
        corge_doc.setCreators(
            corge_doc.listCreators() + ('corge_source_group_id', ))
        corge_doc.setContributors(
            ('corge_source_group_id', 'corge_source_user_id'))
        logout()


COLLECTIVE_UPGRADE_FIXTURE = UpgradeTesting()

COLLECTIVE_UPGRADE_INTEGRATION_TESTING = \
    IntegrationTesting(bases=(COLLECTIVE_UPGRADE_FIXTURE, ),
                       name="collective.upgrade:Integration")
