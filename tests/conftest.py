"""
Shared test fixtures for unit, integration, and e2e tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from jinja2 import DictLoader, Environment

# ============================================================================
# FIXTURE: Jinja2 Environment (mocked for unit tests)
# ============================================================================


@pytest.fixture
def jinja_env():
    """
    Minimal Jinja2 environment for unit testing.
    Uses DictLoader to avoid file I/O during tests.
    """
    return Environment(loader=DictLoader({}))


@pytest.fixture
def jinja_env_with_templates():
    """
    Jinja2 environment pre-loaded with sample templates.
    """
    templates = {
        "hello.jinja2": "Hello {{ name }}!",
        "math.jinja2": "{{ x }} + {{ y }} = {{ x + y }}",
        "undefined.jinja2": "Name: {{ undefined_var }}",
        "empty.jinja2": "",
        "with_filter.jinja2": '{{ data | get("key") }}',
        "with_global.jinja2": '{{ run("echo test") }}',
    }
    return Environment(loader=DictLoader(templates))


# ============================================================================
# FIXTURE: Temporary directories and files
# ============================================================================


@pytest.fixture
def tmp_templates_dir():
    """
    Create a temporary directory with sample template files.
    Cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write sample templates
        Path(tmpdir, "sample.jinja2").write_text("Hello {{ name }}!")
        Path(tmpdir, "config.jinja2").write_text("{{ config | tojson }}")
        Path(tmpdir, "multi.jinja2").write_text("Line 1\nLine 2: {{ var }}")

        yield tmpdir


@pytest.fixture
def tmp_config_dir():
    """
    Create a temporary directory with sample config files.
    Supports YAML, JSON, and KV formats.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # YAML config
        Path(tmpdir, "config.yml").write_text("name: test\nvalue: 42\nnested:\n  key: value\n")

        # JSON config
        Path(tmpdir, "config.json").write_text('{"env": "test", "port": 8080, "debug": true}')

        # KV format (simple key=value)
        Path(tmpdir, "config.env").write_text("KEY1=value1\nKEY2=value2\nKEY3=value3\n")

        yield tmpdir


@pytest.fixture
def tmp_output_dir():
    """
    Create a temporary directory for rendered output files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# FIXTURE: Mock objects for external dependencies
# ============================================================================


@pytest.fixture
def mock_requests():
    """
    Mock requests library for testing network-dependent functions.
    (e.g., whatismyip(), ip_api(), etc.)
    """
    mock = MagicMock()
    mock.get.return_value.json.return_value = {
        "query": "192.168.1.1",
        "country": "Test Country",
        "city": "Test City",
    }
    return mock


@pytest.fixture
def mock_subprocess():
    """
    Mock subprocess calls for testing command execution.
    """
    mock = MagicMock()
    mock.check_output.return_value = b"mocked output"
    mock.CalledProcessError = OSError  # Simplified error handling
    return mock


# ============================================================================
# FIXTURE: Sample data for testing
# ============================================================================


@pytest.fixture
def sample_context():
    """
    A typical template context with various data types.
    """
    return {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
        "active": True,
        "tags": ["python", "testing", "jinja2"],
        "metadata": {
            "created": "2026-02-28",
            "version": "1.0",
            "nested": {
                "level": 3,
            },
        },
    }


@pytest.fixture
def sample_filters():
    """
    Sample custom Jinja2 filters for testing.
    """
    return {
        "double": lambda x: x * 2,
        "reverse": lambda s: s[::-1],
        "upper_keys": lambda d: {k.upper(): v for k, v in d.items()} if isinstance(d, dict) else d,
    }


@pytest.fixture
def sample_tests():
    """
    Sample custom Jinja2 tests for testing.
    """
    return {
        "even": lambda n: n % 2 == 0,
        "odd": lambda n: n % 2 != 0,
        "long": lambda s: len(s) > 5 if isinstance(s, str) else False,
    }


# ============================================================================
# FIXTURE: Pytest configuration helpers
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_env():
    """
    Clean up environment variables after each test.
    Prevents test pollution.
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def monkeypatch_env(monkeypatch):
    """
    Convenience fixture for patching environment variables.
    """

    def set_env(key, value):
        monkeypatch.setenv(key, value)

    def del_env(key):
        monkeypatch.delenv(key, raising=False)

    return type("EnvPatcher", (), {"set": set_env, "delete": del_env})()
