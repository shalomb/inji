#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# NAME

# inji - Render jina2 templates to stdout

import argparse
import atexit
import fnmatch
import json
import locale
import os
from   os.path import abspath, dirname, join
from setproctitle import setproctitle
import shutil
import signal
import sys
import tempfile

from .engine import TemplateEngine
from . import utils

def cli_args():
  parser = argparse.ArgumentParser(
      description='inji - render jinja templates'
    )
  required = parser.add_argument_group('required arguments')

  required.add_argument('-t', '-f', '--template',
    action = 'store',  required=False, type=utils.file_or_stdin,
    dest='template', default='-',
    help='/path/to/template.j2 (defaults to -)'
  )

  parser.add_argument('-j', '--json-config', '-c',
    action = 'store', required=False,
    type=lambda x: utils.json_parse(x),
    dest='json_string',
    help="-c '{ \"foo\": \"bar\", \"fred\": \"wilma\" }'"
  )

  parser.add_argument('-k', '--kv-config', '-d',
    action = 'store', required=False,
    type=lambda x: utils.kv_parse(x),
    dest='kv_pair',
    help='-d foo=bar -d fred=wilma'
  )

  parser.add_argument('-o', '--overlay-dir',
    action = 'append', required=False, type=lambda p, t='dir': utils.path(p, t),
    dest='overlay_dir', default=[],
    help='/path/to/overlay/'
  )

  parser.add_argument('-v', '-p', '--vars-file', '--vars',
    action = 'append', required=False, type=lambda p, t='file': utils.path(p, t),
    dest='vars_file', default=[],
    help='/path/to/vars.yaml'
  )

  parser.add_argument('--strict-mode', '-s',
    action = 'store', required=False, type=str,
    dest='undefined_variables_mode', default='strict',
    choices=[ 'strict', 'empty', 'keep',
              'StrictUndefined', 'Undefined', 'DebugUndefined' ],
    help='Refer to http://jinja.pocoo.org/docs/2.10/api/#undefined-types'
  )

  return parser.parse_args()


def sigint_handler(signum, frame):  # pragma: no cover # despite being covered
  """ Handle SIGINT, ctrl-c gracefully """
  signal.signal(signum, signal.SIG_IGN) # ignore subsequent ctrl-c's
  sys.exit( 128 + signal.SIGINT )       # 130 by convention

def main():
  """ Our main method """

  # cleanly handle ctrl-c's
  signal.signal(signal.SIGINT, sigint_handler)

  # set process name
  setproctitle('inji')

  args = cli_args()

  # this holds all the possible vars files we are told about or imply
  vars_files = []

  # context in the local configuration files - p5
  vars_files += fnmatch.filter(os.listdir('.'), "*inji.y*ml")

  # context in the overlay directories - p4
  for d in args.overlay_dir:
    files = list(utils.recursive_iglob(d, '*.y*ml'))
    if len(files):
      loc = locale.getlocale()
      locale.setlocale(locale.LC_ALL, 'C') # Using LC_ALL=C POSIX locale
      files.sort()                         # We force the sort collation of files
      locale.setlocale(locale.LC_ALL, loc) # And then reset it back
      vars_files += files

  # context from named vars files - p3
  vars_files += args.vars_file

  # This will hold the final vars dict merged from various available sources
  context = {}
  for file in vars_files:
    context.update(utils.read_context(file))

  # context from environment variables - p2
  context.update(os.environ)

  # context at the command line (either JSON or KV type) - p1
  if args.json_string:
    context.update(args.json_string)

  if args.kv_pair:
    context.update(args.kv_pair)

  if args.template == '-':
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
    args.template = tmpfile

  engine = TemplateEngine( undefined_variables_mode_behaviour=args.undefined_variables_mode )
  for block in engine.render( template=args.template,
                              context=context,
                            ):
    print(block)
