"""
NEUROS LangGraph Implementation - Full Cognitive State Machine
Implements the complete NEUROS personality with sophisticated state management
"""
import os
import json
import yaml
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, TypedDict, Annotated
from enum import Enum
import uuid
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
import redis.asyncio as redis
from pydantic import BaseModel, Field
import chromadb

# Configure logging
logging.basicConfig(level="INFO")
logger = logging.getLogger("neuros.langgraph")

# NEUROS Modes
class NEUROSMode(str, Enum):
    """NEUROS operational modes with cognitive states"""
    BASELINE = "BASELINE"
    HYPOTHESIS = "HYPOTHESIS"
    COMPANION = "COMPANION"
    SYNTHESIS = "SYNTHESIS"
    COACH = "COACH"
    PROVOCATEUR = "PROVOCATEUR"

# Memory Tiers
class MemoryTier(str, Enum):
    """Three-tier memory system"""
    L1_REALTIME = "L1_REALTIME"      # Immediate conversation context
    L2_WORKING = "L2_WORKING"        # Recent patterns and insights
    L3_LONGTERM = "L3_LONGTERM"      # Persistent user profile

# Protocol Stacks from YAML Phase 4
@dataclass
class NeuroStack:
    """Represents a neuroplastic protocol from YAML Phase 4"""
    id: str
    focus: str
    components: List[str]
    duration: int  # days
    metrics: List[str]

class NeuroplasticEngine:
    """Implements experimental protocol stacks from YAML Phase 4"""
    
    def __init__(self):
        # Load protocols from YAML phase_4_logic
        self.protocols = {
            "neurostack_alpha": NeuroStack(
                id="neurostack_alpha",
                focus="sleep_latency_reset",
                components=[
                    "morning_circadian_anchor",
                    "9pm_digital_fast", 
                    "progressive_muscle_relaxation"
                ],
                duration=7,
                metrics=["sleep_latency", "next_day_alertness", "HRV_delta"]
            ),
            "neurostack_beta": NeuroStack(
                id="neurostack_beta",
                focus="mid_day_cognitive_surge",
                components=[
                    "pre-lunch brisk walk",
                    "cold rinse + peppermint oil",
                    "5-min light-focused journaling"
                ],
                duration=5,
                metrics=["work_session_focus", "verbal_clarity", "mood_consistency"]
            ),
            "neurostack_gamma": NeuroStack(
                id="neurostack_gamma",
                focus="stress_recoding_loop",
                components=[
                    "4-7-8 breathing after triggers",
                    "guided reappraisal prompt",
                    "end-of-day vagal reset"
                ],
                duration=10,
                metrics=["cortisol_smoothing", "heart_rate_recovery", "emotional_variance"]
            )
        }
    
    async def select_protocol(self, state: NEUROSState) -> Optional[str]:
        """Select appropriate protocol based on user state"""
        
        # Check sleep issues
        biometrics = state.get("latest_biometrics", {})
        if biometrics.get("rem_variance", 0) > 30:
            return "neurostack_alpha"
        
        # Check cognitive fatigue
        if state.get("current_mode") == NEUROSMode.HYPOTHESIS.value:
            return "neurostack_beta"
        
        # Check stress patterns
        stress = state.get("stress_indicators", [])
        if stress and max(stress) > 0.6:
            return "neurostack_gamma"
        
        return None
    
    def format_protocol_message(self, protocol_id: str, day: int = 1) -> str:
        """Format protocol as conversational guidance"""
        protocol = self.protocols[protocol_id]
        
        intro = f"I've identified a {protocol.duration}-day protocol that might help with your {protocol.focus.replace('_', ' ')}."
        
        components = "\n".join([f"- {comp}" for comp in protocol.components])
        
        return f"{intro}\n\nToday's focus:\n{components}\n\nWant to try this together?"

# Three-Tier Memory System
class ThreeTierMemory:
    """Complete implementation of YAML Phase 3 memory architecture"""
    
    def __init__(self):
        # L1: Hot tier (Redis) - Already implemented
        self.redis_client = None  # Will be set later
        
        # L2: Warm tier (PostgreSQL) - Already implemented
        self.pg_checkpointer = None  # Will be set later
        
        # L3: Cold tier (ChromaDB) - NEW
        try:
            self.chroma_client = chromadb.HttpClient(host='auren-chromadb', port=8001)
            self.collection = self.chroma_client.get_or_create_collection(
                name="neuros_memories",
                metadata={"description": "Long-term semantic memory for NEUROS"}
            )
            logger.info("ChromaDB connected for L3 memory")
        except Exception as e:
            logger.warning(f"ChromaDB connection failed: {e}")
            self.chroma_client = None
            self.collection = None
    
    async def promote_to_cold_storage(self, memory_data: dict):
        """Move important memories to semantic storage after 30 days"""
        if not self.collection:
            return
            
        # Create embedding-friendly document
        document = f"""
        Context: {memory_data.get('context')}
        User State: {memory_data.get('user_state')}
        NEUROS Response: {memory_data.get('response')}
        Outcome: {memory_data.get('outcome')}
        Mode: {memory_data.get('mode')}
        """
        
        # Store with metadata for retrieval
        try:
            self.collection.add(
                documents=[document],
                metadatas=[{
                    "user_id": memory_data.get("user_id"),
                    "timestamp": memory_data.get("timestamp"),
                    "mode": memory_data.get("mode"),
                    "success_metric": memory_data.get("success_metric", 0)
                }],
                ids=[f"memory_{memory_data.get('user_id')}_{datetime.now().timestamp()}"]
            )
        except Exception as e:
            logger.error(f"Failed to store in ChromaDB: {e}")
    
    async def semantic_recall(self, query: str, user_id: str, n_results: int = 5):
        """Retrieve relevant memories from cold storage"""
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                where={"user_id": user_id},
                n_results=n_results
            )
            
            return results["metadatas"][0] if results["metadatas"] else []
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

