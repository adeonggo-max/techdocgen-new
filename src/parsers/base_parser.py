"""Base parser interface"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import re


class BaseParser(ABC):
    """Base class for language-specific parsers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.include_comments = self.config.get("documentation", {}).get("include_comments", True)
        self.include_imports = self.config.get("documentation", {}).get("include_imports", True)
    
    @abstractmethod
    def parse(self, code: str) -> Dict[str, Any]:
        """
        Parse source code and extract structured information
        
        Args:
            code: Source code string
            
        Returns:
            Dictionary with parsed information (classes, functions, imports, etc.)
        """
        pass
    
    def extract_comments(self, code: str) -> List[str]:
        """Extract comments from code"""
        comments = []
        # Extract single-line comments
        single_line = re.findall(r'//.*?$', code, re.MULTILINE)
        comments.extend(single_line)
        # Extract multi-line comments
        multi_line = re.findall(r'/\*.*?\*/', code, re.DOTALL)
        comments.extend(multi_line)
        return comments
    
    def clean_comment(self, comment: str) -> str:
        """Clean comment string"""
        comment = comment.strip()
        # Remove comment markers
        comment = re.sub(r'^//\s*', '', comment)
        comment = re.sub(r'^/\*\s*', '', comment)
        comment = re.sub(r'\s*\*/$', '', comment)
        comment = re.sub(r'^\*\s*', '', comment, flags=re.MULTILINE)
        return comment.strip()







