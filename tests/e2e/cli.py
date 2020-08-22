#!/usr/bin/python3

# -*- coding: utf-8 -*-

import atexit
import json
import os
from   os.path import abspath, dirname, join
import pytest
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

import inji

# The location of the inji CLI entry point
injicmd = inji.cli_location

def check_output(*args, **kwargs):
  os.environ['PYTHONUNBUFFERED'] = "1"
  return subprocess.check_output( [*args], **kwargs ).decode('utf-8')

def run_negative_test( command=[ injicmd ],
                        exit_code=2,
                        errors=None,
                        stderr=subprocess.STDOUT,
                        input=None
                      ):
  """ Run an inji command checking for the provided exit code
      and strings in stderr
  """
  class NegativeTestException(Exception): pass
  with pytest.raises(NegativeTestException) as e_info:
    try:
      check_output(*command, stderr=stderr, input=input)
    except subprocess.CalledProcessError as exc:
      msg = 'exit_code:{} output:{}'.format(exc.returncode, exc.output)
      raise NegativeTestException(msg) from exc
  e = str(e_info)
  assert f"exit_code:{exit_code} " in e
  for string in errors:
    assert re.search(f'{string}', e)
  return True

def file_from_text(*args, **kwargs):
  """ Write args to a tempfile and return the filename """

  fqdir=kwargs.get('dir', tempfile.tempdir)

  if kwargs.get('name') is None:
    _, filename = tempfile.mkstemp(text=True, dir=fqdir)
  else:
    filename = join(fqdir, kwargs.get('name'))

  atexit.register(os.remove, filename)
  with open(filename, "a+") as f:
    f.write('\n'.join(args))

  return abspath(filename)

class TestFixtureHelloWorld(unittest.TestCase):

  def test_hello_world(self):
    assert check_output('/bin/echo', 'hello', 'world') == "hello world\n"

  def test_check_output(self):
    out = check_output( 'sed', 's/foo/bar/', input=b'foo' )
    assert "bar" in out

