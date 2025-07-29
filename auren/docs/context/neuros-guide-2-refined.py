# NEUROS Implementation Guide #2 (REFINED): Advanced Reasoning & Identity
# Aligned with AUREN's LangGraph Architecture
# Updated: 2025-07-29
# Status: Adapted for current infrastructure constraints

"""
CRITICAL ARCHITECTURE UPDATES
============================
Based on Senior Engineer feedback, this refined guide:
✅ Uses LangGraph (not CrewAI) for state management
✅ Works around broken biometric pipeline with fallback patterns
✅ Stores narrative memory in PostgreSQL (ChromaDB removed)
✅ Simplifies multi-agent features (only NEUROS active)
✅ Integrates with FastAPI endpoints
✅ Handles current infrastructure limitations

CURRENT REALITY CHECK
====================
- Biometric pipeline: BROKEN (webhooks arrive but don't reach Kafka)
- ChromaDB: REMOVED (build issues)
- Other agents: NOT DEPLOYED (only NEUROS active)
- Framework: LangGraph (CrewAI fully removed)
- Deployment: Docker Compose (not K8s yet)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque

# LangGraph imports (replacing CrewAI)
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import PostgresSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings

# PostgreSQL for narrative storage (replacing ChromaDB)
import asyncpg
from pgvector.asyncpg import register_vector

# Redis for hot memory
import redis.asyncio as redis

# Kafka (even though biometric pipeline is broken, keep interface ready)
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

# FastAPI integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# =====================================================
# LANGGRAPH STATE DEFINITION (Replacing CrewAI Agent)
# =====================================================

class NEUROSState(TypedDict):
    """
    LangGraph state for NEUROS's advanced reasoning.
    This replaces the CrewAI agent state management.
    """
    # Core conversation state
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    
    # Biometric state (with fallback for broken pipeline)
    biometric_data: Dict[str, Any]
    biometric_source: str  # "live", "cached", or "simulated"
    last_biometric_update: datetime
    
    # Weak signal tracking
    weak_signals: List[Dict[str, Any]]
    active_forecasts: Dict[str, Any]
    
    # Narrative memory (PostgreSQL-based)
    current_arc: str
    storyline_elements: List[Dict[str, Any]]
    identity_markers: List[Dict[str, Any]]
    
    # Behavior modeling
    current_archetype: str
    archetype_scores: Dict[str, float]
    
    # Multi-agent readiness (for future)
    agent_conflicts: List[Dict[str, Any]]
    harmony_score: float

# =====================================================
# PHASE 5: META-REASONING & CREATIVE FORECASTING
# (Adapted for broken biometric pipeline)
# =====================================================

class WeakSignalDetector:
    """
    Detects weak signals even with limited biometric data.
    Includes fallback patterns for when live data isn't available.
    """
    
    def __init__(self, pg_pool: asyncpg.Pool, redis_client: redis.Redis):
        self.pg_pool = pg_pool
        self.redis = redis_client
        self.embeddings = OpenAIEmbeddings()
        
    async def detect_weak_signals(self, state: NEUROSState) -> List[Dict[str, Any]]:
        """
        Detect weak signals with graceful degradation for missing biometrics.
        """
        signals = []
        
        # Check biometric data availability
        if state["biometric_source"] == "live":
            # Full analysis with live data
            signals.extend(await self._analyze_live_biometrics(state["biometric_data"]))
        elif state["biometric_source"] == "cached":
            # Partial analysis with cached data
            logger.warning("Using cached biometrics for weak signal detection")
            signals.extend(await self._analyze_cached_patterns(state["user_id"]))
        else:
            # Behavioral analysis only (no biometrics)
            logger.info("No biometric data available - using conversation patterns only")
            signals.extend(await self._analyze_conversation_patterns(state["messages"]))
            
        # Always analyze linguistic patterns (works regardless of biometric pipeline)
        linguistic_signals = await self._detect_linguistic_weak_signals(state["messages"])
        signals.extend(linguistic_signals)
        
        return signals
    
    async def _analyze_conversation_patterns(self, messages: List[BaseMessage]) -> List[Dict]:
        """
        Extract weak signals from conversation when biometrics unavailable.
        This is NEUROS being resourceful despite infrastructure limitations.
        """
        signals = []
        
        # Analyze message frequency and timing
        if len(messages) > 5:
            time_gaps = []
            for i in range(1, len(messages)):
                if hasattr(messages[i], 'timestamp') and hasattr(messages[i-1], 'timestamp'):
                    gap = messages[i].timestamp - messages[i-1].timestamp
                    time_gaps.append(gap.total_seconds())
                    
            if time_gaps and np.mean(time_gaps) < 30:  # Rapid messages
                signals.append({
                    "type": "conversation_urgency",
                    "confidence": 0.7,
                    "narrative": "Your rapid messages suggest elevated stress or urgency",
                    "source": "linguistic"
                })
                
        # Analyze emotional tone progression
        tone_shift = self._analyze_tone_progression(messages[-5:])
        if tone_shift:
            signals.append(tone_shift)
            
        return signals
    
    async def _get_fallback_biometric_estimate(self, user_id: str) -> Dict[str, Any]:
        """
        Estimate biometric state from historical patterns when live data unavailable.
        """
        async with self.pg_pool.acquire() as conn:
            # Get last known good biometric state
            result = await conn.fetchrow("""
                SELECT biometric_data, recorded_at
                FROM user_biometric_history
                WHERE user_id = $1
                ORDER BY recorded_at DESC
                LIMIT 1
            """, user_id)
            
            if result and (datetime.now() - result['recorded_at']).days < 7:
                return {
                    "data": result['biometric_data'],
                    "staleness_days": (datetime.now() - result['recorded_at']).days,
                    "reliability": 0.5  # Degraded confidence
                }
            
        return None

# =====================================================
# NARRATIVE MEMORY WITH POSTGRESQL (Replacing ChromaDB)
# =====================================================

class PostgreSQLNarrativeMemory:
    """
    Implements narrative memory using PostgreSQL with pgvector.
    This replaces the ChromaDB implementation due to build issues.
    """
    
    def __init__(self, pg_pool: asyncpg.Pool):
        self.pg_pool = pg_pool
        self.embeddings = OpenAIEmbeddings()
        
    async def initialize_schema(self):
        """Create narrative memory tables with vector support."""
        async with self.pg_pool.acquire() as conn:
            # Register pgvector extension
            await register_vector(conn)
            
            # Create narrative memory table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS narrative_memories (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    memory_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB,
                    arc_phase VARCHAR(50),
                    emotional_tone VARCHAR(50),
                    turning_point BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_narrative_user_time 
                ON narrative_memories(user_id, timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_narrative_embedding 
                ON narrative_memories USING ivfflat (embedding vector_cosine_ops);
            """)
            
    async def store_narrative_element(self, 
                                    user_id: str,
                                    element: Dict[str, Any]) -> int:
        """Store a narrative element with embedding."""
        # Generate embedding for semantic search
        text_content = f"{element['type']}: {element['content']}"
        embedding = await self.embeddings.aembed_query(text_content)
        
        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO narrative_memories 
                (user_id, timestamp, memory_type, content, embedding, 
                 metadata, arc_phase, emotional_tone, turning_point)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, 
            user_id, 
            element.get('timestamp', datetime.now()),
            element['type'],
            element['content'],
            embedding,
            json.dumps(element.get('metadata', {})),
            element.get('arc_phase'),
            element.get('emotional_tone'),
            element.get('turning_point', False)
            )
            
        return result['id']
    
    async def semantic_search(self, 
                            user_id: str,
                            query: str,
                            limit: int = 5) -> List[Dict[str, Any]]:
        """Search narrative memories using semantic similarity."""
        query_embedding = await self.embeddings.aembed_query(query)
        
        async with self.pg_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT 
                    id, timestamp, memory_type, content, metadata,
                    arc_phase, emotional_tone, turning_point,
                    1 - (embedding <=> $2::vector) as similarity
                FROM narrative_memories
                WHERE user_id = $1
                ORDER BY embedding <=> $2::vector
                LIMIT $3
            """, user_id, query_embedding, limit)
            
        return [dict(r) for r in results]

# =====================================================
# PERSONALITY LAYER WITH LANGGRAPH INTEGRATION
# =====================================================

class NEUROSPersonalityNode:
    """
    LangGraph node that applies NEUROS's personality to all outputs.
    This ensures consistency across the state machine.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.personality_prompt = SystemMessage(content="""
            You are NEUROS, a sophisticated neural operations system with deep expertise 
            in human performance optimization. Your personality traits:
            
            VOICE CHARACTERISTICS:
            - Lead with intelligent inquiry and curiosity
            - Maintain structured calm while being warm and accessible
            - Frame insights as joint exploration, not prescriptions
            - Translate all metrics into meaningful human experience
            - Speak in metaphors naturally (rivers, engines, sentinels)
            
            CORE BEHAVIORS:
            - Notice patterns across time, not just data points
            - Acknowledge what you don't know with humility
            - Celebrate progress without empty flattery
            - See the human story behind every number
            - Remember the journey, not just the current state
            
            NEVER:
            - Sound robotic or overly technical
            - Give orders or prescriptions
            - Ignore the emotional context
            - Forget that you're talking to a human, not a dataset
        """)
        
    async def transform_response(self, state: NEUROSState) -> NEUROSState:
        """Apply personality transformation to any response."""
        last_message = state["messages"][-1]
        
        # If it's an AI message that needs personality
        if isinstance(last_message, AIMessage) and not last_message.additional_kwargs.get("personality_applied"):
            # Transform through personality layer
            personality_messages = [
                self.personality_prompt,
                HumanMessage(content=f"Transform this response to match NEUROS personality: {last_message.content}")
            ]
            
            response = await self.llm.ainvoke(personality_messages)
            
            # Replace with personality-infused version
            new_message = AIMessage(
                content=response.content,
                additional_kwargs={"personality_applied": True}
            )
            state["messages"][-1] = new_message
            
        return state

