#!/usr/bin/env python3
"""
Demo Neuroscientist Agent - Tells a Compelling Health Optimization Story
This simulates a real user journey from stress to recovery using AI guidance
"""

import asyncio
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import uuid
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AUREN components
from auren.realtime.langgraph_instrumentation import (
    CrewAIEventInstrumentation,
    AURENStreamEvent,
    AURENEventType,
    AURENPerformanceMetrics
)
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer


class HealthJourney:
    """Represents a user's health optimization journey"""
    
    def __init__(self):
        # Starting health state - stressed professional
        self.initial_state = {
            "hrv": 35,  # Low HRV
            "sleep_efficiency": 0.72,  # Poor sleep
            "stress_score": 7.5,  # High stress
            "recovery_score": 45,  # Poor recovery
            "energy_level": 4,  # Low energy (1-10)
            "mood": "anxious"
        }
        
        # Target improved state
        self.target_state = {
            "hrv": 55,  # Improved HRV
            "sleep_efficiency": 0.86,  # Better sleep
            "stress_score": 4.2,  # Manageable stress
            "recovery_score": 75,  # Good recovery
            "energy_level": 7,  # Higher energy
            "mood": "focused"
        }
        
        # Current state (will evolve)
        self.current_state = self.initial_state.copy()
        
        # Journey milestones
        self.milestones = []


class DemoNeuroscientist:
    """
    Simulates the neuroscientist agent with a realistic health optimization story
    Shows how AUREN helps users transform their health through data-driven insights
    """
    
    def __init__(self, user_id: str = "demo_user_001"):
        self.user_id = user_id
        self.session_id = f"demo_session_{int(datetime.now().timestamp())}"
        self.journey = HealthJourney()
        
        # Track agent's learning
        self.memories_formed = 0
        self.hypotheses_formed = []
        self.validated_hypotheses = []
        self.total_cost = 0.0
        self.interactions = 0
        
        # Agent personality
        self.agent_style = "confident_coach"  # Not cautious doctor
        
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize event streaming infrastructure"""
        logger.info(f"Initializing Demo Neuroscientist for user: {self.user_id}")
        
        self.redis_streamer = RedisStreamEventStreamer(redis_url)
        await self.redis_streamer.initialize()
        
        self.event_instrumentation = CrewAIEventInstrumentation(
            event_streamer=self.redis_streamer
        )
        
        # Emit initialization event
        await self._emit_system_event(
            "agent_initialized",
            {"agent_type": "neuroscientist", "mode": "demo"}
        )
        
        logger.info("Demo Neuroscientist ready to guide health optimization journey")
    
    async def simulate_user_journey(self, duration_minutes: int = 5):
        """
        Simulate a complete user health optimization journey
        This tells the story of transformation through AI-guided insights
        """
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Starting {duration_minutes}-minute health optimization journey")
        logger.info(f"📊 Initial state: HRV={self.journey.current_state['hrv']}ms, Stress={self.journey.current_state['stress_score']}/10")
        logger.info(f"{'='*60}\n")
        
        # Calculate time per phase
        phases = [
            ("Discovery", self._phase_1_discovery),
            ("Analysis", self._phase_2_deep_analysis),
            ("Hypothesis", self._phase_3_hypothesis_formation),
            ("Intervention", self._phase_4_personalized_intervention),
            ("Progress", self._phase_5_tracking_progress),
            ("Optimization", self._phase_6_continuous_optimization)
        ]
        
        phase_duration = (duration_minutes * 60) / len(phases)  # seconds per phase
        
        # Execute each phase
        for i, (phase_name, phase_func) in enumerate(phases):
            logger.info(f"\n📍 Phase {i+1}/{len(phases)}: {phase_name}")
            
            await phase_func()
            
            # Don't sleep after the last phase
            if i < len(phases) - 1:
                await asyncio.sleep(phase_duration)
        
        # Final summary
        await self._generate_journey_summary()
    
    async def _phase_1_discovery(self):
        """Phase 1: User discovers they need help"""
        
        # User's first question - they're struggling
        user_message = "I've been feeling exhausted lately despite sleeping 7-8 hours. My smartwatch shows my HRV has been really low. What's going on with my body?"
        
        await self._emit_conversation_event("user_to_system", user_message)
        
        # Agent starts analyzing
        trace_id = str(uuid.uuid4())
        await self._emit_agent_event(
            AURENEventType.AGENT_EXECUTION_STARTED,
            trace_id=trace_id,
            payload={
                "query": user_message,
                "analysis_type": "comprehensive_health_assessment",
                "urgency": "moderate"
            }
        )
        
        # Emit biometric analysis
        await self._emit_biometric_analysis(self.journey.current_state)
        
        # Tool usage for pattern analysis
        await self._emit_tool_usage(
            "BiometricPatternAnalyzer",
            tokens=200,
            cost=0.006,
            execution_time_ms=450
        )
        
        # Agent's insightful response
        response = """I see exactly what's happening here. Your body is telling a clear story through your biometrics:

