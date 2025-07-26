"""
FastAPI Dashboard API for AUREN's real-time health intelligence dashboard.
Enhanced with Kafka integration and stunning visual support.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, WebSocket, HTTPException, Query, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aioredis
from aiokafka import AIOKafkaProducer

# Import the visualizers you built
from auren.realtime.dashboard_backends import (
    ReasoningChainVisualizer,
    CostAnalyticsDashboard,
    LearningSystemVisualizer
)

# Import memory system
from auren.core.memory.unified_memory_system import UnifiedMemorySystem
from auren.config.production_settings import settings
from auren.core.anomaly.htm_detector import HTMAnomalyDetector, HTMConfig
import asyncpg

# Initialize logger
logger = logging.getLogger(__name__)

# Global instances
redis_client: Optional[aioredis.Redis] = None
kafka_producer: Optional[AIOKafkaProducer] = None
active_connections: List[WebSocket] = []
memory_system: Optional[UnifiedMemorySystem] = None
db_pool: Optional[asyncpg.Pool] = None
anomaly_detector: Optional[HTMAnomalyDetector] = None

# Environment configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown"""
    global redis_client, kafka_producer, memory_system, db_pool, anomaly_detector
    
    logger.info("Dashboard API starting up...")
    
    # Initialize Redis
    try:
        redis_client = await aioredis.from_url(REDIS_URL)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    # Initialize Kafka if enabled
    if KAFKA_ENABLED:
        try:
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode()
            )
            await kafka_producer.start()
            logger.info("Kafka producer initialized")
        except Exception as e:
            logger.warning(f"Kafka initialization failed: {e}")
    
    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=5,
        max_size=20,
        timeout=30.0,
        command_timeout=10.0
    )
    
    # Initialize memory system
    memory_system = UnifiedMemorySystem(
        redis_url=settings.redis_url,
        postgresql_pool=db_pool,
        chromadb_host=settings.chromadb_host,
        chromadb_port=settings.chromadb_port
    )
    await memory_system.initialize()
    
    # Initialize HTM anomaly detector if enabled
    if settings.enable_htm_anomaly_detection:
        htm_config = HTMConfig(
            column_dimensions=settings.htm_columns,
            cells_per_column=settings.htm_cells_per_column,
            activation_threshold=settings.htm_activation_threshold
        )
        anomaly_detector = HTMAnomalyDetector(
            redis_url=REDIS_URL,
            config=htm_config
        )
        await anomaly_detector.initialize()
        logger.info("HTM Anomaly Detector initialized")
    
    # Initialize visualizers
    # visualizers["reasoning"] = ReasoningChainVisualizer(redis_url=REDIS_URL) # This line is removed as per new_code
    # visualizers["cost"] = CostAnalyticsDashboard(redis_url=REDIS_URL) # This line is removed as per new_code
    # visualizers["learning"] = LearningSystemVisualizer( # This line is removed as per new_code
    #     redis_url=REDIS_URL,
    #     memory_backend=None,  # Will be set when available
    #     hypothesis_validator=None  # Will be set when available
    # )
    
    # Initialize connections
    # for viz in visualizers.values(): # This line is removed as per new_code
    #     await viz.initialize() # This line is removed as per new_code
    
    logger.info("Dashboard API initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Dashboard API shutting down...")
    # for viz in visualizers.values(): # This line is removed as per new_code
    #     if hasattr(viz, 'cleanup'): # This line is removed as per new_code
    #         await viz.cleanup() # This line is removed as per new_code
    if redis_client:
        await redis_client.close()
    if kafka_producer:
        await kafka_producer.stop()
    if memory_system:
        await memory_system.cleanup()
    if db_pool:
        await db_pool.close()
    if anomaly_detector:
        await anomaly_detector.cleanup()

