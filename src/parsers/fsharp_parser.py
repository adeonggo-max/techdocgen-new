"""F# code parser"""

import re
from typing import Dict, List, Any
from .base_parser import BaseParser


class FSharpParser(BaseParser):
    """Parser for F# source code"""
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse F# code"""
        result = {
            "namespace": self._extract_namespace(code),
            "open": self._extract_opens(code) if self.include_imports else [],
            "modules": self._extract_modules(code),
            "types": self._extract_types(code),
            "records": self._extract_records(code),
            "unions": self._extract_unions(code),
            "functions": self._extract_functions(code),
            "comments": self.extract_comments(code) if self.include_comments else []
        }
        return result
    
    def _extract_namespace(self, code: str) -> str:
        """Extract namespace declaration"""
        match = re.search(r'namespace\s+([\w.]+)', code, re.IGNORECASE)
        return match.group(1) if match else ""
    
    def _extract_opens(self, code: str) -> List[str]:
        """Extract open statements"""
        opens = re.findall(r'open\s+([\w.*=]+)', code, re.IGNORECASE)
        return opens
    
    def _extract_modules(self, code: str) -> List[Dict[str, Any]]:
        """Extract module definitions"""
        modules = []
        pattern = r'(?:public\s+)?module\s+(\w+)\s*='
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            module_name = match.group(1)
            start_pos = match.end()
            body = self._extract_module_body(code, start_pos)
            
            module_info = {
                "name": module_name,
                "functions": self._extract_functions(body),
                "types": self._extract_types(body)
            }
            modules.append(module_info)
        
        return modules
    
    def _extract_types(self, code: str) -> List[Dict[str, Any]]:
        """Extract type definitions (classes, interfaces)"""
        types = []
        # Classes
        pattern = r'(?:type\s+)?(\w+)\s*\([^)]*\)\s*=\s*class'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            type_name = match.group(1)
            start_pos = match.end()
            body = self._extract_fs_block(code, start_pos, "class", "end")
            
            type_info = {
                "name": type_name,
                "kind": "class",
                "members": self._extract_members(body)
            }
            types.append(type_info)
        
        # Interfaces
        pattern = r'type\s+(\w+)\s*=\s*interface'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            type_name = match.group(1)
            start_pos = match.end()
            body = self._extract_fs_block(code, start_pos, "interface", "end")
            
            type_info = {
                "name": type_name,
                "kind": "interface",
                "members": self._extract_members(body)
            }
            types.append(type_info)
        
        return types
    
    def _extract_records(self, code: str) -> List[Dict[str, Any]]:
        """Extract record type definitions"""
        records = []
        pattern = r'type\s+(\w+)\s*=\s*\{[^}]*\}'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            record_name = match.group(1)
            body = match.group(0)
            
            # Extract fields
            fields = re.findall(r'(\w+)\s*:\s*([\w<>,\s\[\]]+)', body)
            
            record_info = {
                "name": record_name,
                "fields": [{"name": f[0], "type": f[1].strip()} for f in fields]
            }
            records.append(record_info)
        
        return records
    
    def _extract_unions(self, code: str) -> List[Dict[str, Any]]:
        """Extract discriminated union type definitions"""
        unions = []
        pattern = r'type\s+(\w+)\s*=\s*'
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            union_name = match.group(1)
            # Check if it's a union (has |)
            union_match = re.search(rf'type\s+{union_name}\s*=\s*([^\n]+)', code, re.IGNORECASE)
            if union_match and '|' in union_match.group(1):
                cases = re.findall(r'\|\s*(\w+)(?:[^|]*)', union_match.group(1))
                
                union_info = {
                    "name": union_name,
                    "cases": cases
                }
                unions.append(union_info)
        
        return unions
    
    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """Extract function definitions"""
        functions = []
        # Function with let binding
        pattern = r'(?:let\s+(?:rec\s+)?|member\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>,\s\[\]]+)?\s*='
        
        for match in re.finditer(pattern, code, re.IGNORECASE):
            func_name = match.group(1)
            if func_name in ['if', 'for', 'while', 'match', 'try', 'with']:
                continue
            
            func_info = {
                "name": func_name,
                "signature": match.group(0).strip(),
                "modifiers": self._extract_modifiers(match.group(0))
            }
            functions.append(func_info)
        
        return functions
    
    def _extract_members(self, code: str) -> List[Dict[str, Any]]:
        """Extract class/interface members"""
        members = []
        # Properties
        pattern = r'member\s+(?:this\.)?(\w+)\s*(?::\s*[\w<>,\s\[\]]+)?\s*(?:with\s+get|with\s+set)'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            members.append({
                "name": match.group(1),
                "kind": "property",
                "signature": match.group(0).strip()
            })
        
        # Methods
        pattern = r'member\s+(?:this\.)?(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>,\s\[\]]+)?'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            members.append({
                "name": match.group(1),
                "kind": "method",
                "signature": match.group(0).strip()
            })
        
        return members
    
    def _extract_modifiers(self, declaration: str) -> List[str]:
        """Extract modifiers"""
        modifiers = []
        modifier_keywords = ['public', 'private', 'internal', 'static', 'abstract', 'override', 'rec']
        for mod in modifier_keywords:
            if mod.lower() in declaration.lower():
                modifiers.append(mod)
        return modifiers
    
    def _extract_fs_block(self, code: str, start_pos: int, start_keyword: str, end_keyword: str) -> str:
        """Extract F# block content"""
        if start_pos >= len(code):
            return ""
        
        # Find the matching end statement
        end_pattern = rf'\b{end_keyword}\b'
        end_match = re.search(end_pattern, code[start_pos:], re.IGNORECASE)
        
        if end_match:
            end_pos = start_pos + end_match.start()
            return code[start_pos:end_pos]
        
        return ""
    
    def _extract_module_body(self, code: str, start_pos: int) -> str:
        """Extract module body until next module or end of scope"""
        if start_pos >= len(code):
            return ""
        
        # Find next module or end of file
        next_module = re.search(r'\bmodule\s+\w+\s*=', code[start_pos:], re.IGNORECASE)
        if next_module:
            return code[start_pos:start_pos + next_module.start()]
        
        return code[start_pos:]
    
    def extract_comments(self, code: str) -> List[str]:
        """Extract comments from F# code"""
        comments = []
        # Extract single-line comments (//)
        single_line = re.findall(r'//.*?$', code, re.MULTILINE)
        comments.extend(single_line)
        # Extract multi-line comments (* ... *)
        multi_line = re.findall(r'\(\*.*?\*\)', code, re.DOTALL)
        comments.extend(multi_line)
        return comments
    
    def clean_comment(self, comment: str) -> str:
        """Clean F# comment string"""
        comment = comment.strip()
        # Remove comment markers
        comment = re.sub(r'^//\s*', '', comment)
        comment = re.sub(r'^\(\*\s*', '', comment)
        comment = re.sub(r'\s*\*\)$', '', comment)
        comment = re.sub(r'^\*\s*', '', comment, flags=re.MULTILINE)
        return comment.strip()







