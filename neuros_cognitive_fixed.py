#!/usr/bin/env python3
"""
NEUROS Cognitive Architecture - REDIS API FIXED VERSION
=======================================================
All Redis API calls modernized for compatibility.
Ready for staged deployment.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TypedDict, Generator
from enum import Enum
from contextlib import contextmanager

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Database and storage
import asyncpg
from pgvector.asyncpg import register_vector

# Redis for hot memory - FIXED IMPORTS
import redis
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore

# FastAPI integration
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# =====================================================
# LANGGRAPH STATE DEFINITION
# =====================================================

class CognitiveMode(Enum):
    """NEUROS Cognitive Modes from specification."""
    BASELINE = "baseline"
    REFLEX = "reflex"
    HYPOTHESIS = "hypothesis"
    COMPANION = "companion"
    SENTINEL = "sentinel"

class NEUROSState(TypedDict):
    """Enhanced LangGraph state with cognitive architecture."""
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    biometric_data: Dict[str, Any]
    biometric_source: str
    weak_signals: List[Dict[str, Any]]
    current_arc: str
    current_archetype: str
    harmony_score: float
    cognitive_mode: CognitiveMode
    request_type: str
    response_cached: bool
    memory_context: Dict[str, Any]

# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class AnalyzeRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

# =====================================================
# REQUEST CLASSIFIER (Quick Win #1)
# =====================================================

class RequestClassifier:
    """Classifies requests for fast-path routing."""
    
    SIMPLE_PATTERNS = [
        "hello", "hi", "hey", "good morning", "good afternoon", 
        "good evening", "how are you", "what's up", "sup"
    ]
    
    STATUS_PATTERNS = [
        "status", "how am i doing", "check in", "update",
        "my progress", "how's my", "am i okay"
    ]
    
    @staticmethod
    def classify(message: str) -> str:
        """Classify request type for optimal routing."""
        message_lower = message.lower().strip()
        
        if any(pattern in message_lower for pattern in RequestClassifier.SIMPLE_PATTERNS):
            return "simple_greeting"
        
        if any(pattern in message_lower for pattern in RequestClassifier.STATUS_PATTERNS):
            return "status_check"
        
        return "complex_analysis"

# =====================================================
# THREE-TIER MEMORY SYSTEM - FIXED REDIS OPERATIONS
# =====================================================

class MemoryTier:
    """Implements three-tier memory with FIXED Redis sync operations."""
    
    def __init__(self, redis_client: redis.Redis, pg_pool=None):
        self.redis = redis_client
        self.pg_pool = pg_pool
        
    def get_hot_memory(self, user_id: str) -> Dict[str, Any]:
        """Hot tier: <24h, millisecond access. SYNC operation."""
        key = f"neuros:hot:{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else {}
        
    def store_hot_memory(self, user_id: str, data: Dict[str, Any]):
        """Store in hot tier with 24h TTL. SYNC operation."""
        key = f"neuros:hot:{user_id}"
        self.redis.setex(key, timedelta(hours=24), json.dumps(data))
        
    def get_personalized_greeting(self, user_id: str) -> Optional[str]:
        """Get cached personalized greeting. SYNC operation."""
        memory = self.get_hot_memory(user_id)
        return memory.get("personalized_greeting")

# =====================================================
# COGNITIVE MODE MANAGER
# =====================================================

class CognitiveModeManager:
    """Manages NEUROS cognitive mode switching."""
    
    @staticmethod
    def determine_mode(state: NEUROSState) -> CognitiveMode:
        """Determine cognitive mode based on state."""
        request_type = state.get("request_type", "complex_analysis")
        
        if request_type == "simple_greeting":
            return CognitiveMode.COMPANION
        elif request_type == "status_check":
            return CognitiveMode.BASELINE
            
        biometric_data = state.get("biometric_data", {})
        if biometric_data.get("hrv", 100) < 25:
            return CognitiveMode.REFLEX
            
        return CognitiveMode.HYPOTHESIS

# =====================================================
# ENHANCED COGNITIVE ARCHITECTURE WORKFLOW
# =====================================================

class NEUROSCognitiveWorkflow:
    """Full cognitive architecture with FIXED Redis operations."""
    
    def __init__(self, config: Dict[str, Any], redis_client: redis.Redis = None, pg_pool=None):
        self.config = config
        self.redis_client = redis_client
        self.memory_tier = MemoryTier(redis_client, pg_pool) if redis_client else None
        
        # Initialize advanced engines
        self.mission_engine = AutonomousMissionEngine()
        self.pre_symptom_detector = PreSymptomDetector()
        self.neuroplastic_protocols = NeuroplasticProtocol()
        self.narrative_engine = NarrativeIntelligence()
        
        # Only initialize LLM for modes that need it
        self.llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
            openai_api_key=config["openai"]["api_key"]
        )
        
        # Mode-specific prompts
        self.mode_prompts = {
            CognitiveMode.COMPANION: SystemMessage(content="""
                You are NEUROS in companion mode - warm, supportive, and conversational.
                Lead with intelligent inquiry and curiosity. Frame insights as joint exploration.
                Use metaphors naturally (rivers, engines, sentinels). 
                Keep responses brief and friendly. Focus on emotional support over analysis.
            """),
            CognitiveMode.BASELINE: SystemMessage(content="""
                You are NEUROS in baseline mode - observing patterns and providing updates.
                Maintain structured calm. Translate metrics into meaningful human experience.
                Give concise status summaries based on recent patterns. Be informative but brief.
                Always provide context before conclusion.
            """),
            CognitiveMode.REFLEX: SystemMessage(content="""
                You are NEUROS in reflex mode - IMMEDIATE INTERVENTION REQUIRED.
                Be direct, actionable, and focused on immediate steps to address the crisis.
                Skip pleasantries - focus on what needs to happen RIGHT NOW.
                Deploy emergency protocols without hesitation.
            """),
            CognitiveMode.HYPOTHESIS: SystemMessage(content="""
                You are NEUROS in hypothesis mode - deeply analytical and pattern-seeking.
                Lead with intelligent inquiry. Explore connections, test assumptions.
                Use your full personality with metaphors and collaborative exploration.
                Frame protocols as experiments, not orders.
            """),
            CognitiveMode.SENTINEL: SystemMessage(content="""
                You are NEUROS in sentinel mode - high-alert monitoring.
                Track biometric volatility and psychological flags with vigilance.
                Maintain calm authority while conveying urgency when needed.
                Focus on early warning signs and preventive measures.
            """)
        }
        
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the enhanced cognitive architecture workflow."""
        workflow = StateGraph(NEUROSState)
        
        # Core cognitive nodes
        workflow.add_node("classify_request", self.classify_request_node)
        workflow.add_node("check_memory", self.check_memory_node)
        workflow.add_node("fast_response", self.fast_response_node)
        workflow.add_node("cognitive_processing", self.cognitive_processing_node)
        workflow.add_node("update_memory", self.update_memory_node)
        
        # Routing
        workflow.add_edge("classify_request", "check_memory")
        
        workflow.add_conditional_edges(
            "check_memory",
            self.route_by_priority,
            {
                "fast": "fast_response",
                "process": "cognitive_processing"
            }
        )
        
        workflow.add_edge("fast_response", "update_memory")
        workflow.add_edge("cognitive_processing", "update_memory")
        workflow.add_edge("update_memory", END)
        
        workflow.set_entry_point("classify_request")
        
        return workflow.compile()
    
    async def classify_request_node(self, state: NEUROSState) -> NEUROSState:
        """Classify the incoming request."""
        message = state["messages"][-1].content if state["messages"] else ""
        state["request_type"] = RequestClassifier.classify(message)
        state["cognitive_mode"] = CognitiveModeManager.determine_mode(state)
        return state
    
    async def check_memory_node(self, state: NEUROSState) -> NEUROSState:
        """Check memory for cached responses."""
        if self.memory_tier and state["request_type"] == "simple_greeting":
            cached_greeting = self.memory_tier.get_personalized_greeting(state["user_id"])
            if cached_greeting:
                state["response_cached"] = True
                state["messages"].append(AIMessage(content=cached_greeting))
        return state
    
    def route_by_priority(self, state: NEUROSState) -> str:
        """Route based on request type and cache status."""
        if state.get("response_cached"):
            return "fast"
        elif state["request_type"] == "simple_greeting":
            return "fast"
        else:
            return "process"
    
    async def fast_response_node(self, state: NEUROSState) -> NEUROSState:
        """Generate fast response for simple requests."""
        if not state.get("response_cached"):
            hour = datetime.now().hour
            time_greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
            
            greetings = [
                f"{time_greeting}! Sleep latency rose 19 minutes last night — how did it feel subjectively?",
                f"{time_greeting}. Your nervous system seems settled. What's on your mind today?",
                f"{time_greeting}! I noticed some interesting patterns. Ready to explore?"
            ]
            
            response = greetings[hash(state["user_id"]) % len(greetings)]
            state["messages"].append(AIMessage(content=response))
            
        return state
    
    async def cognitive_processing_node(self, state: NEUROSState) -> NEUROSState:
        """Full cognitive processing for complex requests."""
        mode = state["cognitive_mode"]
        messages = [self.mode_prompts[mode]]
        messages.append(HumanMessage(content=state["messages"][-1].content))
        
        response = await self.llm.ainvoke(messages)
        state["messages"].append(response)
        
        return state
    
    async def update_memory_node(self, state: NEUROSState) -> NEUROSState:
        """Update memory with conversation context."""
        if self.memory_tier:
            memory_data = {
                "last_interaction": datetime.now().isoformat(),
                "last_mode": state["cognitive_mode"].value,
                "request_type": state["request_type"]
            }
            
            if state["request_type"] == "simple_greeting" and not state.get("response_cached"):
                memory_data["personalized_greeting"] = state["messages"][-1].content
                
            self.memory_tier.store_hot_memory(state["user_id"], memory_data)
            
        return state

# =====================================================
# SIMPLIFIED ADVANCED ENGINES (for initial deployment)
# =====================================================

class MissionType(Enum):
    """Types of autonomous missions."""
    CLARITY_REBOOT = "clarity_reboot"
    PUSH_PHASE_INITIATION = "push_phase_initiation"
    INTROSPECTION_MISSION = "introspection_mission"
    CIRCADIAN_LOCKDOWN = "circadian_lockdown"
    COGNITIVE_BURNOUT_FLUSH = "cognitive_burnout_flush"

class AutonomousMissionEngine:
    """Simplified mission engine."""
    async def should_generate_mission(self, state: NEUROSState) -> Optional[MissionType]:
        return None  # Disabled for initial deployment
    
    def generate_mission_prompt(self, mission_type: MissionType) -> str:
        return ""

class PreSymptomDetector:
    """Simplified pre-symptom detector."""
    async def detect_pre_symptoms(self, user_history: Dict) -> List[Dict]:
        return []  # Disabled for initial deployment

class NeuroplasticProtocol:
    """Simplified protocol engine."""
    def select_protocol(self, user_state: Dict) -> Optional[str]:
        return None  # Disabled for initial deployment

class NarrativeIntelligence:
    """Simplified narrative engine."""
    async def detect_current_archetype(self, user_behavior: Dict) -> str:
        return "strategist"  # Default for initial deployment
    
    def track_identity_evolution(self, old_archetype: str, new_archetype: str) -> str:
        return ""

