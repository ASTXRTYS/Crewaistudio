"""Production configuration with security enhancements."""

from pydantic_settings import BaseSettings
from typing import Optional, List, Dict
import secrets

class ProductionConfig(BaseSettings):
    """Production environment configuration with security."""
    
    # API Configuration - bind to localhost in production, use reverse proxy
    api_host: str = "127.0.0.1"  # Changed from 0.0.0.0
    api_port: int = 8000
    api_workers: int = 4
    
    # Add trusted proxy settings for production
    trusted_hosts: List[str] = ["auren.yourdomain.com", "localhost"]
    behind_proxy: bool = True
    proxy_headers: Dict[str, str] = {
        "x-forwarded-for": "X-Forwarded-For",
        "x-forwarded-proto": "X-Forwarded-Proto",
        "x-forwarded-host": "X-Forwarded-Host"
    }
    
    # Security
    jwt_secret: str = secrets.token_urlsafe(32)  # Generate secure default
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    
    # CORS settings
    cors_origins: List[str] = ["https://auren.yourdomain.com"]
    cors_allow_credentials: bool = True
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    class Config:
        env_file = ".env.production"
        case_sensitive = False
