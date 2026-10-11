*** Settings ***
Documentation  The upgrade form of a Plone site: @@collective.upgrade.form?submitted=1
...            The log is filtered for duplicates over the whole process: keep the first
...            scenario first, restart a robot server before running this file again.
Resource  collective_upgrade.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
A Manager runs the pending upgrades and reads the log
    Enable autologin as  Manager
    Run the upgrades of the site
    The upgrade log contains  Upgrading <PloneSite at plone>
    The upgrade log contains  Nothing to upgrade for profile 'Products.CMFPlone:plone'
    The upgrade log contains  Running upgrade step for profile collective.upgrade.tests:upgrades from 1 to 2: First step from 1 to 2.
    The upgrade log contains  Running upgrade step for profile collective.upgrade.tests:upgrades from 2 to 3: Step from 2 to 3.
    The upgrade log contains  Upgraded <PloneSite at plone>

Running the upgrades again shows no message already logged
    Enable autologin as  Manager
    Run the upgrades of the site
    Run the upgrades of the site
    The upgrade log shows no message

Anonymous is asked to log in
    Run the upgrades of the site
    The login form is shown

A Member is refused
    Enable autologin as  Member
    Run the upgrades of the site
    The access is refused
