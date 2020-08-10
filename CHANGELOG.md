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
