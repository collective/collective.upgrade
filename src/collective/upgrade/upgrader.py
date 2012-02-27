from zope.component import hooks

import transaction

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.upgrade import _upgrade_registry

from collective.upgrade import utils


class PortalUpgrader(utils.Upgrader):

    def upgrade(self, **kw):
        hooks.setSite(self.context)
        self.setup = getToolByName(self.context, 'portal_setup')
        self.log('Upgrading {0}'.format(self.context))

        # Do the baseline profile upgrade first
        baseline = self.setup.getBaselineContextID()
        prof_type, profile_id = baseline.split('-', 1)
        self.upgradeProfile(profile_id)

        # Upgrade extension profiles
        self.upgradeExtensions()

        self.log('Upgraded {0}'.format(self.context))
        self.commit()

    def upgradeProfile(self, profile_id):
        upgrades = self.listUpgrades(profile_id)
        if not upgrades:
            self.log('Nothing to upgrade for profile %r' % profile_id)
            return
        while upgrades:
            transaction.begin()
            self.doUpgrades(profile_id, upgrades)
            self.commit()
            upgrades = self.listUpgrades(profile_id)
        else:
            self.log('Finished upgrading %r profile' % profile_id)

    def listUpgrades(self, profile_id):
        """Return only the upgrade steps needed to get to the next version."""
        all_upgrades = list(self.flattenUpgrades(profile_id))
        if not all_upgrades:
            return all_upgrades
        upgrades = [all_upgrades[0]]
        dest = upgrades[0]['dest']
        for info in all_upgrades[1:]:
            if info['dest'] == dest:
                upgrades.append(info)
            else:
                break

        return upgrades

    def flattenUpgrades(self, profile_id):
        for info in self.setup.listUpgrades(profile_id):
            if type(info) == list:
                for subinfo in info:
                    yield subinfo
            elif info['proposed']:
                yield info
                
    def doUpgrades(self, profile_id, steps_to_run):
        """Perform all selected upgrade steps.
        """
        step = None
        if steps_to_run:
            self.log("Upgrading profile %r to %r" %
                     (profile_id, steps_to_run[0]['sdest']))
        for step in steps_to_run:
            step = _upgrade_registry.getUpgradeStep(profile_id, step['id'])
            if step is not None:
                self.log("Running upgrade step %r for profile %r."
                         % (step.title, profile_id))
                step.doStep(self.setup)
                self.log("Ran upgrade step %s for profile %s"
                         % (step.title, profile_id))

        self.log("Upgraded profile %r to %r" % (profile_id, step.sdest))
        # We update the profile version to the last one we have reached
        # with running an upgrade step.
        if step and step.dest is not None and step.checker is None:
            self.setup.setLastVersionForProfile(profile_id, step.dest)
        else:
            raise ValueError(
                'Upgrade steps %r finished for profile %r but no new version '
                '%r recorded.' % (steps_to_run, profile_id, step.sdest))

    def upgradeExtensions(self):
        for profile_id in self.setup.listProfilesWithUpgrades():
            if self.isProfileInstalled(profile_id):
                self.upgradeProfile(profile_id)

    def isProfileInstalled(self, profile_id):
        return self.setup.getLastVersionForProfile(profile_id) != 'unknown'
