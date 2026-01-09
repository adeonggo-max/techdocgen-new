"""MCP (Model Context Protocol) LLM integration"""

from typing import Dict, Any, Optional
import requests
from .base_llm import BaseLLM


class MCPLLM(BaseLLM):
    """MCP server integration for LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.server_url = config.get("server_url", "http://localhost:8000")
        self.model = config.get("model", "default")
        self.temperature = config.get("temperature", 0.3)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using MCP server"""
        url = f"{self.server_url}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            
            # Handle different MCP response formats
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0].get("message", {}).get("content", "")
            elif "content" in result:
                return result["content"]
            else:
                return str(result)
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Could not connect to MCP server at {self.server_url}. Make sure the MCP server is running.")
        except Exception as e:
            raise RuntimeError(f"MCP server error: {e}")







