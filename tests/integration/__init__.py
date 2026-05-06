"""
Integration tests for inji feature workflows.

Tests interaction between modules (no subprocess calls to CLI).
- Config sourcing (env vars → CLI args → config files → defaults)
- Template rendering with filters and globals
- Error propagation through module boundaries
"""
