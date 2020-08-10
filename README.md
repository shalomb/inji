## inji

Render static jinja2 template files, optionally specifying parameters
contained in vars files.

Useful in CI/CD scenarios where
[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
configuration is necessary and the reduction of copy-paste duplication
can be done through templating/parameterization.

### Installation

NOTE: Support for Python2 is now dropped. Python3 is required.

```
pip install inji
```

### Usage

##### Render a lone Jinja2 template.

```
inji --template=jello-world.j2
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
Your jinja templates then reference these accordingly.

e.g.

Building multiple docker image variants from a single template

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
  - inji -t Dockerfile.j2 -c '{"ref": "'"${CI_COMMIT_REF_NAME:-unknown}"'"}' > Dockerfile
  - docker build -t "myimage:$distribution-$version" .
  - docker push --all-tags "myimage"
...
```

Where the `Dockerfile.j2` template is something like

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

##### Render a template using variables from multiple vars files

```
inji --template=nginx.conf.j2    \
      --vars-file=web-tier.yaml  \
      --vars-file=eu-west-1.yaml \
      --vars-file=prod.yaml  > /etc/nginx/sites-enabled/prod-eu-west-1.conf
```

This is especially useful in managing layered configuration.
i.e. variables from files specified later on the command-line
will be overlain over those defined earlier.

### Etymology

_inji_ is named in keeping of the UNIX tradition of short (memorable?)
 command names.

_inji_ (_/ɪndʒi:/_) also happens to be the Tamil word for Ginger.
In this case, it is a near-anagram of _Jinja_ which ostensibly is a homophone
of Ginger (Zingiber).

### Example

This is a very contrived example showing how to orient a `.gitlab-ci.yml`
towards business workflows - in this case a 3-stage Gitlab CI/CD deployment
pipeline to production.

```
$ cat .gitlab-ci.yml.vars
---
project:
  name: snowmobile
  id:   https://gitlab.com/snowslope/snowmobile.git
  url:  https://snowmobile.example.com/

deployer:
  image: snowmobile-deployer:latest

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
