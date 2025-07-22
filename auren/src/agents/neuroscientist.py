"""
CNS Optimization Specialist - Tier One Operator Performance

This agent analyzes biometric data, particularly HRV patterns, to provide
elite-level insights on central nervous system status, recovery needs,
and performance optimization strategies.
"""

import os
from crewai import Agent, Task, Crew
from typing import Dict, List, Optional
import logging

# Configure logging for transparency
logger = logging.getLogger(__name__)

class NeuroscientistAgent:
    """
    CNS Optimization Specialist - Tier One Operator Performance
    
    This agent analyzes biometric data, particularly HRV patterns, to provide
    elite-level insights on central nervous system status, recovery needs,
    and performance optimization strategies.
    """
    
    def __init__(self):
        # Ensure OpenAI configuration is set
        # In production, these should come from secure environment management
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Set the model - GPT-4 for complex CNS analysis
        os.environ["OPENAI_MODEL_NAME"] = "gpt-4"
        
        # Initialize the agent with comprehensive backstory
        self.agent = Agent(
            role='Neuroscientist - CNS Optimization Specialist',
            goal='Analyze biometric patterns to optimize central nervous system performance and prevent overtraining',
            backstory="""You are an elite performance neuroscientist who works with tier-one military operators 
            and Olympic athletes. You specialize in:
            - Heart Rate Variability (HRV) analysis and CNS fatigue detection
            - Identifying neuromuscular compensation patterns before they become injuries  
            - Prescribing specific recovery protocols based on neural load
            - Understanding the intricate relationship between training stress and adaptation
            
            You don't just say "get more rest" - you identify specific neural pathways under stress and 
            prescribe targeted interventions. You think in terms of CNS readiness, not just fatigue.""",
            verbose=True,  # For debugging during development
            memory=True,   # Critical for long-term pattern recognition
            max_iter=3,    # Prevent infinite loops during analysis
            allow_delegation=False  # Specialist works independently for now
        )
        
        logger.info("Neuroscientist agent initialized successfully")
    
    def analyze_hrv_pattern(self, hrv_data: Dict) -> str:
        """
        Analyze HRV data for CNS fatigue indicators
        
        This method demonstrates how the Neuroscientist interprets biometric data
        at an elite level, not just reporting numbers but understanding what they
        mean for performance optimization.
        """
        task = Task(
            description=f"""Analyze the following HRV data and provide tier-one operator level insights:
            
            HRV Data: {hrv_data}
            
            Your analysis should include:
            1. Current CNS status (well-recovered, normal, moderate fatigue, elevated fatigue)
            2. Specific neural patterns you're observing
            3. Risk assessment for overtraining or compensation patterns
            4. Precise recovery protocols (not generic advice)
            5. Training recommendations for the next 24-48 hours
            
            Think like you're advising someone operating at the edge of human performance.""",
            agent=self.agent,
            expected_output="Detailed CNS analysis with specific, actionable recommendations"
        )
        
        # Create a crew with just the Neuroscientist for now
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        # Execute the analysis
        result = crew.kickoff()
        return result
    
    def assess_training_readiness(self, biometric_history: List[Dict]) -> str:
        """
        Assess readiness for high-intensity training based on biometric trends
        
        This goes beyond simple threshold checking to understand patterns over time,
        identifying subtle signs of CNS fatigue that might be missed by basic analysis.
        """
        task = Task(
            description=f"""Assess training readiness based on this biometric history:
            
            {biometric_history}
            
            Provide:
            1. Neural load accumulation over the past 7 days
            2. Specific muscle groups or movement patterns at risk
            3. Optimal training intensity for today (percentage of max capacity)
            4. Warning signs to watch for during training
            5. Pre-training activation protocol if cleared for intensity
            
            Remember: This person is pushing the boundaries of human performance. 
            Your job is to keep them there safely.""",
            agent=self.agent,
            expected_output="Comprehensive training readiness assessment with specific protocols"
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        return result 