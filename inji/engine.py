#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from jinja2 import DebugUndefined, StrictUndefined, Undefined, make_logging_undefined
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound, UndefinedError
import sys
import logging
import inspect

from . import utils
from . import filters
from . import tests
from . import globals

def get_symbols(mod):
  return { k:v for k,v
            in inspect.getmembers(mod)
            if not (k.startswith('_')) }

class TemplateEngine(object):

  def __init__( self,
                undefined_variables_mode_behaviour='strict',
                j2_env_params={},
    ):

    UndefinedHandler = StrictUndefined
    m = undefined_variables_mode_behaviour
    if   m in ['empty',  'Undefined']:
      UndefinedHandler = Undefined
    elif m in ['keep',   'DebugUndefined']:
      UndefinedHandler = DebugUndefined

    # Setup debug logging on STDERR to have the jinja2 engine emit
    # its activities
    root = logging.getLogger(__name__)
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
    root.addHandler(handler)

    UndefinedHandler = make_logging_undefined( logger=root, base=UndefinedHandler )

    j2_env_params.setdefault('undefined', UndefinedHandler)
    j2_env_params.setdefault('trim_blocks', True)
    j2_env_params.setdefault('keep_trailing_newline', False)
    j2_env_params.setdefault('extensions', [
                            'jinja2.ext.i18n',
                            'jinja2.ext.do',
                            'jinja2.ext.loopcontrols',
                          ])

    self.j2_env_params = j2_env_params

    self.filters = get_symbols(filters)
    self.tests   = get_symbols(tests)
    self.globals = get_symbols(globals)

  def render(
      self,
      template,
      context
    ):
    """ Render the template """

    # We don't assume that includes and other sourceables reside relative
    # to the current directory but instead relative to the "master" template
    # we are processing. We deviate from jinja tradition this way.
    # This is because.
    # 1. We process template from stdin in temporary directories
    # 2. We should be free to change the process CWD and not break rendering
    rootdir = utils.dirname(template)

    self.j2_env_params.setdefault('loader', FileSystemLoader(rootdir))
    j2_env = Environment(**self.j2_env_params)

    j2_env.globals.update(self.globals)
    j2_env.filters.update(self.filters)
    j2_env.tests.update(self.tests)

    try:
      template = utils.basename(template)
      yield j2_env.get_template(template).render(context)
    except UndefinedError as e:
      raise UndefinedError( "variable {} in template '{}'".format(
              str(e), template) ) from e

