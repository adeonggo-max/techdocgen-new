"""Folder reader for reading multiple files from a directory"""

from pathlib import Path
from typing import List, Dict, Any
from .base_reader import BaseReader


class FolderReader(BaseReader):
    """Reads source code from all files in a folder"""
    
    def __init__(self, folder_path: str, config: Dict[str, Any] = None):
        super().__init__(config)
        self.folder_path = Path(folder_path)
    
    def read(self) -> List[Dict[str, Any]]:
        """Read all source code files from the folder"""
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")
        
        if not self.folder_path.is_dir():
            raise ValueError(f"Path is not a directory: {self.folder_path}")
        
        files = []
        extensions = self.config.get("extensions", {})
        all_extensions = []
        for exts in extensions.values():
            all_extensions.extend(exts)
        
        # Recursively find all source files
        for file_path in self.folder_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in all_extensions:
                continue
            
            if self._should_exclude(file_path):
                continue
            
            if not self._is_valid_size(file_path):
                print(f"Warning: File {file_path} exceeds size limit, skipping")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                language = self._detect_language(file_path)
                
                files.append({
                    "path": str(file_path),
                    "content": content,
                    "language": language,
                    "name": file_path.name,
                    "relative_path": str(file_path.relative_to(self.folder_path))
                })
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
        
        return files







