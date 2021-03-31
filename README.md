[![Pythons](https://img.shields.io/badge/python-3.5%E2%80%933.9%20%7C%20pypy-blue.svg)](.travis.yml)
[![Build Status](https://travis-ci.org/shalomb/inji.svg?branch=develop)](https://travis-ci.org/shalomb/inji)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/shalomb/inji/badges/quality-score.png?b=develop)](https://scrutinizer-ci.com/g/shalomb/inji/?branch=develop)
[![Code Coverage](https://scrutinizer-ci.com/g/shalomb/inji/badges/coverage.png?b=develop)](https://scrutinizer-ci.com/g/shalomb/inji/?branch=develop)
[![Code Intelligence Status](https://scrutinizer-ci.com/g/shalomb/inji/badges/code-intelligence.svg?b=develop)](https://scrutinizer-ci.com/code-intelligence)

![inji](./inji-logo.png)

Inji renders static
[jinja2](https://jinja.palletsprojects.com/en/2.11.x/)
templates.

Templates may be parametrized in which case inji can be given one or more
YAML vars files to source parameters used in the templates.

Useful in CI/CD scenarios where
[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
configuration is necessary and templating/parametrization is a
usable pattern.

### Installation

```
python3 -m pip install inji   #  or use pip3/pip, requires python >= 3.6 (may work on 3.5)
```

### Usage

##### Render a Jinja2 template

```
$ system=$(< /etc/hostname)
$ startime=$(date +%FT%T%z)

$ echo 'Reporting from {{ node }}, it is now {{ time }}' \
    | inji --k node="$system" -k time="$startime"
Hello from leto, it is now 2021-03-29T09:54:56+0200

```

Or from a file

```
$ inji jello-star-motd.j2 -k ... > /etc/motd
```

##### Render a template passing vars in a JSON object

JSON allows you to pass configuration in complex/multi-dimensional objects.

```
$ echo '
node : {{ node.name }}
time : {{ node.time }}
' > template.j2

$ inji template.j2 -j '{
  "node":{
    "name":"'$(</etc/hostname)'", // Note the "interpolation" of shell commands
    "time":"'$(date)'"            // here with the quoting.
  }
}'
```

##### Render a template passing vars from a YAML file


```
inji motd.j2 --vars-file=production.yaml
```

vars files must contain valid
[YAML documents](https://yaml.org/spec/1.2/spec.html#id2800132)
and can hold either simple
[scalars](https://yaml.org/spec/1.2/spec.html#id2760844)
or
[collections](https://yaml.org/spec/1.2/spec.html#id2759963).
Your jinja templates can then reference parameters/variables inside these
varsfiles depending on your context.

##### Multiple docker images from a single Dockerfile

A trivial case is building multiple docker images from a base Dockerfile.

Anyone who has maintained a project like this finds themselves having to
maintain multiple Dockerfiles, one-per-image even though the differences
between each Dockerfile are trivial. Such a
[WET approach](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself#DRY_vs_WET_solutions)
where copy-paste duplication is rife knows of painful maintenance
when the structure of the Dockerfile has to change, etc.

Instead, to [DRY](https://wiki.c2.com/?DontRepeatYourself) things up, consider
how paramertrization or templating addresses the issue.

```
$ cat Dockerfile.j2
FROM {{ distribution }}:{{ version }}    # These jinja2 vars are set by inji
                                         # from travis' environment variables

MAINTAINER http://my.org/PlatformOps

ENV container       docker
ENV distribution {{ distribution }}
ENV version      {{ version }}-{{ ref }} # `ref` is set at inji's CLI

{% if distribution == 'centos' %}        # Conditional execution
RUN yum -y update && yum clean all
{% endif %}

{% if distribution == 'debian' %}
RUN apt update -qq && apt upgrade -y
{% endif %}

{% if distribution == 'fedora' %}
RUN dnf -y update && dnf clean all
{% endif %}

RUN my-awesome-build-script {{ distribution }} {{ version }}

ENTRYPOINT ["/opt/bin/myserv"]
```

Then a CI build job (e.g. Travis CI) using inji would look like this.

```
$ cat .travis.yml
---
language: python
sudo: required
services:
  - docker

env:

  - distribution: centos
    version: 7

  - distribution: centos
    version: 8

  - distribution: debian
    version: stretch

  - distribution: debian
    version: buster

  - distribution: fedora
    version: 28

  - distribution: fedora
    version: 29

before_script:
  - pip install inji

script:
  - >
    inji Dockerfile.j2 --kv-config ref="$CI_COMMIT_REF_NAME" |
      docker build --pull --tag "myimage:$distribution-$version" -
  - docker push --all-tags "myimage"
...
```

##### Render a template using variables from multiple vars files

```
$ inji nginx.conf.j2             \
      --vars-file=web-tier.yaml  \
      --vars-file=eu-west-1.yaml \
      --vars-file=prod.yaml    > /etc/nginx/sites-enabled/prod-eu-west-1.conf
```

Here, variables from files specified later on the command-line
will override those from files specified before
(prod.yaml supercedes eu-west-1.yaml, etc).

This is especially useful in managing layered configuration where different
tiers of a deployment enforce/provide different parameters.

##### Using directory configuration overlays

An inevitable practice is using multiple smaller configuration files
to avoid the growing pains of huge configuration files,
to source configuration from different sources,
improve churn, reduce friction, etc, etc, etc.
Here, explicitly naming configuration files for inji to use becomes
a new pain point.

With overlay directories, inji naively reads in all yaml files from a directory
and compiles a combined configuration object before using that in rendering
a template.

```
$ tree conf/
conf/
├── dev
│   ├── service-discovery.yaml
│   ├── load-balancer-ip.yaml
│   ├── modules.yaml
│   └── sites.yaml
├── prod
│   ├── service-discovery.yaml
│   ├── load-balancer-ip.yaml
│   ├── modules.yaml
│   └── sites.yaml
└── stage
    ├── service-discovery.yaml
    ├── load-balancer-ip.yaml
    ├── modules.yaml
    └── sites.yaml
3 directories, 9 files

$ inji  nginx.conf.j2 \  # here $CI_ENV is be some variable your CI system
        --overlay="conf/$CI_ENV" \  # sets holding the name of the target deployment
        > nginx.conf                # e.g. dev, stage, prod
```

### Parameter sourcing and precedence order

Parameters  (configuration)  can  be   specified  and  sourced  from  multiple
sources. The  order of parameters  sourced and their precedence  is [12-factor
friendly](https://12factor.net/config)  and  is done  as  set  out here  (from
lowest-to-highest precedence).

- Default configuration file (`.inji.y*ml` or `inji.y*ml`) in current directory.
- Overlay directories - last file sorted alphabetically wins
- Named configuration file - last one specified wins
- Environmental variables - last one specified wins
- CLI JSON strings - last one specified wins
- CLI KV strings - last one specified wins
- Template parameters - last one specified wins (Jinja2 order)

### Examples

This is a very contrived example showing how to orient a `.gitlab-ci.yml`
towards business workflows -
a multi-stage CI/CD deployment pipeline expedited by Gitlab.

Note the use of complex objects in the parameters.

```
$ cat .gitlab-ci.vars
---
project:
  name: snowmobile
  id:   https://gitlab.com/snowslope/snowmobile.git
  url:  https://snowmobile.example.com/

deployer:
  image: snowmobile-deployer:latest

# This serves as the more succinct business abstract

environments:

  - name: snowmobile-env_dev
    type: dev
    region: us-east-1
    ci_url:  https://snowmobile-dev.env.example.com/
    branches:
      - /^[0-9]+\-.*/  # Match feature branches that have
                       # a ticket number at the start of the branch name

  - name: snowmobile-env_stage
    type: stage
    region: eu-west-2
    ci_url:  https://snowmobile-stage.env.example.com/
    branches:
      - master         # Deploy to stage only after merge request is complete

  - name: snowmobile-env_prod
    type: production
    region: eu-west-1
    ci_url:  https://snowmobile.env.example.com/
    branches:
      - tags           # Only deploy tagged releases to production

...
```

```
$ cat .gitlab-ci.j2
---

# >>>>>>>>>>>>>
# >> WARNING >>   This file is autogenerated!!
# >> !!!!!!! >>   Edit .gitlab-ci.{j2, vars} instead and `make gitlab-ci-yml`
# >>>>>>>>>>>>>   All edits will be lost on the next update

# This template when rendered with parameters from the above varsfile
# produces the actual fuller .gitlab-ci.yml file

stages:
{% for env in environments %}
  - '{{ env.name }}:provision'
  - '{{ env.name }}:validate'
  - '{{ env.name }}:deploy'
  - '{{ env.name }}:test'
  - '{{ env.name }}:destroy'
{% endfor %}
  - 'docs:publish'

variables:
  project:             {{  project.name }}
  project_id:          '{{ project.id   }}'
  project_url:         {{  project.url  }}

{% for env in environments %}

# {{ env.type }} Run infrastructure provisioning
'provision:{{ env.name }}':
  stage: '{{ env.name }}:provision'
  environment:
    name: {{ env.type }}/$SITE/$CI_COMMIT_REF_NAME
    url:  {{ env.ci_url }}
  variables:
    SITE:                {{ env.name }}
    CI_ENVIRONMENT_TYPE: {{ env.type }}
    REGION:              {{ env.region }}
    CI_URL:              {{ env.ci_url }}
  image:  {{ deployer.image }}
  script:
    - snowmobile-ctl provision

  {% if env.branches -%}
  only: {{ env.branches }}
  {% endif %}

# {{ env.type }} Run application deployment
'deploy:{{ env.name }}':
  stage: '{{ env.name }}:deploy'
  # ...
  script:
    - snowmobile-ctl deploy

# {{ env.type }} Run smoke tests
'test:{{ env.name }}':
  stage: '{{ env.name }}:test'
  # ...
  script:
    - snowmobile-ctl smoke-test

{% endfor %}

# vim:ft=yaml
...
```

To then update the `.gitlab-ci.yml`, run inji with the above.

```
$ inji .gitlab-ci.j2 \
       --vars-file .gitlab-ci.vars > .gitlab-ci.yml
```

WARNING: Edits to the above files are not automatically reflected in
`.gitlab-ci.yml` and some other mechanism using inji to render the latter needs
to be run before Gitlab acts upon it. e.g. Using a
[git commit hook](https://git-scm.com/docs/githooks#_pre_commit)
or
[gitattribute filter](https://www.bignerdranch.com/blog/git-smudge-and-clean-filters-making-changes-so-you-dont-have-to/)
, etc.

```
$ cat .githooks/pre-commit
#!/bin/sh

set -e

source_update=0
file_update=0

# NOTE: git diff --exit-code ... returns 1 if file has changed
git diff --exit-code .gitlab-ci.j2   || source_update=1
git diff --exit-code .gitlab-ci.vars || source_update=1
git diff --exit-code .gitlab-ci.yaml || file_update=1

if [ "$file_update" = 1 ]; then
  echo >&2 ".gitlab-ci.yaml updated without updating templates (.gitlab-ci.{j2,vars})"
  exit 1
fi

[ "$source_update" = 0 ] && exit 0

inji .gitlab-ci.j2 --vars-file .gitlab-ci.vars > .gitlab-ci.yaml

git add .gitlab-ci.yaml &&
  git commit --amend -C HEAD --no-verify
```

### Etymology

Why the name inji?

Apart from keeping to the UNIX tradition of short (memorable?)
 command names, _inji_ is a 4-letter near-anagram of _Jinja_.

[_inji_](https://en.wikipedia.org/wiki/Ginger#Etymology) (_/ɪndʒi:/_)
also happens to be the Dravidian word and ostensibly the source of the
English word Ginger, of which jinja is a partial homophone.

### TODO

Only potential ideas so far - No commitment is made.

* [ ] Read config from JSON/TOML files?
* [ ] Manage collections of templates e.g. `*.j2`
* [ ] Dry-run syntax checking
* [ ] Document patterns driving the design and refactor docs
* [ ] Document use of macros
* [ ] Document use of vars collections
