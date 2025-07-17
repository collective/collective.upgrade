import os

from setuptools import find_packages, setup

version = "1.8.dev0"

install_requires = [
    "setuptools",
    # -*- Extra requirements: -*-
    "zope.globalrequest",
    "zodbupdate",
    "Products.GenericSetup",
    "Products.CMFCore",
]

tests_require = [
    "plone.app.testing",
    "plone.app.robotframework",
    "plone.app.contenttypes",
]

setup(
    name="collective.upgrade",
    version=version,
    description="CMF portal upgrade helpers",
    long_description=open("README.rst").read()
    + "\n"
    + open(os.path.join("CHANGES.rst")).read(),
    # Get more strings from
    # http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone",
        "Framework :: Plone :: 6.1",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="Zope CMF Plone GenericSetup upgrade",
    author="Ross Patterson",
    author_email="me@rpatterson.net",
    url="https://github.com/collective/collective.upgrade",
    license="GPL",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    namespace_packages=["collective"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=dict(
        test=tests_require, steps=["experimental.broken", "collective.setdefaulteditor"]
    ),
    test_suite="collective.upgrade.tests.test_suite",
    scripts=["run-portal-upgrades"],
    entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      upgrade-portals = collective.upgrade.run:main

      [z3c.autoinclude.plugin]
      target = plone
      """,
)
