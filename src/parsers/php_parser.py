"""PHP code parser"""

import re
from typing import Dict, List, Any
from .base_parser import BaseParser


class PHPParser(BaseParser):
    """Parser for PHP source code"""
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse PHP code"""
        result = {
            "namespace": self._extract_namespace(code),
            "use": self._extract_uses(code) if self.include_imports else [],
            "classes": self._extract_classes(code),
            "interfaces": self._extract_interfaces(code),
            "traits": self._extract_traits(code),
            "functions": self._extract_functions(code),
            "constants": self._extract_constants(code),
            "comments": self.extract_comments(code) if self.include_comments else []
        }
        return result
    
    def _extract_namespace(self, code: str) -> str:
        """Extract namespace declaration"""
        match = re.search(r'namespace\s+([\w\\]+);', code)
        return match.group(1) if match else ""
    
    def _extract_uses(self, code: str) -> List[str]:
        """Extract use/import statements"""
        uses = re.findall(r'use\s+([\w\\]+)(?:\s+as\s+\w+)?;', code)
        return uses
    
    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        pattern = r'(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{'
        
        for match in re.finditer(pattern, code):
            class_name = match.group(1)
            extends = match.group(2) if match.group(2) else None
            implements = [i.strip() for i in match.group(3).split(',')] if match.group(3) else []
            
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            class_info = {
                "name": class_name,
                "extends": extends,
                "implements": implements,
                "methods": self._extract_methods(body),
                "properties": self._extract_properties(body),
                "constants": self._extract_class_constants(body),
                "modifiers": self._extract_modifiers(match.group(0))
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_interfaces(self, code: str) -> List[Dict[str, Any]]:
        """Extract interface definitions"""
        interfaces = []
        pattern = r'interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?\s*\{'
        
        for match in re.finditer(pattern, code):
            interface_name = match.group(1)
            extends = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            interface_info = {
                "name": interface_name,
                "extends": extends,
                "methods": self._extract_methods(body)
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_traits(self, code: str) -> List[Dict[str, Any]]:
        """Extract trait definitions"""
        traits = []
        pattern = r'trait\s+(\w+)\s*\{'
        
        for match in re.finditer(pattern, code):
            trait_name = match.group(1)
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            trait_info = {
                "name": trait_name,
                "methods": self._extract_methods(body),
                "properties": self._extract_properties(body)
            }
            traits.append(trait_info)
        
        return traits
    
    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """Extract standalone function definitions"""
        functions = []
        # Match functions outside of classes
        pattern = r'function\s+(\w+)\s*\([^)]*\)\s*(?:\:\s*[\w\|]+)?\s*\{'
        
        for match in re.finditer(pattern, code):
            func_name = match.group(1)
            # Check if it's inside a class (simple heuristic)
            before_match = code[:match.start()]
            open_braces = before_match.count('{')
            close_braces = before_match.count('}')
            if 'class' in before_match and open_braces > close_braces:
                continue  # Skip, it's a method
            
            func_info = {
                "name": func_name,
                "signature": match.group(0).split('{')[0].strip()
            }
            functions.append(func_info)
        
        return functions
    
    def _extract_methods(self, code: str) -> List[Dict[str, Any]]:
        """Extract method definitions"""
        methods = []
        pattern = r'(?:public|private|protected|static|final|abstract)?\s*function\s+(\w+)\s*\([^)]*\)\s*(?:\:\s*[\w\|]+)?\s*\{'
        
        for match in re.finditer(pattern, code):
            method_name = match.group(1)
            
            method_info = {
                "name": method_name,
                "signature": match.group(0).split('{')[0].strip(),
                "modifiers": self._extract_modifiers(match.group(0))
            }
            methods.append(method_info)
        
        return methods
    
    def _extract_properties(self, code: str) -> List[Dict[str, Any]]:
        """Extract property definitions"""
        properties = []
        pattern = r'(?:public|private|protected|static)?\s*(?:\$(\w+)|const\s+(\w+))\s*(?:=\s*[^;]+)?;'
        
        for match in re.finditer(pattern, code):
            prop_name = match.group(1) or match.group(2)
            if not prop_name:
                continue
            
            prop_info = {
                "name": prop_name,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            properties.append(prop_info)
        
        return properties
    
    def _extract_constants(self, code: str) -> List[Dict[str, Any]]:
        """Extract constant definitions"""
        constants = []
        # Match define() calls
        define_pattern = r"define\s*\(\s*['\"](\w+)['\"]"
        for match in re.finditer(define_pattern, code):
            constants.append({"name": match.group(1), "type": "define"})
        
        # Match const declarations
        const_pattern = r'const\s+(\w+)\s*='
        for match in re.finditer(const_pattern, code):
            constants.append({"name": match.group(1), "type": "const"})
        
        return constants
    
    def _extract_class_constants(self, code: str) -> List[Dict[str, Any]]:
        """Extract class constant definitions"""
        constants = []
        pattern = r'(?:public|private|protected)?\s*const\s+(\w+)\s*='
        for match in re.finditer(pattern, code):
            constants.append({"name": match.group(1)})
        return constants
    
    def _extract_modifiers(self, declaration: str) -> List[str]:
        """Extract access and other modifiers"""
        modifiers = []
        modifier_keywords = ['public', 'private', 'protected', 'static', 'final', 'abstract']
        for mod in modifier_keywords:
            if mod in declaration:
                modifiers.append(mod)
        return modifiers
    
    def _extract_balanced_braces(self, code: str, start_pos: int) -> str:
        """Extract balanced brace content"""
        if start_pos >= len(code) or code[start_pos] != '{':
            return ""
        
        depth = 0
        end_pos = start_pos
        
        for i in range(start_pos, len(code)):
            if code[i] == '{':
                depth += 1
            elif code[i] == '}':
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        
        return code[start_pos:end_pos]







