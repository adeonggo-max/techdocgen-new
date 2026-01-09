"""VB.NET code parser"""

import re
from typing import Dict, List, Any
from .base_parser import BaseParser


class VBNetParser(BaseParser):
    """Parser for VB.NET source code"""
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse VB.NET code"""
        result = {
            "namespace": self._extract_namespace(code),
            "imports": self._extract_imports(code) if self.include_imports else [],
            "classes": self._extract_classes(code),
            "interfaces": self._extract_interfaces(code),
            "enums": self._extract_enums(code),
            "structures": self._extract_structures(code),
            "modules": self._extract_modules(code),
            "comments": self.extract_comments(code) if self.include_comments else []
        }
        return result
    
    def _extract_namespace(self, code: str) -> str:
        """Extract namespace declaration"""
        match = re.search(r'Namespace\s+([\w.]+)', code, re.IGNORECASE)
        return match.group(1) if match else ""
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract Imports statements"""
        imports = re.findall(r'Imports\s+([\w.*=]+)', code, re.IGNORECASE)
        return imports
    
    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        pattern = r'(?:Public|Private|Friend|Protected|MustInherit|NotInheritable|Partial)?\s*Class\s+(\w+)(?:\s+Inherits\s+([\w,\s<>]+))?\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            class_name = match.group(1)
            inherits = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            # Find class body (between Class and End Class)
            start_pos = match.end()
            body = self._extract_vb_block(code, start_pos, "Class")
            
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
        pattern = r'(?:Public|Private|Friend)?\s*Interface\s+(\w+)(?:\s+Inherits\s+([\w,\s]+))?\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            interface_name = match.group(1)
            inherits = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            start_pos = match.end()
            body = self._extract_vb_block(code, start_pos, "Interface")
            
            interface_info = {
                "name": interface_name,
                "inherits": inherits,
                "methods": self._extract_methods(body),
                "properties": self._extract_properties(body)
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_enums(self, code: str) -> List[Dict[str, Any]]:
        """Extract enum definitions"""
        enums = []
        pattern = r'(?:Public|Private|Friend)?\s*Enum\s+(\w+)\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            enum_name = match.group(1)
            start_pos = match.end()
            body = self._extract_vb_block(code, start_pos, "Enum")
            
            constants = re.findall(r'(\w+)(?:\s*=\s*[^\n]+)?', body)
            
            enum_info = {
                "name": enum_name,
                "constants": constants
            }
            enums.append(enum_info)
        
        return enums
    
    def _extract_structures(self, code: str) -> List[Dict[str, Any]]:
        """Extract structure definitions"""
        structures = []
        pattern = r'(?:Public|Private|Friend)?\s*Structure\s+(\w+)(?:\s+Implements\s+([\w,\s]+))?\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            struct_name = match.group(1)
            implements = [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            
            start_pos = match.end()
            body = self._extract_vb_block(code, start_pos, "Structure")
            
            struct_info = {
                "name": struct_name,
                "implements": implements,
                "fields": self._extract_fields(body),
                "properties": self._extract_properties(body)
            }
            structures.append(struct_info)
        
        return structures
    
    def _extract_modules(self, code: str) -> List[Dict[str, Any]]:
        """Extract module definitions"""
        modules = []
        pattern = r'(?:Public|Private|Friend)?\s*Module\s+(\w+)\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            module_name = match.group(1)
            start_pos = match.end()
            body = self._extract_vb_block(code, start_pos, "Module")
            
            module_info = {
                "name": module_name,
                "functions": self._extract_methods(body),
                "subroutines": self._extract_subroutines(body)
            }
            modules.append(module_info)
        
        return modules
    
    def _extract_methods(self, code: str) -> List[Dict[str, Any]]:
        """Extract function and method definitions"""
        methods = []
        # Functions (return values)
        pattern = r'(?:Public|Private|Friend|Protected|Shared|Overridable|Overrides|MustOverride|Async)?\s*Function\s+(\w+)\s*\([^)]*\)\s*(?:As\s+[\w<>,\s\[\]]+)?'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            method_name = match.group(1)
            method_info = {
                "name": method_name,
                "signature": match.group(0).strip(),
                "type": "Function",
                "modifiers": self._extract_modifiers(match.group(0))
            }
            methods.append(method_info)
        
        return methods
    
    def _extract_subroutines(self, code: str) -> List[Dict[str, Any]]:
        """Extract Sub (subroutine) definitions"""
        subroutines = []
        pattern = r'(?:Public|Private|Friend|Protected|Shared|Overridable|Overrides|MustOverride|Async)?\s*Sub\s+(\w+)\s*\([^)]*\)\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            sub_name = match.group(1)
            sub_info = {
                "name": sub_name,
                "signature": match.group(0).strip(),
                "type": "Sub",
                "modifiers": self._extract_modifiers(match.group(0))
            }
            subroutines.append(sub_info)
        
        return subroutines
    
    def _extract_properties(self, code: str) -> List[Dict[str, Any]]:
        """Extract property definitions"""
        properties = []
        pattern = r'(?:Public|Private|Friend|Protected|Shared|Overridable|Overrides)?\s*Property\s+(\w+)\s*(?:\([^)]*\))?\s*As\s+([\w<>,\s\[\]]+)'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            prop_name = match.group(1)
            prop_type = match.group(2).strip()
            
            prop_info = {
                "name": prop_name,
                "type": prop_type,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            properties.append(prop_info)
        
        return properties
    
    def _extract_fields(self, code: str) -> List[Dict[str, Any]]:
        """Extract field/variable definitions"""
        fields = []
        pattern = r'(?:Public|Private|Friend|Protected|Shared|ReadOnly|Const)?\s*(?:Dim|Private|Public|Friend|Protected)?\s*(\w+)\s+As\s+([\w<>,\s\[\]]+)(?:\s*=\s*[^\n]+)?'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            
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
        modifier_keywords = ['Public', 'Private', 'Friend', 'Protected', 'Shared', 'Overridable', 'Overrides', 'MustOverride', 'MustInherit', 'NotInheritable', 'Partial', 'Async', 'ReadOnly', 'Const', 'MustInherit']
        for mod in modifier_keywords:
            if mod.lower() in declaration.lower():
                modifiers.append(mod)
        return modifiers
    
    def _extract_vb_block(self, code: str, start_pos: int, block_type: str) -> str:
        """Extract VB.NET block content (between block start and End Block)"""
        if start_pos >= len(code):
            return ""
        
        # Find the matching End statement
        end_pattern = rf'End\s+{block_type}'
        end_match = re.search(end_pattern, code[start_pos:], re.IGNORECASE)
        
        if end_match:
            end_pos = start_pos + end_match.start()
            return code[start_pos:end_pos]
        
        return ""
    
    def extract_comments(self, code: str) -> List[str]:
        """Extract comments from VB.NET code"""
        comments = []
        # Extract single-line comments (')
        single_line = re.findall(r"'.*?$", code, re.MULTILINE)
        comments.extend(single_line)
        # Extract REM comments
        rem_comments = re.findall(r'REM\s+.*?$', code, re.IGNORECASE | re.MULTILINE)
        comments.extend(rem_comments)
        return comments
    
    def clean_comment(self, comment: str) -> str:
        """Clean VB.NET comment string"""
        comment = comment.strip()
        # Remove comment markers
        comment = re.sub(r"^'\s*", '', comment)
        comment = re.sub(r'^REM\s+', '', comment, flags=re.IGNORECASE)
        return comment.strip()







