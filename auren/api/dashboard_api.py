"""
FastAPI Dashboard API - The Bridge Between Frontend and Backend
This serves data to the dashboard and handles WebSocket connections
"""

from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Dict, Optional, List, Any
import asyncio
import json
import os
from datetime import datetime, timezone
import redis.asyncio as redis
import logging
from pathlib import Path

# Import the visualizers you built
from auren.realtime.dashboard_backends import (
    ReasoningChainVisualizer,
    CostAnalyticsDashboard,
    LearningSystemVisualizer
)

# Import memory system
from auren.core.memory import UnifiedMemorySystem
from auren.config.production_settings import settings
from auren.core.anomaly.htm_detector import HTMAnomalyDetector, HTMConfig
import asyncpg

logger = logging.getLogger(__name__)

# Global instances
visualizers = {}
active_connections: List[WebSocket] = []
memory_system: Optional[UnifiedMemorySystem] = None
db_pool: Optional[asyncpg.Pool] = None
anomaly_detector: Optional[HTMAnomalyDetector] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown"""
    global memory_system, db_pool, anomaly_detector
    
    # Startup
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
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
            redis_url=redis_url,
            config=htm_config
        )
        await anomaly_detector.initialize()
        logger.info("HTM Anomaly Detector initialized")
    
    # Initialize visualizers
    visualizers["reasoning"] = ReasoningChainVisualizer(redis_url=redis_url)
    visualizers["cost"] = CostAnalyticsDashboard(redis_url=redis_url)
    visualizers["learning"] = LearningSystemVisualizer(
        redis_url=redis_url,
        memory_backend=None,  # Will be set when available
        hypothesis_validator=None  # Will be set when available
    )
    
    # Initialize connections
    for viz in visualizers.values():
        await viz.initialize()
    
    logger.info("Dashboard API initialized successfully")
    
    yield
    
    # Shutdown
    for viz in visualizers.values():
        if hasattr(viz, 'cleanup'):
            await viz.cleanup()
    
    logger.info("Dashboard API shutdown complete")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="AUREN Dashboard API",
    version="1.0.0",
    description="Real-time API for AUREN health intelligence dashboard",
    lifespan=lifespan
)

# Configure CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
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
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
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
    for name, viz in visualizers.items():
        try:
            # Simple check - can we access the visualizer?
            health_status["components"][f"{name}_visualizer"] = "healthy"
        except Exception as e:
            health_status["components"][f"{name}_visualizer"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    
    # Add connection count
    health_status["active_websocket_connections"] = len(active_connections)
    
    return health_status

# REST Endpoints for Dashboard Data
@app.get("/api/reasoning-chain/{session_id}")
async def get_reasoning_chain(session_id: str, limit: int = 50):
    """Get the reasoning chain for a specific session"""
    try:
        if "reasoning" not in visualizers:
            raise HTTPException(status_code=503, detail="Reasoning visualizer not initialized")
        
        chain_data = await visualizers["reasoning"].get_reasoning_chain(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "chain": chain_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting reasoning chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cost-analytics")
async def get_cost_analytics(period: str = "today"):
    """Get cost analytics"""
    try:
        if "cost" not in visualizers:
            raise HTTPException(status_code=503, detail="Cost visualizer not initialized")
        
        # Validate period parameter
        valid_periods = ["today", "week", "month", "all"]
        if period not in valid_periods:
            period = "today"
        
        metrics = await visualizers["cost"].get_cost_metrics()
        
        return {
            "success": True,
            "period": period,
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cost analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning-progress")
async def get_learning_progress():
    """Get learning system progress"""
    try:
        if "learning" not in visualizers:
            raise HTTPException(status_code=503, detail="Learning visualizer not initialized")
        
        progress = await visualizers["learning"].get_learning_metrics()
        
        return {
            "success": True,
            "progress": progress,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-metrics")
async def get_system_metrics():
    """Get overall system metrics across all users"""
    try:
        # Aggregate metrics across all visualizers
        total_events = 0
        active_sessions = 0
        
        # Get Redis metrics
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        
        # Count events in streams
        for tier in ["critical", "operational", "analytical"]:
            stream_key = f"auren:events:{tier}"
            try:
                count = await redis_client.xlen(stream_key)
                total_events += count
            except:
                pass
        
        await redis_client.close()
        
        return {
            "success": True,
            "metrics": {
                "total_events_processed": total_events,
                "active_websocket_connections": len(active_connections),
                "system_uptime_seconds": 0,  # Would track actual uptime
                "health_status": "operational"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
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
    agent_id: str,
    depth: int = 1
):
    """
    Fetch knowledge graph data from all three tiers
    depth=1: 50 nodes (hot tier only)
    depth=2: 500 nodes (hot + warm)
    depth=3: 5000 nodes (all tiers)
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not initialized")
    
    # Validate depth parameter
    if depth < 1 or depth > 3:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 3")
    
    try:
        nodes = []
        
        # Helper function to format memories as nodes
        def format_as_nodes(memories, tier):
            formatted_nodes = []
            for memory in memories:
                node = {
                    "id": memory.get("memory_id", memory.get("id", "")),
                    "content": memory.get("content", ""),
                    "tier": tier,
                    "type": memory.get("memory_type", "KNOWLEDGE"),
                    "access_count": memory.get("access_count", 0),
                    "importance": memory.get("importance", 0.5),
                    "is_user_context": "user_context" in memory.get("tags", []) if memory.get("tags") else False,
                    "timestamp": memory.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "metadata": memory.get("metadata", {})
                }
                
                # Special handling for user context
                if node["is_user_context"]:
                    node["shape"] = "diamond"
                    node["glow"] = True
                
                formatted_nodes.append(node)
            
            return formatted_nodes
        
        # Fetch from appropriate tiers based on depth
        if depth >= 1:
            # Hot tier - current context and active knowledge
            hot_memories = await memory_system.redis_tier.get_recent_memories(
                agent_id=agent_id,
                limit=50
            )
            nodes.extend(format_as_nodes(hot_memories, tier="hot"))
        
        if depth >= 2:
            # Warm tier - structured user data and patterns
            warm_memories = await memory_system.postgres_tier.search_memories(
                agent_id=agent_id,
                filters={"limit": 450}
            )
            nodes.extend(format_as_nodes(warm_memories, tier="warm"))
        
        if depth >= 3:
            # Cold tier - semantic knowledge base
            cold_results = await memory_system.chromadb_tier.semantic_search(
                agent_id=agent_id,
                query="",  # Empty query to get all
                limit=4500
            )
            
            # Convert cold tier results to node format
            cold_memories = []
            for result in cold_results:
                memory_dict = {
                    "memory_id": result.metadata.get("memory_id", ""),
                    "content": result.metadata.get("content", ""),
                    "memory_type": result.metadata.get("memory_type", "KNOWLEDGE"),
                    "importance": result.metadata.get("importance", 0.5),
                    "tags": result.metadata.get("tags", []),
                    "metadata": result.metadata
                }
                cold_memories.append(memory_dict)
            
            nodes.extend(format_as_nodes(cold_memories, tier="cold"))
        
        # Calculate edges based on semantic similarity
        edges = calculate_knowledge_connections(nodes)
        
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
        logger.error(f"Error fetching knowledge graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def calculate_knowledge_connections(nodes: List[Dict]) -> List[Dict]:
    """
    Calculate edges between nodes based on semantic similarity and relationships.
    For now, we'll create simple connections based on memory type and tier proximity.
    In production, this would use embeddings for true semantic similarity.
    """
    edges = []
    
    # Group nodes by type for more meaningful connections
    nodes_by_type = {}
    for node in nodes:
        node_type = node.get("type", "KNOWLEDGE")
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    # Create connections within same type (simplified logic)
    for node_type, type_nodes in nodes_by_type.items():
        # Connect nodes that are temporally close or have high importance
        for i, node1 in enumerate(type_nodes):
            for node2 in type_nodes[i+1:i+5]:  # Connect to next 4 nodes max
                # Calculate connection strength based on importance and tier
                strength = (node1["importance"] + node2["importance"]) / 2
                
                # Boost connection if both are user context
                if node1.get("is_user_context") and node2.get("is_user_context"):
                    strength *= 1.5
                
                # Create edge if strength is significant
                if strength > 0.3:
                    edges.append({
                        "source": node1["id"],
                        "target": node2["id"],
                        "strength": min(strength, 1.0),
                        "type": "semantic"
                    })
    
    # Connect hot tier memories to their warm/cold tier origins
    hot_nodes = [n for n in nodes if n["tier"] == "hot"]
    other_nodes = [n for n in nodes if n["tier"] != "hot"]
    
    for hot_node in hot_nodes[:20]:  # Limit connections for performance
        # Find related memories in other tiers (simplified - would use embeddings in production)
        for other_node in other_nodes:
            # Check if content overlaps significantly (simplified check)
            if (hot_node["type"] == other_node["type"] and 
                hot_node.get("is_user_context") == other_node.get("is_user_context")):
                edges.append({
                    "source": hot_node["id"],
                    "target": other_node["id"],
                    "strength": 0.5,
                    "type": "tier_connection"
                })
                break
    
    return edges

@app.post("/api/knowledge-graph/access")
async def report_knowledge_access(
    agent_id: str,
    memory_id: str,
    tier: str
):
    """Report when an agent accesses knowledge for real-time updates"""
    event = {
        "type": "knowledge_access",
        "agent_id": agent_id,
        "memory_id": memory_id,
        "tier": tier,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Broadcast to all connected WebSocket clients
    for connection in active_connections:
        try:
            await connection.send_json(event)
        except:
            # Remove dead connections
            active_connections.remove(connection)
    
    return {"status": "success", "event": event}

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
    """WebSocket connection for real-time dashboard updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"WebSocket connected for user: {user_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Create background tasks for streaming updates
        async def stream_reasoning_updates():
            """Stream reasoning chain updates"""
            while True:
                try:
                    if "reasoning" in visualizers:
                        # Get latest reasoning events
                        chains = await visualizers["reasoning"].get_active_chains()
                        
                        if chains:
                            await websocket.send_json({
                                "type": "reasoning_update",
                                "data": chains,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                    
                    await asyncio.sleep(1)  # Update every second
                    
                except Exception as e:
                    logger.error(f"Error streaming reasoning updates: {e}")
                    break
        
        async def stream_cost_updates():
            """Stream cost metric updates"""
            while True:
                try:
                    if "cost" in visualizers:
                        # Get real-time cost metrics
                        metrics = await visualizers["cost"].get_cost_metrics()
                        
                        if metrics:
                            await websocket.send_json({
                                "type": "cost_update",
                                "data": metrics,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                    
                    await asyncio.sleep(2)  # Update every 2 seconds
                    
                except Exception as e:
                    logger.error(f"Error streaming cost updates: {e}")
                    break
        
        async def stream_learning_updates():
            """Stream learning progress updates"""
            while True:
                try:
                    if "learning" in visualizers:
                        # Get learning progress updates
                        progress = await visualizers["learning"].get_learning_metrics()
                        
                        if progress:
                            await websocket.send_json({
                                "type": "learning_update",
                                "data": progress,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error streaming learning updates: {e}")
                    break
        
        async def handle_client_messages():
            """Handle messages from the client"""
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    # Handle different message types
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "subscribe":
                        # Handle subscription updates
                        logger.info(f"Client subscribed to: {data.get('channels', [])}")
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    break
        
        # Run all tasks concurrently
        await asyncio.gather(
            stream_reasoning_updates(),
            stream_cost_updates(),
            stream_learning_updates(),
            handle_client_messages()
        )
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected for user: {user_id}")

# WebSocket endpoint for real-time anomaly alerts
@app.websocket("/ws/anomaly/{agent_id}")
async def anomaly_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time anomaly alerts"""
    await websocket.accept()
    
    # Subscribe to anomaly events for this agent
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
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