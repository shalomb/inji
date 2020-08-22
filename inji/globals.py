#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# hold global variables and functions for direct use in templates
# https://jinja.palletsprojects.com/en/2.11.x/api/#the-global-namespace
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-global-functions

from datetime import datetime, timezone
import inspect
import markdown as _markdown
import platform as _platform
import socket
import sys

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

  date  = ( """ Return the timestamp for datetime.now() """,
    datetime.now()  # variable
  ),

  host_id = ( """ Return the host's ID """,
    lambda : utils.cmd('hostid')
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

)


for k,v in _globals.items():
  setattr(sys.modules[__name__], k, v[1])
