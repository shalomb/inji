"""
Integration test fixtures (inherited from tests/conftest.py + integration-specific additions).
"""

import pytest
import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def file_based_jinja_env(tmp_templates_dir):
    """
    Jinja2 environment using FileSystemLoader (for integration tests with real files).
    """
    return Environment(loader=FileSystemLoader(tmp_templates_dir))


@pytest.fixture
def full_config_set(tmp_config_dir):
    """
    Complete configuration setup (YAML, JSON, ENV) for testing config precedence.
    """
    return {
        'yaml_file': Path(tmp_config_dir) / 'config.yml',
        'json_file': Path(tmp_config_dir) / 'config.json',
        'env_file': Path(tmp_config_dir) / 'config.env',
        'dir': tmp_config_dir,
    }


@pytest.fixture
def complex_template_context():
    """
    Complex context with nested data, lists, and special values.
    """
    return {
        'app': {
            'name': 'inji',
            'version': '0.6.0',
            'features': {
                'jinja2': True,
                'filters': True,
                'globals': True,
                'markdown': True,
            }
        },
        'users': [
            {'name': 'Alice', 'role': 'admin'},
            {'name': 'Bob', 'role': 'user'},
            {'name': 'Charlie', 'role': 'user'},
        ],
        'settings': {
            'debug': False,
            'log_level': 'info',
            'timeout': 30,
        }
    }
