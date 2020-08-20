#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import importlib
import inspect
import sys

# mixin for ansible.plugins.filters.*

class FilterModule(object):

  def __init__(self):
    self._filters = {}

  def filters(self):

    for spec in [
        'ansible.plugins.filter.core',
        'ansible.plugins.filter.mathstuff',
        'ansible.plugins.filter.urls',
        'ansible.plugins.filter.urlsplit',
      ]:

      mod = importlib.import_module(spec)

      if hasattr(mod, 'FilterModule'):
        _filters = mod.FilterModule().filters()
        for k,v in _filters.items():
          self._filters.update( {
            k: [ "{}.{}".format(spec, k), v ]
          } )

      del mod
    return self._filters

class TestModule(object):

  def __init__(self):
    self._tests = {}

  def tests(self):

    for spec in [
        'ansible.plugins.test.core',
        'ansible.plugins.test.files',
        'ansible.plugins.test.mathstuff',
      ]:

      mod = importlib.import_module(spec)

      if hasattr(mod, 'TestModule'):
        _tests = mod.TestModule().tests()
        for k,v in _tests.items():
          self._tests.update( {
            k: [ "{}.{}".format(spec, k), v ]
          } )

      del mod
    return self._tests
