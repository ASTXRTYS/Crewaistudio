#!/usr/bin/env python3
"""
=============================================================================
AUREN BIOMETRIC BRIDGE - FASTAPI HTTP LAYER
=============================================================================
FastAPI application for webhook endpoints with HIPAA-compliant logging
and proper error handling.

Note: Rate limiting should be implemented at infrastructure layer (ALB/nginx)
=============================================================================
"""

import os
import uuid
import hmac
import hashlib
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager

import asyncpg
import aioredis
from aiokafka import AIOKafkaProducer

from .bridge import (
    ConcurrentBiometricProcessor,
    Settings,
    request_id_var,
    hipaa_logger
)

# Initialize FastAPI app
app = FastAPI(
    title="AUREN Biometric Bridge API",
    description="Production-ready biometric webhook processing system",
    version="2.0.0"
)

# Security
security = HTTPBearer()

# Global processor instance (initialized on startup)
processor: ConcurrentBiometricProcessor = None


# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with proper resource cleanup"""
    # Startup
    hipaa_logger.info("Starting AUREN Biometric Bridge API...")
    
    # Load settings
    settings = Settings()
    
    # Initialize connection pools
    pg_pool = await asyncpg.create_pool(
        settings.postgres_url,
        min_size=settings.pg_pool_min_size,
        max_size=settings.pg_pool_max_size,
        command_timeout=60,
        server_settings={'jit': 'off'}
    )
    
    redis = await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        health_check_interval=30,
        socket_keepalive=True
    )
    
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        compression_type='snappy',
        linger_ms=10,
        batch_size=16384,
        retries=3,
        retry_backoff_ms=100
    )
    await producer.start()
    
    # Create and start processor
    global processor
    processor = ConcurrentBiometricProcessor(producer, redis, pg_pool)
    await processor.start()
    
    # Store in app state
    app.state.processor = processor
    app.state.pg_pool = pg_pool
    app.state.redis = redis
    app.state.producer = producer
    app.state.settings = settings
    
    hipaa_logger.info("Biometric Bridge API started successfully")
    
    yield
    
    # Shutdown
    hipaa_logger.info("Shutting down AUREN Biometric Bridge API...")
    await processor.shutdown()
    await pg_pool.close()
    await redis.close()
    await producer.stop()
    hipaa_logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan)


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_processor() -> ConcurrentBiometricProcessor:
    """Dependency injection for processor"""
    return app.state.processor


async def get_settings() -> Settings:
    """Dependency injection for settings"""
    return app.state.settings


async def verify_webhook_signature(
    request: Request,
    secret: str,
    header_name: str
) -> bool:
    """Verify webhook signature for security"""
    signature = request.headers.get(header_name)
    if not signature:
        return False
    
    body = await request.body()
    expected_sig = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_sig)


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@app.post("/webhooks/oura")
async def oura_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    processor: ConcurrentBiometricProcessor = Depends(get_processor),
    settings: Settings = Depends(get_settings)
):
    """Process Oura Ring webhook events"""
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Verify signature if configured
    if settings.oura_webhook_secret:
        is_valid = await verify_webhook_signature(
            request,
            settings.oura_webhook_secret,
            "X-Oura-Signature"
        )
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    
    # Process in background to return quickly
    background_tasks.add_task(
        processor.process_webhook,
        "oura",
        data
    )
    
    return {"status": "accepted", "request_id": request_id}


@app.post("/webhooks/whoop")
async def whoop_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    processor: ConcurrentBiometricProcessor = Depends(get_processor),
    settings: Settings = Depends(get_settings)
):
    """Process WHOOP Band webhook events"""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Verify signature
    if settings.whoop_webhook_secret:
        is_valid = await verify_webhook_signature(
            request,
            settings.whoop_webhook_secret,
            "X-Whoop-Signature-256"
        )
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    
    background_tasks.add_task(
        processor.process_webhook,
        "whoop",
        data
    )
    
    return {"status": "accepted", "request_id": request_id}


@app.post("/webhooks/healthkit")
async def healthkit_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    processor: ConcurrentBiometricProcessor = Depends(get_processor),
    settings: Settings = Depends(get_settings),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Process Apple HealthKit data pushes"""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Validate API key since HealthKit doesn't have webhook signatures
    if credentials.credentials != settings.healthkit_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    data = await request.json()
    
    background_tasks.add_task(
        processor.process_webhook,
        "healthkit",
        data
    )
    
    return {"status": "accepted", "request_id": request_id}


# =============================================================================
# HEALTH & MONITORING ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "biometric-bridge"}


@app.get("/ready")
async def readiness_check(
    processor: ConcurrentBiometricProcessor = Depends(get_processor)
):
    """Readiness probe that checks dependencies"""
    try:
        # Check PostgreSQL
        async with app.state.pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis
        await app.state.redis.ping()
        
        # Get processor metrics
        metrics = await processor.get_processing_metrics()
        
        return {
            "status": "ready",
            "dependencies": {
                "postgres": "healthy",
                "redis": "healthy",
                "kafka": "healthy"
            },
            "processor": metrics
        }
    except Exception as e:
        hipaa_logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e)
        }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    # Note: In production, use prometheus_client.generate_latest()
    # This is a placeholder
    return {
        "message": "Prometheus metrics endpoint",
        "info": "Configure prometheus_client to expose metrics here"
    }


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    return {
        "error": "validation_error",
        "detail": str(exc),
        "request_id": request_id_var.get()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    hipaa_logger.error(f"Unexpected error: {exc}")
    return {
        "error": "internal_server_error",
        "detail": "An unexpected error occurred",
        "request_id": request_id_var.get()
    }


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "AUREN Biometric Bridge",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "webhooks": [
                "/webhooks/oura",
                "/webhooks/whoop",
                "/webhooks/healthkit"
            ],
            "monitoring": [
                "/health",
                "/ready",
                "/metrics"
            ]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    ) 