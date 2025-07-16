"""
BaseSpecialist - The foundation for autonomous AI specialists.

This module provides the base class for all AUREN specialists, implementing
the core functionality for autonomous, self-evolving AI colleagues that
maintain their own knowledge, hypotheses, and relationships over time.

Phase 1: Added synchronous wrappers for CrewAI compatibility
while maintaining the async architecture for future scalability.
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

logger = logging.getLogger(__name__)


class SpecialistDomain(Enum):
    """Domains of expertise for specialists."""
    NEUROSCIENCE = "neuroscience"
    NUTRITION = "nutrition"
    FITNESS = "fitness"
    PHYSICAL_THERAPY = "physical_therapy"
    MEDICAL_ESTHETICS = "medical_esthetics"


@dataclass
class SpecialistTraits:
    """Personality traits that influence specialist behavior."""
    risk_tolerance: float = 0.5  # 0.0 to 1.0
    collaboration_style: str = "balanced"  # assertive, accommodating, balanced
    learning_rate: float = 0.1  # How quickly they update beliefs
    skepticism_level: float = 0.5  # How much evidence they need
    innovation_tendency: float = 0.5  # Preference for novel approaches


@dataclass
class SpecialistGenesis:
    """Initial configuration for specialist creation."""
    identity: str
    mission: str
    expertise: List[str]
    collaboration_philosophy: str
    initial_hypotheses: List[str]
    learning_objectives: List[str]
    traits: SpecialistTraits
    
    def to_backstory(self) -> str:
        """Convert genesis to CrewAI backstory format."""
        return f"""
        I am {self.identity}, a specialist focused on {self.mission}.
        
        My expertise includes: {', '.join(self.expertise)}.
        
        My collaboration philosophy: {self.collaboration_philosophy}.
        
        I approach problems with {self.traits.collaboration_style} collaboration,
        {self.traits.risk_tolerance * 100:.0f}% risk tolerance, and
        {self.traits.innovation_tendency * 100:.0f}% innovation tendency.
        
        My learning objectives: {', '.join(self.learning_objectives)}.
        """


@dataclass
class Hypothesis:
    """Represents a testable hypothesis."""
    id: str
    statement: str
    confidence: float  # 0.0 to 1.0
    evidence_for: List[str]
    evidence_against: List[str]
    test_count: int = 0
    last_tested: Optional[datetime] = None
    
    def update_confidence(self, supporting: bool, weight: float = 0.1):
        """Update confidence based on evidence."""
        if supporting:
            self.confidence = min(1.0, self.confidence + weight * (1 - self.confidence))
        else:
            self.confidence = max(0.0, self.confidence - weight * self.confidence)


class HypothesisTracker:
    """Manages specialist hypotheses and their evolution."""
    
    def __init__(self):
        self.hypotheses: Dict[str, Hypothesis] = {}
    
    def add_hypothesis(self, statement: str, initial_confidence: float = 0.5) -> Hypothesis:
        """Add a new hypothesis."""
        hypothesis = Hypothesis(
            id=str(uuid.uuid4()),
            statement=statement,
            confidence=initial_confidence,
            evidence_for=[],
            evidence_against=[]
        )
        self.hypotheses[hypothesis.id] = hypothesis
        return hypothesis
    
    def update_confidence(
        self,
        hypothesis_id: str,
        supporting: bool,
        evidence: str,
        weight: float = 0.1
    ):
        """Update hypothesis confidence with new evidence."""
        if hypothesis_id in self.hypotheses:
            hypothesis = self.hypotheses[hypothesis_id]
            if supporting:
                hypothesis.evidence_for.append(evidence)
            else:
                hypothesis.evidence_against.append(evidence)
            hypothesis.update_confidence(supporting, weight)
            hypothesis.test_count += 1
            hypothesis.last_tested = datetime.now()
    
    def get_testable_hypotheses(
        self,
        min_confidence: float = 0.3,
        max_confidence: float = 0.7
    ) -> List[Hypothesis]:
        """Get hypotheses ready for testing."""
        return [
            h for h in self.hypotheses.values()
            if min_confidence <= h.confidence <= max_confidence
        ]
    
    def prune_failed_hypotheses(self, threshold: float = 0.2) -> List[str]:
        """Remove hypotheses with very low confidence."""
        failed = [
            h_id for h_id, h in self.hypotheses.items()
            if h.confidence < threshold and h.test_count > 0
        ]
        for h_id in failed:
            del self.hypotheses[h_id]
        return failed


@dataclass
class EvolutionRecord:
    """Records how a specialist evolves over time."""
    timestamp: datetime
    interaction_type: str
    learning: str
    confidence_delta: float
    relationship_impact: float = 0.0


@dataclass
class ConsensusPosition:
    """Represents a specialist's position on a consensus topic."""
    specialist_id: str
    position: str
    confidence: float
    reasoning: str
    supporting_evidence: List[str]


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
    
    Phase 1: Added synchronous wrappers for CrewAI compatibility
    while maintaining the async architecture for future scalability.
    """
    
    def __init__(
        self,
        genesis: SpecialistGenesis,
        cognitive_profile: Any,
        memory_path: Path
    ):
        self.identity = genesis.identity
        self.mission = genesis.mission
        self.expertise = genesis.expertise
        self.collaboration_philosophy = genesis.collaboration_philosophy
        self.traits = genesis.traits
        self.cognitive_profile = cognitive_profile
        
        # Memory management
        self.memory_backend = JSONFileMemoryBackend(memory_path)
        self.evolution_history: List[EvolutionRecord] = []
        self.hypothesis_tracker = HypothesisTracker()
        
        # Relationship tracking
        self.relationship_score = 0.5  # 0.0 to 1.0
        
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
        # Record interaction
        evolution = EvolutionRecord(
            timestamp=datetime.now(),
            interaction_type="user_interaction",
            learning=f"Processed: {message[:50]}...",
            confidence_delta=0.0
        )
        self.evolution_history.append(evolution)
        
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
        
        This async method allows specialists to participate in consensus building.
        """
        # Analyze other positions
        my_position = ConsensusPosition(
            specialist_id=self.identity,
            position=f"Based on {self.domain.value} expertise...",
            confidence=self.relationship_score,
            reasoning=f"My {self.domain.value} perspective considers...",
            supporting_evidence=[h.statement for h in self.hypothesis_tracker.hypotheses.values() if h.confidence > 0.7]
        )
        
        # Update relationship based on collaboration
        collaboration_bonus = 0.05 if self.traits.collaboration_style == "accommodating" else 0.02
        self.relationship_score = min(1.0, self.relationship_score + collaboration_bonus)
        
        # Record collaboration
        evolution = EvolutionRecord(
            timestamp=datetime.now(),
            interaction_type="collaboration",
            learning=f"Collaborated on: {topic}",
            confidence_delta=0.02,
            relationship_impact=collaboration_bonus
        )
        self.evolution_history.append(evolution)
        self._save_memory()
        
        return my_position
    
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
    
    @property
    def domain(self) -> SpecialistDomain:
        """Convenience property for accessing domain."""
        return self.get_domain()
