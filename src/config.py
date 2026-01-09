"""Configuration management for the documentation generator"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Manages configuration from YAML and environment variables"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self.config = self._load_config()
        self._load_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            return self._default_config()
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_env_vars(self):
        """Override config with environment variables"""
        # LLM API Keys
        if os.getenv("OPENAI_API_KEY"):
            self.config.setdefault("llm_providers", {}).setdefault("openai", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.config.setdefault("llm_providers", {}).setdefault("anthropic", {})["api_key"] = os.getenv("ANTHROPIC_API_KEY")
        
        # Ollama settings
        if os.getenv("OLLAMA_BASE_URL"):
            self.config.setdefault("llm_providers", {}).setdefault("ollama", {})["base_url"] = os.getenv("OLLAMA_BASE_URL")
        
        if os.getenv("OLLAMA_MODEL"):
            self.config.setdefault("llm_providers", {}).setdefault("ollama", {})["model"] = os.getenv("OLLAMA_MODEL")
        
        # Default provider
        if os.getenv("DEFAULT_LLM_PROVIDER"):
            self.config["default_llm_provider"] = os.getenv("DEFAULT_LLM_PROVIDER")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "languages": ["java", "csharp", "php"],
            "extensions": {
                "java": [".java"],
                "csharp": [".cs"],
                "php": [".php"]
            },
            "llm_providers": {
                "ollama": {
                    "enabled": True,
                    "model": "llama3.2",
                    "base_url": "http://localhost:11434"
                }
            },
            "default_llm_provider": "ollama",
            "documentation": {
                "include_comments": True,
                "include_imports": True,
                "include_methods": True,
                "include_classes": True,
                "include_functions": True
            },
            "output": {
                "format": "markdown",
                "directory": "./docs"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration"""
        return self.config.get("llm_providers", {}).get(provider, {})
    
    def get_default_provider(self) -> str:
        """Get default LLM provider"""
        return self.config.get("default_llm_provider", "ollama")