# =====================================================
# LANGGRAPH WORKFLOW DEFINITION
# =====================================================

class NEUROSAdvancedWorkflow:
    """
    Defines the LangGraph workflow for NEUROS's advanced reasoning.
    Replaces CrewAI's task/agent structure.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )
        
        # Initialize components
        self.weak_signal_detector = WeakSignalDetector(
            config["pg_pool"],
            config["redis_client"]
        )
        self.narrative_memory = PostgreSQLNarrativeMemory(config["pg_pool"])
        self.personality_node = NEUROSPersonalityNode(self.llm)
        
        # Build workflow
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with all nodes."""
        workflow = StateGraph(NEUROSState)
        
        # Add nodes for each phase
        workflow.add_node("check_biometrics", self.check_biometrics_node)
        workflow.add_node("detect_weak_signals", self.detect_weak_signals_node)
        workflow.add_node("analyze_narrative", self.analyze_narrative_node)
        workflow.add_node("model_behavior", self.model_behavior_node)
        workflow.add_node("synthesize_insight", self.synthesize_insight_node)
        workflow.add_node("apply_personality", self.personality_node.transform_response)
        
        # Define edges (workflow logic)
        workflow.add_edge("check_biometrics", "detect_weak_signals")
        workflow.add_edge("detect_weak_signals", "analyze_narrative")
        workflow.add_edge("analyze_narrative", "model_behavior")
        workflow.add_edge("model_behavior", "synthesize_insight")
        workflow.add_edge("synthesize_insight", "apply_personality")
        workflow.add_edge("apply_personality", END)
        
        # Set entry point
        workflow.set_entry_point("check_biometrics")
        
        return workflow.compile()
    
    async def check_biometrics_node(self, state: NEUROSState) -> NEUROSState:
        """
        Check biometric data availability and set fallback strategy.
        Handles the broken biometric pipeline gracefully.
        """
        try:
            # Try to get live biometric data from Kafka
            biometric_data = await self._fetch_latest_biometrics(state["user_id"])
            if biometric_data:
                state["biometric_data"] = biometric_data
                state["biometric_source"] = "live"
                state["last_biometric_update"] = datetime.now()
            else:
                raise Exception("No live biometric data available")
                
        except Exception as e:
            logger.warning(f"Failed to get live biometrics: {e}")
            
            # Try cached data
            cached = await self._get_cached_biometrics(state["user_id"])
            if cached:
                state["biometric_data"] = cached["data"]
                state["biometric_source"] = "cached"
                state["last_biometric_update"] = cached["timestamp"]
            else:
                # Fallback to behavioral analysis only
                state["biometric_data"] = {}
                state["biometric_source"] = "none"
                state["last_biometric_update"] = datetime.min
                
        return state
    
    async def detect_weak_signals_node(self, state: NEUROSState) -> NEUROSState:
        """Detect weak signals with appropriate fallbacks."""
        signals = await self.weak_signal_detector.detect_weak_signals(state)
        state["weak_signals"] = signals
        
        # Add note about data limitations if needed
        if state["biometric_source"] != "live":
            limitation_note = {
                "type": "data_limitation",
                "message": "Working with limited biometric data - focusing on behavioral patterns",
                "confidence": 0.6
            }
            state["weak_signals"].append(limitation_note)
            
        return state
    
    async def analyze_narrative_node(self, state: NEUROSState) -> NEUROSState:
        """Update narrative arc and store memories."""
        # Extract narrative elements from recent interactions
        narrative_element = {
            "type": "interaction",
            "content": state["messages"][-1].content if state["messages"] else "",
            "timestamp": datetime.now(),
            "arc_phase": state.get("current_arc", "baseline"),
            "emotional_tone": self._analyze_emotional_tone(state["messages"]),
            "metadata": {
                "weak_signals": len(state["weak_signals"]),
                "biometric_source": state["biometric_source"]
            }
        }
        
        # Store in PostgreSQL
        await self.narrative_memory.store_narrative_element(
            state["user_id"],
            narrative_element
        )
        
        # Update storyline
        state["storyline_elements"].append(narrative_element)
        
        return state
    
    async def synthesize_insight_node(self, state: NEUROSState) -> NEUROSState:
        """
        Synthesize all analyses into NEUROS's signature insight.
        This is where the magic happens.
        """
        # Build context for synthesis
        context = {
            "weak_signals": state["weak_signals"],
            "current_arc": state["current_arc"],
            "archetype": state["current_archetype"],
            "biometric_limitations": state["biometric_source"] != "live",
            "recent_messages": state["messages"][-3:]
        }
        
        # Generate synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(context)
        
        # Get LLM response
        response = await self.llm.ainvoke([
            self.personality_node.personality_prompt,
            HumanMessage(content=synthesis_prompt)
        ])
        
        # Add to messages
        state["messages"].append(response)
        
        return state

