#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# NAME
# inji/__init__.py

from   os.path import abspath, dirname, join

def cli_location():
  return abspath(join(dirname(__file__), '../bin/inji'))

