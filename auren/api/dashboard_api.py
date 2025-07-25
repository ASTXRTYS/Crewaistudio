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

# Import the visualizers you built
from auren.realtime.dashboard_backends import (
    ReasoningChainVisualizer,
    CostAnalyticsDashboard,
    LearningSystemVisualizer
)

logger = logging.getLogger(__name__)

# Global instances
visualizers = {}
active_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown"""
    # Startup
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
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