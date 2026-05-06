[![Pythons](https://img.shields.io/badge/python-3.5%E2%80%933.9%20%7C%20pypy-blue.svg)](.travis.yml)
[![Build Status](https://travis-ci.org/shalomb/inji.svg?branch=develop)](https://travis-ci.org/shalomb/inji)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/shalomb/inji/badges/quality-score.png?b=develop)](https://scrutinizer-ci.com/g/shalomb/inji/?branch=develop)
[![Code Coverage](https://scrutinizer-ci.com/g/shalomb/inji/badges/coverage.png?b=develop)](https://scrutinizer-ci.com/g/shalomb/inji/?branch=develop)

![inji](./inji-logo.png)

Inji renders static [Jinja2](https://jinja.palletsprojects.com/) templates right from the command line.

If you've ever found yourself maintaining ten nearly identical Dockerfiles, or wrestling with a massive 1,000-line CI/CD configuration file, you know the pain of copy-paste development. Inji fixes this. You hand it a template and some variables (from YAML, JSON, or your environment), and it generates the final file. No magic, just clean, DRY configuration.

### Installation

```bash
pip install inji
```
*(Requires Python 3.6+)*

### Why use this?

Configuration files get messy fast. When you split them up or try to reuse them across different environments (dev, stage, prod), you usually end up copying and pasting the same boilerplate. Inji lets you use standard Jinja2 templating to keep your configuration sane and manageable.

### Usage

#### The Basics
Pass variables directly from the command line:

```bash
$ echo 'Reporting from {{ node }}, it is now {{ time }}' \
    | inji -k node="$(hostname)" -k time="$(date -u)"
Reporting from leto, it is now Thu Mar 29 09:54:56 UTC 2021
```

Or render a file:

```bash
$ inji motd.j2 -k env="production" > /etc/motd
```

#### YAML and JSON variables
Typing out variables is fine for quick scripts, but you'll probably want to store them in files. 

```bash
$ inji nginx.conf.j2 --vars-file=production.yaml > nginx.conf
```

JSON works too, which is handy if you need to pass nested objects on the fly:

```bash
$ inji template.j2 -j '{"node": {"name": "leto", "role": "db"}}'
```

#### Layering configurations
Real-world deployments usually mean layering configs. Maybe you have a base web config, overridden by a specific region, which is then overridden by the production environment. Inji handles this gracefully: later files override earlier ones.

```bash
$ inji nginx.conf.j2 \
      --vars-file=web-tier.yaml \
      --vars-file=eu-west-1.yaml \
      --vars-file=prod.yaml > /etc/nginx/sites-enabled/prod-eu-west-1.conf
```

#### Overlay Directories
If you have a bunch of small config files scattered in a directory (say, `conf/prod/`), you can just point Inji at the whole folder. It reads all the YAML files, merges them into one configuration object, and renders your template.

```bash
$ inji nginx.conf.j2 --overlay="conf/prod" > nginx.conf
```

### Order of Precedence
When you're pulling variables from everywhere, who wins? Inji follows a [12-factor-friendly](https://12factor.net/config) hierarchy. From lowest to highest priority:

1. Default config file (`.inji.yaml` or `inji.yaml` in the current directory)
2. Overlay directories (last file sorted alphabetically wins)
3. Named `--vars-file` arguments (last one specified wins)
4. Environment variables
5. CLI JSON strings (`-j`)
6. CLI key-value pairs (`-k`)
7. Variables defined inside the Jinja2 template itself

### Built-in Superpowers

Inji isn't just plain Jinja2—it comes loaded with custom globals and filters out of the box so you don't have to keep piping through `sed`, `awk`, or `curl`.

#### Environment & Git Context
Need to tag a Docker image with the current git commit or branch? Inji has globals for that:

```jinja
VERSION: {{ git_tag() }}
COMMIT: {{ git_commit_id() }}
BRANCH: {{ git_branch() }}
```

#### OS & Network Introspection
If you're generating configs on the fly inside a server or CI runner, you can tap directly into the host's environment:

```jinja
HOSTNAME: {{ hostname() }}
PUBLIC_IP: {{ whatismyip() }}
DISTRO: {{ os_release('PRETTY_NAME') }}
```

#### HTTP Requests & APIs
You can even fetch JSON from an API directly inside your template using `GET()`:

```jinja
{% set my_ip_info = ip_api() %}
REGION: {{ my_ip_info.regionName }}
COUNTRY: {{ my_ip_info.country }}
```

#### Running Shell Commands
Need something really specific? Just use the `run()` global to execute any shell command and capture its stdout:

```jinja
LOAD_AVERAGE: {{ run("uptime | awk '{print $10}'") }}
```

#### Custom Filters
Inji bundles dozens of helpful list, string, and formatting filters to manipulate data cleanly inside your templates.

```jinja
# Extract specific keys from an environment variable fallback
API_URL: {{ default_url | env_override("API_URL") }}

# Parse CSV strings into lists
{% set ports = "80,443,8080" | from_csv %}

# Read a file's contents directly into a template variable
{% set local_key = "id_rsa.pub" | cat %}
```

### Real-world Examples

#### DRY Dockerfiles
Instead of maintaining a separate `Dockerfile` for CentOS, Debian, and Fedora, write one `Dockerfile.j2`:

```jinja
FROM {{ distribution }}:{{ version }}

ENV container docker
ENV distribution {{ distribution }}
ENV version {{ version }}-{{ ref }}

{% if distribution == 'centos' %}
RUN yum -y update && yum clean all
{% elif distribution == 'debian' %}
RUN apt update -qq && apt upgrade -y
{% elif distribution == 'fedora' %}
RUN dnf -y update && dnf clean all
{% endif %}

RUN my-awesome-build-script {{ distribution }} {{ version }}
ENTRYPOINT ["/opt/bin/myserv"]
```

Then build it in your CI pipeline by passing the variables you need:
```bash
$ inji Dockerfile.j2 -k distribution=debian -k version=buster -k ref=$CI_COMMIT_REF_NAME | docker build --tag "myimage:debian-buster" -
```

#### Dynamic CI/CD Pipelines
You can even generate your `.gitlab-ci.yml` or GitHub Actions workflows dynamically. Define your environments in a `.vars` file and loop through them in a `.j2` template to stamp out identical jobs for dev, stage, and prod without duplicating all the YAML boilerplate. 

If you do this, just remember to use a `pre-commit` hook to ensure your rendered `.yml` file always stays in sync with your `.j2` template.

### What's with the name?
Inji is a four-letter near-anagram of Jinja. It also happens to be the Dravidian word for ginger, which is a partial homophone for Jinja. Naming things is hard, but we liked this one.

### TODO
Only potential ideas so far—no commitment is made:

* [ ] Read config from JSON/TOML files natively
* [ ] Manage collections of templates (e.g., `*.j2`)
* [ ] Dry-run syntax checking
* [ ] Document patterns driving the design and refactor docs
* [ ] Document use of macros and vars collections