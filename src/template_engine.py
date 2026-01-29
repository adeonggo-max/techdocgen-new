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

Model Use : {% if llm_provider == 'ollama' %}local {% endif %}{{ model_name }}

---

{% if dependency_map %}
{{ dependency_map }}

---
{% endif %}

{% if integration_graph or correlation_graph %}
## Visualization

{% if correlation_signals %}
### Correlation Signals

- .NET Messaging Files: {{ correlation_signals.csharp_messaging|length }}
- Node.js Messaging Files: {{ correlation_signals.node_messaging|length }}
- Angular Files: {{ correlation_signals.angular_files|length }}
- Cross-Stack Signal: {% if correlation_signals.csharp_messaging and correlation_signals.node_messaging %}Detected{% else %}Not detected{% endif %}

{% if correlation_graph %}
### Correlation Graph

{{ correlation_graph }}

{% endif %}
{% endif %}

{% if integration_graph %}
### Integration Graph

{{ integration_graph }}

{% endif %}

---
{% endif %}

{% if app_sequence_diagram %}
## App Interaction Sequence

{{ app_sequence_diagram }}

---
{% endif %}

{% if service_catalog %}
## Service Catalog

{% if service_catalog.controllers %}
### Controllers

{% for ctrl in service_catalog.controllers %}
- `{{ ctrl.name }}`{% if ctrl.route %} (Route: `{{ ctrl.route }}`){% endif %}
{% endfor %}

{% endif %}

{% if service_catalog.endpoints %}
### Endpoints

| Controller | Method | HTTP | Route |
|------------|--------|------|-------|
{% for ep in service_catalog.endpoints %}
| `{{ ep.controller }}` | `{{ ep.method }}` | {{ ep.http_verbs|join(', ') }} | `{{ ep.route }}` |
{% endfor %}

{% endif %}

{% if service_catalog.endpoint_flows %}
### Endpoint Flow Details

{% for ep in service_catalog.endpoint_flows %}
#### {{ ep.http_verbs|join(', ') }} {{ ep.route }} ({{ ep.controller }}.{{ ep.method }})

{% if ep.steps %}
{% for step in ep.steps %}
- {{ step }}
{% endfor %}
{% else %}
- No flow steps detected.
{% endif %}

{% endfor %}

{% endif %}

{% if service_catalog.services %}
### Services / Repositories

{{ service_catalog.services|join(', ') }}

{% endif %}

{% if service_catalog.interfaces %}
### Interfaces

{{ service_catalog.interfaces|join(', ') }}

{% endif %}

{% if service_catalog.flow_graph %}
### Controller Flow Graph

{{ service_catalog.flow_graph }}

{% endif %}

---
{% endif %}

{% if service_catalog and service_catalog.api_spec %}
## API Specifications

| HTTP | Route | Controller.Method | Components/Services |
|------|-------|-------------------|---------------------|
{% for api in service_catalog.api_spec %}
| {{ api.http_verbs|join(', ') }} | `{{ api.route }}` | `{{ api.controller }}.{{ api.method }}` | {% if api.components %}{{ api.components|join(', ') }}{% else %}N/A{% endif %} |
{% endfor %}

{% if service_catalog.endpoint_sequence_diagrams %}
### Endpoint Sequence Diagrams

{% for seq in service_catalog.endpoint_sequence_diagrams %}
#### {{ seq.http_verbs|join(', ') }} {{ seq.route }} ({{ seq.controller }}.{{ seq.method }})

{{ seq.mermaid }}

{% endfor %}
{% endif %}

---
{% endif %}

{% if messaging_flows %}
## Messaging Flows

{% for flow in messaging_flows %}
- Queue `{{ flow.queue }}`{% if flow.consumers %} -> Consumers: {{ flow.consumers|join(', ') }}{% endif %}{% if flow.sagas %}; Sagas: {{ flow.sagas|join(', ') }}{% endif %} {% if flow.file %}(`{{ flow.file }}`){% endif %}
{% endfor %}

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

{% if file_info.parsed_info.interfaces %}
**Interfaces:** {{ file_info.parsed_info.interfaces|length }}

{% endif %}

{% if file_info.parsed_info.enums %}
**Enums:** {{ file_info.parsed_info.enums|length }}

{% endif %}

{% if file_info.parsed_info.types %}
**Type Aliases:** {{ file_info.parsed_info.types|length }}

{% endif %}

{% if file_info.parsed_info.top_level_keys %}
**Top-Level Config Keys:** {{ file_info.parsed_info.top_level_keys|length }}

{% endif %}

{% if file_info.parsed_info.custom_elements %}
**Custom Elements:** {{ file_info.parsed_info.custom_elements|length }}

{% endif %}

{% if file_info.sequence_diagram %}
#### Sequence Diagram

{{ file_info.sequence_diagram }}

{% endif %}

{% if file_info.call_graphs %}
#### Call Graphs

{% for graph in file_info.call_graphs %}
##### {{ graph.class }}

{{ graph.mermaid }}

{% endfor %}

{% endif %}

{% if file_info.messaging_flows %}
#### Messaging Flows

{% if file_info.messaging_flows.flows %}
{% for flow in file_info.messaging_flows.flows %}
- Queue `{{ flow.queue }}`{% if flow.consumers %} -> Consumers: {{ flow.consumers|join(', ') }}{% endif %}{% if flow.sagas %}; Sagas: {{ flow.sagas|join(', ') }}{% endif %}
{% endfor %}
{% endif %}

{% if file_info.messaging_flows.publishes %}
- Publishes: {{ file_info.messaging_flows.publishes|join(', ') }}
{% endif %}
{% if file_info.messaging_flows.sends %}
- Sends: {{ file_info.messaging_flows.sends|join(', ') }}
{% endif %}
{% if file_info.messaging_flows.send_endpoints %}
- Send Endpoints: {{ file_info.messaging_flows.send_endpoints|join(', ') }}
{% endif %}
{% if file_info.messaging_flows.consumer_messages %}
- Consumers: {% for item in file_info.messaging_flows.consumer_messages %}{{ item.consumer }}({{ item.message }}){% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

{% endif %}

---

{% endfor %}
{% endif %}
{% endfor %}
"""
            default_template_path.write_text(default_template, encoding='utf-8')
        
        return default_template_path
