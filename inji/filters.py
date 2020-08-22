#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-builtin-filters
# https://www.webforefront.com/django/usebuiltinjinjafilters.html

from datetime import datetime, timezone
import ast
import csv
import os
import re
import sys
import time

# TODO
# Encapsulating filters in this way is great but it does little for their
# test coverage (nice trick to fool pycoverage eh!)
# Set these up for proper unit (not end-to-end) tests.

filters = dict(

  env_override = (
  """
    Allow for a value set in the environment to override a given value
    e.g. url | env_override("URL")
    """,
    lambda v, k: os.getenv(k, v)
  ),

  format_dict = (
  """
    Given a dict as value, return a formatted string as specified in format.
    e.g. url | urlsplit | format_dict("{scheme}://{hostname}:8080/{path}/")
    """,
    lambda v, f: f.format(**v)
  ),

  format_list = (
  """
    Given a list as value, return a formatted string as specified in format.
    e.g. url | urlsplit | format_list("{0}://{1}")
    """,
    lambda v, f: f.format(*v)
  ),

  from_csv = (
    """
    Split a string delimited by commas and return items in a list.
    e.g. (foo,) | from_csv  # note the (foo,) as csv.reader is expecting lines
    """,
    lambda v: list(csv.reader(v))[0]  # magic number is for single line of text
  ),

  from_literal = ( """ Parse a string using ast.literal_eval() """,
    lambda v: ast.literal_eval(v)
  ),

  items = ( """
    Select items specified by indexes from the list passed in
    e.g. range(1,10) | items(0,2,5,-3,-2)
    """,
    lambda *n: list(n[0][x] for x in n[1:])
  ),

  keys = (
    """
    Return the keys of a dict passed in
    """,
    lambda d: d.keys()
  ),

  strftime = ( """ For a given date, return a date string in strftime(3) format """,
    lambda v, f='%F %T%z', tz='UTC': v.strftime(f),
  ),

  to_date = ( """ For a given string, try and parse the date """,
    # NOTE This isn't resilient against leapseconds
    # https://stackoverflow.com/questions/1697815/how-do-you-convert-a-time-struct-time-object-into-a-datetime-object#comment31967564_1697838
    lambda v, f='%Y-%m-%d %H:%M:%S.%f': datetime( *(time.strptime(v, f)[:5]) )
  ),

  to_url = ( """
    Take values from a dict passed in and
    return a string formatted in the form of a URL
    """,
    lambda v, f='https://{hostname}':
                  f.format(**v)
  ),

  values = (
    """
    Return the values of a dict passed in
    """,
    lambda d: d.values()
  ),

  wrap = ( """
    Wrap value with "parantheses" specified in format (default "()")
    """,
    lambda v, t='()': '{}{}{}'.format(t[0], v, t[1])
  ),

)

if 'USE_ANSIBLE_SUPPORT' in os.environ.keys():
  from .ansible import FilterModule
  filters.update(FilterModule().filters())

for k,v in filters.items():
  setattr(sys.modules[__name__], k, v[1])
