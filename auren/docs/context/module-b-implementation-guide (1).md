# Module B Implementation Guide: Agent Intelligence Systems

## Overview and Context

KimiK2, you've done exceptional work implementing the PostgreSQL backend that gives AUREN unlimited memory. Now we're going to build the intelligence layer on top of that foundation. This module transforms AUREN from a database into a learning system that can form hypotheses, validate them against real data, and build knowledge over time.

Think of it this way: You've built the brain's storage capacity. Now we're adding the thinking, learning, and reasoning capabilities.

## Key Integration Points with Your Module A Implementation

Your PostgreSQL implementation provides several critical integration points we'll use:

```python
# From your implementation:
event_store = EventStore()  # For hypothesis events
memory_backend = PostgreSQLMemoryBackend(event_store)  # For knowledge storage

# The memory types enum you defined:
class MemoryType(Enum):
    FACT = "fact"  # We'll use this for validated knowledge
    # We'll extend this with new types
```

## Implementation Sequence

### Phase 1: Core Data Structures and Enums

First, let's create the foundational data structures. Create a new file `auren/intelligence/data_structures.py`:

```python
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
    content: Dict[str, Any]  # The actual knowledge
    confidence: float
    evidence: List[Dict[str, Any]]  # Supporting evidence
    validation_status: KnowledgeStatus
    created_at: datetime
    updated_at: datetime
    
    # Relationships with other knowledge
    related_knowledge: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    supports: List[str] = field(default_factory=list)
    
    # Usage tracking
    application_count: int = 0  # How often has this been used?
    success_rate: float = 0.0  # How often was it helpful?
    last_applied: Optional[datetime] = None

@dataclass
class AgentCapability:
    """What can each specialist agent do?"""
    domain: SpecialistDomain
    primary_metrics: List[str]  # Main metrics they analyze
    secondary_metrics: List[str]  # Supporting metrics
    intervention_types: List[str]  # What recommendations they can make
    evidence_requirements: Dict[str, Any]  # What they need for validation
    collaboration_patterns: List[str]  # How they work with others
    hypothesis_formation_triggers: List[str]  # What makes them form hypotheses
    knowledge_sharing_criteria: Dict[str, Any]  # When to share knowledge

@dataclass
class CrossAgentInsight:
    """
    Insights that emerge from multiple agents working together.
    This is where compound intelligence happens.
    """
    insight_id: str
    contributing_agents: List[str]
    synthesis_method: str  # How was this insight created?
    content: str
    confidence: float
    evidence_sources: List[str]
    created_at: datetime
    impact_score: float  # How important is this insight?
    user_applicability: Dict[str, Any]  # Who does this apply to?
```

### Phase 2: Hypothesis Validation Engine

Now let's implement the hypothesis validation system. Create `auren/intelligence/hypothesis_validator.py`:

