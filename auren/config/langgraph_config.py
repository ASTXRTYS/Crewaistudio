"""
LangGraph Configuration with LangSmith Tracing & Enhanced Checkpointing
Created: 2025-01-29
Purpose: Production-ready configuration for observability and persistence
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langchain.cache import RedisCache
from langsmith import Client
import redis


@dataclass
class LangGraphConfig:
    """Central configuration for LangGraph components"""
    
    # LangSmith Configuration
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "auren-production"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    enable_tracing: bool = True
    
    # PostgreSQL Configuration
    postgres_url: str = ""
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 40
    
    # Redis Configuration
    redis_url: str = ""
    redis_cache_ttl: int = 3600  # 1 hour default
    redis_max_connections: int = 50
    
    # Checkpointing Configuration
    checkpoint_namespace: str = "auren"
    checkpoint_ttl_days: int = 90  # How long to keep checkpoints
    enable_checkpoint_compression: bool = True
    
    # Performance Configuration
    enable_caching: bool = True
    enable_async_checkpointing: bool = True
    batch_checkpoint_size: int = 10
    
    @classmethod
    def from_env(cls) -> "LangGraphConfig":
        """Load configuration from environment variables"""
        return cls(
            langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "auren-production"),
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            postgres_url=os.getenv("POSTGRES_URL", ""),
            redis_url=os.getenv("REDIS_URL", ""),
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
        )


class LangGraphRuntime:
    """Enhanced LangGraph runtime with tracing and checkpointing"""
    
    def __init__(self, config: Optional[LangGraphConfig] = None):
        self.config = config or LangGraphConfig.from_env()
        self._langsmith_client: Optional[Client] = None
        self._checkpointer: Optional[PostgresSaver] = None
        self._store: Optional[PostgresStore] = None
        self._cache: Optional[RedisCache] = None
        
    @property
    def langsmith_client(self) -> Optional[Client]:
        """Lazy-load LangSmith client"""
        if self._langsmith_client is None and self.config.langsmith_api_key:
            self._langsmith_client = Client(
                api_key=self.config.langsmith_api_key,
                api_url=self.config.langsmith_endpoint
            )
        return self._langsmith_client
    
    @property
    def checkpointer(self) -> PostgresSaver:
        """Get or create PostgreSQL checkpointer"""
        if self._checkpointer is None:
            self._checkpointer = PostgresSaver.from_conn_string(
                self.config.postgres_url,
                pool_size=self.config.postgres_pool_size,
                max_overflow=self.config.postgres_max_overflow
            )
        return self._checkpointer
    
    @property
    def store(self) -> PostgresStore:
        """Get or create PostgreSQL store for additional data"""
        if self._store is None:
            self._store = PostgresStore.from_conn_string(
                self.config.postgres_url
            )
        return self._store
    
    @property  
    def cache(self) -> Optional[RedisCache]:
        """Get or create Redis cache"""
        if self._cache is None and self.config.enable_caching:
            redis_client = redis.from_url(
                self.config.redis_url,
                max_connections=self.config.redis_max_connections
            )
            self._cache = RedisCache(redis_client)
        return self._cache
    
    def get_runnable_config(
        self, 
        thread_id: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> RunnableConfig:
        """
        Get runnable configuration with tracing and checkpointing
        
        Args:
            thread_id: Unique thread/session ID
            user_id: Optional user ID for tracing
            **kwargs: Additional configuration options
            
        Returns:
            RunnableConfig with all settings applied
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": self.config.checkpoint_namespace,
            }
        }
        
        # Add LangSmith tracing if enabled
        if self.config.enable_tracing and self.langsmith_client:
            config["callbacks"] = []
            config["metadata"] = {
                "user_id": user_id,
                "project": self.config.langsmith_project,
                **kwargs.get("metadata", {})
            }
            
            # Add tags for filtering in LangSmith
            config["tags"] = kwargs.get("tags", [])
            if user_id:
                config["tags"].append(f"user:{user_id}")
        
        # Add any additional config
        config.update(kwargs)
        
        return config
    
    async def cleanup_old_checkpoints(self, days: Optional[int] = None):
        """Clean up old checkpoints to manage storage"""
        days = days or self.config.checkpoint_ttl_days
        
        # This would be implemented based on your checkpoint schema
        # Example SQL: DELETE FROM checkpoints WHERE created_at < NOW() - INTERVAL '90 days'
        pass
    
    def create_graph_with_tracing(self, graph_builder):
        """
        Compile a graph with tracing and checkpointing enabled
        
        Args:
            graph_builder: StateGraph builder instance
            
        Returns:
            Compiled graph with all enhancements
        """
        # Add checkpointer
        compiled = graph_builder.compile(
            checkpointer=self.checkpointer,
            interrupt_before=[],  # Can add nodes to interrupt before
            interrupt_after=[],   # Can add nodes to interrupt after
        )
        
        # Wrap with cache if enabled
        if self.cache:
            # This would wrap the graph with caching logic
            # Implementation depends on specific caching needs
            pass
        
        return compiled
    
    @lru_cache(maxsize=128)
    def get_cached_config(self, cache_key: str) -> Dict[str, Any]:
        """Cache frequently used configurations"""
        # This can cache compiled graphs or configurations
        return {}


# Global runtime instance (singleton pattern)
_runtime: Optional[LangGraphRuntime] = None


def get_langgraph_runtime() -> LangGraphRuntime:
    """Get or create the global LangGraph runtime"""
    global _runtime
    if _runtime is None:
        _runtime = LangGraphRuntime()
    return _runtime


# Convenience functions
def create_traced_config(thread_id: str, **kwargs) -> RunnableConfig:
    """Create a traced configuration for a graph run"""
    runtime = get_langgraph_runtime()
    return runtime.get_runnable_config(thread_id, **kwargs)


def compile_with_tracing(graph_builder):
    """Compile a graph with all production features"""
    runtime = get_langgraph_runtime()
    return runtime.create_graph_with_tracing(graph_builder) 