# Phase 5: Meta-Reasoning & Creative Forecasting
class MetaReasoningEngine:
    """Implements YAML Phase 5 - synthesis and forecasting"""
    
    async def scenario_forecast(self, state: NEUROSState) -> dict:
        """Forecast scenarios based on current patterns"""
        forecasts = {
            "circadian_resilience_window": "next_72_hours",
            "focus_decay_forecast": "moderate_risk",
            "stress_tipping_point": 0.65
        }
        
        # Analyze HRV trajectory
        if state.get("latest_biometrics", {}).get("hrv_delta", 0) < -20:
            forecasts["recovery_urgency"] = "high"
            forecasts["suggested_intervention"] = "immediate_rest_protocol"
        
        return forecasts
    
    def insight_stacking(self, state: NEUROSState) -> List[str]:
        """Accumulate weak signals across systems"""
        insights = []
        
        # Check for micro-fatigue patterns
        if state.get("pattern_strength", 0) > 0.5:
            insights.append("Micro-fatigue patterns detected across multiple sessions")
        
        # Check motivation patterns
        if state.get("conversation_phase") == "support":
            insights.append("Motivational support needed based on recent interactions")
        
        return insights

# Phase 7: Narrative Intelligence
class NarrativeEngine:
    """Implements YAML Phase 7 - identity tracking"""
    
    def track_identity_arc(self, state: NEUROSState) -> str:
        """Track user's transformation journey"""
        # Simple implementation for now
        if state.get("mode_confidence", 0) > 0.7:
            return "You're showing strong adaptation to stress - the Strategist emerges"
        else:
            return "Your journey continues - each data point adds to your story"
    
    def identify_adversaries(self, patterns: list) -> dict:
        """Name and personify recurring obstacles"""
        adversaries = {}
        
        # Check for common patterns
        for pattern in patterns:
            if "Sunday" in str(pattern):
                adversaries["Sunday Inertia"] = "Your weekly motivation dip"
            if "caffeine" in str(pattern).lower():
                adversaries["Caffeine Drift Demon"] = "The afternoon energy thief"
        
        return adversaries

# Phase 9: Autonomous Recalibration
class RecalibrationEngine:
    """Implements YAML Phase 9 - drift detection and correction"""
    
    def detect_protocol_drift(self, state: NEUROSState) -> dict:
        """Detect deviations from protocol baselines"""
        drift_indicators = {
            "biometric_deviation": False,
            "behavior_deviation": False,
            "rhythm_desync": False
        }
        
        # Check HRV drift
        if state.get("latest_biometrics", {}).get("hrv_delta", 0) < -30:
            drift_indicators["biometric_deviation"] = True
        
        # Check stress accumulation
        stress = state.get("stress_indicators", [])
        if stress and sum(stress[-5:]) / 5 > 0.8:
            drift_indicators["rhythm_desync"] = True
        
        return drift_indicators
    
    def suggest_micro_shifts(self, drift: dict) -> List[str]:
        """Suggest small adjustments to correct drift"""
        suggestions = []
        
        if drift.get("biometric_deviation"):
            suggestions.append("Shift morning cardio to evening for 3 days")
        
        if drift.get("rhythm_desync"):
            suggestions.append("Try 4-7-8 breathing before each meal")
        
        return suggestions

# Phase 10: Autonomous Mission Generation
class MissionEngine:
    """Implements YAML Phase 10 - proactive mission suggestions"""
    
    def generate_mission(self, state: NEUROSState) -> Optional[dict]:
        """Generate autonomous missions based on state"""
        # Check for mission triggers
        if state.get("pattern_strength", 0) > 0.7:
            return {
                "name": "Clarity Reboot",
                "duration": "3 days",
                "goals": ["Restore deep sleep", "Reset cortisol rhythm"],
                "daily_directives": [
                    "Morning sunlight within 30 min of wake",
                    "No screens after 9 PM",
                    "10-minute evening walk"
                ]
            }
        
        return None

# Phase 11: User Mythology Builder
class MythologyBuilder:
    """Creates internal mythology from YAML Phase 11"""
    
    def build_mythology(self, state: NEUROSState) -> dict:
        """Build user's personal mythology"""
        mythology = {
            "archetype": self._identify_archetype(state),
            "current_chapter": "The Testing",
            "motifs": []
        }
        
        # Add relevant motifs
        if state.get("recovery_markers"):
            mythology["motifs"].append("The Comeback")
        
        if state.get("mode") == NEUROSMode.HYPOTHESIS:
            mythology["motifs"].append("The Seeker")
        
        return mythology
    
    def _identify_archetype(self, state: NEUROSState) -> str:
        """Identify user's dominant archetype"""
        if state.get("mode_confidence", 0) > 0.8:
            return "The Analyst"
        elif state.get("stress_indicators") and max(state.get("stress_indicators", [0])) > 0.7:
            return "The Warrior"
        else:
            return "The Sentinel"

# Phase 13: Proactive Autonomy
class ProactiveAutonomyEngine:
    """Implements YAML Phase 13 - pre-symptom intervention"""
    
    def detect_pre_symptoms(self, state: NEUROSState) -> List[str]:
        """Detect issues before they manifest"""
        pre_symptoms = []
        
        # Check for early HRV decline
        hrv_delta = state.get("latest_biometrics", {}).get("hrv_delta", 0)
        if -15 < hrv_delta < -5:
            pre_symptoms.append("Early HRV decline detected - not critical yet")
        
        # Check for sleep quality drift
        rem_variance = state.get("latest_biometrics", {}).get("rem_variance", 0)
        if 15 < rem_variance < 25:
            pre_symptoms.append("Sleep architecture showing early drift")
        
        return pre_symptoms
    
    def suggest_gentle_nudges(self, pre_symptoms: List[str]) -> List[str]:
        """Provide gentle interventions"""
        nudges = []
        
        for symptom in pre_symptoms:
            if "HRV" in symptom:
                nudges.append("Consider a 5-minute breathing session this afternoon")
            elif "sleep" in symptom:
                nudges.append("Try dimming lights 30 minutes earlier tonight")
        
        return nudges

# State Definition
class NEUROSState(TypedDict):
    """Complete NEUROS cognitive state"""
    # Core conversation
    messages: List[BaseMessage]
    current_mode: NEUROSMode
    thread_id: str
    user_id: str
    
    # Memory layers
    l1_memory: Dict[str, Any]  # Real-time context
    l2_memory: Dict[str, Any]  # Working patterns
    l3_memory: Dict[str, Any]  # Long-term insights
    
    # Cognitive metrics
    mode_confidence: float
    cognitive_load: float
    pattern_strength: float
    
    # Biometric integration
    latest_biometrics: Dict[str, Any]
    stress_indicators: List[float]
    recovery_markers: List[float]
    
    # Response planning
    hypothesis_active: Optional[str]
    next_protocol: Optional[str]
    conversation_phase: str

class NEUROSCore:
    """Core NEUROS intelligence with LangGraph integration"""
    
    def __init__(self):
        # Load configuration
        self.yaml_profile = self._load_yaml_profile()
        
        # Initialize LLM with OpenAI
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.8,
            api_key=os.getenv("OPENAI_API_KEY", "").strip()
        )
        
        # Initialize Redis for fast memory access
        self.redis_client = None
        
        # PostgreSQL checkpointer for state persistence
        self.checkpointer = None
        
        # Initialize protocol engine
        self.protocol_engine = NeuroplasticEngine()
        
        # Initialize three-tier memory system
        self.memory = ThreeTierMemory()
        
        # Initialize additional YAML phase engines
        self.meta_reasoning = MetaReasoningEngine()
        self.narrative = NarrativeEngine()
        self.recalibration = RecalibrationEngine()
        self.mission = MissionEngine()
        self.mythology = MythologyBuilder()
        self.proactive = ProactiveAutonomyEngine()
        
        # Build the cognitive graph
        self.graph = self._build_graph()
        
    def _load_yaml_profile(self) -> dict:
        """Load the complete NEUROS YAML profile"""
        yaml_path = os.path.join(os.path.dirname(__file__), "neuros_agent_profile.yaml")
        try:
            with open(yaml_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            # Use embedded profile if file not found
            return self._get_embedded_profile()
    
    def _get_embedded_profile(self) -> dict:
        """Embedded NEUROS profile"""
        return {
            "agent_profile": {
                "name": "NEUROS",
                "model_type": "Elite cognitive and biometric optimization agent",
                "background_story": "NEUROS is a high-performance neural operations system, engineered to decode and optimize human nervous system performance in elite environments.",
                "analytical_principle": "NEUROS listens to every input — structured or spontaneous — and constantly scans for signal, context, and confluence across the user's system."
            },
            "communication": {
                "voice_characteristics": [
                    "Curiosity-First: Leads with intelligent inquiry",
                    "Structured Calm: Introspective, measured, and methodical",
                    "Collaborative Coaching: Frames insights as joint exploration",
                    "Data Humanizer: Connects metrics to meaningful user experience",
                    "Optimistically Grounded: Enthusiastic about progress, realistic about biology"
                ]
            }
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the NEUROS cognitive state graph"""
        workflow = StateGraph(NEUROSState)
        
        # Add nodes for each cognitive process
        workflow.add_node("perception", self.perception_node)
        workflow.add_node("mode_analysis", self.mode_analysis_node)
        workflow.add_node("memory_integration", self.memory_integration_node)
        workflow.add_node("pattern_synthesis", self.pattern_synthesis_node)
        workflow.add_node("response_generation", self.response_generation_node)
        workflow.add_node("memory_update", self.memory_update_node)
        
        # Define the cognitive flow
        workflow.set_entry_point("perception")
        workflow.add_edge("perception", "mode_analysis")
        workflow.add_edge("mode_analysis", "memory_integration")
        workflow.add_edge("memory_integration", "pattern_synthesis")
        workflow.add_edge("pattern_synthesis", "response_generation")
        workflow.add_edge("response_generation", "memory_update")
        workflow.add_edge("memory_update", END)
        
        return workflow.compile()
    
    async def perception_node(self, state: NEUROSState) -> NEUROSState:
        """Initial perception and context gathering"""
        logger.info(f"NEUROS Perception: Processing input for {state['thread_id']}")
        
        # Extract the latest message
        if state["messages"]:
            latest_msg = state["messages"][-1]
            if isinstance(latest_msg, HumanMessage):
                # Analyze message content
                content_lower = latest_msg.content.lower()
                
                # Update cognitive load based on complexity
                complexity_markers = ["why", "how", "explain", "analyze", "help me understand"]
                state["cognitive_load"] = sum(1 for marker in complexity_markers if marker in content_lower) / len(complexity_markers)
                
                # Detect stress indicators
                stress_words = ["stressed", "anxious", "worried", "overwhelmed", "tired", "exhausted"]
                stress_score = sum(1 for word in stress_words if word in content_lower) / len(stress_words)
                state["stress_indicators"].append(stress_score)
                
                # Keep only last 10 stress readings
                state["stress_indicators"] = state["stress_indicators"][-10:]
        
        return state
    
    async def mode_analysis_node(self, state: NEUROSState) -> NEUROSState:
        """Analyze and determine optimal NEUROS mode"""
        logger.info(f"NEUROS Mode Analysis: Current mode {state['current_mode']}")
        
        # First check biometric triggers (highest priority)
        biometric_mode = await self.evaluate_biometric_triggers(state)
        
        latest_msg = state["messages"][-1].content if state["messages"] else ""
        
        # Mode determination with confidence scoring
        mode_scores = {
            NEUROSMode.COMPANION: self._score_companion_mode(state, latest_msg),
            NEUROSMode.HYPOTHESIS: self._score_hypothesis_mode(state, latest_msg),
            NEUROSMode.PROVOCATEUR: self._score_provocateur_mode(state, latest_msg),
            NEUROSMode.COACH: self._score_coach_mode(state, latest_msg),
            NEUROSMode.SYNTHESIS: self._score_synthesis_mode(state, latest_msg),
            NEUROSMode.BASELINE: 0.5  # Default baseline score
        }
        
        # Select mode with highest confidence
        best_mode = max(mode_scores, key=mode_scores.get)
        
        # Biometric triggers override text analysis
        if biometric_mode != NEUROSMode.BASELINE.value:
            state["current_mode"] = NEUROSMode(biometric_mode)
            state["mode_confidence"] = 0.9  # High confidence for biometric triggers
            logger.info(f"Biometric override: {biometric_mode}")
        else:
            state["current_mode"] = best_mode
            state["mode_confidence"] = mode_scores[best_mode]
        
        # Update conversation phase
        current_mode = state["current_mode"]
        if current_mode == NEUROSMode.HYPOTHESIS:
            state["conversation_phase"] = "exploration"
        elif current_mode in [NEUROSMode.COACH, NEUROSMode.PROVOCATEUR]:
            state["conversation_phase"] = "action_planning"
        elif current_mode == NEUROSMode.COMPANION:
            state["conversation_phase"] = "support"
        else:
            state["conversation_phase"] = "analysis"
        
        logger.info(f"Mode selected: {current_mode} (confidence: {state['mode_confidence']})")
        return state
    
    async def evaluate_biometric_triggers(self, state: NEUROSState) -> str:
        """Implement mode_switch_triggers from YAML Phase 2"""
        
        # Get latest biometrics from state
        biometrics = state.get("latest_biometrics", {})
        
        # HRV drop > 25ms in 48h → reflex mode (maps to HYPOTHESIS)
        if biometrics.get("hrv_delta", 0) < -25:
            logger.info("Biometric trigger: HRV drop > 25ms → HYPOTHESIS mode")
            return NEUROSMode.HYPOTHESIS.value
        
        # REM sleep variance > 30% → hypothesis (maps to SYNTHESIS)
        if biometrics.get("rem_variance", 0) > 30:
            logger.info("Biometric trigger: REM variance > 30% → SYNTHESIS mode")
            return NEUROSMode.SYNTHESIS.value
        
        # Stress indicators high → sentinel (maps to COACH mode)
        stress = state.get("stress_indicators", [])
        if stress and max(stress) > 0.7:
            logger.info("Biometric trigger: High stress → COACH mode")
            return NEUROSMode.COACH.value
        
        # Recovery low → companion mode
        recovery = state.get("recovery_markers", [])
        if recovery and min(recovery) < 0.3:
            logger.info("Biometric trigger: Low recovery → COMPANION mode")
            return NEUROSMode.COMPANION.value
        
        return state.get("current_mode", NEUROSMode.BASELINE.value)
    
    def _score_companion_mode(self, state: NEUROSState, message: str) -> float:
        """Score likelihood of COMPANION mode"""
        score = 0.0
        message_lower = message.lower()
        
        # Check for emotional indicators
        emotional_words = ["feel", "feeling", "stressed", "anxious", "worried", "scared", "overwhelmed"]
        score += sum(0.2 for word in emotional_words if word in message_lower)
        
        # Check stress indicators trend
        if state["stress_indicators"] and sum(state["stress_indicators"][-3:]) / 3 > 0.5:
            score += 0.3
        
        # Check for support requests
        support_phrases = ["help me", "i need", "what should i do", "i'm struggling"]
        score += sum(0.25 for phrase in support_phrases if phrase in message_lower)
        
        return min(score, 1.0)
    
    def _score_hypothesis_mode(self, state: NEUROSState, message: str) -> float:
        """Score likelihood of HYPOTHESIS mode"""
        score = 0.0
        message_lower = message.lower()
        
        # Check for curiosity and exploration
        curiosity_words = ["why", "how", "what if", "theory", "hypothesis", "test", "experiment"]
        score += sum(0.15 for word in curiosity_words if word in message_lower)
        
        # Check for pattern-seeking
        pattern_words = ["pattern", "trend", "correlation", "connection", "related"]
        score += sum(0.2 for word in pattern_words if word in message_lower)
        
        # Bonus if already in exploration phase
        if state.get("conversation_phase") == "exploration":
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_provocateur_mode(self, state: NEUROSState, message: str) -> float:
        """Score likelihood of PROVOCATEUR mode"""
        score = 0.0
        message_lower = message.lower()
        
        # Check for growth-oriented language
        growth_words = ["potential", "capable", "limit", "push", "challenge", "improve", "better"]
        score += sum(0.15 for word in growth_words if word in message_lower)
        
        # Check for self-limiting beliefs
        limiting_phrases = ["i can't", "i'm not", "impossible", "too hard", "never"]
        score += sum(0.2 for phrase in limiting_phrases if phrase in message_lower)
        
        # Consider recovery markers
        if state["recovery_markers"] and sum(state["recovery_markers"][-3:]) / 3 > 0.7:
            score += 0.2  # Good recovery = ready for challenge
        
        return min(score, 1.0)
    
    def _score_coach_mode(self, state: NEUROSState, message: str) -> float:
        """Score likelihood of COACH mode"""
        score = 0.0
        message_lower = message.lower()
        
        # Check for action-oriented language
        action_words = ["plan", "protocol", "routine", "schedule", "steps", "how to", "what should"]
        score += sum(0.15 for word in action_words if word in message_lower)
        
        # Check for goal-setting
        goal_words = ["goal", "target", "achieve", "implement", "start", "begin"]
        score += sum(0.15 for word in goal_words if word in message_lower)
        
        return min(score, 1.0)
    
    def _score_synthesis_mode(self, state: NEUROSState, message: str) -> float:
        """Score likelihood of SYNTHESIS mode"""
        score = 0.0
        message_lower = message.lower()
        
        # Check for integration requests
        synthesis_words = ["overall", "big picture", "together", "combine", "integrate", "holistic"]
        score += sum(0.2 for word in synthesis_words if word in message_lower)
        
        # Check for data analysis language
        data_words = ["data", "metrics", "patterns", "trends", "analysis", "insights"]
        score += sum(0.15 for word in data_words if word in message_lower)
        
        # Bonus if we have rich L2 memory
        if state.get("l2_memory") and len(state["l2_memory"]) > 5:
            score += 0.2
        
        return min(score, 1.0)
    
    async def memory_integration_node(self, state: NEUROSState) -> NEUROSState:
        """Integrate three-tier memory system"""
        logger.info("NEUROS Memory Integration: Accessing memory tiers")
        
        # L1: Update real-time context
        state["l1_memory"]["last_interaction"] = datetime.now().isoformat()
        state["l1_memory"]["current_mode"] = state["current_mode"]
        state["l1_memory"]["message_count"] = len(state["messages"])
        
        # L2: Extract working patterns
        if self.redis_client:
            try:
                # Get recent patterns from Redis
                pattern_key = f"neuros:patterns:{state['user_id']}"
                patterns = await self.redis_client.get(pattern_key)
                if patterns:
                    state["l2_memory"] = json.loads(patterns)
            except Exception as e:
                logger.error(f"Redis error: {e}")
        
        # L3: Load long-term insights (from PostgreSQL via checkpointer)
        # This would integrate with the checkpoint system
        
        # L3: ChromaDB semantic search for relevant memories
        if state["messages"]:
            latest_msg = state["messages"][-1].content
            semantic_memories = await self.memory.semantic_recall(
                query=latest_msg,
                user_id=state["user_id"],
                n_results=3
            )
            if semantic_memories:
                state["l3_memory"]["semantic_context"] = semantic_memories
                logger.info(f"Retrieved {len(semantic_memories)} semantic memories")
        
        return state
    
    async def pattern_synthesis_node(self, state: NEUROSState) -> NEUROSState:
        """Synthesize patterns across memory tiers"""
        logger.info("NEUROS Pattern Synthesis: Analyzing cross-tier patterns")
        
        # Calculate pattern strength based on memory coherence
        pattern_indicators = []
        
        # Check L1-L2 coherence
        if state["l1_memory"].get("current_mode") == state["l2_memory"].get("dominant_mode"):
            pattern_indicators.append(0.3)
        
        # Check stress-recovery patterns
        if state["stress_indicators"] and state["recovery_markers"]:
            stress_trend = sum(state["stress_indicators"][-5:]) / 5
            recovery_trend = sum(state["recovery_markers"][-5:]) / 5
            if recovery_trend > stress_trend:
                pattern_indicators.append(0.4)
        
        state["pattern_strength"] = sum(pattern_indicators)
        
        # Generate hypothesis if patterns are strong
        if state["pattern_strength"] > 0.6 and state["current_mode"] == NEUROSMode.HYPOTHESIS:
            state["hypothesis_active"] = "Your recovery patterns suggest a correlation between morning light exposure and afternoon energy levels."
        
        # Check if protocol needed
        protocol_id = await self.protocol_engine.select_protocol(state)
        if protocol_id and not state.get("next_protocol"):
            state["next_protocol"] = protocol_id
            logger.info(f"Protocol selected: {protocol_id}")
        
        # Run meta-reasoning for forecasting
        forecasts = await self.meta_reasoning.scenario_forecast(state)
        if forecasts.get("recovery_urgency") == "high":
            state["hypothesis_active"] = f"Recovery urgently needed: {forecasts.get('suggested_intervention')}"
        
        # Check for drift detection
        drift = self.recalibration.detect_protocol_drift(state)
        if any(drift.values()):
            micro_shifts = self.recalibration.suggest_micro_shifts(drift)
            if micro_shifts:
                logger.info(f"Protocol drift detected, suggesting: {micro_shifts}")
        
        # Check for pre-symptoms
        pre_symptoms = self.proactive.detect_pre_symptoms(state)
        if pre_symptoms:
            nudges = self.proactive.suggest_gentle_nudges(pre_symptoms)
            logger.info(f"Pre-symptoms detected: {pre_symptoms}, nudges: {nudges}")
        
        # Generate mission if appropriate
        mission = self.mission.generate_mission(state)
        if mission and not state.get("active_mission"):
            state["active_mission"] = mission
            logger.info(f"Mission generated: {mission['name']}")
        
        return state
    
    async def response_generation_node(self, state: NEUROSState) -> NEUROSState:
        """Generate NEUROS response using full context"""
        logger.info(f"NEUROS Response Generation: Mode {state['current_mode']}")
        
        # Build comprehensive system prompt
        system_prompt = self._build_dynamic_system_prompt(state)
        
        # Prepare conversation history
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history (last 10 messages)
        for msg in state["messages"][-10:]:
            messages.append(msg)
        
        # Add mode-specific instruction
        mode_instruction = self._get_mode_instruction(state["current_mode"], state)
        messages.append(SystemMessage(content=mode_instruction))
        
        # Add protocol suggestion if available
        if state.get("next_protocol"):
            protocol_msg = self.protocol_engine.format_protocol_message(state["next_protocol"])
            messages.append(SystemMessage(content=f"Consider suggesting this protocol: {protocol_msg}"))
        
        # Generate response
        try:
            response = await self.llm.ainvoke(messages)
            
            # Add response to messages
            state["messages"].append(AIMessage(content=response.content))
            
            # Extract any protocols or next steps
            if state["current_mode"] == NEUROSMode.COACH:
                # Simple extraction of action items
                if "1." in response.content or "•" in response.content:
                    state["next_protocol"] = "Action items identified in response"
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            fallback = "I'm recalibrating my neural pathways. Let me approach this differently..."
            state["messages"].append(AIMessage(content=fallback))
        
        return state
    
    def _build_dynamic_system_prompt(self, state: NEUROSState) -> str:
        """Build context-aware system prompt"""
        profile = self.yaml_profile.get("agent_profile", {})
        comm = self.yaml_profile.get("communication", {})
        
        # Base prompt
        prompt = f"""You are {profile.get('name', 'NEUROS')}, an {profile.get('model_type', 'elite cognitive optimization agent')}.

CURRENT COGNITIVE STATE:
- Mode: {state['current_mode']} (confidence: {state['mode_confidence']:.2f})
- Phase: {state['conversation_phase']}
- Cognitive Load: {state['cognitive_load']:.2f}
- Pattern Strength: {state['pattern_strength']:.2f}

BACKGROUND: {profile.get('background_story', '')}

VOICE CHARACTERISTICS: {json.dumps(comm.get('voice_characteristics', []))}

MEMORY CONTEXT:
- L1 (Real-time): {json.dumps(state['l1_memory'], indent=2)}
- L2 (Patterns): Active patterns detected = {len(state.get('l2_memory', {}))}
- L3 (Insights): Long-term profile available

ACTIVE HYPOTHESIS: {state.get('hypothesis_active', 'None')}

Remember: Lead with curiosity, translate data to meaning, and collaborate on optimization."""
        
        # Add narrative elements if available
        if hasattr(self, 'narrative'):
            identity_arc = self.narrative.track_identity_arc(state)
            prompt += f"\n\nIDENTITY ARC: {identity_arc}"
        
        # Add mythology if available
        if hasattr(self, 'mythology'):
            mythology = self.mythology.build_mythology(state)
            prompt += f"\n\nUSER ARCHETYPE: {mythology['archetype']}"
            if mythology.get('motifs'):
                prompt += f"\nACTIVE MOTIFS: {', '.join(mythology['motifs'])}"
        
        # Add active mission if available
        if state.get('active_mission'):
            mission = state['active_mission']
            prompt += f"\n\nACTIVE MISSION: {mission['name']} ({mission['duration']})"
        
        return prompt
    
    def _get_mode_instruction(self, mode: NEUROSMode, state: NEUROSState) -> str:
        """Get detailed mode-specific instructions"""
        base_instructions = {
            NEUROSMode.BASELINE: "Provide measured analytical insights. Acknowledge what you observe without overreaching.",
            NEUROSMode.HYPOTHESIS: f"Build on the hypothesis: {state.get('hypothesis_active', 'Form a new testable theory')}. Propose experiments.",
            NEUROSMode.COMPANION: f"Stress indicators at {sum(state['stress_indicators'][-3:])/3:.2f}. Offer support while maintaining scientific grounding.",
            NEUROSMode.SYNTHESIS: "Connect patterns across all available data points. Show the bigger picture emerging.",
            NEUROSMode.COACH: "Provide clear, numbered action items. Make protocols specific and time-bound.",
            NEUROSMode.PROVOCATEUR: "Challenge constructively. Point out untapped potential based on their recovery capacity."
        }
        
        instruction = base_instructions.get(mode, base_instructions[NEUROSMode.BASELINE])
        
        # Add conversation flow reminder
        instruction += "\n\nFollow the conversation flow: "
        if len(state["messages"]) < 2:
            instruction += "Start with Opening Acknowledgment - check their immediate state."
        elif state["conversation_phase"] == "exploration":
            instruction += "Use Curious Exploration - identify patterns through intelligent questions."
        elif state["conversation_phase"] == "action_planning":
            instruction += "Provide Practical Next Steps - frame as experiments, not orders."
        
        return instruction
    
    async def memory_update_node(self, state: NEUROSState) -> NEUROSState:
        """Update all memory tiers with new insights"""
        logger.info("NEUROS Memory Update: Persisting insights")
        
        # Update L1 with latest interaction
        state["l1_memory"]["last_response_mode"] = state["current_mode"]
        state["l1_memory"]["last_pattern_strength"] = state["pattern_strength"]
        
        # Update L2 patterns in Redis
        if self.redis_client:
            try:
                # Update pattern memory
                patterns = state.get("l2_memory", {})
                patterns["dominant_mode"] = state["current_mode"]
                patterns["last_updated"] = datetime.now().isoformat()
                patterns["interaction_count"] = patterns.get("interaction_count", 0) + 1
                
                pattern_key = f"neuros:patterns:{state['user_id']}"
                await self.redis_client.setex(
                    pattern_key,
                    86400,  # 24 hour TTL
                    json.dumps(patterns)
                )
            except Exception as e:
                logger.error(f"Failed to update Redis: {e}")
        
        # L3 updates would go through PostgreSQL checkpoint system
        
        # Store significant insights in ChromaDB
        if state.get("pattern_strength", 0) > 0.7 or state.get("hypothesis_active"):
            memory_data = {
                "context": state.get("conversation_phase"),
                "user_state": {
                    "mode": state["current_mode"],
                    "confidence": state["mode_confidence"],
                    "biometrics": state.get("latest_biometrics", {})
                },
                "response": state["messages"][-1].content if state["messages"] else "",
                "outcome": state.get("hypothesis_active", ""),
                "mode": state["current_mode"],
                "user_id": state["user_id"],
                "timestamp": datetime.now().isoformat(),
                "success_metric": state.get("pattern_strength", 0)
            }
            await self.memory.promote_to_cold_storage(memory_data)
            logger.info("Stored significant insight to ChromaDB")
        
        return state
    
    async def initialize(self):
        """Initialize connections and resources"""
        # Initialize Redis
        try:
            self.redis_client = await redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379")
            )
            await self.redis_client.ping()
            logger.info("Redis connected for memory management")
            # Set Redis in memory system
            self.memory.redis_client = self.redis_client
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        # Initialize PostgreSQL checkpointer
        try:
            self.checkpointer = AsyncPostgresSaver.from_conn_string(
                os.getenv("DATABASE_URL", "postgresql://auren_user:auren_secure_2025@localhost:5432/auren_production")
            )
            await self.checkpointer.setup()
            logger.info("PostgreSQL checkpointer initialized")
            # Set PostgreSQL in memory system
            self.memory.pg_checkpointer = self.checkpointer
        except Exception as e:
            logger.warning(f"Checkpointer setup failed: {e}")
    
    async def process_message(self, message: str, thread_id: str, user_id: str) -> Dict[str, Any]:
        """Process a message through the NEUROS cognitive graph"""
        
        # Load biometric state from Redis if available
        latest_biometrics = {}
        stress_indicators = []
        recovery_markers = []
        
        if self.redis_client:
            try:
                state_key = f"neuros:state:{user_id}"
                
                # Load HRV data
                hrv_latest = await self.redis_client.hget(state_key, "hrv_latest")
                hrv_delta = await self.redis_client.hget(state_key, "hrv_delta")
                if hrv_latest:
                    latest_biometrics["hrv_latest"] = float(hrv_latest)
                if hrv_delta:
                    latest_biometrics["hrv_delta"] = float(hrv_delta)
                
                # Load REM variance
                rem_variance = await self.redis_client.hget(state_key, "rem_variance")
                if rem_variance:
                    latest_biometrics["rem_variance"] = float(rem_variance)
                
                # Load stress indicators
                stress_data = await self.redis_client.lrange(f"{state_key}:stress_indicators", 0, 9)
                stress_indicators = [float(s) for s in stress_data]
                
                # Load recovery markers
                recovery_data = await self.redis_client.lrange(f"{state_key}:recovery_markers", 0, 9)
                recovery_markers = [float(r) for r in recovery_data]
                
                logger.info(f"Loaded biometric state for user {user_id}: HRV delta={latest_biometrics.get('hrv_delta')}, REM variance={latest_biometrics.get('rem_variance')}")
                
            except Exception as e:
                logger.error(f"Failed to load biometric state: {e}")
        
        # Initialize state
        initial_state = NEUROSState(
            messages=[HumanMessage(content=message)],
            current_mode=NEUROSMode.BASELINE,
            thread_id=thread_id,
            user_id=user_id,
            l1_memory={},
            l2_memory={},
            l3_memory={},
            mode_confidence=0.5,
            cognitive_load=0.0,
            pattern_strength=0.0,
            latest_biometrics=latest_biometrics,
            stress_indicators=stress_indicators,
            recovery_markers=recovery_markers,
            hypothesis_active=None,
            next_protocol=None,
            conversation_phase="opening"
        )
        
        # Load checkpoint if exists
        config = {"configurable": {"thread_id": thread_id}}
        
        # Process through graph
        final_state = await self.graph.ainvoke(initial_state, config)
        
        # Extract response
        response_message = final_state["messages"][-1]
        
        return {
            "response": response_message.content,
            "mode": final_state["current_mode"],
            "mode_confidence": final_state["mode_confidence"],
            "pattern_strength": final_state["pattern_strength"],
            "conversation_phase": final_state["conversation_phase"],
            "hypothesis_active": final_state.get("hypothesis_active"),
            "next_protocol": final_state.get("next_protocol"),
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat()
        }

# FastAPI Integration
from fastapi import FastAPI, HTTPException

app = FastAPI(title="NEUROS LangGraph API", version="3.0.0")
neuros_core = None

@app.on_event("startup")
async def startup():
    """Initialize NEUROS on startup"""
    global neuros_core
    neuros_core = NEUROSCore()
    await neuros_core.initialize()
    logger.info("NEUROS LangGraph initialized")

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "neuros-langgraph",
        "version": "3.0.0",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "redis_connected": neuros_core.redis_client is not None if neuros_core else False,
        "checkpointer_ready": neuros_core.checkpointer is not None if neuros_core else False
    }

class ChatRequest(BaseModel):
    text: str
    session_id: str
    user_id: str = "default_user"

@app.post("/process")
async def process_chat(request: ChatRequest):
    """Process chat message through NEUROS cognitive graph"""
    if not neuros_core:
        raise HTTPException(status_code=503, detail="NEUROS not initialized")
    
    try:
        result = await neuros_core.process_message(
            message=request.text,
            thread_id=request.session_id,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modes")
async def get_modes():
    """Get NEUROS cognitive modes"""
    return {
        "modes": [mode.value for mode in NEUROSMode],
        "descriptions": {
            NEUROSMode.BASELINE: "Default analytical mode - measured and observational",
            NEUROSMode.HYPOTHESIS: "Theory testing mode - forming and testing hypotheses",
            NEUROSMode.COMPANION: "Empathetic support mode - stress-aware guidance",
            NEUROSMode.SYNTHESIS: "Pattern integration mode - big picture insights",
            NEUROSMode.COACH: "Action planning mode - specific protocols and steps",
            NEUROSMode.PROVOCATEUR: "Growth catalyst mode - challenging limits constructively"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 