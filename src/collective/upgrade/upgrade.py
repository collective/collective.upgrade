import sys
import logging
import pdb

import transaction

from AccessControl import SpecialUsers
from AccessControl.SecurityManagement import newSecurityManager

from Products.CMFCore.utils import getToolByName


class Upgrader(object):

    def __call__(self):
        newSecurityManager(None, SpecialUsers.system)
        
        for portal in self.app.objectValues('Plone Site'):
            self.portal = portal
            self.setup = getToolByName(portal, 'portal_setup')

            # May fix the profile version
            migration = self.app.unrestrictedTraverse(
                getToolByName(portal, 'portal_migration').getPhysicalPath())
            migration.getInstanceVersion()

            # Do the core plone upgrade first
            profile_id = 'Products.CMFPlone:plone'
            self.upgradeProfile(profile_id)

            # Upgrade installed add-ons
            self.upgradeAddOns()

    def upgradeProfile(self, profile_id):
        upgrades = list(self.listUpgrades(profile_id))
        while upgrades:
            try:
                transaction.begin()
                self.doUpgrades(profile_id, upgrades)
                self.commit()
            except:
                self.logger.exception('Exception upgrading %r' % profile_id)
                pdb.post_mortem(sys.exc_info()[2])
                transaction.abort()
                break
            upgrades = list(self.listUpgrades(profile_id))
        else:
            self.log('Finished upgrading %r profile' % profile_id)

    def listUpgrades(self, profile_id):
        for info in self.setup.listUpgrades(profile_id):
            if type(info) == list:
                for subinfo in info:
                    if subinfo['proposed']:
                        yield subinfo
            elif info['proposed']:
                yield info

    def upgradeAddOns(self):
