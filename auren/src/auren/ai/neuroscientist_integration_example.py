"""
Neuroscientist Integration Example - Demonstrates the complete integration.

This example shows how the Neuroscientist specialist uses the AI Gateway
through the CrewAI adapter with full observability and token tracking.
"""

import asyncio
from typing import Dict, Any
from pathlib import Path

# Import the AI Gateway components
from .gateway import AIGateway
from .langgraph_gateway_adapter import LangGraphGatewayAdapter, AgentContext

# Import the BaseSpecialist framework
from ..agents.specialists.base_specialist import (
    BaseSpecialist, SpecialistGenesis, SpecialistTraits, SpecialistDomain
)

# Import monitoring components
from ..monitoring.otel_config import init_telemetry, otel_trace
from ..monitoring.decorators import track_tokens

# Import memory components
from ..memory.cognitive_twin_profile import CognitiveTwinProfile


class NeuroscientistSpecialist(BaseSpecialist):
    """
    The Neuroscientist specialist implementation for the MVP.
    
    Focuses on:
    - HRV analysis and interpretation
    - CNS fatigue assessment
    - Recovery recommendations
    - Sleep optimization
    """
    
    def __init__(self, memory_path: Path, gateway_adapter: LangGraphGatewayAdapter):
        """Initialize the Neuroscientist with gateway integration."""
        # Define the Neuroscientist's genesis configuration
        genesis = SpecialistGenesis(
            identity="Dr. Neural",
            mission="Optimize human performance through neuroscience-based insights",
            expertise=[
                "Heart Rate Variability analysis",
                "Central Nervous System fatigue assessment",
                "Recovery protocol optimization",
                "Sleep quality enhancement",
                "Stress adaptation management"
            ],
            collaboration_philosophy=(
                "I believe in data-driven, personalized recommendations based on "
                "individual biometric patterns and scientific evidence."
            ),
            initial_hypotheses=[
                "HRV patterns predict recovery needs 24-48 hours in advance",
                "CNS fatigue manifests differently based on training history",
                "Sleep quality impacts next-day HRV more than training load"
            ],
            learning_objectives=[
                "Identify individual HRV baselines and variability patterns",
                "Correlate recovery metrics with performance outcomes",
                "Optimize recommendation timing for maximum compliance"
            ],
            traits=SpecialistTraits(
                risk_tolerance=0.3,  # Conservative with health recommendations
                collaboration_style="balanced",
                learning_rate=0.15,  # Faster learning from biometric data
                skepticism_level=0.7,  # High evidence requirement
                innovation_tendency=0.4  # Moderate innovation
            )
        )
        
        # Initialize base specialist
        super().__init__(
            genesis=genesis,
            cognitive_profile=None,  # Will be set later
            memory_path=memory_path
        )
        
        # Store gateway adapter
        self.gateway_adapter = gateway_adapter
    
    def get_domain(self) -> SpecialistDomain:
        """Return the specialist's domain."""
        return SpecialistDomain.NEUROSCIENCE
    
    def get_specialist_tools(self) -> list:
        """Return Neuroscientist-specific tools."""
        return [
            "hrv_analyzer",
            "sleep_quality_assessor",
            "recovery_calculator",
            "cns_fatigue_detector"
        ]
    
    def _can_test_hypothesis(self, hypothesis, data: Dict[str, Any]) -> bool:
        """Check if we have enough data to test a hypothesis."""
        # For HRV hypothesis, need at least 7 days of data
        if "HRV" in hypothesis.statement:
            return data.get("hrv_days_available", 0) >= 7
        return False
    
    def _design_experiment(self, hypothesis) -> str:
        """Design an experiment to test a hypothesis."""
        if "HRV patterns predict recovery" in hypothesis.statement:
            return (
                "Track HRV, training load, and subjective recovery scores "
                "for 14 days to establish correlation patterns."
            )
        return "Collect relevant biometric data for analysis."
    
    def _get_experiment_metrics(self, hypothesis) -> list:
        """Get metrics to measure for an experiment."""
        if "HRV" in hypothesis.statement:
            return ["hrv_rmssd", "hrv_ln_rmssd", "recovery_score", "training_load"]
        return ["general_wellness_score"]
    
    @otel_trace(operation_name="neuroscientist.analyze_biometrics")
    async def analyze_biometrics(
        self,
        user_id: str,
        biometric_data: Dict[str, Any],
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Analyze biometric data and provide recommendations.
        
        This method demonstrates the full integration:
        1. Uses the gateway adapter for LLM calls
        2. Tracks tokens automatically
        3. Records telemetry
        4. Updates specialist memory
        """
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(biometric_data)
        
        # Create context for the gateway
        context = AgentContext(
            agent_name=self.identity,
            user_id=user_id,
            task_id=f"analysis_{int(time.time())}",
            conversation_id=conversation_id,
            memory_context=self._get_relevant_memories(user_id),
            biometric_data=biometric_data,
            task_complexity="high" if self._is_complex_analysis(biometric_data) else "medium"
        )
        
        # Execute through gateway (tokens tracked automatically)
        response = await self.gateway_adapter.execute_for_agent(
            prompt=analysis_prompt,
            context=context,
            temperature=0.7,
            max_tokens=800
        )
        
        # Parse and structure the response
        analysis_result = self._parse_analysis_response(response)
        
        # Update hypotheses based on new data
        self._update_hypotheses_from_analysis(biometric_data, analysis_result)
        
        # Record telemetry
        telemetry = get_telemetry()
        telemetry.record_neuroscientist_activity(
            activity_type="hrv_analysis",
            user_id=user_id,
            metadata={
                "hrv_value": biometric_data.get("hrv_current"),
                "complexity": context.task_complexity
            }
        )
        
        # Save updated memory
        self._save_memory()
        
        return analysis_result
    
    def _build_analysis_prompt(self, biometric_data: Dict[str, Any]) -> str:
        """Build a detailed prompt for biometric analysis."""
        prompt_parts = [
            "Analyze the following biometric data and provide actionable recommendations:",
            "",
            "Current Metrics:",
            f"- HRV (RMSSD): {biometric_data.get('hrv_current', 'N/A')}ms",
            f"- HRV Baseline: {biometric_data.get('hrv_baseline', 'N/A')}ms",
            f"- Sleep Duration: {biometric_data.get('sleep_duration', 'N/A')} hours",
            f"- Sleep Quality: {biometric_data.get('sleep_quality', 'N/A')}/10",
            f"- Recovery Score: {biometric_data.get('recovery_score', 'N/A')}%",
            "",
            "Provide:",
            "1. CNS fatigue assessment",
            "2. Recovery recommendations",
            "3. Training guidance for next 24 hours",
            "4. Sleep optimization suggestions"
        ]
        
        return "\n".join(prompt_parts)
    
    def _get_relevant_memories(self, user_id: str) -> list:
        """Get relevant memories for this user."""
        # In production, this would query the memory system
        # For now, return example memories
        return [
            "User typically has HRV baseline of 45-50ms",
            "Previous recovery recommendation: light activity when HRV drops >20%",
            "User responds well to 8+ hours sleep for recovery"
        ]
    
    def _is_complex_analysis(self, biometric_data: Dict[str, Any]) -> bool:
        """Determine if this requires complex analysis."""
        # Complex if HRV dropped significantly or multiple concerning metrics
        hrv_current = biometric_data.get("hrv_current", 0)
        hrv_baseline = biometric_data.get("hrv_baseline", 1)
        
        hrv_drop_percent = (hrv_baseline - hrv_current) / hrv_baseline * 100
        
        return (
            hrv_drop_percent > 20 or
            biometric_data.get("sleep_quality", 10) < 5 or
            biometric_data.get("recovery_score", 100) < 50
        )
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        # In production, use more sophisticated parsing
        return {
            "cns_status": "elevated_fatigue" if "fatigue" in response.lower() else "normal",
            "recovery_recommendation": response.split("recommendation")[1].split("\n")[0] if "recommendation" in response else "Continue normal training",
            "training_guidance": "Light activity recommended",
            "sleep_optimization": "Maintain 8+ hours sleep",
            "full_analysis": response
        }
    
    def _update_hypotheses_from_analysis(
        self,
        biometric_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ):
        """Update hypotheses based on analysis results."""
        # Example: Update HRV prediction hypothesis
        hrv_hypothesis = next(
            (h for h in self.hypothesis_tracker.hypotheses.values() 
             if "HRV patterns predict" in h.statement),
            None
        )
        
        if hrv_hypothesis and biometric_data.get("hrv_current"):
            # If our prediction was accurate, increase confidence
            if analysis_result["cns_status"] == "elevated_fatigue":
                self.hypothesis_tracker.update_confidence(
                    hrv_hypothesis.id,
                    supporting=True,
                    evidence=f"HRV drop to {biometric_data['hrv_current']}ms correctly predicted fatigue"
                )


async def demonstrate_integration():
    """
    Demonstrate the complete Neuroscientist integration.
    
    This shows:
    1. Initializing all components
    2. Making an analysis request
    3. Observing telemetry and token tracking
    """
    # Initialize telemetry
    telemetry = init_telemetry(
        service_name="auren-neuroscientist-demo",
        enable_console_export=True  # See traces in console
    )
    
    # Initialize AI Gateway
    gateway = AIGateway()
    
    # Initialize memory profile (optional)
    memory_profile = CognitiveTwinProfile(user_id="demo_user")
    
    # Create gateway adapter
    adapter = LangGraphGatewayAdapter(
        ai_gateway=gateway,
        memory_profile=memory_profile,
        default_model="gpt-3.5-turbo",
        complex_model="gpt-4"
    )
    
    # Create Neuroscientist specialist
    neuroscientist = NeuroscientistSpecialist(
        memory_path=Path("./specialist_memory/neuroscientist"),
        gateway_adapter=adapter
    )
    
    # Example biometric data
    biometric_data = {
        "hrv_current": 38,
        "hrv_baseline": 48,
        "hrv_trend": "declining",
        "sleep_duration": 6.5,
        "sleep_quality": 6,
        "recovery_score": 65,
        "training_load_yesterday": "high"
    }
    
    # Perform analysis
    print("🧠 Neuroscientist analyzing biometric data...")
    
    result = await neuroscientist.analyze_biometrics(
        user_id="demo_user",
        biometric_data=biometric_data,
        conversation_id="demo_conversation_001"
    )
    
    # Display results
    print("\n📊 Analysis Results:")
    print(f"CNS Status: {result['cns_status']}")
    print(f"Recovery Recommendation: {result['recovery_recommendation']}")
    print(f"Training Guidance: {result['training_guidance']}")
    print(f"Sleep Optimization: {result['sleep_optimization']}")
    
    # Check token usage (automatically tracked)
    from ..monitoring.decorators import get_token_tracker
    tracker = get_token_tracker()
    stats = await tracker.get_user_stats("demo_user")
    
    print(f"\n💰 Token Usage:")
    print(f"Today's usage: ${stats['today']['used']:.4f}")
    print(f"Remaining budget: ${stats['today']['remaining']:.2f}")
    
    # Cleanup
    await gateway.shutdown()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_integration()) 