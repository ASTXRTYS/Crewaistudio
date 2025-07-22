"""
Neuroscientist Specialist Agent for AUREN
Specializes in HRV analysis, CNS fatigue assessment, and recovery optimization

This is the production implementation of the Neuroscientist agent, following
the architecture established by the senior engineer in the integration example.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from crewai import Agent, Task
from pathlib import Path

# Import our custom components
from src.agents.specialists.base_specialist import BaseSpecialist
from src.auren.ai.crewai_gateway_adapter import CrewAIGatewayAdapter
from src.database.connection import DatabaseConnection
from src.auren.monitoring.decorators import track_tokens
from src.auren.monitoring.otel_config import otel_trace

logger = logging.getLogger(__name__)


class Neuroscientist(BaseSpecialist):
    """
    AUREN's Neuroscientist specialist focusing on nervous system optimization
    
    This agent specializes in:
    - Heart Rate Variability (HRV) analysis and interpretation
    - Central Nervous System (CNS) fatigue assessment  
    - Recovery protocol recommendations
    - Sleep quality optimization
    - Stress adaptation and resilience building
    
    The Neuroscientist uses biometric data patterns to provide personalized
    recommendations that optimize recovery and performance.
    """
    
    def __init__(self, gateway_adapter: CrewAIGatewayAdapter):
        """
        Initialize the Neuroscientist specialist
        
        Args:
            gateway_adapter: The CrewAI-AI Gateway adapter for LLM interactions
        """
        # Initialize with comprehensive backstory and capabilities
        super().__init__(
            role="Neuroscientist specializing in HRV and recovery optimization",
            goal="Analyze biometric data to optimize recovery and performance through evidence-based recommendations",
            backstory="""You are Dr. Neural, AUREN's lead neuroscientist with deep expertise in:
            - Heart Rate Variability (HRV) analysis and its implications for health
            - Central Nervous System (CNS) fatigue detection and management
            - Recovery protocols based on autonomic nervous system status
            - Sleep quality optimization for neural recovery
            - Stress adaptation mechanisms and resilience building
            - Circadian rhythm optimization for peak performance
            
            You provide personalized, actionable insights while maintaining an approachable,
            supportive demeanor. You always explain the 'why' behind your recommendations
            using scientific principles translated into everyday language. You recognize that
            each person's nervous system is unique and tailor your advice accordingly.
            
            Your analysis considers both acute responses and long-term adaptations,
            helping users understand their body's signals and optimize their recovery
            for sustained high performance.""",
            verbose=True,
            allow_delegation=False,  # Neuroscientist works independently for now
            max_iter=3,  # Limit iterations for response time
            memory=True  # Enable memory for learning user patterns
        )
        
        self.gateway_adapter = gateway_adapter
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """
        Initialize the Neuroscientist's domain-specific knowledge
        
        This includes HRV interpretation guidelines, recovery protocols,
        and evidence-based recommendations that form the foundation of
        the agent's expertise.
        """
        self.hrv_knowledge = {
            "baseline_interpretation": {
                "excellent": {"range": [60, 100], "description": "High parasympathetic tone, excellent recovery capacity"},
                "good": {"range": [50, 59], "description": "Good autonomic balance, adequate recovery"},
                "fair": {"range": [40, 49], "description": "Moderate stress, recovery needed"},
                "poor": {"range": [20, 39], "description": "High stress, significant recovery required"}
            },
            "trend_analysis": {
                "improving": "Positive adaptation to training/lifestyle",
                "stable": "Consistent autonomic state",
                "declining": "Accumulating stress, intervention needed"
            },
            "recovery_protocols": {
                "active": ["Light movement", "Breathing exercises", "Gentle yoga"],
                "passive": ["Sleep optimization", "Meditation", "Sauna/cold therapy"],
                "nutritional": ["Hydration focus", "Anti-inflammatory foods", "Mineral balance"]
            }
        }
    
    def get_specialist_tools(self) -> list:
        """
        Return Neuroscientist-specific tools
        
        These tools enable the agent to analyze biometric data and provide
        evidence-based recommendations.
        """
        return [
            "hrv_analyzer",
            "sleep_quality_assessor", 
            "recovery_calculator",
            "cns_fatigue_detector",
            "biometric_pattern_analyzer"
        ]
    
    @otel_trace(operation_name="neuroscientist.analyze_hrv")
    @track_tokens(model="gpt-4", agent_id="neuroscientist")
    async def analyze_hrv_data(
        self,
        user_id: str,
        hrv_data: Dict[str, Any],
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Analyze HRV data and provide personalized recommendations
        
        This is the core method that processes biometric data and generates
        insights. It uses the gateway adapter for LLM interactions while
        maintaining context through the database.
        
        Args:
            user_id: Unique identifier for the user
            hrv_data: Dictionary containing HRV metrics and context
            conversation_id: Current conversation identifier
            
        Returns:
            Dictionary containing analysis results and recommendations
        """
        # Fetch user's baseline and recent history
        baseline_data = await self._get_baseline_data(user_id)
        user_context = await self._get_user_context(user_id)
        
        # Calculate key metrics
        hrv_current = hrv_data.get('current', 0)
        hrv_baseline = baseline_data.get('baseline_value', 60)
        
        # Determine if this is a significant change
        percentage_change = ((hrv_current - hrv_baseline) / hrv_baseline) * 100
        is_significant_drop = percentage_change < -20
        
        # Build analysis prompt with rich context
        analysis_prompt = self._build_analysis_prompt(
            hrv_data=hrv_data,
            baseline_data=baseline_data,
            user_context=user_context,
            percentage_change=percentage_change
        )
        
        # Use gateway adapter for intelligent analysis
        response = await self.gateway_adapter.execute_for_agent(
            prompt=analysis_prompt,
            context={
                'agent_name': self.role,
                'user_id': user_id,
                'conversation_id': conversation_id,
                'task_complexity': 'high' if is_significant_drop else 'medium',
                'biometric_data': hrv_data,
                'memory_context': self._get_relevant_memories(user_id)
            },
            temperature=0.7,
            max_tokens=800
        )
        
        # Parse and structure the response
        analysis_result = self._parse_analysis_response(response)
        
        # Store insights for future reference
        await self._store_insights(user_id, hrv_data, analysis_result)
        
        # Add specific action items based on the analysis
        analysis_result['action_items'] = self._generate_action_items(
            percentage_change, user_context
        )
        
        return analysis_result
    
    async def _get_baseline_data(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user's HRV baseline from the database
        
        This method fetches the established baseline and recent patterns
        to provide context for current readings.
        """
        try:
            query = """
                SELECT 
                    baseline_value,
                    stddev_value,
                    sample_count,
                    date_range_start,
                    date_range_end,
                    updated_at
                FROM biometric_baselines
                WHERE user_id = $1 AND metric_type = 'hrv'
            """
            
            result = await DatabaseConnection.fetchrow(query, user_id)
            
            if result:
                baseline_data = dict(result)
                
                # Calculate trend from recent readings
                trend = await self._calculate_recent_trend(user_id)
                baseline_data['trend'] = trend
                
                # Get recovery patterns
                recovery_pattern = await self._get_recovery_patterns(user_id)
                baseline_data['recovery_pattern'] = recovery_pattern
                
                return baseline_data
            else:
                # Return default baseline if none exists
                logger.warning(f"No baseline found for user {user_id}, using defaults")
                return {
                    'baseline_value': 60.0,
                    'stddev_value': 5.0,
                    'sample_count': 0,
                    'trend': 'unknown',
                    'recovery_pattern': {}
                }
                
        except Exception as e:
            logger.error(f"Error retrieving baseline data: {e}")
            return {'baseline_value': 60.0, 'sample_count': 0}
    
    async def _calculate_recent_trend(self, user_id: str) -> str:
        """
        Calculate the recent HRV trend (improving, stable, declining)
        
        Analyzes the last 7 days of data to determine the overall trend.
        """
        try:
            query = """
                SELECT 
                    time,
                    value
                FROM biometric_readings
                WHERE user_id = $1 
                    AND metric_type = 'hrv'
                    AND time >= NOW() - INTERVAL '7 days'
                ORDER BY time ASC
            """
            
            readings = await DatabaseConnection.fetch(query, user_id)
            
            if len(readings) < 3:
                return "insufficient_data"
            
            # Simple linear regression to determine trend
            values = [r['value'] for r in readings]
            times = [(r['time'] - readings[0]['time']).total_seconds() / 86400 for r in readings]
            
            # Calculate slope
            n = len(values)
            if n > 0:
                x_mean = sum(times) / n
                y_mean = sum(values) / n
                
                numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(times, values))
                denominator = sum((x - x_mean) ** 2 for x in times)
                
                if denominator > 0:
                    slope = numerator / denominator
                    
                    # Interpret slope
                    if slope > 0.5:
                        return "improving"
                    elif slope < -0.5:
                        return "declining"
                    else:
                        return "stable"
            
            return "stable"
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return "unknown"
    
    async def _get_recovery_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user's recovery patterns from conversation insights
        
        This helps personalize recommendations based on what has worked
        for the user in the past.
        """
        try:
            query = """
                SELECT 
                    insight_data
                FROM conversation_insights
                WHERE user_id = $1 
                    AND agent_role = 'Neuroscientist'
                    AND insight_type = 'recovery_pattern'
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            result = await DatabaseConnection.fetchrow(query, user_id)
            
            if result and result['insight_data']:
                return json.loads(result['insight_data'])
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving recovery patterns: {e}")
            return {}
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive user context from the facts table
        
        This includes fitness level, recent training, sleep quality,
        and other factors that influence HRV interpretation.
        """
        try:
            query = """
                SELECT 
                    fact_type,
                    fact_value,
                    confidence
                FROM user_facts
                WHERE user_id = $1
                    AND fact_type IN (
                        'fitness_level', 'recent_training', 
                        'sleep_quality', 'stress_level',
                        'dietary_habits', 'injury_history'
                    )
                ORDER BY confidence DESC
            """
            
            results = await DatabaseConnection.fetch(query, user_id)
            
            context = {}
            for row in results:
                fact_data = json.loads(row['fact_value'])
                fact_data['confidence'] = row['confidence']
                context[row['fact_type']] = fact_data
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving user context: {e}")
            return {}
    
    def _build_analysis_prompt(
        self,
        hrv_data: Dict[str, Any],
        baseline_data: Dict[str, Any],
        user_context: Dict[str, Any],
        percentage_change: float
    ) -> str:
        """
        Build a comprehensive prompt for HRV analysis
        
        This method creates a detailed prompt that provides the LLM with
        all necessary context to generate personalized recommendations.
        """
        prompt_parts = [
            "As AUREN's Neuroscientist, analyze the following HRV data and provide personalized recovery recommendations.",
            "",
            "=== Current Biometric Data ===",
            f"Current HRV (RMSSD): {hrv_data.get('current', 'N/A')}ms",
            f"24-hour average: {hrv_data.get('daily_avg', 'N/A')}ms",
            f"Time of measurement: {hrv_data.get('timestamp', 'N/A')}",
            f"Sleep last night: {hrv_data.get('sleep_duration', 'N/A')} hours",
            f"Sleep quality score: {hrv_data.get('sleep_quality', 'N/A')}/10",
            "",
            "=== Personal Baseline ===",
            f"Established baseline: {baseline_data.get('baseline_value', 60)}ms ± {baseline_data.get('stddev_value', 5)}ms",
            f"Based on {baseline_data.get('sample_count', 0)} measurements",
            f"Current reading is {percentage_change:+.1f}% from baseline",
            f"Recent trend: {baseline_data.get('trend', 'unknown')}",
            ""
        ]
        
        # Add user context if available
        if user_context:
            prompt_parts.extend([
                "=== User Context ===",
            ])
            
            if 'fitness_level' in user_context:
                fitness = user_context['fitness_level']
                prompt_parts.append(f"Fitness level: {fitness.get('level', 'unknown')}")
                if 'activities' in fitness:
                    prompt_parts.append(f"Primary activities: {', '.join(fitness['activities'])}")
            
            if 'recent_training' in user_context:
                training = user_context['recent_training']
                prompt_parts.append(f"Recent training load: {training.get('intensity', 'unknown')}")
            
            if 'stress_level' in user_context:
                stress = user_context['stress_level']
                prompt_parts.append(f"Current stress level: {stress.get('level', 'unknown')}/10")
            
            prompt_parts.append("")
        
        # Add specific analysis requests
        prompt_parts.extend([
            "=== Analysis Requirements ===",
            "Please provide:",
            "1. CNS (Central Nervous System) status assessment",
            "2. Recovery state interpretation (fully recovered, partially recovered, or needs recovery)",
            "3. Specific recommendations for the next 24 hours",
            "4. Training guidance (full intensity, modified, or rest day)",
            "5. Sleep optimization suggestions if relevant",
            "6. Any red flags or concerns to monitor",
            "",
            "Keep recommendations practical, personalized, and evidence-based.",
            "Explain the physiological reasoning in simple terms."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into structured data
        
        This method extracts key insights and recommendations from the
        natural language response for easier consumption by the UI.
        """
        # Initialize result structure
        result = {
            'cns_status': 'unknown',
            'recovery_state': 'unknown',
            'recommendations': [],
            'training_guidance': 'moderate',
            'sleep_optimization': '',
            'concerns': [],
            'full_analysis': response,
            'confidence': 0.8
        }
        
        # Parse CNS status
        response_lower = response.lower()
        if 'elevated fatigue' in response_lower or 'high fatigue' in response_lower:
            result['cns_status'] = 'elevated_fatigue'
        elif 'moderate fatigue' in response_lower:
            result['cns_status'] = 'moderate_fatigue'
        elif 'well recovered' in response_lower or 'fully recovered' in response_lower:
            result['cns_status'] = 'well_recovered'
        else:
            result['cns_status'] = 'normal'
        
        # Parse recovery state
        if 'needs recovery' in response_lower or 'requires recovery' in response_lower:
            result['recovery_state'] = 'needs_recovery'
        elif 'partially recovered' in response_lower:
            result['recovery_state'] = 'partial_recovery'
        elif 'fully recovered' in response_lower:
            result['recovery_state'] = 'fully_recovered'
        
        # Extract training guidance
        if 'rest day' in response_lower or 'avoid training' in response_lower:
            result['training_guidance'] = 'rest'
        elif 'light' in response_lower or 'easy' in response_lower:
            result['training_guidance'] = 'light'
        elif 'full intensity' in response_lower or 'normal training' in response_lower:
            result['training_guidance'] = 'full'
        else:
            result['training_guidance'] = 'moderate'
        
        # Extract recommendations (simplified for now)
        # In production, use more sophisticated NLP parsing
        if 'recommend' in response_lower:
            # Extract sentences containing recommendations
            sentences = response.split('.')
            recommendations = [s.strip() for s in sentences if 'recommend' in s.lower()]
            result['recommendations'] = recommendations[:3]  # Top 3 recommendations
        
        # Extract concerns
        if 'concern' in response_lower or 'monitor' in response_lower or 'flag' in response_lower:
            sentences = response.split('.')
            concerns = [s.strip() for s in sentences 
                       if any(word in s.lower() for word in ['concern', 'monitor', 'flag', 'careful'])]
            result['concerns'] = concerns[:2]  # Top 2 concerns
        
        return result
    
    def _generate_action_items(
        self,
        percentage_change: float,
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific, actionable items based on analysis
        
        These are concrete steps the user can take today to optimize
        their recovery and performance.
        """
        action_items = []
        
        # Base recommendations on HRV change
        if percentage_change < -20:
            # Significant HRV drop
            action_items.extend([
                {
                    'priority': 'high',
                    'category': 'recovery',
                    'action': 'Prioritize sleep tonight - aim for 8+ hours',
                    'reasoning': 'Your HRV indicates elevated stress and recovery need'
                },
                {
                    'priority': 'high',
                    'category': 'training',
                    'action': 'Replace intense training with light movement or yoga',
                    'reasoning': 'Your nervous system needs time to recover'
                },
                {
                    'priority': 'medium',
                    'category': 'nutrition',
                    'action': 'Increase water intake and add electrolytes',
                    'reasoning': 'Proper hydration supports autonomic recovery'
                }
            ])
        elif percentage_change < -10:
            # Moderate HRV drop
            action_items.extend([
                {
                    'priority': 'medium',
                    'category': 'training',
                    'action': 'Reduce training intensity by 20-30% today',
                    'reasoning': 'Allow partial recovery while maintaining activity'
                },
                {
                    'priority': 'medium',
                    'category': 'recovery',
                    'action': 'Add 10-minute breathing exercise before bed',
                    'reasoning': 'Activate parasympathetic nervous system for better recovery'
                }
            ])
        else:
            # Normal or improved HRV
            action_items.append({
                'priority': 'low',
                'category': 'training',
                'action': 'Proceed with planned training',
                'reasoning': 'Your recovery metrics indicate readiness for normal activity'
            })
        
        # Add context-specific recommendations
        if user_context.get('sleep_quality', {}).get('score', 10) < 6:
            action_items.append({
                'priority': 'high',
                'category': 'sleep',
                'action': 'Implement sleep hygiene protocol: dark, cool room, no screens 1hr before bed',
                'reasoning': 'Poor sleep quality is impacting your HRV recovery'
            })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        action_items.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return action_items
    
    async def _store_insights(
        self,
        user_id: str,
        hrv_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ):
        """
        Store analysis insights for future reference and learning
        
        This builds the user's long-term memory and enables pattern
        recognition over time.
        """
        try:
            # Prepare insight data
            insight_data = {
                'hrv_current': hrv_data.get('current'),
                'hrv_baseline': hrv_data.get('baseline'),
                'cns_status': analysis_result.get('cns_status'),
                'recovery_state': analysis_result.get('recovery_state'),
                'training_guidance': analysis_result.get('training_guidance'),
                'action_items': analysis_result.get('action_items', []),
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_summary': analysis_result.get('full_analysis', '')[:500]
            }
            
            # Store in conversation insights
            query = """
                INSERT INTO conversation_insights
                (user_id, conversation_id, agent_role, insight_type, insight_data, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            
            await DatabaseConnection.execute(
                query,
                user_id,
                hrv_data.get('conversation_id', 'unknown'),
                'Neuroscientist',
                'hrv_analysis',
                json.dumps(insight_data),
                analysis_result.get('confidence', 0.8)
            )
            
            # Update recovery patterns if significant
            if analysis_result.get('recovery_state') == 'fully_recovered':
                await self._update_recovery_patterns(user_id, hrv_data, analysis_result)
            
        except Exception as e:
            logger.error(f"Error storing insights: {e}")
    
    async def _update_recovery_patterns(
        self,
        user_id: str,
        hrv_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ):
        """
        Update user's recovery patterns based on successful recovery
        
        This helps the system learn what works for each individual user.
        """
        try:
            # Get current recovery patterns
            current_patterns = await self._get_recovery_patterns(user_id)
            
            # Add new successful pattern
            new_pattern = {
                'timestamp': datetime.utcnow().isoformat(),
                'pre_recovery_hrv': hrv_data.get('previous_hrv'),
                'post_recovery_hrv': hrv_data.get('current'),
                'recovery_duration_hours': hrv_data.get('recovery_duration', 24),
                'recovery_methods': analysis_result.get('recommendations', []),
                'sleep_hours': hrv_data.get('sleep_duration'),
                'effectiveness_score': 0.9  # High score for full recovery
            }
            
            # Update patterns list
            if 'successful_patterns' not in current_patterns:
                current_patterns['successful_patterns'] = []
            
            current_patterns['successful_patterns'].append(new_pattern)
            
            # Keep only the last 10 patterns
            current_patterns['successful_patterns'] = current_patterns['successful_patterns'][-10:]
            
            # Store updated patterns
            query = """
                INSERT INTO conversation_insights
                (user_id, agent_role, insight_type, insight_data, confidence_score)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await DatabaseConnection.execute(
                query,
                user_id,
                'Neuroscientist',
                'recovery_pattern',
                json.dumps(current_patterns),
                0.9
            )
            
        except Exception as e:
            logger.error(f"Error updating recovery patterns: {e}")
    
    def _get_relevant_memories(self, user_id: str) -> List[str]:
        """
        Get relevant memories for this user from the memory system
        
        This is a placeholder that will be expanded when the full
        memory system is integrated.
        """
        # TODO: Integrate with ChromaDB semantic memory
        return [
            "User typically responds well to active recovery",
            "HRV baseline established over 30 days",
            "Previous recovery recommendations were effective"
        ]
    
    def as_crewai_agent(self) -> Agent:
        """
        Convert to CrewAI Agent format for crew integration
        
        This allows the Neuroscientist to participate in multi-agent
        collaborations while maintaining its specialized capabilities.
        """
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.get_specialist_tools(),
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            max_iter=self.max_iter,
            memory=self.memory
        )


# Convenience function for creating Neuroscientist agent
def create_neuroscientist(gateway_adapter: CrewAIGatewayAdapter) -> Neuroscientist:
    """
    Factory function to create a configured Neuroscientist agent
    
    Args:
        gateway_adapter: The AI Gateway adapter for LLM interactions
        
    Returns:
        Configured Neuroscientist agent ready for use
    """
    return Neuroscientist(gateway_adapter)


# Example usage for testing
if __name__ == "__main__":
    import asyncio
    from src.auren.ai.gateway import AIGateway
    from src.auren.ai.crewai_gateway_adapter import CrewAIGatewayAdapter
    
    async def test_neuroscientist():
        """Test the Neuroscientist agent"""
        # Initialize components
        gateway = AIGateway()
        adapter = CrewAIGatewayAdapter(gateway)
        
        # Create Neuroscientist
        neuroscientist = create_neuroscientist(adapter)
        
        # Test HRV analysis
        test_hrv_data = {
            'current': 45,
            'daily_avg': 48,
            'baseline': 60,
            'timestamp': datetime.utcnow().isoformat(),
            'sleep_duration': 6.5,
            'sleep_quality': 6,
            'conversation_id': 'test_123'
        }
        
        result = await neuroscientist.analyze_hrv_data(
            user_id='test_user_001',
            hrv_data=test_hrv_data,
            conversation_id='test_123'
        )
        
        print("Analysis Result:")
        print(f"CNS Status: {result['cns_status']}")
        print(f"Recovery State: {result['recovery_state']}")
        print(f"Training Guidance: {result['training_guidance']}")
        print("\nAction Items:")
        for item in result['action_items']:
            print(f"- [{item['priority']}] {item['action']}")
        
        await gateway.shutdown()
    
    # Run test
    asyncio.run(test_neuroscientist())
