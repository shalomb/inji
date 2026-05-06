---
name: Feature Request
about: Suggest a new filter, global, CLI option, or other capability
title: "feat: "
labels: "enhancement"
assignees: ""
---

## Before Opening This Issue

- [ ] I searched [existing issues](https://github.com/shalomb/inji/issues) for duplicates
- [ ] I checked the [README](https://github.com/shalomb/inji#readme) — it's not already supported
- [ ] I understand there is no guaranteed timeline for implementation

---

## Objective *(required)*

> One-line summary: what are we building and why?
> e.g. "Add a `to_json` filter so templates can serialise dicts inline"

## Context

> Why does this matter?
> - What problem does it solve?
> - What use cases or workflows does it enable?

## Success Criteria *(required)*

> How will we know this is done? Make them specific and testable.

- [ ] [e.g. New filter `to_json` available in templates]
- [ ] [e.g. Works with nested dicts and lists]
- [ ] [e.g. Covered by unit tests]
- [ ] [e.g. Documented in README]

## Suggested Work Breakdown

> Major tasks (rough guidance for the developer):

1. **Implementation** (~X hours)
2. **Tests** (~X hours)
3. **Docs** (~X hours)

## Desired Usage

> Show what using this feature would look like:

```bash
# template
{{ data | to_json }}

# command
$ inji template.j2 -k data='{"key": "value"}'

# expected output
{"key": "value"}
```

## Alternatives Considered

> What other approaches did you consider, and why is this the right one?

## Additional Context

> Anything else — links, prior art, related issues.
