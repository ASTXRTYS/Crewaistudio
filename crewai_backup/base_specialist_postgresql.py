"""
PostgreSQL-compatible Base Specialist
Provides the same interface as BaseSpecialist but uses PostgreSQL backend
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from asyncpg.pool import Pool

from .shared_types import (
    SpecialistDomain,
    SpecialistTraits,
    SpecialistGenesis,
    EvolutionRecord,
    ConsensusPosition,
    Hypothesis,
    HypothesisTracker
)
from .postgresql_memory_backend import PostgreSQLMemoryBackend

logger = logging.getLogger(__name__)

class BaseSpecialistPostgreSQL(ABC):
    """
    PostgreSQL-compatible base class for autonomous AI specialists.
    
    This class provides the same interface as BaseSpecialist but uses
    PostgreSQL for unlimited memory storage instead of JSON files.
    """
    
    def __init__(
        self,
        genesis: SpecialistGenesis,
        cognitive_profile: Any,
        db_pool: Pool,
        user_id: Optional[str] = None,
        override_agent: Optional[Any] = None
    ):
        """
        Initialize a specialist with PostgreSQL backend.
        
        Args:
            genesis: Birth configuration defining identity and mission
            cognitive_profile: Reference to user's cognitive twin profile
            db_pool: PostgreSQL connection pool
            user_id: User ID for user-specific memory isolation
            override_agent: Optional pre-configured CrewAI agent
        """
        self.identity = genesis.identity
        self.mission = genesis.mission
        self.expertise = genesis.expertise
        self.collaboration_philosophy = genesis.collaboration_philosophy
        self.traits = genesis.traits
        self.cognitive_profile = cognitive_profile
        self.user_id = user_id
        
        # PostgreSQL memory management
        self.memory_backend = PostgreSQLMemoryBackend(
            pool=db_pool,
            specialist_type=self.identity.lower().replace(" ", "_"),
            user_id=user_id
        )
        
        # Initialize memory backend
        asyncio.create_task(self.memory_backend.initialize())
        
        # Relationship tracking
        self.relationship_score = 0.5  # 0.0 to 1.0
        
        # Initialize hypotheses from genesis
        self.hypothesis_tracker = HypothesisTracker()
        for hypothesis in genesis.initial_hypotheses:
            self.hypothesis_tracker.add_hypothesis(hypothesis)
    
    @abstractmethod
    def get_domain(self) -> SpecialistDomain:
        """Return the specialist's domain of expertise."""
        pass
    
    @abstractmethod
    def get_specialist_tools(self) -> List[Any]:
        """Return tools specific to this specialist's domain."""
        pass
    
    @abstractmethod
    def _can_test_hypothesis(self, hypothesis: Hypothesis, data: Dict[str, Any]) -> bool:
        """Check if we have enough data to test this hypothesis."""
        pass
    
    @abstractmethod
    def _design_experiment(self, hypothesis: Hypothesis) -> str:
        """Design an experiment to test this hypothesis."""
        pass
    
    @abstractmethod
    def _get_experiment_metrics(self, hypothesis: Hypothesis) -> List[str]:
        """Get metrics to measure for this experiment."""
        pass
    
    async def add_memory(self, memory_type: str, content: Dict[str, Any], confidence: float = 0.5) -> int:
        """Add a new memory entry."""
        return await self.memory_backend.add_memory(memory_type, content, confidence)
    
    async def get_memories(self, memory_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve memories with filtering."""
        return await self.memory_backend.get_memories(memory_type=memory_type, limit=limit)
    
    async def add_hypothesis(self, hypothesis: str, initial_confidence: float) -> int:
        """Create a new hypothesis."""
        return await self.memory_backend.add_hypothesis(hypothesis, initial_confidence)
    
    async def update_hypothesis(self, hypothesis_id: int, test_result: Dict[str, Any], new_confidence: float):
        """Update hypothesis based on evidence."""
        await self.memory_backend.update_hypothesis(hypothesis_id, test_result, new_confidence)
    
    async def get_learning_history(self) -> Dict[str, Any]:
        """Get complete learning history."""
        return await self.memory_backend.get_learning_history()
    
    async def process_interaction(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an interaction with the user.
        
        This is the main async method for specialist interaction.
        """
        # Add interaction as memory
        await self.add_memory(
            memory_type="interaction",
            content={
                "message": message,
                "context": context,
                "response_type": "user_interaction"
            },
            confidence=0.8
        )
        
        # Check for testable hypotheses
        learning_history = await self.get_learning_history()
        hypotheses = learning_history.get('hypotheses', [])
        testable = [h for h in hypotheses if h['status'] == 'active'][:3]
        
        # Generate response based on domain expertise
        response = {
            "recommendation": f"As a {self.identity} specialist, I recommend...",
            "insights": [h['hypothesis_text'] for h in testable],
            "confidence": self.relationship_score,
            "next_steps": ["Continue monitoring", "Test hypotheses"]
        }
        
        return response
    
    async def form_hypothesis(self, observation: Dict[str, Any], confidence: float = 0.5) -> int:
        """
        Form a new hypothesis based on observations.
        
        This is how specialists develop theories about users.
        """
        hypothesis_text = await self._generate_hypothesis_text(observation)
        
        hypothesis_id = await self.add_hypothesis(hypothesis_text, confidence)
        
        # Store in memory for quick access
        await self.add_memory(
            memory_type='hypothesis',
            content={
                'hypothesis_id': hypothesis_id,
                'hypothesis': hypothesis_text,
                'observation': observation
            },
            confidence=confidence
        )
        
        return hypothesis_id
    
    async def _generate_hypothesis_text(self, observation: Dict[str, Any]) -> str:
        """Generate hypothesis text from observation."""
        # This would be implemented by concrete specialist classes
        return f"Based on observation: {observation}"
    
    # === CREWAI COMPATIBILITY METHODS ===
    
    def process_interaction_sync(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for CrewAI compatibility."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process_interaction(message, context))
    
    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute task in CrewAI-compatible format."""
        if context is None:
            context = {}
        
        result = self.process_interaction_sync(task_description, context)
        
        response_parts = []
        if 'recommendation' in result:
            response_parts.append(f"Recommendation: {result['recommendation']}")
        if 'insights' in result:
            response_parts.append(f"Key Insights: {', '.join(result['insights'])}")
        if 'confidence' in result:
            response_parts.append(f"Confidence Level: {result['confidence']:.0%}")
        
        return '\n'.join(response_parts)
