#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# hold global variables and functions for direct use in templates
# https://jinja.palletsprojects.com/en/2.11.x/api/#the-global-namespace
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-global-functions

import builtins
from datetime import datetime, timezone
import json
import inspect
import markdown as _markdown
import platform as _platform
import socket
import sys
import re

from . import utils

def _os_release(k=None):
  ret = {}
  for line in open('/etc/os-release').read().strip().split('\n'):
    k,v = line.split('=', 1)
    ret[k] = v.strip('"')
  return ret

"""
_globals contains the dictionary of functions (implemented as lambda functions)
or variables (regular values) that are accessible inside template expressions.
"""
_globals = dict(

  bacon_ipsum = ( """ Return N paragraphs of bacon-ipsum """,
    lambda n=3: utils.get(
      'https://baconipsum.com/api/?type=all-meat&paras={}&start-with-lorem=1&format=html'.format(n)
    )
  ),

  cat  = ( """ Read a file in """,
    lambda *n: [ utils.load_file(x) for x in n ]
  ),

  date  = ( """ Return the timestamp for datetime.now() """,
    datetime.now()  # variable
  ),

  git_branch = ( """ Return the current git branch of HEAD """,
    lambda : utils.cmd(f"git rev-parse --abbrev-ref HEAD")
  ),

  GET = ( """ Issue a HTTP GET request against URL returning body content or an object if the response was JSON """,
    lambda url='http://httpbin.org/anything':
      utils.get(url)
  ),

  git_commit_id = ( """ Return the git commit ID of HEAD """,
    lambda fmt='%h': utils.cmd(f"git log --pretty=format:{fmt} -n 1 HEAD")
  ),

  git_remote_url = ( """ Return the URL of the named origin """,
    lambda origin='origin': utils.cmd(f'git remote get-url {origin}')
  ),

  git_remote_url_http = ( """ Return the HTTP URL of the named origin """,
    lambda origin='origin':
      re.sub( 'git@(.*):', 'https://\\1/',
        utils.cmd(f'git remote get-url {origin}')
      ),
  ),

  git_tag = ( """ Return the value of git describe --tag --always """,
    lambda fmt='current':
      utils.cmd('git describe --tag --always') if
        fmt=='current' else
        re.sub( '-[A-Fa-fg0-9\-]+$', '',
          utils.cmd('git describe --tag --always')
        )
  ),

  host_id = ( """ Return the host's ID """,
    lambda : utils.cmd('hostid')
  ),

  int = ( """ Cast value as an int """,
    lambda v: builtins.int(v)
  ),

  fqdn = ( """ Return the current host's fqdn """,
    lambda : socket.getfqdn()
  ),

  hostname = ( """ Return the current host's name """,
    lambda : socket.gethostname()
  ),

  machine_id = ( """ Return the machine's ID """,
    lambda :  utils.load_file('/var/lib/dbus/machine-id') or
              utils.load_file('/etc/machine-id')
  ),

  markdown = ( """ Load content from a markdown file and convert it to html """,
    lambda f,
      output_format='html5',
      extensions=[
        'admonition',
        'extra',
        'meta',
        'sane_lists',
        'smarty',
        'toc',
        'wikilinks',
        'wikilinks',
      ],
      extension_configs = {
        'codehilite': {
          'linenums': True,
          'guess_lang': False,
        }
      }
    : _markdown.markdown(
        utils.load_file(f),
        extensions=extensions,
        output_format=output_format
      )
  ),

  now  = ( """ Return the timestamp for datetime.now() """,
    lambda : datetime.now()
  ),

  os = ( """ Dictionary holding the contents of /etc/os-release """,
    _os_release()
  ),

  os_release = ( """ Lookup key in /etc/os-release and return its value """,
    lambda k: _os_release()[k]
  ),

  platform = ( """ Access functions in the platform module """,
    dict(set(inspect.getmembers(_platform, inspect.isfunction)))
  ),

  run = (
    """
    Run a command and return its STDOUT
    e.g. hello {{ run('id -un') }}
    """,
    lambda v: utils.cmd(v)
  ),

  ip_api = ( """ Return an attribute from the http://ip-api.com/json response object (i.e. status, country, countryCode, region, regionName, city, zip, lat, lon, timezone, isp, org, as, query) """,
    lambda key='country':
      utils.ip_api(key)
  ),

  whatismyip = ( """ Return the host's public (IPv4) address """,
    lambda : utils.whatismyip()
  ),

)


for k,v in _globals.items():
  setattr(sys.modules[__name__], k, v[1])
