"""
NEUROS Cognitive Service - Main API Entry Point
The world's first biometric-aware AI personality system
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from section_8_neuros_graph import NEUROSCognitiveGraph

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neuros.main")

# Global NEUROS instance
neuros_graph: Optional[NEUROSCognitiveGraph] = None

# Request/Response models
class BiometricEvent(BaseModel):
    """Biometric event from Kafka"""
    event_type: str
    user_id: str
    timestamp: str
    data: Dict[str, Any]
    thread_id: Optional[str] = None

class ProcessResponse(BaseModel):
    """Response from NEUROS processing"""
    status: str
    mode: str
    response: str
    thread_id: str
    metadata: Dict[str, Any]

class HealthStatus(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    checks: Dict[str, bool]

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage NEUROS lifecycle"""
    global neuros_graph
    
    logger.info("Starting NEUROS Cognitive Service...")
    
    try:
        # Initialize NEUROS
        from langchain_openai import ChatOpenAI  # Or your LLM of choice
        
        llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        neuros_graph = NEUROSCognitiveGraph(
            llm=llm,
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL"),
            neuros_yaml_path=os.getenv("NEUROS_YAML_PATH", "/config/neuros_agent_profile.yaml")
        )
        
        await neuros_graph.initialize()
        logger.info("NEUROS initialized successfully")
        
        yield
        
    finally:
        # Cleanup
        if neuros_graph:
            await neuros_graph.cleanup()
        logger.info("NEUROS shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="NEUROS Cognitive Service",
    description="Biometric-aware AI personality system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    checks = {
        "neuros": neuros_graph is not None,
        "postgres": False,
        "redis": False,
        "kafka": False
    }
    
    if neuros_graph:
        try:
            # Check PostgreSQL
            if neuros_graph.postgres_pool:
                async with neuros_graph.postgres_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                checks["postgres"] = True
        except:
            pass
        
        try:
            # Check Redis
            if neuros_graph.redis_client:
                await neuros_graph.redis_client.ping()
                checks["redis"] = True
        except:
            pass
    
    status = "healthy" if all(checks.values()) else "degraded"
    
    return HealthStatus(
        status=status,
        service="neuros-cognitive",
        version="1.0.0",
        checks=checks
    )

# Process biometric event
@app.post("/process", response_model=ProcessResponse)
async def process_biometric_event(event: BiometricEvent):
    """Process a biometric event through NEUROS"""
    if not neuros_graph:
        raise HTTPException(status_code=503, detail="NEUROS not initialized")
    
    try:
        # Use provided thread_id or generate new one
        thread_id = event.thread_id or f"user_{event.user_id}_{event.timestamp}"
        
        # Process through NEUROS
        result = await neuros_graph.process_biometric_event(
            event.dict(),
            thread_id
        )
        
        return ProcessResponse(
            status="success",
            mode=result.get("mode", "unknown"),
            response=result.get("response", ""),
            thread_id=thread_id,
            metadata={
                "processing_time": result.get("processing_time", 0),
                "confidence": result.get("confidence", 0),
                "memory_updated": result.get("memory_updated", False)
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing biometric event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get current state
@app.get("/state/{thread_id}")
async def get_state(thread_id: str):
    """Get current NEUROS state for a thread"""
    if not neuros_graph:
        raise HTTPException(status_code=503, detail="NEUROS not initialized")
    
    try:
        # Get state from checkpointer
        if neuros_graph.checkpointer:
            state = await neuros_graph.graph.aget_state(
                {"configurable": {"thread_id": thread_id}}
            )
            
            if state and state.values:
                return {
                    "thread_id": thread_id,
                    "current_mode": state.values.get("current_mode"),
                    "mode_confidence": state.values.get("mode_confidence"),
                    "last_interaction": state.values.get("last_interaction"),
                    "messages_count": len(state.values.get("messages", [])),
                    "checkpoint_version": state.values.get("checkpoint_version")
                }
        
        raise HTTPException(status_code=404, detail="Thread not found")
        
    except Exception as e:
        logger.error(f"Error getting state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """WebSocket for real-time NEUROS updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive biometric data
            data = await websocket.receive_json()
            
            # Process through NEUROS
            event = BiometricEvent(
                event_type=data.get("event_type", "realtime"),
                user_id=data.get("user_id", "ws_user"),
                timestamp=data.get("timestamp", datetime.now().isoformat()),
                data=data,
                thread_id=thread_id
            )
            
            result = await process_biometric_event(event)
            
            # Send response
            await websocket.send_json(result.dict())
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for thread {thread_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV") == "development",
        workers=int(os.getenv("WORKERS", 2))
    ) 