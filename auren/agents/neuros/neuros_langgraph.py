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

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage
import redis.asyncio as redis
from pydantic import BaseModel, Field

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
        state["current_mode"] = best_mode
        state["mode_confidence"] = mode_scores[best_mode]
        
        # Update conversation phase
        if best_mode == NEUROSMode.HYPOTHESIS:
            state["conversation_phase"] = "exploration"
        elif best_mode in [NEUROSMode.COACH, NEUROSMode.PROVOCATEUR]:
            state["conversation_phase"] = "action_planning"
        elif best_mode == NEUROSMode.COMPANION:
            state["conversation_phase"] = "support"
        else:
            state["conversation_phase"] = "analysis"
        
        logger.info(f"Mode selected: {best_mode} (confidence: {state['mode_confidence']})")
        return state
    
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
    
    async def process_message(self, message: str, thread_id: str, user_id: str) -> Dict[str, Any]:
        """Process a message through the NEUROS cognitive graph"""
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
            latest_biometrics={},
            stress_indicators=[],
            recovery_markers=[],
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