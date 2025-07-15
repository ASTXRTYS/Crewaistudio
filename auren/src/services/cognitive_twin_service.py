"""
Cognitive Twin Service - Clean API layer between AUREN and CognitiveTwinProfile.
Handles natural language extraction, data validation, and user-friendly responses.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re
from ..memory.cognitive_twin_profile import CognitiveTwinProfile, BiometricEntry, BiometricType

logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class WeightRequest(BaseModel):
    """Request model for weight tracking."""
    weight: float = Field(..., gt=0, description="Weight value")
    unit: str = Field(default="lbs", description="Weight unit (lbs, kg)")
    
    @validator('unit')
    def validate_unit(cls, v):
        if v.lower() not in ['lbs', 'kg']:
            raise ValueError('Unit must be "lbs" or "kg"')
        return v.lower()

class EnergyRequest(BaseModel):
    """Request model for energy tracking."""
    level: int = Field(..., ge=1, le=10, description="Energy level 1-10")
    time_of_day: Optional[str] = Field(None, description="Time context (morning, afternoon, evening)")

class MilestoneRequest(BaseModel):
    """Request model for milestone tracking."""
    category: str = Field(..., description="Milestone category")
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Milestone description")
    impact_metrics: Dict[str, Any] = Field(default_factory=dict)

class WeightResponse(BaseModel):
    """Response model for weight tracking."""
    success: bool
    message: str
    weight_change: Optional[float] = None
    days_tracked: Optional[int] = None
    average_rate: Optional[float] = None

class InsightsResponse(BaseModel):
    """Response model for pattern insights."""
    success: bool
    insights: Dict[str, Any]
    message: str

class CognitiveTwinService:
    """
    Service layer that provides clean APIs for AUREN to interact with CognitiveTwinProfile.
    Handles natural language extraction, data validation, and user-friendly responses.
    """
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._profile_cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes
    
    async def _get_or_create_profile(self, user_id: str) -> CognitiveTwinProfile:
        """Get existing profile or create new one."""
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]
        
        profile = CognitiveTwinProfile(user_id, self.db_pool)
        await profile.initialize()
        self._profile_cache[user_id] = profile
        return profile
    
    async def track_weight(self, user_id: str, weight: float, unit: str = "lbs") -> WeightResponse:
        """Track weight with natural language response."""
        try:
            profile = await self._get_or_create_profile(user_id)
            
            # Create biometric entry
            entry = BiometricEntry(
                user_id=user_id,
                timestamp=datetime.now(),
                measurement_type=BiometricType.WEIGHT,
                data={"weight": weight, "unit": unit}
            )
            
            await profile.add_biometric_entry(entry)
            
            # Get insights for response
            insights = await profile.get_pattern_insights("weight_loss", timeframe_days=30)
            
            # Build response
            message = f"Got it! I've recorded your weight as {weight} {unit}."
            
            # Add insights if available
            if insights.get("patterns_found"):
                for pattern in insights["patterns_found"]:
                    if pattern["pattern"] == "weight_loss_rate":
                        message += f" {pattern['description']}"
            
            return WeightResponse(
                success=True,
                message=message,
                weight_change=insights.get("total_change"),
                days_tracked=insights.get("days_tracked"),
                average_rate=insights.get("average_rate")
            )
            
        except Exception as e:
            logger.error(f"Error tracking weight for user {user_id}: {e}")
            return WeightResponse(
                success=False,
                message="I'm having trouble remembering that right now, but I'll keep track of it for next time!"
            )
    
    async def track_energy(self, user_id: str, level: int, time_of_day: Optional[str] = None) -> Dict[str, Any]:
        """Track energy level with context."""
        try:
            profile = await self._get_or_create_profile(user_id)
            
            entry = BiometricEntry(
                user_id=user_id,
                timestamp=datetime.now(),
                measurement_type=BiometricType.ENERGY,
                data={
                    "level": level,
                    "time_of_day": time_of_day or "general"
                }
            )
            
            await profile.add_biometric_entry(entry)
            
            return {
                "success": True,
                "message": f"Noted your energy level as {level}/10. I'll track how this changes over time!"
            }
            
        except Exception as e:
            logger.error(f"Error tracking energy for user {user_id}: {e}")
            return {
                "success": False,
                "message": "I'm having trouble remembering that right now, but I'll keep track of it for next time!"
            }
    
    async def track_sleep(self, user_id: str, hours: float, quality: int = 5) -> Dict[str, Any]:
        """Track sleep duration and quality."""
        try:
            profile = await self._get_or_create_profile(user_id)
            
            entry = BiometricEntry(
                user_id=user_id,
                timestamp=datetime.now(),
                measurement_type=BiometricType.SLEEP,
                data={
                    "hours": hours,
                    "quality": quality  # 1-10 scale
                }
            )
            
            await profile.add_biometric_entry(entry)
            
            return {
                "success": True,
                "message": f"Recorded your sleep as {hours} hours with {quality}/10 quality. This will help me understand your patterns!"
            }
            
        except Exception as e:
            logger.error(f"Error tracking sleep for user {user_id}: {e}")
            return {
                "success": False,
                "message": "I'm having trouble remembering that right now, but I'll keep track of it for next time!"
            }
    
    async def track_milestone(self, user_id: str, category: str, title: str, 
                            description: str, impact_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Track significant achievements."""
        try:
            profile = await self._get_or_create_profile(user_id)
            
            await profile.track_milestone(
                category=category,
                title=title,
                description=description,
                impact_metrics=impact_metrics or {}
            )
            
            return {
                "success": True,
                "message": f"Congratulations! I've recorded your milestone: {title}"
            }
            
        except Exception as e:
            logger.error(f"Error tracking milestone for user {user_id}: {e}")
            return {
                "success": False,
                "message": "I'm having trouble remembering that right now, but I'll keep track of it for next time!"
            }
    
    async def get_weight_insights(self, user_id: str, days_back: int = 30) -> InsightsResponse:
        """Get weight loss insights for user."""
        try:
            profile = await self._get_or_create_profile(user_id)
            insights = await profile.get_pattern_insights("weight_loss", timeframe_days=days_back)
            
            if not insights.get("patterns_found"):
                message = "I don't have enough weight data yet to show patterns. Keep tracking and I'll find your trends!"
            else:
                patterns = [p["description"] for p in insights["patterns_found"]]
                message = "Here's what I've noticed about your weight: " + "; ".join(patterns)
            
            return InsightsResponse(
                success=True,
                insights=insights,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error getting weight insights for user {user_id}: {e}")
            return InsightsResponse(
                success=False,
                insights={},
                message="I'm having trouble accessing your weight data right now. Please try again later!"
            )
    
    async def get_energy_insights(self, user_id: str, days_back: int = 30) -> InsightsResponse:
        """Get energy pattern insights."""
        try:
            profile = await self._get_or_create_profile(user_id)
            insights = await profile.get_pattern_insights("energy_optimization", timeframe_days=days_back)
            
            if not insights.get("patterns_found"):
                message = "I need more energy data to find your patterns. Keep tracking your energy levels!"
            else:
                patterns = [p["description"] for p in insights["patterns_found"]]
                message = "Here's what I've noticed about your energy: " + "; ".join(patterns)
            
            return InsightsResponse(
                success=True,
                insights=insights,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error getting energy insights for user {user_id}: {e}")
            return InsightsResponse(
                success=False,
                insights={},
                message="I'm having trouble accessing your energy data right now. Please try again later!"
            )
    
    def extract_weight_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract weight data from natural language."""
        text = text.lower()
        
        # Common patterns
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)',
            r'(\d+(?:\.\d+)?)\s*(?:kg|kilos?)',
            r'weighs?\s+(\d+(?:\.\d+)?)',
            r'down\s+to\s+(\d+(?:\.\d+)?)',
            r'at\s+(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                weight = float(match.group(1))
                
                # Determine unit
                unit = "lbs"
                if "kg" in text or "kilo" in text:
                    unit = "kg"
                
                return {"weight": weight, "unit": unit}
        
        return None
    
    def extract_energy_from_text(self, text: str) -> Optional[int]:
        """Extract energy level from natural language."""
        text = text.lower()
        
        # Look for "X out of 10" or "X/10" patterns
        patterns = [
            r'(\d+)\s*(?:out\s+of\s+10|\/10)',
            r'energy\s+(?:is|at)\s+(\d+)',
            r'feeling\s+(?:a\s+)?(\d+)\s*\/\s*10'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                level = int(match.group(1))
                if 1 <= level <= 10:
                    return level
        
        # Look for descriptive terms
        energy_map = {
            "exhausted": 2, "tired": 3, "low": 3,
            "okay": 5, "fine": 5, "alright": 5,
            "good": 7, "great": 8, "amazing": 9, "fantastic": 10
        }
        
        for word, level in energy_map.items():
            if word in text:
                return level
        
        return None
    
    def extract_sleep_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract sleep data from natural language."""
        text = text.lower()
        
        # Hours patterns
        hour_patterns = [
            r'(\d+(?:\.\d+)?)\s*hours?\s+of?\s*sleep',
            r'slept\s+for?\s+(\d+(?:\.\d+)?)\s*hours?',
            r'got\s+(\d+(?:\.\d+)?)\s*hours?\s+sleep'
        ]
        
        for pattern in hour_patterns:
            match = re.search(pattern, text)
            if match:
                hours = float(match.group(1))
                return {"hours": hours, "quality": 5}  # Default quality
        
        return None
    
    async def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Get quick summary of user's data."""
        try:
            profile = await self._get_or_create_profile(user_id)
            return profile.get_summary()
        except Exception as e:
            logger.error(f"Error getting user summary for {user_id}: {e}")
            return {"error": "Unable to retrieve user summary"}
