"""Single file reader"""

from pathlib import Path
from typing import List, Dict, Any
from .base_reader import BaseReader


class FileReader(BaseReader):
    """Reads source code from a single file"""
    
    def __init__(self, file_path: str, config: Dict[str, Any] = None):
        super().__init__(config)
        self.file_path = Path(file_path)
    
    def read(self) -> List[Dict[str, Any]]:
        """Read the single file"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")
        
        if self._should_exclude(self.file_path):
            return []
        
        if not self._is_valid_size(self.file_path):
            print(f"Warning: File {self.file_path} exceeds size limit, skipping")
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_language(self.file_path)
            
            return [{
                "path": str(self.file_path),
                "content": content,
                "language": language,
                "name": self.file_path.name
            }]
        except Exception as e:
            print(f"Error reading file {self.file_path}: {e}")
            return []







