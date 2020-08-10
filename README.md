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
# requires python3

python3 -m pip install inji    #  or pip3/pip install inji
```

### Usage

##### Render a Jinja2 template

```
inji --template=jello-world.j2
```

or read the template in from STDIN

```
my-generator | inji
```

##### Render a template passing vars from a YAML file.

```
inji --template=motd.j2 --vars-file=production.yaml
```

vars files must contain valid
[YAML documents](https://yaml.org/spec/1.2/spec.html#id2800132)
and can hold either simple
[scalars](https://yaml.org/spec/1.2/spec.html#id2760844)
or
[collections](https://yaml.org/spec/1.2/spec.html#id2759963).
Your jinja templates then reference these accordingly depending on your context.

e.g.

A typical case is building multiple docker images - without the assistance
of a templating tool, you may have to keep and maintain several Dockerfiles
and corresponding build commands for each image
- but imagine the yucky prospects of maintaining that kind of
[WET approach](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself#DRY_vs_WET_solutions).

Instead, to DRY things up, consider a templated Dockerfile like this

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

Then a Travis CI build job using inji would look like this.

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
  - json_config='{ "ref": "'"$CI_COMMIT_REF_NAME"'" }'
  - >
    inji --template Dockerfile.j2 --config "$json_config" |
      docker build --pull --tag "myimage:$distribution-$version" -
  - docker push --all-tags "myimage"
...
```

##### Render a template using variables from multiple vars files

```
inji --template=nginx.conf.j2    \
      --vars-file=web-tier.yaml  \
      --vars-file=eu-west-1.yaml \
      --vars-file=prod.yaml  > /etc/nginx/sites-enabled/prod-eu-west-1.conf
```

Here, variables from files specified later on the command-line
will override those from files specified before
(prod.yaml supercedes eu-west-1.yaml, etc).

This is especially useful in managing layered configuration where different
tiers of a deployment enforce/provide different parameters.

##### Using directory overlays

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

$ inji  --template=nginx.conf.j2 \  # here $CI_ENV is be some variable your CI system
        --overlay="conf/$CI_ENV" \  # sets holding the name of the target deployment
        > nginx.conf                # e.g. dev, stage, prod
```

### Fuller Example

This is a very contrived example showing how to orient a `.gitlab-ci.yml`
towards business workflows -
a multi-stage CI/CD deployment pipeline expedited by Gitlab.

```
$ cat .gitlab-ci.yml.vars
---
project:
  name: snowmobile
  id:   https://gitlab.com/snowslope/snowmobile.git
  url:  https://snowmobile.example.com/

deployer:
  image: snowmobile-deployer:latest

# This serves as a more succinct business abstract

environments:

  - name: snowmobile-env_dev
    type: dev
    datacenter: eu-west-1
    url:  https://snowmobile-dev.env.example.com/
    only:
      - /^[0-9]+\-.*/  # Match feature branches that have
                       # a ticket number at the start of the branch name

  - name: snowmobile-env_stage
    type: stage
    datacenter: eu-west-2
    url:  https://snowmobile-stage.env.example.com/
    only:
      - master         # Deploy to stage only after merge request is complete

  - name: snowmobile-env_prod
    type: production
    datacenter: eu-west-1
    url:  https://snowmobile.env.example.com/
    only:
      - tags           # Only deploy tagged releases to production

...
```

```
$ cat .gitlab-ci.yml.j2
---

# >>>>>>>>>>>>>
# >> WARNING >>   This file is autogenerated!!
# >>>>>>>>>>>>>   All edits will be lost on the next update.

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

# {{ env.type }} Run tenant provisioning, runner setup on shared runner
'provision:{{ env.name }}':
  stage: '{{ env.name }}:provision'
  environment:
    name: {{ env.type }}/$SITE/$CI_COMMIT_REF_NAME
    url:  {{ env.url }}
  variables:
    SITE:                {{ env.name }}
    CI_ENVIRONMENT_TYPE: {{ env.type }}
    DATACENTER:          {{ env.datacenter }}
    URL:                 {{ env.url }}
  image:  {{ deployer.image }}
  script:
    - snowmobile-ctl provision

  {% if env.only -%}
  only: {{ env.only }}
  {% endif %}

# {{ env.type }} Run deployment
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
$ inji -t .gitlab-ci.yml.j2 \
       -v .gitlab-ci.yml.vars > .gitlab-ci.yml
```

WARNING: Edits to the above files are not automatically reflected in
`.gitlab-ci.yml` and some other mechanism using inji to render the latter needs
to be run before Gitlab acts upon it. e.g. Using a
[git commit hook](https://git-scm.com/docs/githooks#_pre_commit)
or
[gitattribute filter](https://www.bignerdranch.com/blog/git-smudge-and-clean-filters-making-changes-so-you-dont-have-to/)
, etc.

e.g.
```
$ cat .githooks/pre-commit
#!/bin/sh

set -e

inji -t .gitlab-ci.yml.j2 -v .gitlab-ci.yml.vars > .gitlab-ci.yml

# NOTE: git diff --exit-code ... returns 1 if file has changed
if ! git diff --exit-code .gitlab-ci.yml; then
  git add .gitlab-ci.yml &&
    git commit --amend -C HEAD --no-verify
fi
```

### Etymology

Why the name inji?

_inji_ is named in keeping of the UNIX tradition of short (memorable?)
 command names. In this case, it is a 4-letter near-anagram of _Jinja_.

[_inji_](https://en.wikipedia.org/wiki/Ginger#Etymology) (_/ɪndʒi:/_)
also happens to be the Dravidian word and ostensibly the source of the
English word Ginger, of which jinja is a partial homophone.

### TODO

Only potential ideas so far - No commitment is made.

* [ ] Read config from JSON/TOML files?
* [ ] Manage collections of templates e.g. `*.j2`
* [ ] Dry-run syntax checking