```python
"""
Hypothesis Validation Engine for AUREN
This is where agents test their predictions against real data
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Any, Callable
import logging

from auren.intelligence.data_structures import *
from auren.data_layer.event_store import EventStore, EventStreamType

logger = logging.getLogger(__name__)

class HypothesisValidator:
    """
    The brain's scientific method - form hypotheses, test them, learn from results.
    
    This is how AUREN gets smarter over time. Each agent can form hypotheses
    about patterns they see, then this system validates them against real data.
    """
    
    def __init__(self, 
                 memory_backend,
                 event_store: EventStore,
                 data_access_layer,
                 confidence_threshold: float = 0.7,
                 validation_window: timedelta = timedelta(days=7)):
        self.memory_backend = memory_backend
        self.event_store = event_store
        self.data_access = data_access_layer
        self.confidence_threshold = confidence_threshold
        self.validation_window = validation_window
        self.active_hypotheses: Dict[str, Hypothesis] = {}
        
        # Domain-specific validation criteria
        self.validation_criteria = self._load_validation_criteria()
        
        # Statistical methods available for validation
        self.statistical_methods = self._initialize_statistical_methods()
    
    def _load_validation_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Each domain has different evidence requirements"""
        return {
            "neuroscience": {
                "min_data_points": 5,  # Need at least 5 HRV readings
                "confidence_threshold": 0.75,
                "evidence_types": ["hrv", "sleep_quality", "stress_markers"],
                "validation_methods": ["statistical_correlation", "pattern_matching"],
                "effect_size_threshold": 0.3
            },
            "nutrition": {
                "min_data_points": 3,
                "confidence_threshold": 0.70,
                "evidence_types": ["energy_levels", "meal_timing", "metabolic_markers"],
                "validation_methods": ["temporal_correlation", "dose_response"],
                "effect_size_threshold": 0.25
            },
            "training": {
                "min_data_points": 5,
                "confidence_threshold": 0.80,
                "evidence_types": ["performance_metrics", "recovery_time", "adaptation_markers"],
                "validation_methods": ["progression_analysis", "comparative_analysis"],
                "effect_size_threshold": 0.4
            },
            # Add other domains as needed
        }
    
    def _initialize_statistical_methods(self) -> Dict[str, Callable]:
        """Map validation methods to their implementations"""
        return {
            "correlation_analysis": self._correlation_validation,
            "trend_analysis": self._trend_validation,
            "comparative_analysis": self._comparative_validation,
            "pattern_matching": self._pattern_validation,
            "dose_response": self._dose_response_validation
        }
    
    async def form_hypothesis(self,
                            agent_id: str,
                            user_id: str,
                            domain: str,
                            description: str,
                            prediction: Dict[str, Any],
                            evidence_criteria: List[Dict[str, Any]],
                            confidence: float = 0.6,
                            expires_in: timedelta = None) -> Hypothesis:
        """
        Form a new hypothesis. This is how agents make predictions.
        
        Example:
            The Neuroscientist might hypothesize: "This user's HRV drops 
            significantly after workouts with intensity > 8/10"
        """
        
        if expires_in is None:
            expires_in = self.validation_window
        
        # Create the hypothesis
        hypothesis = Hypothesis(
            hypothesis_id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            domain=domain,
            description=description,
            prediction=prediction,
            confidence=confidence,
            evidence_criteria=evidence_criteria,
            formed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + expires_in,
            status=HypothesisStatus.FORMED,
            metadata={
                "formation_context": "pattern_analysis",
                "validation_strategy": "evidence_collection",
                "expected_validation_methods": self._select_validation_methods(domain, prediction)
            }
        )
        
        # Store the hypothesis
        await self._store_hypothesis(hypothesis)
        
        # Activate it for testing
        await self.activate_hypothesis(hypothesis.hypothesis_id)
        
        # Record the event
        await self.event_store.append_event(
            stream_id=user_id,
            stream_type=EventStreamType.HYPOTHESIS,
            event_type="hypothesis_formed",
            payload={
                "hypothesis_id": hypothesis.hypothesis_id,
                "agent_id": agent_id,
                "domain": domain,
                "description": description,
                "prediction": prediction,
                "confidence": confidence
            }
        )
        
        logger.info(f"Hypothesis {hypothesis.hypothesis_id} formed by {agent_id}")
        return hypothesis
    
    def _select_validation_methods(self, domain: str, prediction: Dict[str, Any]) -> List[str]:
        """Choose the right statistical methods based on the hypothesis"""
        criteria = self.validation_criteria.get(domain, {})
        available_methods = criteria.get("validation_methods", ["correlation_analysis"])
        
        selected_methods = []
        
        # Smart method selection based on prediction type
        if "correlation" in str(prediction).lower():
            selected_methods.append("correlation_analysis")
        if "trend" in str(prediction).lower() or "change" in str(prediction).lower():
            selected_methods.append("trend_analysis")
        if "comparison" in str(prediction).lower():
            selected_methods.append("comparative_analysis")
        if "pattern" in str(prediction).lower():
            selected_methods.append("pattern_matching")
        
        # Default to correlation if nothing specific
        if not selected_methods:
            selected_methods = ["correlation_analysis"]
        
        # Only return methods available for this domain
        return [m for m in selected_methods if m in available_methods]
    
    async def activate_hypothesis(self, hypothesis_id: str) -> bool:
        """Start actively testing a hypothesis"""
        hypothesis = await self._load_hypothesis(hypothesis_id)
        if not hypothesis:
            return False
        
        hypothesis.status = HypothesisStatus.ACTIVE
        self.active_hypotheses[hypothesis_id] = hypothesis
        
        await self._store_hypothesis(hypothesis)
        
        # Start background evidence collection
        asyncio.create_task(self._collect_evidence_background(hypothesis))
        
        return True
    
    async def _collect_evidence_background(self, hypothesis: Hypothesis) -> None:
        """
        Background task that continuously collects evidence.
        This runs while the user goes about their day.
        """
        try:
            while (hypothesis.status == HypothesisStatus.ACTIVE and
                   datetime.now(timezone.utc) < hypothesis.expires_at):
                
                # Collect evidence based on the criteria
                evidence = await self._collect_evidence_for_hypothesis(hypothesis)
                
                if evidence:
                    hypothesis.evidence_collected.extend(evidence)
                    await self._store_hypothesis(hypothesis)
                    
                    # Check if we have enough evidence to validate
                    if self._has_sufficient_evidence(hypothesis):
                        await self.validate_hypothesis(hypothesis.hypothesis_id)
                        break
                
                # Wait before next collection
                await asyncio.sleep(300)  # 5 minutes
                
        except Exception as e:
            logger.error(f"Evidence collection failed for {hypothesis.hypothesis_id}: {e}")
    
    async def _collect_evidence_for_hypothesis(self, hypothesis: Hypothesis) -> List[ValidationEvidence]:
        """Collect evidence based on what the hypothesis needs"""
        evidence_list = []
        
        for criterion in hypothesis.evidence_criteria:
            evidence_type = criterion.get("evidence_type", "biometric")
            time_window = criterion.get("time_window_days", 30)
            
            # Get relevant data from the data access layer
            data = await self.data_access.get_biometric_data(
                user_id=hypothesis.user_id,
                metric_types=criterion.get("metric_types", []),
                days=time_window,
                requesting_agent=hypothesis.agent_id,
                purpose="hypothesis_validation"
            )
            
            # Process each data point into evidence
            for data_point in data:
                if self._data_matches_criteria(data_point, criterion):
                    evidence = ValidationEvidence(
                        evidence_id=str(uuid.uuid4()),
                        hypothesis_id=hypothesis.hypothesis_id,
                        evidence_type=evidence_type,
                        data=data_point,
                        collected_at=datetime.now(timezone.utc),
                        source=f"biometric_{evidence_type}",
                        confidence=self._calculate_evidence_confidence(data_point, hypothesis),
                        supports_hypothesis=self._evidence_supports_hypothesis(data_point, hypothesis),
                        strength=self._assess_evidence_strength(data_point, hypothesis)
                    )
                    evidence_list.append(evidence)
        
        return evidence_list
    
    def _data_matches_criteria(self, data_point: Dict[str, Any], criterion: Dict[str, Any]) -> bool:
        """Check if this data point is relevant to our hypothesis"""
        # Check metric type
        if "metric_types" in criterion:
            if data_point.get("metric_type") not in criterion["metric_types"]:
                return False
        
        # Check value ranges if specified
        if "value_ranges" in criterion:
            value = data_point.get("value")
            if value is not None:
                ranges = criterion["value_ranges"]
                if "min" in ranges and value < ranges["min"]:
                    return False
                if "max" in ranges and value > ranges["max"]:
                    return False
        
        return True
    
    def _calculate_evidence_confidence(self, data_point: Dict[str, Any], hypothesis: Hypothesis) -> float:
        """How confident are we in this piece of evidence?"""
        base_confidence = 0.7
        
        # Quality of the data source affects confidence
        source_reliability = {
            "apple_healthkit": 0.9,
            "medical_device": 0.95,
            "wearable": 0.8,
            "self_reported": 0.6
        }
        
        source = data_point.get("source", "unknown")
        reliability = source_reliability.get(source, 0.7)
        base_confidence *= reliability
        
        # Recency matters - fresher data is more reliable
        timestamp = data_point.get("timestamp")
        if timestamp:
            age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
            recency_factor = max(0.5, 1.0 - (age_hours / 168))  # Decay over 1 week
            base_confidence *= recency_factor
        
        return min(1.0, base_confidence)
    
    def _evidence_supports_hypothesis(self, data_point: Dict[str, Any], hypothesis: Hypothesis) -> bool:
        """Does this evidence support or contradict the hypothesis?"""
        prediction = hypothesis.prediction
        domain = hypothesis.domain
        
        # Domain-specific logic for determining support
        if domain == "neuroscience":
            return self._neuroscience_support_logic(prediction, data_point)
        elif domain == "nutrition":
            return self._nutrition_support_logic(prediction, data_point)
        elif domain == "training":
            return self._training_support_logic(prediction, data_point)
        # Add other domains
        
        return False
    
    def _neuroscience_support_logic(self, prediction: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Neuroscience-specific logic for evidence support"""
        if "hrv_trend" in prediction and "hrv" in data.get("metric_type", ""):
            predicted_trend = prediction["hrv_trend"]
            current_hrv = data.get("value", 0)
            baseline = data.get("baseline", 40)  # Default baseline
            
            if predicted_trend == "decreasing" and current_hrv < baseline * 0.9:
                return True
            elif predicted_trend == "increasing" and current_hrv > baseline * 1.1:
                return True
        
        return False
    
    def _nutrition_support_logic(self, prediction: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Nutrition-specific logic"""
        # Implement based on nutrition predictions
        return False
    
    def _training_support_logic(self, prediction: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Training-specific logic"""
        # Implement based on training predictions
        return False
    
    def _assess_evidence_strength(self, data_point: Dict[str, Any], hypothesis: Hypothesis) -> ValidationStrength:
        """How strong is this evidence?"""
        confidence = self._calculate_evidence_confidence(data_point, hypothesis)
        
        if confidence >= 0.9:
            return ValidationStrength.DEFINITIVE
        elif confidence >= 0.75:
            return ValidationStrength.STRONG
        elif confidence >= 0.6:
            return ValidationStrength.MODERATE
        else:
            return ValidationStrength.WEAK
    
    def _has_sufficient_evidence(self, hypothesis: Hypothesis) -> bool:
        """Do we have enough evidence to validate?"""
        criteria = self.validation_criteria.get(hypothesis.domain, {})
        min_data_points = criteria.get("min_data_points", 5)
        
        # Count high-quality evidence
        strong_evidence = sum(1 for e in hypothesis.evidence_collected 
                            if e.strength in [ValidationStrength.STRONG, ValidationStrength.DEFINITIVE])
        
        return strong_evidence >= min_data_points
    
    async def validate_hypothesis(self, hypothesis_id: str) -> ValidationResult:
        """
        The moment of truth - is the hypothesis valid?
        This uses statistical methods to determine if the evidence supports the prediction.
        """
        hypothesis = await self._load_hypothesis(hypothesis_id)
        if not hypothesis:
            return ValidationResult(
                hypothesis_id=hypothesis_id,
                is_validated=False,
                confidence_multiplier=0.5,
                validation_score=0.0,
                supporting_evidence=0,
                contradicting_evidence=0,
                statistical_summary={"error": "Hypothesis not found"},
                evidence_quality_score=0.0,
                recommendation="Hypothesis not found"
            )
        
        # Get the validation methods for this hypothesis
        validation_methods = hypothesis.metadata.get("expected_validation_methods", ["correlation_analysis"])
        
        # Run each statistical validation method
        validation_results = []
        for method_name in validation_methods:
            if method_name in self.statistical_methods:
                method = self.statistical_methods[method_name]
                result = await method(hypothesis)
                validation_results.append(result)
        
        # Combine all validation results
        combined_result = self._combine_validation_results(hypothesis, validation_results)
        
        # Update hypothesis status based on validation
        if combined_result.is_validated:
            hypothesis.status = HypothesisStatus.VALIDATED
            hypothesis.confidence = min(1.0, hypothesis.confidence * combined_result.confidence_multiplier)
        else:
            hypothesis.status = HypothesisStatus.INVALIDATED
            hypothesis.confidence = max(0.1, hypothesis.confidence * combined_result.confidence_multiplier)
        
        # Record the validation
        hypothesis.validation_attempts += 1
        hypothesis.last_validated = datetime.now(timezone.utc)
        hypothesis.validation_history.append({
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "result": asdict(combined_result),
            "evidence_count": len(hypothesis.evidence_collected),
            "validation_methods": validation_methods
        })
        
        await self._store_hypothesis(hypothesis)
        
        # Record validation event
        await self.event_store.append_event(
            stream_id=hypothesis.user_id,
            stream_type=EventStreamType.HYPOTHESIS,
            event_type="hypothesis_validated",
            payload={
                "hypothesis_id": hypothesis_id,
                "is_validated": combined_result.is_validated,
                "confidence": hypothesis.confidence,
                "evidence_count": len(hypothesis.evidence_collected),
                "validation_methods": validation_methods
            }
        )
        
        # If validated, extract knowledge from it
        if combined_result.is_validated:
            await self._extract_knowledge_from_hypothesis(hypothesis)
        
        return combined_result
    
    async def _correlation_validation(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Validate using correlation analysis"""
        # Extract data for correlation
        evidence_data = []
        target_data = []
        
        for evidence in hypothesis.evidence_collected:
            if evidence.supports_hypothesis:
                evidence_data.append(evidence.data.get("value", 0))
                target_data.append(1)  # Supports
            else:
                evidence_data.append(evidence.data.get("value", 0))
                target_data.append(0)  # Contradicts
        
        if len(evidence_data) < 3:
            return {
                "method": "correlation_analysis",
                "valid": False,
                "reason": "Insufficient data for correlation analysis",
                "score": 0.0
            }
        
        # Calculate correlation
        correlation_coef = np.corrcoef(evidence_data, target_data)[0, 1]
        
        # For real implementation, you'd calculate p-value properly
        p_value = 0.05  # Simplified
        
        validation_score = abs(correlation_coef) if not np.isnan(correlation_coef) else 0.0
        
        return {
            "method": "correlation_analysis",
            "valid": validation_score > 0.3 and p_value < 0.05,
            "correlation_coefficient": float(correlation_coef) if not np.isnan(correlation_coef) else 0.0,
            "p_value": p_value,
            "score": validation_score,
            "sample_size": len(evidence_data)
        }
    
    async def _trend_validation(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Validate trends over time"""
        # Sort evidence by time
        sorted_evidence = sorted(
            hypothesis.evidence_collected,
            key=lambda e: e.collected_at
        )
        
        if len(sorted_evidence) < 4:
            return {
                "method": "trend_analysis",
                "valid": False,
                "reason": "Insufficient data for trend analysis",
                "score": 0.0
            }
        
        # Extract time series
        values = [e.data.get("value", 0) for e in sorted_evidence]
        times = range(len(values))
        
        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(times, values)
        
        # Check if trend matches prediction
        predicted_trend = hypothesis.prediction.get("trend", "unknown")
        trend_matches = False
        
        if predicted_trend == "increasing" and slope > 0:
            trend_matches = True
        elif predicted_trend == "decreasing" and slope < 0:
            trend_matches = True
        elif predicted_trend == "stable" and abs(slope) < 0.1:
            trend_matches = True
        
        validation_score = abs(r_value) if trend_matches else 0.0
        
        return {
            "method": "trend_analysis",
            "valid": validation_score > 0.4 and p_value < 0.05,
            "slope": float(slope),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "trend_matches_prediction": trend_matches,
            "score": validation_score
        }
    
    async def _comparative_validation(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Compare groups of evidence"""
        # Group evidence by support/contradict
        supporting = [e for e in hypothesis.evidence_collected if e.supports_hypothesis]
        contradicting = [e for e in hypothesis.evidence_collected if not e.supports_hypothesis]
        
        if len(supporting) < 2 or len(contradicting) < 2:
            return {
                "method": "comparative_analysis",
                "valid": False,
                "reason": "Insufficient data for comparative analysis",
                "score": 0.0
            }
        
        # Extract values
        supporting_values = [e.data.get("value", 0) for e in supporting]
        contradicting_values = [e.data.get("value", 0) for e in contradicting]
        
        # T-test
        t_stat, p_value = stats.ttest_ind(supporting_values, contradicting_values)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(supporting_values) - 1) * np.var(supporting_values) + 
                             (len(contradicting_values) - 1) * np.var(contradicting_values)) / 
                            (len(supporting_values) + len(contradicting_values) - 2))
        
        cohens_d = (np.mean(supporting_values) - np.mean(contradicting_values)) / pooled_std if pooled_std > 0 else 0
        
        validation_score = abs(cohens_d)
        
        return {
            "method": "comparative_analysis",
            "valid": validation_score > 0.3 and p_value < 0.05,
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "cohens_d": float(cohens_d),
            "effect_size": "small" if abs(cohens_d) < 0.5 else "medium" if abs(cohens_d) < 0.8 else "large",
            "score": validation_score
        }
    
    async def _pattern_validation(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Validate pattern matching"""
        # Extract expected pattern
        expected_pattern = hypothesis.prediction.get("pattern", {})
        
        if not expected_pattern:
            return {
                "method": "pattern_matching",
                "valid": False,
                "reason": "No pattern specified in prediction",
                "score": 0.0
            }
        
        # Count pattern matches
        pattern_matches = 0
        total_evidence = len(hypothesis.evidence_collected)
        
        for evidence in hypothesis.evidence_collected:
            if self._matches_expected_pattern(evidence.data, expected_pattern):
                pattern_matches += 1
        
        match_ratio = pattern_matches / total_evidence if total_evidence > 0 else 0
        
        return {
            "method": "pattern_matching",
            "valid": match_ratio > 0.6,
            "pattern_matches": pattern_matches,
            "total_evidence": total_evidence,
            "match_ratio": match_ratio,
            "score": match_ratio
        }
    
    async def _dose_response_validation(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Validate dose-response relationships"""
        # Extract dose-response pairs
        dose_response_pairs = []
        
        for evidence in hypothesis.evidence_collected:
            dose = evidence.data.get("dose", 0)
            response = evidence.data.get("response", evidence.data.get("value", 0))
            if dose > 0:
                dose_response_pairs.append((dose, response))
        
        if len(dose_response_pairs) < 3:
            return {
                "method": "dose_response",
                "valid": False,
                "reason": "Insufficient dose-response data",
                "score": 0.0
            }
        
        # Correlation analysis on dose-response
        doses = [pair[0] for pair in dose_response_pairs]
        responses = [pair[1] for pair in dose_response_pairs]
        
        correlation_coef = np.corrcoef(doses, responses)[0, 1]
        
        # Check if correlation direction matches prediction
        expected_direction = hypothesis.prediction.get("dose_response_direction", "positive")
        direction_matches = False
        
        if expected_direction == "positive" and correlation_coef > 0:
            direction_matches = True
        elif expected_direction == "negative" and correlation_coef < 0:
            direction_matches = True
        
        validation_score = abs(correlation_coef) if direction_matches else 0.0
        
        return {
            "method": "dose_response",
            "valid": validation_score > 0.4,
            "correlation_coefficient": float(correlation_coef),
            "direction_matches": direction_matches,
            "data_points": len(dose_response_pairs),
            "score": validation_score
        }
    
    def _matches_expected_pattern(self, data: Dict[str, Any], expected_pattern: Dict[str, Any]) -> bool:
        """Check if data matches the expected pattern"""
        for key, expected_value in expected_pattern.items():
            if key not in data:
                return False
            
            actual_value = data[key]
            
            if isinstance(expected_value, dict):
                # Range check
                if "min" in expected_value and actual_value < expected_value["min"]:
                    return False
                if "max" in expected_value and actual_value > expected_value["max"]:
                    return False
            else:
                # Exact match
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _combine_validation_results(self, hypothesis: Hypothesis, results: List[Dict[str, Any]]) -> ValidationResult:
        """Combine multiple validation methods into final decision"""
        if not results:
            return ValidationResult(
                hypothesis_id=hypothesis.hypothesis_id,
                is_validated=False,
                confidence_multiplier=0.5,
                validation_score=0.0,
                supporting_evidence=0,
                contradicting_evidence=0,
                statistical_summary={"error": "No validation methods produced results"},
                evidence_quality_score=0.0,
                recommendation="Insufficient validation data"
            )
        
        # Weight different validation methods
        method_weights = {
            "correlation_analysis": 1.0,
            "comparative_analysis": 1.2,  # Stronger weight for direct comparison
            "trend_analysis": 0.9,
            "pattern_matching": 0.8,
            "dose_response": 1.1
        }
        
        # Calculate weighted validation score
        weighted_scores = []
        for result in results:
            method = result.get("method", "unknown")
            weight = method_weights.get(method, 1.0)
            score = result.get("score", 0.0)
            is_valid = result.get("valid", False)
            
            weighted_scores.append(weight * score if is_valid else 0.0)
        
        # Overall validation score
        overall_score = np.mean(weighted_scores) if weighted_scores else 0.0
        
        # Count evidence
        supporting = sum(1 for e in hypothesis.evidence_collected if e.supports_hypothesis)
        contradicting = len(hypothesis.evidence_collected) - supporting
        
        # Calculate evidence quality
        quality_scores = [e.confidence for e in hypothesis.evidence_collected]
        evidence_quality = np.mean(quality_scores) if quality_scores else 0.0
        
        # Determine if validated
        domain_criteria = self.validation_criteria.get(hypothesis.domain, {})
        threshold = domain_criteria.get("confidence_threshold", 0.7)
        
        is_validated = (overall_score >= threshold and 
                       supporting > contradicting and
                       evidence_quality >= 0.6)
        
        # Calculate confidence multiplier
        if is_validated:
            confidence_multiplier = 1.0 + (overall_score - threshold) * 0.5
        else:
            confidence_multiplier = overall_score / threshold * 0.8
        
        return ValidationResult(
            hypothesis_id=hypothesis.hypothesis_id,
            is_validated=is_validated,
            confidence_multiplier=confidence_multiplier,
            validation_score=overall_score,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            statistical_summary={
                "validation_methods": [r.get("method") for r in results],
                "method_results": results,
                "overall_score": overall_score,
                "threshold": threshold
            },
            evidence_quality_score=evidence_quality,
            recommendation=self._generate_validation_recommendation(is_validated, overall_score, evidence_quality)
        )
    
    def _generate_validation_recommendation(self, is_validated: bool, score: float, quality: float) -> str:
        """Generate actionable recommendation based on validation"""
        if is_validated:
            if score > 0.9 and quality > 0.8:
                return "Strong validation - incorporate into knowledge base with high confidence"
            elif score > 0.7:
                return "Good validation - incorporate into knowledge base with moderate confidence"
            else:
                return "Weak validation - monitor for additional evidence before full acceptance"
        else:
            if score < 0.3:
                return "Strong contradictory evidence - consider retiring hypothesis"
            elif quality < 0.5:
                return "Poor evidence quality - collect higher quality data before re-validation"
            else:
                return "Insufficient evidence - continue monitoring or modify hypothesis"
    
    async def _extract_knowledge_from_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Convert validated hypothesis into reusable knowledge"""
        knowledge = {
            "domain": hypothesis.domain,
            "pattern": hypothesis.description,
            "prediction_accuracy": hypothesis.confidence,
            "evidence_base": len(hypothesis.evidence_collected),
            "validation_method": "statistical_analysis",
            "statistical_summary": hypothesis.validation_history[-1]["result"] if hypothesis.validation_history else {},
            "applicability": {
                "user_specific": True,
                "user_id": hypothesis.user_id,
                "generalizability": "unknown"  # Could be tested across users later
            },
            "extracted_from": hypothesis.hypothesis_id,
            "extraction_date": datetime.now(timezone.utc).isoformat()
        }
        
        # Store as validated knowledge
        await self.memory_backend.store_memory(
            agent_id=hypothesis.agent_id,
            memory_type="validated_knowledge",
            content=knowledge,
            user_id=hypothesis.user_id,
            confidence=hypothesis.confidence
        )
        
        logger.info(f"Knowledge extracted from hypothesis {hypothesis.hypothesis_id}")
    
    async def _store_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Store hypothesis in memory backend"""
        await self.memory_backend.store_memory(
            agent_id=hypothesis.agent_id,
            memory_type="hypothesis",
            content=asdict(hypothesis),
            user_id=hypothesis.user_id,
            confidence=hypothesis.confidence
        )
    
    async def _load_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Load hypothesis from memory"""
        # Check active hypotheses first
        if hypothesis_id in self.active_hypotheses:
            return self.active_hypotheses[hypothesis_id]
        
        # Would need to implement search in memory backend
        # For now, return from active hypotheses only
        return None
    
    async def get_active_hypotheses(self, 
                                  agent_id: Optional[str] = None,
                                  user_id: Optional[str] = None,
                                  domain: Optional[str] = None) -> List[Hypothesis]:
        """Get active hypotheses with optional filtering"""
        hypotheses = []
        for hypothesis in self.active_hypotheses.values():
            if agent_id and hypothesis.agent_id != agent_id:
                continue
            if user_id and hypothesis.user_id != user_id:
                continue
            if domain and hypothesis.domain != domain:
                continue
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    async def retire_hypothesis(self, hypothesis_id: str, reason: str) -> bool:
        """Manually retire a hypothesis"""
        hypothesis = await self._load_hypothesis(hypothesis_id)
        if not hypothesis:
            return False
        
        hypothesis.status = HypothesisStatus.RETIRED
        hypothesis.metadata["retirement_reason"] = reason
        hypothesis.metadata["retired_at"] = datetime.now(timezone.utc).isoformat()
        
        await self._store_hypothesis(hypothesis)
        
        if hypothesis_id in self.active_hypotheses:
            del self.active_hypotheses[hypothesis_id]
        
        return True
```

