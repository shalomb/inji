# Makefile for python projects

# TODO: Consider modernizing things with Hypermodern Python
# https://medium.com/@cjolowicz/hypermodern-python-d44485d9d769

THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
THIS_DIR      := $(shell dirname $(THIS_MAKEFILE))
THIS_PROJECT  := $(shell basename $(THIS_DIR))

package   = $(THIS_PROJECT)
bin       = venv/bin
python    = $(bin)/python
pip       = $(bin)/pip3 --disable-pip-version-check
pytest    = $(bin)/pytest -ra -rxXs --color=auto --full-trace -vvv --tb=short -W ignore::DeprecationWarning --showlocals
setup     = $(python) ./setup.py
script    = $(package)/$(package)
git       = $(shell which git)

.PHONY: all clean requirements.txt venv version

default: help

workspace: venv requirements.txt
buildenv:  clean workspace version

all: workspace install

help: ## Show make targets available
	@ echo "Available tasks:"
	@ grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s - %s\n", $$1, $$2}'

install: workspace show ## Install a release into workspace
	@ $(setup) version
	@ $(setup) clean --all
	@ $(pip)   install .

install-e: buildenv show ## Install a (pre-release) editable version into workspace
	@ $(pip) install -e ./

show: ## Show the version installed by pip
	@ $(pip) list | grep -i $(package) || true

run: ## Run the installable
	@  $(python) $(script) -h

package: version ## Build and validate the wheels ready for a PyPi release
	@ $(setup) install sdist bdist_wheel
	@ $(pip) install twine
	@ twine check dist/*

release: package ## Upload wheels to PyPi to mark a new release
	@ twine upload --skip-existing dist/*

clean: ## Wipe the  workspace clean
	@ test -e "$(git)" && $(git) checkout requirements.txt || true
	@ ./setup.py clean --all --verbose
	@ rm -frv .coverage dist/ build/ *.egg-info/ venv/ .*.sw? test*.tap || true
	@ find . -depth -type d -iname __pycache__ -exec rm -frv {} +

venv-deps: ## Install virtualenv
	@ pip install --upgrade setuptools wheel virtualenv

venv: $(pip) requirements.txt ## Create the workspace with test frameworks
	@ $(pip) install --upgrade pip setuptools wheel pytest pytest-tap pytest-cov

$(pip): venv-deps ## Install pip
	@ test -d venv || virtualenv venv/
	@ $(pip) install --upgrade pip setuptools wheel

requirements.txt: ## Create requirements.txt from setup.py
	@ test -e "$(git)" && $(git) checkout requirements.txt || true
	@ $(setup) requirements >> requirements.txt
	@ $(pip) install --upgrade --requirement requirements.txt

uninstall: ## Uninstall the package
	@ $(pip) uninstall -y $(package)

version: ## Derive new version number for a bump
ifndef CI_BUILD_REF_NAME
	$(warning CI_BUILD_REF_NAME is not set, are we running under gitlab CI?)
	@ $(git) describe --tags > version
else
	@ echo "$$CI_BUILD_REF_NAME" > version
endif
	@ $(setup) version

# @ bin/test-harness $(filter-out $@,$(MAKECMDGOALS))
test-deps: buildenv $(pip) ## Install (py)test dependencies
	@:

test: ## Run pytest tests (argument narrows down by name)
	@ $(eval args := $(filter-out $@,$(MAKECMDGOALS)))
	@ $(pytest) tests/**/*.py -k "$(args)"

test-cov: ## Run coverage tests
	@ rm -f .coverage
	@ $(pytest) \
		--cov-append \
		--cov-report term \
		--cov-report=term-missing \
		--cov-fail-under=96 \
		--cov inji/ tests/

test-durations: ## Run tests and report durations
	@ $(pytest) tests/ -vvvv --durations=0

%: ## Fallback to nothing
	@:

