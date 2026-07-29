#!/usr/bin/make
# pyenv is a requirement, with 2.7, 3.7, 3.10, 3.13 python versions, and virtualenv installed in each version
# plone parameter must be passed to create environment 'make setup plone=6.0' or after a make cleanall
# The original Makefile can be found on https://github.com/IMIO/scripts-buildout

SHELL=/bin/bash
plones=4.3 5.2 6.0 6.1
b_o=
old_plone=$(shell [ -e .plone-version ] && cat .plone-version)

ifeq (, $(shell which pyenv))
  $(error "pyenv command not found! Aborting")
endif

ifndef plone
ifeq (,$(filter setup,$(MAKECMDGOALS)))
  plone=$(old_plone)
endif
endif

ifneq ($(wildcard bin/instance),)
    b_o=-N
endif

ifndef python
ifeq ($(plone),4.3)
  python=2.7
endif
ifeq ($(plone),5.2)
  python=3.8
endif
ifeq ($(plone),6.0)
  python=3.10
endif
ifeq ($(plone),6.1)
  python=3.13
endif
endif

all: buildout

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.python-version:  ## Setups pyenv version
	@pyenv local `pyenv versions |grep "  $(python)" |tail -1 |xargs`
	@echo "Local pyenv version is `cat .python-version`"
	@ if [[ `pyenv which virtualenv` != `pyenv prefix`* ]] ; then echo "You need to install virtualenv in `cat .python-version` pyenv python (pip install virtualenv)"; exit 1; fi

bin/buildout: .python-version  ## Setups environment
	virtualenv .
	./bin/pip install --upgrade pip
	./bin/pip install -r requirements-$(plone).txt
	@echo "$(plone)" > .plone-version

.PHONY: setup
setup: oneof-plone backup cleanall bin/buildout restore  ## Setups environment

.PHONY: buildout
buildout: oneof-plone bin/buildout  ## Runs setup and buildout
	rm -f .installed.cfg .mr.developer.cfg
	bin/buildout -t 5 -c test-$(plone).cfg ${b_o}

.PHONY: test
test: oneof-plone bin/buildout  ## run bin/test without robot
	# can be run by example with: make test opt='-t "settings"'
	bin/test -t \!robot ${opt}

.PHONY: cleanall
cleanall:  ## Cleans all installed buildout files
	rm -fr bin include lib local share develop-eggs downloads eggs parts .installed.cfg .mr.developer.cfg .python-version pyvenv.cfg

.PHONY: backup
backup:  ## Backups db files
	@if [ '$(old_plone)' != '' ] && [ -f var/filestorage/Data.fs ]; then mv var/filestorage/Data.fs var/filestorage/Data.fs.$(old_plone); mv var/blobstorage var/blobstorage.$(old_plone); fi

.PHONY: restore
restore:  ## Restores db files
	@if [ '$(plone)' != '' ] && [ -f var/filestorage/Data.fs.$(plone) ]; then mv var/filestorage/Data.fs.$(plone) var/filestorage/Data.fs; mv var/blobstorage.$(plone) var/blobstorage; fi

.PHONY: which-python
which-python: oneof-plone  ## Displays versions information
	@echo "current plone = $(old_plone)"
	@echo "current python = `cat .python-version`"
	@echo "plone var = $(plone)"
	@echo "python var = $(python)"

.PHONY: vcr
vcr:  ## Shows requirements in checkversion-r.html
	@bin/versioncheck -rbo checkversion-r-$(plone).html test-$(plone).cfg

.PHONY: vcn
vcn:  ## Shows newer packages in checkversion-n.html
	@bin/versioncheck -npbo checkversion-n-$(plone).html test-$(plone).cfg

.PHONY: guard-%
guard-%:
	@ if [ "${${*}}" = "" ]; then echo "You must give a value for variable '$*' : like $*=xxx"; exit 1; fi

.PHONY: oneof-%
oneof-%:
	@ if ! echo "${${*}s}" | tr " " '\n' |grep -Fqx "${${*}}"; then echo "Invalid '$*' parameter ('${${*}}') : must be one of '${${*}s}'"; exit 1; fi
