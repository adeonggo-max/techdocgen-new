"""Ollama LLM integration for local models"""

from typing import Dict, Any, Optional
import requests
from .base_llm import BaseLLM


class OllamaLLM(BaseLLM):
    """Ollama local LLM integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama3.2")
        self.temperature = config.get("temperature", 0.3)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Ollama API"""
        url = f"{self.base_url}/api/generate"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Could not connect to Ollama at {self.base_url}. Make sure Ollama is running.")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")







