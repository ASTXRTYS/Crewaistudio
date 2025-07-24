"""
Knowledge Manager for AUREN
Manages knowledge storage, retrieval, and validation
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from intelligence.data_structures import (
    KnowledgeItem, KnowledgeStatus, KnowledgeType, 
    create_knowledge_id, LearningMetrics
)
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore, EventStreamType

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    Manages the complete knowledge lifecycle:
    - Storage and retrieval of validated knowledge
    - Knowledge validation and confidence scoring
    - Cross-agent knowledge sharing
    - Knowledge graph construction
    """
    
    def __init__(self, memory_backend: PostgreSQLMemoryBackend, event_store: EventStore, hypothesis_validator=None):
        self.memory_backend = memory_backend
        self.event_store = event_store
        self.hypothesis_validator = hypothesis_validator
    
    async def add_knowledge(self, knowledge: KnowledgeItem) -> str:
        """
        Add validated knowledge to the system
        
        Args:
            knowledge: The knowledge item to add
            
        Returns:
            Knowledge ID
        """
        
        # Store in memory backend
        knowledge_id = await self.memory_backend.store_memory(
            agent_id=knowledge.agent_id,
            memory_type="knowledge",
            content={
                "knowledge_id": knowledge.knowledge_id,
                "domain": knowledge.domain,
                "knowledge_type": knowledge.knowledge_type.value,
                "title": knowledge.title,
                "description": knowledge.description,
                "content": knowledge.content,
                "confidence": knowledge.confidence,
                "evidence_sources": knowledge.evidence_sources,
                "validation_status": knowledge.validation_status.value,
                "related_knowledge": knowledge.related_knowledge,
                "conflicts_with": knowledge.conflicts_with,
                "supports": knowledge.supports,
                "application_count": knowledge.application_count,
                "success_rate": knowledge.success_rate,
                "last_applied": knowledge.last_applied.isoformat() if knowledge.last_applied else None,
                "metadata": knowledge.metadata
            },
            user_id=knowledge.user_id,
            confidence=knowledge.confidence
        )
        
        # Log knowledge addition event
        await self.event_store.append_event(
            stream_id=knowledge.user_id,
            stream_type=EventStreamType.KNOWLEDGE,
            event_type="knowledge_added",
            payload={
                "knowledge_id": knowledge.knowledge_id,
                "agent_id": knowledge.agent_id,
                "domain": knowledge.domain,
                "knowledge_type": knowledge.knowledge_type.value,
                "confidence": knowledge.confidence,
                "validation_status": knowledge.validation_status.value
            }
        )
        
        logger.info(f"Added knowledge: {knowledge.title} for user {knowledge.user_id}")
        return knowledge_id
    
    async def get_knowledge(self,
                          user_id: str,
                          domain: Optional[str] = None,
                          knowledge_type: Optional[KnowledgeType] = None,
                          validation_status: Optional[KnowledgeStatus] = None,
                          min_confidence: float = 0.0,
                          limit: int = 100,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge with filtering
        
        Args:
            user_id: The user whose knowledge to retrieve
            domain: Optional domain filter
            knowledge_type: Optional knowledge type filter
            validation_status: Optional validation status filter
            min_confidence: Minimum confidence threshold
            limit: Maximum number of knowledge items
            offset: Pagination offset
            
        Returns:
            List of knowledge items
        """
        
        # Get memories from backend
        memories = await self.memory_backend.get_memories(
            user_id=user_id,
            memory_type="knowledge",
            min_confidence=min_confidence,
            limit=limit,
            offset=offset
        )
        
        # Filter by additional criteria
        filtered_knowledge = []
        for memory in memories:
            content = memory['content']
            
            # Apply domain filter
            if domain and content.get('domain') != domain:
                continue
            
            # Apply knowledge type filter
            if knowledge_type and content.get('knowledge_type') != knowledge_type.value:
                continue
            
            # Apply validation status filter
            if validation_status and content.get('validation_status') != validation_status.value:
                continue
            
            # Convert back to knowledge format
            knowledge = {
                "knowledge_id": content['knowledge_id'],
                "agent_id": memory['agent_id'],
                "user_id": user_id,
                "domain": content['domain'],
                "knowledge_type": content['knowledge_type'],
                "title": content['title'],
                "description": content['description'],
                "content": content['content'],
                "confidence": content['confidence'],
                "evidence_sources": content['evidence_sources'],
                "validation_status": content['validation_status'],
                "related_knowledge": content['related_knowledge'],
                "conflicts_with": content['conflicts_with'],
                "supports": content['supports'],
                "application_count": content['application_count'],
                "success_rate": content['success_rate'],
                "last_applied": content['last_applied'],
                "created_at": memory['created_at'].isoformat(),
                "updated_at": memory['updated_at'].isoformat(),
                "metadata": content['metadata']
            }
            
            filtered_knowledge.append(knowledge)
        
        return filtered_knowledge
    
    async def update_knowledge(self,
                             knowledge_id: str,
                             user_id: str,
                             updates: Dict[str, Any]) -> bool:
        """
        Update existing knowledge
        
        Args:
            knowledge_id: The knowledge ID to update
            user_id: The user who owns the knowledge
            updates: Dictionary of updates
            
        Returns:
            True if updated successfully
        """
        
        # Find the knowledge item
        knowledge_list = await self.get_knowledge(user_id=user_id)
        knowledge_item = None
        
        for knowledge in knowledge_list:
            if knowledge['knowledge_id'] == knowledge_id:
                knowledge_item = knowledge
                break
        
        if not knowledge_item:
            return False
        
        # Update the knowledge
        for key, value in updates.items():
            if key in knowledge_item:
                knowledge_item[key] = value
        
        # Update in memory backend
        memory_id = None
        memories = await self.memory_backend.get_memories(
            user_id=user_id,
            memory_type="knowledge"
        )
        
        for memory in memories:
            if memory['content']['knowledge_id'] == knowledge_id:
                memory_id = memory['id']
                break
        
        if memory_id:
            await self.memory_backend.update_memory(
                memory_id=memory_id,
                content={
                    "knowledge_id": knowledge_item['knowledge_id'],
                    "domain": knowledge_item['domain'],
                    "knowledge_type": knowledge_item['knowledge_type'],
                    "title": knowledge_item['title'],
                    "description": knowledge_item['description'],
                    "content": knowledge_item['content'],
                    "confidence": knowledge_item['confidence'],
                    "evidence_sources": knowledge_item['evidence_sources'],
                    "validation_status": knowledge_item['validation_status'],
                    "related_knowledge": knowledge_item['related_knowledge'],
                    "conflicts_with": knowledge_item['conflicts_with'],
                    "supports": knowledge_item['supports'],
                    "application_count": knowledge_item['application_count'],
                    "success_rate": knowledge_item['success_rate'],
                    "last_applied": knowledge_item['last_applied'],
                    "metadata": knowledge_item['metadata']
                }
            )
            
            # Log update event
            await self.event_store.append_event(
                stream_id=user_id,
                stream_type=EventStreamType.KNOWLEDGE,
                event_type="knowledge_updated",
                payload={
                    "knowledge_id": knowledge_id,
                    "updates": updates
                }
            )
            
            return True
        
        return False
    
    async def validate_knowledge(self,
                              knowledge_id: str,
                              user_id: str,
                              validation_data: Dict[str, Any]) -> bool:
        """
        Validate knowledge with new evidence
        
        Args:
            knowledge_id: The knowledge ID to validate
            user_id: The user who owns the knowledge
            validation_data: Validation data
            
        Returns:
            True if validated successfully
        """
        
        # Get current knowledge
        knowledge_list = await self.get_knowledge(user_id=user_id)
        knowledge_item = None
        
        for knowledge in knowledge_list:
            if knowledge['knowledge_id'] == knowledge_id:
                knowledge_item = knowledge
                break
        
        if not knowledge_item:
            return False
        
        # Update validation status
        updates = {
            "validation_status": "validated",
            "confidence": validation_data.get('confidence', knowledge_item['confidence']),
            "success_rate": validation_data.get('success_rate', knowledge_item['success_rate']),
            "application_count": knowledge_item['application_count'] + 1
        }
        
        return await self.update_knowledge(knowledge_id, user_id, updates)
    
    async def get_knowledge_graph(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Build knowledge graph showing relationships between knowledge
        
        Args:
            user_id: The user whose knowledge to graph
            
        Returns:
            Knowledge graph with relationships
        """
        
        knowledge_list = await self.get_knowledge(user_id=user_id)
        
        # Build graph with relationships
        graph = []
        knowledge_map = {k['knowledge_id']: k for k in knowledge_list}
        
        for knowledge in knowledge_list:
            # Add relationship information
            knowledge_graph = {
                **knowledge,
                "relationships": {
                    "related": [knowledge_map.get(rid, {"knowledge_id": rid}) for rid in knowledge['related_knowledge']],
                    "conflicts": [knowledge_map.get(cid, {"knowledge_id": cid}) for cid in knowledge['conflicts_with']],
                    "supports": [knowledge_map.get(sid, {"knowledge_id": sid}) for sid in knowledge['supports']]
                }
            }
            graph.append(knowledge_graph)
        
        return graph
    
    async def get_cross_agent_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get insights that emerge from cross-agent collaboration
        
        Args:
            user_id: The user to analyze
            
        Returns:
            Cross-agent insights
        """
        
        knowledge_list = await self.get_knowledge(user_id=user_id)
        
        # Group by domain
        domain_knowledge = {}
        for knowledge in knowledge_list:
            domain = knowledge['domain']
            if domain not in domain_knowledge:
                domain_knowledge[domain] = []
            domain_knowledge[domain].append(knowledge)
        
        # Generate insights from cross-domain patterns
        insights = []
        
        # Example: Find patterns that appear across domains
        for domain, knowledge_items in domain_knowledge.items():
            if len(knowledge_items) > 1:
                insight = {
                    "insight_id": f"cross_domain_{domain}_{len(insights)}",
                    "agents_involved": list(set([k['agent_id'] for k in knowledge_items])),
                    "user_id": user_id,
                    "insight_type": "cross_domain_pattern",
                    "description": f"Found {len(knowledge_items)} knowledge items in {domain} domain",
                    "supporting_knowledge": [k['knowledge_id'] for k in knowledge_items],
                    "confidence": sum([k['confidence'] for k in knowledge_items]) / len(knowledge_items),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                insights.append(insight)
        
        return insights
    
    async def search_knowledge(self,
                            user_id: str,
                            query: str,
                            domain: Optional[str] = None,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search knowledge using full-text search
        
        Args:
            user_id: The user whose knowledge to search
            query: Search query
            domain: Optional domain filter
            limit: Maximum results
            
        Returns:
            Matching knowledge items
        """
        
        # Get all knowledge
        knowledge_list = await self.get_knowledge(user_id=user_id)
        
        # Filter by query
        filtered = []
        for knowledge in knowledge_list:
            # Search in title and description
            search_text = f"{knowledge['title']} {knowledge['description']}".lower()
            if query.lower() in search_text:
                filtered.append(knowledge)
        
        # Apply domain filter
        if domain:
            filtered = [k for k in filtered if k['domain'] == domain]
        
        # Sort by confidence
        filtered.sort(key=lambda x: x['confidence'], reverse=True)
        
        return filtered[:limit]
    
    async def get_learning_metrics(self, user_id: str) -> LearningMetrics:
        """
        Get learning metrics for a user
        
        Args:
            user_id: The user to analyze
            
        Returns:
            Learning metrics
        """
        
        knowledge_list = await self.get_knowledge(user_id=user_id)
        
        # Calculate metrics
        total_knowledge = len(knowledge_list)
        knowledge_by_domain = {}
        total_confidence = 0.0
        
        for knowledge in knowledge_list:
            domain = knowledge['domain']
            if domain not in knowledge_by_domain:
                knowledge_by_domain[domain] = 0
            knowledge_by_domain[domain] += 1
            total_confidence += knowledge['confidence']
        
        average_confidence = total_confidence / total_knowledge if total_knowledge > 0 else 0.0
        
        # Get hypothesis metrics from event store
        hypothesis_events = await self.event_store.get_events(
            stream_id=user_id,
            stream_type=EventStreamType.HYPOTHESIS,
            limit=1000
        )
        
        total_hypotheses = len(hypothesis_events)
        validated_hypotheses = len([e for e in hypothesis_events if e['event_data'].get('status') == 'validated'])
        invalidated_hypotheses = len([e for e in hypothesis_events if e['event_data'].get('status') == 'invalidated'])
        active_hypotheses = len([e for e in hypothesis_events if e['event_data'].get('status') == 'active'])
        
        # Calculate learning rate
        learning_rate = (validated_hypotheses / total_hypotheses) if total_hypotheses > 0 else 0.0
        
        return LearningMetrics(
            total_hypotheses=total_hypotheses,
            validated_hypotheses=validated_hypotheses,
            invalidated_hypotheses=invalidated_hypotheses,
            active_hypotheses=active_hypotheses,
            total_knowledge=total_knowledge,
            knowledge_by_domain=knowledge_by_domain,
            average_confidence=average_confidence,
            learning_rate=learning_rate,
            last_updated=datetime.now(timezone.utc)
        )
    
    async def cleanup_expired_knowledge(self, user_id: str) -> int:
        """
        Clean up expired knowledge
        
        Args:
            user_id: The user whose knowledge to clean
            
        Returns:
            Number of knowledge items cleaned
        """
        
        return await self.memory_backend.cleanup_expired_memories()
    
    async def get_knowledge_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary of knowledge for a user
        
        Args:
            user_id: The user to summarize
            
        Returns:
            Knowledge summary
        """
        
        metrics = await self.get_learning_metrics(user_id)
        stats = await self.memory_backend.get_memory_stats(user_id)
        
        return {
            "learning_metrics": asdict(metrics),
            "memory_stats": stats,
            "user_id": user_id,
            "summary_generated_at": datetime.now(timezone.utc).isoformat()
        }
