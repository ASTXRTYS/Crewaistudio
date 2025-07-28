# =============================================================================
# SECTION 12: MAIN EXECUTION - CLEAN IMPLEMENTATION (NO CREWAI)
# =============================================================================
# Purpose: Production-ready runtime without CrewAI dependencies
# Last Updated: 2025-01-29
# =============================================================================

import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import asyncpg
import redis.asyncio as aioredis
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tenacity import retry, stop_after_attempt, wait_exponential

# Import our security layer
from security import create_security_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# GLOBAL STATE MANAGEMENT
# =============================================================================

class AppState:
    """Centralized state management for graceful shutdown"""
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.shutdown_event = asyncio.Event()
        
app_state = AppState()

# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle with proper startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting AUREN Production Runtime (Section 12)...")
    logger.info("Clean implementation without CrewAI dependencies")
    
    try:
        # Initialize connections with retry
        app_state.postgres_pool = await create_postgres_pool()
        app_state.redis_client = await create_redis_client()
        
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
    title="AUREN Production Runtime",
    description="Clean production runtime without CrewAI dependencies",
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
        "implementation": "clean-no-crewai",
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
    
    # Add custom metrics here
    metrics_data.append('auren_section12_up {implementation="clean"} 1')
    
    return JSONResponse(
        content="\n".join(metrics_data),
        media_type="text/plain"
    )

@app.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe"""
    ready = app_state.postgres_pool is not None and app_state.redis_client is not None
    
    if ready:
        return {"status": "ready", "implementation": "clean-no-crewai"}
    else:
        raise HTTPException(status_code=503, detail="Not ready")

# =============================================================================
# WEBHOOK ENDPOINTS (PLACEHOLDER)
# =============================================================================

@app.post("/webhooks/{device_type}")
async def webhook_handler(device_type: str, request: Request):
    """
    Placeholder webhook handler for biometric devices
    In production, this would process and store biometric data
    """
    try:
        data = await request.json()
        
        # Log the webhook
        logger.info(f"Received webhook from {device_type}: {data.get('event_type', 'unknown')}")
        
        # In production: 
        # - Validate webhook signature
        # - Process biometric data
        # - Store in PostgreSQL/TimescaleDB
        # - Publish to Kafka if needed
        
        return {"status": "accepted", "device": device_type}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# API INFO
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "service": "AUREN Production Runtime",
        "version": "12.0.0",
        "status": "operational",
        "implementation": "clean-no-crewai",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "readiness": "/readiness",
            "webhooks": "/webhooks/{device_type}",
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
            "POSTGRES_URL"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.info("Please check your .env file or environment configuration")
            sys.exit(1)
        
        # Run as FastAPI server
        logger.info("Starting clean production runtime...")
        
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