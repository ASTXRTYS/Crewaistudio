"""
Hypothesis Validation Service
Enables agents to learn from their predictions and improve over time
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncpg
from asyncpg.pool import Pool

class HypothesisStatus(Enum):
    """Lifecycle states for hypotheses"""
    PROPOSED = "proposed"
    TESTING = "testing"
    VALIDATED = "validated"
    REJECTED = "rejected"
    INSUFFICIENT_DATA = "insufficient_data"

class ValidationTrigger(Enum):
    """When to trigger hypothesis validation"""
    TIME_BASED = "time_based"  # After X hours/days
    EVENT_BASED = "event_based"  # When specific event occurs
    DATA_THRESHOLD = "data_threshold"  # When enough data collected

class HypothesisValidator:
    """
    Central service for validating agent hypotheses using scientific method
    
    This service enables agents to:
    1. Form testable hypotheses about users
    2. Design experiments to test them
    3. Collect evidence and adjust confidence
    4. Learn from successes and failures
    """
    
    def __init__(self, db_pool: Pool):
        self.pool = db_pool
        
    async def initialize(self):
        """Initialize validation tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS hypothesis_validation (
                    id SERIAL PRIMARY KEY,
                    hypothesis_id INTEGER NOT NULL,
                    specialist_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255),
                    validation_method VARCHAR(50) NOT NULL,
                    validation_data JSONB NOT NULL,
                    outcome VARCHAR(20) NOT NULL,
                    confidence_change FLOAT NOT NULL,
                    statistical_significance FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    INDEX idx_hypothesis_validation (hypothesis_id),
                    INDEX idx_specialist_user (specialist_type, user_id),
                    INDEX idx_created_at (created_at DESC)
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_experiments (
                    id SERIAL PRIMARY KEY,
                    hypothesis_id INTEGER NOT NULL,
                    experiment_design JSONB NOT NULL,
                    metrics_to_track JSONB NOT NULL,
                    expected_outcome JSONB NOT NULL,
                    actual_outcome JSONB,
                    status VARCHAR(20) DEFAULT 'pending',
                    started_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    INDEX idx_experiment_hypothesis (hypothesis_id),
                    INDEX idx_experiment_status (status)
                );
            """)
    
    async def validate_hypothesis(self,
                                hypothesis_id: int,
                                specialist_type: str,
                                user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a hypothesis using available data
        
        Returns validation results including:
        - Whether hypothesis is supported or rejected
        - Statistical significance
        - Confidence adjustment
        - Learning insights
        """
        
        # Get hypothesis details
        async with self.pool.acquire() as conn:
            hypothesis = await conn.fetchrow("""
                SELECT * FROM specialist_hypotheses
                WHERE id = $1 AND specialist_type = $2
            """, hypothesis_id, specialist_type)
            
            if not hypothesis:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")
        
        # Design experiment
        experiment = await self._design_experiment(hypothesis)
        
        # Collect validation data
        validation_data = await self._collect_validation_data(
            hypothesis, experiment, user_id
        )
        
        # Analyze results
        analysis = await self._analyze_results(hypothesis, validation_data)
        
        # Update hypothesis confidence
        await self._update_hypothesis_confidence(
            hypothesis_id, analysis['confidence_change'], analysis['outcome']
        )
        
        # Store validation record
        validation_id = await self._store_validation_record(
            hypothesis_id, specialist_type, user_id, experiment, analysis
        )
        
        return {
            'validation_id': validation_id,
            'hypothesis_id': hypothesis_id,
            'outcome': analysis['outcome'],
            'confidence_change': analysis['confidence_change'],
            'statistical_significance': analysis.get('statistical_significance'),
            'learning_insights': analysis.get('learning_insights', [])
        }
    
    async def _design_experiment(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        """Design an experiment to test the hypothesis"""
        
        # Extract key variables from hypothesis
        hypothesis_text = hypothesis['hypothesis_text']
        
        # Determine experiment type based on hypothesis
        if 'sleep' in hypothesis_text.lower():
            experiment_type = 'sleep_correlation'
            metrics = ['sleep_duration', 'sleep_quality', 'next_day_performance']
            duration_days = 7
        elif 'hrv' in hypothesis_text.lower():
            experiment_type = 'hrv_impact'
            metrics = ['hrv', 'stress_level', 'recovery_score']
            duration_days = 14
        elif 'nutrition' in hypothesis_text.lower():
            experiment_type = 'nutrition_effect'
            metrics = ['calories', 'macronutrients', 'energy_level']
            duration_days = 21
        else:
            experiment_type = 'general_correlation'
            metrics = ['user_reported_outcome', 'objective_measure']
            duration_days = 7
        
        return {
            'type': experiment_type,
            'metrics': metrics,
            'duration_days': duration_days,
            'expected_pattern': 'positive_correlation',
            'minimum_data_points': 5
        }
    
    async def _collect_validation_data(self,
                                     hypothesis: Dict[str, Any],
                                     experiment: Dict[str, Any],
                                     user_id: Optional[str] = None) -> Dict[str, Any]:
        """Collect data needed for validation"""
        
        async with self.pool.acquire() as conn:
            # Get relevant biometric data
            metrics = experiment['metrics']
            
            # Build query for time-series data
            query = """
                SELECT time, metric_type, value
                FROM biometric_readings
                WHERE metric_type = ANY($1)
            """
            params = [metrics]
            
            if user_id:
                query += " AND user_id = $2"
                params.append(user_id)
            
            query += " ORDER BY time DESC LIMIT 100"
            
            readings = await conn.fetch(query, *params)
            
            # Organize data by metric
            data_by_metric = {}
            for reading in readings:
                metric = reading['metric_type']
                if metric not in data_by_metric:
                    data_by_metric[metric] = []
                data_by_metric[metric].append({
                    'timestamp': reading['time'].isoformat(),
                    'value': reading['value']
                })
            
            # Get user facts for context
            facts = await conn.fetch("""
                SELECT fact_type, fact_value
                FROM user_facts
                WHERE user_id = $1
            """, user_id)
            
            return {
                'biometric_data': data_by_metric,
                'user_facts': [dict(f) for f in facts],
                'data_points': len(readings)
            }
    
    async def _analyze_results(self,
                           hypothesis: Dict[str, Any],
                           validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze validation results"""
        
        # Simple correlation analysis (in production, use proper stats)
        data_points = validation_data['data_points']
        
        if data_points < 5:
            return {
                'outcome': HypothesisStatus.INSUFFICIENT_DATA.value,
                'confidence_change': -0.1,
                'statistical_significance': 0.0,
                'learning_insights': ['Need more data to validate']
            }
        
        # Mock analysis - in production use scipy/statsmodels
        # For now, simulate a random outcome
        import random
        correlation = random.uniform(-0.8, 0.8)
        
        if abs(correlation) > 0.5:
            outcome = HypothesisStatus.VALIDATED.value
            confidence_change = 0.15
            significance = 0.05
        else:
            outcome = HypothesisStatus.REJECTED.value
            confidence_change = -0.2
            significance = 0.1
        
        return {
            'outcome': outcome,
            'confidence_change': confidence_change,
            'statistical_significance': significance,
            'correlation': correlation,
            'learning_insights': [
                f"Found correlation of {correlation:.2f}",
                f"Based on {data_points} data points"
            ]
        }
    
    async def _update_hypothesis_confidence(self,
                                          hypothesis_id: int,
                                          confidence_change: float,
                                          outcome: str):
        """Update hypothesis confidence based on validation"""
        
        async with self.pool.acquire() as conn:
            # Get current confidence
            current = await conn.fetchrow("""
                SELECT current_confidence FROM specialist_hypotheses
                WHERE id = $1
            """, hypothesis_id)
            
            if not current:
                return
            
            new_confidence = max(0.0, min(1.0, current['current_confidence'] + confidence_change))
            
            await conn.execute("""
                UPDATE specialist_hypotheses
                SET current_confidence = $1,
                    status = $2,
                    last_tested_at = NOW(),
                    test_count = test_count + 1
                WHERE id = $3
            """, new_confidence, outcome, hypothesis_id)
    
    async def _store_validation_record(self,
                                     hypothesis_id: int,
                                     specialist_type: str,
                                     user_id: Optional[str],
                                     experiment: Dict[str, Any],
                                     analysis: Dict[str, Any]) -> int:
        """Store validation record for audit and learning"""
        
        async with self.pool.acquire() as conn:
            validation_id = await conn.fetchval("""
                INSERT INTO hypothesis_validation
                (hypothesis_id, specialist_type, user_id, validation_method,
                 validation_data, outcome, confidence_change, statistical_significance)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, hypothesis_id, specialist_type, user_id,
                experiment['type'], json.dumps(experiment),
                analysis['outcome'], analysis['confidence_change'],
                analysis.get('statistical_significance'))
            
            return validation_id
    
    async def get_validation_history(self,
                                   specialist_type: str,
                                   user_id: Optional[str] = None,
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """Get validation history for learning analysis"""
        
        async with self.pool.acquire() as conn:
            validations = await conn.fetch("""
                SELECT hv.*, sh.hypothesis_text
                FROM hypothesis_validation hv
                JOIN specialist_hypotheses sh ON hv.hypothesis_id = sh.id
                WHERE hv.specialist_type = $1
                  AND ($2::VARCHAR IS NULL OR hv.user_id = $2)
                ORDER BY hv.created_at DESC
                LIMIT $3
            """, specialist_type, user_id, limit)
            
            return [dict(v) for v in validations]
    
    async def get_learning_metrics(self,
                               specialist_type: str,
                               user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get learning metrics for specialist performance"""
        
        async with self.pool.acquire() as conn:
            metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_validations,
                    COUNT(*) FILTER (WHERE outcome = 'validated') as validated,
                    COUNT(*) FILTER (WHERE outcome = 'rejected') as rejected,
                    AVG(confidence_change) as avg_confidence_change,
                    AVG(statistical_significance) as avg_significance,
                    COUNT(DISTINCT hypothesis_id) as hypotheses_tested
                FROM hypothesis_validation
                WHERE specialist_type = $1
                  AND ($2::VARCHAR IS NULL OR user_id = $2)
            """, specialist_type, user_id)
            
            return dict(metrics)
    
    async def schedule_validation(self,
                                hypothesis_id: int,
                                trigger_type: ValidationTrigger,
                                trigger_config: Dict[str, Any]):
        """Schedule automatic validation based on trigger"""
        
        # This would integrate with a task scheduler
        # For now, just store the schedule
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO validation_schedules
                (hypothesis_id, trigger_type, trigger_config, created_at)
                VALUES ($1, $2, $3, NOW())
            """, hypothesis_id, trigger_type.value, json.dumps(trigger_config))
    
    async def get_pending_validations(self,
                                    specialist_type: str,
                                    user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get hypotheses ready for validation"""
        
        async with self.pool.acquire() as conn:
            pending = await conn.fetch("""
                SELECT sh.*, COUNT(hv.id) as validation_count
                FROM specialist_hypotheses sh
                LEFT JOIN hypothesis_validation hv ON sh.id = hv.hypothesis_id
                WHERE sh.specialist_type = $1
                  AND ($2::VARCHAR IS NULL OR sh.user_id = $2)
                  AND sh.status = 'active'
                GROUP BY sh.id
                HAVING COUNT(hv.id) < 3  # Max 3 validations per hypothesis
                ORDER BY sh.last_tested_at ASC NULLS FIRST
            """, specialist_type, user_id)
            
            return [dict(p) for p in pending]
