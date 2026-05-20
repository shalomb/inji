"""
Unit tests for inji.cli module.

Tests CLI argument parsing and main() entry-point logic:
- Argument parsing (templates, vars files, overlay dirs, JSON/KV config, strict mode)
- Context assembly (precedence: vars files < env vars < json < kv)
- Stdin handling (dash / tempfile flow)
- Version helpers
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from inji import cli


class TestPkgLocation:
    def test_returns_absolute_path(self):
        result = cli.pkg_location()
        assert os.path.isabs(result)

    def test_points_to_inji_package(self):
        result = cli.pkg_location()
        assert result.endswith("inji")


class TestVersion:
    def test_returns_string(self):
        assert isinstance(cli._version(), str)

    def test_not_empty(self):
        assert cli._version() != ""


class TestCliArgs:
    """Test argument parsing via cli_args()."""

    def _parse(self, argv):
        with patch("sys.argv", ["inji"] + argv):
            return cli.cli_args()

    def test_default_template_is_stdin(self):
        args = self._parse([])
        assert args.template == "-"

    def test_template_file(self):
        with tempfile.NamedTemporaryFile(suffix=".j2", delete=False) as f:
            f.write(b"{{ name }}")
            f.flush()
            try:
                args = self._parse([f.name])
                assert f.name in args.template
            finally:
                os.unlink(f.name)

    def test_json_config(self):
        args = self._parse(["-c", '{"key": "value"}'])
        assert args.json_string == {"key": "value"}

    def test_kv_config_single(self):
        args = self._parse(["-d", "foo=bar"])
        assert args.kv_pair == [{"foo": "bar"}]

    def test_kv_config_multiple(self):
        args = self._parse(["-d", "foo=bar", "-d", "baz=qux"])
        assert args.kv_pair == [{"foo": "bar"}, {"baz": "qux"}]

    def test_vars_file(self):
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            f.write(b"key: val\n")
            f.flush()
            try:
                args = self._parse(["-v", f.name])
                assert f.name in args.vars_file
            finally:
                os.unlink(f.name)

    def test_overlay_dir(self):
        with tempfile.TemporaryDirectory() as d:
            args = self._parse(["-o", d])
            assert d in args.overlay_dir

    def test_strict_mode_default(self):
        args = self._parse([])
        assert args.undefined_variables_mode == "strict"

    def test_strict_mode_empty(self):
        args = self._parse(["--strict-mode", "empty"])
        assert args.undefined_variables_mode == "empty"

    def test_strict_mode_keep(self):
        args = self._parse(["--strict-mode", "keep"])
        assert args.undefined_variables_mode == "keep"

    def test_invalid_strict_mode(self):
        with pytest.raises(SystemExit):
            self._parse(["--strict-mode", "invalid"])

    def test_version_flag_exits(self):
        with pytest.raises(SystemExit):
            self._parse(["--version"])


class TestMain:
    """Test main() context assembly and rendering."""

    def _run(self, argv, stdin=None, env=None):
        """Run main() with controlled argv, stdin, and env."""
        extra_env = env or {}
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to tmpdir so local inji.yml discovery is isolated
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch("sys.argv", ["inji"] + argv):
                    with patch.dict(os.environ, extra_env, clear=False):
                        if stdin is not None:
                            with patch("sys.stdin") as mock_stdin:
                                mock_stdin.read.return_value = stdin
                                output = []
                                with patch("builtins.print", side_effect=output.append):
                                    cli.main()
                        else:
                            output = []
                            with patch("builtins.print", side_effect=output.append):
                                cli.main()
                        return output
            finally:
                os.chdir(old_cwd)

    def test_render_template_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("hello {{ name }}")
            f.flush()
            try:
                out = self._run(["-c", '{"name": "world"}', f.name])
                assert out == ["hello world"]
            finally:
                os.unlink(f.name)

    def test_render_stdin(self):
        out = self._run(["-c", '{"name": "stdin"}'], stdin="{{ name }}")
        assert out == ["stdin"]

    def test_json_context_overrides_env(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("{{ MYVAR }}")
            f.flush()
            try:
                # env sets MYVAR=from_env, json overrides to from_json
                out = self._run(
                    ["-c", '{"MYVAR": "from_json"}', f.name],
                    env={"MYVAR": "from_env"},
                )
                assert out == ["from_json"]
            finally:
                os.unlink(f.name)

    def test_kv_context_overrides_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("{{ key }}")
            f.flush()
            try:
                out = self._run(["-c", '{"key": "from_json"}', "-d", "key=from_kv", f.name])
                assert out == ["from_kv"]
            finally:
                os.unlink(f.name)

    def test_env_var_available_in_template(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("{{ INJI_TEST_VAR }}")
            f.flush()
            try:
                out = self._run([f.name], env={"INJI_TEST_VAR": "from_env"})
                assert out == ["from_env"]
            finally:
                os.unlink(f.name)

    def test_vars_file_loaded(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as vf:
            vf.write("greeting: hello\n")
            vf.flush()
            with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as tf:
                tf.write("{{ greeting }}")
                tf.flush()
                try:
                    out = self._run(["-v", vf.name, tf.name])
                    assert out == ["hello"]
                finally:
                    os.unlink(vf.name)
                    os.unlink(tf.name)

    def test_overlay_dir_vars_loaded(self):
        with tempfile.TemporaryDirectory() as overlay:
            Path(overlay, "vars.yml").write_text("colour: blue\n")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as tf:
                tf.write("{{ colour }}")
                tf.flush()
                try:
                    out = self._run(["-o", overlay, tf.name])
                    assert out == ["blue"]
                finally:
                    os.unlink(tf.name)

    def test_multiple_templates_rendered_in_order(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as t1:
            t1.write("first")
            t1.flush()
            with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as t2:
                t2.write("second")
                t2.flush()
                try:
                    out = self._run([t1.name, t2.name])
                    assert out == ["first", "second"]
                finally:
                    os.unlink(t1.name)
                    os.unlink(t2.name)

    def test_strict_mode_raises_on_undefined(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("{{ undefined_var }}")
            f.flush()
            try:
                with pytest.raises(Exception):
                    self._run([f.name])
            finally:
                os.unlink(f.name)

    def test_empty_mode_silences_undefined(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("{{ undefined_var }}")
            f.flush()
            try:
                out = self._run(["--strict-mode", "empty", f.name])
                assert out == [""]
            finally:
                os.unlink(f.name)