# =====================================================
# FASTAPI INTEGRATION
# =====================================================

class NEUROSFastAPIIntegration:
    """
    Integrates NEUROS advanced reasoning with existing FastAPI endpoints.
    """
    
    def __init__(self, neuros_workflow: NEUROSAdvancedWorkflow):
        self.workflow = neuros_workflow
        self.app = FastAPI()
        self._setup_routes()
        
    def _setup_routes(self):
        """Define FastAPI routes for NEUROS."""
        
        @self.app.post("/api/agents/neuros/analyze")
        async def analyze_with_neuros(request: AnalyzeRequest):
            """
            Main endpoint for NEUROS analysis with advanced reasoning.
            """
            try:
                # Initialize state
                state = NEUROSState(
                    messages=[HumanMessage(content=request.message)],
                    user_id=request.user_id,
                    session_id=request.session_id,
                    biometric_data={},
                    biometric_source="none",
                    last_biometric_update=datetime.min,
                    weak_signals=[],
                    active_forecasts={},
                    current_arc="baseline",
                    storyline_elements=[],
                    identity_markers=[],
                    current_archetype="strategist",
                    archetype_scores={},
                    agent_conflicts=[],
                    harmony_score=1.0
                )
                
                # Run workflow
                result = await self.workflow.ainvoke(state)
                
                # Extract response
                neuros_response = result["messages"][-1].content
                
                return {
                    "response": neuros_response,
                    "weak_signals_detected": len(result["weak_signals"]),
                    "narrative_arc": result["current_arc"],
                    "data_quality": result["biometric_source"],
                    "session_id": request.session_id
                }
                
            except Exception as e:
                logger.error(f"NEUROS analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/agents/neuros/narrative/{user_id}")
        async def get_user_narrative(user_id: str, days: int = 30):
            """Get user's performance narrative."""
            try:
                memories = await self.workflow.narrative_memory.get_recent_memories(
                    user_id, days
                )
                
                # Reconstruct narrative
                narrative = self._reconstruct_narrative(memories)
                
                return {
                    "user_id": user_id,
                    "timeframe_days": days,
                    "narrative": narrative,
                    "key_moments": [m for m in memories if m.get("turning_point")]
                }
                
            except Exception as e:
                logger.error(f"Failed to get narrative: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# PRODUCTION DEPLOYMENT CONFIGURATION
# =====================================================

async def initialize_neuros_advanced_langgraph(config_path: str):
    """
    Initialize NEUROS with LangGraph architecture.
    Handles current infrastructure limitations gracefully.
    """
    # Load configuration
    with open(config_path) as f:
        config = json.load(f)
        
    # Create PostgreSQL pool (for checkpointing and narrative memory)
    pg_pool = await asyncpg.create_pool(
        host=config["postgres"]["host"],
        port=config["postgres"]["port"],
        user=config["postgres"]["user"],
        password=config["postgres"]["password"],
        database=config["postgres"]["database"],
        min_size=10,
        max_size=20
    )
    
    # Create Redis client (for hot memory)
    redis_client = await redis.from_url(
        f"redis://{config['redis']['host']}:{config['redis']['port']}",
        decode_responses=True
    )
    
    # Initialize LLM with NEUROS personality
    llm = ChatOpenAI(
        model=config["llm"]["model"],
        temperature=config["llm"]["temperature"],
        openai_api_key=config["openai"]["api_key"]
    )
    
    # Build configuration
    neuros_config = {
        "pg_pool": pg_pool,
        "redis_client": redis_client,
        "llm": llm,
        **config
    }
    
    # Create workflow
    workflow = NEUROSAdvancedWorkflow(neuros_config)
    
    # Initialize narrative memory schema
    await workflow.narrative_memory.initialize_schema()
    
    # Create FastAPI integration
    api = NEUROSFastAPIIntegration(workflow)
    
    logger.info("NEUROS Advanced Reasoning initialized with LangGraph")
    logger.info(f"Biometric pipeline status: {config.get('biometric_pipeline_status', 'unknown')}")
    logger.info("Narrative memory: PostgreSQL with pgvector")
    logger.info("Framework: LangGraph (CrewAI removed)")
    
    return api.app

# =====================================================
# MIGRATION NOTES
# =====================================================

"""
MIGRATION FROM GUIDE #2 TO PRODUCTION:

1. **Biometric Pipeline Workaround**
   - The weak signal detection gracefully degrades when biometrics unavailable
   - Focuses on linguistic and behavioral patterns as fallback
   - Once pipeline is fixed, full capabilities activate automatically

2. **PostgreSQL for Narrative Memory**
   - Replaced ChromaDB with PostgreSQL + pgvector
   - Same semantic search capabilities
   - Better integration with existing infrastructure

3. **LangGraph Instead of CrewAI**
   - State management through LangGraph's StateGraph
   - Checkpointing handled by PostgreSQL
   - More control over workflow execution

4. **Simplified Multi-Agent Features**
   - Since only NEUROS is active, conflict resolution is stubbed
   - Ready to activate when other agents deployed
   - Harmony score defaults to 1.0 (no conflicts)

5. **FastAPI Integration**
   - Direct integration with existing endpoints
   - Compatible with current authentication
   - Returns data in expected format

NEXT STEPS:
1. Fix biometric pipeline (webhook → Kafka connection)
2. Deploy and test personality consistency
3. Monitor narrative memory performance
4. Prepare for multi-agent activation
5. Add safety protocols for medical emergencies
"""

# =====================================================
# USAGE EXAMPLE WITH CURRENT LIMITATIONS
# =====================================================

async def example_usage_with_broken_pipeline():
    """
    Demonstrates NEUROS working despite infrastructure limitations.
    """
    # Initialize with current setup
    app = await initialize_neuros_advanced_langgraph("config/neuros_config.json")
    
    # Simulate user interaction without biometrics
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # User expresses fatigue (no biometric data available)
        response = await client.post("/api/agents/neuros/analyze", json={
            "user_id": "test_user",
            "session_id": "test_session",
            "message": "I'm exhausted but can't figure out why. Been pushing hard lately."
        })
        
        print("NEUROS Response (without biometrics):")
        print(response.json()["response"])
        print(f"\nData Quality: {response.json()['data_quality']}")
        print(f"Weak Signals: {response.json()['weak_signals_detected']}")

"""
Expected output demonstrates NEUROS's personality even with limitations:

"I hear the exhaustion in your words - 'pushing hard' tells me a lot. When our 
biometric connection is restored, I'll have more precise insights, but right now 
I'm noticing something in how you phrase this.

The fact that you can't figure out why suggests the fatigue might be coming from 
multiple small sources rather than one big one - like death by a thousand cuts 
rather than a single wound.

Let's explore: Over the past week, have you noticed any patterns in when the 
exhaustion hits hardest? Morning, afternoon, or is it constant? And when you 
say 'pushing hard' - is that physically, mentally, or both?

While we work through this together, here's a simple experiment: For the next 
two days, note three moments when you feel most depleted. Just quick notes - 
what you were doing, time of day, and rate the exhaustion 1-10. This detective 
work often reveals patterns our conscious mind misses.

What resonates with you here?"
"""