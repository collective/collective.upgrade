*** Settings ***
Documentation  collective.upgrade keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            The only browser entry point is the upgrade form, a text/plain log stream.
Resource  ui_plone${PLONE_MAJOR}.robot


*** Variables ***
${UPGRADE_FORM}  @@collective.upgrade.form?submitted=1


*** Keywords ***
Run the upgrades of the site
    Go to  ${PLONE_URL}/${UPGRADE_FORM}

The upgrade log contains
    [Arguments]  ${text}
    Page should contain  ${text}

The upgrade log shows no message
    Page should not contain  collective.upgrade
