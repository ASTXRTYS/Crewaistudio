"""
Monitoring models for AUREN AI Gateway.

Provides data models for tracking usage, costs, and performance metrics.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TokenUsageRequest(BaseModel):
    """Request to track token usage."""
    model_config = ConfigDict(extra="allow")
    
    user_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserStats(BaseModel):
    """User statistics for token usage."""
    model_config = ConfigDict(extra="allow")
    
    user_id: str
    daily_usage: Dict[str, float] = Field(default_factory=dict)
    monthly_usage: Dict[str, float] = Field(default_factory=dict)
    total_usage: float = 0.0
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class BudgetAlert(BaseModel):
    """Budget alert configuration."""
    model_config = ConfigDict(extra="allow")
    
    user_id: str
    alert_type: str = Field(..., pattern="^(warning|critical|exceeded)$")
    threshold: float
    current_usage: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = False


class PerformanceMetric(BaseModel):
    """Performance metrics for model usage."""
    model_config = ConfigDict(extra="allow")
    
    model: str
    provider: str
    response_time: float
    tokens_per_second: float
    success_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostBreakdown(BaseModel):
    """Detailed cost breakdown for usage."""
    model_config = ConfigDict(extra="allow")
    
    user_id: str
    model: str
    prompt_cost: float
    completion_cost: float
    total_cost: float
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsagePattern(BaseModel):
    """Usage patterns and trends."""
    model_config = ConfigDict(extra="allow")
    
    user_id: str
    period: str  # "daily", "weekly", "monthly"
    models_used: List[str]
    total_tokens: int
    total_cost: float
    average_response_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheckResult(BaseModel):
    """Health check result for providers."""
    model_config = ConfigDict(extra="allow")
    
    provider: str
    healthy: bool
    response_time: float
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CircuitBreakerStats(BaseModel):
    """Circuit breaker statistics."""
    model_config = ConfigDict(extra="allow")
    
    name: str
    state: str
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime] = None
    failure_reasons: Dict[str, int] = Field(default_factory=dict)
    stability_score: float = 1.0
