
# Makefile for python projects
#
# Modernized: pyproject.toml and uv support added
#
# TODO: Consider further modernization with Hypermodern Python
# https://medium.com/@cjolowicz/hypermodern-python-d44485d9d769
.ONESHELL:
SHELLFLAGS := -u nounset -ec

THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
THIS_DIR      := $(shell dirname $(THIS_MAKEFILE))
THIS_PROJECT  := inji

# Allow test to `import $(package)`
export PYTHONPATH := $(THIS_DIR):$(PYTHONPATH)
export PATH       := $(THIS_DIR)/bin:$(PATH)

# Modern uv-based variables
git       = $(shell which git)
package   = $(THIS_PROJECT)
uv        = $(shell which uv)
python    = $(uv) run python
pytest    = $(uv) run pytest tests/**/*.py
script    = bin/$(package)

# Legacy variables for backward compatibility
bin       = .venv/bin
pip       = $(uv) pip

define venv

endef

.PHONY: all clean venv version requirements.txt

## --- Main targets --- ##
.PHONY: all clean help install install-dev install-build uninstall show run build test workspace

default: help

workspace: sync ## Create workspace with dependencies
buildenv:  clean workspace test-deps

all: workspace install

help: ## Show make targets available
	@ echo "Available tasks:"
	@ grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s - %s\n", $$1, $$2}'

## --- Environment Management --- ##
sync: ## Install/sync dependencies with uv from pyproject.toml
	test -x "$(uv)" || curl -LsSf https://astral.sh/uv/install.sh | sh
	$(uv) sync --extra test

install: sync ## Install this package for use
	$(uv) pip install .

install-dev: sync ## Install package in development/editable mode
	$(uv) pip install -e .
	which inji

install-build: package ## Install the built package
	$(uv) pip install dist/*.whl

uninstall: ## Uninstall the package
	$(uv) pip uninstall -y $(package)

show: ## Show the version installed
	$(uv) pip list | grep -i $(package) || true
	$(python) $(script) --version

run: ## Run the installable
	@ $(python) $(script) -h

## --- Testing --- ##
test-deps: sync ## Install test dependencies (included in sync)
	@ echo "Test dependencies installed via uv sync"

test: sync ## Run pytest tests (argument narrows down by name)
	$(eval args := $(filter-out $@,$(MAKECMDGOALS)))
	$(pytest) -k '$(args)'

test-cov: sync ## Run coverage tests
	rm -f .coverage
	$(pytest) \
		--cov-append \
		--cov-report term \
		--cov-report=term-missing \
		--cov-fail-under=35 \
		--cov $$PWD/inji/

test-durations: sync ## Run tests and report durations
	$(pytest) --durations=24

## --- Package Management --- ##
build: package ## Alias for package
	@ :

package: clean version ## Build and validate wheels using pyproject.toml
	$(uv) sync --extra build
	$(uv) build
	$(uv) run twine check dist/*

release: package ## Upload wheels to PyPi to mark a new release
	$(uv) run twine upload --skip-existing dist/*

version: ## Get version from git or pyproject.toml
	@ $(git) describe --tags --always 2>/dev/null | sed 's/^[vV]//; s/-[a-f0-9]\{8\}$$//' || echo "0.6.0"

## --- Maintenance and Cleanup --- ##
clean: ## Wipe the workspace clean
	test -e "$(git)" && $(git) checkout version || true
	find ./ -depth '(' -type d -iname __pycache__ -o -type f -iname '.*.sw?' ')' -exec rm -fr {} +
	rm -fr .coverage dist/ build/ .pytest_cache *.egg-info/ test*.tap .venv/ uv.lock || true

requirements.txt: ## Generate requirements.txt from pyproject.toml (for CI compatibility)
	$(uv) pip compile pyproject.toml -o requirements.txt

## --- Legacy Compatibility --- ##
# Maintained for backward compatibility - use uv directly instead
venv-deps: sync ## Legacy: use sync instead
	@ echo "Note: Use 'make sync' instead. venv-deps is deprecated."

venv: sync ## Legacy: use sync instead  
	@ echo "Note: Use 'make sync' instead. venv is deprecated."

requirements: sync ## Legacy: use sync instead
	@ echo "Note: Use 'make sync' instead. requirements is deprecated."

install-editable: install-dev ## Legacy: use install-dev instead
	@ echo "Note: Use 'make install-dev' instead. install-editable is deprecated."

%: ## Fallback to nothing
	@:
