"""
AUREN Production Settings Configuration
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class AURENSettings(BaseSettings):
    """Production-ready settings for AUREN system"""
    
    # Memory System Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    database_url: str = Field(
        default="postgresql://auren_user:auren_secure_password_change_me@localhost:5432/auren",
        env="DATABASE_URL"
    )
    chromadb_host: str = Field(default="localhost", env="CHROMADB_HOST")
    chromadb_port: int = Field(default=8000, env="CHROMADB_PORT")
    chromadb_path: str = Field(
        default="/Users/Jason/Downloads/CrewAI-Studio-main/data/chromadb",
        env="CHROMADB_PATH"
    )
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # WebSocket Configuration
    websocket_host: str = Field(default="0.0.0.0", env="WEBSOCKET_HOST")
    websocket_port: int = Field(default=8765, env="WEBSOCKET_PORT")
    
    # FastAPI Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    
    # Dashboard Configuration
    dashboard_port: int = Field(default=3001, env="DASHBOARD_PORT")
    
    # Monitoring Configuration
    prometheus_url: str = Field(default="http://localhost:9090", env="PROMETHEUS_URL")
    grafana_url: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    
    # Agent Configuration
    agent_memory_namespace: str = Field(default="auren_agents", env="AGENT_MEMORY_NAMESPACE")
    agent_memory_ttl_seconds: int = Field(default=86400, env="AGENT_MEMORY_TTL_SECONDS")  # 24 hours
    agent_memory_max_items: int = Field(default=10000, env="AGENT_MEMORY_MAX_ITEMS")
    
    # Performance Settings
    redis_max_memory: str = Field(default="2gb", env="REDIS_MAX_MEMORY")
    postgres_max_connections: int = Field(default=100, env="POSTGRES_MAX_CONNECTIONS")
    chromadb_batch_size: int = Field(default=1000, env="CHROMADB_BATCH_SIZE")
    
    # Security Settings
    jwt_secret_key: str = Field(
        default="your_jwt_secret_key_here_change_in_production",
        env="JWT_SECRET_KEY"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3001", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # Feature Flags
    enable_htm_anomaly_detection: bool = Field(default=True, env="ENABLE_HTM_ANOMALY_DETECTION")
    enable_memory_compression: bool = Field(default=True, env="ENABLE_MEMORY_COMPRESSION")
    enable_agent_memory_control: bool = Field(default=True, env="ENABLE_AGENT_MEMORY_CONTROL")
    enable_cross_user_patterns: bool = Field(default=False, env="ENABLE_CROSS_USER_PATTERNS")
    
    # HTM Configuration (from Compass research)
    htm_columns: int = Field(default=4096, env="HTM_COLUMNS")
    htm_cells_per_column: int = Field(default=16, env="HTM_CELLS_PER_COLUMN")
    htm_activation_threshold: int = Field(default=8, env="HTM_ACTIVATION_THRESHOLD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = AURENSettings()


def get_docker_internal_url(service: str, port: int) -> str:
    """Get Docker internal URL for service communication"""
    if os.getenv("DOCKER_ENV", "false").lower() == "true":
        return f"http://{service}:{port}"
    return f"http://localhost:{port}" 