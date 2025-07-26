"""
Core data structures for AUREN's agent intelligence system
These define how agents think, learn, and share knowledge
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Status tracking for hypotheses as they move through validation
class HypothesisStatus(Enum):
    """Tracks where a hypothesis is in its lifecycle"""
    FORMED = "formed"  # Just created, not yet tested
    ACTIVE = "active"  # Currently collecting evidence
    VALIDATED = "validated"  # Confirmed through evidence
    INVALIDATED = "invalidated"  # Disproven by evidence
    EXPIRED = "expired"  # Timed out without enough evidence
    RETIRED = "retired"  # Manually retired

class ValidationStrength(Enum):
    """How strong is the evidence for/against a hypothesis?"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    DEFINITIVE = "definitive"

class KnowledgeType(Enum):
    """Different types of knowledge agents can learn"""
    PATTERN = "pattern"  # Recurring patterns in data
    RELATIONSHIP = "relationship"  # How things relate to each other
    INTERVENTION = "intervention"  # What actions help
    CORRELATION = "correlation"  # Things that occur together
    PREDICTION_MODEL = "prediction_model"  # Predictive insights
    BEST_PRACTICE = "best_practice"  # Optimal approaches
    CONTRAINDICATION = "contraindication"  # What to avoid

class KnowledgeStatus(Enum):
    """Is this knowledge ready to use?"""
    PROVISIONAL = "provisional"  # Still being validated
    VALIDATED = "validated"  # Confirmed and ready to use
    DEPRECATED = "deprecated"  # No longer valid
    CONFLICTED = "conflicted"  # Conflicts with other knowledge

class SpecialistDomain(Enum):
    """The specialist domains in AUREN"""
    NEUROSCIENCE = "neuroscience"
    NUTRITION = "nutrition"
    TRAINING = "training"
    RECOVERY = "recovery"
    SLEEP = "sleep"
    MENTAL_HEALTH = "mental_health"

@dataclass
class Hypothesis:
    """
    A hypothesis is a testable prediction about user patterns.
    For example: "User's HRV drops after intense workouts"
    """
    hypothesis_id: str
    agent_id: str  # Which agent formed this hypothesis
    user_id: str
    domain: str  # Which specialist domain
    description: str  # Human-readable hypothesis
    prediction: Dict[str, Any]  # What we expect to see
    confidence: float  # How confident are we? (0.0 to 1.0)
    evidence_criteria: List[Dict[str, Any]]  # What evidence do we need?
    formed_at: datetime
    expires_at: datetime  # When to give up if no evidence
    status: HypothesisStatus
    metadata: Dict[str, Any]
    
    # Validation tracking
    evidence_collected: List[Dict[str, Any]] = field(default_factory=list)
    validation_attempts: int = 0
    validation_history: List[Dict[str, Any]] = field(default_factory=list)
    last_validated: Optional[datetime] = None

@dataclass
class ValidationEvidence:
    """Evidence collected to validate/invalidate a hypothesis"""
    evidence_id: str
    hypothesis_id: str
    evidence_type: str
    data: Dict[str, Any]
    collected_at: datetime
    source: str  # Where did this evidence come from?
    confidence: float
    supports_hypothesis: bool  # Does this support or contradict?
    strength: ValidationStrength

@dataclass
class ValidationResult:
    """The result of validating a hypothesis with evidence"""
    hypothesis_id: str
    is_validated: bool
    confidence_multiplier: float  # Adjust hypothesis confidence
    validation_score: float
    supporting_evidence: int
    contradicting_evidence: int
    statistical_summary: Dict[str, Any]
    evidence_quality_score: float
    recommendation: str  # What to do with this hypothesis

@dataclass
class KnowledgeItem:
    """
    A piece of validated knowledge that agents can use.
    This is what hypotheses become when validated.
    """
    knowledge_id: str
    agent_id: str
    domain: str
    knowledge_type: KnowledgeType
    title: str
    description: str
    content: Dict[str, Any]
    confidence: float
    evidence_sources: List[str]
    validation_status: KnowledgeStatus
    related_knowledge: List[str]  # IDs of related knowledge
    conflicts_with: List[str]  # IDs of conflicting knowledge
    supports: List[str]  # IDs of knowledge this supports
    application_count: int  # How many times has this been used?
    success_rate: float  # Success rate when applied
    last_applied: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class CrossAgentInsight:
    """Insights that emerge from collaboration between agents"""
    insight_id: str
    agents_involved: List[str]
    user_id: str
    insight_type: str  # What kind of insight is this?
    description: str
    supporting_knowledge: List[str]  # Knowledge IDs that support this
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class EmergencyProtocol:
    """Emergency response protocols for critical situations"""
    protocol_id: str
    trigger_conditions: Dict[str, Any]
    severity_level: int  # 1-10 scale
    response_actions: List[Dict[str, Any]]
    estimated_impact: str
    confidence: float
    created_at: datetime
    last_triggered: Optional[datetime]
    trigger_count: int = 0

