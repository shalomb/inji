## inji

Render a jinja template from file to stdout.

Optionally, variables can be supplied to inji in the form of vars (yaml)
files where invocation data/configuration can be help separately.
(e.g. per-environment configuration).

Multiple varsfiles can be specified and inji will attempt to merge data from
the files with data from the later files overlaying data in earlier ones.

### Usage

Render a lone Jinja2 template.

```
inji --template=jello-world.j2
```

Render a template passing vars from a YAML file.

```
inji --template=motd.j2 --vars-file=vars.yaml
```

Render a template passing 2 variable files containing configuration with the
second one overriding any configuration from the first.

```
inji --template=nginx.conf.j2 --vars-file=org.yaml --vars-file=dev-env.yaml
```

NOTE

This is a python2 implementation but should work under python3


