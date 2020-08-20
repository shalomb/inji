#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-builtin-filters
# https://www.webforefront.com/django/usebuiltinjinjafilters.html

import re
import sys
import os
import csv

filters = dict(

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

  keys = (
    """
    Return the keys of a dict passed in
    """,
    lambda d: d.keys()
  ),

  values = (
    """
    Return the values of a dict passed in
    """,
    lambda d: d.values()
  ),

  items = ( """
    Select items specified by indexes from the list passed in
    e.g. range(1,10) | items(0,2,5,-3,-2)
    """,
    lambda *n: list(n[0][x] for x in n[1:])
  ),

  wrap = ( """
    Wrap value with "parantheses" specified in format (default "()")
    """,
    lambda v, t='()': '{}{}{}'.format(t[0], v, t[1])
  ),

  to_csv = ( """
    Split a string delimited by commas and return items in a list
    """,
    lambda v: list(csv.reader(v))[0]  # magic number is for single line of text
  ),

  to_url = ( """
    Take values from a dict passed in and
    return a string formatted in the form of a URL
    """,
    lambda v, f='https://{hostname}':
                  f.format(**v) ),
)

if 'USE_ANSIBLE_SUPPORT' in os.environ.keys():
  from .ansible import FilterModule
  filters.update(FilterModule().filters())

for k,v in filters.items():
  setattr(sys.modules[__name__], k, v[1])
