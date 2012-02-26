import sys
import logging
import pdb

import transaction

from Products.CMFCore.utils import getToolByName

from collective.upgrade import utils


class Upgrader(utils.Upgrader):

    def __call__(self):
        self.portal = portal = self.context
        self.setup = getToolByName(portal, 'portal_setup')

        # May fix the profile version
        migration = getToolByName(portal, 'portal_migration')
        migration.getInstanceVersion()

        # Do the core plone upgrade first
        baseline = self.setup.getBaselineContextID()
        prof_type, profile_id = baseline.split('-', 1)
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