# Create FastAPI app
app = FastAPI(
    title="AUREN Dashboard API",
    version="2.0.0",
    description="Real-time API for AUREN health intelligence dashboard with stunning visuals",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check for all systems"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {}
    }
    
    # Check Redis connectivity
    try:
        redis_client = aioredis.from_url(REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check PostgreSQL connectivity
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["components"]["postgres"] = "healthy"
    except Exception as e:
        health_status["components"]["postgres"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check ChromaDB connectivity
    try:
        if memory_system and memory_system.chromadb_tier:
            stats = await memory_system.chromadb_tier.get_memory_stats()
            health_status["components"]["chromadb"] = "healthy"
    except Exception as e:
        health_status["components"]["chromadb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check visualizer health
    # for name, viz in visualizers.items(): # This line is removed as per new_code
    #     try: # This line is removed as per new_code
    #         # Simple check - can we access the visualizer? # This line is removed as per new_code
    #         health_status["components"][f"{name}_visualizer"] = "healthy" # This line is removed as per new_code
    #     except Exception as e: # This line is removed as per new_code
    #         health_status["components"][f"{name}_visualizer"] = f"unhealthy: {str(e)}" # This line is removed as per new_code
    #         health_status["status"] = "degraded" # This line is removed as per new_code
    
    # Add connection count
    health_status["active_websocket_connections"] = len(active_connections)
    
    return health_status

# REST Endpoints for Dashboard Data
@app.get("/api/reasoning-chain/{session_id}")
async def get_reasoning_chain(session_id: str, limit: int = 50):
    """Get the reasoning chain for a specific session"""
    try:
        # if "reasoning" not in visualizers: # This line is removed as per new_code
        #     raise HTTPException(status_code=503, detail="Reasoning visualizer not initialized") # This line is removed as per new_code
        
        # chain_data = await visualizers["reasoning"].get_reasoning_chain(session_id) # This line is removed as per new_code
        
        # return { # This line is removed as per new_code
        #     "success": True, # This line is removed as per new_code
        #     "session_id": session_id, # This line is removed as per new_code
        #     "chain": chain_data, # This line is removed as per new_code
        #     "timestamp": datetime.now(timezone.utc).isoformat() # This line is removed as per new_code
        # } # This line is removed as per new_code
        raise HTTPException(status_code=503, detail="Reasoning visualizer not initialized")
    except Exception as e:
        logger.error(f"Error getting reasoning chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cost-analytics")
async def get_cost_analytics(period: str = "today"):
    """Get cost analytics"""
    try:
        # if "cost" not in visualizers: # This line is removed as per new_code
        #     raise HTTPException(status_code=503, detail="Cost visualizer not initialized") # This line is removed as per new_code
        
        # # Validate period parameter # This line is removed as per new_code
        # valid_periods = ["today", "week", "month", "all"] # This line is removed as per new_code
        # if period not in valid_periods: # This line is removed as per new_code
        #     period = "today" # This line is removed as per new_code
        
        # metrics = await visualizers["cost"].get_cost_metrics() # This line is removed as per new_code
        
        # return { # This line is removed as per new_code
        #     "success": True, # This line is removed as per new_code
        #     "period": period, # This line is removed as per new_code
        #     "metrics": metrics, # This line is removed as per new_code
        #     "timestamp": datetime.now(timezone.utc).isoformat() # This line is removed as per new_code
        # } # This line is removed as per new_code
        raise HTTPException(status_code=503, detail="Cost visualizer not initialized")
    except Exception as e:
        logger.error(f"Error getting cost analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning-progress")
async def get_learning_progress():
    """Get learning system progress"""
    try:
        # if "learning" not in visualizers: # This line is removed as per new_code
        #     raise HTTPException(status_code=503, detail="Learning visualizer not initialized") # This line is removed as per new_code
        
        # progress = await visualizers["learning"].get_learning_metrics() # This line is removed as per new_code
        
        # return { # This line is removed as per new_code
        #     "success": True, # This line is removed as per new_code
        #     "progress": progress, # This line is removed as per new_code
        #     "timestamp": datetime.now(timezone.utc).isoformat() # This line is removed as per new_code
        # } # This line is removed as per new_code
        raise HTTPException(status_code=503, detail="Learning visualizer not initialized")
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-metrics")
async def get_system_metrics():
    """Get overall system metrics across all users"""
    try:
        # Aggregate metrics across all visualizers # This line is removed as per new_code
        total_events = 0 # This line is removed as per new_code
        active_sessions = 0 # This line is removed as per new_code
        
        # Get Redis metrics # This line is removed as per new_code
        redis_client = aioredis.from_url(REDIS_URL) # This line is removed as per new_code
        
        # Count events in streams # This line is removed as per new_code
        for tier in ["critical", "operational", "analytical"]: # This line is removed as per new_code
            stream_key = f"auren:events:{tier}" # This line is removed as per new_code
            try: # This line is removed as per new_code
                count = await redis_client.xlen(stream_key) # This line is removed as per new_code
                total_events += count # This line is removed as per new_code
            except: # This line is removed as per new_code
                pass # This line is removed as per new_code
        
        await redis_client.close() # This line is removed as per new_code
        
        return { # This line is removed as per new_code
            "success": True, # This line is removed as per new_code
            "metrics": { # This line is removed as per new_code
                "total_events_processed": total_events, # This line is removed as per new_code
                "active_websocket_connections": len(active_connections), # This line is removed as per new_code
                "system_uptime_seconds": 0,  # Would track actual uptime # This line is removed as per new_code
                "health_status": "operational" # This line is removed as per new_code
            }, # This line is removed as per new_code
            "timestamp": datetime.now(timezone.utc).isoformat() # This line is removed as per new_code
        } # This line is removed as per new_code
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Memory Statistics Endpoints
@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get comprehensive memory system statistics"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not initialized")
    
    try:
        stats = await memory_system.get_system_stats()
        
        # Enrich with real-time metrics
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overview": {
                "total_memories": sum([
                    stats.get("redis", {}).get("total_memories", 0),
                    stats.get("postgres", {}).get("total_memories", 0),
                    stats.get("chromadb", {}).get("total_memories", 0)
                ]),
                "active_agents": stats.get("active_agents", 0),
                "memory_operations_per_second": stats.get("ops_per_second", 0)
            },
            "tiers": {
                "hot": {
                    "name": "Redis (Hot Tier)",
                    "memories": stats.get("redis", {}).get("total_memories", 0),
                    "memory_usage_mb": stats.get("redis", {}).get("memory_usage_mb", 0),
                    "hit_rate": stats.get("redis", {}).get("hit_rate", 0),
                    "avg_ttl_seconds": stats.get("redis", {}).get("avg_ttl", 0),
                    "operations": {
                        "reads_per_sec": stats.get("redis", {}).get("reads_per_sec", 0),
                        "writes_per_sec": stats.get("redis", {}).get("writes_per_sec", 0)
                    }
                },
                "warm": {
                    "name": "PostgreSQL (Warm Tier)",
                    "memories": stats.get("postgres", {}).get("total_memories", 0),
                    "events": stats.get("postgres", {}).get("total_events", 0),
                    "agents": stats.get("postgres", {}).get("unique_agents", 0),
                    "avg_query_time_ms": stats.get("postgres", {}).get("avg_query_time_ms", 0),
                    "operations": {
                        "queries_per_sec": stats.get("postgres", {}).get("queries_per_sec", 0),
                        "events_per_sec": stats.get("postgres", {}).get("events_per_sec", 0)
                    }
                },
                "cold": {
                    "name": "ChromaDB (Cold Tier)",
                    "memories": stats.get("chromadb", {}).get("total_memories", 0),
                    "collections": stats.get("chromadb", {}).get("collections", 0),
                    "embeddings": stats.get("chromadb", {}).get("total_embeddings", 0),
                    "storage_gb": stats.get("chromadb", {}).get("storage_gb", 0),
                    "operations": {
                        "searches_per_sec": stats.get("chromadb", {}).get("searches_per_sec", 0),
                        "avg_search_time_ms": stats.get("chromadb", {}).get("avg_search_time_ms", 0)
                    }
                }
            },
            "memory_flow": {
                "redis_to_postgres": stats.get("tier_transitions", {}).get("hot_to_warm", 0),
                "postgres_to_chromadb": stats.get("tier_transitions", {}).get("warm_to_cold", 0),
                "promotions": stats.get("tier_transitions", {}).get("promotions", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/agent/{agent_id}/stats")
async def get_agent_memory_stats(agent_id: str):
    """Get memory statistics for a specific agent"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not initialized")
    
    try:
        # Get agent-specific stats from each tier
        redis_stats = await memory_system.redis_tier.get_memory_stats(agent_id)
        postgres_stats = await memory_system.postgres_tier.get_memory_stats(agent_id)
        chromadb_stats = await memory_system.chromadb_tier.get_memory_stats(agent_id)
        
        return {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_count": {
                "hot": redis_stats.get("memory_count", 0),
                "warm": postgres_stats.get("memory_count", 0),
                "cold": chromadb_stats.get("memory_count", 0),
                "total": sum([
                    redis_stats.get("memory_count", 0),
                    postgres_stats.get("memory_count", 0),
                    chromadb_stats.get("memory_count", 0)
                ])
            },
            "memory_types": postgres_stats.get("memory_types", {}),
            "recent_activity": {
                "last_store": redis_stats.get("last_store_time"),
                "last_recall": redis_stats.get("last_recall_time"),
                "stores_last_hour": redis_stats.get("stores_last_hour", 0),
                "recalls_last_hour": redis_stats.get("recalls_last_hour", 0)
            },
            "performance": {
                "avg_recall_time_ms": postgres_stats.get("avg_recall_time_ms", 0),
                "cache_hit_rate": redis_stats.get("hit_rate", 0),
                "semantic_search_accuracy": chromadb_stats.get("avg_confidence", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching agent memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/recent")
async def get_recent_memories(limit: int = 10, agent_id: Optional[str] = None):
    """Get recent memory operations across all tiers"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not initialized")
    
    try:
        # Query recent memories from PostgreSQL (event store)
        async with db_pool.acquire() as conn:
            query = """
                SELECT 
                    e.event_id,
                    e.event_type,
                    e.payload,
                    e.metadata,
                    e.created_at,
                    am.agent_id,
                    am.memory_type,
                    am.importance
                FROM events e
                LEFT JOIN agent_memories am ON e.stream_id = am.memory_id
                WHERE e.event_type IN ('memory_stored', 'memory_retrieved', 'memory_updated')
                {}
                ORDER BY e.created_at DESC
                LIMIT $1
            """.format("AND am.agent_id = $2" if agent_id else "")
            
            if agent_id:
                rows = await conn.fetch(query, limit, agent_id)
            else:
                rows = await conn.fetch(query, limit)
        
        recent_memories = []
        for row in rows:
            recent_memories.append({
                "event_id": str(row["event_id"]),
                "event_type": row["event_type"],
                "agent_id": row["agent_id"],
                "memory_type": row["memory_type"],
                "importance": float(row["importance"]) if row["importance"] else 0,
                "timestamp": row["created_at"].isoformat(),
                "content_preview": row["payload"].get("content", "")[:100] + "..."
            })
        
        return {
            "memories": recent_memories,
            "count": len(recent_memories),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching recent memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Graph Endpoints
@app.get("/api/knowledge-graph/data")
async def get_knowledge_graph_data(
    agent_id: str = Query(..., description="Agent ID to fetch knowledge for"),
    depth: int = Query(default=1, ge=1, le=3, description="Graph depth (1=50 nodes, 2=500, 3=5000)")
):
    """
    Fetch knowledge graph data from all three memory tiers with enhanced visual properties.
    """
    try:
        nodes = []
        edges = []
        
        if memory_system:
            # Fetch from all three tiers based on depth
            if depth >= 1:
                # Hot tier (Redis)
                hot_memories = await memory_system.redis_tier.get_agent_memories(agent_id)
                for mem_id, memory in hot_memories.items():
                    nodes.append(format_as_node(memory, "hot", mem_id))
            
            if depth >= 2:
                # Warm tier (PostgreSQL)
                warm_memories = await memory_system.postgres_tier.get_memories_by_agent(agent_id, limit=500)
                for memory in warm_memories:
                    nodes.append(format_as_node(memory, "warm"))
            
            if depth >= 3:
                # Cold tier (ChromaDB)
                cold_memories = await memory_system.chromadb_tier.search(
                    query=f"agent:{agent_id}",
                    n_results=min(5000 - len(nodes), 1000)
                )
                for memory in cold_memories:
                    nodes.append(format_as_node(memory, "cold"))
            
            # Calculate connections
            edges = calculate_knowledge_connections(nodes)
        else:
            # Use mock data if memory system not available
            return await get_mock_knowledge_graph(agent_id, depth)
        
        # Send Kafka event if enabled
        if kafka_producer:
            await kafka_producer.send(
                "memory-access",
                {
                    "event": "graph_accessed",
                    "agent_id": agent_id,
                    "depth": depth,
                    "node_count": len(nodes),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_knowledge": len(nodes),
                "hot_tier_count": sum(1 for n in nodes if n["tier"] == "hot"),
                "warm_tier_count": sum(1 for n in nodes if n["tier"] == "warm"),
                "cold_tier_count": sum(1 for n in nodes if n["tier"] == "cold"),
                "user_context_count": sum(1 for n in nodes if n.get("is_user_context", False))
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching knowledge graph: {e}")
        # Fallback to mock data on error
        return await get_mock_knowledge_graph(agent_id, depth)

def format_as_node(memory: Dict[str, Any], tier: str, memory_id: Optional[str] = None) -> Dict[str, Any]:
    """Format memory as a graph node with enhanced visual properties."""
    return {
        "id": memory_id or memory.get("id", f"{tier}_{id(memory)}"),
        "content": memory.get("content", ""),
        "label": memory.get("content", "")[:30] + "..." if len(memory.get("content", "")) > 30 else memory.get("content", ""),
        "tier": tier,
        "type": memory.get("type", "KNOWLEDGE"),
        "importance": memory.get("importance", 0.5),
        "access_count": memory.get("access_count", 0),
        "is_user_context": memory.get("metadata", {}).get("is_user_context", False),
        "shape": "diamond" if memory.get("metadata", {}).get("is_user_context", False) else "circle",
        "glow": memory.get("metadata", {}).get("is_breakthrough", False),
        "timestamp": memory.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "confidence": memory.get("confidence", 0.8),
        "source": memory.get("source", "unknown")
    }

def calculate_knowledge_connections(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate semantic connections between knowledge nodes."""
    edges = []
    
    # Simple connection logic - connect nodes with similar content
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes[i+1:], i+1):
            # Calculate similarity (simplified)
            similarity = calculate_semantic_similarity(node1["content"], node2["content"])
            
            if similarity > 0.7:
                edges.append({
                    "source": node1["id"],
                    "target": node2["id"],
                    "strength": similarity,
                    "type": "semantic",
                    "glow": similarity > 0.9  # Strong connections glow
                })
    
    return edges

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """Simple semantic similarity calculation."""
    # Simplified - in production would use embeddings
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

async def get_mock_knowledge_graph(agent_id: str, depth: int) -> Dict[str, Any]:
    """Generate mock knowledge graph data for testing."""
    nodes = []
    node_count = 50 if depth == 1 else 500 if depth == 2 else 5000
    
    for i in range(min(node_count, 100)):  # Limit for performance
        tier = "hot" if i < 20 else "warm" if i < 60 else "cold"
        nodes.append({
            "id": f"node_{i}",
            "content": f"Knowledge item {i} for {agent_id}",
            "label": f"Knowledge {i}",
            "tier": tier,
            "type": "KNOWLEDGE",
            "importance": 0.5 + (i % 5) / 10,
            "access_count": 10 - i % 10,
            "is_user_context": i % 7 == 0,
            "shape": "diamond" if i % 7 == 0 else "circle",
            "glow": i % 11 == 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    edges = []
    for i in range(min(50, len(nodes) - 1)):
        edges.append({
            "source": nodes[i]["id"],
            "target": nodes[i + 1]["id"],
            "strength": 0.5,
            "type": "semantic",
            "glow": i % 10 == 0
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_knowledge": len(nodes),
            "hot_tier_count": sum(1 for n in nodes if n["tier"] == "hot"),
            "warm_tier_count": sum(1 for n in nodes if n["tier"] == "warm"),
            "cold_tier_count": sum(1 for n in nodes if n["tier"] == "cold"),
            "user_context_count": sum(1 for n in nodes if n.get("is_user_context", False))
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/knowledge-graph/access")
async def record_knowledge_access(
    node_id: str,
    agent_id: str,
    interaction_type: str = "view"
):
    """Record when a knowledge node is accessed and broadcast to connected clients."""
    access_event = {
        "type": "knowledge_access",
        "node_id": node_id,
        "agent_id": agent_id,
        "interaction_type": interaction_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Broadcast to all connected WebSocket clients
    await broadcast_to_websockets(access_event)
    
    # Send to Kafka if enabled
    if kafka_producer:
        await kafka_producer.send("memory-access", access_event)
    
    # Store in Redis for real-time tracking
    if redis_client:
        await redis_client.hincrby(f"knowledge_access:{node_id}", "count", 1)
        await redis_client.hset(f"knowledge_access:{node_id}", "last_accessed", access_event["timestamp"])
    
    return {"status": "success", "event": access_event}

# Anomaly Detection Endpoints
@app.post("/api/anomaly/detect")
async def detect_anomaly(
    agent_id: str,
    metric_name: str,
    value: float,
    context: Optional[Dict[str, Any]] = None
):
    """Detect anomaly in real-time using HTM"""
    if not anomaly_detector:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection not enabled. Set ENABLE_HTM_ANOMALY_DETECTION=true"
        )
    
    try:
        result = await anomaly_detector.detect_anomaly(
            agent_id=agent_id,
            metric_name=metric_name,
            value=value,
            context=context
        )
        
        return {
            "timestamp": result.timestamp.isoformat(),
            "is_anomaly": result.is_anomaly,
            "anomaly_score": result.anomaly_score,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "compute_time_us": result.context.get("compute_time_us", 0),
            "threshold": result.context.get("threshold", 0)
        }
    except Exception as e:
        logger.error(f"Error detecting anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/anomaly/detect-batch")
async def detect_anomaly_batch(
    agent_id: str,
    metrics: List[Dict[str, Any]]
):
    """Detect anomalies in a batch of metrics"""
    if not anomaly_detector:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection not enabled"
        )
    
    try:
        results = await anomaly_detector.detect_batch(agent_id, metrics)
        
        return {
            "agent_id": agent_id,
            "results": [
                {
                    "metric": r.metric_name,
                    "value": r.raw_value,
                    "is_anomaly": r.is_anomaly,
                    "score": r.anomaly_score,
                    "explanation": r.explanation
                }
                for r in results
            ],
            "anomalies_found": sum(1 for r in results if r.is_anomaly),
            "total_metrics": len(results)
        }
    except Exception as e:
        logger.error(f"Error in batch anomaly detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anomaly/agent/{agent_id}/summary")
async def get_agent_anomaly_summary(agent_id: str):
    """Get anomaly detection summary for an agent"""
    if not anomaly_detector:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection not enabled"
        )
    
    try:
        summary = await anomaly_detector.get_agent_anomaly_summary(agent_id)
        return summary
    except Exception as e:
        logger.error(f"Error fetching anomaly summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard/{user_id}")
async def dashboard_websocket(websocket: WebSocket, user_id: str):
    """Enhanced WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial connection success
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": ["knowledge_graph", "memory_access", "breakthrough_detection"]
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    await handle_subscription(websocket, message)
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected for user {user_id}")

async def handle_subscription(websocket: WebSocket, message: Dict[str, Any]):
    """Handle WebSocket subscription requests."""
    subscription_type = message.get("subscription_type")
    
    if subscription_type == "agent_status":
        # Subscribe to specific agent status updates
        agent_id = message.get("agent_id")
        # Implementation would add websocket to agent-specific subscriber list
        await websocket.send_json({
            "type": "subscription_confirmed",
            "subscription_type": subscription_type,
            "agent_id": agent_id
        })

# WebSocket endpoint for real-time anomaly alerts
@app.websocket("/ws/anomaly/{agent_id}")
async def anomaly_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time anomaly alerts"""
    await websocket.accept()
    
    # Subscribe to anomaly events for this agent
    redis_client = aioredis.from_url(REDIS_URL)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"anomaly:{agent_id}")
    
    try:
        while True:
            # Listen for anomaly events
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            
            if message and message['type'] == 'message':
                # Send anomaly to client
                await websocket.send_text(message['data'].decode())
            
            # Keep connection alive
            await asyncio.sleep(0.1)
    
    except WebSocketDisconnect:
        logger.info(f"Anomaly WebSocket disconnected for agent {agent_id}")
    except Exception as e:
        logger.error(f"Error in anomaly WebSocket: {e}")
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
        await redis_client.close()

# Serve the dashboard HTML (for development)
@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard page"""
    # Try multiple dashboard locations
    dashboard_paths = [
        Path(__file__).parent.parent / "docs" / "context" / "auren-realtime-dashboard.html",
        Path(__file__).parent.parent / "dashboard" / "realtime_dashboard.html",
        "auren/docs/context/auren-realtime-dashboard.html",
        "auren/dashboard/realtime_dashboard.html"
    ]
    
    dashboard_path = None
    for path in dashboard_paths:
        if Path(path).exists() or os.path.exists(str(path)):
            dashboard_path = str(path)
            break
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        return {"message": "Dashboard HTML not found. Please ensure realtime_dashboard.html is in auren/dashboard/"}

@app.get("/dashboard")
async def serve_dashboard_alt():
    """Alternative dashboard route"""
    return await serve_dashboard()

# Static file serving for any dashboard assets
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files for the dashboard"""
    static_path = f"auren/dashboard/static/{file_path}"
    if os.path.exists(static_path):
        return FileResponse(static_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/agent-cards/{agent_id}")
async def get_agent_card_data(agent_id: str):
    """Get comprehensive data for an agent card display."""
    try:
        # Placeholder for agent card data
        return {
            "agent_id": agent_id,
            "name": agent_id.replace("_", " ").title(),
            "status": "thinking",
            "knowledge_count": 1247,
            "active_hypotheses": 3,
            "accuracy": 94.2,
            "specialization": "CNS Optimization",
            "last_breakthrough": datetime.now(timezone.utc).isoformat(),
            "performance_metrics": {
                "response_time_ms": 8.3,
                "decisions_per_minute": 147,
                "knowledge_growth_rate": 2.3
            }
        }
    except Exception as e:
        logger.error(f"Error fetching agent card data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # Enable auto-reload for development
    ) 