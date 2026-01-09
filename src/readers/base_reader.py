"""Base reader interface"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path


class BaseReader(ABC):
    """Base class for all source code readers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.exclude_patterns = self.config.get("documentation", {}).get("exclude_patterns", [])
        self.max_file_size = self.config.get("documentation", {}).get("max_file_size_mb", 10) * 1024 * 1024
    
    @abstractmethod
    def read(self) -> List[Dict[str, Any]]:
        """
        Read source code files
        
        Returns:
            List of dictionaries with 'path', 'content', 'language' keys
        """
        pass
    
    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns"""
        path_str = str(file_path)
        for pattern in self.exclude_patterns:
            # Simple pattern matching (can be enhanced with pathspec)
            if pattern.replace("**/", "").replace("**", "") in path_str:
                return True
        return False
    
    def _is_valid_size(self, file_path: Path) -> bool:
        """Check if file size is within limits"""
        try:
            return file_path.stat().st_size <= self.max_file_size
        except:
            return False
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        extensions = self.config.get("extensions", {})
        
        for lang, exts in extensions.items():
            if ext in exts:
                return lang
        
        return "unknown"







