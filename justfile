# =============================================================================
# inji — Jinja2 CLI template renderer
# =============================================================================
# Usage:  just <recipe>
#         just test          # full graduated test ladder
#         just lint          # ruff check + format check
#         just fmt           # auto-format with ruff
#         just build         # build wheel + sdist
# =============================================================================

set shell := ["bash", "-euo", "pipefail", "-c"]

# Show available recipes
default:
    @just --list --unsorted

# =============================================================================
# ENVIRONMENT
# =============================================================================

# Install / sync all dependencies from pyproject.toml (dev + test groups)
sync:
    @uv sync --extra dev --extra test

# Install package in editable mode (for local development)
dev: sync
    @uv pip install -e .
    @which inji

# Install package (non-editable)
install: sync
    @uv pip install .

# Uninstall the package
uninstall:
    @uv pip uninstall -y inji || true

# Show installed version
version:
    @uv pip show inji 2>/dev/null | grep -i version || echo "not installed"

# Wipe workspace (preserve uv.lock and .venv)
clean:
    @git checkout -- version 2>/dev/null || true
    @find . -depth \( -type d -name __pycache__ -o -type f -name "*.sw?" \) -exec rm -rf {} + 2>/dev/null || true
    @rm -rf .coverage dist/ build/ .pytest_cache *.egg-info/ test*.tap || true

# =============================================================================
# GRADUATED TEST LADDER
# =============================================================================
# Phase 0   → syntax    (instant, zero deps)
# Phase 0.5 → lint      (fast, ruff check + format)
# Phase 1   → unit      (isolated, ~3s)
# Phase 2   → coverage  (full suite + threshold, ~15s)

# Phase 0: Python syntax validation (instant fail-fast)
test-syntax:
    @printf "Phase 0 — syntax\n"
    @find inji tests -name "*.py" -exec python3 -m py_compile {} +
    @printf "  ✅ syntax OK\n"

# Phase 0.5: Ruff lint + format check (zero-tolerance)
test-lint:
    @printf "Phase 0.5 — lint\n"
    @uv run ruff check inji/ tests/
    @uv run ruff format --check inji/ tests/
    @printf "  ✅ lint OK\n"

# Phase 1: Unit tests only (fast, isolated)
test-unit: sync
    @printf "Phase 1 — unit tests\n"
    @uv run pytest tests/unit/ -q
    @printf "  ✅ unit tests OK\n"

# Phase 2: Full suite + coverage threshold
test-cov: sync
    @printf "Phase 2 — coverage\n"
    @rm -f .coverage
    @uv run pytest \
        --cov-append \
        --cov-report term-missing \
        --cov-fail-under=35 \
        --cov inji/
    @printf "  ✅ coverage OK\n"

# Full graduated test ladder (all phases, fail-fast)
test: sync test-syntax test-lint test-unit test-cov
    @printf "\n✅  All phases passed (syntax → lint → unit → coverage)\n"

# Report slowest tests
test-durations: sync
    @uv run pytest tests/ --durations=20

# =============================================================================
# LINT & FORMAT
# =============================================================================

# Run ruff linter (check only — no fixes applied)
lint:
    @uv run ruff check inji/ tests/

# Apply ruff auto-fixes
lint-fix:
    @uv run ruff check inji/ tests/ --fix

# Auto-format source with ruff
fmt:
    @uv run ruff format inji/ tests/

# Check formatting without modifying files
fmt-check:
    @uv run ruff format --check inji/ tests/

# =============================================================================
# BUILD & RELEASE
# =============================================================================

# Build wheel + sdist and validate with twine
build: clean sync
    @uv sync --extra build
    @uv build
    @uv run twine check dist/*

# Upload to PyPI (requires credentials)
release: build
    @uv run twine upload --skip-existing dist/*

# Generate requirements.txt from pyproject.toml (CI compatibility shim)
requirements:
    @uv pip compile pyproject.toml -o requirements.txt

# =============================================================================
# INSTALL PRE-COMMIT HOOK
# =============================================================================

# Install the git pre-commit hook into .git/hooks/
install-hooks:
    @cp .githooks/pre-commit .git/hooks/pre-commit
    @chmod +x .git/hooks/pre-commit
    @printf "✅ pre-commit hook installed\n"
