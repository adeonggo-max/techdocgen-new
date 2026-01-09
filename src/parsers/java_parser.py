"""Java code parser"""

import re
from typing import Dict, List, Any
from .base_parser import BaseParser


class JavaParser(BaseParser):
    """Parser for Java source code"""
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse Java code"""
        result = {
            "package": self._extract_package(code),
            "imports": self._extract_imports(code) if self.include_imports else [],
            "classes": self._extract_classes(code),
            "interfaces": self._extract_interfaces(code),
            "enums": self._extract_enums(code),
            "comments": self.extract_comments(code) if self.include_comments else []
        }
        return result
    
    def _extract_package(self, code: str) -> str:
        """Extract package declaration"""
        match = re.search(r'package\s+([\w.]+);', code)
        return match.group(1) if match else ""
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements"""
        imports = re.findall(r'import\s+(?:static\s+)?([\w.*]+);', code)
        return imports
    
    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        # Match class declarations with modifiers, name, and extends/implements
        pattern = r'(?:public|private|protected|abstract|final|static)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{'
        
        for match in re.finditer(pattern, code):
            class_name = match.group(1)
            extends = match.group(2) if match.group(2) else None
            implements = [i.strip() for i in match.group(3).split(',')] if match.group(3) else []
            
            # Extract class body
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            class_info = {
                "name": class_name,
                "extends": extends,
                "implements": implements,
                "methods": self._extract_methods(body),
                "fields": self._extract_fields(body),
                "modifiers": self._extract_modifiers(match.group(0))
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_interfaces(self, code: str) -> List[Dict[str, Any]]:
        """Extract interface definitions"""
        interfaces = []
        pattern = r'(?:public|private|protected)?\s*interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?\s*\{'
        
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
    
    def _extract_enums(self, code: str) -> List[Dict[str, Any]]:
        """Extract enum definitions"""
        enums = []
        pattern = r'(?:public|private|protected)?\s*enum\s+(\w+)\s*\{'
        
        for match in re.finditer(pattern, code):
            enum_name = match.group(1)
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            # Extract enum constants
            constants = re.findall(r'(\w+)(?:\([^)]*\))?(?=,|;|\})', body)
            
            enum_info = {
                "name": enum_name,
                "constants": constants
            }
            enums.append(enum_info)
        
        return enums
    
    def _extract_methods(self, code: str) -> List[Dict[str, Any]]:
        """Extract method definitions"""
        methods = []
        # Match method declarations
        pattern = r'(?:public|private|protected|static|final|abstract|synchronized)?\s*(?:[\w<>,\s\[\]]+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
        
        for match in re.finditer(pattern, code):
            method_name = match.group(1)
            # Skip constructors (same name as class)
            if method_name in ['if', 'for', 'while', 'switch', 'try', 'catch']:
                continue
            
            method_info = {
                "name": method_name,
                "signature": match.group(0).split('{')[0].strip(),
                "modifiers": self._extract_modifiers(match.group(0))
            }
            methods.append(method_info)
        
        return methods
    
    def _extract_fields(self, code: str) -> List[Dict[str, Any]]:
        """Extract field/attribute definitions"""
        fields = []
        # Match field declarations
        pattern = r'(?:public|private|protected|static|final)?\s*([\w<>,\s\[\]]+)\s+(\w+)\s*(?:=\s*[^;]+)?;'
        
        for match in re.finditer(pattern, code):
            field_type = match.group(1).strip()
            field_name = match.group(2)
            
            field_info = {
                "name": field_name,
                "type": field_type,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            fields.append(field_info)
        
        return fields
    
    def _extract_modifiers(self, declaration: str) -> List[str]:
        """Extract access and other modifiers"""
        modifiers = []
        modifier_keywords = ['public', 'private', 'protected', 'static', 'final', 'abstract', 'synchronized']
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







