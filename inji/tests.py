#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# Hold custom jinja2 tests
# https://jinja.palletsprojects.com/en/2.11.x/api/#custom-tests
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-builtin-tests

from jinja2 import is_undefined
import re
import sys
import math
import os

def _is_prime(n):
  if n == 2:
    return True
  for i in range(2, int(math.ceil(math.sqrt(n))) + 1):
    if n % i == 0:
      return False
  return True

tests = dict(

  is_prime = ( """ Tests if a number is prime """,
    lambda v: _is_prime(v)
  ),

)

if 'USE_ANSIBLE_SUPPORT' in os.environ.keys():
  from .ansible import TestModule
  tests.update(TestModule().tests())

for k,v in tests.items():
  setattr(sys.modules[__name__], k, v[1])