@dataclass
class BiometricDataPoint:
    """A single biometric data point"""
    timestamp: datetime
    metric_type: str  # hrv, stress, sleep, etc.
    value: float
    source: str  # device, manual, etc.
    quality: float  # 0.0 to 1.0
    context: Dict[str, Any]  # Additional context

@dataclass
class UserProfile:
    """User profile for personalization"""
    user_id: str
    baseline_metrics: Dict[str, float]
    preferences: Dict[str, Any]
    medical_history: List[str]
    current_goals: List[str]
    risk_factors: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class ValidationRequest:
    """Request to validate a hypothesis"""
    hypothesis_id: str
    user_id: str
    validation_method: str  # statistical, clinical, etc.
    required_confidence: float
    max_duration: timedelta
    additional_data: Dict[str, Any]

@dataclass
class CollaborationRequest:
    """Request for cross-agent collaboration"""
    request_id: str
    requesting_agent: str
    target_agents: List[str]
    user_id: str
    question: str
    context: Dict[str, Any]
    urgency: int  # 1-10 scale
    created_at: datetime

@dataclass
class LearningMetrics:
    """Metrics about the learning system"""
    total_hypotheses: int
    validated_hypotheses: int
    invalidated_hypotheses: int
    active_hypotheses: int
    total_knowledge: int
    knowledge_by_domain: Dict[str, int]
    average_confidence: float
    learning_rate: float  # How quickly the system is improving
    last_updated: datetime

# Configuration for different domains
DOMAIN_CONFIGS = {
    "neuroscience": {
        "key_metrics": ["hrv", "cortisol", "sleep_quality", "cognitive_performance"],
        "validation_methods": ["statistical", "clinical", "biometric"],
        "evidence_requirements": {
            "minimum_samples": 10,
            "minimum_duration_days": 7,
            "confidence_threshold": 0.8
        }
    },
    "nutrition": {
        "key_metrics": ["calories", "macros", "micronutrients", "energy_levels"],
        "validation_methods": ["biometric", "self_reported", "lab_results"],
        "evidence_requirements": {
            "minimum_samples": 14,
            "minimum_duration_days": 14,
            "confidence_threshold": 0.75
        }
    },
    "training": {
        "key_metrics": ["performance", "recovery", "fatigue", "motivation"],
        "validation_methods": ["biometric", "performance", "self_reported"],
        "evidence_requirements": {
            "minimum_samples": 7,
            "minimum_duration_days": 7,
            "confidence_threshold": 0.7
        }
    }
}

# Emergency thresholds
EMERGENCY_THRESHOLDS = {
    "hrv": {"critical": 20, "warning": 30},
    "stress": {"critical": 8, "warning": 6},
    "sleep": {"critical": 4, "warning": 6},
    "fatigue": {"critical": 8, "warning": 6}
}

# Confidence adjustment factors
CONFIDENCE_FACTORS = {
    "evidence_quality": 0.3,
    "sample_size": 0.2,
    "consistency": 0.2,
    "clinical_validation": 0.3
}

def create_hypothesis_id() -> str:
    """Generate unique hypothesis ID"""
    return f"hypothesis_{uuid.uuid4().hex[:8]}"

def create_knowledge_id() -> str:
    """Generate unique knowledge ID"""
    return f"knowledge_{uuid.uuid4().hex[:8]}"

def create_insight_id() -> str:
    """Generate unique insight ID"""
    return f"insight_{uuid.uuid4().hex[:8]}"

