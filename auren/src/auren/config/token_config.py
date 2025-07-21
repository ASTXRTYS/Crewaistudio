"""
Token tracking configuration and constants
"""

# Model pricing per 1K tokens (in USD)
MODEL_PRICING = {
    # OpenAI
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    
    # Anthropic
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    
    # Self-hosted (CoreWeave)
    "llama-3.1-70b": {"prompt": 0.00266, "completion": 0.00354},
    "llama-3.1-8b": {"prompt": 0.00018, "completion": 0.00018},
}

# Daily limits by user tier (in USD)
USER_TIERS = {
    "free": 1.0,
    "beta": 10.0,
    "premium": 50.0,
    "enterprise": 500.0,
}

# Alert thresholds
BUDGET_WARNING_THRESHOLD = 0.8  # Warn at 80% usage
BUDGET_CRITICAL_THRESHOLD = 0.95  # Critical at 95% usage

# Redis configuration
REDIS_CONFIG = {
    "token_ttl": 86400,  # 24 hours for individual records
    "daily_stats_ttl": 172800,  # 48 hours for daily aggregates
    "conversation_ttl": 7200,  # 2 hours for conversation context
}
