"""
Minimal FastAPI Dashboard API - Simplified for quick deployment
"""

from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
import asyncio
import json
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Global instances
active_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown"""
    logger.info("Dashboard API starting up...")
    yield
    logger.info("Dashboard API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AUREN Dashboard API",
    version="1.0.0",
    description="Real-time API for AUREN health intelligence dashboard",
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

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "auren-api-minimal"
    }

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Mock memory statistics for now"""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overview": {
            "total_memories": 15,
            "active_agents": 1,
            "memory_operations_per_second": 0
        },
        "tiers": {
            "hot": {
                "name": "Redis (Hot Tier)",
                "memories": 15,
                "memory_usage_mb": 1.2
            },
            "warm": {
                "name": "PostgreSQL (Warm Tier)", 
                "memories": 0
            },
            "cold": {
                "name": "ChromaDB (Cold Tier)",
                "memories": 0
            }
        }
    }

@app.get("/api/knowledge-graph/data")
async def get_knowledge_graph_data(
    agent_id: str = Query(...),
    depth: int = Query(default=1, ge=1, le=3)
):
    """Return mock knowledge graph data for testing"""
    
    # Create mock nodes based on depth
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # Create mock edges
    edges = []
    for i in range(min(50, len(nodes) - 1)):
        edges.append({
            "source": nodes[i]["id"],
            "target": nodes[i + 1]["id"],
            "strength": 0.5,
            "type": "semantic"
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

@app.websocket("/ws/dashboard/{user_id}")
async def dashboard_websocket(websocket: WebSocket, user_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back for now
                await websocket.send_text(f"Echo: {data}")
            except Exception:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 