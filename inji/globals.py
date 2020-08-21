#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# hold global variables and functions for direct use in templates
# https://jinja.palletsprojects.com/en/2.11.x/api/#the-global-namespace
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-global-functions

from datetime import datetime, timezone
import socket
import sys

_globals = dict(

  now  = ( """ Return the timestamp for datetime.now() """,
    lambda : datetime.now()
  ),

  date  = ( """ Return the timestamp for datetime.now() """,
    datetime.now()  # variable
  ),

  strftime = ( """ Return a date string specified in strftime(3) format """,
    lambda f='%F %T%z', tz='UTC':
      datetime.now(timezone.utc if tz == 'UTC' else None).strftime(f)
  ),

  hostname = ( """ Return the current hostname """,
    lambda : socket.gethostname()
  ),

)

for k,v in _globals.items():
  setattr(sys.modules[__name__], k, v[1])
