from collective.upgrade import testing
from plone.testing import layered

import doctest
import unittest

optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests(
        [
            layered(
                doctest.DocFileSuite("pas.rst", optionflags=optionflags),
                layer=testing.COLLECTIVE_UPGRADE_INTEGRATION_TESTING,
            )
        ]
    )
    return suite
