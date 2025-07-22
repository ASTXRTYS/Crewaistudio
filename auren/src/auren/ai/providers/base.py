"""
Base interface for LLM providers in the AUREN AI Gateway.
This abstract base class ensures all providers implement the required methods
for seamless integration with the gateway's routing logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import asyncio


@dataclass
class LLMResponse:
    """
    Standardized response format from any LLM provider.
    This ensures consistent handling across different providers.
    """
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens
            },
            "finish_reason": self.finish_reason,
            "metadata": self.metadata or {}
        }


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All providers must implement these methods to ensure compatibility
    with the AI Gateway's routing and monitoring systems.
    """
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        
    @abstractmethod
    async def complete(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The input prompt to complete
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens to generate (None = model default)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with completion and token usage information
        """
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion for the given prompt.
        
        Yields chunks of text as they become available.
        Final yield should be a LLMResponse object with complete metadata.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and ready to serve requests.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        pass