def calculate_confidence_adjustment(
    evidence_quality: float,
    sample_size: int,
    consistency: float,
    clinical_validation: bool
) -> float:
    """
    Calculate confidence adjustment based on validation factors
    
    Args:
        evidence_quality: Quality of evidence (0.0 to 1.0)
        sample_size: Number of data points
        consistency: Consistency of results (0.0 to 1.0)
        clinical_validation: Whether clinically validated
        
    Returns:
        Confidence multiplier
    """
    
    base_multiplier = 1.0
    
    # Evidence quality impact
    quality_factor = evidence_quality * CONFIDENCE_FACTORS["evidence_quality"]
    
    # Sample size impact (diminishing returns)
    size_factor = min(1.0, sample_size / 100) * CONFIDENCE_FACTORS["sample_size"]
    
    # Consistency impact
    consistency_factor = consistency * CONFIDENCE_FACTORS["consistency"]
    
    # Clinical validation impact
    clinical_factor = (1.0 if clinical_validation else 0.5) * CONFIDENCE_FACTORS["clinical_validation"]
    
    # Calculate total adjustment
    total_adjustment = quality_factor + size_factor + consistency_factor + clinical_factor
    
    # Apply to base multiplier
    multiplier = base_multiplier * (1 + total_adjustment)
    
    # Cap between 0.5 and 2.0
    return max(0.5, min(2.0, multiplier))

def is_emergency_condition(metrics: Dict[str, float]) -> tuple[bool, str]:
    """
    Check if metrics indicate emergency condition
    
    Args:
        metrics: Dictionary of metric values
        
    Returns:
        Tuple of (is_emergency, reason)
    """
    
    for metric, value in metrics.items():
        if metric in EMERGENCY_THRESHOLDS:
            thresholds = EMERGENCY_THRESHOLDS[metric]
            if value <= thresholds.get("critical", 0) or value >= thresholds.get("critical", 10):
                return True, f"Critical {metric}: {value}"
    
    return False, ""

def format_hypothesis_for_display(hypothesis: Hypothesis) -> str:
    """Format hypothesis for user-friendly display"""
    return f"""
    **Hypothesis**: {hypothesis.description}
    **Confidence**: {hypothesis.confidence:.0%}
    **Status**: {hypothesis.status.value.title()}
    **Domain**: {hypothesis.domain.title()}
    **Formed**: {hypothesis.formed_at.strftime('%Y-%m-%d')}
    **Expires**: {hypothesis.expires_at.strftime('%Y-%m-%d')}
    """

def format_knowledge_for_display(knowledge: KnowledgeItem) -> str:
    """Format knowledge for user-friendly display"""
    return f"""
    **{knowledge.title}**
    {knowledge.description}
    
    **Confidence**: {knowledge.confidence:.0%}
    **Status**: {knowledge.validation_status.value.title()}
    **Domain**: {knowledge.domain.title()}
    **Success Rate**: {knowledge.success_rate:.0%}
    **Applications**: {knowledge.application_count}
    """

# Example usage functions
def create_sample_hypothesis(user_id: str, agent_id: str) -> Hypothesis:
    """Create a sample hypothesis for testing"""
    return Hypothesis(
        hypothesis_id=create_hypothesis_id(),
        agent_id=agent_id,
        user_id=user_id,
        domain="neuroscience",
        description="User's HRV improves with consistent sleep schedule",
        prediction={
            "expected_change": 15,
            "metric": "hrv",
            "condition": "consistent_sleep"
        },
        confidence=0.7,
        evidence_criteria=[
            {"type": "hrv", "minimum_days": 14, "threshold": 10},
            {"type": "sleep_consistency", "minimum_days": 14}
        ],
        formed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        status=HypothesisStatus.FORMED,
        metadata={"source": "neuroscientist_analysis"}
    )

def create_sample_knowledge(user_id: str, agent_id: str) -> KnowledgeItem:
    """Create sample knowledge for testing"""
    return KnowledgeItem(
        knowledge_id=create_knowledge_id(),
        agent_id=agent_id,
        user_id=user_id,
        domain="neuroscience",
        knowledge_type=KnowledgeType.PATTERN,
        title="HRV-Sleep Correlation",
        description="Consistent sleep schedule improves HRV by 15-20%",
        content={
            "pattern": "hrv_improvement",
            "magnitude": 17.5,
            "confidence_interval": [15, 20],
            "conditions": ["consistent_sleep", "7+_hours"]
        },
        confidence=0.85,
        evidence_sources=["biometric_data", "sleep_tracking", "clinical_validation"],
        validation_status=KnowledgeStatus.VALIDATED,
        related_knowledge=[],
        conflicts_with=[],
        supports=[],
        application_count=25,
        success_rate=0.92,
        last_applied=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata={"validation_method": "statistical", "sample_size": 50}
    )
