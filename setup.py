from setuptools import setup

import os

version = "3.0.1.dev0"

install_requires = [
    "plone.base",
    "plone.uuid",
    "Products.CMFCore",
    "Products.CMFEditions",
    "Products.CMFPlone",
    "Products.GenericSetup",
    "Products.PluggableAuthService",
    "Zope",
    "zodbupdate",
]

tests_require = [
    "plone.app.caching",
    "plone.app.contenttypes",
    "plone.app.robotframework",
    "plone.app.testing",
    "plone.registry",
    "plone.testing",
    "Products.PlonePAS",
    "plonetheme.barceloneta",
    "robotsuite",
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
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="Zope CMF Plone GenericSetup upgrade",
    author="Ross Patterson",
    author_email="me@rpatterson.net",
    url="https://github.com/collective/collective.upgrade",
    license="GPL",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require=dict(test=tests_require, steps=["experimental.broken"]),
    entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      upgrade-portals = collective.upgrade.run:main
      run-portal-upgrades = collective.upgrade.run:run_portal_upgrades

      [z3c.autoinclude.plugin]
      target = plone
      """,
)
