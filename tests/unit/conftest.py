"""
Unit test fixtures (inherited from tests/conftest.py + unit-specific additions).
"""

from unittest.mock import MagicMock

import pytest
from jinja2 import Environment, StrictUndefined


@pytest.fixture
def strict_jinja_env():
    """
    Jinja2 environment that raises on undefined variables.
    Useful for testing error handling.
    """
    return Environment(undefined=StrictUndefined)


@pytest.fixture
def mock_file_io():
    """
    Mock file I/O operations.
    """
    mock = MagicMock()
    mock.open = MagicMock()
    mock.read = MagicMock(return_value="file content")
    return mock


@pytest.fixture
def mock_api_calls():
    """
    Mock API call responses (for globals like ip_api, whatismyip).
    """
    responses = {
        "ip_api": {
            "query": "203.0.113.42",
            "country": "Test Country",
            "city": "Test City",
            "isp": "Test ISP",
            "status": "success",
        },
        "ip_check": "203.0.113.42",
    }
    mock = MagicMock()
    mock.get.return_value.json.return_value = responses["ip_api"]
    mock.get.return_value.text = responses["ip_check"]
    return mock


@pytest.fixture
def mock_subprocess():
    """
    Mock subprocess command execution (for globals like run(), gitdescribe()).
    """
    mock = MagicMock()
    mock.check_output.return_value = b"command output"
    mock.run.return_value.stdout = b"command output"
    mock.run.return_value.returncode = 0
    return mock
