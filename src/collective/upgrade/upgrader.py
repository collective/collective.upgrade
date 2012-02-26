from zope import interface
from zope import component

import transaction

from Products.CMFCore import interfaces as cmf_ifaces
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.upgrade import _upgrade_registry

from collective.upgrade import interfaces
from collective.upgrade import utils


class PortalUpgrader(utils.Upgrader):
    interface.implements(interfaces.IPortalUpgrader)
    component.adapts(cmf_ifaces.ISiteRoot)

    def __call__(self):
        self.portal = portal = self.context
        self.setup = getToolByName(portal, 'portal_setup')

        # Do the baseline profile upgrade first
        baseline = self.setup.getBaselineContextID()
        prof_type, profile_id = baseline.split('-', 1)
        self.upgradeProfile(profile_id)

        # Upgrade extension profiles
        self.upgradeExtensions()

    def upgradeProfile(self, profile_id):
        upgrades = list(self.listUpgrades(profile_id))
        if not upgrades:
            self.log('Nothing to upgrade for profile %r' % profile_id)
            return
        while upgrades:
            transaction.begin()
            self.doUpgrades(profile_id, upgrades)
            self.commit()
            upgrades = list(self.listUpgrades(profile_id))
        else:
            self.log('Finished upgrading %r profile' % profile_id)

    def listUpgrades(self, profile_id):
        """Return only the upgrade steps needed to get to the next version."""
        # TODO Handle 'unknown' versions.  For some reason if
        # setup.getLastVersionForProfile(profile_id) == 'unknown'
        # then all upgrade steps for all versions of the profile up to
        # the current version are marked 'proposed' so we lose
        # incremental committing for those profiles.
        for info in self.setup.listUpgrades(profile_id):
            if type(info) == list:
                for subinfo in info:
                    if subinfo['proposed']:
                        yield subinfo
            elif info['proposed']:
                yield info

    def doUpgrades(self, profile_id, steps_to_run):
        """Perform all selected upgrade steps.
        """
        step = None
        for step in steps_to_run:
            step = _upgrade_registry.getUpgradeStep(profile_id, step['id'])
            if step is not None:
                self.log("Running upgrade step %s for profile %s: %r"
                         % (step.title, profile_id, step.__dict__))
                step.doStep(self.setup)
                self.log("Ran upgrade step %s for profile %s"
                         % (step.title, profile_id))

        self.log("Upgraded profile %r to %r" % (profile_id, step.dest))
        # We update the profile version to the last one we have reached
        # with running an upgrade step.
        if step and step.dest is not None and step.checker is None:
            self.setup.setLastVersionForProfile(profile_id, step.dest)
        else:
            raise ValueError(
                'Upgrade steps %r finished for profile %r but no new version '
                '%r recorded.' % (steps_to_run, profile_id, step.dest))

    def upgradeExtensions(self):
        for profile_id in self.setup.listProfilesWithUpgrades():
            if self.isProfileInstalled(profile_id):
                self.upgradeProfile(profile_id)

    def isProfileInstalled(self, profile_id):
        return self.setup.getLastVersionForProfile(profile_id) != 'unknown'
