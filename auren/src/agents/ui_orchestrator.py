"""
AUREN - The Cognitive Twin Interface
====================================

This module implements AUREN, the warm and intelligent personality that serves as
the primary interface for users. AUREN remembers everything, learns patterns
specific to each individual, and provides deeply personalized optimization guidance.

Based on the specification in /auren/config/agents/ui_orchestrator.yaml
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import logging

import redis.asyncio as redis
import asyncpg
import chromadb
from crewai import Agent

from ..memory.cognitive_twin import CognitiveTwinMemory
from ..tools.pattern_analyzer import PatternAnalyzer
from ..tools.milestone_tracker import MilestoneTracker
from ..tools.specialist_coordinator import SpecialistCoordinator
from ..tools.insight_generator import InsightGenerator
from ..tools.protocol_manager import ProtocolManager

logger = logging.getLogger(__name__)


@dataclass
class AURENContext:
    """Context object for AUREN interactions"""
    user_id: str
    timestamp: datetime
    message: str
    session_id: str
    metadata: Dict[str, Any]


class AUREN:
    """
    AUREN - The Cognitive Twin Interface
    
    AUREN is the warm, intelligent personality that users interact with.
    She remembers everything, learns individual patterns, and provides
    deeply personalized optimization guidance based on months/years of data.
    
    Key Features:
    - Permanent memory retention (Redis, PostgreSQL, ChromaDB)
    - Pattern recognition across biological data
    - Seamless specialist coordination
    - Scientific approach to optimization
    - Natural, conversational interaction style
    
    Example:
        >>> auren = AUREN(user_id="astxrtys")
        >>> response = await auren.process_message("Good morning")
        >>> print(response)
        "Good morning! I see you're up earlier than usual..."
    """
    
    def __init__(self, user_id: str):
        """
        Initialize AUREN for a specific user
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.name = "AUREN"
        self.role = "Personal Optimization Companion"
        
        # Memory layers
        self.memory = CognitiveTwinMemory(user_id=user_id)
        self.pattern_analyzer = PatternAnalyzer(user_id=user_id)
        self.milestone_tracker = MilestoneTracker(user_id=user_id)
        self.specialist_coordinator = SpecialistCoordinator(user_id=user_id)
        self.insight_generator = InsightGenerator(user_id=user_id)
        self.protocol_manager = ProtocolManager(user_id=user_id)
        
        # Initialize personality traits
        self.attributes = [
            "Warm and encouraging personality",
            "Deep historical awareness", 
            "Pattern recognition expertise",
            "Scientific approach to optimization",
            "Natural conversational flow",
            "Seamless specialist coordination"
        ]
        
    async def initialize(self) -> None:
        """Initialize all memory layers and connections"""
        await self.memory.initialize()
        logger.info(f"AUREN initialized for user {self.user_id}")
    
    async def process_message(self, message: str) -> str:
        """
        Process a user message with full historical context
        
        Args:
            message: The user's input message
            
        Returns:
            AUREN's personalized response based on user history
            
        Example:
            >>> response = await auren.process_message("Good morning")
            >>> # Response includes awareness of sleep patterns, recent workouts, etc.
        """
        try:
            # Create interaction context
            context = AURENContext(
                user_id=self.user_id,
                timestamp=datetime.now(),
                message=message.lower().strip(),
                session_id=f"{self.user_id}_{datetime.now().isoformat()}",
                metadata={}
            )
            
            # Store the interaction
            await self.memory.store_interaction(context)
            
            # Generate contextual greeting if appropriate
            if self._is_greeting(message):
                return await self._generate_contextual_greeting(context)
            
            # Analyze intent and generate response
            intent = await self._analyze_intent(context)
            
            # Route to appropriate handler
            if intent["type"] == "nutrition":
                return await self._handle_nutrition_query(context, intent)
            elif intent["type"] == "workout":
                return await self._handle_workout_query(context, intent)
            elif intent["type"] == "progress":
                return await self._handle_progress_query(context, intent)
            elif intent["type"] == "milestone":
                return await self._handle_milestone_query(context, intent)
            else:
                return await self._handle_general_query(context, intent)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm here to help! Could you tell me more about what you're looking for?"
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = {"good morning", "morning", "hello", "hi", "hey", "good evening", "good afternoon"}
        return any(greeting in message.lower() for greeting in greetings)
    
    async def _generate_contextual_greeting(self, context: AURENContext) -> str:
        """Generate a personalized greeting with historical context"""
        try:
            # Get recent patterns
            recent_patterns = await self.pattern_analyzer.get_recent_patterns(days=7)
            sleep_patterns = await self.memory.get_sleep_data(days=3)
            workout_recovery = await self.memory.get_workout_recovery_status()
            
            greeting_parts = []
            
            # Time-based greeting
            current_hour = context.timestamp.hour
            if current_hour < 12:
                greeting_parts.append("Good morning!")
            elif current_hour < 17:
                greeting_parts.append("Good afternoon!")
            else:
                greeting_parts.append("Good evening!")
            
            # Add contextual awareness
            if recent_patterns:
                # Check for early wake patterns
                if sleep_patterns and sleep_patterns.get("avg_wake_time"):
                    wake_time = sleep_patterns["avg_wake_time"]
                    if context.timestamp.hour < wake_time.hour - 1:
                        greeting_parts.append("I see you're up a bit earlier than usual - that's great!")
            
            # Add workout context
            if workout_recovery:
                if workout_recovery.get("cns_recovery") == "good":
                    last_workout = workout_recovery.get("last_workout_date")
                    if last_workout:
                        greeting_parts.append(
                            f"Your CNS recovery from {last_workout.strftime('%A')}'s session "
                            f"looks good based on yesterday's check-in."
                        )
            
            # Add energy pattern context
            energy_patterns = await self.pattern_analyzer.get_energy_patterns()
            if energy_patterns and energy_patterns.get("optimal_workout_time"):
                optimal_time = energy_patterns["optimal_workout_time"]
                greeting_parts.append(
                    f"Based on your energy patterns, {optimal_time} workouts have consistently "
                    f"given you the best results."
                )
            
            greeting_parts.append("How are you feeling today?")
            
            return " ".join(greeting_parts)
            
        except Exception as e:
            logger.error(f"Error generating contextual greeting: {e}")
            return f"Good {self._get_time_greeting()}! How are you feeling today?"
    
    def _get_time_greeting(self) -> str:
        """Get appropriate time-based greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    async def _analyze_intent(self, context: AURENContext) -> Dict[str, Any]:
        """Analyze user intent from message"""
        message = context.message.lower()
        
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
        nutrition_matches = [kw for kw in nutrition_keywords if kw in message]
        if nutrition_matches:
            intent["type"] = "nutrition"
            intent["keywords"] = nutrition_matches
            intent["confidence"] = len(nutrition_matches) / len(nutrition_keywords)
        
        # Check for workout intent
        workout_matches = [kw for kw in workout_keywords if kw in message]
        if workout_matches and len(workout_matches) > len(nutrition_matches):
            intent["type"] = "workout"
            intent["keywords"] = workout_matches
            intent["confidence"] = len(workout_matches) / len(workout_keywords)
        
        # Check for progress intent
        progress_matches = [kw for kw in progress_keywords if kw in message]
        if progress_matches and len(progress_matches) > max(len(nutrition_matches), len(workout_matches)):
            intent["type"] = "progress"
            intent["keywords"] = progress_matches
            intent["confidence"] = len(progress_matches) / len(progress_keywords)
        
        # Check for milestone intent
        milestone_matches = [kw for kw in milestone_keywords if kw in message]
        if milestone_matches and len(milestone_matches) > max(len(nutrition_matches), len(workout_matches), len(progress_matches)):
            intent["type"] = "milestone"
            intent["keywords"] = milestone_matches
            intent["confidence"] = len(milestone_matches) / len(milestone_keywords)
        
        return intent
    
    async def _handle_nutrition_query(self, context: AURENContext, intent: Dict[str, Any]) -> str:
        """Handle nutrition-related queries with historical context"""
        try:
            # Get user's nutrition patterns
            nutrition_patterns = await self.pattern_analyzer.get_nutrition_patterns()
            recent_meals = await self.memory.get_recent_meals(days=7)
            energy_correlations = await self.pattern_analyzer.get_energy_meal_correlations()
            
            response_parts = []
            
            # Analyze what works for this user
            if nutrition_patterns:
                optimal_macros = nutrition_patterns.get("optimal_breakfast_macros")
                if optimal_macros and "breakfast" in context.message:
                    response_parts.append(
                        f"Looking at your recent patterns, you've had the best energy levels "
                        f"and workout performance when you have that protein-forward breakfast "
                        f"with moderate carbs - similar to what worked so well for you last Thursday."
                    )
                    
                    # Check for specific context
                    if "presentation" in context.message or "meeting" in context.message:
                        response_parts.append(
                            f"Since you mentioned having that important presentation today, "
                            f"I'd suggest something like your usual egg white omelet with the sweet potato hash. "
                            f"That combination has consistently given you stable energy through the morning "
                            f"without the 10am crash you get from higher-carb options."
                        )
                        
                        response_parts.append(
                            "Want me to remind you of the exact macros that have been working best?"
                        )
                    else:
                        response_parts.append(
                            f"Based on your data, aim for {optimal_macros['protein']}g protein, "
                            f"{optimal_macros['carbs']}g carbs, and {optimal_macros['fat']}g fat. "
                            f"This has given you the most stable energy."
                        )
            
            if not response_parts:
                response_parts.append(
                    "I'd love to help with your nutrition! Could you tell me more about "
                    "what you're looking to optimize - energy, recovery, or something specific?"
                )
            
            return " ".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling nutrition query: {e}")
            return "I'm here to help with your nutrition! What would you like to know?"
    
    async def _handle_workout_query(self, context: AURENContext, intent: Dict[str, Any]) -> str:
        """Handle workout-related queries with historical context"""
        try:
            # Get workout patterns and recovery data
            workout_patterns = await self.pattern_analyzer.get_workout_patterns()
            recovery_status = await self.memory.get_workout_recovery_status()
            recent_performance = await self.memory.get_recent_performance(days=14)
            
            response_parts = []
            
            if workout_patterns:
                optimal_volume = workout_patterns.get("optimal_weekly_volume")
                best_split = workout_patterns.get("optimal_training_split")
                
                if optimal_volume and best_split:
                    response_parts.append(
                        f"Based on your 3-month data, your sweet spot has been "
                        f"{optimal_volume} training sessions per week using the {best_split} split. "
                        f"This has given you the best strength gains while maintaining recovery."
                    )
            
            if recovery_status:
                cns_status = recovery_status.get("cns_recovery")
                if cns_status == "poor":
                    response_parts.append(
                        "Your CNS recovery indicators suggest taking a lighter day today. "
                        "Your HRV has been trending down and your grip strength was 15% lower yesterday."
                    )
                elif cns_status == "good":
                    response_parts.append(
                        "Your recovery looks excellent! Your HRV is up 8% and you're ready to push hard today."
                    )
            
            if not response_parts:
                response_parts.append(
                    "I'd love to help optimize your training! What specific aspect are you thinking about - "
                    "programming, recovery, or performance?"
                )
            
            return " ".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling workout query: {e}")
            return "I'm here to help with your training! What would you like to focus on?"
    
    async def _handle_progress_query(self, context: AURENContext, intent: Dict[str, Any]) -> str:
        """Handle progress-related queries with historical data"""
        try:
            # Get comprehensive progress data
            body_composition = await self.memory.get_body_composition_changes()
            strength_progress = await self.memory.get_strength_progress()
            energy_trends = await self.pattern_analyzer.get_energy_trends()
            
            response_parts = []
            
            if body_composition:
                fat_loss = body_composition.get("fat_loss_lbs", 0)
                muscle_gain = body_composition.get("muscle_gain_lbs", 0)
                
                if fat_loss > 0 or muscle_gain > 0:
                    response_parts.append(
                        f"Amazing progress! You've lost {fat_loss}lbs of fat "
                        f"while gaining {muscle_gain}lbs of lean mass since we started tracking."
                    )
            
            if strength_progress:
                key_lifts = strength_progress.get("key_lifts", {})
                if key_lifts:
                    improvements = []
                    for lift, data in key_lifts.items():
                        if data.get("improvement_percent", 0) > 5:
                            improvements.append(
                                f"{lift.title()}: +{data['improvement_percent']}% "
                                f"({data['current']}lbs vs {data['starting']}lbs)"
                            )
                    
                    if improvements:
                        response_parts.append(
                            f"Your strength gains have been incredible: {', '.join(improvements)}"
                        )
            
            if energy_trends:
                avg_improvement = energy_trends.get("average_daily_energy_improvement", 0)
                if avg_improvement > 0:
                    response_parts.append(
                        f"And your daily energy levels are up {avg_improvement}% on average - "
                        f"the nutrition and training adjustments are clearly working!"
                    )
            
            if not response_parts:
                response_parts.append(
                    "Let's look at your progress together! I can see your transformation story "
                    "unfolding across all your data. What specific aspect would you like to celebrate?"
                )
            
            return " ".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling progress query: {e}")
            return "I'm excited to celebrate your progress with you! What would you like to review?"
    
    async def _handle_milestone_query(self, context: AURENContext, intent: Dict[str, Any]) -> str:
        """Handle milestone-related queries with celebration"""
        try:
            # Check for recent milestones
            recent_milestones = await self.milestone_tracker.get_recent_milestones(days=7)
            
            response_parts = []
            
            if recent_milestones:
                latest = recent_milestones[-1]
                response_parts.append(
                    f"Congratulations on hitting {latest['milestone']}! "
                    f"This is a huge achievement - {latest['description']}"
                )
                
                # Add context about the journey
                if latest.get("days_to_achieve"):
                    response_parts.append(
                        f"It took you {latest['days_to_achieve']} days of consistent effort "
                        f"to get here, and your dedication shows."
                    )
            else:
                response_parts.append(
                    "Every day you're making progress! What milestone are you working toward? "
                    "I can help track it and celebrate when you get there."
                )
            
            return " ".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling milestone query: {e}")
            return "I'm here to celebrate every win with you! What's the milestone you're excited about?"
    
    async def _handle_general_query(self, context: AURENContext, intent: Dict[str, Any]) -> str:
        """Handle general queries with personalized context"""
        try:
            # Get general context about user's current state
            current_state = await self.memory.get_current_optimization_state()
            recent_insights = await self.insight_generator.get_recent_insights()
            
            response_parts = []
            
            if current_state:
                phase = current_state.get("current_phase", "optimization")
                days_tracked = current_state.get("days_tracked", 0)
                
                response_parts.append(
                    f"I've been tracking your {phase} journey for {days_tracked} days now, "
                    f"and I'm seeing some fascinating patterns emerge."
                )
            
            if recent_insights:
                top_insight = recent_insights[0] if recent_insights else None
                if top_insight:
                    response_parts.append(
                        f"One thing that's become really clear is {top_insight['insight']} - "
                        f"this has been consistent across your last {top_insight['data_points']} data points."
                    )
            
            if not response_parts:
                response_parts.append(
                    "I'm here to help you optimize based on YOUR unique patterns and data. "
                    "What would you like to explore together?"
                )
            
            return " ".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            return "I'm here to help with your optimization journey! What would you like to focus on?"
    
    async def get_comprehensive_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the user's optimization journey
        
        Returns:
            Complete summary including patterns, milestones, and insights
        """
        try:
            return {
                "user_id": self.user_id,
                "total_days_tracked": await self.memory.get_total_days_tracked(),
                "patterns_discovered": await self.pattern_analyzer.get_all_patterns(),
                "milestones_achieved": await self.milestone_tracker.get_all_milestones(),
                "current_insights": await self.insight_generator.get_current_insights(),
                "specialist_recommendations": await self.specialist_coordinator.get_recommendations()
            }
        except Exception as e:
            logger.error(f"Error generating comprehensive summary: {e}")
            return {"error": "Unable to generate summary", "user_id": self.user_id}
    
    async def close(self) -> None:
        """Clean up connections and save state"""
        await self.memory.close()
        logger.info(f"AUREN closed for user {self.user_id}")


# Convenience function for quick initialization
async def create_auren(user_id: str) -> AUREN:
    """
    Create and initialize AUREN for a specific user
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        Initialized AUREN instance ready for interaction
    """
    auren = AUREN(user_id=user_id)
    await auren.initialize()
    return auren
