# ADR-001: Testing Pyramid Strategy for inji

**Status:** PROPOSED  
**Date:** 2026-02-27  
**Author:** Lisa (Planning Agent)  
**Decision Date:** [pending review]

---

## Problem Statement

Current test suite (v0.6.0) consists of:
- **34 end-to-end (e2e) tests** in `tests/e2e/cli.py` (503 LOC)
- **0 unit tests** (no isolation testing for individual modules)
- **Code coverage: ~35%** (despite functional coverage appearing ~70%)
- **All tests subprocess-based**, tightly coupled to CLI interface

**Issues:**
1. Can't test module logic in isolation (engine.py, filters.py, globals.py, utils.py)
2. CLI refactoring breaks all 34 tests simultaneously (high coupling)
3. Ansible integration (60 LOC) has zero test coverage
4. Edge cases and error branches uncovered in many modules
5. Test execution speed and maintainability limited by e2e-only approach

**Root cause:** Code structure (modular) doesn't match test structure (e2e-only). No testing pyramid.

---

## Decision

Adopt a **testing pyramid** with three layers:

### Layer 1: Unit Tests (Base) — FAST, FOCUSED, ISOLATED
- **Target:** Individual modules/functions
- **Scope:** Logic validation, edge cases, error handling
- **Technology:** pytest + unittest.mock (for I/O stubbing)
- **Modules to add coverage:**
  - `inji/engine.py` (89 LOC) → 15-20 tests
  - `inji/filters.py` (189 LOC) → 25-35 tests
  - `inji/globals.py` (165 LOC) → 20-25 tests
  - `inji/utils.py` (100 LOC) → 10-15 tests
  - `inji/ansible.py` (60 LOC) → 5-10 tests
- **Total new tests:** ~75-100
- **Expected coverage boost:** 35% → 60-65%

### Layer 2: Integration Tests (Middle) — MEDIUM SPEED, BROADER SCOPE
- **Target:** Feature workflows (config sourcing, multi-template rendering)
- **Scope:** Interaction between modules; data flow
- **Technology:** pytest + temp file fixtures (no mocks, real I/O)
- **Examples:**
  - Config precedence (env vars → CLI args → config files)
  - Template + globals + filters working together
  - Error propagation through module boundaries
- **New tests:** ~15-20
- **No subprocess calls** (call Python functions directly)

### Layer 3: End-to-End Tests (Apex) — SLOW, SMOKE TESTS
- **Target:** CLI as users experience it
- **Scope:** Full CLI workflows, help, version, exit codes
- **Technology:** pytest + subprocess (existing approach)
- **Scope:** Keep existing 34 tests + add missing CLI cases (e.g., Ansible CLI flags)
- **New tests:** ~5-10 (mainly Ansible)
- **Purpose:** Smoke test; catch real-world integration issues

### Pyramid Ratios

