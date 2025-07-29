# Simplified NEUROS LangGraph Implementation without ChromaDB
# Focuses on core YAML features that can run with existing infrastructure

import os
import asyncio
import json
import logging
import uuid
import yaml
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="NEUROS LangGraph API", version="3.1.0-simple")

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
    l2_memory: Dict[str, Any]  # PostgreSQL warm memory
    latest_biometrics: Dict[str, Any]
    stress_indicators: List[float]
    recovery_markers: List[float]
    next_protocol: Optional[str]

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
        
        # Initialize Redis for fast memory access
        self.redis_client = None
        
        # PostgreSQL checkpointer for state persistence
        self.checkpointer = None
        
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
        workflow.add_node("response_generation", self.response_generation_node)
        workflow.add_node("memory_update", self.memory_update_node)
        
        # Define edges
        workflow.set_entry_point("mode_analysis")
        workflow.add_edge("mode_analysis", "memory_integration")
        workflow.add_edge("memory_integration", "pattern_synthesis")
        workflow.add_edge("pattern_synthesis", "response_generation")
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
        if biometric_mode != state.get("mode", NEUROSMode.BASELINE.value):
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
        
        return state.get("mode", NEUROSMode.BASELINE.value)
    
    def _score_companion_mode(self, state: NEUROSState, msg: str) -> float:
        """Score companion mode based on emotional support needs"""
        emotional_keywords = ["tired", "stressed", "anxious", "overwhelmed", "difficult"]
        score = sum(1 for word in emotional_keywords if word in msg.lower()) * 0.2
        
        # Check recovery markers
        if state.get("recovery_markers") and min(state["recovery_markers"]) < 0.5:
            score += 0.3
        
        return min(score, 0.9)
    
    def _score_hypothesis_mode(self, state: NEUROSState, msg: str) -> float:
        """Score hypothesis mode based on pattern exploration needs"""
        inquiry_keywords = ["why", "how", "pattern", "trend", "connection"]
        score = sum(1 for word in inquiry_keywords if word in msg.lower()) * 0.15
        
        # Boost if patterns detected
        if state.get("pattern_strength", 0) > 0.6:
            score += 0.4
        
        return min(score, 0.9)
    
    def _score_provocateur_mode(self, state: NEUROSState, msg: str) -> float:
        """Score provocateur mode for challenging assumptions"""
        if any(word in msg.lower() for word in ["always", "never", "impossible", "can't"]):
            return 0.7
        return 0.1
    
    def _score_coach_mode(self, state: NEUROSState, msg: str) -> float:
        """Score coach mode for guidance needs"""
        action_keywords = ["should", "advice", "recommend", "help", "improve"]
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
        """Integrate memory from L1 (Redis) and L2 (PostgreSQL)"""
        logger.info("NEUROS Memory Integration")
        
        # L1: Load immediate context from Redis
        if self.redis_client:
            try:
                user_key = f"neuros:user:{state['user_id']}"
                l1_data = await self.redis_client.hgetall(user_key)
                state["l1_memory"] = {k.decode(): v.decode() for k, v in l1_data.items()}
            except Exception as e:
                logger.error(f"Redis memory load failed: {e}")
        
        # L2: Checkpoint data is already in state from PostgreSQL
        
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
        if state["pattern_strength"] > 0.6 and state["current_mode"] == NEUROSMode.HYPOTHESIS:
            state["hypothesis_active"] = "Your recovery patterns suggest a correlation between morning light exposure and afternoon energy levels."
        
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
        
        # Generate response
        response = await self.llm.ainvoke(messages)
        
        # Add to messages
        state["messages"].append(response)
        
        return state
    
    def _build_dynamic_system_prompt(self, state: NEUROSState) -> str:
        """Build a dynamic system prompt based on YAML profile and current state"""
        base_prompt = f"""You are NEUROS, an elite cognitive and biometric optimization agent.

CURRENT MODE: {state['current_mode']} (confidence: {state['mode_confidence']:.2f})
USER STATE: Recovery markers at {state.get('recovery_markers', [0.5])[0]:.2f}

{self.profile.get('agent_profile', {}).get('background_story', '')}

COMMUNICATION STYLE:
- Curiosity-first approach
- Translate metrics into meaningful human insights
- Frame protocols as experiments, not orders

ACTIVE HYPOTHESIS: {state.get('hypothesis_active', 'None')}

Remember: Lead with curiosity, translate data to meaning, and collaborate on optimization."""
        
        return base_prompt
    
    def _get_mode_instruction(self, mode: str, state: NEUROSState) -> str:
        """Get mode-specific instructions"""
        mode_instructions = {
            NEUROSMode.COMPANION: "Be supportive and understanding. Focus on emotional resonance.",
            NEUROSMode.HYPOTHESIS: "Explore patterns actively. Ask probing questions about connections.",
            NEUROSMode.PROVOCATEUR: "Challenge assumptions constructively. Reframe limiting beliefs.",
            NEUROSMode.COACH: "Provide clear, actionable guidance. Break down complex goals.",
            NEUROSMode.SYNTHESIS: "Connect disparate insights. Show the bigger picture.",
            NEUROSMode.SENTINEL: "Monitor closely for risks. Be direct about concerns."
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
                await self.redis_client.hmset(user_key, updates)
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
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        # Initialize PostgreSQL checkpointer
        try:
            self.checkpointer = AsyncPostgresSaver.from_conn_string(
                os.getenv("DATABASE_URL", "postgresql://auren_user:auren_secure_2025@localhost:5432/auren_production")
            )
            await self.checkpointer.setup()
            logger.info("PostgreSQL checkpointer initialized")
        except Exception as e:
            logger.warning(f"Checkpointer setup failed: {e}")
        
        # Rebuild graph with checkpointer
        self.graph = self._build_graph()
    
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
                stress_data = await self.redis_client.hget(state_key, "stress_indicators")
                if stress_data:
                    stress_indicators = json.loads(stress_data)
                
                # Load recovery markers
                recovery_data = await self.redis_client.hget(state_key, "recovery_markers")
                if recovery_data:
                    recovery_markers = json.loads(recovery_data)
                
            except Exception as e:
                logger.error(f"Failed to load biometric state: {e}")
        
        # Initialize state
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
            latest_biometrics=latest_biometrics,
            stress_indicators=stress_indicators,
            recovery_markers=recovery_markers,
            next_protocol=None
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
                "metadata": {
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
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
    metadata: Dict[str, Any]

# API Routes
@app.on_event("startup")
async def startup_event():
    """Initialize NEUROS on startup"""
    await neuros.initialize()
    logger.info("NEUROS LangGraph v3.1.0-simple initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NEUROS LangGraph",
        "version": "3.1.0-simple",
        "features": {
            "modes": list(NEUROSMode),
            "memory_tiers": ["L1_Redis", "L2_PostgreSQL"],
            "biometric_triggers": True,
            "yaml_profile": bool(neuros.profile)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 