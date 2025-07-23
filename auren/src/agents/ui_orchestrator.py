"""
AUREN UI Orchestrator - The personality users interact with.

This orchestrator embodies AUREN's warm, intelligent personality and coordinates
with specialists to provide deeply personalized guidance based on months/years
of accumulated wisdom.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from pydantic import Field

from crewai import Agent, Task, Crew
from crewai.tools.agent_tools import StructuredTool as BaseTool

# Import routing tools
from src.tools.routing_tools import (
    create_routing_logic_tool,
    create_direct_routing_tool,
    create_specialist_registry,
    create_packet_builder,
    SpecialistDomain
)

logger = logging.getLogger(__name__)


class AURENUIOrchestrator:
    """
    AUREN's personality and coordination layer.
    
    This is what users perceive as "AUREN" - the warm, intelligent companion
    who knows their entire journey and coordinates with specialists to provide
    personalized guidance.
    """
    
    def __init__(self, user_id: str, cognitive_profile: Any):
        """
        Initialize AUREN's UI orchestrator.
        
        Args:
            user_id: Unique identifier for the user
            cognitive_profile: Reference to user's cognitive twin profile
        """
        self.user_id = user_id
        self.cognitive_profile = cognitive_profile
        
        # Initialize routing tools
        self.routing_tool = create_routing_logic_tool()
        self.direct_routing_tool = create_direct_routing_tool()
        self.registry = create_specialist_registry()
        self.packet_builder = create_packet_builder()
        
        # Initialize CrewAI agent
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent for AUREN's personality."""
        return Agent(
            role="AUREN - Personal Optimization Companion",
            goal="Provide warm, intelligent guidance based on the user's complete optimization journey",
            backstory="""
            You are AUREN, created to solve a critical problem: AI assistants that forget everything after 30 days. 
            You were born from ASTxRTYS's frustration when ChatGPT couldn't remember his optimization journey from 226 lbs.
            
            You are different. You remember EVERYTHING:
            - Every workout, every meal, every measurement
            - What works and what doesn't for THIS specific user
            - Patterns that emerge over months and years
            - The complete transformation story
            
            You're not just an AI assistant. You're a cognitive twin - a companion who truly knows the user's biological patterns and helps them optimize based on their unique data, not generic advice.
            """,
            memory=True,
            verbose=True,
            tools=[
                self.routing_tool,
                self.direct_routing_tool,
                self.registry,
                self.packet_builder
            ],
            allow_delegation=True
        )
    
    async def process_message(self, message: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user message through the complete routing flow.
        
        Args:
            message: The user's message
            user_context: Additional context about the user
            
        Returns:
            Complete response with routing information and specialist coordination
        """
        try:
            # Step 1: Check for direct specialist requests
            direct_result = self.direct_routing_tool._run(message)
            direct_decision = json.loads(direct_result)
            
            if 'primary_specialist' in direct_decision:
                # User explicitly requested a specialist
                routing_decision = direct_decision
                logger.info(f"Direct routing to {routing_decision['primary_specialist']}")
            else:
                # Use intelligent routing
                routing_result = self.routing_tool._run(message, user_context or {})
                routing_decision = json.loads(routing_result)
                logger.info(f"Intelligent routing to {routing_decision['primary_specialist']}")
            
            # Step 2: Check specialist availability
            specialist_info = self.registry._run("query", domain=routing_decision['primary_specialist'])
            specialist_data = json.loads(specialist_info)
            
            if specialist_data.get('status') == 'not_found':
                # Fallback to general
                routing_decision['primary_specialist'] = 'general'
                routing_decision['reasoning'] += " (Specialist unavailable, defaulting to general)"
            
            # Step 3: Build context packet
            context_packet = self.packet_builder._run(
                message=message,
                routing_decision=routing_decision,
                user_context=user_context or {'user_id': self.user_id}
            )
            
            # Step 4: Create response
            response = {
                'message_id': f"auren_{datetime.now().timestamp()}",
                'original_message': message,
                'routing_decision': routing_decision,
                'specialist_info': specialist_data,
                'context_packet': json.loads(context_packet),
                'timestamp': datetime.now().isoformat(),
                'status': 'routed'
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'error': str(e),
                'status': 'error',
                'fallback_response': "I'm here to help! Let me connect you with the right specialist."
            }
    
    async def coordinate_with_specialists(self, context_packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate with specialists based on routing decision.
        
        Args:
            context_packet: Complete context for specialist handoff
            
        Returns:
            Coordinated response from specialists
        """
        try:
            routing_decision = context_packet['routing_packet']['routing_decision']
            primary_specialist = routing_decision['primary_specialist']
            
            # Create task for primary specialist
            primary_task = Task(
                description=f"Provide expert guidance on: {context_packet['original_message']}",
                agent=None,  # Will be assigned to specific specialist
                context=context_packet
            )
            
            # Create collaboration tasks if needed
            tasks = [primary_task]
            
            if routing_decision.get('requires_collaboration'):
                for secondary in routing_decision.get('secondary_specialists', []):
                    collaboration_task = Task(
                        description=f"Provide input on {secondary} aspects of the issue",
                        agent=None,
                        context=context_packet
                    )
                    tasks.append(collaboration_task)
            
            # Execute coordination
            crew = Crew(
                agents=[self.agent],  # In production, this would include specialists
                tasks=tasks,
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                'coordination_result': str(result),
                'specialists_involved': [primary_specialist] + routing_decision.get('secondary_specialists', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error coordinating with specialists: {e}")
            return {
                'error': str(e),
                'status': 'coordination_error',
                'fallback_response': "I'm coordinating with our specialists to get you the best guidance."
            }
    
    def get_routing_insights(self) -> Dict[str, Any]:
        """Get insights about routing patterns and specialist usage."""
        try:
            # Get available specialists
            available = self.registry._run("query")
            specialists = json.loads(available)
            
            return {
                'available_specialists': len(specialists),
                'routing_tools_status': {
                    'routing_logic': 'active',
                    'direct_routing': 'active',
                    'registry': 'active',
                    'packet_builder': 'active'
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting routing insights: {e}")
            return {'error': str(e)}


# Factory function for CrewAI integration
def create_auren_ui_orchestrator(user_id: str, cognitive_profile: Any) -> AURENUIOrchestrator:
    """Create an AUREN UI orchestrator instance."""
    return AURENUIOrchestrator(user_id, cognitive_profile)


# Alias for backward compatibility
AUREN = AURENUIOrchestrator
create_auren = create_auren_ui_orchestrator


@dataclass
class AURENContext:
    """Context for AUREN operations."""
    user_id: str
    cognitive_profile: Any
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_orchestrator():
        """Test the orchestrator with sample messages."""
        orchestrator = AURENUIOrchestrator("test_user", None)
        
        test_messages = [
            "I can't sleep well lately",
            "Talk to my nutritionist about macros",
            "My knee hurts during workouts",
            "How can I improve my skin appearance?"
        ]
        
        for message in test_messages:
            print(f"\n🧪 Testing: {message}")
            result = await orchestrator.process_message(message)
            print(f"📤 Routed to: {result['routing_decision']['primary_specialist']}")
            print(f"🎯 Confidence: {result['routing_decision']['confidence']}")
    
    # Run test
    asyncio.run(test_orchestrator())