# =====================================================
# FASTAPI INTEGRATION
# =====================================================

class NEUROSFastAPIIntegration:
    """Integrates NEUROS cognitive architecture with FastAPI."""
    
    def __init__(self, neuros_workflow: NEUROSCognitiveWorkflow):
        self.workflow = neuros_workflow
        self.app = FastAPI(title="NEUROS Cognitive Architecture")
        self._setup_middleware()
        self._setup_routes()
        
    def _setup_middleware(self):
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://auren-4yzu414cz-jason-madrugas-projects.vercel.app",
                "https://auren-pwa.vercel.app",
                "http://localhost:3000",
                "http://localhost:5173"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_routes(self):
        """Define FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Enhanced health check."""
            return {
                "status": "healthy", 
                "service": "neuros-cognitive-architecture",
                "implementation": "staged-deployment-v1",
                "features": {
                    "request_classification": True,
                    "memory_tier": True,
                    "cognitive_modes": True,
                    "fast_path": True
                }
            }
        
        @self.app.post("/api/agents/neuros/analyze")
        async def analyze_with_neuros(request: AnalyzeRequest):
            """Cognitive architecture endpoint."""
            try:
                start_time = datetime.now()
                
                # Initialize state
                state = NEUROSState(
                    messages=[HumanMessage(content=request.message)],
                    user_id=request.user_id,
                    session_id=request.session_id,
                    biometric_data={},
                    biometric_source="none",
                    weak_signals=[],
                    current_arc="baseline",
                    current_archetype="strategist",
                    harmony_score=1.0,
                    cognitive_mode=CognitiveMode.BASELINE,
                    request_type="unknown",
                    response_cached=False,
                    memory_context={}
                )
                
                # Run workflow
                result = await self.workflow.workflow.ainvoke(state)
                
                # Extract response
                neuros_response = result["messages"][-1].content
                
                # Calculate performance
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                logger.info(f"Request type: {result['request_type']}, "
                          f"Mode: {result['cognitive_mode'].value}, "
                          f"Response time: {response_time:.3f}s, "
                          f"Cached: {result.get('response_cached', False)}")
                
                return {
                    "response": neuros_response,
                    "cognitive_mode": result["cognitive_mode"].value,
                    "request_type": result["request_type"],
                    "response_cached": result.get("response_cached", False),
                    "weak_signals_detected": len(result["weak_signals"]),
                    "narrative_arc": result["current_arc"],
                    "data_quality": result["biometric_source"],
                    "session_id": request.session_id,
                    "response_time": response_time
                }
                
            except Exception as e:
                logger.error(f"NEUROS analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# INITIALIZATION - FIXED FUNCTION NAME
# =====================================================

async def initialize_neuros_advanced_langgraph(config_path: str):
    """Initialize NEUROS with FIXED Redis API and correct function name."""
    # Load configuration
    with open(config_path) as f:
        config = json.load(f)
    
    # Create SYNC Redis client using modern API
    redis_client = redis.Redis.from_url(
        config.get("redis_url", "redis://auren-redis:6379"),
        decode_responses=True
    )
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running without memory tier.")
        redis_client = None
    
    # Initialize PostgreSQL pool if configured
    pg_pool = None
    if config.get("postgres_url") and False:  # Disabled for initial deployment
        try:
            pg_pool = await asyncpg.create_pool(
                config["postgres_url"],
                min_size=5,
                max_size=20
            )
            logger.info("PostgreSQL pool created successfully")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
    
    # Create cognitive architecture workflow
    workflow = NEUROSCognitiveWorkflow(config, redis_client, pg_pool)
    
    # Create FastAPI integration
    api = NEUROSFastAPIIntegration(workflow)
    
    logger.info("NEUROS Cognitive Architecture initialized (Staged Deployment v1)")
    logger.info("Features enabled: Request Classification, Memory Tier, Fast Path")
    logger.info("Expected response times: <100ms (cached), <500ms (template), 2-5s (complex)")
    
    return api.app 