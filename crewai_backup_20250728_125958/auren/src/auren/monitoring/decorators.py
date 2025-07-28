"""
Token tracking decorators for easy integration with CrewAI agents
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, Dict
import inspect
from collections import defaultdict
from threading import Lock

from .token_tracker import TokenTracker, BudgetExceededException
from .tokenizer_service import TokenizerService

# Global instances (initialized on first use)
_token_tracker: Optional[TokenTracker] = None
_tokenizer_service: Optional[TokenizerService] = None
_rate_limiter = defaultdict(lambda: {"count": 0, "window_start": time.time()})
_rate_limit_lock = Lock()


class RateLimitExceededException(Exception):
    """Raised when rate limit is exceeded"""
    pass


def get_token_tracker() -> TokenTracker:
    """Get or create global token tracker instance"""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker


def get_tokenizer_service() -> TokenizerService:
    """Get or create global tokenizer service"""
    global _tokenizer_service
    if _tokenizer_service is None:
        _tokenizer_service = TokenizerService()
    return _tokenizer_service


def track_tokens(
    model: Optional[str] = None,
    agent_id: Optional[str] = None,
    extract_metadata: bool = True,
    rate_limit: int = 100,  # requests per minute
    rate_limit_window: int = 60,  # seconds
):
    """
    Decorator to track token usage for any LLM call
    
    Args:
        model: Model name (can be overridden by function)
        agent_id: Agent identifier
        extract_metadata: Whether to extract context from function args
    
    Usage:
        @track_tokens(model="gpt-4", agent_id="neuroscientist")
        async def generate_response(prompt: str) -> str:
            # Your LLM call here
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Extract context from function arguments
            context = _extract_context(func, args, kwargs, agent_id)
            
            # Check rate limit
            if rate_limit > 0:
                with _rate_limit_lock:
                    rate_key = f"{context['user_id']}:{agent_id or 'default'}"
                    limiter = _rate_limiter[rate_key]
                    
                    # Reset window if expired
                    if time.time() - limiter["window_start"] > rate_limit_window:
                        limiter["count"] = 0
                        limiter["window_start"] = time.time()
                    
                    # Check limit
                    if limiter["count"] >= rate_limit:
                        raise RateLimitExceededException(
                            f"Rate limit exceeded: {rate_limit} requests per {rate_limit_window}s"
                        )
                    
                    limiter["count"] += 1
            
            # Get model from kwargs or use default
            actual_model = kwargs.get("model", model) or "gpt-3.5-turbo"
            
            # Get prompt for token counting
            prompt = _extract_prompt(args, kwargs)
            
            # Count prompt tokens
            tokenizer = get_tokenizer_service()
            prompt_tokens = tokenizer.count_tokens(actual_model, prompt) if prompt else 0
            
            try:
                # Execute the actual function
                result = await func(*args, **kwargs)
                
                # Count completion tokens
                completion_tokens = tokenizer.count_tokens(actual_model, str(result))
                
                # Track usage
                tracker = get_token_tracker()
                await tracker.track_usage(
                    user_id=context["user_id"],
                    agent_id=context["agent_id"],
                    task_id=context["task_id"],
                    conversation_id=context["conversation_id"],
                    model=actual_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    metadata={
                        "function": func.__name__,
                        "duration_ms": int((time.time() - start_time) * 1000),
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                # Still track failed attempts
                tracker = get_token_tracker()
                await tracker.track_usage(
                    user_id=context["user_id"],
                    agent_id=context["agent_id"],
                    task_id=context["task_id"],
                    conversation_id=context["conversation_id"],
                    model=actual_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    metadata={
                        "function": func.__name__,
                        "duration_ms": int((time.time() - start_time) * 1000),
                        "success": False,
                        "error": str(e)
                    }
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _extract_context(func: Callable, args: tuple, kwargs: dict, default_agent_id: str) -> Dict[str, str]:
    """Extract tracking context from function arguments"""
    context = {
        "user_id": "unknown",
        "agent_id": default_agent_id or "unknown",
        "task_id": "unknown",
        "conversation_id": "unknown"
    }
    
    # Try to extract from kwargs first
    context["user_id"] = kwargs.get("user_id", context["user_id"])
    context["task_id"] = kwargs.get("task_id", context["task_id"])
    context["conversation_id"] = kwargs.get("conversation_id", context["conversation_id"])
    
    # For CrewAI integration: check if first arg is self with agent info
    if args and hasattr(args[0], "__class__"):
        obj = args[0]
        if hasattr(obj, "role"):  # CrewAI agent
            context["agent_id"] = getattr(obj, "role", context["agent_id"])
        if hasattr(obj, "id"):
            context["agent_id"] = getattr(obj, "id", context["agent_id"])
    
    return context


def _extract_prompt(args: tuple, kwargs: dict) -> Optional[str]:
    """Extract prompt text from function arguments"""
    # Common parameter names for prompts
    prompt_params = ["prompt", "message", "messages", "text", "query", "question"]
    
    # Check kwargs
    for param in prompt_params:
        if param in kwargs:
            value = kwargs[param]
            if isinstance(value, str):
                return value
            elif isinstance(value, list) and value:  # For chat messages
                # Extract text from message list
                texts = []
                for msg in value:
                    if isinstance(msg, dict) and "content" in msg:
                        texts.append(msg["content"])
                    elif isinstance(msg, str):
                        texts.append(msg)
                return "\n".join(texts)
    
    # Check positional args (usually first non-self arg)
    start_idx = 1 if args and hasattr(args[0], "__class__") else 0
    if len(args) > start_idx and isinstance(args[start_idx], str):
        return args[start_idx]
    
    return None
