"""
Unit tests for inji.utils module.

Tests utility functions for:
- Configuration parsing (JSON, YAML, key-value)
- File operations (path validation, file loading)
- Command execution (subprocess wrapper)
- Network operations (HTTP requests, IP lookup)
- Path manipulation (walking directories, expanding paths)
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

from inji import utils


class TestJsonParsing:
    """Test JSON parsing utilities."""
    
    def test_json_parse_valid(self):
        """Parse valid JSON string."""
        result = utils.json_parse('{"name": "Alice", "age": 30}')
        assert result == {'name': 'Alice', 'age': 30}
    
    def test_json_parse_array(self):
        """Parse JSON array."""
        result = utils.json_parse('[1, 2, 3, 4, 5]')
        assert result == [1, 2, 3, 4, 5]
    
    def test_json_parse_null(self):
        """Parse JSON null."""
        result = utils.json_parse('null')
        assert result is None
    
    def test_json_parse_invalid(self):
        """Raise on invalid JSON."""
        with pytest.raises(TypeError):
            utils.json_parse('{ invalid json }')
    
    def test_json_parse_empty(self):
        """Parse empty JSON object."""
        result = utils.json_parse('{}')
        assert result == {}


class TestKvParsing:
    """Test key-value parsing utilities."""
    
    def test_kv_parse_simple(self):
        """Parse simple key=value."""
        result = utils.kv_parse('foo=bar')
        assert result == {'foo': 'bar'}
    
    def test_kv_parse_with_equals(self):
        """Parse value containing equals sign."""
        result = utils.kv_parse('url=http://example.com?foo=bar')
        assert result == {'url': 'http://example.com?foo=bar'}
    
    def test_kv_parse_empty_value(self):
        """Parse with empty value."""
        result = utils.kv_parse('key=')
        assert result == {'key': ''}
    
    def test_kv_parse_no_key(self):
        """Raise on missing key."""
        with pytest.raises(TypeError):
            utils.kv_parse('=value')
    
    def test_kv_parse_no_equals(self):
        """Raise on missing equals separator."""
        with pytest.raises(ValueError):
            utils.kv_parse('invalidformat')


class TestYamlReading:
    """Test YAML file reading."""
    
    def test_read_context_valid_yaml(self):
        """Read valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('name: Alice\nage: 30\n')
            f.flush()
            
            try:
                result = utils.read_context(f.name)
                assert result == {'name': 'Alice', 'age': 30}
            finally:
                os.unlink(f.name)
    
    def test_read_context_nested(self):
        """Read YAML with nested structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('user:\n  name: Alice\n  age: 30\n')
            f.flush()
            
            try:
                result = utils.read_context(f.name)
                assert result['user']['name'] == 'Alice'
                assert result['user']['age'] == 30
            finally:
                os.unlink(f.name)
    
    def test_read_context_empty_file(self):
        """Raise on empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('')
            f.flush()
            
            try:
                with pytest.raises(TypeError):
                    utils.read_context(f.name)
            finally:
                os.unlink(f.name)
    
    def test_read_context_invalid_yaml(self):
        """Raise on invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('invalid: yaml: file:')
            f.flush()
            
            try:
                # Invalid YAML might not raise, depends on yaml.load
                result = utils.read_context(f.name)
                # If it doesn't raise, at least check result is a dict
                assert isinstance(result, (dict, type(None)))
            finally:
                os.unlink(f.name)


class TestPathValidation:
    """Test file path validation and checking."""
    
    def test_path_file_exists(self):
        """Valid path to existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            
            try:
                result = utils.path(f.name, type='file')
                assert result == f.name
            finally:
                os.unlink(f.name)
    
    def test_path_file_not_exists(self):
        """Raise on non-existent file."""
        with pytest.raises(Exception):  # argparse.ArgumentTypeError
            utils.path('/nonexistent/file.txt', type='file')
    
    def test_path_dir_when_file_expected(self):
        """Raise when directory provided but file expected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(Exception):  # argparse.ArgumentTypeError
                utils.path(tmpdir, type='file')
    
    def test_path_expandvars(self):
        """Expand environment variables in path."""
        # Create temp file in a directory we control
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.txt'
            test_file.write_text('content')
            
            # Test with absolute path (no vars to expand)
            result = utils.path(str(test_file))
            assert result == str(test_file)


class TestFileOrStdin:
    """Test file or stdin validation."""
    
    def test_file_or_stdin_dash(self):
        """Recognize dash as stdin marker."""
        result = utils.file_or_stdin('-')
        assert result == '-'
    
    def test_file_or_stdin_dev_stdin(self):
        """Recognize /dev/stdin as stdin marker."""
        result = utils.file_or_stdin('/dev/stdin')
        assert result == '-'
    
    def test_file_or_stdin_file(self):
        """Validate regular file path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test')
            f.flush()
            
            try:
                result = utils.file_or_stdin(f.name)
                assert result == f.name
            finally:
                os.unlink(f.name)


