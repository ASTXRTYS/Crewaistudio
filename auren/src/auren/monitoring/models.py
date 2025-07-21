"""
Pydantic models for token tracking data validation
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class TokenUsageRequest(BaseModel):
    """Request model for tracking token usage"""
    user_id: str = Field(..., description="User identifier")
    agent_id: str = Field(..., description="Agent identifier")
    task_id: str = Field(..., description="Task identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    model: str = Field(..., description="LLM model name")
    prompt_tokens: int = Field(..., ge=0, description="Number of prompt tokens")
    completion_tokens: int = Field(..., ge=0, description="Number of completion tokens")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class UserStats(BaseModel):
    """User token usage statistics"""
    user_id: str
    today: Dict[str, float] = Field(..., description="Today's usage summary")
    daily_breakdown: list = Field(..., description="Daily usage history")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "today": {
                    "spent": 2.45,
                    "limit": 10.0,
                    "remaining": 7.55,
                    "percentage": 24.5,
                },
                "daily_breakdown": [
                    {
                        "date": "2024-01-15",
                        "total_cost": 2.45,
                        "total_tokens": 15234,
                        "request_count": 42,
                    }
                ],
            }
        }


class BudgetAlert(BaseModel):
    """Budget alert notification"""
    user_id: str
    alert_type: str = Field(..., regex="^(warning|critical|exceeded)$")
    current_usage: float
    limit: float
    percentage: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
