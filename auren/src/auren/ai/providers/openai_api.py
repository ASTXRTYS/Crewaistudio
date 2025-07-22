"""
OpenAI API provider implementation for the AUREN AI Gateway.
This serves as the fallback provider when self-hosted models are unavailable
or when budget constraints require cheaper alternatives.
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any
import openai
from openai import AsyncOpenAI

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider supporting GPT-3.5 and GPT-4 models.
    
    This provider handles:
    - Async API calls with proper error handling
    - Token counting and usage tracking
    - Streaming responses for real-time interaction
    - Automatic retry logic for transient failures
    """
    
    def __init__(self, model_name: str, api_key: str, **kwargs):
        super().__init__(model_name, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Map friendly names to OpenAI model IDs
        self.model_mapping = {
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4-turbo": "gpt-4-turbo-preview",
            "gpt-4": "gpt-4"
        }
        
        self.actual_model = self.model_mapping.get(model_name, model_name)
        
    async def complete(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion using OpenAI's API.
        
        Includes automatic retry logic for transient failures and
        proper error handling for rate limits and API errors.
        """
        try:
            # Build the messages format required by OpenAI
            messages = [{"role": "user", "content": prompt}]
            
            # Make the API call with retries
            for attempt in range(3):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.actual_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                    break
                except openai.RateLimitError as e:
                    if attempt < 2:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
                        
            # Extract the completion and usage information
            completion = response.choices[0].message.content
            usage = response.usage
            
            return LLMResponse(
                content=completion,
                model=self.model_name,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "provider": "openai",
                    "actual_model": self.actual_model,
                    "request_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
            
    async def stream_complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from OpenAI's API.
        
        Yields text chunks as they arrive, with a final yield
        containing the complete LLMResponse with usage data.
        """
        messages = [{"role": "user", "content": prompt}]
        
        stream = await self.client.chat.completions.create(
            model=self.actual_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
            **kwargs
        )
        
        content_chunks = []
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                content_chunks.append(content)
                yield content
            
            # Final chunk contains usage information
            if chunk.usage:
                full_content = "".join(content_chunks)
                yield LLMResponse(
                    content=full_content,
                    model=self.model_name,
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    metadata={
                        "provider": "openai",
                        "actual_model": self.actual_model,
                        "streamed": True
                    }
                )
                
    async def health_check(self) -> bool:
        """
        Check OpenAI API health by making a minimal API call.
        
        Uses a very short completion to minimize cost while verifying connectivity.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.actual_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
            
    @property
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming for all chat models."""
        return True
