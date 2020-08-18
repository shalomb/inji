#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import argparse
from os.path import abspath, basename, dirname, exists, expandvars, isdir, isfile, join
import json
import os
import fnmatch
import sys
import yaml

def json_parse(string):
  """ Parse a JSON string into a dictionary """
  try:
    return json.loads(string)
  except Exception as e:
    msg = 'Error parsing JSON config: {}'.format(str(e))
    print(msg, file=sys.stderr)
    raise TypeError(msg)


def kv_parse(string):
  """ Parse a string of the form foo=bar into a dictionary """
  try:
    key, val = string.split('=', 1)
    if key is None or key == '':
      raise TypeError('Empty key')
  except Exception as e:
    err = "Invalid key found parsing KV string '{}': {}".format(string, str(e))
    print(err, file=sys.stderr)
    raise
  return { key: val }


def read_context(yaml_file):
  yaml_file = yaml_file.__str__()
  with open(yaml_file, 'r') as f:
    try:
      in_vars = yaml.load(f, Loader=yaml.SafeLoader)
      if in_vars is None:
        raise TypeError("'{}' contains no data".format(yaml_file))
    except TypeError as exc:
      raise exc
  return in_vars


def recursive_iglob(rootdir='.', pattern='*'):
  for root, dirnames, filenames in os.walk(rootdir):
    for filename in fnmatch.filter(filenames, pattern):
      yield os.path.join(root, filename)


def path(fspath, type='file'):
  """
  Checks if a filesystem path exists with the correct type
  """

  fspath = abspath(expandvars(str(fspath)))
  msg = None
  prefix = "path '{0}'".format(fspath)

  if not exists(fspath):
    msg = "{0} does not exist".format(prefix)

  if type == 'file' and isdir(fspath):
    msg = "{0} is not a file".format(prefix)

  if msg is not None:
    print(msg, file=sys.stderr)
    raise argparse.ArgumentTypeError(msg)

  return fspath


def file_or_stdin(file):
  # /dev/stdin is a special case allowing bash (and other shells?) to name stdin
  # as a file. While python should have no problem reading from it, we actually
  # read template relative to the template's basedir and /dev has no templates.
  if file == '-' or file == '/dev/stdin':
    return '-'
  return path(file)
