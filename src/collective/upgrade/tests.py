# -*- coding: utf-8 -*-
import doctest
import unittest
from plone.testing import layered
from collective.upgrade import testing


optionflags = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_NDIFF)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite('pas.rst',
                                     optionflags=optionflags),
                layer=testing.COLLECTIVE_UPGRADE_INTEGRATION_TESTING)])
    return suite
