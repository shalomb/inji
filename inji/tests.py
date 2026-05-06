#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# Hold custom jinja2 tests
# https://jinja.palletsprojects.com/en/2.11.x/api/#custom-tests
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-builtin-tests

import math
import sys


def _is_prime(n):
    if n == 2:
        return True
    for i in range(2, int(math.ceil(math.sqrt(n))) + 1):
        if n % i == 0:
            return False
    return True


tests = dict(
    is_prime=(""" Tests if a number is prime """, lambda v: _is_prime(v)),
)

try:
    if __import__("importlib.util", fromlist=["find_spec"]).find_spec("ansible"):
        from .ansible import TestModule

        tests.update(TestModule().tests())
except Exception:
    pass

for k, v in tests.items():
    setattr(sys.modules[__name__], k, v[1])
