#!/usr/bin/python3

# -*- coding: utf-8 -*-

import atexit
import os
from   os.path import abspath, dirname, join
import pytest
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, join(dirname(abspath(__file__)), '../..'))
sys.path.insert(0, join(dirname(abspath(__file__)), '../../inji'))

import inji
inji = abspath(join(sys.path[0], 'inji'))

def run(cmd, *args, **kwargs):
  os.environ['PYTHONUNBUFFERED'] = "1"
  proc = subprocess.Popen( [cmd, *args],
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
  )
  stdout, stderr = proc.communicate(**kwargs)
  return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

def check_output(*args, **kwargs):
  return subprocess.check_output( [*args], **kwargs ).decode('utf-8')

def file_from_text(*args, **kwargs):
  _, tmpfile = tempfile.mkstemp(text=True)
  atexit.register(os.remove, tmpfile)
  with open(tmpfile, "a+") as f:
    f.write('\n'.join(args))
  return tmpfile

def dump(obj):

    def pretty(obj):
        j = json.dumps( obj, sort_keys=True, indent=2,
                    separators=(', ', ': ') )
        try:
            from pygments import highlight, lexers, formatters
            return highlight( j,
                    lexers.JsonLexer(), formatters.TerminalFormatter() )
        except ImportError as e:
            return j

    try:
        return pretty(obj)
    except TypeError as e:
        return pretty(obj.__dict__)

class TestFixtureHelloWorld(unittest.TestCase):

  def test_hello_world(self):
    code, out, err = run('/bin/echo', 'hello', 'world')
    assert 'hello' in out
    assert 'world' in out
    assert '' in err
    assert code == 0

  def test_check_output(self):
    out = check_output( 'sed', 's/foo/bar/', input=b'foo' )
    assert "bar" in out

class TestInjiCmd(unittest.TestCase):

  def test_help(self):
    code, out, err = run(inji, '-h')
    assert 'usage:' in out
    assert code == 0

  def test_py2_stdin(self):
    assert 'Hola world!' in \
      check_output( 'python3', inji, '-t', '-',
                    input=b"{% set foo='world!' %}Hola {{ foo }}"
      )

  def test_stdin(self):
    assert 'Hola world!' in \
      check_output( inji, '-t', '-',
                    input=b"{% set foo='world!' %}Hola {{ foo }}"
      )

  def test_stdin_empty_input(self):
    """Empty string returns newline"""
    assert '\n' == check_output( inji, '-t', '-', input=b"" )

  def test_strict_undefined_var(self):
    """Undefined vars blow up"""
    class BollocksException(Exception): pass
    with pytest.raises(BollocksException) as e_info:
      try:
        check_output( inji, '-t', '-',
                      input=b"{% set foo='world!' %}Hola {{ bar }}",
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise BollocksException(msg) from exc
    e = str(e_info)
    assert "exit_code:1 " in e
    assert re.search('jinja2.exceptions.UndefinedError.+bar.+is undefined', e)

  def test_keep_undefined_var(self):
    """Preserve undefined vars in output"""
    assert '[Hola {{ foo }}]\n' == \
      check_output( inji, '-t', '-', '-s', 'keep',
                          input=b"[Hola {{ foo }}]"
      )

  def test_empty_undefined_var(self):
    """Empty undefined vars in output"""
    assert '[Hola ]\n' == \
      check_output( inji, '-t', '-', '-s', 'empty',
                          input=b"[Hola {{ foo }}]"
      )

  def test_template_render(self):
    template = file_from_text("{% set foo='world!' %}Hola {{ foo }}")
    assert 'Hola world!\n' == \
      check_output( inji, '-t', template )

if __name__ == '__main__':
  TestInjiCmd().test_undefined_var3()

