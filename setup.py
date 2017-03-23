from setuptools import setup, find_packages
import os
import sys

version = '1.2'

install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'zope.globalrequest',
          'zodbupdate',
          'Products.GenericSetup',
          'Products.CMFCore',
      ]
if sys.version_info[:2] < (2, 7):
    # depend on the argparse dist before it was included in the stdlib
    install_requires.append('argparse')

tests_require = ['plone.app.testing']

setup(name='collective.upgrade',
      version=version,
      description="CMF portal upgrade helpers",
      long_description=open(
          "README.rst").read() + "\n" + open(
          os.path.join("CHANGES.rst")).read(),
      # Get more strings from
      # http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          ],
      keywords='Zope CMF Plone GenericSetup upgrade',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      url='http://github.com/collective/collective.upgrade',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require=dict(
          test=tests_require,
          steps=['experimental.broken',
                 'collective.setdefaulteditor']),
      test_suite='collective.upgrade.tests.test_suite',
      scripts=['run-portal-upgrades'],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      upgrade-portals = collective.upgrade.run:main

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
