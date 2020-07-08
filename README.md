## inji

Render static jinja2 template files, optionally specifying parameters
contained in vars files.

Useful in CI/CD scenarios to keep configuration
[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
across environments.

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
Your jinja templates must reference these accordingly.

e.g.
```
$ cat vars.yaml
sage: victor
section: indigo

envoy:
  names:
    - alice
    - bob
    - chuck
  location: metaverse
  origin: world's end
```

```
$ cat hello-world.j2
Hello {{ envoy.names | join(', ') }}!!

I am {{ sage }}, the {{ section }} sage.

It seems you are at {{ envoy.location }} today and come from {{ envoy.origin }}.
```

```
$ inji -t hello-world.j2 -v vars.yaml
Hello alice, bob, chuck!!

I am victor, the indigo sage.

It seems you are at metaverse today and come from world's end.
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

