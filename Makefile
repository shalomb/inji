# Makefile for python projects

# TODO: Consider modernizing things with Hypermodern Python
# https://medium.com/@cjolowicz/hypermodern-python-d44485d9d769

.ONESHELL:
SHELLFLAGS := -u nounset -ec

THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
THIS_DIR      := $(shell dirname $(THIS_MAKEFILE))
THIS_PROJECT  := 'inji'

# Allow test to `import $(package)`
export PYTHONPATH := $(THIS_DIR):$(PYTHONPATH)
export PATH       := $(THIS_DIR)/bin:$(PATH)

bin       = venv/bin
git       = $(shell which git)
package   = $(THIS_PROJECT)
pip       = $(bin)/pip3 --disable-pip-version-check
pytest    = . venv/bin/activate; $(bin)/pytest tests/**/*.py
python    = $(bin)/python
script    = bin/$(package)
setup     = $(python) ./setup.py
twine     = $(bin)/twine

define venv

endef

.PHONY: all clean venv version

default: help

workspace: venv-deps venv requirements
buildenv:  clean workspace test-deps

all: workspace install

help: ## Show make targets available
	@ echo "Available tasks:"
	@ grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s - %s\n", $$1, $$2}'

install: workspace show ## Install a release into workspace
	$(setup) version
	$(setup) clean --all
	$(pip)   install .

_install-e:
	$(pip) install -e ./
	which inji

install-editable: _install-e show ## Install an editable version into workspace

show: ## Show the version installed by pip
	$(pip) list | grep -i $(package) || true
	$(python) $(script) --version

run: ## Run the installable
	 $(python) $(script) -h

build: package
	@ :

package: test-cov version ## Build and validate the wheels ready for a PyPi release
	$(setup) install bdist_wheel sdist
	$(twine) check dist/*

release: package ## Upload wheels to PyPi to mark a new release
	$(twine) upload --skip-existing dist/*

clean: ## Wipe the  workspace clean
	test -e "$(git)" && $(git) checkout version || true
	find tests/ -depth -type d '(' -iname __pycache__ -o -iname '*.sw?' ')' -exec rm -fr {} +
	rm -fr .coverage dist/ build/ *.egg-info/ test*.tap || true
	./setup.py clean --all --verbose

venv-deps: ## Install virtualenv bootstrap dependencies
	pip install --upgrade pip setuptools twine virtualenv wheel

venv: $(pip) requirements ## Create the workspace with test frameworks

$(pip): venv-deps venv ## Install pip
	test -d venv/bin || virtualenv venv/
	$(pip) install --upgrade pip

requirements: ## Install dev/runtime requirements
	$(pip) install --upgrade $$($(setup) requirements)

requirements.txt: ## Create requirements.txt from setup.py
	# This is required by most CI systems
	$(setup) requirements >> requirements.txt

uninstall: ## Uninstall the package
	$(pip) uninstall -y $(package)

version: ## Derive new version number for a bump
ifndef CI_BUILD_REF_NAME
	$(warning CI_BUILD_REF_NAME is not set, are we running under gitlab CI?)
	$(git) describe --tags --always > version
else
	echo "$$CI_BUILD_REF_NAME" > version
endif
	$(setup) version

test-deps: ## Install (py)test dependencies
	$(pip) install -U $$($(setup) requirements --test)

test: ## Run pytest tests (argument narrows down by name)
	$(eval args := $(filter-out $@,$(MAKECMDGOALS)))
	$(pytest) -k '$(args)'

test-cov: ## Run coverage tests
	rm -f .coverage
	$(pytest) \
		--cov-append \
		--cov-report term \
		--cov-report=term-missing \
		--cov-fail-under=100 \
		--cov $$PWD/inji/

test-durations: ## Run tests and report durations
	$(pytest) --durations=24

%: ## Fallback to nothing
	@:

