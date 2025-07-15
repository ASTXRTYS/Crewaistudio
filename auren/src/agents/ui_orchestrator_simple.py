"""
AUREN - Simplified Cognitive Twin Interface
==========================================

This module provides a simplified version of AUREN that can be used
for testing and development without external dependencies.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimpleAURENContext:
    """Simplified context for AUREN interactions"""
    user_id: str
    timestamp: datetime
    message: str
    session_id: str
    metadata: Dict[str, Any]


class SimpleAUREN:
    """
    Simplified AUREN implementation for testing and development
    
    This version provides the core AUREN personality without external
    dependencies, making it easy to test the interface and logic.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize SimpleAUREN for a specific user
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.name = "AUREN"
        self.role = "Personal Optimization Companion"
        
        # Mock data for testing
        self.mock_data = {
            "user_patterns": {
                "optimal_workout_time": "morning",
                "optimal_breakfast_macros": {"protein": 40, "carbs": 30, "fat": 15},
                "weekly_training_volume": 4,
                "training_split": "upper/lower"
            },
            "recent_data": {
                "last_workout": datetime.now() - timedelta(days=2),
                "cns_recovery": "good",
                "sleep_wake_time": datetime.now().replace(hour=7, minute=0)
            },
            "progress": {
                "fat_loss_lbs": 12,
                "muscle_gain_lbs": 8,
                "strength_improvements": {
                    "bench_press": {"current": 185, "starting": 135, "improvement_percent": 37},
                    "squat": {"current": 225, "starting": 185, "improvement_percent": 22}
                }
            },
            "milestones": [
                {
                    "milestone": "100lb bench press",
                    "description": "First time hitting triple digits",
                    "days_to_achieve": 45
                }
            ]
        }
        
        # Store interactions for memory simulation
        self.interactions = []
        
    async def process_message(self, message: str) -> str:
        """
        Process a user message with simulated historical context
        
        Args:
            message: The user's input message
            
        Returns:
            AUREN's personalized response based on mock data
        """
        try:
            # Store interaction
            self.interactions.append({
                "timestamp": datetime.now(),
                "message": message.lower().strip(),
                "response": None
            })
            
            # Generate contextual greeting if appropriate
            if self._is_greeting(message):
                return await self._generate_contextual_greeting()
            
            # Analyze intent and generate response
            intent = self._analyze_intent(message)
            
            # Route to appropriate handler
            if intent["type"] == "nutrition":
                return await self._handle_nutrition_query(message, intent)
            elif intent["type"] == "workout":
                return await self._handle_workout_query(message, intent)
            elif intent["type"] == "progress":
                return await self._handle_progress_query(message, intent)
            elif intent["type"] == "milestone":
                return await self._handle_milestone_query(message, intent)
            else:
                return await self._handle_general_query(message, intent)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm here to help! Could you tell me more about what you're looking for?"
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = {"good morning", "morning", "hello", "hi", "hey", "good evening", "good afternoon"}
        return any(greeting in message.lower() for greeting in greetings)
    
    async def _generate_contextual_greeting(self) -> str:
        """Generate a personalized greeting with mock historical context"""
        current_hour = datetime.now().hour
        
        if current_hour < 12:
            greeting = "Good morning!"
        elif current_hour < 17:
            greeting = "Good afternoon!"
        else:
            greeting = "Good evening!"
        
        # Add contextual awareness based on mock data
        response_parts = [greeting]
        
        if self.mock_data["recent_data"]["cns_recovery"] == "good":
            last_workout = self.mock_data["recent_data"]["last_workout"]
            day_name = last_workout.strftime('%A')
            response_parts.append(
                f"Your CNS recovery from {day_name}'s session looks good based on yesterday's check-in."
            )
        
        if self.mock_data["user_patterns"]["optimal_workout_time"] == "morning":
            response_parts.append(
                "Based on your energy patterns, morning workouts have consistently given you the best results."
            )
        
        response_parts.append("How are you feeling today?")
        
        return " ".join(response_parts)
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent from message"""
        message_lower = message.lower()
        
        # Nutrition-related keywords
        nutrition_keywords = {
            "eat", "food", "meal", "breakfast", "lunch", "dinner", "snack",
            "calories", "protein", "carbs", "fat", "macro", "nutrition"
        }
        
        # Workout-related keywords
        workout_keywords = {
            "workout", "exercise", "gym", "lift", "cardio", "training", "session",
            "reps", "sets", "weight", "strength", "muscle"
        }
        
        # Progress-related keywords
        progress_keywords = {
            "progress", "results", "weight", "measurement", "dexa", "body fat",
            "muscle", "strength", "improvement", "change"
        }
        
        # Milestone-related keywords
        milestone_keywords = {
            "milestone", "achievement", "goal", "target", "celebrate", "hit",
            "reached", "accomplished"
        }
        
        intent = {"type": "general", "confidence": 0.0, "keywords": []}
        
        # Check for nutrition intent
        nutrition_matches = [kw for kw in nutrition_keywords if kw in message_lower]
        if nutrition_matches:
            intent["type"] = "nutrition"
            intent["keywords"] = nutrition_matches
            intent["confidence"] = len(nutrition_matches) / len(nutrition_keywords)
        
        # Check for workout intent
        workout_matches = [kw for kw in workout_keywords if kw in message_lower]
        if workout_matches and len(workout_matches) > len(nutrition_matches):
            intent["type"] = "workout"
            intent["keywords"] = workout_matches
            intent["confidence"] = len(workout_matches) / len(workout_keywords)
        
        # Check for progress intent
        progress_matches = [kw for kw in progress_keywords if kw in message_lower]
        if progress_matches and len(progress_matches) > max(len(nutrition_matches), len(workout_matches)):
            intent["type"] = "progress"
            intent["keywords"] = progress_matches
            intent["confidence"] = len(progress_matches) / len(progress_keywords)
        
        # Check for milestone intent
        milestone_matches = [kw for kw in milestone_keywords if kw in message_lower]
        if milestone_matches and len(milestone_matches) > max(len(nutrition_matches), len(workout_matches), len(progress_matches)):
            intent["type"] = "milestone"
            intent["keywords"] = milestone_matches
            intent["confidence"] = len(milestone_matches) / len(milestone_keywords)
        
        return intent
    
    async def _handle_nutrition_query(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle nutrition-related queries with mock context"""
        macros = self.mock_data["user_patterns"]["optimal_breakfast_macros"]
        
        if "breakfast" in message:
            response = (
                f"Looking at your recent patterns, you've had the best energy levels "
                f"and workout performance when you have that protein-forward breakfast "
                f"with moderate carbs. Based on your data, aim for {macros['protein']}g protein, "
                f"{macros['carbs']}g carbs, and {macros['fat']}g fat."
            )
            
            if "presentation" in message or "meeting" in message:
                response += (
                    " Since you mentioned having an important presentation today, "
                    "I'd suggest your usual egg white omelet with sweet potato hash. "
                    "This combo has consistently given you stable energy without the 10am crash."
                )
            
            return response
        
        return "I'd love to help with your nutrition! What specific aspect are you looking to optimize?"
    
    async def _handle_workout_query(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle workout-related queries with mock context"""
        patterns = self.mock_data["user_patterns"]
        recovery = self.mock_data["recent_data"]["cns_recovery"]
        
        response = (
            f"Based on your 3-month data, your sweet spot has been {patterns['weekly_training_volume']} "
            f"training sessions per week using the {patterns['training_split']} split. "
            f"This has given you the best strength gains while maintaining recovery."
        )
        
        if recovery == "poor":
            response += " Your CNS recovery indicators suggest taking a lighter day today."
        elif recovery == "good":
            response += " Your recovery looks excellent and you're ready to push hard today!"
        
        return response
    
    async def _handle_progress_query(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle progress-related queries with mock data"""
        progress = self.mock_data["progress"]
        
        response = (
            f"Amazing progress! You've lost {progress['fat_loss_lbs']}lbs of fat "
            f"while gaining {progress['muscle_gain_lbs']}lbs of lean mass since we started tracking."
        )
        
        # Add strength improvements
        improvements = []
        for lift, data in progress["strength_improvements"].items():
            improvements.append(
                f"{lift.replace('_', ' ').title()}: +{data['improvement_percent']}% "
                f"({data['current']}lbs vs {data['starting']}lbs)"
            )
        
        if improvements:
            response += f" Your strength gains have been incredible: {', '.join(improvements)}"
        
        return response
    
    async def _handle_milestone_query(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle milestone-related queries with celebration"""
        milestones = self.mock_data["milestones"]
        
        if milestones:
            latest = milestones[-1]
            return (
                f"Congratulations on hitting {latest['milestone']}! "
                f"This is a huge achievement - {latest['description']} "
                f"It took you {latest['days_to_achieve']} days of consistent effort to get here."
            )
        
        return "Every day you're making progress! What milestone are you working toward?"
    
    async def _handle_general_query(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle general queries with personalized context"""
        return (
            "I've been tracking your optimization journey for 90 days now, "
            "and I'm seeing some fascinating patterns emerge. "
            "One thing that's become really clear is that morning workouts correlate "
            "with 25% higher energy levels - this has been consistent across your last 30 data points. "
            "What would you like to explore together?"
        )
    
    def get_interaction_history(self) -> List[Dict[str, Any]]:
        """Get interaction history for testing"""
        return self.interactions
    
    def get_mock_summary(self) -> Dict[str, Any]:
        """Get mock summary for testing"""
        return {
            "user_id": self.user_id,
            "total_days_tracked": 90,
            "patterns_discovered": self.mock_data["user_patterns"],
            "milestones_achieved": self.mock_data["milestones"],
            "progress_summary": self.mock_data["progress"]
        }


# Convenience function for testing
async def create_simple_auren(user_id: str) -> SimpleAUREN:
    """
    Create and initialize SimpleAUREN for testing
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        Initialized SimpleAUREN instance ready for interaction
    """
    return SimpleAUREN(user_id=user_id)


# Example usage
if __name__ == "__main__":
    async def demo():
        """Demonstrate SimpleAUREN functionality"""
        print("🧠 AUREN Cognitive Twin Demo")
        print("=" * 50)
        
        auren = await create_simple_auren("demo_user")
        
        test_messages = [
            "Good morning",
            "What should I eat for breakfast?",
            "What should I eat before my presentation?",
            "How's my progress?",
            "Should I workout today?",
            "I hit a new milestone!",
            "Tell me about my journey"
        ]
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = await auren.process_message(message)
            print(f"🤖 AUREN: {response}")
            print("-" * 50)
        
        print("\n✅ Demo complete!")
    
    asyncio.run(demo())
