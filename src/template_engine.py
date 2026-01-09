"""Template engine for documentation generation"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape


class TemplateEngine:
    """Template engine for rendering documentation templates"""
    
    def __init__(self, template_dir: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize template engine
        
        Args:
            template_dir: Directory containing templates (default: ./templates)
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Determine template directory
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to templates directory in project root
            project_root = Path(__file__).parent.parent
            self.template_dir = project_root / "templates"
        
        # Create templates directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['join_paths'] = self._join_paths
        self.env.filters['format_file_size'] = self._format_file_size
        self.env.filters['count_items'] = self._count_items
    
    def _join_paths(self, paths: List[str]) -> str:
        """Join file paths with newlines"""
        return '\n'.join(f"- `{path}`" for path in paths)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _count_items(self, items: List) -> int:
        """Count items in a list"""
        return len(items) if items else 0
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context
        
        Args:
            template_name: Name of the template file
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered template as string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            # Fallback to default template if custom template not found
            if template_name != "default.md":
                return self.render("default.md", context)
            raise FileNotFoundError(
                f"Template '{template_name}' not found in {self.template_dir}. "
                f"Please create a default template or specify a valid template path."
            )
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template from a string
        
        Args:
            template_string: Template as string
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered template as string
        """
        template = self.env.from_string(template_string)
        return template.render(**context)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template files"""
        templates = []
        if self.template_dir.exists():
            for file in self.template_dir.glob("*.md"):
                templates.append(file.name)
        return sorted(templates)
    
    def create_default_template(self) -> Path:
        """
        Create a default template file if it doesn't exist
        
        Returns:
            Path to the default template file
        """
        default_template_path = self.template_dir / "default.md"
        
        if not default_template_path.exists():
            default_template = """# Technical Documentation

**TechDocGen by IBMC**

Generated using {{ llm_provider|upper }} LLM

---

{% if dependency_map %}
{{ dependency_map }}

---
{% endif %}

{% for language, files in files_by_language.items() %}
{% if language != "unknown" %}
## {{ language|upper }} Files

Found {{ files|length }} {{ language }} file(s)

{% for file_info in files %}
### {{ file_info.name }}

**Path:** `{{ file_info.relative_path or file_info.path }}`

{{ file_info.documentation }}

#### Code Structure

{% if file_info.parsed_info.classes %}
**Classes:** {{ file_info.parsed_info.classes|length }}
{% for cls in file_info.parsed_info.classes %}
- `{{ cls.name }}`{% if cls.methods %} ({{ cls.methods|length }} methods){% endif %}
{% endfor %}

{% endif %}

{% if file_info.parsed_info.functions %}
**Functions:** {{ file_info.parsed_info.functions|length }}

{% endif %}

{% if file_info.sequence_diagram %}
#### Sequence Diagram

{{ file_info.sequence_diagram }}

{% endif %}

---

{% endfor %}
{% endif %}
{% endfor %}
"""
            default_template_path.write_text(default_template, encoding='utf-8')
        
        return default_template_path
