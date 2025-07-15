"""
AUREN with Cognitive Twin Integration
====================================

This module shows how AUREN integrates with the CognitiveTwinService
to track biometrics through natural conversation while maintaining
her warm, intelligent personality.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..services.cognitive_twin_service import CognitiveTwinService
from ..core.database import db

logger = logging.getLogger(__name__)

class AURENWithCognitive:
    """
    AUREN enhanced with Cognitive Twin Service integration.
    
    This class demonstrates how AUREN can seamlessly track user biometrics
    through natural conversation while maintaining her personality.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.cognitive_service = None
        
    async def initialize(self):
        """Initialize database connection and cognitive service."""
        await db.initialize()
        self.cognitive_service = CognitiveTwinService(db.pool)
        logger.info(f"AUREN with Cognitive Twin initialized for {self.user_id}")
    
    async def process_message_with_tracking(self, message: str) -> str:
        """
        Process user message and automatically track any biometric data.
        
        This method extracts weight, energy, sleep, etc. from natural language
        and tracks it without disrupting the conversation flow.
        """
        if not self.cognitive_service:
            await self.initialize()
        
        # Extract and track biometric data
        tracked_data = await self._extract_and_track_biometrics(message)
        
        # Generate contextual response
        response = await self._generate_contextual_response(message, tracked_data)
        
        return response
    
    async def _extract_and_track_biometrics(self, message: str) -> Dict[str, Any]:
        """Extract and track biometric data from natural language."""
        tracked = {}
        
        # Extract weight
        weight_data = self.cognitive_service.extract_weight_from_text(message)
        if weight_data:
            result = await self.cognitive_service.track_weight(
                self.user_id, 
                weight_data["weight"], 
                weight_data["unit"]
            )
            tracked["weight"] = {
                "value": weight_data["weight"],
                "unit": weight_data["unit"],
                "response": result.message
            }
        
        # Extract energy
        energy_level = self.cognitive_service.extract_energy_from_text(message)
        if energy_level:
            result = await self.cognitive_service.track_energy(
                self.user_id, 
                energy_level
            )
            tracked["energy"] = {
                "level": energy_level,
                "response": result["message"]
            }
        
        # Extract sleep
        sleep_data = self.cognitive_service.extract_sleep_from_text(message)
        if sleep_data:
            result = await self.cognitive_service.track_sleep(
                self.user_id,
                sleep_data["hours"],
                sleep_data["quality"]
            )
            tracked["sleep"] = {
                "hours": sleep_data["hours"],
                "response": result["message"]
            }
        
        return tracked
    
    async def _generate_contextual_response(self, message: str, tracked_data: Dict[str, Any]) -> str:
        """Generate natural response that incorporates tracking confirmation."""
        
        # Base response based on message content
        message_lower = message.lower()
        
        # Handle greetings
        if any(word in message_lower for word in ["good morning", "morning", "hello", "hi"]):
            return await self._morning_greeting(tracked_data)
        
        # Handle progress queries
        if any(word in message_lower for word in ["progress", "how am i doing", "results"]):
            return await self._progress_update()
        
        # Handle specific data mentions
        if tracked_data:
            return await self._acknowledge_tracking(tracked_data)
        
        # Default response
        return "I'm here to help! What would you like to explore together?"
    
    async def _morning_greeting(self, tracked_data: Dict[str, Any]) -> str:
        """Generate personalized morning greeting."""
        response_parts = ["Good morning!"]
        
        # Add insights based on tracked data
        if "weight" in tracked_data:
            weight_insights = await self.cognitive_service.get_weight_insights(self.user_id)
            if weight_insights.success and weight_insights.insights.get("patterns_found"):
                response_parts.append(weight_insights.message)
        
        response_parts.append("How are you feeling today?")
        return " ".join(response_parts)
    
    async def _progress_update(self) -> str:
        """Generate progress update with insights."""
        weight_insights = await self.cognitive_service.get_weight_insights(self.user_id)
        energy_insights = await self.cognitive_service.get_energy_insights(self.user_id)
        
        response_parts = ["Here's your progress summary:"]
        
        if weight_insights.success and weight_insights.insights.get("patterns_found"):
            response_parts.append(weight_insights.message)
        
        if energy_insights.success and energy_insights.insights.get("patterns_found"):
            response_parts.append(energy_insights.message)
        
        if len(response_parts) == 1:
            response_parts.append("Keep tracking your data and I'll help you discover your patterns!")
        
        return " ".join(response_parts)
    
    async def _acknowledge_tracking(self, tracked_data: Dict[str, Any]) -> str:
        """Acknowledge tracked data naturally."""
        acknowledgments = []
        
        if "weight" in tracked_data:
            acknowledgments.append(tracked_data["weight"]["response"])
        
        if "energy" in tracked_data:
            acknowledgments.append(tracked_data["energy"]["response"])
        
        if "sleep" in tracked_data:
            acknowledgments.append(tracked_data["sleep"]["response"])
        
        return " ".join(acknowledgments)
    
    async def get_user_summary(self) -> Dict[str, Any]:
        """Get comprehensive user summary."""
        if not self.cognitive_service:
            await self.initialize()
        
        return await self.cognitive_service.get_user_summary(self.user_id)
    
    async def close(self):
        """Clean up database connections."""
        await db.close()

# Demo function
async def demo_auren_integration():
    """Demonstrate AUREN with Cognitive Twin integration."""
    
    print("🧠 AUREN with Cognitive Twin Integration Demo")
    print("=" * 60)
    
    auren = AURENWithCognitive("demo_user_astxryts")
    await auren.initialize()
    
    # Test conversations
    test_conversations = [
        "Good morning! I weighed 218.5 lbs today",
        "Energy is 8 out of 10 this morning",
        "Got 7.5 hours of sleep last night",
        "How's my progress going?",
        "Down to 215 pounds this week!"
    ]
    
    for message in test_conversations:
        print(f"\n👤 User: {message}")
        response = await auren.process_message_with_tracking(message)
        print(f"🤖 AUREN: {response}")
    
    # Show summary
    summary = await auren.get_user_summary()
    print(f"\n📊 User Summary: {summary}")
    
    await auren.close()

if __name__ == "__main__":
    asyncio.run(demo_auren_integration())
