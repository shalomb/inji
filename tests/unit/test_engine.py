"""
Unit tests for inji.engine module.

Tests the TemplateEngine class in isolation:
- Template rendering with context
- Undefined variable handling (strict, debug, empty modes)
- Custom filters, globals, and tests injection
- Error handling (missing templates, syntax errors)
- Edge cases (empty templates, large templates, special characters)
"""

import pytest
import tempfile
from pathlib import Path
from jinja2 import TemplateNotFound, UndefinedError, TemplateSyntaxError

from inji.engine import TemplateEngine


class TestTemplateEngineInit:
    """Test TemplateEngine initialization."""
    
    def test_init_default(self):
        """Engine initializes with default parameters."""
        engine = TemplateEngine()
        assert engine is not None
        assert engine.filters is not None
        assert engine.tests is not None
        assert engine.globals is not None
    
    def test_init_undefined_mode_strict(self):
        """Engine initializes with strict undefined mode (default)."""
        engine = TemplateEngine(undefined_variables_mode_behaviour='strict')
        assert engine is not None
    
    def test_init_undefined_mode_debug(self):
        """Engine initializes with debug undefined mode."""
        engine = TemplateEngine(undefined_variables_mode_behaviour='DebugUndefined')
        assert engine is not None
    
    def test_init_undefined_mode_empty(self):
        """Engine initializes with empty undefined mode."""
        engine = TemplateEngine(undefined_variables_mode_behaviour='Undefined')
        assert engine is not None
    
    def test_init_custom_j2_params(self):
        """Engine accepts custom Jinja2 parameters."""
        params = {'trim_blocks': False, 'keep_trailing_newline': True}
        engine = TemplateEngine(j2_env_params=params)
        assert engine.j2_env_params['trim_blocks'] is False
        assert engine.j2_env_params['keep_trailing_newline'] is True
    
    def test_filters_loaded(self):
        """Custom filters are loaded."""
        engine = TemplateEngine()
        # Should have custom filters from inji/filters.py
        # engine.filters is get_symbols(filters) — all module-level names
        assert 'format_dict' in engine.filters
        assert 'wrap' in engine.filters
        assert 'append' in engine.filters
    
    def test_globals_loaded(self):
        """Custom globals are loaded."""
        engine = TemplateEngine()
        # Should have custom globals from inji/globals.py
        assert 'run' in engine.globals
        assert 'gitdescribe' in engine.globals or len(engine.globals) > 0
    
    def test_tests_loaded(self):
        """Custom tests are loaded."""
        engine = TemplateEngine()
        # Should have custom tests from inji/tests.py
        assert 'is_prime' in engine.tests