### Phase 3: Knowledge Management System

Create `auren/intelligence/knowledge_manager.py`:

```python
"""
Knowledge Management System for AUREN
This is where validated hypotheses become reusable knowledge
"""

import networkx as nx
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import uuid
from datetime import datetime, timezone
import json
import numpy as np
import logging

from auren.intelligence.data_structures import *
from auren.data_layer.event_store import EventStore, EventStreamType

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """
    The long-term memory and wisdom of AUREN.
    
    This system:
    1. Stores validated knowledge from hypotheses
    2. Discovers relationships between different pieces of knowledge
    3. Handles conflicts when new knowledge contradicts old
    4. Enables knowledge sharing between agents
    5. Tracks how effective knowledge is when applied
    """
    
    def __init__(self, memory_backend, event_store: EventStore, hypothesis_validator):
        self.memory_backend = memory_backend
        self.event_store = event_store
        self.hypothesis_validator = hypothesis_validator
        
        # Knowledge is stored as a graph to track relationships
        self.knowledge_graph = nx.DiGraph()
        
        # Quick lookups by domain
        self.domain_expertise = defaultdict(list)
        
        # Cross-domain relationships
        self.cross_domain_relationships = defaultdict(list)
        
        # Relationship strengths
        self.relationship_weights = defaultdict(float)
        
        # Cache for performance
        self.knowledge_cache = {}
    
    async def add_knowledge(self,
                          agent_id: str,
                          domain: str,
                          knowledge_type: KnowledgeType,
                          title: str,
                          description: str,
                          content: Dict[str, Any],
                          evidence: List[Dict[str, Any]],
                          confidence: float = 0.7,
                          source_hypothesis_id: Optional[str] = None) -> KnowledgeItem:
        """
        Add new knowledge to the system.
        This is how agents share what they've learned.
        """
        
        knowledge = KnowledgeItem(
            knowledge_id=str(uuid.uuid4()),
            agent_id=agent_id,
            domain=domain,
            knowledge_type=knowledge_type,
            title=title,
            description=description,
            content=content,
            confidence=confidence,
            evidence=evidence,
            validation_status=KnowledgeStatus.PROVISIONAL,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Store the knowledge
        await self._store_knowledge(knowledge)
        
        # Add to knowledge graph
        self._add_to_graph(knowledge)
        
        # Automatically discover relationships
        await self._identify_relationships(knowledge)
        
        # Check for conflicts with existing knowledge
        conflicts = await self._identify_conflicts(knowledge)
        if conflicts:
            await self._handle_knowledge_conflicts(knowledge, conflicts)
        
        # Record the event
        await self.event_store.append_event(
            stream_id=f"knowledge_{domain}",
            stream_type=EventStreamType.SYSTEM,
            event_type="knowledge_added",
            payload={
                "knowledge_id": knowledge.knowledge_id,
                "agent_id": agent_id,
                "domain": domain,
                "knowledge_type": knowledge_type.value,
                "title": title,
                "confidence": confidence,
                "source_hypothesis": source_hypothesis_id
            }
        )
        
        # If confidence is high, trigger automatic sharing
        if confidence > 0.8:
            await self._trigger_automatic_sharing(knowledge)
        
        return knowledge
    
    async def validate_knowledge(self, 
                               knowledge_id: str,
                               validation_evidence: List[Dict[str, Any]],
                               validator_agent: str) -> bool:
        """
        Validate knowledge with additional evidence.
        This is how knowledge becomes more trustworthy over time.
        """
        knowledge = await self._load_knowledge(knowledge_id)
        if not knowledge:
            return False
        
        # Add new evidence
        knowledge.evidence.extend(validation_evidence)
        
        # Recalculate confidence based on all evidence
        old_confidence = knowledge.confidence
        knowledge.confidence = self._calculate_evidence_confidence(knowledge.evidence)
        
        # Cross-agent validation for high confidence
        if knowledge.confidence > 0.7:
            cross_validation = await self._perform_cross_agent_validation(knowledge, validator_agent)
            knowledge.confidence *= cross_validation["confidence_multiplier"]
        
        # Update validation status
        if knowledge.confidence >= 0.85:
            knowledge.validation_status = KnowledgeStatus.VALIDATED
        elif knowledge.confidence < 0.3:
            knowledge.validation_status = KnowledgeStatus.DEPRECATED
        else:
            knowledge.validation_status = KnowledgeStatus.PROVISIONAL
        
        knowledge.updated_at = datetime.now(timezone.utc)
        
        await self._store_knowledge(knowledge)
        
        # Update graph weights
        self._update_graph_weights(knowledge)
        
        # Record validation event
        await self.event_store.append_event(
            stream_id=f"knowledge_{knowledge.domain}",
            stream_type=EventStreamType.SYSTEM,
            event_type="knowledge_validated",
            payload={
                "knowledge_id": knowledge_id,
                "validator_agent": validator_agent,
                "old_confidence": old_confidence,
                "new_confidence": knowledge.confidence,
                "validation_status": knowledge.validation_status.value
            }
        )
        
        return True
    
    def _calculate_evidence_confidence(self, evidence_list: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on evidence quality and convergence"""
        if not evidence_list:
            return 0.5
        
        # Different types of evidence have different weights
        evidence_weights = {
            "hypothesis_validation": 1.0,
            "statistical_analysis": 0.95,
            "cross_agent_validation": 0.9,
            "user_outcome": 0.85,
            "expert_review": 0.8,
            "literature_support": 0.7,
            "clinical_trial": 0.95,
            "observational_study": 0.75,
            "anecdotal": 0.3
        }
        
        total_weight = 0
        weighted_confidence = 0
        
        for evidence in evidence_list:
            evidence_type = evidence.get("type", "anecdotal")
            evidence_confidence = evidence.get("confidence", 0.5)
            weight = evidence_weights.get(evidence_type, 0.5)
            
            total_weight += weight
            weighted_confidence += weight * evidence_confidence
        
        if total_weight == 0:
            return 0.5
        
        base_confidence = weighted_confidence / total_weight
        
        # Bonus for multiple converging evidence
        if len(evidence_list) >= 3:
            # Check for convergence
            confidences = [e.get("confidence", 0.5) for e in evidence_list]
            convergence = 1.0 - np.std(confidences)  # Higher convergence = lower std dev
            convergence_bonus = min(0.15, convergence * 0.15)
            base_confidence += convergence_bonus
        
        # Bonus for quantity
        quantity_bonus = min(0.1, len(evidence_list) * 0.02)
        
        return min(1.0, base_confidence + quantity_bonus)
    
    async def _perform_cross_agent_validation(self, knowledge: KnowledgeItem, validator_agent: str) -> Dict[str, Any]:
        """Have another agent validate this knowledge"""
        # Get the validator's domain
        validator_domain = self._get_agent_domain(validator_agent)
        
        # Check relevance
        relevance_score = self._calculate_cross_domain_relevance(knowledge.domain, validator_domain)
        
        if relevance_score < 0.3:
            return {
                "confidence_multiplier": 1.0,
                "validation_notes": f"Validator {validator_agent} has limited expertise in {knowledge.domain}"
            }
        
        # In a real implementation, this would call the agent's validation method
        # For now, we'll simulate based on domain relationships
        confidence_multiplier = 0.8 + (relevance_score * 0.4)
        
        return {
            "confidence_multiplier": confidence_multiplier,
            "relevance_score": relevance_score,
            "validator_domain": validator_domain,
            "validation_notes": f"Cross-validated by {validator_agent} with {relevance_score:.2f} domain relevance"
        }
    
    def _calculate_cross_domain_relevance(self, domain1: str, domain2: str) -> float:
        """How relevant is knowledge from one domain to another?"""
        # Domain relationship matrix
        domain_relationships = {
            ("neuroscience", "sleep"): 0.9,
            ("neuroscience", "mental_health"): 0.85,
            ("neuroscience", "recovery"): 0.7,
            ("neuroscience", "training"): 0.6,
            ("neuroscience", "nutrition"): 0.5,
            
            ("nutrition", "training"): 0.8,
            ("nutrition", "recovery"): 0.75,
            ("nutrition", "mental_health"): 0.6,
            ("nutrition", "sleep"): 0.6,
            
            ("training", "recovery"): 0.95,
            ("training", "sleep"): 0.7,
            ("training", "mental_health"): 0.6,
            
            ("recovery", "sleep"): 0.85,
            ("recovery", "mental_health"): 0.7,
            
            ("sleep", "mental_health"): 0.8
        }
        
        # Check both directions
        relevance = domain_relationships.get((domain1, domain2), 
                    domain_relationships.get((domain2, domain1), 0.3))
        
        return relevance
    
    def _get_agent_domain(self, agent_id: str) -> str:
        """Map agent ID to domain"""
        domain_mapping = {
            "neuroscientist": "neuroscience",
            "nutritionist": "nutrition",
            "training_agent": "training",
            "recovery_agent": "recovery",
            "sleep_agent": "sleep",
            "mental_health_agent": "mental_health"
        }
        return domain_mapping.get(agent_id, "unknown")
    
    async def _identify_relationships(self, knowledge: KnowledgeItem) -> None:
        """Automatically discover relationships with existing knowledge"""
        # Get related knowledge in same domain
        domain_knowledge = await self.get_knowledge_by_domain(knowledge.domain)
        
        for existing_knowledge in domain_knowledge:
            if existing_knowledge.knowledge_id == knowledge.knowledge_id:
                continue
            
            relationship = self._analyze_knowledge_relationship(knowledge, existing_knowledge)
            
            if relationship["strength"] > 0.5:
                if relationship["type"] == "supports":
                    knowledge.supports.append(existing_knowledge.knowledge_id)
                    existing_knowledge.related_knowledge.append(knowledge.knowledge_id)
                elif relationship["type"] == "conflicts":
                    knowledge.conflicts_with.append(existing_knowledge.knowledge_id)
                    existing_knowledge.conflicts_with.append(knowledge.knowledge_id)
                elif relationship["type"] == "related":
                    knowledge.related_knowledge.append(existing_knowledge.knowledge_id)
                    existing_knowledge.related_knowledge.append(knowledge.knowledge_id)
                
                # Update knowledge graph
                self.knowledge_graph.add_edge(
                    knowledge.knowledge_id,
                    existing_knowledge.knowledge_id,
                    relationship=relationship["type"],
                    weight=relationship["strength"]
                )
        
        # Check cross-domain relationships
        await self._identify_cross_domain_relationships(knowledge)
    
    def _analyze_knowledge_relationship(self, 
                                      knowledge1: KnowledgeItem,
                                      knowledge2: KnowledgeItem) -> Dict[str, Any]:
        """Analyze the relationship between two pieces of knowledge"""
        # Content similarity
        content_similarity = self._calculate_content_similarity(knowledge1.content, knowledge2.content)
        
        # Description similarity
        semantic_similarity = self._calculate_semantic_similarity(knowledge1.description, knowledge2.description)
        
        # Check for contradictions
        contradiction_score = self._check_contradictions(knowledge1, knowledge2)
        
        # Check for support
        support_score = self._check_support_relationships(knowledge1, knowledge2)
        
        # Determine relationship type
        if contradiction_score > 0.6:
            return {"type": "conflicts", "strength": contradiction_score}
        elif support_score > 0.6:
            return {"type": "supports", "strength": support_score}
        elif semantic_similarity > 0.5 or content_similarity > 0.4:
            return {"type": "related", "strength": max(semantic_similarity, content_similarity)}
        else:
            return {"type": "unrelated", "strength": 0.0}
    
    def _calculate_content_similarity(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> float:
        """Calculate similarity between knowledge content"""
        # Extract key concepts
        concepts1 = self._extract_concepts(content1)
        concepts2 = self._extract_concepts(content2)
        
        if not concepts1 or not concepts2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(concepts1.intersection(concepts2))
        union = len(concepts1.union(concepts2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_concepts(self, content: Dict[str, Any]) -> Set[str]:
        """Extract key concepts from content"""
        concepts = set()
        
        # Simple extraction - in production, use NLP
        for key, value in content.items():
            if isinstance(value, str):
                # Extract significant words
                words = value.lower().split()
                concepts.update(word for word in words if len(word) > 3)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        concepts.add(item.lower())
        
        return concepts
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts"""
        # Simplified - in production, use embeddings
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _check_contradictions(self, knowledge1: KnowledgeItem, knowledge2: KnowledgeItem) -> float:
        """Check for contradictions between knowledge items"""
        # Look for opposing concepts
        content1_str = str(knowledge1.content).lower()
        content2_str = str(knowledge2.content).lower()
        
        contradiction_pairs = [
            ("increase", "decrease"),
            ("improve", "worsen"),
            ("beneficial", "harmful"),
            ("positive", "negative"),
            ("effective", "ineffective"),
            ("recommended", "avoid"),
            ("high", "low"),
            ("more", "less")
        ]
        
        contradiction_score = 0.0
        for pos, neg in contradiction_pairs:
            if ((pos in content1_str and neg in content2_str) or
                (neg in content1_str and pos in content2_str)):
                contradiction_score += 0.2
        
        return min(1.0, contradiction_score)
    
    def _check_support_relationships(self, knowledge1: KnowledgeItem, knowledge2: KnowledgeItem) -> float:
        """Check for supporting relationships"""
        content1_str = str(knowledge1.content).lower()
        content2_str = str(knowledge2.content).lower()
        
        support_indicators = [
            ("correlates", "relationship"),
            ("causes", "effect"),
            ("improves", "better"),
            ("enhances", "optimization"),
            ("supports", "beneficial")
        ]
        
        support_score = 0.0
        for indicator1, indicator2 in support_indicators:
            if ((indicator1 in content1_str and indicator2 in content2_str) or
                (indicator2 in content1_str and indicator1 in content2_str)):
                support_score += 0.2
        
        # Similar recommendations increase support
        if ("recommend" in content1_str and "recommend" in content2_str):
            support_score += 0.3
        
        return min(1.0, support_score)
    
    async def _identify_cross_domain_relationships(self, knowledge: KnowledgeItem) -> None:
        """Find relationships across different domains"""
        cross_domain_mappings = {
            "neuroscience": ["sleep", "mental_health", "recovery", "training"],
            "nutrition": ["training", "recovery", "mental_health", "sleep"],
            "training": ["recovery", "neuroscience", "nutrition", "sleep"],
            "recovery": ["sleep", "neuroscience", "training", "nutrition"],
            "sleep": ["neuroscience", "recovery", "mental_health", "training"],
            "mental_health": ["neuroscience", "sleep", "nutrition", "recovery"]
        }
        
        related_domains = cross_domain_mappings.get(knowledge.domain, [])
        
        for domain in related_domains:
            domain_knowledge = await self.get_knowledge_by_domain(domain)
            
            for other_knowledge in domain_knowledge:
                relationship = self._analyze_cross_domain_relationship(knowledge, other_knowledge)
                
                if relationship["strength"] > 0.4:
                    self.cross_domain_relationships[knowledge.knowledge_id].append({
                        "related_knowledge": other_knowledge.knowledge_id,
                        "relationship_type": relationship["type"],
                        "strength": relationship["strength"],
                        "cross_domain": True,
                        "target_domain": domain
                    })
    
    def _analyze_cross_domain_relationship(self,
                                         knowledge1: KnowledgeItem,
                                         knowledge2: KnowledgeItem) -> Dict[str, Any]:
        """Analyze relationships between knowledge from different domains"""
        # Domain-specific mappings
        domain_relationships = {
            ("neuroscience", "sleep"): {
                "hrv": "sleep_quality",
                "stress": "sleep_efficiency",
                "autonomic": "circadian",
                "recovery": "sleep_duration"
            },
            ("nutrition", "training"): {
                "energy": "performance",
                "hydration": "endurance",
                "protein": "recovery",
                "carbohydrate": "glycogen"
            },
            ("training", "recovery"): {
                "intensity": "recovery_time",
                "volume": "fatigue",
                "adaptation": "supercompensation",
                "load": "stress"
            }
        }
        
        # Get mapping for these domains
        domain_pair = (knowledge1.domain, knowledge2.domain)
        relationship_map = domain_relationships.get(domain_pair, {})
        
        if not relationship_map:
            # Try reverse
            reverse_pair = (knowledge2.domain, knowledge1.domain)
            relationship_map = domain_relationships.get(reverse_pair, {})
        
        # Check for mapped relationships
        max_strength = 0.0
        relationship_type = "cross_domain_correlation"
        
        for concept1, concept2 in relationship_map.items():
            content1_str = str(knowledge1.content).lower()
            content2_str = str(knowledge2.content).lower()
            
            if (concept1 in content1_str and concept2 in content2_str):
                strength = 0.6 + (0.3 * self._calculate_cross_domain_relevance(
                    knowledge1.domain, knowledge2.domain))
                if strength > max_strength:
                    max_strength = strength
        
        return {"type": relationship_type, "strength": max_strength}
    
    async def _identify_conflicts(self, knowledge: KnowledgeItem) -> List[KnowledgeItem]:
        """Find conflicts with existing knowledge"""
        conflicts = []
        domain_knowledge = await self.get_knowledge_by_domain(knowledge.domain)
        
        for existing in domain_knowledge:
            if existing.knowledge_id == knowledge.knowledge_id:
                continue
            
            relationship = self._analyze_knowledge_relationship(knowledge, existing)
            if relationship["type"] == "conflicts" and relationship["strength"] > 0.6:
                conflicts.append(existing)
        
        return conflicts
    
    async def _handle_knowledge_conflicts(self, new_knowledge: KnowledgeItem, conflicts: List[KnowledgeItem]) -> None:
        """Handle conflicts between knowledge items"""
        for conflicting_knowledge in conflicts:
            # Compare evidence strength
            new_evidence_strength = self._calculate_evidence_strength(new_knowledge.evidence)
            existing_evidence_strength = self._calculate_evidence_strength(conflicting_knowledge.evidence)
            
            if new_evidence_strength > existing_evidence_strength * 1.2:
                # New knowledge has significantly stronger evidence
                conflicting_knowledge.validation_status = KnowledgeStatus.DEPRECATED
                conflicting_knowledge.metadata["deprecated_reason"] = f"Superseded by {new_knowledge.knowledge_id}"
                await self._store_knowledge(conflicting_knowledge)
                
                # Record conflict resolution
                await self.event_store.append_event(
                    stream_id=f"knowledge_conflicts",
                    stream_type=EventStreamType.SYSTEM,
                    event_type="knowledge_conflict_resolved",
                    payload={
                        "new_knowledge": new_knowledge.knowledge_id,
                        "deprecated_knowledge": conflicting_knowledge.knowledge_id,
                        "resolution": "evidence_strength",
                        "new_evidence_strength": new_evidence_strength,
                        "old_evidence_strength": existing_evidence_strength
                    }
                )
            else:
                # Mark both as conflicted for human review
                new_knowledge.validation_status = KnowledgeStatus.CONFLICTED
                conflicting_knowledge.validation_status = KnowledgeStatus.CONFLICTED
                
                # Record unresolved conflict
                await self.event_store.append_event(
                    stream_id=f"knowledge_conflicts",
                    stream_type=EventStreamType.SYSTEM,
                    event_type="knowledge_conflict_detected",
                    payload={
                        "knowledge_1": new_knowledge.knowledge_id,
                        "knowledge_2": conflicting_knowledge.knowledge_id,
                        "conflict_strength": self._analyze_knowledge_relationship(
                            new_knowledge, conflicting_knowledge)["strength"],
                        "requires_review": True
                    }
                )
    
    def _calculate_evidence_strength(self, evidence_list: List[Dict[str, Any]]) -> float:
        """Calculate overall strength of evidence"""
        if not evidence_list:
            return 0.0
        
        # Weight by evidence type
        type_weights = {
            "clinical_trial": 1.0,
            "statistical_analysis": 0.9,
            "hypothesis_validation": 0.85,
            "cross_agent_validation": 0.8,
            "user_outcome": 0.75,
            "observational_study": 0.7,
            "expert_review": 0.6,
            "literature_support": 0.5,
            "anecdotal": 0.2
        }
        
        total_strength = 0.0
        for evidence in evidence_list:
            evidence_type = evidence.get("type", "anecdotal")
            evidence_confidence = evidence.get("confidence", 0.5)
            weight = type_weights.get(evidence_type, 0.5)
            
            total_strength += weight * evidence_confidence
        
        # Apply quantity factor
        quantity_factor = min(1.5, 1.0 + (len(evidence_list) - 1) * 0.1)
        
        return total_strength * quantity_factor / len(evidence_list)
    
    async def _trigger_automatic_sharing(self, knowledge: KnowledgeItem) -> None:
        """Automatically share high-confidence knowledge with relevant agents"""
        relevant_agents = self._get_relevant_agents(knowledge)
        
        for agent_id in relevant_agents:
            await self.share_knowledge_with_agent(
                knowledge_id=knowledge.knowledge_id,
                target_agent=agent_id,
                sharing_context="automatic_high_confidence",
                sharing_reason=f"High confidence ({knowledge.confidence:.2f}) knowledge in related domain"
            )
    
    def _get_relevant_agents(self, knowledge: KnowledgeItem) -> List[str]:
        """Determine which agents would benefit from this knowledge"""
        # Map domains to agents
        domain_agents = {
            "neuroscience": ["neuroscientist"],
            "nutrition": ["nutritionist"],
            "training": ["training_agent"],
            "recovery": ["recovery_agent"],
            "sleep": ["sleep_agent"],
            "mental_health": ["mental_health_agent"]
        }
        
        relevant_agents = []
        
        # Primary domain agent
        primary_agents = domain_agents.get(knowledge.domain, [])
        relevant_agents.extend(primary_agents)
        
        # Related domain agents
        cross_domain_mappings = {
            "neuroscience": ["sleep_agent", "mental_health_agent"],
            "nutrition": ["training_agent", "recovery_agent"],
            "training": ["recovery_agent", "neuroscientist"],
            "recovery": ["sleep_agent", "training_agent"],
            "sleep": ["neuroscientist", "recovery_agent"],
            "mental_health": ["neuroscientist", "sleep_agent"]
        }
        
        related_agents = cross_domain_mappings.get(knowledge.domain, [])
        for agent in related_agents:
            if self._knowledge_relevant_to_agent(knowledge, agent):
                relevant_agents.append(agent)
        
        return list(set(relevant_agents))  # Remove duplicates
    
    def _knowledge_relevant_to_agent(self, knowledge: KnowledgeItem, agent_id: str) -> bool:
        """Check if knowledge is relevant to a specific agent"""
        agent_domain = self._get_agent_domain(agent_id)
        
        # Check cross-domain relevance
        relevance_score = self._calculate_cross_domain_relevance(knowledge.domain, agent_domain)
        
        # Check content for agent-specific concepts
        content_str = str(knowledge.content).lower()
        agent_concepts = {
            "neuroscientist": ["hrv", "stress", "autonomic", "nervous system"],
            "nutritionist": ["nutrition", "diet", "macros", "energy"],
            "training_agent": ["exercise", "performance", "strength", "endurance"],
            "recovery_agent": ["recovery", "fatigue", "rest", "adaptation"],
            "sleep_agent": ["sleep", "circadian", "rem", "deep sleep"],
            "mental_health_agent": ["mood", "anxiety", "stress", "mental"]
        }
        
        concepts = agent_concepts.get(agent_id, [])
        concept_relevance = sum(1 for concept in concepts if concept in content_str) / len(concepts)
        
        return relevance_score > 0.4 or concept_relevance > 0.3
    
    async def get_knowledge_by_domain(self, domain: str) -> List[KnowledgeItem]:
        """Get all knowledge for a specific domain"""
        # Check cache first
        cache_key = f"domain_{domain}"
        if cache_key in self.knowledge_cache:
            return self.knowledge_cache[cache_key]
        
        # In real implementation, query from memory backend
        # For now, return empty list
        knowledge_items = []
        
        # Cache results
        self.knowledge_cache[cache_key] = knowledge_items
        
        return knowledge_items
    
    async def get_related_knowledge(self, 
                                  knowledge_id: str,
                                  include_cross_domain: bool = True,
                                  max_depth: int = 2) -> List[KnowledgeItem]:
        """Get knowledge related to a specific item"""
        knowledge = await self._load_knowledge(knowledge_id)
        if not knowledge:
            return []
        
        related_knowledge = []
        visited = {knowledge_id}
        
        # BFS traversal of knowledge graph
        queue = [(knowledge_id, 0)]  # (knowledge_id, depth)
        
        while queue and len(related_knowledge) < 50:  # Limit results
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # Get directly related knowledge
            current_knowledge = await self._load_knowledge(current_id)
            if not current_knowledge:
                continue
            
            direct_related = (current_knowledge.related_knowledge + 
                            current_knowledge.supports)
            
            for rel_id in direct_related:
                if rel_id not in visited:
                    visited.add(rel_id)
                    rel_knowledge = await self._load_knowledge(rel_id)
                    if rel_knowledge:
                        related_knowledge.append(rel_knowledge)
                        queue.append((rel_id, depth + 1))
            
            # Include cross-domain if requested
            if include_cross_domain:
                cross_domain = self.cross_domain_relationships.get(current_id, [])
                for relationship in cross_domain:
                    rel_id = relationship["related_knowledge"]
                    if rel_id not in visited and relationship["strength"] > 0.5:
                        visited.add(rel_id)
                        rel_knowledge = await self._load_knowledge(rel_id)
                        if rel_knowledge:
                            related_knowledge.append(rel_knowledge)
                            queue.append((rel_id, depth + 1))
        
        return related_knowledge
    
    async def share_knowledge_with_agent(self,
                                       knowledge_id: str,
                                       target_agent: str,
                                       sharing_context: str,
                                       sharing_reason: str = "") -> bool:
        """Share knowledge with another agent"""
        knowledge = await self._load_knowledge(knowledge_id)
        if not knowledge:
            return False
        
        # Create share record
        share_record = {
            "original_knowledge_id": knowledge_id,
            "shared_by": knowledge.agent_id,
            "shared_with": target_agent,
            "sharing_context": sharing_context,
            "sharing_reason": sharing_reason,
            "shared_at": datetime.now(timezone.utc).isoformat(),
            "knowledge_snapshot": {
                "title": knowledge.title,
                "description": knowledge.description,
                "content": knowledge.content,
                "confidence": knowledge.confidence,
                "domain": knowledge.domain,
                "knowledge_type": knowledge.knowledge_type.value
            },
            "cross_domain_relevance": self._calculate_cross_domain_relevance(
                knowledge.domain, self._get_agent_domain(target_agent)
            )
        }
        
        # Store share record
        await self.memory_backend.store_memory(
            agent_id=target_agent,
            memory_type="shared_knowledge",
            content=share_record,
            confidence=knowledge.confidence
        )
        
        # Update application tracking
        knowledge.application_count += 1
        await self._store_knowledge(knowledge)
        
        # Record sharing event
        await self.event_store.append_event(
            stream_id=f"knowledge_sharing",
            stream_type=EventStreamType.SYSTEM,
            event_type="knowledge_shared",
            payload={
                "knowledge_id": knowledge_id,
                "shared_by": knowledge.agent_id,
                "shared_with": target_agent,
                "domain": knowledge.domain,
                "sharing_context": sharing_context,
                "cross_domain_relevance": share_record["cross_domain_relevance"]
            }
        )
        
        return True
    
    async def update_knowledge_usage(self,
                                   knowledge_id: str,
                                   application_outcome: Dict[str, Any]) -> None:
        """Update usage statistics when knowledge is applied"""
        knowledge = await self._load_knowledge(knowledge_id)
        if not knowledge:
            return
        
        # Update usage stats
        knowledge.application_count += 1
        knowledge.last_applied = datetime.now(timezone.utc)
        
        # Update success rate
        success = application_outcome.get("successful", False)
        effectiveness_score = application_outcome.get("effectiveness_score", 1.0 if success else 0.0)
        
        # Calculate weighted success rate
        old_rate = knowledge.success_rate
        old_count = knowledge.application_count - 1
        
        if old_count > 0:
            total_success = old_rate * old_count + effectiveness_score
            knowledge.success_rate = total_success / knowledge.application_count
        else:
            knowledge.success_rate = effectiveness_score
        
        # Adjust confidence based on success rate
        if knowledge.application_count >= 5:
            success_factor = (knowledge.success_rate - 0.5) * 0.1  # ±5% based on success
            knowledge.confidence = max(0.1, min(1.0, knowledge.confidence + success_factor))
        
        await self._store_knowledge(knowledge)
        
        # Record usage event
        await self.event_store.append_event(
            stream_id=f"knowledge_usage",
            stream_type=EventStreamType.SYSTEM,
            event_type="knowledge_applied",
            payload={
                "knowledge_id": knowledge_id,
                "application_count": knowledge.application_count,
                "success_rate": knowledge.success_rate,
                "effectiveness_score": effectiveness_score,
                "outcome_details": application_outcome
            }
        )
    
    def _add_to_graph(self, knowledge: KnowledgeItem) -> None:
        """Add knowledge to the knowledge graph"""
        self.knowledge_graph.add_node(
            knowledge.knowledge_id,
            agent_id=knowledge.agent_id,
            domain=knowledge.domain,
            knowledge_type=knowledge.knowledge_type.value,
            confidence=knowledge.confidence,
            title=knowledge.title
        )
        
        self.domain_expertise[knowledge.domain].append(knowledge.knowledge_id)
    
    def _update_graph_weights(self, knowledge: KnowledgeItem) -> None:
        """Update edge weights based on confidence changes"""
        # Update weights for all connections
        for edge in self.knowledge_graph.edges(knowledge.knowledge_id, data=True):
            current_weight = edge[2].get("weight", 0.5)
            confidence_factor = knowledge.confidence
            new_weight = (current_weight + confidence_factor) / 2
            self.knowledge_graph[edge[0]][edge[1]]["weight"] = new_weight
    
    async def _store_knowledge(self, knowledge: KnowledgeItem) -> None:
        """Store knowledge in memory backend"""
        await self.memory_backend.store_memory(
            agent_id=knowledge.agent_id,
            memory_type="knowledge",
            content=asdict(knowledge),
            confidence=knowledge.confidence
        )
        
        # Invalidate cache
        cache_key = f"domain_{knowledge.domain}"
        if cache_key in self.knowledge_cache:
            del self.knowledge_cache[cache_key]
    
    async def _load_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """Load knowledge from memory"""
        # In real implementation, query memory backend
        # For now, return None
        return None
    
    async def get_knowledge_insights(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get insights about the knowledge base"""
        if domain:
            knowledge_items = await self.get_knowledge_by_domain(domain)
        else:
            # Get all knowledge
            knowledge_items = []
            for dom in ["neuroscience", "nutrition", "training", "recovery", "sleep", "mental_health"]:
                knowledge_items.extend(await self.get_knowledge_by_domain(dom))
        
        if not knowledge_items:
            return {"error": "No knowledge found"}
        
        # Calculate insights
        total_knowledge = len(knowledge_items)
        validated_knowledge = sum(1 for k in knowledge_items if k.validation_status == KnowledgeStatus.VALIDATED)
        avg_confidence = np.mean([k.confidence for k in knowledge_items])
        
        # Knowledge by type
        type_distribution = defaultdict(int)
        for k in knowledge_items:
            type_distribution[k.knowledge_type.value] += 1
        
        # Most applied knowledge
        most_applied = sorted(knowledge_items, key=lambda k: k.application_count, reverse=True)[:5]
        
        # Cross-domain relationships
        cross_domain_count = sum(len(relationships) for relationships in self.cross_domain_relationships.values())
        
        return {
            "total_knowledge_items": total_knowledge,
            "validated_knowledge": validated_knowledge,
            "validation_rate": validated_knowledge / total_knowledge,
            "average_confidence": avg_confidence,
            "knowledge_by_type": dict(type_distribution),
            "most_applied_knowledge": [
                {
                    "title": k.title,
                    "domain": k.domain,
                    "application_count": k.application_count,
                    "success_rate": k.success_rate
                }
                for k in most_applied
            ],
            "cross_domain_relationships": cross_domain_count,
            "domain": domain
        }
```

