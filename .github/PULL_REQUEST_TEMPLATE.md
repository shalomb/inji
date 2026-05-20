<!--
  Start at "Risk and review focus" — that's where the author tells you
  where to look. If "Driver" or "Alternatives rejected" is vague, send
  it back. An empty evidence table row is a blocker.
-->
<!--
  Three things this PR body needs to do:
    1. Let a reviewer orient in under 60 seconds — problem, fix, where to look
    2. Show the change is safe to ship — tested scenarios, no regressions
    3. Leave enough context that someone in 18 months doesn't have to
       reconstruct your reasoning from the diff

  Fill in every section. Delete the > prompt text before opening — it's
  for you, not the reviewer. PRs opened with prompts still visible will
  be sent back.
-->

## Summary

> One sentence. What was broken or missing, and what does this PR do about it?
> Write it so a colleague skimming the PR list gets it without clicking through.

<!-- closes #NNNN -->

---

## Why

> What forced this change? A bug surfaced, a dependency was vulnerable, behaviour was wrong?
> Name the alternatives you ruled out and say why. "None considered" is a problem.
> Someone reading this in a year should understand the trade-off without the Slack thread.

**Driver:**
<!-- Who hit this problem? What happened? -->

**Alternatives rejected:**
<!-- Name them. "None considered" is wrong — something was always considered, even "do nothing". -->

---

## What changed

> What modules/files did you touch? The diff shows lines — this explains what the diff *means*.
> Keep it short. If it needs more than a paragraph, the PR is probably too big.

**Affected:** <!-- e.g. inji/filters.py · tests/test_filters.py -->

<details>
<summary>Breaking changes</summary>

<!-- Delete this section entirely if the PR has no breaking changes. -->

- [ ] This PR has breaking changes — PR title uses `feat!:` or `fix!:`

| Area | Detail |
|------|--------|
| CLI flags / options | <!-- added / removed / renamed --> |
| Template behaviour | <!-- what changes in rendered output --> |
| Python API | <!-- public interface changes --> |

**Migration — before and after:**
```
# Before


# After

```

</details>

---

## Risk and review focus

> You wrote the code. Tell the reviewer where to look and what could go wrong.
> A reviewer who has to guess where the risk is will either miss it or check everything.

**Look here first:** <!-- The part most likely to be wrong is... -->

**Edge cases left for later:**
<!-- What did you think about but deliberately skip? Say why. -->

**Skip:** <!-- What looks like it changed but didn't need manual attention? -->

**Dependencies:** <!-- Does this PR depend on another PR landing first? -->

---

## Evidence

> A checkbox with no link is not evidence. Fill in the table.

| Gate | Result |
|------|--------|
| CI (lint · test · security-audit) | TBD |
| Peer review | ❌ not yet |

**Scenarios tested:**
<!-- Name them. "All tests pass" is not a scenario. -->
<!-- At minimum: happy path and at least one failure/edge path. -->

---

<details>
<summary>Pre-submission checklist</summary>

**Standards**
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/) format
- [ ] Each commit is atomic — code + tests + docs together
- [ ] Self-review complete — no debug statements, no dead code

**Tests**
- [ ] `just test` passes locally (syntax → lint → unit)
- [ ] New behaviour covered by tests
- [ ] No regressions to existing tests

**Security**
- [ ] No hardcoded secrets or credentials
- [ ] Input validation in place where needed

**GenAI**
- [ ] This PR contains code generated with GenAI assistance _(leave unchecked if no GenAI used)_
- [ ] All generated code has been reviewed, tested, and validated

</details>
