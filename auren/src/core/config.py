"""
Configuration management for AUREN.
Handles environment-based configuration with sensible defaults.
"""

import os
from typing import Optional
from pathlib import Path

def get_database_url() -> str:
    """
    Get database URL from environment with fallback to local development.
    
    Supports:
    - Local PostgreSQL: postgresql://localhost/auren
    - Cloud providers: postgresql://user:pass@host:port/db
    - SSL connections: postgresql://...?sslmode=require
    """
    # Primary: DATABASE_URL environment variable
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fallback: Construct from individual components
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "auren")
    user = os.getenv("DB_USER", "auren")
    password = os.getenv("DB_PASSWORD", "auren")
    
    # Handle password in URL
    if password:
        password = f":{password}"
    
    # Handle SSL mode
    ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
    ssl_param = f"?sslmode={ssl_mode}" if ssl_mode != "prefer" else ""
    
    return f"postgresql://{user}{password}@{host}:{port}/{database}{ssl_param}"

def get_config() -> dict:
    """
    Get complete configuration dictionary.
    """
    return {
        "database_url": get_database_url(),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "cache_ttl": int(os.getenv("CACHE_TTL", "300")),  # 5 minutes default
        "max_pool_size": int(os.getenv("MAX_POOL_SIZE", "10")),
        "min_pool_size": int(os.getenv("MIN_POOL_SIZE", "1")),
    }

# Environment validation
def validate_environment() -> None:
    """Validate required environment variables."""
    required_vars = ["DATABASE_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        # Allow fallback for local development
        if "localhost" not in get_database_url():
            raise ValueError(
                f"Missing required environment variables: {missing}. "
                f"Set DATABASE_URL or individual DB_* variables."
            )
