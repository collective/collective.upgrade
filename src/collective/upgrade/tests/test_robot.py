"""Robot suites of tests/robot, run with the layer of their file name.

The Plone UI keywords are in ui_plone6.robot.
"""

from ..testing import COLLECTIVE_UPGRADE_ACCEPTANCE_TESTING
from plone.testing import layered

import os
import robotsuite
import unittest

# suites needing an optional integration layer, e.g. {'test_facetednav.robot': ADDONS_ACCEPTANCE}
SUITE_LAYERS = {}


def test_suite():
    suite = unittest.TestSuite()
    robot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robot")
    for name in sorted(os.listdir(robot_dir)):
        if name.startswith("test_") and name.endswith(".robot"):
            suite.addTests(
                [
                    layered(
                        robotsuite.RobotTestSuite(os.path.join("robot", name)),
                        layer=SUITE_LAYERS.get(
                            name, COLLECTIVE_UPGRADE_ACCEPTANCE_TESTING
                        ),
                    ),
                ]
            )
    return suite
