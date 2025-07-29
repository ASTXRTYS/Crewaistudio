#!/usr/bin/env python3
"""
Startup script for NEUROS Advanced Reasoning
"""
import asyncio
import uvicorn
from neuros_advanced_reasoning_simple import initialize_neuros_advanced_langgraph

async def main():
    """Initialize and run NEUROS Advanced."""
    app = await initialize_neuros_advanced_langgraph("config/neuros_config.json")
    
    # Run with uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main()) 