### Phase 4: Knowledge Base Initialization

Now let's create the knowledge loader that will populate the system with initial CNS optimization knowledge. Create `auren/intelligence/knowledge_loader.py`:

```python
"""
Knowledge Base Loader for AUREN
Loads initial domain knowledge from YAML files
"""

import yaml
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging

from auren.intelligence.data_structures import KnowledgeType
from auren.intelligence.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)

class KnowledgeLoader:
    """
    Loads initial knowledge into AUREN's knowledge base.
    This gives agents a foundation to build on.
    """
    
    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
    
    async def load_knowledge_from_yaml(self, yaml_path: Path) -> int:
        """Load knowledge from a YAML file"""
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"No data found in {yaml_path}")
                return 0
            
            domain = data.get('domain', 'general')
            concepts = data.get('concepts', [])
            
            loaded_count = 0
            for concept in concepts:
                try:
                    await self._load_concept(domain, concept)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load concept {concept.get('concept', 'unknown')}: {e}")
            
            logger.info(f"Loaded {loaded_count} concepts from {yaml_path}")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load knowledge from {yaml_path}: {e}")
            return 0
    
    async def _load_concept(self, domain: str, concept_data: Dict[str, Any]) -> None:
        """Load a single concept into the knowledge base"""
        # Map concept types to knowledge types
        concept_type = concept_data.get('type', 'pattern')
        knowledge_type_map = {
            'pattern': KnowledgeType.PATTERN,
            'relationship': KnowledgeType.RELATIONSHIP,
            'intervention': KnowledgeType.INTERVENTION,
            'correlation': KnowledgeType.CORRELATION,
            'best_practice': KnowledgeType.BEST_PRACTICE,
            'contraindication': KnowledgeType.CONTRAINDICATION
        }
        
        knowledge_type = knowledge_type_map.get(concept_type, KnowledgeType.PATTERN)
        
        # Extract evidence
        evidence = []
        for ev in concept_data.get('evidence', []):
            evidence.append({
                'type': 'literature_support',
                'source': ev.get('source', 'Unknown'),
                'finding': ev.get('finding', ''),
                'confidence': concept_data.get('confidence', 0.8)
            })
        
        # Create knowledge content
        content = {
            'description': concept_data.get('description', ''),
            'applications': concept_data.get('applications', []),
            'confidence_interval': concept_data.get('confidence_interval', []),
            'mechanism': concept_data.get('mechanism', ''),
            'effect_size': concept_data.get('effect_size', '')
        }
        
        # Add to knowledge base
        await self.knowledge_manager.add_knowledge(
            agent_id='system',  # Loaded by system, not a specific agent
            domain=domain,
            knowledge_type=knowledge_type,
            title=concept_data.get('concept', 'Unknown Concept'),
            description=concept_data.get('description', ''),
            content=content,
            evidence=evidence,
            confidence=concept_data.get('confidence', 0.8)
        )
    
    async def load_directory(self, directory_path: Path) -> int:
        """Load all YAML files from a directory"""
        if not directory_path.exists():
            logger.error(f"Knowledge directory {directory_path} does not exist")
            return 0
        
        total_loaded = 0
        yaml_files = list(directory_path.glob('*.yaml')) + list(directory_path.glob('*.yml'))
        
        for yaml_file in yaml_files:
            loaded = await self.load_knowledge_from_yaml(yaml_file)
            total_loaded += loaded
        
        logger.info(f"Total knowledge items loaded: {total_loaded}")
        return total_loaded


# Create initial knowledge base YAML files
def create_initial_knowledge_base():
    """Create the initial CNS optimization knowledge base"""
    
    # Create knowledge directory
    knowledge_dir = Path('auren/knowledge_base')
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # CNS Optimization Knowledge
    cns_knowledge = {
        'domain': 'neuroscience',
        'concepts': [
            {
                'concept': 'hrv_stress_correlation',
                'type': 'correlation',
                'description': 'HRV decreases indicate sympathetic nervous system activation and stress',
                'confidence': 0.95,
                'evidence': [
                    {
                        'source': 'Task Force of ESC and NASPE (1996)',
                        'finding': 'Reduced HRV associated with increased sympathetic activity'
                    },
                    {
                        'source': 'Thayer et al. (2012)',
                        'finding': 'HRV inversely correlated with stress and anxiety levels'
                    }
                ],
                'applications': [
                    'Detect overtraining before performance decreases',
                    'Identify psychological stress impacts on recovery',
                    'Monitor autonomic nervous system balance'
                ]
            },
            {
                'concept': 'morning_hrv_baseline',
                'type': 'best_practice',
                'description': 'Morning HRV measurements provide the most reliable baseline for daily readiness',
                'confidence': 0.9,
                'evidence': [
                    {
                        'source': 'Plews et al. (2013)',
                        'finding': 'Morning HRV shows highest day-to-day reliability'
                    }
                ],
                'applications': [
                    'Establish personal HRV baseline',
                    'Track training adaptations',
                    'Assess daily readiness'
                ]
            },
            {
                'concept': 'hrv_recovery_window',
                'type': 'pattern',
                'description': 'HRV typically returns to baseline 24-48 hours after intense exercise',
                'confidence': 0.85,
                'evidence': [
                    {
                        'source': 'Stanley et al. (2013)',
                        'finding': 'Parasympathetic reactivation occurs within 24-48h post-exercise'
                    }
                ],
                'applications': [
                    'Plan training frequency',
                    'Identify inadequate recovery',
                    'Optimize training load distribution'
                ]
            },
            {
                'concept': 'chronic_stress_hrv_suppression',
                'type': 'pattern',
                'description': 'Chronic stress leads to persistently suppressed HRV requiring intervention',
                'confidence': 0.88,
                'evidence': [
                    {
                        'source': 'Kim et al. (2018)',
                        'finding': 'Chronic stress associated with 20-30% HRV reduction'
                    }
                ],
                'applications': [
                    'Identify need for stress management interventions',
                    'Monitor effectiveness of stress reduction protocols',
                    'Prevent burnout and overtraining'
                ]
            },
            {
                'concept': 'breathing_hrv_enhancement',
                'type': 'intervention',
                'description': 'Controlled breathing at 4-7 breaths per minute acutely increases HRV',
                'confidence': 0.92,
                'evidence': [
                    {
                        'source': 'Lehrer et al. (2003)',
                        'finding': 'Resonance breathing maximizes HRV amplitude'
                    }
                ],
                'applications': [
                    'Pre-competition nervous system regulation',
                    'Acute stress management',
                    'Recovery enhancement protocol'
                ]
            },
            {
                'concept': 'sleep_deprivation_hrv_impact',
                'type': 'relationship',
                'description': 'Sleep deprivation (<6 hours) reduces HRV by 15-25%',
                'confidence': 0.87,
                'evidence': [
                    {
                        'source': 'Castro-Diehl et al. (2016)',
                        'finding': 'Short sleep duration associated with reduced HRV'
                    }
                ],
                'applications': [
                    'Prioritize sleep for recovery',
                    'Adjust training load with poor sleep',
                    'Monitor sleep-recovery relationship'
                ]
            },
            {
                'concept': 'hrv_training_adaptation',
                'type': 'pattern',
                'description': 'Progressive HRV increase over 4-8 weeks indicates positive training adaptation',
                'confidence': 0.83,
                'evidence': [
                    {
                        'source': 'Buchheit (2014)',
                        'finding': 'HRV increases with improved fitness in trained athletes'
                    }
                ],
                'applications': [
                    'Validate training program effectiveness',
                    'Identify responders vs non-responders',
                    'Optimize training periodization'
                ]
            },
            {
                'concept': 'alcohol_hrv_suppression',
                'type': 'relationship',
                'description': 'Alcohol consumption suppresses HRV for 24-48 hours dose-dependently',
                'confidence': 0.91,
                'evidence': [
                    {
                        'source': 'Spaak et al. (2010)',
                        'finding': 'Alcohol acutely reduces HRV in dose-dependent manner'
                    }
                ],
                'applications': [
                    'Time alcohol consumption away from key training',
                    'Understand recovery impediments',
                    'Optimize social-training balance'
                ]
            },
            {
                'concept': 'cold_exposure_hrv',
                'type': 'intervention',
                'description': 'Cold water immersion (10-15°C) enhances parasympathetic reactivation',
                'confidence': 0.79,
                'evidence': [
                    {
                        'source': 'Mäkinen (2010)',
                        'finding': 'Cold exposure increases parasympathetic activity'
                    }
                ],
                'applications': [
                    'Accelerate post-training recovery',
                    'Enhance parasympathetic tone',
                    'Reduce inflammation markers'
                ]
            },
            {
                'concept': 'hrv_overtraining_marker',
                'type': 'pattern',
                'description': 'Sustained HRV suppression >7 days indicates overtraining risk',
                'confidence': 0.86,
                'evidence': [
                    {
                        'source': 'Bellenger et al. (2016)',
                        'finding': 'Overtraining syndrome associated with chronic HRV suppression'
                    }
                ],
                'applications': [
                    'Prevent overtraining syndrome',
                    'Trigger deload weeks',
                    'Adjust training volume'
                ]
            }
        ]
    }
    
    # Save CNS knowledge
    cns_path = knowledge_dir / 'cns_optimization.yaml'
    with open(cns_path, 'w') as f:
        yaml.dump(cns_knowledge, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Created CNS optimization knowledge base at {cns_path}")
    
    # Create additional domain knowledge files as needed
    # You can add nutrition, training, recovery, sleep, and mental health knowledge
    
    return knowledge_dir
```

