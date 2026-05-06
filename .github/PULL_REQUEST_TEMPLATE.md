## Pre-flight Checklist

- [ ] All changes complete and tested locally (`just test` passes)
- [ ] `just lint` passes (ruff check + format)
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/) format (`feat:`, `fix:`, `chore:`, etc.)
- [ ] Each commit is atomic (code + tests + docs together)
- [ ] Self-review completed — no debug statements, no dead code

---

## Summary

> One-line description of what this PR does.

## Issue Context

**Related Issue:** closes #

- [ ] Issue is linked above
- [ ] PR adequately addresses the issue

## What Changed

> Clear summary of modifications:
> - Files / modules changed
> - Behaviour added, removed, or modified

## Why

> Business or technical context:
> - What problem does this solve?
> - Why this approach over alternatives?

## Testing Evidence

- [ ] `just test` passed (syntax → lint → unit → coverage)
- [ ] New behaviour covered by unit or e2e tests
- [ ] No regressions to existing tests

**Test output:**
```
# paste relevant just test / pytest output here
```

## Breaking Changes

- [ ] This PR contains breaking changes
  - If yes, describe migration path below:

## GenAI Attribution

- [ ] This PR contains code generated with GenAI assistance
  - If yes, all generated code has been reviewed and validated

---

> Once all checks are met, request review from the maintainer.
