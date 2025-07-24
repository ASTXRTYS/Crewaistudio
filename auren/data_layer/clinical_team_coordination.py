"""
Clinical Team Coordination System for AUREN
Enables specialist collaboration for complex cases
Implements the medical consultation protocol from Module B
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ClinicalTeamCoordination:
    """
    Coordinates specialist teams for complex clinical cases
    Enables cross-domain pattern discovery and validation
    """
    
    def __init__(self, memory_backend):
        self.memory_backend = memory_backend
        self.specialist_domains = {
            "neuroscientist": {
                "expertise": ["CNS_optimization", "stress_management", "cognitive_performance"],
                "priority": 1,
                "response_time": 0.008
            },
            "training_coach": {
                "expertise": ["performance", "workout_optimization", "progressive_overload"],
                "priority": 2,
                "response_time": 0.012
            },
            "nutritionist": {
                "expertise": ["metabolic", "nutrition_timing", "macronutrient_balance"],
                "priority": 2,
                "response_time": 0.010
            },
            "recovery_specialist": {
                "expertise": ["adaptation", "recovery_protocols", "injury_prevention"],
                "priority": 3,
                "response_time": 0.015
            },
            "sleep_expert": {
                "expertise": ["circadian", "sleep_optimization", "recovery_quality"],
                "priority": 3,
                "response_time": 0.012
            },
            "mental_health_advisor": {
                "expertise": ["psychological", "stress_management", "motivation"],
                "priority": 2,
                "response_time": 0.010
            }
        }
    
    async def initiate_clinical_consultation(self,
                                           user_id: str,
                                           primary_concern: str,
                                           consultation_type: str = "routine",
                                           urgency_level: int = 1) -> Dict[str, Any]:
        """
        Initiate a clinical consultation with relevant specialists
        Implements the medical consultation protocol from Module B
        """
        
        start_time = time.time()
        
        try:
            # Identify relevant specialists based on primary concern
            relevant_specialists = await self._identify_relevant_specialists(
                primary_concern, urgency_level
            )
            
            if not relevant_specialists:
                return {
                    "consultation_id": None,
                    "error": "No relevant specialists found for this concern",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Create consultation record
            consultation_id = await self._create_consultation_record(
                user_id, primary_concern, consultation_type, urgency_level, relevant_specialists
            )
            
            # Gather specialist inputs in parallel
            specialist_inputs = await self._gather_specialist_inputs(
                user_id, relevant_specialists, primary_concern, consultation_type
            )
            
            # Find cross-domain correlations
            correlations = await self._analyze_cross_domain_correlations(
                user_id, specialist_inputs, primary_concern
            )
            
            # Generate collaborative recommendation
            collaborative_recommendation = await self._generate_team_recommendation(
                specialist_inputs, correlations, consultation_type, urgency_level
            )
            
            # Store the team consultation for future reference
            await self._store_team_consultation(
                consultation_id, user_id, primary_concern, specialist_inputs, collaborative_recommendation
            )
            
            # Update global patterns with new insights
            await self._update_global_patterns_from_consultation(
                consultation_id, collaborative_recommendation
            )
            
            total_time = time.time() - start_time
            
            return {
                "consultation_id": consultation_id,
                "participating_specialists": relevant_specialists,
                "specialist_inputs": specialist_inputs,
                "cross_domain_correlations": correlations,
                "team_recommendation": collaborative_recommendation,
                "consultation_confidence": collaborative_recommendation.get("confidence", 0.0),
                "response_time_seconds": total_time,
                "clinical_grade": total_time < 0.05,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Clinical consultation failed: {e}")
            return {
                "consultation_id": None,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _identify_relevant_specialists(self,
                                           primary_concern: str,
                                           urgency_level: int) -> List[str]:
        """Identify which specialists should be involved based on concern"""
        
        concern_lower = primary_concern.lower()
        
        # Map concerns to specialists
        specialist_mapping = {
            "fatigue": ["neuroscientist", "sleep_expert", "training_coach"],
            "stress": ["neuroscientist", "mental_health_advisor", "recovery_specialist"],
            "performance": ["training_coach", "nutritionist", "recovery_specialist"],
            "sleep": ["sleep_expert", "neuroscientist", "mental_health_advisor"],
            "nutrition": ["nutritionist", "training_coach", "recovery_specialist"],
            "recovery": ["recovery_specialist", "training_coach", "sleep_expert"],
            "cognitive": ["neuroscientist", "mental_health_advisor", "sleep_expert"],
            "motivation": ["mental_health_advisor", "training_coach", "neuroscientist"],
            "injury": ["recovery_specialist", "training_coach", "neuroscientist"],
            "weight": ["nutritionist", "training_coach", "recovery_specialist"],
            "energy": ["nutritionist", "sleep_expert", "neuroscientist"],
            "mood": ["mental_health_advisor", "neuroscientist", "sleep_expert"]
        }
        
        # Find matching specialists
        relevant_specialists = set()
        
        for keyword, specialists in specialist_mapping.items():
            if keyword in concern_lower:
                relevant_specialists.update(specialists)
        
        # If no specific match, include general specialists
        if not relevant_specialists:
            relevant_specialists = ["training_coach", "nutritionist", "recovery_specialist"]
        
        # Prioritize based on urgency
        if urgency_level >= 7:
            # Emergency - include neuroscientist and mental health
            relevant_specialists.add("neuroscientist")
            relevant_specialists.add("mental_health_advisor")
        
        return list(relevant_specialists)
    
    async def _create_consultation_record(self,
                                        user_id: str,
                                        primary_concern: str,
                                        consultation_type: str,
                                        urgency_level: int,
                                        specialists: List[str]) -> str:
        """Create consultation record in database"""
        
        try:
            query = """
            INSERT INTO clinical_consultations (
                user_id,
                primary_concern,
                consultation_type,
                urgency_level,
                participating_specialists,
                status,
                created_at,
                updated_at
            ) VALUES ($1, $2, $3, $4, $5, 'active', NOW(), NOW())
            RETURNING id
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                consultation_id = await conn.fetchval(
                    query,
                    user_id,
                    primary_concern,
                    consultation_type,
                    urgency_level,
                    json.dumps(specialists)
                )
                
            return str(consultation_id) if consultation_id else "error"
            
        except Exception as e:
            logger.error(f"Failed to create consultation record: {e}")
            return "error"
    
    async def _gather_specialist_inputs(self,
                                      user_id: str,
                                      specialists: List[str],
                                      primary_concern: str,
                                      consultation_type: str) -> Dict[str, Any]:
        """Gather inputs from all relevant specialists in parallel"""
        
        specialist_tasks = {}
        
        for specialist in specialists:
            specialist_tasks[specialist] = self._get_specialist_analysis(
                specialist, user_id, primary_concern, consultation_type
            )
        
        # Execute all specialist analyses simultaneously
        results = await asyncio.gather(*specialist_tasks.values(), return_exceptions=True)
        
        specialist_inputs = {}
        for specialist, result in zip(specialists, results):
            if isinstance(result, Exception):
                logger.error(f"Specialist {specialist} failed: {result}")
                specialist_inputs[specialist] = {"error": str(result), "confidence": 0.0}
            else:
                specialist_inputs[specialist] = result
        
        return specialist_inputs
    
    async def _get_specialist_analysis(self,
                                     specialist: str,
                                     user_id: str,
                                     primary_concern: str,
                                     consultation_type: str) -> Dict[str, Any]:
        """Get analysis from a specific specialist"""
        
        try:
            # Get relevant data for this specialist
            relevant_data = await self._get_specialist_relevant_data(
                specialist, user_id, primary_concern
            )
            
            # Analyze patterns specific to this specialist's domain
            patterns = await self._analyze_specialist_patterns(
                specialist, user_id, relevant_data, primary_concern
            )
            
            # Generate specialist-specific recommendation
            recommendation = await self._generate_specialist_recommendation(
                specialist, patterns, primary_concern, consultation_type
            )
            
            return {
                "specialist": specialist,
                "domain": self.specialist_domains[specialist]["expertise"],
                "analysis": recommendation,
                "confidence": recommendation.get("confidence", 0.0),
                "data_points": len(relevant_data),
                "patterns_identified": len(patterns),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get specialist analysis for {specialist}: {e}")
            return {"specialist": specialist, "error": str(e), "confidence": 0.0}
    
    async def _get_specialist_relevant_data(self,
                                          specialist: str,
                                          user_id: str,
                                          primary_concern: str) -> List[Dict[str, Any]]:
        """Get data relevant to this specialist's domain"""
        
        try:
            # Get recent data for this specialist's domain
            query = """
            SELECT 
                content,
                confidence_score,
                created_at,
                memory_type
            FROM agent_memories
            WHERE agent_id = $1
            AND user_id = $2
            AND created_at >= NOW() - INTERVAL '30 days'
            AND (
                memory_type = 'observation' OR
                memory_type = 'intervention' OR
                memory_type = 'pattern'
            )
            ORDER BY created_at DESC
            LIMIT 100
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                results = await conn.fetch(query, specialist, user_id)
                
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get specialist relevant data: {e}")
            return []
    
    async def _analyze_specialist_patterns(self,
                                         specialist: str,
                                         user_id: str,
                                         data: List[Dict[str, Any]],
                                         primary_concern: str) -> List[Dict[str, Any]]:
        """Analyze patterns specific to this specialist's domain"""
        
        patterns = []
        
        # Extract patterns from specialist data
        for item in data:
            content = item.get("content", {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    continue
            
            # Look for patterns relevant to the concern
            if "pattern" in str(content).lower() and primary_concern.lower() in str(content).lower():
                patterns.append({
                    "pattern": content,
                    "confidence": item.get("confidence_score", 0.0),
                    "timestamp": item.get("created_at", ""),
                    "memory_type": item.get("memory_type", "")
                })
        
        return patterns
    
    async def _generate_specialist_recommendation(self,
                                                specialist: str,
                                                patterns: List[Dict[str, Any]],
                                                primary_concern: str,
                                                consultation_type: str) -> Dict[str, Any]:
        """Generate specialist-specific recommendation"""
        
        # Default recommendations by specialist
        recommendations = {
            "neuroscientist": {
                "recommendation": "optimize_cns_recovery",
                "confidence": 0.8,
                "interventions": ["reduce_stress", "improve_sleep", "cognitive_support"]
            },
            "training_coach": {
                "recommendation": "adjust_training_protocol",
                "confidence": 0.75,
                "interventions": ["reduce_intensity", "increase_recovery", "form_check"]
            },
            "nutritionist": {
                "recommendation": "optimize_nutrition_timing",
                "confidence": 0.7,
                "interventions": ["meal_timing", "macro_adjustment", "supplementation"]
            },
            "recovery_specialist": {
                "recommendation": "enhance_recovery_protocol",
                "confidence": 0.85,
                "interventions": ["active_recovery", "rest_periods", "mobility_work"]
            },
            "sleep_expert": {
                "recommendation": "optimize_sleep_hygiene",
                "confidence": 0.9,
                "interventions": ["bedtime_routine", "light_exposure", "sleep_environment"]
            },
            "mental_health_advisor": {
                "recommendation": "stress_management_protocol",
                "confidence": 0.8,
                "interventions": ["mindfulness", "cognitive_reframing", "support_system"]
            }
        }
        
        return recommendations.get(specialist, {
            "recommendation": "general_support",
            "confidence": 0.5,
            "interventions": ["monitor_and_assess"]
        })
    
    async def _analyze_cross_domain_correlations(self,
                                               user_id: str,
                                               specialist_inputs: Dict[str, Any],
                                               primary_concern: str) -> List[Dict[str, Any]]:
        """Find correlations between different specialist domains"""
        
        correlations = []
        
        # Get all specialist data for correlation analysis
        specialist_data = {}
        for specialist, input_data in specialist_inputs.items():
            if "error" not in input_data:
                specialist_data[specialist] = input_data
        
        if len(specialist_data) < 2:
            return correlations
        
        # Analyze pairwise correlations
        specialists = list(specialist_data.keys())
        
        for i, specialist_a in enumerate(specialists):
            for specialist_b in specialists[i+1:]:
                
                correlation = await self._find_specialist_correlation(
                    user_id, specialist_a, specialist_b, primary_concern
                )
                
                if correlation and correlation["correlation_strength"] > 0.6:
                    correlations.append(correlation)
        
        return correlations
    
    async def _find_specialist_correlation(self,
                                         user_id: str,
                                         specialist_a: str,
                                         specialist_b: str,
                                         context: str) -> Optional[Dict[str, Any]]:
        """Find specific correlations between two specialists for this user"""
        
        try:
            query = """
            WITH specialist_a_data AS (
                SELECT 
                    DATE(created_at) as date,
                    content->>'value' as value,
                    confidence_score
                FROM agent_memories
                WHERE agent_id = $1
                AND user_id = $2
                AND created_at >= NOW() - INTERVAL '30 days'
                AND content->>'value' IS NOT NULL
            ),
            specialist_b_data AS (
                SELECT 
                    DATE(created_at) as date,
                    content->>'value' as value,
                    confidence_score
                FROM agent_memories
                WHERE agent_id = $3
                AND user_id = $4
                AND created_at >= NOW() - INTERVAL '30 days'
                AND content->>'value' IS NOT NULL
            ),
            correlated_data AS (
                SELECT 
                    a.date,
                    a.value::numeric as value_a,
                    b.value::numeric as value_b,
                    a.confidence_score as confidence_a,
                    b.confidence_score as confidence_b
                FROM specialist_a_data a
                JOIN specialist_b_data b ON a.date = b.date
                WHERE a.value IS NOT NULL AND b.value IS NOT NULL
            )
            SELECT 
                COUNT(*) as sample_size,
                CORR(value_a, value_b) as correlation_coefficient,
                AVG(confidence_a) as avg_confidence_a,
                AVG(confidence_b) as avg_confidence_b
            FROM correlated_data
            HAVING COUNT(*) >= 5
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                result = await conn.fetchrow(query, specialist_a, user_id, specialist_b, user_id)
                
            if result and abs(result["correlation_coefficient"]) > 0.6:
                return {
                    "specialist_pair": [specialist_a, specialist_b],
                    "correlation_type": f"{specialist_a}_vs_{specialist_b}",
                    "correlation_strength": abs(result["correlation_coefficient"]),
                    "sample_size": result["sample_size"],
                    "confidence_a": result["avg_confidence_a"],
                    "confidence_b": result["avg_confidence_b"],
                    "clinical_significance": "high" if result["sample_size"] > 10 else "moderate"
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to find specialist correlation: {e}")
            return None
    
    async def _generate_team_recommendation(self,
                                          specialist_inputs: Dict[str, Any],
                                          correlations: List[Dict[str, Any]],
                                          consultation_type: str,
                                          urgency_level: int) -> Dict[str, Any]:
        """Generate collaborative recommendation from all specialists"""
        
        # Weight recommendations by confidence
        weighted_recommendations = {}
        total_confidence = 0
        
        for specialist, input_data in specialist_inputs.items():
            if "error" not in input_data:
                recommendation = input_data.get("analysis", {})
                confidence = input_data.get("confidence", 0.0)
                
                rec_key = recommendation.get("recommendation", "general_support")
                if rec_key not in weighted_recommendations:
                    weighted_recommendations[rec_key] = {
                        "weight": 0,
                        "specialists": [],
                        "interventions": []
                    }
                
                weighted_recommendations[rec_key]["weight"] += confidence
                weighted_recommendations[rec_key]["specialists"].append(specialist)
                weighted_recommendations[rec_key]["interventions"].extend(
                    recommendation.get("interventions", [])
                )
                
                total_confidence += confidence
        
        if not weighted_recommendations:
            return {
                "recommendation": "general_monitoring",
                "confidence": 0.3,
                "reasoning": "Insufficient specialist input for confident recommendation",
                "interventions": ["monitor_and_assess"],
                "specialists": []
            }
        
        # Select highest-weighted recommendation
        best_recommendation = max(weighted_recommendations.items(), key=lambda x: x[1]["weight"])
        
        # Incorporate cross-domain correlations
        correlation_insights = []
        for correlation in correlations:
            if correlation["correlation_strength"] > 0.8:
                correlation_insights.append(
                    f"Strong correlation between {correlation['specialist_pair'][0]} and {correlation['specialist_pair'][1]}"
                )
        
        return {
            "recommendation": best_recommendation[0],
            "confidence": best_recommendation[1]["weight"] / total_confidence if total_confidence > 0 else 0.0,
            "reasoning": f"Based on {len(specialist_inputs)} specialist analyses",
            "interventions": list(set(best_recommendation[1]["interventions"])),
            "specialists": best_recommendation[1]["specialists"],
            "correlation_insights": correlation_insights,
            "urgency_level": urgency_level,
            "consultation_type": consultation_type
        }
    
    async def _store_team_consultation(self,
                                     consultation_id: str,
                                     user_id: str,
                                     primary_concern: str,
                                     specialist_inputs: Dict[str, Any],
                                     recommendation: Dict[str, Any]) -> bool:
        """Store the team consultation for future reference"""
        
        try:
            query = """
            UPDATE clinical_consultations
            SET 
                specialist_inputs = $1,
                team_recommendation = $2,
                status = 'completed',
                completed_at = NOW()
            WHERE id = $3
            RETURNING id
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                result = await conn.fetchval(
                    query,
                    json.dumps(specialist_inputs),
                    json.dumps(recommendation),
                    consultation_id
                )
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to store team consultation: {e}")
            return False
    
    async def _update_global_patterns_from_consultation(self,
                                                      consultation_id: str,
                                                      recommendation: Dict[str, Any]) -> int:
        """Update global patterns with insights from this consultation"""
        
        try:
            # This would implement pattern extraction from consultations
            # For now, return placeholder
            return 1
            
        except Exception as e:
            logger.error(f"Failed to update global patterns: {e}")
            return 0
    
    async def get_consultation_history(self,
                                     user_id: str,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get consultation history for a user"""
        
        try:
            query = """
            SELECT 
                id,
                primary_concern,
                consultation_type,
                urgency_level,
                participating_specialists,
                team_recommendation,
                created_at,
                completed_at
            FROM clinical_consultations
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """
            
            async with self.memory_backend.manager.get_connection() as conn:
                results = await conn.fetch(query, user_id, limit)
                
            consultations = []
            for row in results:
                consultation = dict(row)
                consultation["participating_specialists"] = json.loads(consultation["participating_specialists"])
                consultation["team_recommendation"] = json.loads(consultation["team_recommendation"])
                consultations.append(consultation)
            
            return consultations
            
        except Exception as e:
            logger.error(f"Failed to get consultation history: {e}")
            return []


# Clinical consultations table schema
CLINICAL_CONSULTATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS clinical_consultations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    primary_concern TEXT NOT NULL,
    consultation_type VARCHAR(50) NOT NULL,
    urgency_level INTEGER NOT NULL DEFAULT 1,
    participating_specialists JSONB NOT NULL,
    specialist_inputs JSONB DEFAULT '{}',
    team_recommendation JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    INDEX idx_user_consultations (user_id, created_at DESC),
    INDEX idx_urgency_level (urgency_level),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);
"""
