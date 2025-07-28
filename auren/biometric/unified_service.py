"""
Unified Biometric + NEUROS Service
Combines Sections 1-8 for immediate deployment
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biometric.bridge import BiometricKafkaLangGraphBridge
from agents.neuros.section_8_neuros_graph import NEUROSCognitiveGraph

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_service")

# Global instances
bridge: Optional[BiometricKafkaLangGraphBridge] = None
neuros: Optional[NEUROSCognitiveGraph] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup"""
    global bridge, neuros
    
    logger.info("Starting Unified Biometric Service...")
    
    try:
        # Initialize NEUROS
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        neuros = NEUROSCognitiveGraph(
            llm=llm,
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL"),
            neuros_yaml_path="/app/neuros_agent_profile.yaml"
        )
        
        await neuros.initialize()
        logger.info("NEUROS initialized")
        
        # Initialize Biometric Bridge
        bridge = BiometricKafkaLangGraphBridge(
            kafka_brokers=os.getenv("KAFKA_BROKERS", "kafka:9092"),
            consumer_group="biometric-processor",
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL")
        )
        
        # Connect bridge to NEUROS
        bridge.graph = neuros
        
        # Start consuming in background
        asyncio.create_task(bridge.consume_loop())
        logger.info("Biometric bridge started")
        
        yield
        
    finally:
        if bridge:
            await bridge.close()
        if neuros:
            await neuros.cleanup()
        logger.info("Shutdown complete")

# Create app
app = FastAPI(
    title="AUREN Unified Biometric Service",
    description="Sections 1-8: Biometric Bridge + NEUROS",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "unified-biometric",
        "components": {
            "neuros": neuros is not None,
            "bridge": bridge is not None,
            "kafka": bridge and bridge.consumer is not None if bridge else False
        }
    }

@app.get("/status")
async def status():
    """Get service status"""
    if not bridge or not neuros:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "events_processed": getattr(bridge, 'events_processed', 0),
        "current_mode": "baseline",  # Get from NEUROS state
        "uptime": "0h"  # Calculate actual uptime
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 