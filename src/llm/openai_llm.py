"""OpenAI LLM integration"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from .base_llm import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or provide in config.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.get("model", "gpt-4-turbo-preview")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")







