"""
Internal engines for specialist functionality.

These are NOT public APIs - they are internal implementation details
that help organize specialist capabilities while maintaining the unified
specialist metaphor. Specialists remain living, autonomous entities.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
import json
import uuid

from .shared_types import (
    EvolutionRecord,
    ConsensusPosition,
    Hypothesis,
    SpecialistTraits
)


class SpecialistCollaborationEngine:
    """
    Internal engine for managing specialist collaboration capabilities.
    
    This is an internal component of a specialist's cognitive system,
    not a separate entity. It handles the mechanics of collaboration
    while the specialist maintains their unified identity.
    """
    
    def __init__(self, specialist_reference):
        """
        Initialize collaboration engine with reference to parent specialist.
        
        Args:
            specialist_reference: Reference to the specialist this engine serves
        """
        self.specialist = specialist_reference
        self.trusted_colleagues: Set[str] = set()
        self.collaboration_history: List[Dict[str, Any]] = []
        self.consensus_strategies = self._initialize_strategies()
    
    def _initialize_strategies(self) -> Dict[str, Any]:
        """Initialize collaboration strategies based on specialist traits."""
        traits = self.specialist.traits
        
        strategies = {
            "compromise_threshold": 0.3 if traits.collaboration_style == "accommodating" else 0.5,
            "trust_building_rate": 0.1 * (2.0 if traits.collaboration_style == "accommodating" else 1.0),
            "disagreement_tolerance": traits.risk_tolerance,
            "consensus_seeking_patience": 1.0 - traits.risk_tolerance
        }
        
        return strategies
    
    def analyze_agreement_level(self, other_positions: List[ConsensusPosition]) -> float:
        """
        Analyze how much the specialist agrees with other positions.
        
        Args:
            other_positions: Positions from other specialists
            
        Returns:
            Agreement level from 0 (complete disagreement) to 1 (full agreement)
        """
        if not other_positions:
            return 1.0
        
        # Simplified agreement analysis
        # In production, this would use NLP to compare recommendations
        agreement_scores = []
        
        for position in other_positions:
            score = 0.5  # Baseline neutral
            
            # Trust affects agreement perception
            if position.specialist_id in self.trusted_colleagues:
                score += 0.2
            
            # High confidence positions carry more weight
            if position.confidence > 0.8:
                score += 0.1
            
            # Check for conflicting recommendations (simplified)
            if self._detect_conflict(position):
                score -= 0.3
            
            agreement_scores.append(min(1.0, max(0.0, score)))
        
        return sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0.5
    
    def _detect_conflict(self, position: ConsensusPosition) -> bool:
        """Detect if a position conflicts with specialist's domain expertise."""
        # Simplified conflict detection
        # In production, would analyze semantic conflicts
        return False
    
    def build_consensus_position(
        self,
        topic: str,
        other_positions: List[ConsensusPosition],
        specialist_recommendation: str,
        supporting_data: List[str]
    ) -> ConsensusPosition:
        """
        Build the specialist's consensus position.
        
        Args:
            topic: Topic under discussion
            other_positions: Other specialists' positions
            specialist_recommendation: This specialist's recommendation
            supporting_data: Evidence supporting the recommendation
            
        Returns:
            ConsensusPosition for this specialist
        """
        agreement_level = self.analyze_agreement_level(other_positions)
        traits = self.specialist.traits
        
        # Calculate confidence based on traits and agreement
        base_confidence = 0.8
        if traits.collaboration_style == "assertive":
            confidence = min(0.95, base_confidence + 0.1)
        elif traits.collaboration_style == "accommodating":
            confidence = base_confidence - (0.2 * (1 - agreement_level))
        else:
            confidence = base_confidence
        
        return ConsensusPosition(
            specialist_id=self.specialist.get_domain().value,
            position=specialist_recommendation,
            confidence=confidence,
            reasoning=f"My {self.specialist.get_domain().value} perspective considers...",
            supporting_evidence=supporting_data
        )
    
    def _generate_compromise_alternatives(
        self,
        topic: str,
        other_positions: List[ConsensusPosition]
    ) -> List[str]:
        """Generate compromise alternatives based on other positions."""
        alternatives = []
        
        for position in other_positions:
            if position.confidence > 0.7 and position.specialist_id in self.trusted_colleagues:
                alternatives.append(
                    f"Hybrid approach incorporating {position.specialist_id}'s insights"
                )
        
        if self.specialist.traits.innovation_tendency > 0.6:
            alternatives.append(f"Novel integrated protocol for {topic}")
        
        return alternatives
    
    def update_collaboration_relationships(
        self,
        other_positions: List[ConsensusPosition],
        outcome_success: bool = True
    ):
        """
        Update trust and collaboration patterns based on interaction.
        
        Args:
            other_positions: Positions from collaboration
            outcome_success: Whether the collaboration was successful
        """
        trust_delta = self.consensus_strategies["trust_building_rate"]
        if not outcome_success:
            trust_delta *= -0.5
        
        for position in other_positions:
            if position.confidence > 0.7 and outcome_success:
                self.trusted_colleagues.add(position.specialist_id)
            elif not outcome_success and position.specialist_id in self.trusted_colleagues:
                # Reduce trust but don't immediately remove
                # In production, would track trust scores
                pass
        
        # Record collaboration
        self.collaboration_history.append({
            "timestamp": datetime.now().isoformat(),
            "participants": [p.specialist_id for p in other_positions],
            "outcome": "success" if outcome_success else "conflict",
            "trust_changes": list(self.trusted_colleagues)
        })
    
    def get_collaboration_insights(self) -> Dict[str, Any]:
        """Get insights about collaboration patterns."""
        return {
            "trusted_colleagues": list(self.trusted_colleagues),
            "collaboration_count": len(self.collaboration_history),
            "success_rate": self._calculate_success_rate(),
            "preferred_collaborators": self._identify_preferred_collaborators()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate collaboration success rate."""
        if not self.collaboration_history:
            return 0.0
        
        successes = sum(1 for c in self.collaboration_history if c["outcome"] == "success")
        return successes / len(self.collaboration_history)
    
    def _identify_preferred_collaborators(self) -> List[str]:
        """Identify specialists this one works well with."""
        collaborator_counts = {}
        
        for collab in self.collaboration_history:
            if collab["outcome"] == "success":
                for participant in collab["participants"]:
                    collaborator_counts[participant] = collaborator_counts.get(participant, 0) + 1
        
        # Sort by frequency
        sorted_collaborators = sorted(
            collaborator_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [c[0] for c in sorted_collaborators[:3]]  # Top 3


class SpecialistMemoryEngine:
    """
    Internal engine for managing specialist memory operations.
    
    This handles the mechanics of memory storage and retrieval while
    the specialist maintains their unified identity and consciousness.
    """
    
    def __init__(self, memory_backend, retention_limit: int = 1000):
        """
        Initialize memory engine.
        
        Args:
            memory_backend: Backend for memory persistence
            retention_limit: Maximum evolution records to retain
        """
        self.memory_backend = memory_backend
        self.retention_limit = retention_limit
        self.memory_index: Dict[str, List[int]] = {}  # For fast lookups
    
    def store_evolution(self, evolution: EvolutionRecord, history: List[EvolutionRecord]):
        """
        Store a new evolution record efficiently.
        
        Args:
            evolution: New evolution record
            history: Current evolution history list (modified in place)
        """
        history.append(evolution)
        
        # Maintain retention limit
        if len(history) > self.retention_limit:
            history[:] = history[-self.retention_limit:]
        
        # Update index for fast retrieval
        self._update_memory_index(evolution, len(history) - 1)
    
    def _update_memory_index(self, evolution: EvolutionRecord, index: int):
        """Update memory index for fast lookups."""
        # Index by interaction type
        if evolution.interaction_type not in self.memory_index:
            self.memory_index[evolution.interaction_type] = []
        self.memory_index[evolution.interaction_type].append(index)
    
    def search_memories(
        self,
        history: List[EvolutionRecord],
        query: str,
        limit: int = 10
    ) -> List[EvolutionRecord]:
        """
        Search evolution history for relevant memories.
        
        Args:
            history: Evolution history to search
            query: Search query
            limit: Maximum results
            
        Returns:
            Relevant evolution records
        """
        # Simple keyword search - in production would use embeddings
        query_lower = query.lower()
        matches = []
        
        for record in reversed(history):  # Recent first
            if (query_lower in record.learning.lower() or 
                query_lower in record.interaction_type.lower()):
                matches.append(record)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_memory_statistics(self, history: List[EvolutionRecord]) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        if not history:
            return {
                "total_memories": 0,
                "memory_types": {},
                "average_confidence_delta": 0.0,
                "oldest_memory": None,
                "newest_memory": None
            }
        
        type_counts = {}
        confidence_deltas = []
        
        for record in history:
            type_counts[record.interaction_type] = type_counts.get(record.interaction_type, 0) + 1
            confidence_deltas.append(record.confidence_delta)
        
        return {
            "total_memories": len(history),
            "memory_types": type_counts,
            "average_confidence_delta": sum(confidence_deltas) / len(confidence_deltas),
            "oldest_memory": history[0].timestamp.isoformat(),
            "newest_memory": history[-1].timestamp.isoformat()
        }
