"""
BaseSpecialist - The foundation for autonomous AI specialists.

This module provides the base class for all AUREN specialists, implementing
the core functionality for autonomous, self-evolving AI colleagues that
maintain their own knowledge, hypotheses, and relationships over time.

Phase 2: Refactored to use internal engines for better modularity while
maintaining the unified specialist metaphor.
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import portalocker
import logging

from .shared_types import (
    SpecialistDomain,
    SpecialistTraits,
    SpecialistGenesis,
    EvolutionRecord,
    ConsensusPosition,
    Hypothesis,
    HypothesisTracker
)
from .engines import SpecialistCollaborationEngine, SpecialistMemoryEngine

logger = logging.getLogger(__name__)


class JSONFileMemoryBackend:
    """Thread-safe JSON file backend for specialist memory."""
    
    def __init__(self, memory_path: Path, retention_limit: int = 1000):
        self.memory_path = memory_path
        self.retention_limit = retention_limit
        self.memory_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, data: Dict[str, Any]) -> bool:
        """Save data to memory file with thread safety."""
        try:
            file_path = self.memory_path / "specialist_memory.json"
            with portalocker.Lock(str(file_path), 'w', timeout=5) as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return False
    
    def load(self) -> Optional[Dict[str, Any]]:
        """Load data from memory file with thread safety."""
        try:
            file_path = self.memory_path / "specialist_memory.json"
            if not file_path.exists():
                return None
            
            with portalocker.Lock(str(file_path), 'r', timeout=5) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return None


class BaseSpecialist(ABC):
    """
    Base class for autonomous AI specialists.
    
    Specialists are self-evolving AI entities that maintain their own
    knowledge, hypotheses, and relationships over time. They can
    collaborate with other specialists and learn from interactions.
    
    Phase 2: Refactored to use internal engines for better modularity.
    """
    
    def __init__(
        self,
        genesis: SpecialistGenesis,
        cognitive_profile: Any,
        memory_path: Path,
        memory_retention_limit: int = 1000,
        override_agent: Optional[Any] = None
    ):
        """
        Initialize a specialist with their genesis configuration.
        
        Args:
            genesis: Birth configuration defining identity and mission
            cognitive_profile: Reference to user's cognitive twin profile
            memory_path: Path to persistent memory storage
            memory_retention_limit: Maximum evolution records to retain
            override_agent: Optional pre-configured CrewAI agent (advanced use case)
                          Default None maintains self-birthing behavior
        """
        self.identity = genesis.identity
        self.mission = genesis.mission
        self.expertise = genesis.expertise
        self.collaboration_philosophy = genesis.collaboration_philosophy
        self.traits = genesis.traits
        self.cognitive_profile = cognitive_profile
        
        # Memory management
        self.memory_backend = JSONFileMemoryBackend(memory_path, memory_retention_limit)
        self.evolution_history: List[EvolutionRecord] = []
        self.hypothesis_tracker = HypothesisTracker()
        
        # Relationship tracking
        self.relationship_score = 0.5  # 0.0 to 1.0
        
        # Initialize internal engines for better modularity
        self._collaboration_engine = SpecialistCollaborationEngine(self)
        self._memory_engine = SpecialistMemoryEngine(
            self.memory_backend,
            memory_retention_limit
        )
        
        # Load existing memory or initialize
        self._load_memory()
        
        # Initialize hypotheses from genesis
        for hypothesis in genesis.initial_hypotheses:
            self.hypothesis_tracker.add_hypothesis(hypothesis)
    
    def _load_memory(self):
        """Load specialist memory from persistent storage."""
        memory_data = self.memory_backend.load()
        if memory_data:
            # Load evolution history
            self.evolution_history = [
                EvolutionRecord(
                    timestamp=datetime.fromisoformat(record['timestamp']),
                    interaction_type=record['interaction_type'],
                    learning=record['learning'],
                    confidence_delta=record['confidence_delta'],
                    relationship_impact=record.get('relationship_impact', 0.0)
                )
                for record in memory_data.get('evolution_history', [])
            ]
            
            # Load relationship score
            self.relationship_score = memory_data.get('relationship_score', 0.5)
            
            # Load hypotheses
            for h_data in memory_data.get('hypotheses', []):
                hypothesis = Hypothesis(
                    id=h_data['id'],
                    statement=h_data['statement'],
                    confidence=h_data['confidence'],
                    evidence_for=h_data.get('evidence_for', []),
                    evidence_against=h_data.get('evidence_against', []),
                    test_count=h_data.get('test_count', 0),
                    last_tested=datetime.fromisoformat(h_data['last_tested']) if h_data.get('last_tested') else None
                )
                self.hypothesis_tracker.hypotheses[hypothesis.id] = hypothesis
    
    def _save_memory(self):
        """Save specialist memory to persistent storage."""
        memory_data = {
            'evolution_history': [
                {
                    'timestamp': record.timestamp.isoformat(),
                    'interaction_type': record.interaction_type,
                    'learning': record.learning,
                    'confidence_delta': record.confidence_delta,
                    'relationship_impact': record.relationship_impact
                }
                for record in self.evolution_history
            ],
            'relationship_score': self.relationship_score,
            'hypotheses': [
                {
                    'id': h.id,
                    'statement': h.statement,
                    'confidence': h.confidence,
                    'evidence_for': h.evidence_for,
                    'evidence_against': h.evidence_against,
                    'test_count': h.test_count,
                    'last_tested': h.last_tested.isoformat() if h.last_tested else None
                }
                for h in self.hypothesis_tracker.hypotheses.values()
            ]
        }
        self.memory_backend.save(memory_data)
    
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
    
    async def process_interaction(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an interaction with the user.
        
        This is the main async method for specialist interaction.
        """
        # Record interaction using memory engine
        evolution = EvolutionRecord(
            timestamp=datetime.now(),
            interaction_type="user_interaction",
            learning=f"Processed: {message[:50]}...",
            confidence_delta=0.0
        )
        self._memory_engine.store_evolution(evolution, self.evolution_history)
        
        # Check for testable hypotheses
        testable = self.hypothesis_tracker.get_testable_hypotheses()
        
        # Generate response based on domain expertise
        response = {
            "recommendation": f"As a {self.identity} specialist, I recommend...",
            "insights": [h.statement for h in testable[:3]],
            "confidence": self.relationship_score,
            "next_steps": ["Continue monitoring", "Test hypotheses"]
        }
        
        # Save memory
        self._save_memory()
        
        return response
    
    async def collaborate_on_consensus(
        self,
        topic: str,
        other_positions: List[ConsensusPosition]
    ) -> ConsensusPosition:
        """
        Collaborate with other specialists to reach consensus.
        
        Uses the collaboration engine for sophisticated consensus building.
        """
        # Use collaboration engine for sophisticated analysis
        agreement_level = self._collaboration_engine.analyze_agreement_level(other_positions)
        
        # Generate specialist recommendation
        recommendation = f"Based on {self.get_domain().value} expertise, I recommend..."
        supporting_data = [h.statement for h in self.hypothesis_tracker.hypotheses.values() if h.confidence > 0.7]
        
        # Use collaboration engine to build consensus position
        position = self._collaboration_engine.build_consensus_position(
            topic=topic,
            other_positions=other_positions,
            specialist_recommendation=recommendation,
            supporting_data=supporting_data
        )
        
        # Update collaboration relationships
        self._collaboration_engine.update_collaboration_relationships(
            other_positions,
            outcome_success=True
        )
        
        # Update relationship score from engine
        self.relationship_score = min(1.0, self.relationship_score + 0.02)
        
        # Record collaboration using memory engine
        evolution = EvolutionRecord(
            timestamp=datetime.now(),
            interaction_type="collaboration",
            learning=f"Collaborated on: {topic}",
            confidence_delta=0.02,
            relationship_impact=0.02
        )
        self._memory_engine.store_evolution(evolution, self.evolution_history)
        self._save_memory()
        
        return position
    
    def get_collaboration_insights(self) -> Dict[str, Any]:
        """
        Get insights about this specialist's collaboration patterns.
        
        Returns:
            Dictionary with collaboration statistics and patterns
        """
        return self._collaboration_engine.get_collaboration_insights()
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search specialist's memories for relevant information.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant memories
        """
        memories = self._memory_engine.search_memories(
            self.evolution_history,
            query,
            limit
        )
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "type": m.interaction_type,
                "learning": m.learning,
                "confidence_delta": m.confidence_delta,
                "adaptation": m.learning
            }
            for m in memories
        ]
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        return self._memory_engine.get_memory_statistics(self.evolution_history)
    
    # === PHASE 1: SYNCHRONOUS WRAPPERS FOR CREWAI COMPATIBILITY ===
    
    def process_interaction_sync(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for process_interaction for CrewAI compatibility.
        
        CrewAI's task execution is synchronous, so this wrapper allows
        specialists to be used in standard CrewAI workflows while maintaining
        our async architecture for future scalability.
        
        Args:
            message: User message or task
            context: Relevant context including biometric data
            
        Returns:
            Response dictionary with recommendations and insights
        """
        # Create new event loop if needed (for thread safety)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async method
        return loop.run_until_complete(self.process_interaction(message, context))
    
    def collaborate_on_consensus_sync(
        self,
        topic: str,
        other_positions: List[ConsensusPosition]
    ) -> ConsensusPosition:
        """
        Synchronous wrapper for collaborate_on_consensus for CrewAI compatibility.
        
        Allows specialists to participate in consensus building within
        CrewAI's synchronous task execution model.
        
        Args:
            topic: The topic requiring consensus
            other_positions: Positions from other specialists
            
        Returns:
            This specialist's consensus position
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.collaborate_on_consensus(topic, other_positions))
    
    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a task in CrewAI-compatible format.
        
        This method provides a simple string-in, string-out interface
        that CrewAI tasks expect, while leveraging the full specialist
        capabilities internally.
        
        Args:
            task_description: The task to execute
            context: Optional context dictionary
            
        Returns:
            String response suitable for CrewAI task output
        """
        if context is None:
            context = {}
        
        # Process using our rich interaction model
        result = self.process_interaction_sync(task_description, context)
        
        # Format response for CrewAI
        response_parts = []
        
        if 'recommendation' in result:
            response_parts.append(f"Recommendation: {result['recommendation']}")
        
        if 'insights' in result:
            response_parts.append(f"Key Insights: {', '.join(result['insights'])}")
        
        if 'confidence' in result:
            response_parts.append(f"Confidence Level: {result['confidence']:.0%}")
        
        if 'next_steps' in result:
            response_parts.append(f"Next Steps: {', '.join(result['next_steps'])}")
        
        return '\n'.join(response_parts)
    
    def to_yaml_config(self) -> Dict[str, Any]:
        """
        Export specialist configuration in YAML-compatible format.
        
        This allows basic interoperability with CrewAI YAML workflows
        while maintaining the dynamic nature of specialists.
        
        Note: This exports a snapshot of current state. The specialist's
        autonomous evolution and trait-based behaviors are not captured
        in static YAML.
        
        Returns:
            Dictionary suitable for YAML serialization
        """
        # Get current tools
        tool_names = []
        for tool in self.get_specialist_tools():
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            elif hasattr(tool, 'name'):
                tool_names.append(tool.name)
            else:
                tool_names.append(str(tool))
        
        config = {
            "role": self.identity,
            "goal": self.mission,
            "backstory": self.genesis.to_backstory() if hasattr(self, 'genesis') else self.identity,
            "memory": True,
            "verbose": True,
            "allow_delegation": True,
            "tools": tool_names,
            "metadata": {
                "domain": self.get_domain().value,
                "traits": {
                    "risk_tolerance": self.traits.risk_tolerance,
                    "collaboration_style": self.traits.collaboration_style,
                    "learning_rate": self.traits.learning_rate,
                    "skepticism_level": self.traits.skepticism_level,
                    "innovation_tendency": self.traits.innovation_tendency
                },
                "relationship_score": self.relationship_score,
                "hypothesis_count": len(self.hypothesis_tracker.hypotheses),
                "evolution_count": len(self.evolution_history),
                "collaboration_insights": self.get_collaboration_insights()
            }
        }
        
        return config
    
    def to_yaml_string(self) -> str:
        """
        Export specialist configuration as YAML string.
        
        Returns:
            YAML formatted string
        """
        import yaml
        return yaml.dump(self.to_yaml_config(), default_flow_style=False)
    
    @property
    def domain(self) -> SpecialistDomain:
        """Convenience property for accessing domain."""
        return self.get_domain()
