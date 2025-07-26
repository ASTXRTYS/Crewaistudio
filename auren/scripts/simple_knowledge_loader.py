"""
Simple Neuroscientist Knowledge Loader
Loads Level 1 knowledge directly into Redis without complex dependencies
"""

import os
import redis
import asyncpg
import asyncio
import json
from datetime import datetime
from pathlib import Path
import uuid

async def load_knowledge():
    """Load neuroscientist knowledge into the memory system"""
    
    # Connect to services
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # PostgreSQL connection
    conn = await asyncpg.connect(
        'postgresql://auren_user:auren_secure_password_change_me@127.0.0.1:5432/auren'
    )
    
    # Knowledge directory
    knowledge_dir = Path("auren/src/agents/Level 1 knowledge")
    
    print(f"📚 Loading knowledge from: {knowledge_dir}")
    
    # Find all knowledge files
    knowledge_files = list(knowledge_dir.glob("*.md"))
    print(f"Found {len(knowledge_files)} knowledge files")
    
    loaded_count = 0
    agent_id = "neuroscientist_001"
    
    for file_path in knowledge_files:
        try:
            print(f"\n📄 Loading: {file_path.name}")
            
            # Read content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract topic
            topic = file_path.stem.replace("neuroscientist_", "").replace("_", " ").title()
            
            # Create memory ID
            memory_id = str(uuid.uuid4())
            
            # Store in Redis (hot tier) with high importance
            redis_key = f"agent:{agent_id}:memory:{memory_id}"
            memory_data = {
                "memory_id": memory_id,
                "agent_id": agent_id,
                "content": content[:1000] + "..." if len(content) > 1000 else content,
                "memory_type": "KNOWLEDGE",
                "importance": 0.95,  # High importance for foundational knowledge
                "tags": json.dumps(["level1", "foundational", topic.lower()]),
                "metadata": json.dumps({
                    "source_file": file_path.name,
                    "topic": topic,
                    "full_length": len(content),
                    "loaded_at": datetime.utcnow().isoformat()
                }),
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "access_count": "1"
            }
            
            # Store in Redis
            redis_client.hset(redis_key, mapping=memory_data)
            
            # Add to importance sorted set (for hot tier management)
            redis_client.zadd(f"agent:{agent_id}:importance", {memory_id: 0.95})
            
            # Also store in PostgreSQL for persistence
            await conn.execute("""
                INSERT INTO agent_memories 
                (memory_id, agent_id, memory_type, content, importance, tags, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (memory_id) DO NOTHING
            """, 
                memory_id, agent_id, "KNOWLEDGE", content, 0.95,
                ["level1", "foundational", topic.lower()],
                {
                    "source_file": file_path.name,
                    "topic": topic,
                    "full_length": len(content)
                },
                datetime.utcnow()
            )
            
            print(f"✅ Loaded {topic} into memory system (ID: {memory_id})")
            loaded_count += 1
            
        except Exception as e:
            print(f"❌ Failed to load {file_path.name}: {e}")
    
    # Close connections
    await conn.close()
    
    print(f"\n🎉 Knowledge loading complete!")
    print(f"Loaded {loaded_count}/{len(knowledge_files)} files")
    
    # Verify in Redis
    total_memories = redis_client.zcard(f"agent:{agent_id}:importance")
    print(f"Total memories in Redis hot tier: {total_memories}")
    
    return loaded_count

if __name__ == "__main__":
    # Run the loader
    asyncio.run(load_knowledge()) 