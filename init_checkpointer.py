# Import still works with separate package installed
from langgraph.checkpoint.postgres import PostgresSaver
import asyncio

async def setup():
    # Temporarily skip setup to test application startup
    print("✅ Skipping checkpointer setup for now - imports work!")
    print("✅ Dependencies are correctly installed!")

if __name__ == "__main__":
    asyncio.run(setup()) 