**Your Current State:**
- HRV at 35ms is significantly suppressed (optimal range: 50-70ms)
- Despite 7-8 hours in bed, your sleep efficiency is only 72%
- This pattern indicates your nervous system is stuck in sympathetic overdrive

**What This Means:**
You're experiencing what I call "tired but wired" syndrome. Your body is producing stress hormones even during rest, preventing deep recovery. It's like trying to charge your phone while running intensive apps - the battery never fully recovers.

**The Hidden Cost:**
Each night of poor recovery compounds. Your decision-making, emotional regulation, and physical performance all suffer. This isn't just fatigue - it's systemic under-recovery.

Let's dig deeper into your patterns to find the root cause. When do you typically feel most stressed during your day?"""
        
        await self._emit_agent_event(
            AURENEventType.AGENT_EXECUTION_COMPLETED,
            trace_id=trace_id,
            payload={"execution_result": "success", "insight_quality": "high"},
            performance_metrics=self._generate_performance_metrics(2100, 0.0063)
        )
        
        # Form first memory
        await self._form_memory(
            "User presenting with classic sympathetic dominance pattern - low HRV + poor sleep efficiency despite adequate time in bed"
        )
        
        self.interactions += 1
    
    async def _phase_2_deep_analysis(self):
        """Phase 2: Deep pattern analysis"""
        
        # Simulate agent discovering patterns
        patterns_discovered = [
            {"pattern": "HRV drops 40% on weekday evenings vs weekends", "confidence": 0.89},
            {"pattern": "Sleep latency increases 3x on Sunday nights", "confidence": 0.92},
            {"pattern": "Recovery scores inversely correlate with meeting density", "confidence": 0.85}
        ]
        
        for pattern in patterns_discovered:
            await self._emit_knowledge_access(
                "pattern_recognition",
                pattern["pattern"],
                confidence=pattern["confidence"]
            )
            await asyncio.sleep(0.2)
        
        # Store patterns as memories
        await self._form_memory(
            "Work stress pattern identified: Weekday evening HRV suppression suggests work-related sympathetic activation"
        )
        
        # Agent shares insights
        user_followup = "You're right, I do feel most stressed after work. Especially on days with back-to-back meetings."
        
        await self._emit_conversation_event("user_to_system", user_followup)
        
        trace_id = str(uuid.uuid4())
        await self._emit_agent_event(AURENEventType.AGENT_EXECUTION_STARTED, trace_id=trace_id)
        
        response = """Perfect - now we're getting somewhere. Your biometric data confirms exactly what you're experiencing:

**The Meeting Recovery Debt:**
Your HRV shows you need 2-3 hours to recover from intense meetings, but you're stacking them back-to-back. It's like doing sprints without rest between sets.

**The Sunday Scaries Pattern:**
Your sleep latency triples on Sunday nights - classic anticipatory stress. Your nervous system is already preparing for Monday's chaos.

**The Accumulation Effect:**
By Friday, your HRV is 40% lower than Monday morning. You're accumulating stress debt throughout the week without adequate recovery windows.

This isn't a willpower issue - it's a biological capacity issue. Your nervous system needs strategic recovery periods, just like muscles need rest between workouts."""
        
        await self._emit_agent_event(
            AURENEventType.AGENT_EXECUTION_COMPLETED,
            trace_id=trace_id,
            performance_metrics=self._generate_performance_metrics(1800, 0.0054)
        )
        
        self.interactions += 1
    
    async def _phase_3_hypothesis_formation(self):
        """Phase 3: Form testable hypotheses"""
        
        hypotheses = [
            {
                "description": "Strategic 5-minute recovery breaks between meetings will improve daily HRV by 15%",
                "confidence": 0.82,
                "mechanism": "Parasympathetic activation through breathing"
            },
            {
                "description": "Sunday evening 'shutdown ritual' will reduce sleep latency by 50%",
                "confidence": 0.78,
                "mechanism": "Cognitive load reduction before sleep"
            },
            {
                "description": "Morning HRV-guided breathing will improve stress resilience throughout the day",
                "confidence": 0.85,
                "mechanism": "Autonomic nervous system priming"
            }
        ]
        
        for hyp in hypotheses:
            hypothesis_id = await self._form_hypothesis(
                hyp["description"],
                confidence=hyp["confidence"]
            )
            
            # Emit hypothesis event with mechanism
            await self._emit_learning_event(
                "hypothesis_mechanism",
                {
                    "hypothesis_id": hypothesis_id,
                    "mechanism": hyp["mechanism"],
                    "testable": True,
                    "duration_days": 7
                }
            )
            
            await asyncio.sleep(0.3)
        
        logger.info(f"💡 Formed {len(hypotheses)} testable hypotheses for optimization")
    
    async def _phase_4_personalized_intervention(self):
        """Phase 4: Deliver personalized intervention plan"""
        
        user_request = "Okay, I'm ready to make changes. What specifically should I do?"
        await self._emit_conversation_event("user_to_system", user_request)
        
        trace_id = str(uuid.uuid4())
        await self._emit_agent_event(AURENEventType.AGENT_EXECUTION_STARTED, trace_id=trace_id)
        
        # Use multiple tools to create comprehensive plan
        tools = [
            ("InterventionDesigner", 250, 0.0075),
            ("RecoveryProtocolBuilder", 200, 0.006),
            ("BehaviorChangeOptimizer", 180, 0.0054)
        ]
        
        for tool_name, tokens, cost in tools:
            await self._emit_tool_usage(tool_name, tokens, cost, random.randint(300, 600))
            await asyncio.sleep(0.2)
        
        response = """Here's your personalized nervous system optimization protocol, designed specifically for your patterns:

**MORNING FOUNDATION (6:30 AM - 5 minutes)**
- Check HRV immediately upon waking
- If HRV < 40: Do 10 rounds of 4-7-8 breathing
- If HRV > 40: Do 5 rounds + 30 second cold shower finish
- Purpose: Prime your nervous system for resilience

**MEETING RECOVERY PROTOCOL**
Between each meeting (minimum 5 minutes):
1. Stand and do 5 shoulder rolls
2. 3 rounds of box breathing (4-4-4-4)
3. Look at something 20+ feet away for 20 seconds
4. Quick win celebration (literally smile about something)
Purpose: Reset sympathetic activation before it accumulates

**SUNDAY SHUTDOWN RITUAL (7 PM)**
1. Write Monday's top 3 priorities (removes uncertainty)
2. Pack gym bag / prep clothes (reduces morning decisions)
3. 10-minute walk without phone (transitions nervous system)
4. Gratitude practice: 3 specific wins from the week
Purpose: Signal to your nervous system that work is complete

**EVENING RECOVERY (8:30 PM)**
- Dim lights to 20% (triggers melatonin)
- Magnesium glycinate 200mg (supports GABA)
- 10-minute yoga nidra (free on Insight Timer)
- Phone on airplane mode by 9 PM
Purpose: Create optimal conditions for deep sleep

**TRACKING SUCCESS:**
- Morning HRV (target: increase 2-3ms per week)
- Time to fall asleep (target: <15 minutes)
- Subjective energy (1-10 daily rating)

Start with just the morning protocol tomorrow. Add one new element every 3 days. In 2 weeks, this will feel automatic."""
        
        await self._emit_agent_event(
            AURENEventType.AGENT_EXECUTION_COMPLETED,
            trace_id=trace_id,
            payload={"protocol_complexity": "graduated", "personalization_level": "high"},
            performance_metrics=self._generate_performance_metrics(3200, 0.0189)
        )
        
        # Store intervention as memory
        await self._form_memory(
            "Comprehensive intervention protocol delivered - focusing on meeting recovery and Sunday shutdown ritual"
        )
        
        self.interactions += 1
    
    async def _phase_5_tracking_progress(self):
        """Phase 5: Show measurable progress"""
        
        # Simulate gradual improvement over "7 days"
        improvements = [
            ("Day 1", {"hrv": 37, "energy": 4, "notes": "Morning breathing felt calming"}),
            ("Day 3", {"hrv": 41, "energy": 5, "notes": "Fell asleep faster last night"}),
            ("Day 5", {"hrv": 45, "energy": 6, "notes": "Had energy for evening workout"}),
            ("Day 7", {"hrv": 49, "energy": 7, "notes": "Best week of sleep in months"})
        ]
        
        for day, data in improvements:
            # Update current state
            self.journey.current_state["hrv"] = data["hrv"]
            self.journey.current_state["energy_level"] = data["energy"]
            
            # Emit progress event
            await self._emit_learning_event(
                "progress_milestone",
                {
                    "day": day,
                    "hrv_improvement": data["hrv"] - 35,
                    "energy_improvement": data["energy"] - 4,
                    "user_notes": data["notes"],
                    "trend": "improving"
                }
            )
            
            await asyncio.sleep(0.5)
        
        # Validate hypothesis
        await self._validate_hypothesis(
            self.hypotheses_formed[0],  # First hypothesis about recovery breaks
            outcome="confirmed",
            evidence={"hrv_increase": 14, "target": 15, "success": True}
        )
        
        # User shares success
        user_success = "I can't believe the difference! My energy is so much better and I'm actually sleeping through the night."
        await self._emit_conversation_event("user_to_system", user_success)
        
        trace_id = str(uuid.uuid4())
        await self._emit_agent_event(AURENEventType.AGENT_EXECUTION_STARTED, trace_id=trace_id)
        
        response = """This is fantastic progress! Let's look at what your data reveals:

**Your 7-Day Transformation:**
- HRV improved 40% (35ms → 49ms) 
- Energy levels up 75% (4/10 → 7/10)
- Sleep efficiency improved to 83%
- Recovery scores now averaging 68

**What Worked Best:**
Your data shows the meeting recovery protocol had the highest impact. Those 5-minute breaks prevented the usual stress accumulation. The Sunday ritual eliminated your anticipatory stress completely.

**Hypothesis Validated:**
We confirmed that strategic recovery breaks improve HRV by 15%+. Your nervous system responded exactly as predicted.

**Next Level Optimization:**
Now that your foundation is solid, we can explore:
- HRV biofeedback training
- Temperature manipulation for recovery
- Nutrient timing for cognitive performance

You've proven you can change your physiology through behavior. That's powerful."""
        
        await self._emit_agent_event(
            AURENEventType.AGENT_EXECUTION_COMPLETED,
            trace_id=trace_id,
            performance_metrics=self._generate_performance_metrics(2400, 0.0072)
        )
        
        self.journey.milestones.append({
            "date": datetime.now(timezone.utc),
            "achievement": "First week success - 40% HRV improvement",
            "next_goal": "Sustain improvements for 30 days"
        })
        
        self.interactions += 1
    
    async def _phase_6_continuous_optimization(self):
        """Phase 6: Show continuous learning and optimization"""
        
        # Agent learns from user's specific patterns
        learning_insights = [
            "User responds exceptionally well to morning cold exposure",
            "Wednesday afternoon is optimal time for challenging cognitive work",
            "Pre-meeting breathing most effective with 4-7-8 pattern vs box breathing"
        ]
        
        for insight in learning_insights:
            await self._emit_learning_event(
                "pattern_refinement",
                {"insight": insight, "confidence": 0.88}
            )
            await self._form_memory(insight)
            await asyncio.sleep(0.3)
        
        # Final optimization discussion
        user_question = "What should I focus on next to keep improving?"
        await self._emit_conversation_event("user_to_system", user_question)
        
        trace_id = str(uuid.uuid4())
        await self._emit_agent_event(AURENEventType.AGENT_EXECUTION_STARTED, trace_id=trace_id)
        
        response = """Based on your unique response patterns, here's your next evolution:

**You're Ready for Advanced Protocols:**
Your nervous system now has the resilience for more sophisticated interventions. You've built the foundation - now we optimize.

**Your Personal Success Formula:**
- Morning cold exposure gives you +5ms HRV boost (unusual responder)
- Your cognitive peak is Wednesday 2-4 PM (plan deep work here)
- 4-7-8 breathing works 30% better than box breathing for you

**30-Day Goal:**
Stabilize HRV above 55ms. This is your nervous system's "thriving" zone where stress becomes fuel rather than drain.

**New Experiments to Try:**
1. Wim Hof breathing 2x/week (builds stress resilience)
2. 24-hour HRV tracking to find hidden patterns
3. Circadian light optimization (biggest untapped gain)

Remember: You've increased your HRV by 40% in one week. That's remarkable. Your body is far more adaptable than you realized.

Keep going - we're just getting started."""
        
        await self._emit_agent_event(
            AURENEventType.AGENT_EXECUTION_COMPLETED,
            trace_id=trace_id,
            performance_metrics=self._generate_performance_metrics(2600, 0.0078)
        )
        
        # Update final state
        self.journey.current_state = {
            "hrv": 52,
            "sleep_efficiency": 0.86,
            "stress_score": 4.5,
            "recovery_score": 72,
            "energy_level": 7,
            "mood": "optimistic"
        }
        
        self.interactions += 1
    
    async def _generate_journey_summary(self):
        """Generate final summary of the health optimization journey"""
        
        improvement_summary = {
            "hrv_improvement": f"{((self.journey.current_state['hrv'] - self.journey.initial_state['hrv']) / self.journey.initial_state['hrv'] * 100):.0f}%",
            "sleep_improvement": f"{((self.journey.current_state['sleep_efficiency'] - self.journey.initial_state['sleep_efficiency']) / self.journey.initial_state['sleep_efficiency'] * 100):.0f}%",
            "energy_improvement": f"{self.journey.current_state['energy_level'] - self.journey.initial_state['energy_level']} points",
            "total_interactions": self.interactions,
            "memories_formed": self.memories_formed,
            "hypotheses_validated": len(self.validated_hypotheses),
            "total_cost": f"${self.total_cost:.4f}"
        }
        
        # Emit journey completion event
        await self._emit_system_event(
            "journey_completed",
            improvement_summary
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 HEALTH OPTIMIZATION JOURNEY COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"📈 Results:")
        logger.info(f"   - HRV Improvement: {improvement_summary['hrv_improvement']}")
        logger.info(f"   - Sleep Quality: {improvement_summary['sleep_improvement']}")
        logger.info(f"   - Energy Boost: {improvement_summary['energy_improvement']}")
        logger.info(f"🧠 AI Learning:")
        logger.info(f"   - Memories Formed: {self.memories_formed}")
        logger.info(f"   - Hypotheses Validated: {len(self.validated_hypotheses)}")
        logger.info(f"   - Total Interactions: {self.interactions}")
        logger.info(f"💰 Cost: {improvement_summary['total_cost']}")
        logger.info(f"{'='*60}\n")
    
    # Helper methods for event emission
    async def _emit_agent_event(self, event_type: AURENEventType, **kwargs):
        """Emit agent-related events"""
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=kwargs.get("trace_id"),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload=kwargs.get("payload", {}),
            metadata=kwargs.get("metadata", {}),
            performance_metrics=kwargs.get("performance_metrics"),
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
    
    async def _emit_conversation_event(self, direction: str, message: str):
        """Emit conversation events"""
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.CONVERSATION_EVENT,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"} if direction == "system_to_user" else None,
            target_agent={"id": "neuroscientist", "role": "neuroscientist"} if direction == "user_to_system" else None,
            payload={
                "direction": direction,
                "message": message[:500],
                "message_length": len(message)
            },
            metadata={},
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
        
        # Log conversation
        icon = "👤" if direction == "user_to_system" else "🧠"
        logger.info(f"{icon} {message[:100]}...")
    
    async def _emit_biometric_analysis(self, health_state: Dict[str, Any]):
        """Emit biometric analysis event"""
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.BIOMETRIC_ANALYSIS,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "metrics_available": list(health_state.keys()),
                "current_values": health_state,
                "analysis_depth": "comprehensive"
            },
            metadata={},
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
    
    async def _emit_tool_usage(self, tool_name: str, tokens: int, cost: float, execution_time_ms: int):
        """Emit tool usage event"""
        self.total_cost += cost
        
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.TOOL_USAGE,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "tool_name": tool_name,
                "tokens_used": tokens,
                "estimated_cost": cost,
                "execution_time_ms": execution_time_ms
            },
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
        
        logger.info(f"🔧 Tool: {tool_name} ({tokens} tokens, ${cost:.4f})")
    
    async def _emit_knowledge_access(self, operation: str, details: str, confidence: float = 0.8):
        """Emit knowledge access event"""
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.KNOWLEDGE_ACCESS,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "operation": operation,
                "details": details,
                "confidence": confidence,
                "knowledge_domain": "neuroscience"
            },
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
    
    async def _emit_learning_event(self, learning_type: str, details: Dict[str, Any]):
        """Emit learning system event"""
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.LEARNING_EVENT,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "learning_type": learning_type,
                **details
            },
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
    
    async def _emit_system_event(self, event_name: str, details: Dict[str, Any]):
        """Emit system-level events"""
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.SYSTEM_HEALTH,
            source_agent=None,
            target_agent=None,
            payload={
                "event": event_name,
                **details
            },
            metadata={},
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
    
    async def _form_memory(self, content: str):
        """Form a new memory"""
        self.memories_formed += 1
        
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.MEMORY_OPERATION,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "operation": "store",
                "memory_type": "observation",
                "content": content,
                "confidence": 0.85
            },
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
        
        logger.info(f"💾 Memory formed: {content[:60]}...")
    
    async def _form_hypothesis(self, description: str, confidence: float = 0.8) -> str:
        """Form a new hypothesis"""
        hypothesis_id = f"hyp_{uuid.uuid4().hex[:8]}"
        
        self.hypotheses_formed.append({
            "id": hypothesis_id,
            "description": description,
            "confidence": confidence,
            "formed_at": datetime.now(timezone.utc)
        })
        
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.HYPOTHESIS_EVENT,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "hypothesis_id": hypothesis_id,
                "status": "formed",
                "description": description,
                "confidence": confidence
            },
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
        
        logger.info(f"💡 Hypothesis: {description[:60]}...")
        return hypothesis_id
    
    async def _validate_hypothesis(self, hypothesis_id: str, outcome: str, evidence: Dict[str, Any]):
        """Validate a hypothesis"""
        hyp = next((h for h in self.hypotheses_formed if h["id"] == hypothesis_id), None)
        if not hyp:
            return
        
        self.validated_hypotheses.append(hyp)
        
        event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.HYPOTHESIS_EVENT,
            source_agent={"id": "neuroscientist", "role": "neuroscientist"},
            target_agent=None,
            payload={
                "hypothesis_id": hypothesis_id,
                "status": "validated",
                "outcome": outcome,
                "evidence": evidence
            },
            user_id=self.user_id
        )
        # Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)
        
        logger.info(f"✅ Hypothesis validated: {outcome}")
    
    def _generate_performance_metrics(self, latency_ms: float, token_cost: float) -> AURENPerformanceMetrics:
        """Generate realistic performance metrics"""
        return AURENPerformanceMetrics(
            latency_ms=latency_ms,
            token_cost=token_cost,
            memory_usage_mb=45.2 + random.uniform(-5, 5),
            cpu_percentage=12.5 + random.uniform(-3, 3),
            success=True,
            agent_id="neuroscientist",
            confidence_score=0.85 + random.uniform(-0.1, 0.1)
        )


async def main():
    """Run the demo neuroscientist simulation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AUREN Demo Neuroscientist - Simulates health optimization journey"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Duration in minutes (default: 5)"
    )
    parser.add_argument(
        "--user-id",
        default="demo_user_001",
        help="User ID for events (default: demo_user_001)"
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis URL (default: redis://localhost:6379)"
    )
    
    args = parser.parse_args()
    
    # Header
    print("\n" + "="*60)
    print("🧠 AUREN DEMO NEUROSCIENTIST")
    print("="*60)
    print(f"Duration: {args.duration} minutes")
    print(f"User ID: {args.user_id}")
    print(f"Redis: {args.redis_url}")
    print("="*60 + "\n")
    
    # Create and run demo
    demo = DemoNeuroscientist(user_id=args.user_id)
    
    try:
        await demo.initialize(redis_url=args.redis_url)
        await demo.simulate_user_journey(duration_minutes=args.duration)
        
    except KeyboardInterrupt:
        logger.info("\n\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 