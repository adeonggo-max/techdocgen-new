# Documentation Templates

This directory contains Jinja2 templates for generating technical documentation.

## Available Templates

### `confluence.md` (Recommended)
A comprehensive Confluence-style template with:
- Consistent structure across all LLM models
- Table of contents
- Structured sections (Overview, Code Structure, Dependencies, Class Details)
- Tables for better readability
- Professional formatting

### `default.md`
A simpler template that matches the original format.

## How Templates Work

1. **Template Engine**: The `TemplateEngine` class uses Jinja2 to render templates
2. **Data Binding**: The generator passes structured data to the template
3. **Consistent Output**: Templates ensure the same structure regardless of LLM model
4. **Customization**: You can create your own templates by copying and modifying existing ones

## Template Variables

Templates receive the following variables:

- `llm_provider`: The LLM provider name (e.g., "ollama", "openai")
- `generation_date`: Date when documentation was generated
- `total_files`: Total number of files processed
- `files_by_language`: Dictionary grouping files by programming language
- `dependency_map`: Markdown string of dependency map (if enabled)
- `languages`: List of languages found

For each file:
- `file_info.name`: File name
- `file_info.path`: Full file path
- `file_info.relative_path`: Relative file path
- `file_info.documentation`: LLM-generated documentation
- `file_info.parsed_info`: Parsed code structure (classes, methods, functions, etc.)
- `file_info.sequence_diagram`: Sequence diagram (if generated)

## Using Custom Templates

1. Create a new `.md` file in this directory
2. Use Jinja2 syntax for variables and control flow
3. Update `config.yaml` to specify your template:

```yaml
documentation:
  template: "your_template.md"
```

Or use the default Confluence template:

```yaml
documentation:
  template: "confluence.md"
```

## Template Syntax

Jinja2 templates support:
- Variables: `{{ variable_name }}`
- Filters: `{{ variable|upper }}`
- Conditionals: `{% if condition %}...{% endif %}`
- Loops: `{% for item in items %}...{% endfor %}`
- Comments: `{# This is a comment #}`

See [Jinja2 Documentation](https://jinja.palletsprojects.com/) for more details.