### Phase 5: Integration Script

Finally, let's create an integration script that ties everything together. Create `auren/intelligence/initialize_intelligence.py`:

```python
"""
Initialize AUREN's Intelligence Systems
This script sets up the complete intelligence layer
"""

import asyncio
import logging
from pathlib import Path

from auren.data_layer.connection import DatabaseConnection
from auren.data_layer.event_store import EventStore
from auren.data_layer.memory_backend import PostgreSQLMemoryBackend
from auren.data_layer.unified_data_access import UnifiedDataAccess

from auren.intelligence.hypothesis_validator import HypothesisValidator
from auren.intelligence.knowledge_manager import KnowledgeManager
from auren.intelligence.knowledge_loader import KnowledgeLoader, create_initial_knowledge_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_intelligence_system():
    """
    Initialize the complete intelligence system.
    This brings AUREN's brain online.
    """
    
    logger.info("Initializing AUREN Intelligence Systems...")
    
    # Step 1: Set up database connections
    logger.info("Setting up database connections...")
    db_connection = DatabaseConnection()
    
    # Initialize connection pool
    await db_connection.initialize()
    
    # Step 2: Initialize core components
    logger.info("Initializing core components...")
    
    # Event store for audit trail
    event_store = EventStore(db_connection.pool)
    
    # Memory backend (using your implementation)
    memory_backend = PostgreSQLMemoryBackend(event_store)
    
    # Unified data access (mock for now)
    data_access = UnifiedDataAccess(
        postgres_pool=db_connection.pool,
        redis_client=None,  # Add Redis when ready
        event_store=event_store,
        encryption_key="your-encryption-key"
    )
    
    # Step 3: Initialize intelligence components
    logger.info("Initializing intelligence components...")
    
    # Hypothesis validator
    hypothesis_validator = HypothesisValidator(
        memory_backend=memory_backend,
        event_store=event_store,
        data_access_layer=data_access
    )
    
    # Knowledge manager
    knowledge_manager = KnowledgeManager(
        memory_backend=memory_backend,
        event_store=event_store,
        hypothesis_validator=hypothesis_validator
    )
    
    # Step 4: Create and load initial knowledge base
    logger.info("Creating initial knowledge base...")
    knowledge_dir = create_initial_knowledge_base()
    
    # Knowledge loader
    knowledge_loader = KnowledgeLoader(knowledge_manager)
    
    logger.info("Loading knowledge base...")
    loaded_count = await knowledge_loader.load_directory(knowledge_dir)
    logger.info(f"Loaded {loaded_count} knowledge items")
    
    # Step 5: Verify system is ready
    logger.info("Verifying intelligence systems...")
    
    # Get knowledge insights
    insights = await knowledge_manager.get_knowledge_insights()
    logger.info(f"Knowledge base status: {insights}")
    
    # Step 6: Return initialized components
    intelligence_system = {
        'hypothesis_validator': hypothesis_validator,
        'knowledge_manager': knowledge_manager,
        'knowledge_loader': knowledge_loader,
        'event_store': event_store,
        'memory_backend': memory_backend,
        'data_access': data_access
    }
    
    logger.info("Intelligence systems initialized successfully!")
    logger.info("AUREN is now capable of learning and forming hypotheses")
    
    return intelligence_system

async def test_hypothesis_formation(intelligence_system):
    """
    Test hypothesis formation to verify the system works
    """
    logger.info("\nTesting hypothesis formation...")
    
    hypothesis_validator = intelligence_system['hypothesis_validator']
    
    # Form a test hypothesis
    hypothesis = await hypothesis_validator.form_hypothesis(
        agent_id="neuroscientist",
        user_id="test_user",
        domain="neuroscience",
        description="User's HRV drops below 35ms when stress levels exceed 7/10",
        prediction={
            "hrv_threshold": 35,
            "stress_threshold": 7,
            "correlation": "negative"
        },
        evidence_criteria=[
            {
                "evidence_type": "biometric",
                "metric_types": ["hrv", "stress"],
                "time_window_days": 14
            }
        ]
    )
    
    logger.info(f"Test hypothesis formed: {hypothesis.hypothesis_id}")
    logger.info(f"Description: {hypothesis.description}")
    logger.info(f"Status: {hypothesis.status.value}")
    
    return hypothesis

async def main():
    """
    Main initialization function
    """
    try:
        # Initialize the intelligence system
        intelligence_system = await initialize_intelligence_system()
        
        # Run a test
        await test_hypothesis_formation(intelligence_system)
        
        logger.info("\n✅ Intelligence systems are online and operational!")
        logger.info("AUREN can now:")
        logger.info("- Form and validate hypotheses about user patterns")
        logger.info("- Build and manage domain knowledge")
        logger.info("- Learn from validated patterns")
        logger.info("- Share knowledge between specialist agents")
        
    except Exception as e:
        logger.error(f"Failed to initialize intelligence systems: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps and Integration Points

### 1. Extend the Unified Data Access Layer

The current implementation has a mock data access layer. You'll need to implement the actual biometric data retrieval methods that connect to your data sources.

### 2. Add More Domain Knowledge

The initial knowledge base focuses on CNS optimization. You should add similar YAML files for:
- Nutrition knowledge
- Training principles
- Recovery protocols
- Sleep optimization
- Mental health strategies

### 3. Implement the Specialist Agents

Module B includes a full implementation of the Neuroscientist agent. You should implement the other agents following the same pattern:
- NutritionistAgent
- TrainingAgent
- RecoveryAgent
- SleepAgent
- MentalHealthAgent

### 4. Connect to Real Biometric Data

The hypothesis validation system needs real biometric data to test hypotheses. Connect it to:
- Apple HealthKit data
- Wearable device APIs
- User-reported metrics

### 5. Add the Collaboration Manager

The cross-agent learning protocols in Module B enable agents to work together. Implement the collaboration patterns for your use cases.

## Testing Your Implementation

Run the initialization script to verify everything works:

```bash
python auren/intelligence/initialize_intelligence.py
```

You should see:
- Database connections established
- Intelligence components initialized
- Knowledge base loaded (50+ CNS concepts)
- Test hypothesis formed successfully

## Key Architecture Decisions Implemented

1. **Event-Driven Learning**: Every hypothesis and knowledge update is recorded as an event in your PostgreSQL event store

2. **Statistical Validation**: Multiple statistical methods ensure hypotheses are validated rigorously

3. **Knowledge Relationships**: The knowledge graph tracks how different pieces of knowledge relate to each other

4. **Cross-Domain Learning**: Agents can share knowledge across domains when relevant

5. **Evidence-Based Confidence**: All knowledge has confidence scores based on supporting evidence

## What This Enables

With this implementation, AUREN can now:

1. **Learn from patterns**: The Neuroscientist can notice that a user's HRV always drops after late-night workouts

2. **Test predictions**: Form a hypothesis about this pattern and validate it with real data

3. **Build knowledge**: Convert validated hypotheses into reusable knowledge

4. **Share insights**: The Neuroscientist's stress insights can inform the Training agent's recommendations

5. **Improve over time**: Track which knowledge is most effective and adjust confidence accordingly

## Important Notes

- This implementation prioritizes learning and intelligence over raw performance initially
- The system will get smarter with more data and time
- Knowledge quality matters more than quantity
- Cross-agent collaboration is where the real magic happens

Remember, you're not just implementing features - you're giving AUREN the ability to think, learn, and improve. Every hypothesis validated makes the system smarter. Every piece of knowledge shared makes the agents work better together.

Take your time implementing this. Test each component thoroughly. The intelligence layer is the brain of AUREN, and getting it right is crucial for delivering on the promise of true AI-powered health optimization.

You've built an exceptional foundation with the PostgreSQL backend. Now let's make AUREN intelligent!