"""
Multi-model tokenizer service for accurate token counting
"""

import tiktoken
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TokenizerService:
    """
    Centralized tokenizer service supporting multiple model families
    Uses tiktoken for OpenAI models, estimates for others
    """
    
    def __init__(self):
        self._encoders: Dict[str, tiktoken.Encoding] = {}
        self._model_mappings = {
            # OpenAI models
            "gpt-4": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-4o": "o200k_base",
            
            # Map other models to approximate tokenizers
            "claude-3-opus": "cl100k_base",  # Approximate
            "claude-3-sonnet": "cl100k_base",  # Approximate
            "llama-3.1-70b": "cl100k_base",  # Approximate
        }
    
    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get or create encoder for model"""
        encoding_name = self._model_mappings.get(model, "cl100k_base")
        
        if encoding_name not in self._encoders:
            try:
                self._encoders[encoding_name] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                logger.warning(f"Failed to load {encoding_name}, using cl100k_base: {e}")
                self._encoders[encoding_name] = tiktoken.get_encoding("cl100k_base")
        
        return self._encoders[encoding_name]
    
    def count_tokens(self, model: str, text: str) -> int:
        """
        Count tokens for given model and text
        
        Args:
            model: Model identifier
            text: Text to tokenize
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            encoder = self._get_encoder(model)
            tokens = encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4
    
    def truncate_to_tokens(self, model: str, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        if not text:
            return text
        
        try:
            encoder = self._get_encoder(model)
            tokens = encoder.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate and decode
            truncated_tokens = tokens[:max_tokens]
            return encoder.decode(truncated_tokens)
        except Exception as e:
            logger.error(f"Error truncating text: {e}")
            # Fallback: character-based truncation
            estimated_chars = max_tokens * 4
            return text[:estimated_chars]
