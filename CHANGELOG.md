# Changelog

## [0.6.3](https://github.com/shalomb/inji/compare/v0.6.2...v0.6.3) (2026-06-23)


### Features

* Modernize inji to v0.6.0 — uv, hatchling, ruff, testing pyramid, justfile ([efe2ffc](https://github.com/shalomb/inji/commit/efe2ffc602174337827d85e895f51b4a1397cf60))


### Bug Fixes

* **ci:** Remove Test PyPI stage from publish workflow; update uv.lock ([2093f64](https://github.com/shalomb/inji/commit/2093f64699d0839f95c517e4e64d29d2bcf677bf))
* **ci:** Remove Test PyPI stage, fix action versions in publish.yml ([081c6ca](https://github.com/shalomb/inji/commit/081c6ca7bf4797ee6beb8baf1fadbb2aa84d64e5))
* **deps:** Upgrade authlib, urllib3, idna; bump dependency-review-action ([#28](https://github.com/shalomb/inji/issues/28)) ([69d787e](https://github.com/shalomb/inji/commit/69d787e65c86384d7a9fb9e217fd7f20ac539618))

## [0.6.2](https://github.com/shalomb/inji/compare/inji-v0.6.1...inji-v0.6.2) (2026-05-06)


### Bug Fixes

* **ci:** Remove Test PyPI stage, fix action versions in publish.yml ([081c6ca](https://github.com/shalomb/inji/commit/081c6ca7bf4797ee6beb8baf1fadbb2aa84d64e5))

## [0.6.1](https://github.com/shalomb/inji/compare/inji-v0.6.0...inji-v0.6.1) (2026-05-06)


### ⚠ Breaking Changes

* **python:** Minimum Python version raised from 3.5 to 3.12. Versions 3.5–3.11 are no longer supported.

### Features

* Modernize inji to v0.6.0 — uv, hatchling, ruff, testing pyramid, justfile ([efe2ffc](https://github.com/shalomb/inji/commit/efe2ffc602174337827d85e895f51b4a1397cf60))

0.5.1 2021-04-01T01:03:56
-------------------------

* Ensure more_itertools is a dependency that is installed in environments
  where it might not already be present. e.g. Cloudflare pages build envs

0.5.1 2021-04-01T00:44:04
-------------------------

* Add global functions to help with public IP address detection
* Update README.md to be a bit clearer (Still a major WIP)

0.5.0 2020-08-17T15:06:12
-------------------------

* Setup project under scrutinizer-ci for CI testing and code quality
  Fix minor issues and bugs
* Add support for passing in KV pairs at the CLI
* Add documentation on parameter precedence and other minor edits to README.md

0.4.0 2020-08-15T13:49:17
-------------------------

* Setup project under scrutinizer-ci for code quality in CI
* Fix duplicated code in tests
* Improve test titling, commentary
* Improve README.md

0.4.0 2020-08-10T23:38:21
-------------------------

* Fix bug with filename sort collation not being guaranteed.
  We now explicitly sort filenames under the C POSIX locale.
  Users should still consider using a file naming convention for ensuring
  filenames are collated to their expectations
  e.g. prefixing filenames with numbers
* Deprecate support for <= python 3.5
* Setup CI testing under Travis CI.
  Fix various small issues in Makefiles, coverage reporting.
* Report build and coverage status
* Improve CLI help messaging
* Improve repo README.md examples and layout

0.3.0 2020-08-06T01:46:57
-------------------------

* Support sourcing of vars from various sources in 12-factor app friendly ways
  (default config file, overlay directories, named config files, env vars,
   JSON args).
* Improve testing and coverage

0.2.1 2020-07-08T22:41:07
-------------------------

* Prepare metadata for Pypi releases to https://pypi.org/project/inji/
* Setup versioning to be derived from annotated git tags
