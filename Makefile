# Makefile for python projects

# TODO: Consider modernizing things with Hypermodern Python
# https://medium.com/@cjolowicz/hypermodern-python-d44485d9d769

.ONESHELL:
SHELLFLAGS := -u nounset -ec

THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
THIS_DIR      := $(shell dirname $(THIS_MAKEFILE))
THIS_PROJECT  := $(shell basename $(THIS_DIR))

# Allow test to `import $(package)`
export PYTHONPATH := $(THIS_DIR):$(PYTHONPATH)

bin       = venv/bin
git       = $(shell which git)
package   = $(THIS_PROJECT)
pip       = $(bin)/pip3 --disable-pip-version-check
pytest    = $(bin)/pytest -ra -rxXs --color=auto --full-trace -vvv --tb=short -W ignore::DeprecationWarning --showlocals
python    = $(bin)/python
script    = $(package)
setup     = $(python) ./setup.py
twine     = $(bin)/twine

define venv

endef

.PHONY: all clean requirements.txt venv version

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

install-e: buildenv show ## Install a (pre-release) editable version into workspace
	$(pip) install -e ./

show: ## Show the version installed by pip
	$(pip) list | grep -i $(package) || true

run: ## Run the installable
	 $(python) $(script) -h

build: package
	:

package: test-cov version ## Build and validate the wheels ready for a PyPi release
	$(setup) install bdist_wheel sdist
	$(pip) install twine
	$(twine) check dist/*

release: package ## Upload wheels to PyPi to mark a new release
	$(twine) upload --skip-existing dist/*

clean: ## Wipe the  workspace clean
	test -e "$(git)" && $(git) checkout requirements.txt || true
	test -e "$(git)" && $(git) checkout version || true
	./setup.py clean --all --verbose
	@ rm -fr .coverage dist/ build/ *.egg-info/ test*.tap || true
	@ find . -depth -type d -iname __pycache__ -o -iname *.sw? -exec rm -fr {} +

venv-deps: ## Install virtualenv bootstrap dependencies
	pip install --upgrade pip setuptools virtualenv wheel

venv: $(pip) requirements ## Create the workspace with test frameworks

$(pip): venv-deps venv ## Install pip
	test -d venv/bin || virtualenv venv/
	@ :

requirements: ## Install runtime requirements
	$(pip) install --upgrade --requirement requirements.txt

requirements.txt: ## Create requirements.txt from setup.py
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
	$(pip) install $$(./setup.py requirements_test)

test: ## Run pytest tests (argument narrows down by name)
	$(eval args := $(filter-out $@,$(MAKECMDGOALS)))
	. venv/bin/activate
	$(pytest) tests/**/*.py -k '$(args)'

test-cov: ## Run coverage tests
	rm -f .coverage
	. venv/bin/activate
	$(pytest) \
		--cov-append \
		--cov-report term \
		--cov-report=term-missing \
		--cov-fail-under=100 \
		--cov $$PWD/inji/ tests/**/*

test-durations: ## Run tests and report durations
	. venv/bin/activate
	$(pytest) tests/**/* -vvvv --durations=24

%: ## Fallback to nothing
	@:

