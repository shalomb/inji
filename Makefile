# Makefile for python projects

# TODO: Consider modernizing things with Hypermodern Python
# https://medium.com/@cjolowicz/hypermodern-python-d44485d9d769

.ONESHELL:
SHELLFLAGS := -u nounset -ec

THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
THIS_DIR      := $(shell dirname $(THIS_MAKEFILE))
THIS_PROJECT  := inji

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
twine     = twine

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

install: venv-deps ## Installs this package
	python3 -m pip install ./

_install-e:
	$(pip) install -e ./
	which inji

install-editable: _install-e show ## Install an editable version into workspace

install-build: venv-deps package ## Installs the built package
	python3 -m pip install dist/*.whl

uninstall: ## Uninstall the package
	python3 -m pip uninstall -y $(package)

show: ## Show the version installed by pip
	$(pip) list | grep -i $(package) || true
	$(python) $(script) --version

run: ## Run the installable
	@ $(python) $(script) -h

build: package
	@ :

package-deps: ## Install dependencies needed to package this distribution
	python3 -m pip install --upgrade twine

package: clean package-deps version ## Build and validate the wheels ready for a PyPi release
	./setup.py bdist_wheel sdist
	./setup.py check -sm
	twine check dist/*

release: package ## Upload wheels to PyPi to mark a new release
	twine upload --skip-existing dist/*

clean: ## Wipe the  workspace clean
	test -e "$(git)" && $(git) checkout version || true
	find ./ -depth '(' -type d -iname __pycache__ -o -type f -iname '.*.sw?' ')' -exec rm -fr {} +
	rm -fr .coverage dist/ build/ .pytest_cache *.egg-info/ test*.tap || true
	./setup.py clean --all --verbose

venv-deps: ## Install virtualenv bootstrap dependencies
	which pip3 || curl -fsSL https://bootstrap.pypa.io/get-pip.py | python3;
	python3 -m pip install --upgrade pip setuptools twine virtualenv wheel

venv: $(pip) requirements ## Create the workspace with test frameworks

$(pip): ## Install pip
	test -d venv/bin || virtualenv venv/
	$(pip) install --upgrade pip

requirements: ## Install dev/runtime requirements
	$(pip) install --upgrade $$($(setup) requirements)

requirements.txt: ## Create requirements.txt from setup.py
	# This is required by most CI systems
	$(setup) requirements >> requirements.txt

version: ## Derive new version number for a bump
ifndef CI_BUILD_REF_NAME
	$(warning CI_BUILD_REF_NAME is not set, are we running under gitlab CI?)
	$(git) describe --tags --always > _version
else
	echo "$$CI_BUILD_REF_NAME" > _version
endif
	grep -iq . _version && mv _version version; rm -f _version
	./setup.py version

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

