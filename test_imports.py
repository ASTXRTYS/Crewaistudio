#!/usr/bin/env python3
"""Test that all critical imports work"""

try:
    print("Testing imports...")
    
    # Test FastAPI
    import fastapi
    print("✅ FastAPI imported")
    
    # Test LangGraph
    import langgraph
    print("✅ LangGraph imported")
    
    # Test the critical checkpointer import (with separate package)
    from langgraph.checkpoint.postgres import PostgresSaver
    print("✅ PostgresSaver imported successfully!")
    
    # Test other dependencies
    import redis
    import asyncpg
    import uvicorn
    print("✅ All other dependencies imported")
    
    print("\n🎉 All imports successful! The environment is correctly set up.")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nThis means the dependency is still not installed correctly.") 