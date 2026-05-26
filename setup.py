from setuptools import find_packages
from setuptools import setup

import os

version = "1.8.dev0"

install_requires = [
    "setuptools",
    # -*- Extra requirements: -*-
    "zope.globalrequest",
    "zodbupdate",
    "Products.GenericSetup",
    "Products.CMFCore",
]

tests_require = ["plone.app.testing", "plone.app.contenttypes"]

setup(
    name="collective.upgrade",
    version=version,
    description="CMF portal upgrade helpers",
    long_description=open("README.rst").read()
    + "\n"
    + open(os.path.join("CHANGES.rst")).read(),
    # Get more strings from https://pypi.org/classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 6.2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="Zope CMF Plone GenericSetup upgrade",
    author="Ross Patterson",
    author_email="me@rpatterson.net",
    url="https://github.com/collective/collective.upgrade",
    license="GPL",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
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
