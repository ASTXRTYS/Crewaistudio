# PGVECTOR MIGRATION DESIGN
## Migrating from ChromaDB to PostgreSQL pgvector

*Created: January 29, 2025*  
*Purpose: Design document for consolidating vector storage*

---

## 🎯 OVERVIEW

Migrate AUREN's vector storage from ChromaDB to PostgreSQL pgvector to achieve:
- **Simplified architecture**: One less database to manage
- **Better data cohesion**: JOIN vectors with other PostgreSQL data
- **Improved performance**: pgvector 0.8 with disk-based ANN
- **Cost reduction**: Eliminate ChromaDB container overhead

---

## 📊 CURRENT STATE ANALYSIS

### ChromaDB Usage
```yaml
# From config/agents/ui_orchestrator.yaml
memory:
  type: "cognitive_twin"
  layers:
    - immediate: "redis"
    - long_term: "postgresql" 
    - knowledge_graph: "chromadb"  # <-- This will move to PostgreSQL
```

### Current Collections
```python
# From src/rag/vector_store.py
self.collections = {
    "journal": self._get_or_create_collection("journal_protocol"),
    "mirage": self._get_or_create_collection("mirage_protocol"),
    "visor": self._get_or_create_collection("visor_protocol"),
    "convergence": self._get_or_create_collection("convergence_insights"),
}
```

### Existing pgvector Usage
```sql
-- Already in PostgreSQL
CREATE TABLE memory_episodes (
    embedding VECTOR(1536),  -- Already using pgvector!
    ...
);
```

---

## 🏗️ MIGRATION ARCHITECTURE

### Target Schema
```sql
-- Unified vector store table
CREATE TABLE vector_store (
    id SERIAL PRIMARY KEY,
    collection VARCHAR(100) NOT NULL,
    document_id VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(255),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(384),  -- MiniLM model
    embedding_1536 vector(1536),  -- For OpenAI embeddings
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_vector_store_collection ON vector_store(collection);
CREATE INDEX idx_vector_store_user_id ON vector_store(user_id);
CREATE INDEX idx_vector_store_metadata ON vector_store USING GIN(metadata);

-- HNSW index for similarity search
CREATE INDEX idx_vector_store_embedding ON vector_store 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_vector_store_embedding_1536 ON vector_store 
    USING hnsw (embedding_1536 vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## 📝 MIGRATION PLAN

### Phase 1: Setup (Week 1)
1. **Enable pgvector extension**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Create migration tables**
   - Run schema creation script
   - Set up performance parameters

3. **Update BiometricVectorStore class**
   ```python
   class BiometricVectorStore:
       def __init__(self, postgres_pool):
           self.pool = postgres_pool
           # Remove ChromaDB client
   ```

### Phase 2: Data Migration (Week 1-2)
1. **Export from ChromaDB**
   ```python
   # Migration script
   async def migrate_collection(collection_name):
       # Get all documents from ChromaDB
       docs = chromadb_collection.get()
       
       # Insert into PostgreSQL
       for doc in docs:
           await insert_vector(doc)
   ```

2. **Verify migration**
   - Count documents in both systems
   - Sample similarity searches
   - Performance benchmarks

### Phase 3: Cutover (Week 2)
1. **Update application code**
   - Switch vector store to PostgreSQL
   - Remove ChromaDB dependencies

2. **Remove ChromaDB container**
   - Update docker-compose files
   - Clean up volumes

---

## 🔧 IMPLEMENTATION DETAILS

### Updated Vector Store Class
```python
class PgVectorStore:
    """PostgreSQL-based vector store using pgvector"""
    
    async def add_documents(
        self, 
        collection: str,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str]
    ):
        """Add documents with embeddings"""
        embeddings = self.embedding_model.encode(documents)
        
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO vector_store 
                (collection, document_id, content, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (document_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                [(collection, id, doc, meta, emb) 
                 for id, doc, meta, emb in zip(ids, documents, metadatas, embeddings)]
            )
    
    async def similarity_search(
        self,
        collection: str,
        query_embedding: List[float],
        k: int = 5
    ) -> List[dict]:
        """Find similar documents"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT 
                    document_id,
                    content,
                    metadata,
                    1 - (embedding <=> $1) as similarity
                FROM vector_store
                WHERE collection = $2
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                query_embedding, collection, k
            )
            
            return [dict(r) for r in results]
```

---

## ⚡ PERFORMANCE OPTIMIZATION

### PostgreSQL Configuration
```sql
-- Set work memory for vector operations
ALTER SYSTEM SET work_mem = '512MB';

-- Configure HNSW parameters
SET hnsw.ef_search = 100;  -- Higher = better recall, slower
SET hnsw.iterative_scan = relaxed_order;

-- Enable parallel workers for index builds
SET max_parallel_maintenance_workers = 4;
```

### Connection Pooling
```python
# Use existing asyncpg pool with proper size
postgres_pool = await asyncpg.create_pool(
    dsn=DATABASE_URL,
    min_size=10,
    max_size=50,
    command_timeout=60
)
```

---

## 🧪 TESTING STRATEGY

### Performance Tests
1. **Insertion Speed**
   - Bulk insert 10k documents
   - Compare with ChromaDB baseline

2. **Query Performance**
   - k-NN search benchmarks
   - Various k values (5, 10, 50)

3. **Memory Usage**
   - Monitor PostgreSQL memory
   - Compare with ChromaDB container

### Functional Tests
```python
async def test_vector_operations():
    # Test CRUD operations
    await store.add_documents(...)
    results = await store.similarity_search(...)
    assert len(results) == k
    
    # Test updates
    await store.update_document(...)
    
    # Test deletions
    await store.delete_collection(...)
```

---

## 📊 ROLLBACK PLAN

If issues arise:
1. **Keep ChromaDB running** during migration
2. **Feature flag** for vector store selection
3. **Parallel run** for 24-48 hours
4. **Quick switch** back if needed

```python
# Feature flag approach
VECTOR_STORE = os.getenv("VECTOR_STORE_TYPE", "chromadb")

if VECTOR_STORE == "pgvector":
    vector_store = PgVectorStore(postgres_pool)
else:
    vector_store = ChromaDBStore(chroma_client)
```

---

## ✅ SUCCESS CRITERIA

- [ ] All ChromaDB data migrated to PostgreSQL
- [ ] Query performance within 20% of ChromaDB
- [ ] No data loss during migration
- [ ] Application fully functional with pgvector
- [ ] ChromaDB container removed
- [ ] Documentation updated

---

## 🎯 BENEFITS REALIZED

1. **Simplified Architecture**
   - One less database to backup
   - Unified query language (SQL)
   - Single connection pool

2. **Better Integration**
   - JOIN vectors with user data
   - Transactional consistency
   - Unified access control

3. **Cost Savings**
   - ~2GB RAM freed (ChromaDB container)
   - Reduced CPU from fewer services
   - Simplified monitoring

---

*This migration will strengthen AUREN's data cohesion and operational efficiency.* 