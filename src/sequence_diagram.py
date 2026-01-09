"""Sequence diagram generator for code visualization"""

import re
from typing import Dict, List, Any, Set, Optional


class SequenceDiagramGenerator:
    """Generates Mermaid sequence diagrams from parsed code"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Check both settings - diagrams enabled if either is True AND sequence_diagrams is not explicitly False
        arch_diagram = self.config.get("output", {}).get("include_architecture_diagram", False)
        seq_diagram = self.config.get("documentation", {}).get("include_sequence_diagrams", False)
        # Only enable if explicitly True
        self.include_diagrams = seq_diagram is True or (arch_diagram is True and seq_diagram is not False)
    
    def generate_sequence_diagram(self, parsed_info: Dict[str, Any], code: str, language: str = "java") -> Optional[str]:
        """Generate a sequence diagram from parsed code information"""
        if not self.include_diagrams:
            return None
        
        try:
            classes = parsed_info.get("classes", [])
            if not classes:
                return None
            
            # Extract method calls and interactions
            interactions = self._extract_interactions(code, classes, language)
            
            if not interactions:
                # Try to generate a simple diagram based on class structure
                return self._generate_simple_class_diagram(classes)
            
            # Generate Mermaid sequence diagram
            return self._build_mermaid_diagram(interactions, classes)
        
        except Exception as e:
            # Don't fail documentation generation if diagram fails
            return None
    
    def _extract_interactions(self, code: str, classes: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """Extract method calls and class interactions from code"""
        interactions = []
        
        # Build class name to methods mapping
        class_methods = {}
        for cls in classes:
            class_name = cls.get("name", "")
            methods = [m.get("name", "") for m in cls.get("methods", [])]
            class_methods[class_name] = methods
        
        # Find method calls in the code
        # This is a simplified approach - in reality, would need AST parsing for accuracy
        
        # Look for patterns like: object.method() or Class.method()
        if language == "java":
            # Pattern for method calls: identifier.identifier(parameters)
            pattern = r'(\w+(?:\.\w+)*)\s*\.\s*(\w+)\s*\('
            matches = re.finditer(pattern, code)
            
            for match in matches:
                caller_part = match.group(1).split('.')[-1]  # Get last part (variable name)
                method_name = match.group(2)
                
                # Try to find which class this method belongs to
                for class_name, methods in class_methods.items():
                    if method_name in methods:
                        # Find the calling class (simplified - look for class containing this code)
                        calling_class = self._find_calling_class(code, match.start(), classes)
                        if calling_class and calling_class != class_name:
                            interactions.append({
                                "from": calling_class,
                                "to": class_name,
                                "method": method_name
                            })
        
        return interactions
    
    def _find_calling_class(self, code: str, position: int, classes: List[Dict[str, Any]]) -> Optional[str]:
        """Find which class contains the code at the given position"""
        # Find the class that contains this position
        for cls in classes:
            # This is simplified - would need actual AST for accuracy
            # For now, return first class as placeholder
            return cls.get("name")
        return None
    
    def _generate_simple_class_diagram(self, classes: List[Dict[str, Any]]) -> str:
        """Generate a simple class interaction diagram when method calls can't be detected"""
        if len(classes) == 0:
            return None
        
        diagram_parts = []
        diagram_parts.append("```mermaid\nsequenceDiagram\n")
        
        # Show interactions between main classes
        main_classes = classes[:min(5, len(classes))]  # Limit to 5 classes for readability
        
        # Add participants first (required in Mermaid)
        for cls in main_classes:
            class_name = self._sanitize_name(cls.get("name", "Unknown"))
            diagram_parts.append(f"    participant {class_name}\n")
        diagram_parts.append("\n")
        
        # For single class, show a minimal valid diagram
        if len(main_classes) == 1:
            cls = main_classes[0]
            class_name = self._sanitize_name(cls.get("name", "Unknown"))
            methods = cls.get("methods", [])[:5]  # Show first 5 methods
            
            # For single class, just show it exists with a note about methods
            # This avoids self-referential arrows which can cause issues
            if methods:
                method_count = len([m for m in methods if m.get("name") and m.get("name") not in ['equals', 'hashCode', 'toString', '__init__', '__str__']])
                if method_count > 0:
                    diagram_parts.append(f"    Note right of {class_name}: Contains {method_count} method(s)\n")
                else:
                    diagram_parts.append(f"    Note right of {class_name}: Class definition\n")
            else:
                diagram_parts.append(f"    Note right of {class_name}: Empty class\n")
        else:
            # Multiple classes - show interactions
            for i in range(len(main_classes) - 1):
                from_class = self._sanitize_name(main_classes[i].get("name", f"Class{i}"))
                to_class = self._sanitize_name(main_classes[i + 1].get("name", f"Class{i+1}"))
                
                # Get first public method from target class
                methods = main_classes[i + 1].get("methods", [])
                method_name = "process"
                for method in methods:
                    mods = method.get("modifiers", [])
                    method_name_raw = method.get("name", "")
                    if method_name_raw and method_name_raw not in ['equals', 'hashCode', 'toString']:
                        if "public" in mods or not mods:
                            method_name = method_name_raw
                            break
                
                safe_method = self._sanitize_name(method_name)
                diagram_parts.append(f"    {from_class}->>{to_class}: {safe_method}()\n")
                diagram_parts.append(f"    activate {to_class}\n")
                diagram_parts.append(f"    {to_class}-->>{from_class}: return\n")
                diagram_parts.append(f"    deactivate {to_class}\n\n")
        
        diagram_parts.append("```\n")
        return "".join(diagram_parts)
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize class/method names for Mermaid (remove special chars, spaces)"""
        if not name:
            return "Unknown"
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[^\w]', '_', name)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it's not empty
        return sanitized if sanitized else "Unknown"
    
    def _build_mermaid_diagram(self, interactions: List[Dict[str, Any]], classes: List[Dict[str, Any]]) -> str:
        """Build Mermaid sequence diagram syntax from interactions"""
        if not interactions:
            return None
        
        diagram_parts = []
        diagram_parts.append("```mermaid\nsequenceDiagram\n")
        
        # Get unique participants
        participants: Set[str] = set()
        for interaction in interactions:
            participants.add(interaction["from"])
            participants.add(interaction["to"])
        
        # Add participants (sanitize names)
        for participant in sorted(participants):
            safe_name = self._sanitize_name(participant)
            diagram_parts.append(f"    participant {safe_name}\n")
        
        diagram_parts.append("\n")
        
        # Add interactions (sanitize names)
        for interaction in interactions[:10]:  # Limit to 10 interactions for readability
            from_class = self._sanitize_name(interaction["from"])
            to_class = self._sanitize_name(interaction["to"])
            method = self._sanitize_name(interaction["method"])
            
            diagram_parts.append(f"    {from_class}->>{to_class}: {method}()\n")
            diagram_parts.append(f"    activate {to_class}\n")
            diagram_parts.append(f"    {to_class}-->>{from_class}: return\n")
            diagram_parts.append(f"    deactivate {to_class}\n\n")
        
        diagram_parts.append("```\n")
        return "".join(diagram_parts)
    
    def generate_from_llm_analysis(self, parsed_info: Dict[str, Any], code: str, llm) -> Optional[str]:
        """Use LLM to analyze code and generate sequence diagram"""
        if not self.include_diagrams:
            return None
        
        if llm is None:
            return None
        
        try:
            classes = parsed_info.get("classes", [])
            if not classes or len(classes) == 0:
                return None
            
            # Create prompt for LLM to analyze code flow
            prompt = f"""Analyze the following code and generate a Mermaid sequence diagram showing the main method calls and interactions between classes.

