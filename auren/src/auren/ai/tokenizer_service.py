"""
Token counting service for accurate cost estimation.

This service provides precise token counting using the same tokenizers
as the actual LLM providers, ensuring accurate cost predictions.
"""

import tiktoken
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenCount:
    """Result of token counting operation."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class TokenizerService:
    """
    Service for accurate token counting across different models.
    
    Uses the same tokenizers as the actual providers to ensure
    cost predictions match actual usage.
    """
    
    def __init__(self):
        """Initialize tokenizers for supported models."""
        self.encoders: Dict[str, tiktoken.Encoding] = {}
        self._initialize_encoders()
        
    def _initialize_encoders(self):
        """Initialize tokenizers for supported models."""
        # OpenAI models
        self.encoders["gpt-3.5-turbo"] = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.encoders["gpt-4-turbo"] = tiktoken.encoding_for_model("gpt-4-turbo")
        self.encoders["gpt-4"] = tiktoken.encoding_for_model("gpt-4")
        
        # Self-hosted models (use cl100k_base for Llama)
        self.encoders["llama-3.1-70b"] = tiktoken.get_encoding("cl100k_base")
        self.encoders["meditron-70b"] = tiktoken.get_encoding("cl100k_base")
        
    def count_tokens(self, model: str, text: str) -> int:
        """
        Count tokens for a given model and text.
        
        Args:
            model: Model name
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if model not in self.encoders:
            logger.warning(f"Unknown model {model}, using cl100k_base")
            encoder = tiktoken.get_encoding("cl100k_base")
        else:
            encoder = self.encoders[model]
            
        return len(encoder.encode(text))
    
    def estimate_completion_tokens(self, prompt_tokens: int, max_tokens: Optional[int] = None) -> int:
        """
        Estimate completion tokens based on prompt length and patterns.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            max_tokens: Maximum tokens allowed for completion
            
        Returns:
            Estimated completion tokens
        """
        if max_tokens:
            # If max_tokens is specified, use it as upper bound
            return min(max_tokens, int(prompt_tokens * 0.8))
        
        # Based on AUREN usage patterns:
        # - Simple queries: 30-50% of prompt length
        # - Complex analysis: 60-80% of prompt length
        # - Conversational: 40-60% of prompt length
        
        if prompt_tokens < 50:
            # Simple queries tend to have shorter completions
            estimated = int(prompt_tokens * 0.4)
        elif prompt_tokens < 200:
            # Medium complexity
            estimated = int(prompt_tokens * 0.6)
        else:
            # Complex queries
            estimated = int(prompt_tokens * 0.7)
            
        return max(10, estimated)  # Minimum 10 tokens
    
    def count_and_estimate(self, model: str, prompt: str, max_tokens: Optional[int] = None) -> TokenCount:
        """
        Count prompt tokens and estimate completion tokens.
        
        Args:
            model: Model name
            prompt: Prompt text
            max_tokens: Maximum tokens for completion
            
        Returns:
            TokenCount with accurate counts
        """
        prompt_tokens = self.count_tokens(model, prompt)
        completion_tokens = self.estimate_completion_tokens(prompt_tokens, max_tokens)
        
        return TokenCount(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
    
    def validate_model_support(self, model: str) -> bool:
        """Check if model is supported for token counting."""
        return model in self.encoders
    
    def get_supported_models(self) -> list[str]:
        """Get list of models with token counting support."""
        return list(self.encoders.keys())


# Global instance for convenience
tokenizer_service = TokenizerService()
