from pathlib import Path
from setuptools import setup

version = "1.8.dev0"

long_description = "\n\n".join(
    Path(filename).read_text(encoding="utf-8")
    for filename in ("README.rst", "CHANGES.rst")
)

entry_points = {
    "console_scripts": [
        "upgrade-portals = collective.upgrade.run:main",
        "run-portal-upgrades = collective.upgrade.run:run_portal_upgrades",
    ],
    "z3c.autoinclude.plugin": [
        "target = plone",
    ],
}

setup(
    name="collective.upgrade",
    version=version,
    description="CMF portal upgrade helpers",
    long_description=long_description,
    long_description_content_type="text/x-rst",
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
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "plone.base",
        "plone.uuid",
        "Products.CMFCore",
        "Products.CMFEditions",
        "Products.CMFPlone",
        "Products.GenericSetup",
        "Products.PluggableAuthService",
        "Zope",
        "zodbupdate",
    ],
    extras_require={
        "test": [
            "plone.app.contenttypes",
            "plone.app.robotframework",
            "plone.app.testing",
            "plone.testing",
            "Products.PlonePAS",
        ],
    },
    entry_points=entry_points,
)
