#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# hold global variables and functions for direct use in templates
# https://jinja.palletsprojects.com/en/2.11.x/api/#the-global-namespace
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-global-functions

from datetime import datetime, timezone
import subprocess
import socket
import sys
import platform as _platform
import inspect

def _os_release(k=None):
  ret = {}
  for line in open('/etc/os-release').read().strip().split('\n'):
    k,v = line.split('=', 1)
    ret[k] = v.strip('"')
  return ret

def _cmd(args):
  return subprocess.check_output(args.split(' ')).decode('utf-8').strip()

"""
_globals contains the dictionary of functions (implemented as lambda functions)
or variables (regular values) that are accessible inside template expressions.
"""
_globals = dict(

  date  = ( """ Return the timestamp for datetime.now() """,
    datetime.now()  # variable
  ),

  host_id = ( """ Return the host's ID """,
    lambda : _cmd('hostid')
  ),

  fqdn = ( """ Return the current host's fqdn """,
    lambda : socket.getfqdn()
  ),

  hostname = ( """ Return the current host's name """,
    lambda : socket.gethostname()
  ),

  machine_id = ( """ Return the machine's ID """,
    open('/etc/machine-id').read().strip()  # variable
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
    lambda v: _cmd(v)
  ),

)


for k,v in _globals.items():
  setattr(sys.modules[__name__], k, v[1])
