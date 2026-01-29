"""Streaming writer for large documentation outputs"""

from typing import Dict, Any, List, Optional
from pathlib import Path


class StreamingDocWriter:
    """Incrementally write documentation to avoid large memory usage"""
    
    def __init__(self, output_path: str, llm_provider: str, model_name: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.output_path.open("w", encoding="utf-8")
        self.total_files = 0
        self.languages = set()
        self.llm_provider = llm_provider
        self.model_name = model_name
        self._write_header()
    
    def _write_header(self):
        self.file.write("# Technical Documentation\n\n")
        local_prefix = "local " if self.llm_provider == "ollama" else ""
        self.file.write(f"**TechDocGen by IBMC**  \n")
        self.file.write(f"**Model Use :** {local_prefix}{self.model_name}\n\n")
        self.file.write("---\n\n")
        self.file.write("## Files\n\n")
    
    def write_file_section(self, file_info: Dict[str, Any], language: str):
        """Write a single file section"""
        self.total_files += 1
        self.languages.add(language)
        
        self.file.write(f"### {file_info['name']} ({language.upper()})\n\n")
        self.file.write(f"**Path:** `{file_info.get('relative_path') or file_info.get('path')}`\n\n")
        self.file.write(file_info.get("documentation", "").strip() + "\n\n")
        
        parsed = file_info.get("parsed_info", {})
        if parsed:
            self.file.write("#### Code Structure\n\n")
            if parsed.get("classes"):
                self.file.write(f"- Classes: {len(parsed['classes'])}\n")
            if parsed.get("interfaces"):
                self.file.write(f"- Interfaces: {len(parsed['interfaces'])}\n")
            if parsed.get("functions"):
                self.file.write(f"- Functions: {len(parsed['functions'])}\n")
            if parsed.get("enums"):
                self.file.write(f"- Enums: {len(parsed['enums'])}\n")
            if parsed.get("types"):
                self.file.write(f"- Types: {len(parsed['types'])}\n")
            if parsed.get("imports"):
                self.file.write(f"- Imports: {len(parsed['imports'])}\n")
            self.file.write("\n")
        
        messaging = file_info.get("messaging_flows")
        if messaging:
            self.file.write("#### Messaging Flows\n\n")
            if messaging.get("flows"):
                for flow in messaging["flows"]:
                    consumers = ", ".join(flow.get("consumers", [])) or "N/A"
                    sagas = ", ".join(flow.get("sagas", [])) or "N/A"
                    self.file.write(f"- Queue `{flow.get('queue')}` -> Consumers: {consumers}; Sagas: {sagas}\n")
            if messaging.get("publishes"):
                self.file.write(f"- Publishes: {', '.join(messaging['publishes'])}\n")
            if messaging.get("sends"):
                self.file.write(f"- Sends: {', '.join(messaging['sends'])}\n")
            if messaging.get("send_endpoints"):
                self.file.write(f"- Send Endpoints: {', '.join(messaging['send_endpoints'])}\n")
            if messaging.get("consumer_messages"):
                entries = [f"{item.get('consumer')}({item.get('message')})" for item in messaging["consumer_messages"]]
                if entries:
                    self.file.write(f"- Consumers: {', '.join(entries)}\n")
            self.file.write("\n")
        
        if file_info.get("sequence_diagram"):
            self.file.write("#### Sequence Diagram\n\n")
            self.file.write(file_info["sequence_diagram"] + "\n\n")

        call_graphs = file_info.get("call_graphs") or []
        if call_graphs:
            self.file.write("#### Call Graphs\n\n")
            for graph in call_graphs:
                self.file.write(f"##### {graph.get('class')}\n\n")
                self.file.write(graph.get("mermaid", "") + "\n\n")
        
        self.file.write("---\n\n")
    
    def finalize(self, integration_graph: Optional[str] = None, app_sequence_diagram: Optional[str] = None):
        """Finalize the document with summary"""
        if app_sequence_diagram:
            self.file.write("## App Interaction Sequence\n\n")
            self.file.write(app_sequence_diagram.strip() + "\n\n")
        if integration_graph:
            self.file.write("## Integration Graph\n\n")
            self.file.write(integration_graph.strip() + "\n\n")
        self.file.write("## Summary\n\n")
        self.file.write(f"- Total files processed: {self.total_files}\n")
        self.file.write(f"- Languages: {', '.join(sorted(self.languages))}\n\n")
        self.file.write("---\n\n")
        self.file.write("*This documentation was automatically generated.*\n")
        self.file.close()
