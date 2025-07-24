"""
Compound Intelligence Engine for AUREN
Transforms individual memories into universal knowledge
Enables pattern discovery that benefits millions of users
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CompoundIntelligenceEngine:
    """
    Manages memory retention to build compound intelligence
    Enables pattern discovery that benefits all users
    Every user's journey contributes to universal knowledge
    """
    
    def __init__(self, memory_backend):
        self.memory_backend = memory_backend
    
    async def extract_population_patterns(self,
                                        pattern_type: str,
                                        min_confidence: float = 0.8,
                                        min_users: int = 10) -> List[Dict[str, Any]]:
        """
        Extract patterns that work across multiple users
        This is the compound intelligence breakthrough
        """
        
        try:
            # Find patterns validated across multiple users
            query = """
            WITH validated_patterns AS (
                SELECT 
                    content->>'pattern_description' as pattern_description,
                    content->>'intervention' as intervention,
                    content->>'outcome' as outcome,
                    confidence_score,
                    user_id,
                    agent_id,
                    created_at,
                    content->>'validation_method' as validation_method,
                    content->>'effect_size' as effect_size
                FROM agent_memories 
                WHERE memory_type = 'validated_pattern'
                AND confidence_score >= $1
                AND validation_status = 'statistically_significant'
                AND created_at >= NOW() - INTERVAL '90 days'
            ),
            population_patterns AS (
                SELECT 
                    pattern_description,
                    intervention,
                    outcome,
                    COUNT(DISTINCT user_id) as user_count,
                    AVG(confidence_score) as avg_confidence,
                    STDDEV(confidence_score) as confidence_std,
                    AVG((content->>'effect_size')::numeric) as avg_effect_size,
                    array_agg(DISTINCT agent_id) as contributing_agents,
                    array_agg(DISTINCT user_id) as user_ids,
                    MIN(created_at) as first_observation,
                    MAX(created_at) as last_observation
                FROM validated_patterns
                GROUP BY pattern_description, intervention, outcome
                HAVING COUNT(DISTINCT user_id) >= $2  -- Must work for multiple users
            )
            SELECT 
                pattern_description,
                intervention,
                outcome,
                user_count,
                avg_confidence,
                confidence_std,
                avg_effect_size,
                contributing_agents,
                user_ids,
                first_observation,
                last_observation,
                -- Population effectiveness score
                (user_count * avg_confidence * (1.0 - confidence_std) * avg_effect_size) as effectiveness_score
            FROM population_patterns
            WHERE avg_confidence >= $1
            ORDER BY effectiveness_score DESC
            LIMIT 50
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                results = await conn.fetch(query, min_confidence, min_users)
                
            patterns = []
            for row in results:
                pattern = dict(row)
                pattern["clinical_significance"] = self._calculate_clinical_significance(pattern)
                pattern["universal_applicability"] = self._assess_universal_applicability(pattern)
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to extract population patterns: {e}")
            return []
    
    async def contribute_to_global_knowledge(self,
                                           user_id: str,
                                           validated_pattern: Dict[str, Any]) -> str:
        """
        Add user's validated pattern to global compound intelligence
        This is how personal optimization becomes universal benefit
        """
        
        try:
            # Check if pattern already exists in global knowledge
            existing_pattern = await self._find_similar_global_pattern(validated_pattern)
            
            if existing_pattern:
                # Strengthen existing pattern with new validation
                pattern_id = await self._strengthen_global_pattern(
                    existing_pattern["id"], 
                    validated_pattern,
                    user_id
                )
                return f"strengthened_{pattern_id}"
            else:
                # Create new global pattern for future users
                pattern_id = await self._create_global_pattern(validated_pattern, user_id)
                return f"created_{pattern_id}"
                
        except Exception as e:
            logger.error(f"Failed to contribute to global knowledge: {e}")
            return "error"
    
    async def get_compound_intelligence_insights(self,
                                               user_id: str,
                                               user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get insights from compound intelligence that could help this user
        Leverages patterns discovered from millions of other users
        """
        
        try:
            # Find global patterns relevant to this user's profile
            query = """
            WITH user_similarity AS (
                SELECT DISTINCT
                    gp.id,
                    gp.pattern_description,
                    gp.intervention,
                    gp.outcome,
                    gp.effectiveness_score,
                    gp.user_count,
                    gp.avg_confidence,
                    gp.avg_effect_size,
                    gp.contributing_agents,
                    -- Calculate similarity to user profile
                    (
                        CASE 
                            WHEN gp.user_demographics->>'age_range' = $2 THEN 0.2 
                            ELSE 0.0 
                        END +
                        CASE 
                            WHEN gp.user_demographics->>'fitness_level' = $3 THEN 0.2 
                            ELSE 0.0 
                        END +
                        CASE 
                            WHEN gp.user_demographics->>'goals' ? $4 THEN 0.3 
                            ELSE 0.0 
                        END +
                        CASE 
                            WHEN gp.user_demographics->>'gender' = $5 THEN 0.1 
                            ELSE 0.0 
                        END +
                        CASE 
                            WHEN gp.user_demographics->>'lifestyle' = $6 THEN 0.2 
                            ELSE 0.0 
                        END
                    ) as similarity_score
                FROM global_patterns gp
                WHERE gp.effectiveness_score > 0.7
                AND gp.user_count >= 10
                AND gp.is_active = true
            )
            SELECT *
            FROM user_similarity 
            WHERE similarity_score > 0.3  -- At least 30% similarity
            ORDER BY (similarity_score * effectiveness_score) DESC
            LIMIT 20
            """
            
            # Extract user profile characteristics
            age_range = self._categorize_age(user_profile.get("age", 30))
            fitness_level = user_profile.get("fitness_level", "intermediate")
            primary_goal = user_profile.get("primary_goal", "general_health")
            gender = user_profile.get("gender", "other")
            lifestyle = user_profile.get("lifestyle", "moderate")
            
            async with self.memory_backend.manager.get_connection() as conn:
                insights = await conn.fetch(
                    query, user_id, age_range, fitness_level, primary_goal, gender, lifestyle
                )
            
            # Enhance insights with personalized recommendations
            enhanced_insights = []
            for insight in insights:
                enhanced_insight = dict(insight)
                enhanced_insight["personalization_score"] = insight["similarity_score"]
                enhanced_insight["expected_benefit"] = self._calculate_expected_benefit(
                    enhanced_insight, user_profile
                )
                enhanced_insight["implementation_priority"] = self._rank_implementation_priority(
                    enhanced_insight
                )
                enhanced_insights.append(enhanced_insight)
            
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"Failed to get compound intelligence insights: {e}")
            return []
    
    async def memory_evolution_protocol(self, agent_id: str, user_id: str) -> Dict[str, Any]:
        """
        Evolve memory quality based on real-world outcomes
        Implements the learning system from Module B
        """
        
        try:
            # Find memories that led to successful outcomes
            successful_memories = await self._identify_successful_intervention_memories(
                agent_id, user_id
            )
            
            # Promote successful memories (increase confidence)
            promoted_count = 0
            for memory in successful_memories:
                promoted = await self._promote_memory_confidence(
                    memory["id"], 
                    increment=0.15,
                    reason="successful_outcome"
                )
                if promoted:
                    promoted_count += 1
            
            # Find memories that led to poor outcomes
            unsuccessful_memories = await self._identify_unsuccessful_intervention_memories(
                agent_id, user_id
            )
            
            # Demote unsuccessful memories (decrease confidence)
            demoted_count = 0
            for memory in unsuccessful_memories:
                demoted = await self._demote_memory_confidence(
                    memory["id"], 
                    decrement=0.1,
                    reason="unsuccessful_outcome"
                )
                if demoted:
                    demoted_count += 1
            
            # Archive extremely low confidence memories (but keep for audit)
            archived_count = await self._archive_low_confidence_memories(
                agent_id, user_id, threshold=0.1
            )
            
            # Update global patterns based on new evidence
            updated_patterns = await self._update_global_patterns_with_new_evidence(
                agent_id, user_id
            )
            
            return {
                "promoted_memories": promoted_count,
                "demoted_memories": demoted_count,
                "archived_memories": archived_count,
                "updated_global_patterns": updated_patterns,
                "evolution_complete": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory evolution failed: {e}")
            return {"error": str(e), "evolution_complete": False}
    
    async def calculate_compound_intelligence_score(self) -> Dict[str, Any]:
        """
        Calculate how much compound intelligence the system has accumulated
        This is the measure of how much smarter the system has become
        """
        
        try:
            query = """
            WITH intelligence_metrics AS (
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(DISTINCT validated_pattern) as total_patterns,
                    AVG(confidence_score) as avg_pattern_confidence,
                    AVG(effectiveness_score) as avg_effectiveness,
                    SUM(user_count) as total_validations,
                    MAX(created_at) as last_update
                FROM global_patterns
                WHERE is_active = true
            ),
            learning_velocity AS (
                SELECT 
                    COUNT(*) as patterns_last_30_days,
                    AVG(effectiveness_score) as recent_effectiveness,
                    AVG(user_count) as recent_user_adoption
                FROM global_patterns
                WHERE created_at >= NOW() - INTERVAL '30 days'
                AND is_active = true
            )
            SELECT 
                im.*,
                lv.patterns_last_30_days,
                lv.recent_effectiveness,
                lv.recent_user_adoption,
                -- Compound intelligence score
                (
                    im.total_users * 0.3 +
                    im.total_patterns * 0.4 +
                    im.avg_pattern_confidence * 100 * 0.2 +
                    im.avg_effectiveness * 100 * 0.1
                ) as compound_intelligence_score
            FROM intelligence_metrics im, learning_velocity lv
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                result = await conn.fetchrow(query)
                
            if result:
                return dict(result)
            else:
                return {
                    "total_users": 0,
                    "total_patterns": 0,
                    "avg_pattern_confidence": 0.0,
                    "avg_effectiveness": 0.0,
                    "compound_intelligence_score": 0.0,
                    "learning_velocity": 0.0
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate compound intelligence score: {e}")
            return {"error": str(e), "compound_intelligence_score": 0.0}
    
    # Private helper methods
    async def _find_similar_global_pattern(self, validated_pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find existing global pattern similar to validated pattern"""
        
        try:
            query = """
            SELECT id, pattern_description, intervention, outcome, effectiveness_score
            FROM global_patterns
            WHERE pattern_description ILIKE '%' || $1 || '%'
            AND intervention ILIKE '%' || $2 || '%'
            AND outcome ILIKE '%' || $3 || '%'
            AND is_active = true
            ORDER BY effectiveness_score DESC
            LIMIT 1
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                result = await conn.fetchrow(
                    query,
                    validated_pattern.get("pattern_description", ""),
                    validated_pattern.get("intervention", ""),
                    validated_pattern.get("outcome", "")
                )
                
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to find similar global pattern: {e}")
            return None
    
    async def _create_global_pattern(self, validated_pattern: Dict[str, Any], user_id: str) -> str:
        """Create new global pattern from validated user pattern"""
        
        try:
            query = """
            INSERT INTO global_patterns (
                pattern_description,
                intervention,
                outcome,
                effectiveness_score,
                user_count,
                avg_confidence,
                avg_effect_size,
                user_demographics,
                contributing_agents,
                first_user_id,
                created_at,
                is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), true)
            RETURNING id
            """
            
            effectiveness_score = validated_pattern.get("effectiveness_score", 0.7)
            effect_size = validated_pattern.get("effect_size", 0.5)
            
            async with self.memory_backend.manager.get_connection() as conn:
                pattern_id = await conn.fetchval(
                    query,
                    validated_pattern.get("pattern_description", ""),
                    validated_pattern.get("intervention", ""),
                    validated_pattern.get("outcome", ""),
                    effectiveness_score,
                    1,  # First user
                    validated_pattern.get("confidence", 0.8),
                    effect_size,
                    json.dumps(validated_pattern.get("user_demographics", {})),
                    json.dumps([validated_pattern.get("agent_id", "unknown")]),
                    user_id
                )
                
            return str(pattern_id) if pattern_id else "error"
            
        except Exception as e:
            logger.error(f"Failed to create global pattern: {e}")
            return "error"
    
    async def _strengthen_global_pattern(self, pattern_id: str, validated_pattern: Dict[str, Any], user_id: str) -> str:
        """Strengthen existing global pattern with new validation"""
        
        try:
            query = """
            UPDATE global_patterns
            SET 
                user_count = user_count + 1,
                avg_confidence = ((avg_confidence * user_count) + $1) / (user_count + 1),
                avg_effect_size = ((avg_effect_size * user_count) + $2) / (user_count + 1),
                effectiveness_score = effectiveness_score + 0.05,
                last_updated = NOW(),
                contributing_agents = array_append(contributing_agents, $3)
            WHERE id = $4
            RETURNING id
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                updated_id = await conn.fetchval(
                    query,
                    validated_pattern.get("confidence", 0.8),
                    validated_pattern.get("effect_size", 0.5),
                    validated_pattern.get("agent_id", "unknown"),
                    pattern_id
                )
                
            return str(updated_id) if updated_id else "error"
            
        except Exception as e:
            logger.error(f"Failed to strengthen global pattern: {e}")
            return "error"
    
    async def _identify_successful_intervention_memories(self, agent_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Identify memories that led to successful outcomes"""
        
        try:
            query = """
            SELECT id, content, confidence_score, created_at
            FROM agent_memories
            WHERE agent_id = $1
            AND user_id = $2
            AND memory_type = 'intervention'
            AND content->>'outcome' = 'successful'
            AND created_at >= NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                results = await conn.fetch(query, agent_id, user_id)
                
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to identify successful memories: {e}")
            return []
    
    async def _identify_unsuccessful_intervention_memories(self, agent_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Identify memories that led to unsuccessful outcomes"""
        
        try:
            query = """
            SELECT id, content, confidence_score, created_at
            FROM agent_memories
            WHERE agent_id = $1
            AND user_id = $2
            AND memory_type = 'intervention'
            AND content->>'outcome' = 'unsuccessful'
            AND created_at >= NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                results = await conn.fetch(query, agent_id, user_id)
                
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to identify unsuccessful memories: {e}")
            return []
    
    async def _promote_memory_confidence(self, memory_id: int, increment: float, reason: str) -> bool:
        """Increase confidence score for successful memory"""
        
        try:
            query = """
            UPDATE agent_memories
            SET 
                confidence_score = LEAST(confidence_score + $1, 1.0),
                metadata = jsonb_set(metadata, '{promotion_reason}', $2::jsonb),
                updated_at = NOW()
            WHERE id = $3
            RETURNING id
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                result = await conn.fetchval(query, increment, json.dumps(reason), memory_id)
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to promote memory confidence: {e}")
            return False
    
    async def _demote_memory_confidence(self, memory_id: int, decrement: float, reason: str) -> bool:
        """Decrease confidence score for unsuccessful memory"""
        
        try:
            query = """
            UPDATE agent_memories
            SET 
                confidence_score = GREATEST(confidence_score - $1, 0.0),
                metadata = jsonb_set(metadata, '{demotion_reason}', $2::jsonb),
                updated_at = NOW()
            WHERE id = $3
            RETURNING id
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                result = await conn.fetchval(query, decrement, json.dumps(reason), memory_id)
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to demote memory confidence: {e}")
            return False
    
    async def _archive_low_confidence_memories(self, agent_id: str, user_id: str, threshold: float) -> int:
        """Archive memories with very low confidence scores"""
        
        try:
            query = """
            UPDATE agent_memories
            SET 
                is_archived = true,
                archived_at = NOW(),
                archive_reason = 'low_confidence'
            WHERE agent_id = $1
            AND user_id = $2
            AND confidence_score < $3
            AND is_archived = false
            RETURNING COUNT(*)
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                count = await conn.fetchval(query, agent_id, user_id, threshold)
                
            return count or 0
            
        except Exception as e:
            logger.error(f"Failed to archive low confidence memories: {e}")
            return 0
    
    async def _update_global_patterns_with_new_evidence(self, agent_id: str, user_id: str) -> int:
        """Update global patterns with new evidence from this user"""
        
        try:
            # This would implement the Bayesian updating logic
            # For now, return placeholder
            return 0
            
        except Exception as e:
            logger.error(f"Failed to update global patterns: {e}")
            return 0
    
    def _categorize_age(self, age: int) -> str:
        """Categorize age into ranges for similarity matching"""
        if age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        else:
            return "55+"
    
    def _calculate_clinical_significance(self, pattern: Dict[str, Any]) -> str:
        """Calculate clinical significance of a population pattern"""
        
        user_count = pattern.get("user_count", 0)
        avg_confidence = pattern.get("avg_confidence", 0.0)
        avg_effect_size = pattern.get("avg_effect_size", 0.0)
        
        score = (user_count * 0.4 + avg_confidence * 100 * 0.3 + avg_effect_size * 100 * 0.3)
        
        if score >= 20:
            return "high"
        elif score >= 10:
            return "moderate"
        else:
            return "low"
    
    def _assess_universal_applicability(self, pattern: Dict[str, Any]) -> float:
        """Assess how universally applicable this pattern is"""
        
        user_count = pattern.get("user_count", 0)
        confidence_std = pattern.get("confidence_std", 1.0)
        
        # Higher user count and lower confidence std = more universal
        return min(user_count / 100.0, 1.0) * (1.0 - confidence_std)
    
    def _calculate_expected_benefit(self, insight: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Calculate expected benefit for this specific user"""
        
        similarity_score = insight.get("similarity_score", 0.0)
        effectiveness_score = insight.get("effectiveness_score", 0.0)
        
        return similarity_score * effectiveness_score
    
    def _rank_implementation_priority(self, insight: Dict[str, Any]) -> str:
        """Rank implementation priority based on expected benefit and risk"""
        
        expected_benefit = insight.get("expected_benefit", 0.0)
        
        if expected_benefit >= 0.7:
            return "high"
        elif expected_benefit >= 0.4:
            return "medium"
        else:
            return "low"


# Global patterns table schema
GLOBAL_PATTERNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS global_patterns (
    id SERIAL PRIMARY KEY,
    pattern_description TEXT NOT NULL,
    intervention TEXT NOT NULL,
    outcome TEXT NOT NULL,
    effectiveness_score FLOAT NOT NULL,
    user_count INTEGER NOT NULL DEFAULT 1,
    avg_confidence FLOAT NOT NULL,
    avg_effect_size FLOAT NOT NULL,
    confidence_std FLOAT DEFAULT 0.0,
    user_demographics JSONB DEFAULT '{}',
    contributing_agents TEXT[] DEFAULT '{}',
    first_user_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    INDEX idx_effectiveness_score (effectiveness_score DESC),
    INDEX idx_user_count (user_count DESC),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_active_patterns (is_active, effectiveness_score DESC)
);
"""
