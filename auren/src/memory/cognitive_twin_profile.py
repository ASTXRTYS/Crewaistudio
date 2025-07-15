"""
Cognitive Twin Profile - The foundation of AUREN's long-term memory.
This tracks biological optimization patterns over months and years.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
import json
import asyncpg
import asyncio
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class BiometricType(Enum):
    """Types of biometric measurements we track."""
    DEXA = "dexa"
    BLOODWORK = "bloodwork"
    MEASUREMENTS = "measurements"
    WEIGHT = "weight"
    PHOTO = "photo"
    ENERGY = "energy"
    SLEEP = "sleep"
    PTOSIS = "ptosis"
    INFLAMMATION = "inflammation"

@dataclass
class BiometricEntry:
    """Represents a single biometric measurement."""
    user_id: str
    timestamp: datetime
    measurement_type: BiometricType
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "measurement_type": self.measurement_type.value,
            "data": self.data,
            "metadata": self.metadata
        }

@dataclass
class Milestone:
    """Represents a significant achievement or event."""
    user_id: str
    timestamp: datetime
    category: str
    title: str
    description: str
    impact_metrics: Dict[str, Any]
    tags: List[str] = field(default_factory=list)

class CognitiveTwinProfile:
    """
    The persistent profile that makes AUREN truly know the user.
    This is not a 30-day chatbot - this is months and years of optimization data.
    """
    
    def __init__(self, user_id: str, db_pool: asyncpg.Pool):
        self.user_id = user_id
        self.db_pool = db_pool
        self._cache = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize or load existing profile from database."""
        async with self.db_pool.acquire() as conn:
            # Check if user exists
            user_data = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                self.user_id
            )
            
            if not user_data:
                # Create new profile
                await conn.execute("""
                    INSERT INTO user_profiles (user_id, profile_data)
                    VALUES ($1, $2)
                """, self.user_id, json.dumps({
                    "created_at": datetime.now().isoformat(),
                    "initial_state": "new_user"
                }))
                self._cache = {"profile_data": {"initial_state": "new_user"}}
            else:
                # Load existing profile
                self._cache = {
                    "profile_data": json.loads(user_data['profile_data']),
                    "preferences": json.loads(user_data['preference_evolution']),
                    "optimization_history": json.loads(user_data['optimization_history'])
                }
        
        self._initialized = True
        logger.info(f"Initialized CognitiveTwinProfile for user: {self.user_id}")
    
    async def add_biometric_entry(self, entry: BiometricEntry) -> None:
        """
        Add a biometric measurement to the timeline.
        This is how AUREN tracks transformation over months/years.
        """
        if not self._initialized:
            await self.initialize()
            
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO biometric_timeline 
                (user_id, timestamp, measurement_type, data, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """, entry.user_id, entry.timestamp, entry.measurement_type.value,
                json.dumps(entry.data), json.dumps(entry.metadata))
        
        # Update cache with latest entry
        if 'latest_biometrics' not in self._cache:
            self._cache['latest_biometrics'] = {}
        self._cache['latest_biometrics'][entry.measurement_type.value] = entry.to_dict()
        
        logger.info(f"Added {entry.measurement_type.value} entry for {self.user_id}")
    
    async def get_biometric_history(
        self,
        measurement_type: Optional[BiometricType] = None,
        days_back: int = 30,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve biometric history with intelligent filtering.
        This enables pattern recognition over extended timeframes.
        """
        query = """
            SELECT * FROM biometric_timeline 
            WHERE user_id = $1 
            AND timestamp >= $2
        """
        params = [self.user_id, datetime.now() - timedelta(days=days_back)]
        
        if measurement_type:
            query += " AND measurement_type = $3"
            params.append(measurement_type.value)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        return [dict(row) for row in rows]
    
    async def track_milestone(
        self,
        category: str,
        title: str,
        description: str,
        impact_metrics: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Record significant achievements or events.
        These become part of the user's permanent optimization story.
        """
        milestone = Milestone(
            user_id=self.user_id,
            timestamp=datetime.now(),
            category=category,
            title=title,
            description=description,
            impact_metrics=impact_metrics,
            tags=tags or []
        )
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO milestones 
                (user_id, timestamp, category, title, description, impact_metrics, tags)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, milestone.user_id, milestone.timestamp, milestone.category,
                milestone.title, milestone.description, 
                json.dumps(milestone.impact_metrics), milestone.tags)
        
        # Update optimization history in cache
        if 'optimization_history' not in self._cache:
            self._cache['optimization_history'] = []
        
        self._cache['optimization_history'].append({
            "timestamp": milestone.timestamp.isoformat(),
            "type": "milestone",
            "category": milestone.category,
            "title": milestone.title,
            "impact": milestone.impact_metrics
        })
        
        # Persist to database
        await self._persist_optimization_history()
        
        logger.info(f"Tracked milestone '{title}' for {self.user_id}")
    
    async def track_preference_evolution(
        self,
        preference_type: str,
        preference_data: Dict[str, Any]
    ) -> None:
        """
        Track how user preferences evolve over time.
        This helps AUREN adapt communication and recommendations.
        """
        if 'preferences' not in self._cache:
            self._cache['preferences'] = {}
        
        if preference_type not in self._cache['preferences']:
            self._cache['preferences'][preference_type] = []
        
        self._cache['preferences'][preference_type].append({
            "timestamp": datetime.now().isoformat(),
            "data": preference_data
        })
        
        # Keep only last 10 entries per preference type to prevent bloat
        self._cache['preferences'][preference_type] = \
            self._cache['preferences'][preference_type][-10:]
        
        await self._persist_preferences()
    
    async def get_pattern_insights(
        self,
        pattern_type: str,
        timeframe_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze patterns in user data over extended timeframes.
        This is where the magic happens - discovering what works for THIS user.
        """
        start_date = datetime.now() - timedelta(days=timeframe_days)
        
        insights = {
            "pattern_type": pattern_type,
            "timeframe_days": timeframe_days,
            "patterns_found": []
        }
        
        if pattern_type == "weight_loss":
            # Analyze weight progression
            weight_history = await self.get_biometric_history(
                measurement_type=BiometricType.WEIGHT,
                days_back=timeframe_days
            )
            
            if len(weight_history) >= 2:
                start_weight = weight_history[-1]['data'].get('weight')
                current_weight = weight_history[0]['data'].get('weight')
                
                if start_weight and current_weight:
                    total_loss = start_weight - current_weight
                    rate_per_week = (total_loss / timeframe_days) * 7
                    
                    insights["patterns_found"].append({
                        "pattern": "weight_loss_rate",
                        "description": f"Average weight loss of {rate_per_week:.2f} lbs/week",
                        "confidence": 0.8 if len(weight_history) > 10 else 0.5
                    })
        
        elif pattern_type == "energy_optimization":
            # Analyze energy patterns
            energy_history = await self.get_biometric_history(
                measurement_type=BiometricType.ENERGY,
                days_back=timeframe_days
            )
            
            # Find patterns in energy levels
            morning_energy = [e for e in energy_history 
                            if datetime.fromisoformat(e['timestamp']).hour < 12]
            
            if morning_energy:
                avg_morning = sum(e['data'].get('level', 5) for e in morning_energy) / len(morning_energy)
                insights["patterns_found"].append({
                    "pattern": "morning_energy",
                    "description": f"Average morning energy: {avg_morning:.1f}/10",
                    "confidence": min(0.9, len(morning_energy) / 30)  # More data = higher confidence
                })
        
        return insights
    
    async def _persist_preferences(self):
        """Persist preference evolution to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_profiles 
                SET preference_evolution = $1, updated_at = $2
                WHERE user_id = $3
            """, json.dumps(self._cache.get('preferences', {})), 
                datetime.now(), self.user_id)
    
    async def _persist_optimization_history(self):
        """Persist optimization history to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_profiles 
                SET optimization_history = $1, updated_at = $2
                WHERE user_id = $3
            """, json.dumps(self._cache.get('optimization_history', [])), 
                datetime.now(), self.user_id)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the user's profile.
        Used by AUREN to quickly understand the user's journey.
        """
        return {
            "user_id": self.user_id,
            "profile_created": self._cache.get("profile_data", {}).get("created_at"),
            "total_milestones": len(self._cache.get("optimization_history", [])),
            "latest_biometrics": self._cache.get("latest_biometrics", {}),
            "preference_categories": list(self._cache.get("preferences", {}).keys())
        }
