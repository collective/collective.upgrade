# encoding: utf-8

import operator

from zope.component import hooks
from zope.event import notify
from zope.traversing.interfaces import BeforeTraverseEvent

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.upgrade import _upgrade_registry

from collective.upgrade import utils


class PortalUpgrader(utils.Upgrader):

    def upgrade(
            self, upgrade_portal=True,
            upgrade_all_profiles=True, upgrade_profiles=(), **kw):
        hooks.setSite(self.context)
        # initialize portal_skins
        self.context.setupCurrentSkin(self.context.REQUEST)
        # setup language
        self.context.portal_languages(self.context, self.context.REQUEST)
        self.setup = getToolByName(self.context, 'portal_setup')
        self.log('Upgrading {0}'.format(self.context))
        # setup BrowserLayer, see: https://dev.plone.org/ticket/11673
        notify(BeforeTraverseEvent(self.context, self.context.REQUEST))

        baseline = self.setup.getBaselineContextID()
        prof_type, profile_id = baseline.split('-', 1)
        self.base_profile = profile_id
        if upgrade_portal:
            # Do the baseline profile upgrade first
            self.upgradeProfile(profile_id, **kw)

        # Upgrade extension profiles
        if upgrade_all_profiles:
            if upgrade_profiles:
                raise ValueError(
                    'upgrade_profiles conflicts with upgrade_all_profiles')
            upgrade_profiles = self.setup.listProfilesWithUpgrades()
        if upgrade_profiles:
            self.upgradeExtensions(upgrade_profiles, **kw)

        self.log('Upgraded {0}'.format(self.context))

    def upgradeProfile(self, profile_id, **kw):
        upgrades = self.listUpgrades(profile_id)
        if not upgrades:
            self.log('Nothing to upgrade for profile %r' % profile_id)
            return
        while upgrades:
            self.doUpgrades(profile_id, upgrades)
            upgrades = self.listUpgrades(profile_id)
        else:
            self.log('Finished upgrading %r profile' % profile_id)

    def listUpgrades(self, profile_id):
        """Return only the upgrade steps needed to get to the next version."""
        all_upgrades = list(self.flattenUpgrades(profile_id))
        if not all_upgrades:
            return all_upgrades
        upgrades = []
        dest = max(
            all_upgrades, key=operator.itemgetter('proposed', 'dest'))['dest']
        for info in all_upgrades:
            if info['dest'] <= dest:
                upgrades.append(info)
        return upgrades

    def flattenUpgrades(self, profile_id):
        for info in self.setup.listUpgrades(profile_id):
            if isinstance(info, list):
                for subinfo in info:
                    yield subinfo
            else:
                yield info

    def doUpgrades(self, profile_id, steps_to_run):
        """Perform all selected upgrade steps.
        """
        step = None
        if steps_to_run:
            self.log("Upgrading profile %r to %r" %
                     (profile_id, steps_to_run[0]['sdest']))
        for info in steps_to_run:
            step = _upgrade_registry.getUpgradeStep(profile_id, info['id'])
            if step is not None:
                msg = 'profile {0} from {ssource} to {sdest}: {title}'.format(
                    profile_id, **info)
                self.log("Running upgrade step for {0}.".format(msg))
                step.doStep(self.setup)
                self.log("Finished upgrade step for {0}.".format(msg))

        # We update the profile version to the last one we have reached
        # with running an upgrade step.
        if step and step.dest is not None and step.checker is None:
            self.setup.setLastVersionForProfile(profile_id, step.dest)
        else:
            raise ValueError(
                'Upgrade steps %r finished for profile %r '
                'but no new version %r recorded.' %
                (steps_to_run, profile_id, '.'.join(step.dest)))

        self.commit("Upgraded profile %r to %r" %
                    (profile_id, '.'.join(step.dest)))

    def upgradeExtensions(self, profile_ids, **kw):
        for profile_id in profile_ids:
            if profile_id == self.base_profile:
                continue
            if self.isProfileInstalled(profile_id):
                self.upgradeProfile(profile_id, **kw)

    def isProfileInstalled(self, profile_id):
        return self.setup.getLastVersionForProfile(profile_id) != 'unknown'