Code structure:
"""
            for cls in classes[:5]:  # Limit to 5 classes
                prompt += f"\nClass: {cls.get('name', 'Unknown')}\n"
                methods = cls.get("methods", [])[:5]
                for method in methods:
                    prompt += f"  - {method.get('name', 'unknown')}()\n"
            
            prompt += f"""

Code snippet (first 1000 chars):
{code[:1000]}

Generate a Mermaid sequence diagram showing the main flow and interactions. Focus on:
1. Main entry points
2. Key method calls between classes
3. Important data flows

Return ONLY the Mermaid diagram code block, nothing else."""

            # Get LLM response
            llm_response = llm.generate(prompt, system_prompt="You are a code analysis expert. Generate clear, concise sequence diagrams.")
            
            # Extract Mermaid code if present
            if "```mermaid" in llm_response:
                # Extract just the mermaid block
                start = llm_response.find("```mermaid")
                end = llm_response.find("```", start + 10)
                if end > start:
                    mermaid_code = llm_response[start+10:end].strip()
                    # Validate and sanitize the Mermaid code
                    if "sequenceDiagram" in mermaid_code:
                        # Sanitize participant names in the LLM response
                        sanitized = self._sanitize_mermaid_code(mermaid_code)
                        # Validate the diagram before returning
                        if self._validate_mermaid_syntax(sanitized):
                            return f"```mermaid\n{sanitized}\n```\n"
                        else:
                            # If LLM diagram is invalid, fall back to simple diagram
                            return None
                    return None
                return None
            elif "sequenceDiagram" in llm_response:
                # Wrap in code block if not present and sanitize
                sanitized = self._sanitize_mermaid_code(llm_response)
                if self._validate_mermaid_syntax(sanitized):
                    return f"```mermaid\n{sanitized}\n```\n"
                return None
            
            return None
        
        except Exception as e:
            # If LLM generation fails, return None to use fallback
            return None
    
    def _sanitize_mermaid_code(self, code: str) -> str:
        """Sanitize Mermaid diagram code to fix common syntax issues"""
        lines = code.split('\n')
        sanitized_lines = []
        
        for line in lines:
            # Skip empty lines at start (but keep them in the middle)
            if not sanitized_lines and not line.strip():
                continue
            
            # Skip comment lines
            if line.strip().startswith('%%'):
                continue
            
            # Fix participant declarations
            if 'participant' in line.lower():
                # Extract and sanitize participant name
                match = re.search(r'participant\s+([^\s:]+)', line, re.IGNORECASE)
                if match:
                    orig_name = match.group(1)
                    safe_name = self._sanitize_name(orig_name)
                    line = re.sub(r'participant\s+' + re.escape(orig_name), f'participant {safe_name}', line, flags=re.IGNORECASE)
            
            # Sanitize names in arrow notations
            # Pattern: Class->>Class: method()
            arrow_pattern = r'(\w+(?:\w|_)*)\s*(->>|-->>|->|--)\s*(\w+(?:\w|_)*)\s*:\s*([^\\n]+)'
            def replace_arrows(m):
                from_class = self._sanitize_name(m.group(1))
                arrow = m.group(2)
                to_class = self._sanitize_name(m.group(3))
                method = m.group(4).strip()
                # Sanitize method name (remove invalid chars but keep parentheses)
                method = re.sub(r'[^\w\(\)\[\]\.]', '_', method)
                return f"{from_class}{arrow}{to_class}: {method}"
            
            line = re.sub(arrow_pattern, replace_arrows, line)
            
            # Sanitize activate/deactivate lines
            if 'activate' in line.lower() or 'deactivate' in line.lower():
                match = re.search(r'(activate|deactivate)\s+([^\s]+)', line, re.IGNORECASE)
                if match:
                    cmd = match.group(1).lower()
                    name = self._sanitize_name(match.group(2))
                    line = f"    {cmd} {name}"
            
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)
    
    def _validate_mermaid_syntax(self, code: str) -> bool:
        """Basic validation of Mermaid sequence diagram syntax"""
        if not code or "sequenceDiagram" not in code:
            return False
        
        lines = code.split('\n')
        has_participant = False
        
        for line in lines:
            line_lower = line.lower().strip()
            # Check for participant declarations
            if 'participant' in line_lower:
                has_participant = True
                # Validate participant syntax
                if not re.match(r'\s*participant\s+\w+', line):
                    return False
        
        # Sequence diagrams should have at least one participant
        if not has_participant:
            return False
        
        # Check for invalid characters in key positions
        if re.search(r'[<>{}]', code.replace('->>', '').replace('-->>', '').replace('->', '')):
            # Might have invalid HTML-like syntax
            pass
        
        return True

