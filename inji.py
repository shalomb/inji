#!/usr/bin/env python

# -*- coding: utf-8 -*-

# NAME

# inji - Render jina2 templates to stdout

from __future__ import print_function, with_statement

import argparse
import atexit
import errno
from glob import glob
from jinja2.exceptions import TemplateNotFound, UndefinedError
from jinja2 import DebugUndefined, StrictUndefined, Undefined, make_logging_undefined
from jinja2 import Environment, FileSystemLoader
import logging
import os
from os.path import abspath, basename, dirname, exists, expandvars, isdir, isfile, join
import re
import shutil
import sys
import tempfile
import yaml

try:
  FileNotFoundError
except NameError:
  FileNotFoundError = IOError

VarsFileNotFoundError = FileNotFoundError

def merge_dict(x, y):
  z = x.copy()
  z.update(y)
  return z

def render_template(jinja2_template, vars_files, strict_mode_behaviour):

  if not isfile(jinja2_template):
    raise TemplateNotFound(
        '"{}", {}'.format(jinja2_template, os.strerror(errno.ENOENT)) )

  vars = {}
  for file in vars_files:
    file = file.__str__()
    with open(file, 'r') as f:
      try:
        dict = yaml.load(f, Loader=yaml.SafeLoader)
        if dict is None:
          raise TypeError("'{}' contains no data".format(file))
      except yaml.YAMLError as exc:
        if strict_mode_behaviour == 'strict':
          raise
        print(exc, file=sys.stderr)
      except TypeError as exc:
        if strict_mode_behaviour == 'strict':
          raise
        print(exc, file=sys.stderr)
    vars = merge_dict(vars, dict)

  m = strict_mode_behaviour
  if   m in ['strict', 'StrictUndefined']:
    Handler = StrictUndefined
  elif m in ['empty',  'Undefined']:
    Handler = Undefined
  elif m in ['keep',   'DebugUndefined']:
    Handler = DebugUndefined
  else:
    raise Exception((
      'Unsupported type "{}" specified to handle undefined variables.\n' +
      'See http://jinja.pocoo.org/docs/2.10/api/#undefined-types.'
    ).format(m))

  root = logging.getLogger(jinja2_template)
  root.setLevel(logging.DEBUG)
  handler = logging.StreamHandler(sys.stderr)
  logformat = '%(name)s %(levelname)s: %(message)s'
  formatter = logging.Formatter(logformat)
  handler.setFormatter(formatter)
  root.addHandler(handler)

  UndefinedHandler = make_logging_undefined( logger=root, base=Handler )

  # This is contra the design philosophy of jinja where templates are part of
  # bigger projects and includes are possible relative to the target template.
  # But we are a tool that renders (simple) templates and while we do not
  # preclude complex use cases, we assume the target is the "master" template
  # and any includes, etc it uses are relative to where it resides (not the
  # current directory of the process).
  dir = dirname(jinja2_template)

  j2_env = Environment( loader=FileSystemLoader(dir),
                        undefined=UndefinedHandler,
                        trim_blocks=True )

  try:
    jinja2_template = basename(jinja2_template)
    yield j2_env.get_template(jinja2_template).render(vars)
  except UndefinedError as e:
    raise UndefinedError( "variable {} in template '{}'".format(
            str(e), jinja2_template) ) from e

def listdir_recurisve(directory):
  directory = os.path.expanduser(os.path.expandvars(directory))
  return [ os.path.join(parent, file)
            for parent, dirs, files in os.walk(directory)
            for file in files ]

def path(fspath, type='file'):
  """
  Checks if a filesystem path exists with the correct type
  """

  fspath = abspath(expandvars(str(fspath)))
  msg = None
  prefix = "path '{0}'".format(fspath)

  if not exists(fspath):
    msg = "{0} does not exist".format(prefix)

  if type == 'file' and not isfile(fspath):
    msg = "{0} is not a file".format(prefix)

  if type == 'dir' and not isdir(fspath):
    msg = "{0} is not a directory".format(prefix)

  if msg is not None:
    raise argparse.ArgumentTypeError(msg)

  return fspath

def file_or_stdin(file):
  # /dev/stdin is a special case allowing bash (and other shells?) to name stdin
  # as a file. While python should have no problem reading from it, we actually
  # read template relative to the template's basedir and /dev has no templates.
  if file == '-' or file == '/dev/stdin':
    return '-'
  return path(file)

def cli_args():
  parser = argparse.ArgumentParser(description='inji - jinja template renderer')
  required = parser.add_argument_group('required arguments')

  required.add_argument('-t', '-f', '--template',
    action = 'store',  required=False, type=file_or_stdin,
    dest='jinja2_template', default='-',
    help='/path/to/template.j2 (defaults to -)'
  )

  parser.add_argument('-o', '--overlay',
    action = 'append', required=False, type=lambda p, t='dir': path(p, t),
    dest='overlays', default=[],
    help='/path/to/overlay/'
  )

  parser.add_argument('-i', '--inji-file', '--inji',
    action = 'store', required=False, type=lambda p, t='file': path(p, t),
    dest='inji_file',
    help='/path/to/inji.yaml (defaults to ./inji.yml)'
  )

  parser.add_argument('-v', '--vars-file', '--vars',
    action = 'append', required=False, type=lambda p, t='file': path(p, t),
    dest='vars_files', default=[],
    help='/path/to/vars.yaml (defaults to ./inji.yaml)'
  )

  parser.add_argument('--strict-mode', '-s',
    action = 'store', required=False, type=str,
    dest='strict_mode', default='strict',
    choices=[ 'strict', 'empty', 'keep',
              'StrictUndefined', 'Undefined', 'DebugUndefined' ],
    help='Refer to http://jinja.pocoo.org/docs/2.10/api/#undefined-types'
  )

  return parser.parse_args()


if __name__ == '__main__':
  args = cli_args()

  args.overlays = [ file for d in args.overlays
                      for file in listdir_recurisve(d)
                      if re.search('\.ya?ml$', file) ]

  if args.inji_file is None:
    args.inji_file = [ file for file in ['./inji.yml', './inji.yaml']
                        if exists(file) ]

  if args.jinja2_template == '-':
    # Template passed in via stdin. Create template as a tempfile and use it
    # instead but since includes are possible (though not likely), we have to do
    # this in an isolated tmpdir container to prevent inadvertent reading of
    # includes not meant to be read.
    tmpdir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, tmpdir)

    _, tmpfile = tempfile.mkstemp(prefix='stdin-', dir=tmpdir, text=True)
    atexit.register(os.remove, tmpfile)

    with open(tmpfile, "a+") as f:
      f.write(sys.stdin.read())
    args.jinja2_template = tmpfile

  for block in render_template( args.jinja2_template,
                                args.vars_files,
                                args.strict_mode ):
    print(block)

