"""
CNS Optimization Specialist - Tier One Operator Performance

This agent analyzes biometric data, particularly HRV patterns, to provide
elite-level insights on central nervous system status, recovery needs,
and performance optimization strategies.

Now integrated with AUREN's three-tier memory system for enhanced pattern
recognition and long-term learning capabilities.
"""

import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END, Task, Crew
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import asyncio

# Import our base agent and memory system
from auren.core.agents.base_agent import BaseAIAgent
from auren.core.memory import MemoryType

# Configure logging for transparency
logger = logging.getLogger(__name__)


class NeuroscientistAgent(BaseAIAgent):
    """
    CNS Optimization Specialist - Tier One Operator Performance
    
    This agent analyzes biometric data, particularly HRV patterns, to provide
    elite-level insights on central nervous system status, recovery needs,
    and performance optimization strategies.
    
    Enhanced with three-tier memory system for:
    - Long-term pattern recognition across athletes
    - Adaptive learning from outcomes
    - Cross-referencing historical cases
    """
    
    def __init__(self, agent_id: str = "neuroscientist_001"):
        # Initialize base agent with memory system
        super().__init__(
            agent_id=agent_id,
            agent_type="medical",
            agent_name="CNS Optimization Specialist",
            description="Elite performance neuroscientist specializing in HRV analysis and CNS optimization",
            metadata={
                "specialization": "CNS_optimization",
                "expertise": ["HRV_analysis", "fatigue_detection", "recovery_protocols"],
                "clearance_level": "medical_professional"
            }
        )
        
        # Ensure OpenAI configuration is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Set the model - GPT-4 for complex CNS analysis
        os.environ["OPENAI_MODEL_NAME"] = "gpt-4"
        
        # Initialize the CrewAI agent with comprehensive backstory
        self.crew_agent = Agent(
            role='Neuroscientist - CNS Optimization Specialist',
            goal='Analyze biometric patterns to optimize central nervous system performance and prevent overtraining',
            backstory="""You are an elite performance neuroscientist who works with tier-one military operators 
            and Olympic athletes. You specialize in:
            - Heart Rate Variability (HRV) analysis and CNS fatigue detection
            - Identifying neuromuscular compensation patterns before they become injuries  
            - Prescribing specific recovery protocols based on neural load
            - Understanding the intricate relationship between training stress and adaptation
            
            You don't just say "get more rest" - you identify specific neural pathways under stress and 
            prescribe targeted interventions. You think in terms of CNS readiness, not just fatigue.
            
            You have access to a sophisticated memory system where you can:
            - Recall similar cases from your experience
            - Learn from past interventions and their outcomes
            - Build long-term profiles of athlete patterns""",
            verbose=True,
            memory=True,   # CrewAI memory still enabled for session context
            max_iter=3,
            allow_delegation=False
        )
        
        logger.info(f"Neuroscientist agent {agent_id} initialized with three-tier memory system")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - routes to appropriate analysis based on input type.
        
        Args:
            input_data: Should contain 'analysis_type' and relevant data
        
        Returns:
            Analysis results with recommendations
        """
        analysis_type = input_data.get("analysis_type", "hrv_analysis")
        
        if analysis_type == "hrv_analysis":
            return await self._process_hrv_analysis(input_data.get("hrv_data", {}))
        elif analysis_type == "training_readiness":
            return await self._process_training_readiness(input_data.get("biometric_history", []))
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    
    async def learn(self, feedback: Dict[str, Any]) -> None:
        """
        Learn from outcomes and feedback to improve future recommendations.
        
        Args:
            feedback: Should contain outcome data and effectiveness metrics
        """
        # Store the learning as a high-importance memory
        await self.remember(
            content=f"Intervention outcome: {feedback}",
            memory_type=MemoryType.EXPERIENCE,
            importance=0.8,
            tags=["outcome", "learning", "feedback"],
            metadata={
                "feedback_type": feedback.get("type", "general"),
                "effectiveness": feedback.get("effectiveness", 0),
                "athlete_id": feedback.get("athlete_id")
            }
        )
    
    async def _process_hrv_analysis(self, hrv_data: Dict) -> Dict[str, Any]:
        """Process HRV analysis with memory augmentation."""
        # First, recall similar cases from memory
        similar_cases = await self.recall(
            query=f"HRV patterns similar to RMSSD={hrv_data.get('rmssd', 0)} and RHR={hrv_data.get('rhr', 0)}",
            memory_types=[MemoryType.EXPERIENCE, MemoryType.KNOWLEDGE],
            limit=5
        )
        
        # Store the current analysis request for future reference
        memory_id = await self.remember(
            content=f"HRV Analysis Request: {hrv_data}",
            memory_type=MemoryType.EXPERIENCE,
            importance=0.6,
            tags=["hrv_analysis", "biometric_data"],
            metadata={"hrv_values": hrv_data}
        )
        
        # Create task with memory context
        task_description = f"""Analyze the following HRV data and provide tier-one operator level insights:
        
        Current HRV Data: {hrv_data}
        
        Similar cases from your experience:
        {self._format_memories_for_context(similar_cases)}
        
        Your analysis should include:
        1. Current CNS status (well-recovered, normal, moderate fatigue, elevated fatigue)
        2. Specific neural patterns you're observing
        3. Risk assessment for overtraining or compensation patterns
        4. Precise recovery protocols (not generic advice)
        5. Training recommendations for the next 24-48 hours
        
        Think like you're advising someone operating at the edge of human performance."""
        
        # Run the analysis
        result = await self._execute_crew_task(task_description)
        
        # Store the analysis result as knowledge
        await self.remember(
            content=f"HRV Analysis Result: {result}",
            memory_type=MemoryType.KNOWLEDGE,
            importance=0.7,
            tags=["hrv_analysis", "recommendations", "cns_status"],
            metadata={
                "input_hrv": hrv_data,
                "related_memory": memory_id
            }
        )
        
        return {
            "analysis": result,
            "similar_cases_found": len(similar_cases),
            "confidence": self._calculate_confidence(similar_cases)
        }
    
    async def _process_training_readiness(self, biometric_history: List[Dict]) -> Dict[str, Any]:
        """Assess training readiness with historical pattern analysis."""
        # Look for patterns in this athlete's history
        athlete_patterns = await self.recall(
            query="training readiness patterns and overtraining indicators",
            memory_types=[MemoryType.KNOWLEDGE, MemoryType.SKILL],
            limit=10
        )
        
        task_description = f"""Assess training readiness based on this biometric history:
        
        Biometric History: {biometric_history}
        
        Known patterns from your expertise:
        {self._format_memories_for_context(athlete_patterns)}
        
        Provide:
        1. Overall readiness score (0-100)
        2. Specific systems status (neural, muscular, metabolic)
        3. Risk factors identified
        4. Recommended training intensity and volume
        5. Specific adaptations to monitor
        
        Consider both acute and chronic load patterns."""
        
        result = await self._execute_crew_task(task_description)
        
        # Learn from this assessment
        await self.remember(
            content=f"Training Readiness Assessment: {result}",
            memory_type=MemoryType.SKILL,
            importance=0.6,
            tags=["readiness_assessment", "training_prescription"],
            ttl_seconds=604800  # Keep in hot tier for 7 days
        )
        
        return {
            "assessment": result,
            "historical_context": len(athlete_patterns) > 0,
            "confidence": self._calculate_confidence(athlete_patterns)
        }
    
    def analyze_hrv_pattern(self, hrv_data: Dict) -> str:
        """
        Synchronous wrapper for backward compatibility with existing code.
        """
        return asyncio.run(self._process_hrv_analysis(hrv_data))["analysis"]
    
    def assess_training_readiness(self, biometric_history: List[Dict]) -> str:
        """
        Synchronous wrapper for backward compatibility with existing code.
        """
        return asyncio.run(self._process_training_readiness(biometric_history))["assessment"]
    
    async def _execute_crew_task(self, task_description: str) -> str:
        """Execute a CrewAI task and return the result."""
        task = # Task migrated to node in StateGraph
        # Original params: description=task_description,
            agent=self.crew_agent,
            expected_output="Detailed analysis with specific, actionable recommendations"
        
        
        crew = StateGraph(dict)
        
        # Build graph from agents and tasks
        for agent in self.agents:
            workflow.add_node(agent.name, agent.process)
        
        # Connect nodes
        workflow.add_edge(START, self.agents[0].name)
        for i in range(len(self.agents) - 1):
            workflow.add_edge(self.agents[i].name, self.agents[i+1].name)
        workflow.add_edge(self.agents[-1].name, END)
        
        return workflow.compile()
        
        # Execute the analysis
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, crew.kickoff)
        return str(result)
    
    def _format_memories_for_context(self, memories: List) -> str:
        """Format memories for inclusion in task context."""
        if not memories:
            return "No similar cases found in memory."
        
        formatted = []
        for i, memory in enumerate(memories[:3], 1):  # Limit to top 3
            formatted.append(f"{i}. {memory.content[:200]}... (confidence: {memory.confidence:.2f})")
        
        return "\n".join(formatted)
    
    def _calculate_confidence(self, similar_cases: List) -> float:
        """Calculate confidence based on similar cases found."""
        if not similar_cases:
            return 0.6  # Base confidence
        
        # Higher confidence with more relevant similar cases
        avg_similarity = sum(m.confidence for m in similar_cases) / len(similar_cases)
        case_factor = min(len(similar_cases) / 5, 1.0)  # Max boost at 5 cases
        
        return min(0.6 + (avg_similarity * 0.3) + (case_factor * 0.1), 0.95) 