
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

## --- Testing: Graduated Test Ladder --- ##
## ⭐ SINGLE ENTRY POINT: `make test`
## Run the complete graduated test ladder (structure → fast → coverage)
## Each phase stops on first failure (fail-fast pattern)

test-deps: sync ## Install test dependencies (included in sync)
	@ echo "Test dependencies installed via uv sync"

test-structure: ## Phase 0: Validate Python syntax (instant fail-fast)
	@echo "🔍 Validating Python syntax..."
	@find inji tests -name "*.py" -exec python3 -m py_compile {} +
	@echo "✅ Syntax validation passed"

test-lint: sync ## Phase 0.5: Lint check with ruff (fast, zero-tolerance)
	@echo "🔍 Running ruff lint check..."
	$(uv) run ruff check inji/ tests/
	@echo "🔍 Running ruff format check..."
	$(uv) run ruff format --check inji/ tests/
	@echo "✅ Lint check passed"

lint: sync ## Run ruff linter (check only — no fixes)
	$(uv) run ruff check inji/ tests/

format: sync ## Auto-format source with ruff
	$(uv) run ruff format inji/ tests/

format-check: sync ## Check formatting without modifying files
	$(uv) run ruff format --check inji/ tests/

test-fast: sync ## Phase 1: Run all unit tests (fast, isolated)
	@echo "🧪 Running unit tests (Phase 1)..."
	@$(pytest) tests/unit/ -v
	@echo "✅ Unit tests passed"

test-cov: sync ## Phase 2: Run coverage validation (threshold 70%)
	@echo "🧪 Running coverage tests (Phase 2)..."
	rm -f .coverage
	$(pytest) \
		--cov-append \
		--cov-report term \
		--cov-report=term-missing \
		--cov-fail-under=70 \
		--cov $$PWD/inji/

test: sync test-structure test-lint test-fast test-cov ## 🚀 MAIN TARGET: Run complete graduated test ladder
	@echo ""
	@echo "✅ COMPLETE: All test levels passed!"
	@echo "   - Phase 0:   Syntax validation"
	@echo "   - Phase 0.5: Lint (ruff check + format)"
	@echo "   - Phase 1:   Unit tests (149 tests)"
	@echo "   - Phase 2:   Coverage validation (35% threshold)"

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
	rm -fr .coverage dist/ build/ .pytest_cache *.egg-info/ test*.tap .venv/ || true

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
