# =============================================================================
# SECTION 12: MAIN EXECUTION - LANGGRAPH PRODUCTION RUNTIME
# =============================================================================
# Purpose: Production-ready runtime using LangGraph patterns
# Last Updated: 2025-01-29
# =============================================================================

import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, TypedDict, Annotated, Literal, List
from datetime import datetime, timedelta
from operator import add

import asyncpg
import redis.asyncio as aioredis
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from tenacity import retry, stop_after_attempt, wait_exponential

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.constants import Send
from langchain_openai import ChatOpenAI

# Import our components
from security import create_security_app
from config.langgraph_config import get_langgraph_runtime, compile_with_tracing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# LANGGRAPH STATE DEFINITIONS
# =============================================================================

class BiometricEventState(TypedDict):
    """State for processing individual biometric events"""
    user_id: str
    event_id: str
    device_type: str
    timestamp: datetime
    raw_data: dict
    processed_data: dict
    analysis_results: Annotated[dict, lambda a, b: {**a, **b}]  # Merge dicts
    insights: Annotated[List[str], add]  # Merge lists
    confidence_scores: Annotated[List[float], add]
    mode_recommendation: Optional[str]
    memory_updates: Annotated[List[dict], add]

class AURENSystemState(TypedDict):
    """Global system state with memory tiers"""
    # User context
    user_id: str
    session_id: str
    
    # Biometric tracking
    recent_events: Annotated[List[dict], add]
    current_mode: str
    mode_history: Annotated[List[dict], add]
    
    # Analysis results  
    hypotheses: Annotated[dict, lambda a, b: {**a, **b}]
    patterns_detected: Annotated[List[dict], add]
    alerts: Annotated[List[dict], add]
    
    # Memory tiers
    hot_memory: dict  # Redis - last 30 days
    warm_memory: dict  # PostgreSQL - 30 days to 1 year
    cold_memory: dict  # ChromaDB - > 1 year
    
    # Processing metadata
    loop_count: int
    max_loops: int
    processing_errors: Annotated[List[str], add]

# =============================================================================
# GLOBAL STATE MANAGEMENT
# =============================================================================

class AppState:
    """Centralized state management for graceful shutdown"""
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.checkpointer: Optional[PostgresSaver] = None
        self.store: Optional[PostgresStore] = None
        self.biometric_graph: Optional[StateGraph] = None
        self.system_graph: Optional[StateGraph] = None
        self.llm: Optional[ChatOpenAI] = None
        self.shutdown_event = asyncio.Event()
        
app_state = AppState()

# =============================================================================
# LANGGRAPH NODE IMPLEMENTATIONS
# =============================================================================

async def route_biometric_event(state: BiometricEventState) -> Literal["oura", "whoop", "apple_health", "manual"]:
    """Route event to device-specific processor"""
    device_type = state.get("device_type", "manual").lower()
    if device_type in ["oura", "whoop", "apple_health"]:
        return device_type
    return "manual"

async def process_oura_event(state: BiometricEventState) -> dict:
    """Process Oura ring data"""
    logger.info(f"Processing Oura event for user {state['user_id']}")
    
    # Extract Oura-specific metrics
    raw_data = state["raw_data"]
    processed = {
        "hrv_rmssd": raw_data.get("hrv_rmssd", 0),
        "readiness_score": raw_data.get("readiness_score", 0),
        "sleep_score": raw_data.get("sleep_score", 0),
        "activity_score": raw_data.get("activity_score", 0),
        "temperature_deviation": raw_data.get("temperature_deviation", 0)
    }
    
    # Generate insights based on thresholds
    insights = []
    if processed["hrv_rmssd"] < 30:
        insights.append("Low HRV detected - consider rest day")
    if processed["readiness_score"] < 70:
        insights.append("Below optimal readiness - monitor stress levels")
        
    return {
        "processed_data": processed,
        "insights": insights,
        "confidence_scores": [0.9]  # High confidence for direct device data
    }

