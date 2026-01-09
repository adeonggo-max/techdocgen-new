"""Sequence diagram generator for code visualization"""

import re
from typing import Dict, List, Any, Set, Optional


class SequenceDiagramGenerator:
    """Generates Mermaid sequence diagrams from parsed code"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.include_diagrams = self.config.get("output", {}).get("include_architecture_diagram", False) or \
                                self.config.get("documentation", {}).get("include_sequence_diagrams", True)
    
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
        if len(classes) < 2:
            return None
        
        diagram_parts = []
        diagram_parts.append("```mermaid\nsequenceDiagram\n")
        
        # Show interactions between main classes
        main_classes = classes[:min(5, len(classes))]  # Limit to 5 classes for readability
        
        for i, cls in enumerate(main_classes):
            class_name = cls.get("name", f"Class{i}")
            # Show activation
            diagram_parts.append(f"    activate {class_name}\n")
            
            # Show some methods
            methods = cls.get("methods", [])[:3]  # Show first 3 methods
            for method in methods:
                method_name = method.get("name", "")
                if method_name and method_name not in ['equals', 'hashCode', 'toString']:
                    diagram_parts.append(f"    {class_name}->>{class_name}: {method_name}()\n")
            
            diagram_parts.append(f"    deactivate {class_name}\n\n")
        
        # Add interactions between classes
        for i in range(len(main_classes) - 1):
            from_class = main_classes[i].get("name", f"Class{i}")
            to_class = main_classes[i + 1].get("name", f"Class{i+1}")
            
            # Get first public method from target class
            methods = main_classes[i + 1].get("methods", [])
            method_name = "process()"
            for method in methods:
                mods = method.get("modifiers", [])
                if "public" in mods or not mods:
                    method_name = method.get("name", "process()") + "()"
                    break
            
            diagram_parts.append(f"    {from_class}->>{to_class}: {method_name}\n")
            diagram_parts.append(f"    activate {to_class}\n")
            diagram_parts.append(f"    {to_class}-->>{from_class}: return\n")
            diagram_parts.append(f"    deactivate {to_class}\n\n")
        
        diagram_parts.append("```\n")
        return "".join(diagram_parts)
    
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
        
        # Add participants
        for participant in sorted(participants):
            diagram_parts.append(f"    participant {participant}\n")
        
        diagram_parts.append("\n")
        
        # Add interactions
        for interaction in interactions[:10]:  # Limit to 10 interactions for readability
            from_class = interaction["from"]
            to_class = interaction["to"]
            method = interaction["method"]
            
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
                    return llm_response[start:end+3] + "\n"
                return llm_response
            elif "sequenceDiagram" in llm_response:
                # Wrap in code block if not present
                return f"```mermaid\n{llm_response}\n```\n"
            
            return None
        
        except Exception as e:
            return None







