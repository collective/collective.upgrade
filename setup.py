from setuptools import setup, find_packages
import os

version = '0.1'

tests_require = ['plone.app.testing']

setup(name='collective.upgrade',
      version=version,
      description="CMF portal upgrade helpers",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("CHANGES.rst")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      url='http://svn.plone.org/svn/plone/plone.example',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir = {'':'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'Products.GenericSetup',
          'Products.CMFCore',
      ],
      tests_require=tests_require,
      extras_require=dict(test=tests_require),
      test_suite = 'collective.upgrade.tests.test_suite',
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
