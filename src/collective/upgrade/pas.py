import mimetypes
import tempfile
import csv

import transaction

from Acquisition import aq_base

from Products.PluggableAuthService.interfaces.plugins import (
    IUserEnumerationPlugin, IGroupEnumerationPlugin, IPropertiesPlugin)

from Products.CMFCore.utils import getToolByName


class UsersGroupsReconciler(object):

    filename = 'reconcile_users_groups.csv'
    fieldnames = ('Source Plugin ID',
                  'Source ID',
                  'Destination Plugin ID',
                  'Destination ID',
                  'Destination Duplicate IDs')
    user_properties = ('fullname', )

    def __init__(self, context,
                 dest_users_plugin=None, dest_properties_plugin=None,
                 dest_groups_plugin=None):
        self.context = context
        self.site = context.getSite()
        self.acl_users = getToolByName(self.site, 'acl_users')

        self.plugins = self.acl_users._getOb('plugins')
        if not dest_users_plugin:
            dest_users_plugin = self.plugins.listPlugins(
                IUserEnumerationPlugin)[0][0]
        self.dest_users = self.acl_users._getOb(dest_users_plugin)
        if not dest_properties_plugin:
            dest_properties_plugin = self.plugins.listPlugins(
                IPropertiesPlugin)[0][0]
        self.dest_properties = self.acl_users._getOb(dest_properties_plugin)
        if not dest_groups_plugin:
            dest_groups_plugin = self.plugins.listPlugins(
                IGroupEnumerationPlugin)[0][0]
        self.dest_groups = self.acl_users._getOb(dest_groups_plugin)

    def export(self):
        if hasattr(self.context, 'openDataFile'):
            csvfile = self.context.openDataFile(self.filename)
        else:
            csvfile = tempfile.TemporaryFile()

        try:
            content_type = mimetypes.guess_type(self.filename)
            writer = csv.DictWriter(csvfile, self.fieldnames)
            writer.writerow(dict((name, name) for name in self.fieldnames))
            writer.writerows(self.get_user_rows())
            writer.writerows(self.get_group_rows())

            if not hasattr(self.context, 'openDataFile'):
                csvfile.seek(0)
                self.context.writeDataFile(
                    self.filename, csvfile.read(), content_type)

        finally:
            csvfile.close()

    def get_user_rows(self):
        seen = set()
        # Temporarily disable the destination plugins from listing
        savepoint = transaction.savepoint(optimistic=True)
        try:
            self.plugins.deactivatePlugin(
                IUserEnumerationPlugin, self.dest_users.getId())
            if self.dest_properties.getId() in self.plugins.listPluginIds(
                IUserEnumerationPlugin):
                self.plugins.deactivatePlugin(
                    IUserEnumerationPlugin, self.dest_properties.getId())

            # Look for matches for the source users
            for info in self.acl_users.searchUsers():
                if info['id'] in seen:
                    continue
                seen.add(info['id'])
                result = {'Source Plugin ID': info['pluginid'],
                          'Source ID': info['id']}

                # Exact user id match
                matches = self.dest_users.enumerateUsers(
                    id=info['id'], exact_match=True)
                if len(matches) == 1:
                    result['Destination Plugin ID'] = matches[0].get(
                        'pluginid', self.dest_users.getId())
                    result['Destination ID'] = matches[0]['id']
                    yield result
                    continue

                # Match on properties
                user = self.acl_users.getUserById(info['id'])
                value = None
                for prop in self.user_properties:
                    prop_result = result.copy()
                    value = None
                    for sheet_id in user.listPropertysheets():
                        sheet = user.getPropertysheet(sheet_id)
                        if sheet.hasProperty(prop):
                            value = sheet.getProperty(prop)
                            if value:
                                break
                    else:
                        continue
                    matches = self.dest_properties.enumerateUsers(
                        **{prop: value})
                    if matches:
                        prop_result['Destination Plugin ID'] = matches[0].get(
                            'pluginid', self.dest_users.getId())
                        prop_result['Destination ID'] = matches[0]['id']
                        if len(matches) > 1:
                            prop_result[
                                'Destination Duplicate IDs'] = ' '.join(
                                match['id'] for match in matches[1:])
                        yield prop_result

                # No match
                if not value:
                    yield result

        # Restore disabled plugins
        finally:
            savepoint.rollback()

    def get_group_rows(self):
        seen = set()
        # Temporarily disable the destination plugins from listing
        savepoint = transaction.savepoint(optimistic=True)
        try:
            self.plugins.deactivatePlugin(
                IGroupEnumerationPlugin, self.dest_groups.getId())

            # Look for matches for the source groups
            for info in self.acl_users.searchGroups():
                if info['id'] in seen:
                    continue
                seen.add(info['id'])
                result = {'Source Plugin ID': info['pluginid'],
                          'Source ID': info['id']}

                # Exact group id match
                matches = self.dest_groups.enumerateGroups(
                    id=info['id'], exact_match=True)
                if len(matches) == 1:
                    result['Destination Plugin ID'] = matches[0].get(
                        'pluginid', self.dest_groups.getId())
                    result['Destination ID'] = matches[0]['id']
                    yield result
                    continue

                # Match on group title
                if info.get('title'):
                    matches = self.dest_groups.enumerateGroups(
                        title=info['title'])
                    if matches:
                        result['Destination Plugin ID'] = matches[0].get(
                            'pluginid', self.dest_groups.getId())
                        result['Destination ID'] = matches[0]['id']
                        if len(matches) > 1:
                            result[
                                'Destination Duplicate IDs'] = ' '.join(
                                match['id'] for match in matches[1:])
                        yield result
                        continue

                # No match
                yield result

        # Restore disabled plugins
        finally:
            savepoint.rollback()


class DataFile(object):

    def __init__(self, file_):
        self.size = file_.tell()
        file_.seek(0)
        self.file = file_


def reconcileUsersAndGroupsExport(context):
    reconciler = UsersGroupsReconciler(context)
    reconciler.export()
