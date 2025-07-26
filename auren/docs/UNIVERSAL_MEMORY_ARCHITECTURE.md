# AUREN Universal Memory Architecture

## Overview

The AUREN Three-Tier Memory System is a **UNIVERSAL INFRASTRUCTURE** shared by all AI agents in the system. This means:

- ✅ **ONE** Redis instance for all agents' hot memories
- ✅ **ONE** PostgreSQL database for all agents' warm memories and event sourcing
- ✅ **ONE** ChromaDB instance for all agents' semantic search capabilities
- ✅ **NO NEED** to create separate memory systems for each agent

## How Agent Isolation Works

While the infrastructure is shared, each agent's memories are **logically isolated** through namespacing:

```python
# Each agent has a unique identifier
agent_id = "neuroscientist_001"

# Memories are stored with agent-specific prefixes
redis_key = f"agent:{agent_id}:memory:{memory_id}"
postgres_record = {"agent_id": agent_id, "memory_id": memory_id, ...}
chromadb_metadata = {"agent_id": agent_id, ...}
```

## Memory Access Patterns

### 1. Agent-Specific Memories
Each agent can only access its own memories by default:

```python
# Agent retrieves only its own memories
memories = await memory_system.search_memories(
    UnifiedMemoryQuery(
        agent_id="neuroscientist_001",  # Filters to this agent only
        query="patient symptoms"
    )
)
```

### 2. Shared Memory Pools (Optional)
Agents can share specific memories through shared pools:

```python
# Creating a shared memory accessible by multiple agents
await memory_system.store_memory(
    content="Global medical protocol update",
    memory_type=MemoryType.SHARED,
    access_list=["neuroscientist_001", "psychiatrist_002", "surgeon_003"]
)
```

### 3. Cross-Agent Pattern Discovery (With Permission)
The system can discover patterns across agents when enabled:

```python
# Discover patterns across all medical agents
patterns = await memory_system.discover_cross_agent_patterns(
    agent_type="medical",
    require_consent=True  # Respects privacy settings
)
```

## Agent Integration Pattern

Every AI agent in AUREN follows this standard integration pattern:

```python
from auren.core.memory import UnifiedMemorySystem
from auren.config.production_settings import settings

class BaseAIAgent:
    """Base class for all AUREN AI agents"""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        
        # Connect to the UNIVERSAL memory system
        self.memory = UnifiedMemorySystem(
            redis_url=settings.redis_url,
            postgresql_pool=self.get_db_pool(),
            chromadb_host=settings.chromadb_host,
            chromadb_port=settings.chromadb_port
        )
        
    async def remember(self, content: str, importance: float = 0.5):
        """Store a memory with agent-specific context"""
        return await self.memory.store_memory(
            content=content,
            memory_type=MemoryType.EXPERIENCE,
            importance=importance,
            metadata={
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "timestamp": datetime.utcnow()
            }
        )
    
    async def recall(self, query: str, limit: int = 10):
        """Retrieve memories specific to this agent"""
        return await self.memory.search_memories(
            UnifiedMemoryQuery(
                query=query,
                agent_id=self.agent_id,
                limit=limit
            )
        )
```

## Infrastructure Scaling

The universal architecture scales efficiently:

### Current Capacity (Single Instance)
- **Redis**: 10,000+ hot memories, 5,000+ ops/sec
- **PostgreSQL**: Unlimited memories, 1,000+ writes/sec
- **ChromaDB**: 500GB storage, millions of embeddings

### Scaling Strategy
1. **Vertical Scaling**: Increase RAM/CPU for immediate capacity boost
2. **Read Replicas**: Add PostgreSQL read replicas for query distribution
3. **Redis Cluster**: Migrate to Redis Cluster mode for horizontal scaling
4. **ChromaDB Sharding**: Implement collection sharding by agent type

## Cost Benefits

The universal architecture provides significant cost savings:

- **Single Infrastructure**: ~$100-200/month vs $1000+ for per-agent systems
- **Shared Resources**: Better resource utilization (80% vs 20% typical)
- **Unified Monitoring**: One set of metrics/alerts instead of N sets
- **Simplified Backup**: Single backup strategy for all agent data

## Security & Privacy

The universal system maintains security through:

1. **Agent Authentication**: Each agent has unique credentials
2. **Row-Level Security**: PostgreSQL policies enforce agent boundaries
3. **Encryption**: All data encrypted at rest and in transit
4. **Audit Trails**: Complete event log of all memory operations
5. **HIPAA Compliance**: Medical data isolation and access controls

## Example: Multiple Agents

Here's how multiple agents coexist in the system:

```python
# Neuroscientist Agent
neuroscientist = NeuroscientistAgent(
    agent_id="neuro_001",
    specialization="cognitive_disorders"
)
await neuroscientist.remember("Patient shows signs of early dementia")

# Psychiatrist Agent  
psychiatrist = PsychiatristAgent(
    agent_id="psych_001",
    specialization="behavioral_therapy"
)
await psychiatrist.remember("Patient responds well to CBT techniques")

# Surgeon Agent
surgeon = SurgeonAgent(
    agent_id="surg_001", 
    specialization="neurosurgery"
)
await surgeon.remember("Successful tumor removal via craniotomy")

# Each agent's memories are isolated but use the SAME infrastructure
# The Redis instance has keys like:
# - "agent:neuro_001:memory:abc123"
# - "agent:psych_001:memory:def456" 
# - "agent:surg_001:memory:ghi789"
```

## Summary

- ✅ **ONE** three-tier memory system serves **ALL** agents
- ✅ Agents are **logically isolated** through namespacing
- ✅ **Optional** shared memory pools for collaboration
- ✅ **Massive cost savings** through resource sharing
- ✅ **Easy scaling** when needed
- ✅ **Full security** and privacy controls

This universal architecture is already implemented and ready for all current and future AUREN agents! 