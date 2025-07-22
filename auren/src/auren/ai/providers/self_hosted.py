"""
Self-hosted LLM provider implementation for AUREN AI Gateway.
This provider connects to vLLM or similar OpenAI-compatible endpoints
running on CoreWeave or other GPU infrastructure.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, AsyncGenerator, Dict, Any
import json

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class SelfHostedProvider(BaseLLMProvider):
    """
    Provider for self-hosted models using vLLM or similar servers.
    
    Designed to work with OpenAI-compatible endpoints, making it easy
    to switch between commercial and self-hosted models. Optimized for
    high-throughput, low-latency inference on dedicated GPU infrastructure.
    """
    
    def __init__(
        self, 
        model_name: str, 
        endpoint_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        **kwargs
    ):
        super().__init__(model_name, **kwargs)
        self.endpoint_url = endpoint_url.rstrip('/')
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # Create session with connection pooling for performance
        self.session = None
        
    async def _ensure_session(self):
        """Lazily create aiohttp session for connection pooling."""
        if self.session is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(
                    limit=100,  # Connection pool size
                    ttl_dns_cache=300  # DNS cache for 5 minutes
                )
            )
            
    async def complete(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion from self-hosted model.
        
        Uses the OpenAI-compatible /v1/completions endpoint standard
        supported by vLLM, TGI, and other inference servers.
        """
        await self._ensure_session()
        
        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        # Add any additional kwargs (like stop sequences)
        payload.update(kwargs)
        
        try:
            async with self.session.post(
                f"{self.endpoint_url}/v1/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Parse response in OpenAI format
                choice = data["choices"][0]
                usage = data["usage"]
                
                return LLMResponse(
                    content=choice["message"]["content"],
                    model=self.model_name,
                    prompt_tokens=usage["prompt_tokens"],
                    completion_tokens=usage["completion_tokens"],
                    total_tokens=usage["total_tokens"],
                    finish_reason=choice.get("finish_reason", "stop"),
                    metadata={
                        "provider": "self_hosted",
                        "endpoint": self.endpoint_url,
                        "model_id": data.get("model", self.model_name)
                    }
                )
                
        except aiohttp.ClientError as e:
            logger.error(f"Self-hosted API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling self-hosted model: {e}")
            raise
            
    async def stream_complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion from self-hosted model using SSE.
        
        Implements Server-Sent Events parsing for streaming responses,
        accumulating token counts for final usage reporting.
        """
        await self._ensure_session()
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        payload.update(kwargs)
        
        content_chunks = []
        prompt_tokens = 0
        completion_tokens = 0
        
        try:
            async with self.session.post(
                f"{self.endpoint_url}/v1/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                # Parse SSE stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_str)
                            choice = data["choices"][0]
                            
                            # Extract content chunk
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                content_chunks.append(content)
                                yield content
                                
                            # Track token usage if provided
                            if "usage" in data:
                                prompt_tokens = data["usage"].get("prompt_tokens", 0)
                                completion_tokens = data["usage"].get("completion_tokens", 0)
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE data: {data_str}")
                            
                # Yield final response with usage data
                full_content = "".join(content_chunks)
                yield LLMResponse(
                    content=full_content,
                    model=self.model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    metadata={
                        "provider": "self_hosted",
                        "endpoint": self.endpoint_url,
                        "streamed": True
                    }
                )
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
            
    async def health_check(self) -> bool:
        """
        Check if the self-hosted endpoint is healthy.
        
        Most vLLM deployments expose a /health endpoint.
        Falls back to checking /v1/models if health endpoint unavailable.
        """
        await self._ensure_session()
        
        # Try health endpoint first
        try:
            async with self.session.get(f"{self.endpoint_url}/health") as response:
                return response.status == 200
        except:
            # Fallback to models endpoint
            try:
                async with self.session.get(f"{self.endpoint_url}/v1/models") as response:
                    return response.status == 200
            except Exception as e:
                logger.error(f"Health check failed for {self.endpoint_url}: {e}")
                return False
                
    @property
    def supports_streaming(self) -> bool:
        """Self-hosted vLLM servers support streaming."""
        return True
        
    async def close(self):
        """Clean up the aiohttp session."""
        if self.session:
            await self.session.close()
