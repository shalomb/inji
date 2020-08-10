#!/usr/bin/python3

# -*- coding: utf-8 -*-

import atexit
import os
from   os.path import abspath, dirname, join
import pytest
import re
import shutil
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
  """ Write args to a tempfile and return the filename """

  fqdir=kwargs.get('dir', tempfile.tempdir)

  if kwargs.get('name') is None:
    _, filename = tempfile.mkstemp( text=True, dir=fqdir)
  else:
    filename = join(fqdir, kwargs.get('name'))

  atexit.register(os.remove, filename)
  with open(filename, "a+") as f:
    f.write('\n'.join(args))

  return abspath(filename)

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
    """Test help message is emitted"""
    code, out, err = run(inji, '-h')
    assert code == 0
    assert 'usage:' in out
    assert '' == err

  def test_stdin(self):
    """Templates should be read in from STDIN (-) by default"""
    assert "Hola world!\n" == \
      check_output( inji,
                    input=b"{% set foo='world!' %}Hola {{ foo }}"
      )

  def test_stdin_empty_input(self):
    """Empty template string should return a newline"""
    assert '\n' == check_output( inji, input=b"" )

  def test_json_config_args(self):
    """Config passed as JSON string"""
    assert "Hola world!\n" == \
      check_output(
        inji, '-c', '{"foo": "world!"}',
          input=b"Hola {{ foo }}"
      )

  def test_empty_json_config_args(self):
    """Empty json config args should cause an error"""
    class EmptyJSONConfigArgs(Exception): pass
    with pytest.raises(EmptyJSONConfigArgs) as e_info:
      try:
        check_output( inji, '-c', '',
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise EmptyJSONConfigArgs(msg) from exc
    e = str(e_info)
    assert re.search('JSON config args string is empty', e)
    assert "exit_code:1 " in e

  def test_12factor_config_sourcing(self):
    """Test config sourcing precendence should adhere to 12-factor app expectations"""
    tmpdir = tempfile.mkdtemp(prefix='param-')
    atexit.register(shutil.rmtree, tmpdir)

    for item in ['dev', 'prod', 'stage']:
      cdir = os.path.join(tmpdir, item)
      os.mkdir(cdir)
      for file in 'a.yml', 'b.yaml', 'c.yaml':
        fqn = os.path.join(cdir, file)
        file_from_text(f"zoo: {file}\nitem: {item}", dir=cdir, name=fqn)

    cfg_file = file_from_text(
        f"zar: bella\nzoo: cfg",
        dir=tmpdir, name='inji.yml' )

    param_file = file_from_text(
        f"zar: zella\nzoo: zorg",
        dir=tmpdir, name='vars.yaml' )

    # needed to source lowest precedence config from ./inji.y?ml
    OLDPWD=os.getcwd()
    os.chdir(tmpdir)

    # test we are able to recursively source params
    # but also source from the p5 config file relative to PWD
    assert re.search('Hola \w+ from bella',
      check_output(
        inji,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ item }} from {{ zar }}"
      )
    )

    # dev/c.yaml should be last file sourced
    assert "Hola c.yaml\n" == \
      check_output(
        inji, '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zoo }}"
      )

    # prod/ should be the last overlay sourced
    assert "Hola prod\n" == \
      check_output(
        inji,
          '-o', f"{tmpdir}/stage",
          '-o', f"{tmpdir}/dev",
          '-o', f"{tmpdir}/prod",
          input=b"Hola {{ item }}"
      )

    # precedence 4
    # named config file trumps overlays, arg position is irrelevant
    assert "Hola zella from zorg\n" == \
      check_output(
        inji,
          '-o', f"{tmpdir}/stage",
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      )

    # precedence 3
    # env vars trump named config files
    os.environ['zoo']='env'
    assert "Hola zella from env\n" == \
      check_output(
        inji,
          '-o', f"{tmpdir}/stage",
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      )

    # precedence 2
    # cli params passed in as JSON take ultimate precendence
    assert "Hola zella from world!\n" == \
      check_output(
        inji,
          '-o', f"{tmpdir}/stage",
          '-c', '{"zoo": "world!"}',
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      )

    # precedence 1
    # except when params are defined in the templates themselves, off course!
    assert "Hola quux from mars\n" == \
      check_output(
        inji,
          '-o', f"{tmpdir}/stage",
          '-c', '{"zoo": "mars"}',
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"{% set zar='quux' %}Hola {{ zar }} from {{ zoo }}"
      )

    os.environ.pop('zoo')
    os.chdir(OLDPWD)

  def test_strict_undefined_var(self):
    """Undefined variables should cause a failure"""
    class BarUndefinedException(Exception): pass
    with pytest.raises(BarUndefinedException) as e_info:
      try:
        check_output( inji,
                      input=b"{% set foo='world!' %}Hola {{ bar }}",
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise BarUndefinedException(msg) from exc
    e = str(e_info)
    assert "exit_code:1 " in e
    assert re.search('jinja2.exceptions.UndefinedError.+bar.+is undefined', e)

  def test_keep_undefined_var(self):
    """Undefined variables in keep mode should be kept"""
    assert '[Hola {{ foo }}]\n' == \
      check_output( inji, '-s', 'keep',
                      input=b"[Hola {{ foo }}]"
      )

  def test_empty_undefined_var(self):
    """Undefined variables in empty mode should leave spaces behind placeholders"""
    assert '[Hola ]\n' == \
      check_output( inji, '-s', 'empty',
                      input=b"[Hola {{ foo }}]"
      )

  def test_template_render_with_envvars(self):
    """Environment variables should be referenceable as parameters"""
    template = file_from_text("Hola {{ foo }}")
    os.environ['foo'] = 'world!'
    assert 'Hola world!\n' == \
      check_output( inji, '-t', template )

  def test_template_file_render(self):
    """Template files should render"""
    template = file_from_text("{% set foo='world!' %}Hola {{ foo }}")
    assert 'Hola world!\n' == \
      check_output( inji, '-t', template )

  def test_template_missing(self):
    """ Missing template files should cause an error"""
    class TemplateFileMissingException(Exception): pass
    with pytest.raises(TemplateFileMissingException) as e_info:
      try:
        check_output( inji, '-t', 'nonexistent-template.j2',
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise TemplateFileMissingException(msg) from exc
    e = str(e_info)
    assert "exit_code:2 " in e
    assert re.search('nonexistent-template.j2.. does not exist', e)

  def test_template_directory(self):
    """ Using a directory as a template source should cause an error"""
    class TemplateFileMissingException(Exception): pass
    with pytest.raises(TemplateFileMissingException) as e_info:
      try:
        check_output( inji, '-t', '/',
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise TemplateFileMissingException(msg) from exc
    e = str(e_info)
    assert "exit_code:2 " in e
    assert re.search('/.. is not a file', e)

  def test_template_render_with_varsfile(self):
    """Params from params files should be rendered on the template output"""
    template = file_from_text("Hola {{ foo }}")
    varsfile = file_from_text("foo: world!")
    assert 'Hola world!\n' == \
      check_output( inji, '-t', template, '-v', varsfile )

  def test_template_render_with_multiple_varsfiles(self):
    """Params from multiple files should be merged before rendering"""
    template = file_from_text("Hola {{ foo }}, Hello {{ bar }}, t{{ t }}")
    varsfile1 = file_from_text("foo: world!\nt: quux")
    varsfile2 = file_from_text("bar: metaverse\nt: moocow")
    assert 'Hola world!, Hello metaverse, tmoocow\n' == \
      check_output(
          inji, '-t', template,
                '-v', varsfile1,
                '-v', varsfile2
      )

  def test_template_render_with_empty_varsfile(self):
    """ Empty varsfile should blow up in strict mode """
    class EmptyVarsFileException(Exception): pass
    with pytest.raises(EmptyVarsFileException) as e_info:
      try:
        template = file_from_text("Hola {{ foo }}, Hello {{ bar }}")
        varsfile = file_from_text('')
        check_output( inji, '-t', template, '-v', varsfile,
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise EmptyVarsFileException(msg) from exc
    e = str(e_info)
    assert re.search('TypeError: .* contains no data', e)
    assert "exit_code:1 " in e

  def test_template_render_with_malformed_varsfile(self):
    """ Malformed varsfile should blow up in strict mode """
    class MalformedVarsFileException(Exception): pass
    with pytest.raises(MalformedVarsFileException) as e_info:
      try:
        template = file_from_text("Hola {{ foo }}, Hello {{ bar }}")
        varsfile = file_from_text('@')
        check_output( inji, '-t', template, '-v', varsfile, '-s', 'strict',
                      stderr=subprocess.STDOUT,
        )
      except subprocess.CalledProcessError as exc:
        msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
        raise MalformedVarsFileException(msg) from exc
    e = str(e_info)
    assert re.search('cannot start any token', e)
    assert "exit_code:1 " in e

if __name__ == '__main__':
  TestInjiCmd().test_empty_json_config_args()