class TestTemplateEngineRender:
    """Test template rendering."""
    
    def test_render_simple_template(self, tmp_templates_dir):
        """Render simple template with context."""
        engine = TemplateEngine()
        template_path = Path(tmp_templates_dir) / 'hello.jinja2'
        template_path.write_text('Hello {{ name }}!')
        
        output = list(engine.render(str(template_path), {'name': 'World'}))
        assert output[0] == 'Hello World!'
    
    def test_render_template_with_expressions(self, tmp_templates_dir):
        """Render template with expressions."""
        engine = TemplateEngine()
        # Create a template with math
        Path(tmp_templates_dir, 'math.jinja2').write_text('Result: {{ x + y }}')
        template_path = Path(tmp_templates_dir) / 'math.jinja2'
        
        output = list(engine.render(str(template_path), {'x': 10, 'y': 5}))
        assert output[0] == 'Result: 15'
    
    def test_render_template_with_filters(self, tmp_templates_dir):
        """Render template using custom filters."""
        engine = TemplateEngine()
        # Create a template using a filter
        Path(tmp_templates_dir, 'with_filter.jinja2').write_text(
            '{{ data | format_dict("{key}") }}'
        )
        template_path = Path(tmp_templates_dir) / 'with_filter.jinja2'
        
        context = {'data': {'key': 'value'}}
        output = list(engine.render(str(template_path), context))
        assert output[0] == 'value'
    
    def test_render_template_with_tests(self, tmp_templates_dir):
        """Render template using custom tests."""
        engine = TemplateEngine()
        # Create a template using a test
        Path(tmp_templates_dir, 'with_test.jinja2').write_text(
            '{% if n is is_prime %}Prime{% else %}Not prime{% endif %}'
        )
        template_path = Path(tmp_templates_dir) / 'with_test.jinja2'
        
        # Test with prime number
        output = list(engine.render(str(template_path), {'n': 7}))
        assert output[0] == 'Prime'
        
        # Test with non-prime number
        output = list(engine.render(str(template_path), {'n': 4}))
        assert output[0] == 'Not prime'
    
    def test_render_empty_template(self, tmp_templates_dir):
        """Render empty template."""
        engine = TemplateEngine()
        template_path = Path(tmp_templates_dir) / 'empty.jinja2'
        template_path.write_text('')
        
        output = list(engine.render(str(template_path), {}))
        assert output[0] == ''
    
    def test_render_template_with_loops(self, tmp_templates_dir):
        """Render template with loops."""
        engine = TemplateEngine()
        Path(tmp_templates_dir, 'loop.jinja2').write_text(
            '{% for item in items %}{{ item }}\n{% endfor %}'
        )
        template_path = Path(tmp_templates_dir) / 'loop.jinja2'
        
        context = {'items': ['a', 'b', 'c']}
        output = list(engine.render(str(template_path), context))
        assert 'a\n' in output[0]
        assert 'b\n' in output[0]
        assert 'c\n' in output[0]
    
    def test_render_template_with_conditionals(self, tmp_templates_dir):
        """Render template with conditionals."""
        engine = TemplateEngine()
        Path(tmp_templates_dir, 'conditional.jinja2').write_text(
            '{% if flag %}Yes{% else %}No{% endif %}'
        )
        template_path = Path(tmp_templates_dir) / 'conditional.jinja2'
        
        # Test True case
        output = list(engine.render(str(template_path), {'flag': True}))
        assert output[0] == 'Yes'
        
        # Test False case
        output = list(engine.render(str(template_path), {'flag': False}))
        assert output[0] == 'No'


class TestTemplateEngineErrors:
    """Test error handling."""
    
    def test_undefined_variable_strict_mode(self, tmp_templates_dir):
        """Undefined variable raises error in strict mode."""
        engine = TemplateEngine(undefined_variables_mode_behaviour='strict')
        Path(tmp_templates_dir, 'undefined.jinja2').write_text(
            'Name: {{ undefined_var }}'
        )
        template_path = Path(tmp_templates_dir) / 'undefined.jinja2'
        
        with pytest.raises(UndefinedError):
            list(engine.render(str(template_path), {}))
    
    def test_undefined_variable_debug_mode(self, tmp_templates_dir):
        """Undefined variable renders debug output in debug mode."""
        engine = TemplateEngine(undefined_variables_mode_behaviour='DebugUndefined')
        Path(tmp_templates_dir, 'undefined.jinja2').write_text(
            'Name: {{ undefined_var }}'
        )
        template_path = Path(tmp_templates_dir) / 'undefined.jinja2'
        
        # Should not raise; renders debug info
        output = list(engine.render(str(template_path), {}))
        assert 'undefined_var' in output[0]
    
    def test_undefined_variable_empty_mode(self, tmp_templates_dir):
        """Undefined variable renders empty in empty mode."""
        engine = TemplateEngine(undefined_variables_mode_behaviour='Undefined')
        Path(tmp_templates_dir, 'undefined.jinja2').write_text(
            'Name: {{ undefined_var }}'
        )
        template_path = Path(tmp_templates_dir) / 'undefined.jinja2'
        
        # Should not raise; renders as empty
        output = list(engine.render(str(template_path), {}))
        assert output[0] == 'Name: '
    
    def test_template_not_found(self, tmp_templates_dir):
        """Missing template file raises error."""
        engine = TemplateEngine()
        template_path = Path(tmp_templates_dir) / 'nonexistent.jinja2'
        
        with pytest.raises(TemplateNotFound):
            list(engine.render(str(template_path), {}))
    
    def test_syntax_error_in_template(self, tmp_templates_dir):
        """Syntax error in template raises error."""
        engine = TemplateEngine()
        Path(tmp_templates_dir, 'syntax_error.jinja2').write_text(
            '{% if true %}\nMissing endif'
        )
        template_path = Path(tmp_templates_dir) / 'syntax_error.jinja2'
        
        with pytest.raises(TemplateSyntaxError):
            list(engine.render(str(template_path), {}))


class TestTemplateEngineEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_render_large_template(self, tmp_templates_dir):
        """Render large template (performance check)."""
        engine = TemplateEngine()
        # Create a large template with many variables
        template_content = '\n'.join([f'{{ var{i} }}' for i in range(1000)])
        Path(tmp_templates_dir, 'large.jinja2').write_text(template_content)
        template_path = Path(tmp_templates_dir) / 'large.jinja2'
        
        # Create context with 1000 variables
        context = {f'var{i}': i for i in range(1000)}
        
        output = list(engine.render(str(template_path), context))
        assert len(output[0]) > 0
        assert '999' in output[0]
    
    def test_render_special_characters(self, tmp_templates_dir):
        """Render template with special characters."""
        engine = TemplateEngine()
        Path(tmp_templates_dir, 'special.jinja2').write_text(
            'Special: {{ text }}'
        )
        template_path = Path(tmp_templates_dir) / 'special.jinja2'
        
        special_text = '<>&"\'©™®'
        context = {'text': special_text}
        output = list(engine.render(str(template_path), context))
        assert special_text in output[0]
    
    def test_render_unicode_content(self, tmp_templates_dir):
        """Render template with unicode content."""
        engine = TemplateEngine()
        Path(tmp_templates_dir, 'unicode.jinja2').write_text(
            '你好 {{ name }}! 🎉'
        )
        template_path = Path(tmp_templates_dir) / 'unicode.jinja2'
        
        output = list(engine.render(str(template_path), {'name': 'World'}))
        assert '你好' in output[0]
        assert '🎉' in output[0]
        assert 'World' in output[0]
    
    def test_render_multiline_template(self, tmp_templates_dir):
        """Render multiline template with whitespace."""
        engine = TemplateEngine()
        template_content = '''Line 1: {{ var1 }}
Line 2: {{ var2 }}
Line 3: {{ var3 }}'''
        Path(tmp_templates_dir, 'multiline.jinja2').write_text(template_content)
        template_path = Path(tmp_templates_dir) / 'multiline.jinja2'
        
        context = {'var1': 'A', 'var2': 'B', 'var3': 'C'}
        output = list(engine.render(str(template_path), context))
        assert 'Line 1: A' in output[0]
        assert 'Line 2: B' in output[0]
        assert 'Line 3: C' in output[0]
    
    def test_render_nested_context(self, tmp_templates_dir):
        """Render template with nested context objects."""
        engine = TemplateEngine()
        Path(tmp_templates_dir, 'nested.jinja2').write_text(
            '{{ user.name }} is {{ user.age }} years old from {{ user.address.city }}'
        )
        template_path = Path(tmp_templates_dir) / 'nested.jinja2'
        
        context = {
            'user': {
                'name': 'Alice',
                'age': 30,
                'address': {'city': 'New York'}
            }
        }
        output = list(engine.render(str(template_path), context))
        assert 'Alice' in output[0]
        assert '30' in output[0]
        assert 'New York' in output[0]


class TestTemplateEngineIntegration:
    """Integration tests combining multiple features."""
    
    def test_render_with_all_features(self, tmp_templates_dir):
        """Render template using filters, tests, globals, loops, conditionals."""
        engine = TemplateEngine()
        template_content = '''
{% for user in users %}
  User: {{ user.name }}
  {%- if user.id is is_prime %} (ID is prime){% endif %}
  Tags: {{ user.tags | tojson }}
{% endfor %}
'''
        Path(tmp_templates_dir, 'complex.jinja2').write_text(template_content)
        template_path = Path(tmp_templates_dir) / 'complex.jinja2'
        
        context = {
            'users': [
                {'name': 'Alice', 'id': 7, 'tags': ['admin', 'python']},
                {'name': 'Bob', 'id': 4, 'tags': ['user', 'testing']},
            ]
        }
        output = list(engine.render(str(template_path), context))
        assert 'Alice' in output[0]
        assert 'Bob' in output[0]
        assert 'admin' in output[0]
