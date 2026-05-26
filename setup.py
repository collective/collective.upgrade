from pathlib import Path
from setuptools import find_packages
from setuptools import setup

version = "1.8.dev0"

long_description = "\n\n".join(
    Path(filename).read_text(encoding="utf-8")
    for filename in ("README.rst", "CHANGES.rst")
)

entry_point = "collective.upgrade.run:main"
entry_points = {
    "console_scripts": [
        f"upgrade-portals = {entry_point}",
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
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "setuptools",
        "zope.globalrequest",
        "zodbupdate",
        "Products.GenericSetup",
        "Products.CMFCore",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            "plone.app.contenttypes",
            "plone.app.robotframework",
            "plone.testing",
        ],
        "steps": [
            "experimental.broken",
            "collective.setdefaulteditor",
        ],
    },
    scripts=["run-portal-upgrades"],
    entry_points=entry_points,
)
