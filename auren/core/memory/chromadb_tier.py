"""
ChromaDB Tier - Semantic Memory Search
Implements Tier 3 of the three-tier memory system with vector embeddings
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SemanticMemoryItem:
    """Memory item with semantic embedding"""
    memory_id: str
    agent_id: str
    user_id: str
    content: Dict[str, Any]
    memory_type: str
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    relevance_score: Optional[float] = None


class ChromaDBTier:
    """
    Tier 3: Semantic Memory Search with Vector Embeddings
    
    Features:
    - Semantic similarity search across all memories
    - Automatic embedding generation
    - Cross-domain knowledge discovery
    - Pattern recognition through embeddings
    - WebSocket event emission
    """
    
    def __init__(self,
                 persist_directory: str = "/auren/data/chromadb",
                 collection_name: str = "auren_memories",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 event_emitter=None):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.event_emitter = event_emitter
        self._initialized = False
        
        # ChromaDB client
        self.client = None
        self.collection = None
        
        # Embedding model
        self.embedding_model = None
    
    async def initialize(self):
        """Initialize ChromaDB and embedding model"""
        if self._initialized:
            return
        
        try:
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Create or get collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            self._initialized = True
            logger.info("ChromaDB tier initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB tier: {e}")
            raise
    
    async def store_memory(self,
                          memory_id: str,
                          agent_id: str,
                          user_id: str,
                          content: Dict[str, Any],
                          memory_type: str,
                          confidence: float = 1.0,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store memory with semantic embedding
        
        Args:
            memory_id: Unique memory identifier
            agent_id: Agent storing the memory
            user_id: Associated user
            content: Memory content
            memory_type: Type of memory
            confidence: Confidence score
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract text for embedding
            text_content = self._extract_text_content(content)
            if not text_content:
                logger.warning(f"No text content found for memory {memory_id}")
                return False
            
            # Generate embedding
            embedding = await self._generate_embedding(text_content)
            
            # Prepare metadata
            chroma_metadata = {
                "memory_id": memory_id,
                "agent_id": agent_id,
                "user_id": user_id,
                "memory_type": memory_type,
                "confidence": float(confidence),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "semantic_tier"
            }
            
            # Add custom metadata
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_metadata[f"meta_{key}"] = value
            
            # Store in ChromaDB
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding.tolist()],
                documents=[text_content],
                metadatas=[chroma_metadata]
            )
            
            # Emit event
            if self.event_emitter:
                await self._emit_memory_event('memory_stored', {
                    'memory_id': memory_id,
                    'agent_id': agent_id,
                    'user_id': user_id,
                    'memory_type': memory_type
                })
            
            logger.debug(f"Stored memory {memory_id} in ChromaDB tier")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory in ChromaDB: {e}")
            return False
    
    async def semantic_search(self,
                             query: str,
                             user_id: Optional[str] = None,
                             agent_id: Optional[str] = None,
                             memory_type: Optional[str] = None,
                             limit: int = 10,
                             min_confidence: float = 0.0) -> List[SemanticMemoryItem]:
        """
        Perform semantic search across memories
        
        Args:
            query: Search query
            user_id: Filter by user
            agent_id: Filter by agent
            memory_type: Filter by memory type
            limit: Maximum results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of semantically similar memories
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Build filter
            where_clause = {}
            if user_id:
                where_clause["user_id"] = user_id
            if agent_id:
                where_clause["agent_id"] = agent_id
            if memory_type:
                where_clause["memory_type"] = memory_type
            if min_confidence > 0:
                where_clause["confidence"] = {"$gte": min_confidence}
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                where=where_clause if where_clause else None,
                n_results=limit
            )
            
            # Parse results
            memories = []
            if results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Convert distance to similarity score (1 - cosine distance)
                    similarity_score = 1 - distance
                    
                    # Reconstruct content from document
                    content = self._parse_document_content(results['documents'][0][i])
                    
                    memory = SemanticMemoryItem(
                        memory_id=memory_id,
                        agent_id=metadata['agent_id'],
                        user_id=metadata['user_id'],
                        content=content,
                        memory_type=metadata['memory_type'],
                        confidence=metadata['confidence'],
                        created_at=datetime.fromisoformat(metadata['created_at']),
                        metadata={k[5:]: v for k, v in metadata.items() if k.startswith('meta_')},
                        relevance_score=similarity_score
                    )
                    memories.append(memory)
            
            # Emit search event
            if self.event_emitter:
                await self._emit_memory_event('semantic_search', {
                    'query': query,
                    'results_count': len(memories),
                    'filters': where_clause
                })
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []
    
    async def find_related_memories(self,
                                   memory_id: str,
                                   limit: int = 10,
                                   cross_user: bool = False) -> List[SemanticMemoryItem]:
        """
        Find memories semantically related to a given memory
        
        Args:
            memory_id: Source memory ID
            limit: Maximum results
            cross_user: Include memories from other users
            
        Returns:
            List of related memories
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get the source memory
            result = self.collection.get(ids=[memory_id])
            
            if not result['ids']:
                logger.warning(f"Memory {memory_id} not found in ChromaDB")
                return []
            
            # Get embedding of source memory
            source_embedding = result['embeddings'][0] if result['embeddings'] else None
            if not source_embedding:
                logger.warning(f"No embedding found for memory {memory_id}")
                return []
            
            source_metadata = result['metadatas'][0]
            
            # Build filter
            where_clause = {}
            if not cross_user:
                where_clause["user_id"] = source_metadata['user_id']
            
            # Search for similar memories (excluding the source)
            results = self.collection.query(
                query_embeddings=[source_embedding],
                where=where_clause if where_clause else None,
                n_results=limit + 1  # Get extra to exclude source
            )
            
            # Parse results, excluding source memory
            memories = []
            if results['ids'] and results['ids'][0]:
                for i, found_id in enumerate(results['ids'][0]):
                    if found_id == memory_id:
                        continue
                    
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance
                    
                    content = self._parse_document_content(results['documents'][0][i])
                    
                    memory = SemanticMemoryItem(
                        memory_id=found_id,
                        agent_id=metadata['agent_id'],
                        user_id=metadata['user_id'],
                        content=content,
                        memory_type=metadata['memory_type'],
                        confidence=metadata['confidence'],
                        created_at=datetime.fromisoformat(metadata['created_at']),
                        metadata={k[5:]: v for k, v in metadata.items() if k.startswith('meta_')},
                        relevance_score=similarity_score
                    )
                    memories.append(memory)
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find related memories: {e}")
            return []
    
    async def discover_patterns(self,
                               user_id: str,
                               min_cluster_size: int = 3,
                               similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Discover patterns in user's memories through clustering
        
        Args:
            user_id: User to analyze
            min_cluster_size: Minimum memories per pattern
            similarity_threshold: Minimum similarity for clustering
            
        Returns:
            List of discovered patterns
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get all user memories
            results = self.collection.get(
                where={"user_id": user_id}
            )
            
            if not results['ids'] or len(results['ids']) < min_cluster_size:
                return []
            
            embeddings = np.array(results['embeddings'])
            
            # Simple clustering using cosine similarity
            patterns = []
            processed = set()
            
            for i, embedding in enumerate(embeddings):
                if i in processed:
                    continue
                
                # Find similar memories
                similarities = np.dot(embeddings, embedding)
                similar_indices = np.where(similarities >= similarity_threshold)[0]
                
                if len(similar_indices) >= min_cluster_size:
                    # Create pattern
                    pattern_memories = []
                    for idx in similar_indices:
                        processed.add(idx)
                        pattern_memories.append({
                            'memory_id': results['ids'][idx],
                            'memory_type': results['metadatas'][idx]['memory_type'],
                            'confidence': results['metadatas'][idx]['confidence'],
                            'similarity': float(similarities[idx])
                        })
                    
                    # Analyze pattern
                    memory_types = [m['memory_type'] for m in pattern_memories]
                    dominant_type = max(set(memory_types), key=memory_types.count)
                    
                    patterns.append({
                        'pattern_id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'size': len(pattern_memories),
                        'dominant_type': dominant_type,
                        'average_confidence': np.mean([m['confidence'] for m in pattern_memories]),
                        'cohesion': float(np.mean([m['similarity'] for m in pattern_memories])),
                        'memories': pattern_memories,
                        'discovered_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Emit pattern discovery event
            if self.event_emitter and patterns:
                await self._emit_memory_event('patterns_discovered', {
                    'user_id': user_id,
                    'patterns_count': len(patterns),
                    'total_memories_clustered': len(processed)
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to discover patterns: {e}")
            return []
    
    async def update_memory_embedding(self,
                                     memory_id: str,
                                     new_content: Dict[str, Any]) -> bool:
        """Update memory content and re-generate embedding"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get existing memory
            result = self.collection.get(ids=[memory_id])
            
            if not result['ids']:
                logger.warning(f"Memory {memory_id} not found for update")
                return False
            
            metadata = result['metadatas'][0]
            
            # Extract new text content
            text_content = self._extract_text_content(new_content)
            if not text_content:
                return False
            
            # Generate new embedding
            new_embedding = await self._generate_embedding(text_content)
            
            # Update in ChromaDB
            self.collection.update(
                ids=[memory_id],
                embeddings=[new_embedding.tolist()],
                documents=[text_content]
            )
            
            # Emit update event
            if self.event_emitter:
                await self._emit_memory_event('embedding_updated', {
                    'memory_id': memory_id,
                    'agent_id': metadata['agent_id'],
                    'user_id': metadata['user_id']
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory embedding: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from ChromaDB"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get memory metadata before deletion
            result = self.collection.get(ids=[memory_id])
            
            if not result['ids']:
                return False
            
            metadata = result['metadatas'][0]
            
            # Delete from ChromaDB
            self.collection.delete(ids=[memory_id])
            
            # Emit deletion event
            if self.event_emitter:
                await self._emit_memory_event('memory_deleted', {
                    'memory_id': memory_id,
                    'agent_id': metadata['agent_id'],
                    'user_id': metadata['user_id']
                })
            
            logger.debug(f"Deleted memory {memory_id} from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory from ChromaDB: {e}")
            return False
    
    async def get_memory_stats(self,
                              user_id: Optional[str] = None,
                              agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get ChromaDB tier statistics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Build filter
            where_clause = {}
            if user_id:
                where_clause["user_id"] = user_id
            if agent_id:
                where_clause["agent_id"] = agent_id
            
            # Get filtered results
            if where_clause:
                results = self.collection.get(where=where_clause)
                filtered_count = len(results['ids']) if results['ids'] else 0
            else:
                filtered_count = self.collection.count()
            
            # Get total count
            total_count = self.collection.count()
            
            # Get memory type distribution
            all_results = self.collection.get()
            memory_types = {}
            
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    mem_type = metadata.get('memory_type', 'unknown')
                    memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            stats = {
                'total_memories': total_count,
                'filtered_memories': filtered_count,
                'memory_types': memory_types,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name,
                'user_id': user_id,
                'agent_id': agent_id
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {}
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embedding_model.encode,
                text
            )
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def _extract_text_content(self, content: Dict[str, Any]) -> str:
        """Extract text from content dictionary"""
        text_parts = []
        
        def extract_text(obj, prefix=""):
            if isinstance(obj, str):
                text_parts.append(f"{prefix}{obj}")
            elif isinstance(obj, (int, float, bool)):
                text_parts.append(f"{prefix}{str(obj)}")
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    extract_text(value, f"{key}: ")
            elif isinstance(obj, list):
                for item in obj:
                    extract_text(item)
        
        extract_text(content)
        return " | ".join(text_parts)
    
    def _parse_document_content(self, document: str) -> Dict[str, Any]:
        """Parse document back to content dictionary"""
        # Simple parsing - in production, store JSON separately
        content = {}
        
        parts = document.split(" | ")
        for part in parts:
            if ": " in part:
                key, value = part.split(": ", 1)
                content[key] = value
            else:
                content['text'] = part
        
        return content
    
    async def _emit_memory_event(self, event_type: str, data: Dict[str, Any]):
        """Emit memory event for dashboard"""
        if self.event_emitter:
            try:
                await self.event_emitter.emit({
                    'type': f'chromadb_tier_{event_type}',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data
                })
            except Exception as e:
                logger.error(f"Failed to emit event: {e}")
    
    async def promote_from_postgres(self, memory_data: Dict[str, Any]) -> bool:
        """Promote memory from PostgreSQL to ChromaDB for semantic search"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Store in ChromaDB
            success = await self.store_memory(
                memory_id=memory_data['memory_id'],
                agent_id=memory_data['agent_id'],
                user_id=memory_data['user_id'],
                content=memory_data['content'],
                memory_type=memory_data['memory_type'],
                confidence=memory_data.get('confidence', 1.0),
                metadata={
                    **memory_data.get('metadata', {}),
                    'promoted_from': 'postgresql',
                    'original_created_at': memory_data.get('created_at')
                }
            )
            
            if success:
                logger.info(f"Promoted memory {memory_data['memory_id']} to ChromaDB")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to promote memory to ChromaDB: {e}")
            return False
    
    async def close(self):
        """Clean up resources"""
        # ChromaDB doesn't require explicit closing
        logger.info("ChromaDB tier closed")
