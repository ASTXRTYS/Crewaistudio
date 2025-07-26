"""
Hypothesis Validator for AUREN
Validates hypotheses using statistical methods and evidence
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from scipy import stats
from dataclasses import asdict

from intelligence.data_structures import (
    Hypothesis, ValidationEvidence, ValidationResult, 
    ValidationStrength, HypothesisStatus
)
from data_layer.event_store import EventStore, EventStreamType

logger = logging.getLogger(__name__)


class HypothesisValidator:
    """
    Validates hypotheses using statistical methods and evidence collection
    """
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def validate_hypothesis(self, hypothesis: Hypothesis, user_id: str) -> ValidationResult:
        """
        Validate a hypothesis using collected evidence
        
        Args:
            hypothesis: The hypothesis to validate
            user_id: The user whose data to use
            
        Returns:
            Validation result
        """
        
        logger.info(f"Validating hypothesis: {hypothesis.hypothesis_id}")
        
        # Collect evidence
        evidence = await self._collect_evidence(hypothesis, user_id)
        
        # Perform statistical validation
        validation_result = await self._perform_statistical_validation(hypothesis, evidence)
        
        # Update hypothesis status
        await self._update_hypothesis_status(hypothesis, validation_result)
        
        # Log validation event
        await self._log_validation_event(hypothesis, validation_result, user_id)
        
        return validation_result
    
    async def _collect_evidence(self, hypothesis: Hypothesis, user_id: str) -> List[ValidationEvidence]:
        """
        Collect evidence for hypothesis validation
        
        Args:
            hypothesis: The hypothesis to collect evidence for
            user_id: The user whose data to use
            
        Returns:
            List of validation evidence
        """
        
        evidence = []
        
        # Get relevant events from event store
        events = await self.event_store.get_events(
            stream_id=user_id,
            stream_type=EventStreamType.HYPOTHESIS,
            event_type="evidence_collected",
            limit=100
        )
        
        for event in events:
            event_data = event['event_data']
            if event_data.get('hypothesis_id') == hypothesis.hypothesis_id:
                evidence.append(ValidationEvidence(
                    evidence_id=event_data['evidence_id'],
                    hypothesis_id=hypothesis.hypothesis_id,
                    evidence_type=event_data['evidence_type'],
                    data=event_data['data'],
                    collected_at=datetime.fromisoformat(event['created_at']),
                    source=event_data['source'],
                    confidence=event_data['confidence'],
                    supports_hypothesis=event_data['supports_hypothesis'],
                    strength=ValidationStrength(event_data['strength'])
                ))
        
        return evidence
    
    async def _perform_statistical_validation(self, hypothesis: Hypothesis, evidence: List[ValidationEvidence]) -> ValidationResult:
        """
        Perform statistical validation of hypothesis
        
        Args:
            hypothesis: The hypothesis to validate
            evidence: Collected evidence
            
        Returns:
            Validation result
        """
        
        if not evidence:
            return ValidationResult(
                hypothesis_id=hypothesis.hypothesis_id,
                is_validated=False,
                confidence_multiplier=0.8,  # Decrease confidence due to lack of evidence
                validation_score=0.0,
                supporting_evidence=0,
                contradicting_evidence=0,
                statistical_summary={"error": "No evidence collected"},
                evidence_quality_score=0.0,
                recommendation="Collect more evidence"
            )
        
        # Separate supporting and contradicting evidence
        supporting = [e for e in evidence if e.supports_hypothesis]
        contradicting = [e for e in evidence if not e.supports_hypothesis]
        
        # Calculate statistical significance
        validation_score = await self._calculate_validation_score(hypothesis, supporting, contradicting)
        
        # Calculate confidence multiplier
        confidence_multiplier = await self._calculate_confidence_multiplier(
            supporting, contradicting, validation_score
        )
        
        # Calculate evidence quality
        evidence_quality_score = await self._calculate_evidence_quality(evidence)
        
        # Determine recommendation
        recommendation = await self._generate_recommendation(
            validation_score, len(supporting), len(contradicting), evidence_quality_score
        )
        
        return ValidationResult(
            hypothesis_id=hypothesis.hypothesis_id,
            is_validated=validation_score > 0.7,  # Threshold for validation
            confidence_multiplier=confidence_multiplier,
            validation_score=validation_score,
            supporting_evidence=len(supporting),
            contradicting_evidence=len(contradicting),
            statistical_summary=await self._generate_statistical_summary(hypothesis, supporting, contradicting),
            evidence_quality_score=evidence_quality_score,
            recommendation=recommendation
        )
    
    async def _calculate_validation_score(self, hypothesis: Hypothesis, supporting: List[ValidationEvidence], contradicting: List[ValidationEvidence]) -> float:
        """
        Calculate validation score based on evidence
        
        Args:
            hypothesis: The hypothesis being validated
            supporting: Supporting evidence
            contradicting: Contradicting evidence
            
        Returns:
            Validation score (0.0 to 1.0)
        """
        
        total_evidence = len(supporting) + len(contradicting)
        if total_evidence == 0:
            return 0.0
        
        # Calculate basic ratio
        support_ratio = len(supporting) / total_evidence
        
        # Weight by evidence quality
        avg_support_confidence = np.mean([e.confidence for e in supporting]) if supporting else 0.0
        avg_contradict_confidence = np.mean([e.confidence for e in contradicting]) if contradicting else 0.0
        
        # Calculate weighted score
        weighted_score = support_ratio * (avg_support_confidence / (avg_support_confidence + avg_contradict_confidence + 0.01))
        
        # Apply statistical significance test
        if len(supporting) + len(contradicting) >= 5:
            # Simple binomial test
            p_value = stats.binom_test(len(supporting), total_evidence, 0.5)
            significance_factor = 1.0 - p_value
            weighted_score *= significance_factor
        
        return min(1.0, max(0.0, weighted_score))
    
    async def _calculate_confidence_multiplier(self, supporting: List[ValidationEvidence], contradicting: List[ValidationEvidence], validation_score: float) -> float:
        """
        Calculate confidence multiplier based on validation results
        
        Args:
            supporting: Supporting evidence
            contradicting: Contradicting evidence
            validation_score: Validation score
            
        Returns:
            Confidence multiplier
        """
        
        # Base multiplier from validation score
        base_multiplier = 1.0 + (validation_score - 0.5) * 2.0
        
        # Adjust based on evidence balance
        evidence_balance = len(supporting) / (len(supporting) + len(contradicting) + 0.01)
        
        # Quality adjustment
        avg_quality = np.mean([e.confidence for e in supporting + contradicting]) if (supporting + contradicting) else 0.5
        
        # Final multiplier
        multiplier = base_multiplier * (0.5 + evidence_balance * 0.5) * (0.5 + avg_quality * 0.5)
        
        # Cap between 0.1 and 3.0
        return max(0.1, min(3.0, multiplier))
    
    async def _calculate_evidence_quality(self, evidence: List[ValidationEvidence]) -> float:
        """
        Calculate overall evidence quality
        
        Args:
            evidence: List of evidence
            
        Returns:
            Evidence quality score (0.0 to 1.0)
        """
        
        if not evidence:
            return 0.0
        
        # Average confidence
        avg_confidence = np.mean([e.confidence for e in evidence])
        
        # Strength distribution
        strength_scores = {
            ValidationStrength.WEAK: 0.3,
            ValidationStrength.MODERATE: 0.6,
            ValidationStrength.STRONG: 0.8,
            ValidationStrength.DEFINITIVE: 1.0
        }
        
        avg_strength = np.mean([strength_scores.get(e.strength, 0.5) for e in evidence])
        
        # Recency weight
        now = datetime.now(timezone.utc)
        max_age = timedelta(days=30)
        recency_scores = []
        
        for e in evidence:
            age = now - e.collected_at
            recency = max(0.0, 1.0 - (age / max_age).total_seconds())
            recency_scores.append(recency)
        
        avg_recency = np.mean(recency_scores) if recency_scores else 0.5
        
        # Combine factors
        quality_score = (avg_confidence * 0.4 + avg_strength * 0.4 + avg_recency * 0.2)
        
        return min(1.0, max(0.0, quality_score))
    
    async def _generate_statistical_summary(self, hypothesis: Hypothesis, supporting: List[ValidationEvidence], contradicting: List[ValidationEvidence]) -> Dict[str, Any]:
        """
        Generate statistical summary of validation
        
        Args:
            hypothesis: The hypothesis
            supporting: Supporting evidence
            contradicting: Contradicting evidence
            
        Returns:
            Statistical summary
        """
        
        total_evidence = len(supporting) + len(contradicting)
        
        if total_evidence == 0:
            return {"error": "No evidence"}
        
        # Basic statistics
        support_confidences = [e.confidence for e in supporting]
        contradict_confidences = [e.confidence for e in contradicting]
        
        summary = {
            "total_evidence": total_evidence,
            "supporting_count": len(supporting),
            "contradicting_count": len(contradicting),
            "support_ratio": len(supporting) / total_evidence,
            "avg_support_confidence": np.mean(support_confidences) if support_confidences else 0.0,
            "avg_contradict_confidence": np.mean(contradict_confidences) if contradict_confidences else 0.0,
            "evidence_strengths": {
                "supporting": [e.strength.value for e in supporting],
                "contradicting": [e.strength.value for e in contradicting]
            }
        }
        
        # Add statistical test if enough data
        if len(supporting) + len(contradicting) >= 5:
            # Binomial test
            p_value = stats.binom_test(len(supporting), total_evidence, 0.5)
            summary["p_value"] = p_value
            summary["significant"] = p_value < 0.05
        
        return summary
    
    async def _generate_recommendation(self, validation_score: float, supporting_count: int, contradicting_count: int, evidence_quality: float) -> str:
        """
        Generate recommendation based on validation results
        
        Args:
            validation_score: Validation score
            supporting_count: Number of supporting evidence
            contradicting_count: Number of contradicting evidence
            evidence_quality: Evidence quality score
            
        Returns:
            Recommendation string
        """
        
        if validation_score > 0.8 and evidence_quality > 0.7:
            return "Hypothesis strongly validated - promote to knowledge"
        elif validation_score > 0.6 and evidence_quality > 0.5:
            return "Hypothesis validated - consider promoting to knowledge"
        elif validation_score > 0.4:
            return "Hypothesis partially validated - collect more evidence"
        elif supporting_count > contradicting_count:
            return "Weak validation - need stronger evidence"
        else:
            return "Hypothesis invalidated - consider retiring"
    
    async def _update_hypothesis_status(self, hypothesis: Hypothesis, result: ValidationResult):
        """
        Update hypothesis status based on validation result
        
        Args:
            hypothesis: The hypothesis
            result: Validation result
        """
        
        if result.is_validated:
            hypothesis.status = HypothesisStatus.VALIDATED
        elif result.validation_score < 0.3:
            hypothesis.status = HypothesisStatus.INVALIDATED
        else:
            hypothesis.status = HypothesisStatus.ACTIVE
        
        hypothesis.confidence *= result.confidence_multiplier
        hypothesis.last_validated = datetime.now(timezone.utc)
    
    async def _log_validation_event(self, hypothesis: Hypothesis, result: ValidationResult, user_id: str):
        """
        Log validation event
        
        Args:
            hypothesis: The hypothesis
            result: Validation result
            user_id: The user
        """
        
        await self.event_store.append_event(
            stream_id=user_id,
            stream_type=EventStreamType.VALIDATION,
            event_type="hypothesis_validated",
            payload={
                "hypothesis_id": hypothesis.hypothesis_id,
                "is_validated": result.is_validated,
                "validation_score": result.validation_score,
                "confidence_multiplier": result.confidence_multiplier,
                "supporting_evidence": result.supporting_evidence,
                "contradicting_evidence": result.contradicting_evidence,
                "evidence_quality_score": result.evidence_quality_score,
                "recommendation": result.recommendation
            }
        )
    
    async def add_evidence(self,
                          hypothesis_id: str,
                          user_id: str,
                          evidence_type: str,
                          data: Dict[str, Any],
                          confidence: float,
                          supports_hypothesis: bool,
                          strength: ValidationStrength) -> str:
        """
        Add evidence for hypothesis validation
        
        Args:
            hypothesis_id: The hypothesis ID
            user_id: The user
            evidence_type: Type of evidence
            data: Evidence data
            confidence: Confidence in evidence
            supports_hypothesis: Whether evidence supports hypothesis
            strength: Evidence strength
            
        Returns:
            Evidence ID
        """
        
        evidence_id = f"evidence_{len(await self.event_store.get_events(user_id, EventStreamType.VALIDATION))}"
        
        await self.event_store.append_event(
            stream_id=user_id,
            stream_type=EventStreamType.VALIDATION,
            event_type="evidence_collected",
            payload={
                "evidence_id": evidence_id,
                "hypothesis_id": hypothesis_id,
                "evidence_type": evidence_type,
                "data": data,
                "confidence": confidence,
                "supports_hypothesis": supports_hypothesis,
                "strength": strength.value
            }
        )
        
        return evidence_id
    
    async def get_validation_history(self, hypothesis_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get validation history for a hypothesis
        
        Args:
            hypothesis_id: The hypothesis ID
            user_id: The user
            
        Returns:
            Validation history
        """
        
        events = await self.event_store.get_events(
            stream_id=user_id,
            stream_type=EventStreamType.VALIDATION,
            event_type="hypothesis_validated"
        )
        
        history = []
        for event in events:
            if event['event_data'].get('hypothesis_id') == hypothesis_id:
                history.append(event['event_data'])
        
        return history
    
    async def get_evidence_summary(self, hypothesis_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get summary of evidence for a hypothesis
        
        Args:
            hypothesis_id: The hypothesis ID
            user_id: The user
            
        Returns:
            Evidence summary
        """
        
        events = await self.event_store.get_events(
            stream_id=user_id,
            stream_type=EventStreamType.VALIDATION,
            event_type="evidence_collected"
        )
        
        evidence = [e for e in events if e['event_data'].get('hypothesis_id') == hypothesis_id]
        
        supporting = [e for e in evidence if e['event_data']['supports_hypothesis']]
        contradicting = [e for e in evidence if not e['event_data']['supports_hypothesis']]
        
        return {
            "total_evidence": len(evidence),
            "supporting_evidence": len(supporting),
            "contradicting_evidence": len(contradicting),
            "evidence_types": list(set([e['event_data']['evidence_type'] for e in evidence])),
            "average_confidence": np.mean([e['event_data']['confidence'] for e in evidence]) if evidence else 0.0
        }
    
    async def cleanup_expired_evidence(self, user_id: str, max_age_days: int = 90) -> int:
        """
        Clean up expired evidence
        
        Args:
            user_id: The user
            max_age_days: Maximum age in days
            
        Returns:
            Number of events cleaned
        """
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        
        return await self.event_store.delete_events(
            stream_id=user_id,
            stream_type=EventStreamType.VALIDATION,
            before_time=cutoff_date
        )
