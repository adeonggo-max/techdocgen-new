"""C# (.NET) code parser"""

import re
from typing import Dict, List, Any
from .base_parser import BaseParser


class CSharpParser(BaseParser):
    """Parser for C# source code"""
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse C# code"""
        result = {
            "namespace": self._extract_namespace(code),
            "using": self._extract_usings(code) if self.include_imports else [],
            "classes": self._extract_classes(code),
            "interfaces": self._extract_interfaces(code),
            "enums": self._extract_enums(code),
            "structs": self._extract_structs(code),
            "comments": self.extract_comments(code) if self.include_comments else []
        }
        return result
    
    def _extract_namespace(self, code: str) -> str:
        """Extract namespace declaration"""
        match = re.search(r'namespace\s+([\w.]+)', code)
        return match.group(1) if match else ""
    
    def _extract_usings(self, code: str) -> List[str]:
        """Extract using statements"""
        usings = re.findall(r'using\s+(?:static\s+)?([\w.*=]+);', code)
        return usings
    
    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        pattern = r'(?:public|private|internal|protected|abstract|sealed|static|partial)?\s*class\s+(\w+)(?:\s*:\s*([\w,\s<>]+))?\s*\{'
        
        for match in re.finditer(pattern, code):
            class_name = match.group(1)
            inherits = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            class_info = {
                "name": class_name,
                "inherits": inherits,
                "methods": self._extract_methods(body),
                "properties": self._extract_properties(body),
                "fields": self._extract_fields(body),
                "modifiers": self._extract_modifiers(match.group(0))
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_interfaces(self, code: str) -> List[Dict[str, Any]]:
        """Extract interface definitions"""
        interfaces = []
        pattern = r'(?:public|private|internal|protected)?\s*interface\s+(\w+)(?:\s*:\s*([\w,\s]+))?\s*\{'
        
        for match in re.finditer(pattern, code):
            interface_name = match.group(1)
            extends = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            interface_info = {
                "name": interface_name,
                "extends": extends,
                "methods": self._extract_methods(body),
                "properties": self._extract_properties(body)
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_enums(self, code: str) -> List[Dict[str, Any]]:
        """Extract enum definitions"""
        enums = []
        pattern = r'(?:public|private|internal)?\s*enum\s+(\w+)\s*\{'
        
        for match in re.finditer(pattern, code):
            enum_name = match.group(1)
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            constants = re.findall(r'(\w+)(?:\s*=\s*[^,}]+)?', body)
            
            enum_info = {
                "name": enum_name,
                "constants": constants
            }
            enums.append(enum_info)
        
        return enums
    
    def _extract_structs(self, code: str) -> List[Dict[str, Any]]:
        """Extract struct definitions"""
        structs = []
        pattern = r'(?:public|private|internal)?\s*struct\s+(\w+)(?:\s*:\s*([\w,\s]+))?\s*\{'
        
        for match in re.finditer(pattern, code):
            struct_name = match.group(1)
            inherits = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            start_pos = match.end()
            body = self._extract_balanced_braces(code, start_pos - 1)
            
            struct_info = {
                "name": struct_name,
                "inherits": inherits,
                "fields": self._extract_fields(body),
                "properties": self._extract_properties(body)
            }
            structs.append(struct_info)
        
        return structs
    
    def _extract_methods(self, code: str) -> List[Dict[str, Any]]:
        """Extract method definitions"""
        methods = []
        pattern = r'(?:public|private|internal|protected|static|virtual|override|abstract|async)?\s*(?:[\w<>,\s\[\]]+\s+)?(\w+)\s*\([^)]*\)\s*\{'
        
        for match in re.finditer(pattern, code):
            method_name = match.group(1)
            if method_name in ['if', 'for', 'while', 'switch', 'try', 'catch', 'using']:
                continue
            
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
        pattern = r'(?:public|private|internal|protected|static|virtual|override)?\s*([\w<>,\s\[\]]+)\s+(\w+)\s*\{\s*(?:get|set)'
        
        for match in re.finditer(pattern, code):
            prop_type = match.group(1).strip()
            prop_name = match.group(2)
            
            prop_info = {
                "name": prop_name,
                "type": prop_type,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            properties.append(prop_info)
        
        return properties
    
    def _extract_fields(self, code: str) -> List[Dict[str, Any]]:
        """Extract field definitions"""
        fields = []
        pattern = r'(?:public|private|internal|protected|static|readonly|const)?\s*([\w<>,\s\[\]]+)\s+(\w+)\s*(?:=\s*[^;]+)?;'
        
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
        modifier_keywords = ['public', 'private', 'internal', 'protected', 'static', 'virtual', 'override', 'abstract', 'sealed', 'partial', 'async', 'readonly', 'const']
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