```
      E2E (5-10%)
     / \
    /   \         ~45 tests
   / 40  \        5s execution
  /-------\
 /         \      Integration (15-20%)
/           \     ~20 tests
/     60     \    2s execution
/-------------\
/             \   Unit (65-75%)
/    100+      \ ~100 tests
/_____________\ 3s execution

Total: ~165 tests, ~10-15s full run
Coverage: ~70-75% (up from 35%)
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
1. Create test directory structure:
   ```
   tests/
   ├── unit/
   │   ├── test_engine.py
   │   ├── test_filters.py
   │   ├── test_globals.py
   │   ├── test_utils.py
   │   ├── test_ansible.py
   │   └── conftest.py (shared fixtures)
   ├── integration/
   │   ├── test_config_sourcing.py
   │   ├── test_rendering.py
   │   └── conftest.py
   └── e2e/
       ├── cli.py (refactored + new Ansible tests)
       └── conftest.py
   ```

2. Create shared fixtures (`tests/conftest.py`):
   - Mock Jinja2 environment
   - Sample templates
   - Config file fixtures
   - Temp directory helpers

3. Add unit tests for `inji/engine.py` (quick win, high value)

### Phase 2: Unit Tests (Weeks 2-3)
- Add 100+ unit tests for filters, globals, utils, ansible
- Gradually raise code coverage target: 35% → 45% → 55%
- Keep e2e tests passing throughout

### Phase 3: Integration Tests (Week 4)
- Add 20 integration tests for cross-module workflows
- Test config precedence without subprocess overhead
- Target: 65% code coverage

### Phase 4: Refactor E2E Suite (Week 5)
- Reorganize 34 existing e2e tests into logical groups
- Add ~5-10 new Ansible CLI e2e tests
- Finalize coverage target: 70%+

---

## Rationale

### Why a Pyramid?

1. **Speed:** Unit tests run in <1s; e2e tests are slow
2. **Isolation:** Can test modules without CLI coupling
3. **Maintainability:** Failures are pinpointed to specific logic, not "CLI broke"
4. **Coverage:** Edge cases and error branches exposed in units
5. **Confidence:** e2e tests catch integration issues; units catch logic bugs

### Why Not Stay E2E-Only?

- ❌ Can't test engine.py logic without invoking CLI
- ❌ Refactoring CLI interface = rewriting 34 tests
- ❌ Edge cases (empty templates, special chars) hard to test via subprocess
- ❌ Coverage metric misleading (35% despite "functional" coverage)
- ❌ Ansible feature untested

### Why Not Go 100% Unit?

- ❌ E2E tests catch real-world integration issues (e.g., Jinja2 breaking changes)
- ❌ subprocess-based tests are resilient to refactoring (no mocks to update)
- ❌ CLI is part of the product; must test it as users experience it

---

## Constraints & Assumptions

### Assumptions
- Modules (engine, filters, globals) are logically independent
- Jinja2 API is stable (don't need extensive Jinja2 testing)
- Config file formats (YAML, JSON) parsing is reliable
- Ansible integration is optional (can test in isolation)

### Constraints
- Must not break existing e2e tests during migration
- Coverage target: 70%+ (up from 35%)
- No external dependencies beyond pytest, pytest-cov, unittest.mock
- Test execution time: <15s for full suite (acceptable for CI/CD)

---

## Alternatives Considered

### Alternative 1: Keep E2E-Only
- **Pros:** No refactoring needed
- **Cons:** Coverage stays 35%; hard to test logic in isolation; brittle to CLI changes
- **Rejected:** Doesn't solve core problem (code/test structure mismatch)

### Alternative 2: Go 100% Unit (No E2E)
- **Pros:** Fast tests; high coverage
- **Cons:** Requires extensive mocking; missed integration issues; CLI untested
- **Rejected:** E2E tests are valuable; they're just not sufficient alone

### Alternative 3: Use Hypothesis (Property-Based Testing)
- **Pros:** Finds edge cases automatically
- **Cons:** Overkill for a CLI tool; adds complexity
- **Rejected:** Pyramid approach is simpler, sufficient for inji's scope

---

## Success Criteria

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Test count | 34 | 165+ | 4-5 weeks |
| Code coverage % | 35% | 70%+ | 4-5 weeks |
| Unit vs E2E ratio | 0:34 | 100:65 | By end of Phase 4 |
| Test execution time | ~5s | <15s | Per phase |
| Modules with unit tests | 0/7 | 6/7 | Phase 2 complete |

---

## Open Questions / ADR Concerns

1. **Mock strategy for I/O?**
   - Unit tests for filters: mock file I/O? Or use temp files?
   - Decision: Use mocks for `requests` (API calls), temp files for local I/O

2. **Ansible tests scope?**
   - Test the Ansible integration module (ansible.py) or just the CLI flag?
   - Decision: Test both — unit tests for ansible.py logic, e2e test for CLI flag

3. **Coverage threshold pace?**
   - Jump from 35% to 70% at end, or raise incrementally per phase?
   - Decision: Raise incrementally (45% → 55% → 65% → 70%) to maintain passing CI

4. **Backwards compat?**
   - Should unit tests use different assert style (pytest) vs existing e2e (unittest)?
   - Decision: All new tests use pytest for consistency; gradually migrate e2e to pytest

---

## References

- **Testing Pyramid:** https://martinfowler.com/bliki/TestPyramid.html
- **Farley Index:** Properties of Good Tests (Fast, Maintainable, Repeatable, Atomic, Necessary, Understandable)
- **Current test state:** See `FIXES_SUMMARY.md` and Lisa's assessment in PR comments

---

## Next Steps

1. **Review & approve** this ADR (Lisa → team)
2. **Create detailed test decomposition** in TODO.md (break into per-module tasks)
3. **Ralph implements Phase 1** (test structure + shared fixtures)
4. **Iterative phases** (2-4) with Bart's quality reviews per phase

---

**Approval Sign-Off:**

- [ ] Lisa (Planning Agent) — validates architecture
- [ ] Ralph (Build Agent) — confirms implementability
- [ ] Bart (Quality Agent) — reviews test quality criteria
- [ ] Team lead — final approval

