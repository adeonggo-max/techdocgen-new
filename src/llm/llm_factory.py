"""Factory for creating LLM instances"""

from typing import Dict, Any
from .base_llm import BaseLLM
from .openai_llm import OpenAILLM
from .anthropic_llm import AnthropicLLM
from .ollama_llm import OllamaLLM
from .mcp_llm import MCPLLM


class LLMFactory:
    """Factory class for creating LLM instances"""
    
    _providers = {
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
        "ollama": OllamaLLM,
        "mcp": MCPLLM
    }
    
    @classmethod
    def create(cls, provider: str, config: Dict[str, Any]) -> BaseLLM:
        """
        Create an LLM instance for the specified provider
        
        Args:
            provider: LLM provider name (openai, anthropic, ollama, mcp)
            config: Configuration dictionary
            
        Returns:
            LLM instance
        """
        provider = provider.lower()
        if provider not in cls._providers:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: {list(cls._providers.keys())}")
        
        llm_class = cls._providers[provider]
        provider_config = config.get("llm_providers", {}).get(provider, {})
        
        if not provider_config.get("enabled", True):
            raise ValueError(f"LLM provider {provider} is not enabled in configuration")
        
        return llm_class(provider_config)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available LLM providers"""
        return list(cls._providers.keys())