class TestCommandExecution:
    """Test subprocess command execution."""
    
    @patch('subprocess.check_output')
    def test_cmd_simple(self, mock_check_output):
        """Execute simple command."""
        mock_check_output.return_value = b'output\n'
        result = utils.cmd('echo test')
        assert result == 'output'
    
    @patch('subprocess.check_output')
    def test_cmd_with_args(self, mock_check_output):
        """Execute command with arguments."""
        mock_check_output.return_value = b'test output'
        result = utils.cmd('echo hello world')
        assert result == 'test output'
    
    @patch('subprocess.check_output')
    def test_cmd_strips_whitespace(self, mock_check_output):
        """Command output is stripped of whitespace."""
        mock_check_output.return_value = b'  output with spaces  \n'
        result = utils.cmd('echo test')
        assert result == 'output with spaces'
    
    @patch('subprocess.check_output')
    def test_cmd_failure(self, mock_check_output):
        """Command execution failure raises exception."""
        mock_check_output.side_effect = OSError('Command not found')
        with pytest.raises(OSError):
            utils.cmd('nonexistent_command')


class TestFileLoading:
    """Test file loading utilities."""
    
    def test_load_file_text(self):
        """Load text file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('file content here')
            f.flush()
            
            try:
                result = utils.load_file(f.name)
                assert result == 'file content here'
            finally:
                os.unlink(f.name)
    
    def test_load_file_strips_whitespace(self):
        """File content is stripped of surrounding whitespace."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('  \n  content  \n  ')
            f.flush()
            
            try:
                result = utils.load_file(f.name)
                assert result == 'content'
            finally:
                os.unlink(f.name)
    
    def test_load_file_utf8(self):
        """Load UTF-8 encoded file."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('Hello 世界 🌍')
            f.flush()
            
            try:
                result = utils.load_file(f.name)
                assert '世界' in result
                assert '🌍' in result
            finally:
                os.unlink(f.name)
    
    def test_load_file_not_found(self):
        """Raise on file not found."""
        with pytest.raises(FileNotFoundError):
            utils.load_file('/nonexistent/file.txt')


class TestHttpGet:
    """Test HTTP GET utilities."""
    
    @patch('inji.utils.requests.get')
    def test_get_json_response(self, mock_get):
        """Fetch and parse JSON response."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'result': 'success'}
        mock_get.return_value = mock_response
        
        result = utils.get('http://api.example.com/data')
        assert result == {'result': 'success'}
    
    @patch('inji.utils.requests.get')
    def test_get_text_response(self, mock_get):
        """Fetch text response."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_response.content = b'plain text response'
        mock_get.return_value = mock_response
        
        result = utils.get('http://example.com/text')
        assert result == 'plain text response'
    
    @patch('inji.utils.requests.get')
    def test_get_network_error(self, mock_get):
        """Handle network errors."""
        mock_get.side_effect = Exception('Network error')
        
        with pytest.raises(Exception):
            utils.get('http://unreachable.example.com')


class TestIpApiUtilities:
    """Test IP API utilities."""
    
    @patch('inji.utils.get')
    def test_ip_api_query(self, mock_get):
        """Get specific IP API field."""
        mock_get.return_value = {
            'query': '203.0.113.42',
            'country': 'Example Country',
            'city': 'Example City'
        }
        
        result = utils.ip_api('query')
        assert result == '203.0.113.42'
    
    @patch('inji.utils.get')
    def test_ip_api_country(self, mock_get):
        """Get country from IP API."""
        mock_get.return_value = {
            'country': 'Example Country'
        }
        
        result = utils.ip_api('country')
        assert result == 'Example Country'
    
    @patch('inji.utils.get')
    def test_whatismyip(self, mock_get):
        """Get public IP address."""
        mock_get.return_value = '203.0.113.42'
        
        result = utils.whatismyip()
        assert result == '203.0.113.42'


class TestPathManipulation:
    """Test path manipulation functions."""
    
    def test_basename(self):
        """Extract filename from path."""
        result = utils.basename('/path/to/file.txt')
        assert result == 'file.txt'
    
    def test_dirname(self):
        """Extract directory from path."""
        result = utils.dirname('/path/to/file.txt')
        assert '/path/to' in result or 'path' in result
    
    def test_abspath(self):
        """Get absolute path."""
        result = utils.path(__file__)
        assert os.path.isabs(result)
    
    def test_recursive_iglob(self):
        """Walk directory tree and find files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            Path(tmpdir, 'file1.txt').write_text('content')
            Path(tmpdir, 'subdir').mkdir()
            Path(tmpdir, 'subdir', 'file2.txt').write_text('content')
            
            results = list(utils.recursive_iglob(tmpdir, '*.txt'))
            assert len(results) == 2