class TestInjiCmd(unittest.TestCase):

  def test_help(self):
    """Test help message is emitted"""
    assert re.search('usage: inji', check_output(injicmd, '-h'))

  def test_stdin(self):
    """Templates should be read in from STDIN (-) by default"""
    assert check_output( injicmd,
                          input=b"{% set foo='world!' %}Hola {{ foo }}"
      ) == "Hola world!\n"

  def test_stdin_empty_input(self):
    """Empty template string should return a newline"""
    assert check_output( injicmd, input=b"" ) == '\n'

  def test_json_config_args(self):
    """Config passed as JSON string"""
    assert check_output(
        injicmd, '-j', '{"foo": "world!"}',
          input=b"Hola {{ foo }}"
      ) == "Hola world!\n"

  def test_invalid_json_config_args(self):
    """Empty json config args should cause an error"""
    input_cases = [ '', '}{', '{@}' ] # invalid JSON inputs
    for json in input_cases:
      run_negative_test(
        command=[ injicmd, '-j', json ],
        errors=[ 'Error parsing JSON config:' ]
      )

  def test_kv_config_args(self):
    """ Config passed as KV strings """
    assert check_output(
        injicmd,
          '-k', 'bar=bar',
          '-k', 'foo=bar',     # should keep bar
          '-k', 'foo=world!',  # valid, last declaration wins
          '-k', 'moo=',        # valid, sets an empty moo
          input=b"Hola {{ foo }}{{ moo }}{{ bar }}"
      ) == "Hola world!bar\n"

  def test_invalid_kv_config_args(self):
    """Invalid KV config args should cause an error"""
    input_cases = [ '', '=', '=baz' ] # invalid KV inputs
    for kv in input_cases:
      run_negative_test(
        command=[ injicmd, '-k', kv ],
        errors=[ 'Invalid key found parsing' ]
      )

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

    # needed to source the default config from ./inji.y?ml
    OLDPWD=os.getcwd()
    os.chdir(tmpdir)

    # test we are able to recursively source params
    # but also source from the default (low-precedence) config file relative to PWD
    assert re.search('Hola \w+ from bella',
      check_output(
        injicmd,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ item }} from {{ zar }}"
      )
    )

    # dev/c.yaml should be last file sourced
    assert check_output(
        injicmd, '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zoo }}"
      ) == "Hola c.yaml\n"

    # prod/ should be the last overlay sourced
    assert check_output(
        injicmd,
          '-o', f"{tmpdir}/stage",
          '-o', f"{tmpdir}/dev",
          '-o', f"{tmpdir}/prod",
          input=b"Hola {{ item }}"
      ) == "Hola prod\n"

    # named config file trumps overlays, arg position is irrelevant
    assert check_output(
        injicmd,
          '-o', f"{tmpdir}/stage",
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      ) == "Hola zella from zorg\n"

    # env vars trump named config files
    os.environ['zoo']='env'
    assert check_output(
        injicmd,
          '-o', f"{tmpdir}/stage",
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      ) == "Hola zella from env\n"

    # cli params passed in as JSON strings at the CLI trump all files
    assert check_output(
        injicmd,
          '-o', f"{tmpdir}/stage",
          '-j', '{"zoo": "world!"}',
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      ) == "Hola zella from world!\n"

    # cli params passed in as KV pairs take ultimate precendence
    # Q: why do KV pairs take precendece over JSON?
    # A: the use-case is overriding particular values from a JSON blurb sourced
    #    from a file or external system.
    assert check_output(
        injicmd,
          '-k', 'zar=della',
          '-o', f"{tmpdir}/stage",
          '-j', '{"zoo": "world!"}',
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"Hola {{ zar }} from {{ zoo }}"
      ) == "Hola della from world!\n"

    # except when params are defined in the templates themselves, off course!
    assert check_output(
        injicmd,
          '-k', 'zar=della',
          '-o', f"{tmpdir}/stage",
          '-j', '{"zoo": "mars"}',
          '-o', f"{tmpdir}/prod",
          '-v', param_file,
          '-o', f"{tmpdir}/dev",
          input=b"{% set zar='quux' %}Hola {{ zar }} from {{ zoo }}"
      ) == "Hola quux from mars\n"

    os.environ.pop('zoo')
    os.chdir(OLDPWD)

  def test_undefined_variables(self):
    """ Undefined variables should cause a failure """
    run_negative_test(
      input=b"{% set foo='world!' %}Hola {{ bar }}",
      exit_code=1,
      errors=[
        'UndefinedError',
        'variable \W{4}bar\W{4} is undefined in template'
      ]
    )

  def test_keep_undefined_var(self):
    """Undefined variable placeholders in keep mode should be kept"""
    assert check_output( injicmd, '-s', 'keep',
                          input=b"[Hola {{ foo }}]"
      ) == '[Hola {{ foo }}]\n'

  def test_empty_undefined_var(self):
    """Undefined variables in empty mode should leave spaces behind placeholders"""
    assert check_output( injicmd, '-s', 'empty',
                          input=b"[Hola {{ foo }}]"
      ) == '[Hola ]\n'

  def test_template_render_with_envvars(self):
    """Environment variables should be referenceable as parameters"""
    template = file_from_text("Hola {{ foo }}")
    os.environ['foo'] = 'world!'
    assert check_output( injicmd, template ) == 'Hola world!\n'
    os.environ.pop('foo')

  def test_template_render_with_internal_vars(self):
    """
    Jinja template should render correctly
    referencing those variables set in the templates themselves
    """
    template = file_from_text("{% set foo='world!' %}Hola {{ foo }}")
    assert check_output( injicmd, template ) == 'Hola world!\n'

  def test_template_missing(self):
    """ Missing template files should cause an error """
    run_negative_test(
      command=[ injicmd, 'nonexistent-template.j2' ],
      errors=[
        'nonexistent-template.j2.. does not exist'
      ]
    )

  def test_template_directory(self):
    """ Using a directory as a template source should cause an error"""
    run_negative_test(
      command=[ injicmd, '/' ],
      errors=[
        'error: argument',
        'path ../.. is not a file',
      ]
    )

  def test_template_render_with_varsfile(self):
    """Params from params files should be rendered on the template output"""
    template = file_from_text("Hola {{ foo }}")
    varsfile = file_from_text("foo: world!")
    assert check_output(
            injicmd, template, '-v', varsfile
        ) == 'Hola world!\n'

  def test_multiple_templates(self):
    """ Multiple template should all be rendered to STDOUT """
    # Documentation note:
    # Positional arguments must be adjacent to one another.
    # i.e. -k foo=bar t1 -k bar=foo t2  # is unsupported by argsparse
    assert check_output(
            injicmd,
              file_from_text("t1: {{ k1 }}{{ quuz }}"),
              file_from_text("t2: {{ k2 }}{{ moo }}"),
              '-k', 'k1=foo',
              '-k', 'k2=bar',
              '-v', file_from_text("k2: bar\nmoo: quux\nquuz: grault")
          ) == "t1: foograult\nt2: barquux\n"

  def test_multiple_templates_alongside_stdin(self):
    """ The use of STDIN with multiple templates should only render STDIN """
    # This is an edge-case that perhaps users would not (should not) likely do
    # but it doesn't make sense to mix STDIN with multiple named template files
    # (or does it?). For now, we favour only using STDIN in this case.
    assert check_output(
            injicmd,
              file_from_text("t1"),    # named template should be ignored
              '/dev/stdin',            # STDIN should be used
              file_from_text("t2"),    # named template should be ignored
              input=b"crash override"  # This is what renders
          ) == "crash override\n"

  def test_template_render_with_multiple_varsfiles(self):
    """Params from multiple files should be merged before rendering"""
    template = file_from_text("Hola {{ foo }}, Hello {{ bar }}, t{{ t }}")
    varsfile1 = file_from_text("foo: world!\nt: quux")
    varsfile2 = file_from_text("bar: metaverse\nt: moocow")
    assert check_output(
          injicmd, template,
                '-v', varsfile1,
                '-v', varsfile2
      ) == 'Hola world!, Hello metaverse, tmoocow\n'

  def test_error_with_empty_varsfile(self):
    """ An empty vars file is an error, we ought to fail early """
    """
    There may be a case for allowing this to just be a warning and so
    we may change this behaviour in the future. For now, it definitely
    is something we should fail-early on.
    """
    assert run_negative_test(
      command=[
        injicmd, file_from_text("Hola {{ foo }}"),
              '-v', file_from_text('')
      ],
      exit_code=1,
      errors=[
        'TypeError: .* contains no data'
      ]
    )

  def test_error_with_malformed_varsfile(self):
    """ An invalid varsfile is a fail-early error """
    run_negative_test(
      command=[
        injicmd, file_from_text("Hola {{ foo }}"),
              '-v', file_from_text('@')
      ],
      exit_code=1,
      errors=[
        'cannot start any token'
      ]
    )

  def test_filters_format_dict(self):
    """ Test the use of the format_dict filter """
    os.environ['USE_ANSIBLE_SUPPORT'] = '1'
    assert check_output(
        injicmd,
          '-k', 'url=https://google.com:443/webhp?q=foo+bar',
          file_from_text("""{{
            url | urlsplit |
              format_dict('scheme={scheme} hostname={hostname} path={path}')
            }}"""),
          ) == "scheme=https hostname=google.com path=/webhp\n"
    os.environ.pop('USE_ANSIBLE_SUPPORT')

  def test_tests_is_prime(self):
    """ Test the use of the is_prime test """
    assert check_output(
        injicmd, file_from_text("""{{ 2 is is_prime }}"""),
      ) == "True\n"
    assert check_output(
        injicmd, file_from_text("""{{ 3 is is_prime }}"""),
      ) == "True\n"
    assert check_output(
        injicmd, file_from_text("""{{ 42 is is_prime }}"""),
      ) == "False\n"

  def test_globals_run(self):
    """ Test the use of the run global function """
    assert re.search( '^\.$',
      check_output(
        injicmd, file_from_text("""{{ run('ls -d') }}"""),
      )
    )

  def test_globals_strftime(self):
    """ Test the use of the strftime global function """
    assert re.search( '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
      check_output(
        injicmd, file_from_text("""{{ date | strftime("%FT%T") }}"""),
      )
    )

  def test_sigint(self):
    """ Test that ctrl-c's are caught properly """
    with subprocess.Popen([injicmd]) as proc:
      proc.send_signal(signal.SIGINT)
      proc.wait(3)
      # exit status -N to indicate killed by signal N
      assert proc.returncode == -1 * signal.SIGINT # SIGINT == 2

if __name__ == '__main__':
  TestInjiCmd().test_globals_strftime()

