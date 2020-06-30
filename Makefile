THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
THIS_DIR      := $(shell dirname $(THIS_MAKEFILE))
THIS_PROJECT  := $(shell basename $(THIS_DIR))

package   = $(THIS_PROJECT)
bin       = venv/bin
python    = $(bin)/python
pip       = $(bin)/pip --disable-pip-version-check
pytest    = $(bin)/pytest -rxXs --color=auto --full-trace -vvv --tb=short -W ignore::DeprecationWarning --showlocals
setup     = $(python) ./setup.py
script    = $(package)/$(package)
git       = $(shell which git)

.PHONY: all clean requirements.txt venv version

default: help

workspace: venv requirements.txt
buildenv:  clean workspace version

all: workspace install

help:
	@ echo "Targets available for '$(THIS_PROJECT)':"
	@ echo '  all              - workspace, install'
	@ echo '  clean            - Clean the (build) workspace'
	@ echo '  install-e        - Install $(package) (editable) using pip'
	@ echo '  install          - Install $(package) using pip'
	@ echo '  package          - Build the pip package/wheel'
	@ echo '  requirements.txt - Update requirements.txt from setup.py'
	@ echo '  run              - Run $(script)'
	@ echo '  show             - Show $(package) as installed by pip'
	@ echo '  test             - Run the test suite for $(package)'
	@ echo '  uninstall        - Uninstall $(package)'
	@ echo '  venv-bootstrap   - Satisfy buildenv requirements to create venv/'
	@ echo '  venv             - Create the venv'
	@ echo '  version          - Derive the (new) version of $(package)'
	@ echo '  workspace        - Setup workspace (clean, venv, requirements, ...)'

# Testing workspace
install: workspace show
	@ $(setup) version
	@ $(setup) clean --all
	@ $(pip)   install .

# Editable workspace
install-e: buildenv show
	@ $(pip) install -e ./

show:
	@ $(pip) list | grep -i $(package) || true

run:
	@  $(python) $(script) -h
	@! $(python) $(script)

package: version
	@ $(setup) install sdist bdist_wheel
	@ $(pip) install twine
	@ twine check dist/*

release: package
	@ twine upload --skip-existing dist/*

clean:
	@ test -e "$(git)" && $(git) checkout requirements.txt || true
	@ ./setup.py clean --all --verbose
	@ rm -frv dist/ build/ *.egg-info/ venv/ .*.sw? test*.tap || true
	@ find . -depth -type d -iname __pycache__ -exec rm -frv {} +

venv-bootstrap:
	@ pip install --upgrade setuptools wheel virtualenv

venv: $(pip) requirements.txt

$(pip): venv-bootstrap
	@ test -d venv || virtualenv venv/
	@ $(pip) install --upgrade pip setuptools wheel pytest pytest-tap pytest-cov

requirements.txt:
	@ test -e "$(git)" && $(git) checkout requirements.txt || true
	@ $(setup) requirements >> requirements.txt
	@ $(pip) install --upgrade --requirement requirements.txt

uninstall:
	@ $(pip) uninstall -y $(package)

version:
ifndef CI_BUILD_REF_NAME
	$(warning CI_BUILD_REF_NAME is not set, are we running under gitlab CI?)
	@ $(git) describe --tags > version
else
	@ echo "$$CI_BUILD_REF_NAME" > version
endif
	@ $(setup) version

# @ bin/test-harness $(filter-out $@,$(MAKECMDGOALS))
test-bootstrap: venv/ venv/bin/ venv/bin/pip requirements.txt
	@:

test:
	@ $(eval args := $(filter-out $@,$(MAKECMDGOALS)))
	@ $(pytest) tests/**/*.py -k "$(args)"

%:
	@:

