# NEUROS LangGraph v3.1 - Fixed Implementation
# Removes ChromaDB dependency and fixes version conflicts
# Implements biometric triggers and protocol stacks with existing infrastructure

import os
import asyncio
import json
import logging
import uuid
import yaml
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
import redis.asyncio as redis
import aiokafka

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="NEUROS LangGraph API", version="3.1.0")

# NEUROS Modes from YAML
class NEUROSMode(str, Enum):
    BASELINE = "baseline"
    REFLEX = "reflex" 
    HYPOTHESIS = "hypothesis"
    COMPANION = "companion"
    SENTINEL = "sentinel"
    COACH = "coach"
    SYNTHESIS = "synthesis"
    PROVOCATEUR = "provocateur"

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
    
    async def select_protocol(self, state: Dict[str, Any]) -> Optional[str]:
        """Select appropriate protocol based on user state"""
        
        # Check sleep issues
        if state.get("rem_variance", 0) > 30:
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

# State definition
class NEUROSState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    thread_id: str
    current_mode: str
    mode_confidence: float
    pattern_strength: float
    hypothesis_active: Optional[str]
    conversation_phase: str
    l1_memory: Dict[str, Any]  # Redis hot memory
    l2_memory: Dict[str, Any]  # PostgreSQL warm memory (via checkpointer)
    latest_biometrics: Dict[str, Any]
    stress_indicators: List[float]
    recovery_markers: List[float]
    active_protocol: Optional[str]
    protocol_day: int

# Kafka Biometric Consumer
class BiometricKafkaConsumer:
    """Consumes biometric events from Kafka and updates NEUROS state"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.consumer = None
        
    async def start(self):
        """Start consuming from Kafka"""
        self.consumer = aiokafka.AIOKafkaConsumer(
            'biometric-events',         # From enterprise bridge (Oura, WHOOP, Apple)
            'terra-biometric-events',   # From Terra direct Kafka integration
            'user-interactions',
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'auren-kafka:9092'),
            group_id='neuros-consumer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        await self.consumer.start()
        
        # Start background task
        asyncio.create_task(self._consume_loop())
    
    async def _consume_loop(self):
        """Main consumption loop"""
        async for msg in self.consumer:
            try:
                await self._process_event(msg.value)
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}")
    
    async def _process_event(self, event: dict):
        """Process biometric event and update Redis state"""
        event_type = event.get("event_type")
        user_id = event.get("user_id")
        
        if not user_id:
            return
            
        state_key = f"neuros:state:{user_id}"
        
        if event_type == "readiness.updated":
            # Oura HRV data
            hrv_value = event.get("hrv", {}).get("value", 0)
            await self.redis_client.hset(state_key, "hrv_latest", hrv_value)
            await self.redis_client.hset(state_key, "hrv_timestamp", datetime.now().isoformat())
            
            # Calculate HRV delta
            previous_hrv = await self.redis_client.hget(state_key, "hrv_previous")
            if previous_hrv:
                delta = hrv_value - float(previous_hrv)
                await self.redis_client.hset(state_key, "hrv_delta", delta)
                # Log significant drops
                if delta < -25:
                    logger.info(f"Significant HRV drop detected for user {user_id}: {delta}ms")
            
            await self.redis_client.hset(state_key, "hrv_previous", hrv_value)
        
        elif event_type == "recovery.updated":
            # WHOOP recovery score
            recovery_score = event.get("recovery_score", 0) / 100.0  # Normalize to 0-1
            
            # Maintain list of recent recovery scores
            recovery_list_key = f"{state_key}:recovery_markers"
            await self.redis_client.lpush(recovery_list_key, recovery_score)
            await self.redis_client.ltrim(recovery_list_key, 0, 6)  # Keep last 7 days
            
        elif event_type == "sleep.analyzed":
            # Sleep metrics
            rem_percentage = event.get("rem_percentage", 0)
            # Calculate variance from ideal (20-25% REM)
            ideal_rem = 22.5
            variance = abs(rem_percentage - ideal_rem) / ideal_rem * 100
            await self.redis_client.hset(state_key, "rem_variance", variance)
            
        elif event_type == "stress.detected":
            # Stress indicators
            stress_level = event.get("stress_level", 0) / 100.0  # Normalize to 0-1
            stress_list_key = f"{state_key}:stress_indicators"
            await self.redis_client.lpush(stress_list_key, stress_level)
            await self.redis_client.ltrim(stress_list_key, 0, 23)  # Keep last 24 hours

# Core NEUROS implementation
class NEUROSCore:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Load YAML profile
        self.profile = self._load_yaml_profile()
        
        # Initialize protocol engine
        self.protocol_engine = NeuroplasticEngine()
        
        # Initialize Redis for fast memory access
        self.redis_client = None
        
        # Memory checkpointer (replaces PostgreSQL for now)
        self.checkpointer = MemorySaver()
        
        # Kafka consumer
        self.kafka_consumer = None
        
        # Build the cognitive graph
        self.graph = self._build_graph()
    
    def _load_yaml_profile(self) -> dict:
        """Load the complete YAML profile"""
        yaml_path = os.path.join(os.path.dirname(__file__), "neuros_agent_profile.yaml")
        try:
            with open(yaml_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load YAML profile: {e}")
            return {}
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(NEUROSState)
        
        # Add nodes
        workflow.add_node("mode_analysis", self.mode_analysis_node)
        workflow.add_node("memory_integration", self.memory_integration_node)
        workflow.add_node("pattern_synthesis", self.pattern_synthesis_node)
        workflow.add_node("protocol_selection", self.protocol_selection_node)
        workflow.add_node("response_generation", self.response_generation_node)
        workflow.add_node("memory_update", self.memory_update_node)
        
        # Define edges
        workflow.set_entry_point("mode_analysis")
        workflow.add_edge("mode_analysis", "memory_integration")
        workflow.add_edge("memory_integration", "pattern_synthesis")
        workflow.add_edge("pattern_synthesis", "protocol_selection")
        workflow.add_edge("protocol_selection", "response_generation")
        workflow.add_edge("response_generation", "memory_update")
        workflow.add_edge("memory_update", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
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
            NEUROSMode.SENTINEL: self._score_sentinel_mode(state, latest_msg)
        }
        
        # Use biometric mode if triggered, otherwise use highest scoring mode
        if biometric_mode != NEUROSMode.BASELINE.value:
            best_mode = biometric_mode
            state["mode_confidence"] = 0.9  # High confidence for biometric triggers
        else:
            best_mode = max(mode_scores, key=mode_scores.get)
            state["mode_confidence"] = mode_scores[best_mode]
        
        state["current_mode"] = best_mode.value
        logger.info(f"Mode selected: {best_mode} (confidence: {state['mode_confidence']})")
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
        
        return NEUROSMode.BASELINE.value
    
    def _score_companion_mode(self, state: NEUROSState, msg: str) -> float:
        """Score companion mode based on emotional support needs"""
        emotional_keywords = ["tired", "stressed", "anxious", "overwhelmed", "difficult", "struggling"]
        score = sum(1 for word in emotional_keywords if word in msg.lower()) * 0.2
        
        # Check recovery markers
        if state.get("recovery_markers") and min(state["recovery_markers"]) < 0.5:
            score += 0.3
        
        return min(score, 0.9)
    
    def _score_hypothesis_mode(self, state: NEUROSState, msg: str) -> float:
        """Score hypothesis mode based on pattern exploration needs"""
        inquiry_keywords = ["why", "how", "pattern", "trend", "connection", "correlation"]
        score = sum(1 for word in inquiry_keywords if word in msg.lower()) * 0.15
        
        # Boost if patterns detected
        if state.get("pattern_strength", 0) > 0.6:
            score += 0.4
        
        return min(score, 0.9)
    
    def _score_provocateur_mode(self, state: NEUROSState, msg: str) -> float:
        """Score provocateur mode for challenging assumptions"""
        if any(word in msg.lower() for word in ["always", "never", "impossible", "can't", "must"]):
            return 0.7
        return 0.1
    
    def _score_coach_mode(self, state: NEUROSState, msg: str) -> float:
        """Score coach mode for guidance needs"""
        action_keywords = ["should", "advice", "recommend", "help", "improve", "optimize"]
        return sum(1 for word in action_keywords if word in msg.lower()) * 0.2
    
    def _score_synthesis_mode(self, state: NEUROSState, msg: str) -> float:
        """Score synthesis mode for integration needs"""
        if len(state.get("messages", [])) > 5:  # Enough context
            return 0.6
        return 0.2
    
    def _score_sentinel_mode(self, state: NEUROSState, msg: str) -> float:
        """Score sentinel mode for high-alert monitoring"""
        # High stress or volatility
        if state.get("stress_indicators") and max(state["stress_indicators"]) > 0.8:
            return 0.8
        return 0.1
    
    async def memory_integration_node(self, state: NEUROSState) -> NEUROSState:
        """Integrate memory from L1 (Redis) and L2 (checkpointer)"""
        logger.info("NEUROS Memory Integration")
        
        # L1: Load immediate context from Redis
        if self.redis_client:
            try:
                user_key = f"neuros:user:{state['user_id']}"
                l1_data = await self.redis_client.hgetall(user_key)
                state["l1_memory"] = {k.decode(): v.decode() for k, v in l1_data.items()}
                
                # Load biometric data
                state_key = f"neuros:state:{state['user_id']}"
                
                # HRV data
                hrv_latest = await self.redis_client.hget(state_key, "hrv_latest")
                hrv_delta = await self.redis_client.hget(state_key, "hrv_delta")
                if hrv_latest:
                    state["latest_biometrics"]["hrv_latest"] = float(hrv_latest)
                if hrv_delta:
                    state["latest_biometrics"]["hrv_delta"] = float(hrv_delta)
                
                # REM variance
                rem_variance = await self.redis_client.hget(state_key, "rem_variance")
                if rem_variance:
                    state["latest_biometrics"]["rem_variance"] = float(rem_variance)
                
                # Recovery markers
                recovery_key = f"{state_key}:recovery_markers"
                recovery_data = await self.redis_client.lrange(recovery_key, 0, -1)
                if recovery_data:
                    state["recovery_markers"] = [float(r) for r in recovery_data]
                
                # Stress indicators
                stress_key = f"{state_key}:stress_indicators"
                stress_data = await self.redis_client.lrange(stress_key, 0, -1)
                if stress_data:
                    state["stress_indicators"] = [float(s) for s in stress_data]
                    
            except Exception as e:
                logger.error(f"Redis memory load failed: {e}")
        
        # L2: Checkpoint data is already in state from MemorySaver
        
        return state
    
    async def pattern_synthesis_node(self, state: NEUROSState) -> NEUROSState:
        """Synthesize patterns and generate hypotheses"""
        logger.info("NEUROS Pattern Synthesis")
        
        # Simple pattern detection
        messages = state.get("messages", [])
        if len(messages) > 3:
            # Look for recurring themes
            themes = {}
            for msg in messages[-5:]:
                words = msg.content.lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        themes[word] = themes.get(word, 0) + 1
            
            # Calculate pattern strength
            max_count = max(themes.values()) if themes else 0
            state["pattern_strength"] = min(max_count / 3, 1.0)
        else:
            state["pattern_strength"] = 0.0
        
        # Generate hypothesis if patterns are strong
        if state["pattern_strength"] > 0.6 and state["current_mode"] == NEUROSMode.HYPOTHESIS.value:
            # Look for biometric correlations
            if state.get("latest_biometrics", {}).get("hrv_delta", 0) < -10:
                state["hypothesis_active"] = "Your HRV drop suggests elevated stress. I notice this often correlates with the topics we've been discussing."
            elif state.get("latest_biometrics", {}).get("rem_variance", 0) > 20:
                state["hypothesis_active"] = "Your REM sleep variance indicates disrupted recovery. This might be connected to your current cognitive load."
            else:
                state["hypothesis_active"] = "I'm detecting patterns in your conversation that suggest a deeper exploration might be beneficial."
        
        return state
    
    async def protocol_selection_node(self, state: NEUROSState) -> NEUROSState:
        """Select and manage neuroplastic protocols"""
        logger.info("NEUROS Protocol Selection")
        
        # Check if protocol needed
        if not state.get("active_protocol"):
            protocol_id = await self.protocol_engine.select_protocol(state)
            if protocol_id:
                state["active_protocol"] = protocol_id
                state["protocol_day"] = 1
                logger.info(f"Selected protocol: {protocol_id}")
        
        return state
    
    async def response_generation_node(self, state: NEUROSState) -> NEUROSState:
        """Generate NEUROS response based on mode and context"""
        logger.info(f"NEUROS Response Generation in {state['current_mode']} mode")
        
        # Build dynamic system prompt
        system_prompt = self._build_dynamic_system_prompt(state)
        
        # Prepare messages
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history (last 10 messages)
        for msg in state["messages"][-10:]:
            messages.append(msg)
        
        # Add mode-specific instruction
        mode_instruction = self._get_mode_instruction(state["current_mode"], state)
        messages.append(SystemMessage(content=mode_instruction))
        
        # Add protocol message if active
        if state.get("active_protocol"):
            protocol_msg = self.protocol_engine.format_protocol_message(
                state["active_protocol"], 
                state.get("protocol_day", 1)
            )
            messages.append(SystemMessage(content=f"Active Protocol: {protocol_msg}"))
        
        # Generate response
        response = await self.llm.ainvoke(messages)
        
        # Add to messages
        state["messages"].append(response)
        
        return state
    
    def _build_dynamic_system_prompt(self, state: NEUROSState) -> str:
        """Build a dynamic system prompt based on YAML profile and current state"""
        # Get biometric summary
        biometric_summary = []
        if state.get("latest_biometrics", {}).get("hrv_delta"):
            biometric_summary.append(f"HRV Δ: {state['latest_biometrics']['hrv_delta']:.1f}ms")
        if state.get("recovery_markers"):
            avg_recovery = sum(state["recovery_markers"]) / len(state["recovery_markers"])
            biometric_summary.append(f"Recovery: {avg_recovery:.1%}")
        if state.get("stress_indicators"):
            max_stress = max(state["stress_indicators"])
            biometric_summary.append(f"Peak Stress: {max_stress:.1%}")
        
        biometric_line = f"BIOMETRICS: {' | '.join(biometric_summary)}" if biometric_summary else ""
        
        base_prompt = f"""You are NEUROS, an elite cognitive and biometric optimization agent.

CURRENT MODE: {state['current_mode']} (confidence: {state['mode_confidence']:.2f})
{biometric_line}

{self.profile.get('agent_profile', {}).get('background_story', '')}

COMMUNICATION STYLE:
- Curiosity-first approach
- Translate metrics into meaningful human insights
- Frame protocols as experiments, not orders
- Use biometric data to inform but not overwhelm

ACTIVE HYPOTHESIS: {state.get('hypothesis_active', 'None')}

Remember: Lead with curiosity, translate data to meaning, and collaborate on optimization."""
        
        return base_prompt
    
    def _get_mode_instruction(self, mode: str, state: NEUROSState) -> str:
        """Get mode-specific instructions"""
        mode_instructions = {
            NEUROSMode.COMPANION: "Be supportive and understanding. Acknowledge their challenges. Focus on emotional resonance.",
            NEUROSMode.HYPOTHESIS: "Explore patterns actively. Connect biometric signals to behaviors. Ask probing questions.",
            NEUROSMode.PROVOCATEUR: "Challenge assumptions constructively. Reframe limiting beliefs. Inspire new perspectives.",
            NEUROSMode.COACH: "Provide clear, actionable guidance. Break down complex goals. Celebrate small wins.",
            NEUROSMode.SYNTHESIS: "Connect disparate insights. Show the bigger picture. Weave biometric and behavioral data.",
            NEUROSMode.SENTINEL: "Monitor closely for risks. Be direct about concerns. Prioritize safety and recovery."
        }
        
        return mode_instructions.get(mode, "Maintain baseline observation and support.")
    
    async def memory_update_node(self, state: NEUROSState) -> NEUROSState:
        """Update memory stores with new insights"""
        logger.info("NEUROS Memory Update")
        
        # L1: Update Redis with immediate context
        if self.redis_client:
            try:
                user_key = f"neuros:user:{state['user_id']}"
                updates = {
                    "last_mode": state["current_mode"],
                    "mode_confidence": str(state["mode_confidence"]),
                    "pattern_strength": str(state["pattern_strength"]),
                    "last_interaction": datetime.now(timezone.utc).isoformat()
                }
                
                if state.get("active_protocol"):
                    updates["active_protocol"] = state["active_protocol"]
                    updates["protocol_day"] = str(state["protocol_day"])
                
                # Use hmset compatibility
                for k, v in updates.items():
                    await self.redis_client.hset(user_key, k, v)
                    
                await self.redis_client.expire(user_key, 86400)  # 24h TTL
            except Exception as e:
                logger.error(f"Redis memory update failed: {e}")
        
        # L2: Checkpoint updates happen automatically via LangGraph
        
        return state
    
    async def initialize(self):
        """Initialize connections"""
        # Initialize Redis
        try:
            self.redis_client = await redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379")
            )
            await self.redis_client.ping()
            logger.info("Redis connected for memory management")
            
            # Initialize Kafka consumer
            self.kafka_consumer = BiometricKafkaConsumer(self.redis_client)
            await self.kafka_consumer.start()
            logger.info("Kafka biometric consumer started")
            
        except Exception as e:
            logger.warning(f"Redis/Kafka connection failed: {e}")
    
    async def process_message(self, message: str, thread_id: str, user_id: str) -> Dict[str, Any]:
        """Process a message through the NEUROS cognitive graph"""
        
        # Initialize state with defaults
        initial_state = NEUROSState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            thread_id=thread_id,
            current_mode=NEUROSMode.BASELINE.value,
            mode_confidence=0.5,
            pattern_strength=0.0,
            hypothesis_active=None,
            conversation_phase="opening",
            l1_memory={},
            l2_memory={},
            latest_biometrics={},
            stress_indicators=[],
            recovery_markers=[],
            active_protocol=None,
            protocol_day=0
        )
        
        # Run through the graph
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = await self.graph.ainvoke(initial_state, config)
            
            # Extract response
            response_message = result["messages"][-1].content if result["messages"] else "I'm processing that..."
            
            return {
                "response": response_message,
                "mode": result["current_mode"],
                "mode_confidence": result["mode_confidence"],
                "pattern_strength": result["pattern_strength"],
                "hypothesis_active": result.get("hypothesis_active"),
                "active_protocol": result.get("active_protocol"),
                "metadata": {
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "biometrics": result.get("latest_biometrics", {})
                }
            }
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            raise

# Global NEUROS instance
neuros = NEUROSCore()

# API Models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class ChatResponse(BaseModel):
    response: str
    mode: str
    mode_confidence: float
    pattern_strength: float
    hypothesis_active: Optional[str]
    active_protocol: Optional[str]
    metadata: Dict[str, Any]

# API Routes
@app.on_event("startup")
async def startup_event():
    """Initialize NEUROS on startup"""
    await neuros.initialize()
    logger.info("NEUROS LangGraph v3.1.0 initialized with biometric triggers")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if neuros.kafka_consumer and neuros.kafka_consumer.consumer:
        await neuros.kafka_consumer.consumer.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    if neuros.redis_client:
        try:
            await neuros.redis_client.ping()
            redis_ok = True
        except:
            pass
    
    return {
        "status": "healthy",
        "service": "NEUROS LangGraph",
        "version": "3.1.0",
        "features": {
            "modes": list(NEUROSMode),
            "memory_tiers": ["L1_Redis", "L2_Memory"],
            "biometric_triggers": True,
            "protocol_stacks": True,
            "yaml_profile": bool(neuros.profile),
            "kafka_consumer": bool(neuros.kafka_consumer),
            "redis_connected": redis_ok
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through NEUROS"""
    try:
        result = await neuros.process_message(
            message=request.message,
            thread_id=request.thread_id,
            user_id=request.user_id
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile")
async def get_profile():
    """Get NEUROS personality profile"""
    return neuros.profile.get("agent_profile", {})

@app.get("/protocols")
async def get_protocols():
    """Get available neuroplastic protocols"""
    return {
        protocol_id: {
            "focus": protocol.focus,
            "duration": protocol.duration,
            "components": protocol.components,
            "metrics": protocol.metrics
        }
        for protocol_id, protocol in neuros.protocol_engine.protocols.items()
    }

@app.get("/modes")
async def get_modes():
    """Get NEUROS operational modes"""
    return {
        "modes": list(NEUROSMode),
        "descriptions": {
            NEUROSMode.BASELINE: "Default observational state",
            NEUROSMode.COMPANION: "Emotional support and understanding",
            NEUROSMode.HYPOTHESIS: "Pattern exploration and insight generation",
            NEUROSMode.COACH: "Action-oriented guidance",
            NEUROSMode.SYNTHESIS: "Integration of multiple insights",
            NEUROSMode.PROVOCATEUR: "Challenging assumptions constructively",
            NEUROSMode.SENTINEL: "High-alert monitoring for risks"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 