async def process_whoop_event(state: BiometricEventState) -> dict:
    """Process WHOOP strap data"""
    logger.info(f"Processing WHOOP event for user {state['user_id']}")
    
    raw_data = state["raw_data"]
    processed = {
        "recovery_score": raw_data.get("recovery_score", 0),
        "strain_score": raw_data.get("strain_score", 0),
        "sleep_performance": raw_data.get("sleep_performance", 0),
        "hrv": raw_data.get("hrv", 0)
    }
    
    insights = []
    if processed["strain_score"] > 18:
        insights.append("High strain detected - ensure adequate recovery")
        
    return {
        "processed_data": processed,
        "insights": insights,
        "confidence_scores": [0.9]
    }

async def process_apple_health_event(state: BiometricEventState) -> dict:
    """Process Apple Health data"""
    logger.info(f"Processing Apple Health event for user {state['user_id']}")
    
    raw_data = state["raw_data"]
    processed = {
        "heart_rate": raw_data.get("heart_rate", 0),
        "steps": raw_data.get("steps", 0),
        "active_energy": raw_data.get("active_energy", 0),
        "stand_hours": raw_data.get("stand_hours", 0)
    }
    
    return {
        "processed_data": processed,
        "insights": ["Apple Health data processed"],
        "confidence_scores": [0.85]
    }

async def process_manual_event(state: BiometricEventState) -> dict:
    """Process manually entered data"""
    logger.info(f"Processing manual event for user {state['user_id']}")
    
    return {
        "processed_data": state["raw_data"],
        "insights": ["Manual entry recorded"],
        "confidence_scores": [0.7]  # Lower confidence for manual data
    }

async def unified_analysis(state: BiometricEventState) -> dict:
    """Unified analysis across all biometric data"""
    logger.info(f"Running unified analysis for user {state['user_id']}")
    
    # Combine all processed data
    all_metrics = {**state.get("processed_data", {}), **state.get("analysis_results", {})}
    
    # Pattern detection
    patterns = []
    if all_metrics.get("hrv_rmssd", 100) < 30 and all_metrics.get("readiness_score", 100) < 70:
        patterns.append({
            "type": "stress_overload",
            "confidence": 0.85,
            "recommendation": "Consider stress reduction techniques"
        })
    
    # Mode recommendation based on biometric state
    mode = "baseline"  # Default
    if patterns:
        if any(p["type"] == "stress_overload" for p in patterns):
            mode = "reflex"  # Quick intervention needed
    
    # Memory updates
    memory_updates = [
        {
            "tier": "hot",
            "key": f"event_{state['event_id']}",
            "value": all_metrics,
            "ttl": 86400 * 30  # 30 days
        }
    ]
    
    return {
        "analysis_results": {"patterns": patterns},
        "mode_recommendation": mode,
        "memory_updates": memory_updates
    }

async def update_memory_tiers(state: BiometricEventState) -> dict:
    """Update memory tiers based on analysis"""
    logger.info(f"Updating memory tiers for user {state['user_id']}")
    
    # Process memory updates
    for update in state.get("memory_updates", []):
        tier = update["tier"]
        key = update["key"]
        value = update["value"]
        
        if tier == "hot" and app_state.redis_client:
            # Update Redis (hot tier)
            await app_state.redis_client.setex(
                f"{state['user_id']}:{key}",
                update.get("ttl", 86400 * 30),
                json.dumps(value)
            )
    
    return {}

# =============================================================================
# LANGGRAPH BUILDERS
# =============================================================================

def build_biometric_graph() -> StateGraph:
    """Build the biometric event processing graph"""
    builder = StateGraph(BiometricEventState)
    
    # Add nodes
    builder.add_node("router", route_biometric_event)
    builder.add_node("oura", process_oura_event)
    builder.add_node("whoop", process_whoop_event)
    builder.add_node("apple_health", process_apple_health_event)
    builder.add_node("manual", process_manual_event)
    builder.add_node("analyze", unified_analysis)
    builder.add_node("update_memory", update_memory_tiers)
    
    # Set entry point
    builder.set_entry_point("router")
    
    # Add conditional routing
    builder.add_conditional_edges(
        "router",
        route_biometric_event,
        {
            "oura": "oura",
            "whoop": "whoop",
            "apple_health": "apple_health",
            "manual": "manual"
        }
    )
    
    # All processors lead to analysis
    for processor in ["oura", "whoop", "apple_health", "manual"]:
        builder.add_edge(processor, "analyze")
    
    # Analysis leads to memory update
    builder.add_edge("analyze", "update_memory")
    builder.add_edge("update_memory", END)
    
    return builder

# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle with proper startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting AUREN LangGraph Runtime (Section 12)...")
    
    try:
        # Initialize connections with retry
        app_state.postgres_pool = await create_postgres_pool()
        app_state.redis_client = await create_redis_client()
        
        # Initialize LangGraph checkpointing
        postgres_url = os.getenv("POSTGRES_URL")
        app_state.checkpointer = PostgresSaver.from_conn_string(postgres_url)
        app_state.store = PostgresStore.from_conn_string(postgres_url)
        
        # Initialize LLM
        app_state.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            streaming=True
        )
        
        # Build graphs
        biometric_builder = build_biometric_graph()
        app_state.biometric_graph = biometric_builder.compile(
            checkpointer=app_state.checkpointer,
            store=app_state.store
        )
        
        logger.info("✅ All systems initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Initiating graceful shutdown...")
    
    # Signal shutdown to all components
    app_state.shutdown_event.set()
    
    # Close connections in order
    if app_state.redis_client:
        await app_state.redis_client.close()
    
    if app_state.postgres_pool:
        await app_state.postgres_pool.close()
    
    logger.info("✅ Graceful shutdown complete")

# =============================================================================
# CONNECTION FACTORIES WITH RETRY
# =============================================================================

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True
)
async def create_postgres_pool() -> asyncpg.Pool:
    """Create PostgreSQL connection pool with retry logic"""
    logger.info("Connecting to PostgreSQL...")
    
    pool = await asyncpg.create_pool(
        os.getenv("POSTGRES_URL"),
        min_size=5,
        max_size=20,
        command_timeout=60
    )
    
    # Test connection
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        logger.info(f"Connected to PostgreSQL: {version}")
    
    return pool

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    reraise=True
)
async def create_redis_client() -> aioredis.Redis:
    """Create Redis client with retry logic"""
    logger.info("Connecting to Redis...")
    
    client = await aioredis.from_url(
        os.getenv("REDIS_URL"),
        encoding="utf-8",
        decode_responses=True,
        health_check_interval=30
    )
    
    # Test connection
    await client.ping()
    logger.info("Connected to Redis")
    
    return client

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Create base app
app = FastAPI(
    title="AUREN LangGraph Runtime",
    description="Production runtime using LangGraph patterns",
    version="12.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Integrate Section 9 security (if enabled)
if os.getenv("ENABLE_SECURITY", "true").lower() == "true":
    app = create_security_app(app, app_state.redis_client)

# =============================================================================
# HEALTH & MONITORING ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "12.0.0",
        "runtime": "langgraph",
        "components": {}
    }
    
    # Check PostgreSQL
    try:
        if app_state.postgres_pool:
            async with app_state.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health_status["components"]["postgres"] = "healthy"
        else:
            health_status["components"]["postgres"] = "not_initialized"
    except Exception as e:
        health_status["components"]["postgres"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        if app_state.redis_client:
            await app_state.redis_client.ping()
            health_status["components"]["redis"] = "healthy"
        else:
            health_status["components"]["redis"] = "not_initialized"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LangGraph
    health_status["components"]["langgraph"] = "healthy" if app_state.biometric_graph else "not_initialized"
    health_status["components"]["checkpointer"] = "healthy" if app_state.checkpointer else "not_initialized"
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_data = []
    
    # Add basic metrics
    if app_state.postgres_pool:
        pool_size = app_state.postgres_pool.get_size()
        pool_free = app_state.postgres_pool.get_idle_size()
        metrics_data.append(f'postgres_pool_size {{}} {pool_size}')
        metrics_data.append(f'postgres_pool_free {{}} {pool_free}')
    
    # LangGraph metrics
    metrics_data.append('auren_langgraph_ready {runtime="production"} 1')
    
    return JSONResponse(
        content="\n".join(metrics_data),
        media_type="text/plain"
    )

@app.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe"""
    ready = all([
        app_state.postgres_pool is not None,
        app_state.redis_client is not None,
        app_state.biometric_graph is not None,
        app_state.checkpointer is not None
    ])
    
    if ready:
        return {"status": "ready", "runtime": "langgraph"}
    else:
        raise HTTPException(status_code=503, detail="Not ready")

# =============================================================================
# BIOMETRIC EVENT ENDPOINTS
# =============================================================================

@app.post("/webhooks/{device_type}")
async def webhook_handler(device_type: str, request: Request):
    """
    Process biometric webhooks through LangGraph
    """
    try:
        data = await request.json()
        
        # Create event state
        event_state = {
            "user_id": data.get("user_id", "unknown"),
            "event_id": data.get("event_id", str(datetime.now().timestamp())),
            "device_type": device_type,
            "timestamp": datetime.now(),
            "raw_data": data,
            "processed_data": {},
            "analysis_results": {},
            "insights": [],
            "confidence_scores": [],
            "memory_updates": []
        }
        
        # Process through LangGraph
        config = {
            "configurable": {
                "thread_id": f"{event_state['user_id']}_{event_state['event_id']}"
            }
        }
        
        result = await app_state.biometric_graph.ainvoke(event_state, config)
        
        logger.info(f"Processed {device_type} webhook for user {result['user_id']}")
        
        return {
            "status": "processed",
            "event_id": result["event_id"],
            "insights": result.get("insights", []),
            "mode_recommendation": result.get("mode_recommendation", "baseline")
        }
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/analyze/{user_id}")
async def analyze_user_state(user_id: str, request: Request):
    """
    Run comprehensive analysis for a user using LangGraph streaming
    """
    try:
        data = await request.json()
        
        # Create analysis state
        state = {
            "user_id": user_id,
            "event_id": f"analysis_{datetime.now().timestamp()}",
            "device_type": "manual",
            "timestamp": datetime.now(),
            "raw_data": data,
            "processed_data": {},
            "analysis_results": {},
            "insights": [],
            "confidence_scores": [],
            "memory_updates": []
        }
        
        config = {
            "configurable": {
                "thread_id": f"{user_id}_analysis"
            }
        }
        
        # Stream results
        async def stream_analysis():
            async for chunk in app_state.biometric_graph.astream(state, config):
                # Stream insights as they're generated
                if "analyze" in chunk and "insights" in chunk["analyze"]:
                    for insight in chunk["analyze"]["insights"]:
                        yield f"data: {json.dumps({'insight': insight})}\n\n"
                        
        return StreamingResponse(
            stream_analysis(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# API INFO
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "service": "AUREN LangGraph Runtime",
        "version": "12.0.0",
        "status": "operational",
        "runtime": "langgraph-production",
        "features": [
            "Biometric event processing with device routing",
            "Memory tier management (hot/warm/cold)",
            "LangGraph checkpointing with PostgreSQL",
            "Streaming analysis results",
            "Production-grade error handling"
        ],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "readiness": "/readiness",
            "webhooks": "/webhooks/{device_type}",
            "analyze": "/analyze/{user_id}",
            "docs": "/docs"
        }
    }

# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

def handle_signal(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}")
    app_state.shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """
    Main execution function
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        required_vars = [
            "REDIS_URL",
            "POSTGRES_URL",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.info("Please check your .env file or environment configuration")
            sys.exit(1)
        
        # Run as FastAPI server
        logger.info("Starting AUREN LangGraph production runtime...")
        
        config = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=int(os.getenv("API_PORT", "8000")),
            log_level="info",
            access_log=True,
            loop="uvloop"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())