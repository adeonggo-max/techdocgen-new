"""Anthropic (Claude) LLM integration"""

import os
from typing import Dict, Any, Optional
from anthropic import Anthropic
from .base_llm import BaseLLM


class AnthropicLLM(BaseLLM):
    """Anthropic Claude API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or provide in config.")
        
        self.client = Anthropic(api_key=api_key)
        self.model = config.get("model", "claude-sonnet-4-5-20250929")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt or "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            error_msg = str(e)
            # Check if it's a model not found error
            if "not_found_error" in error_msg or "404" in error_msg or "model:" in error_msg:
                raise RuntimeError(
                    f"Anthropic API error: Model '{self.model}' not found. "
                    f"Please check your config.yaml and update the model name. "
                    f"Available models: claude-sonnet-4-5-20250929, claude-3-7-sonnet-20250219, claude-3-5-haiku-20241022, claude-3-haiku-20240307. "
                    f"Check Anthropic docs: https://docs.anthropic.com/en/api/models. "
                    f"Original error: {e}"
                )
            raise RuntimeError(f"Anthropic API error: {e}")

