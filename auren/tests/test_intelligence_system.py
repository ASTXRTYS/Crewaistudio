"""
Comprehensive tests for AUREN Intelligence System
Tests knowledge management, hypothesis validation, and cross-agent collaboration
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from intelligence.data_structures import (
    KnowledgeItem, KnowledgeType, KnowledgeStatus,
    Hypothesis, HypothesisStatus, ValidationStrength,
    create_knowledge_id, create_hypothesis_id
)
from intelligence.knowledge_manager import KnowledgeManager
from intelligence.hypothesis_validator import HypothesisValidator
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore, EventStreamType


class TestIntelligenceSystem:
    """Test suite for AUREN intelligence system"""
    
    @pytest.fixture
    async def test_user_id(self):
        """Test user ID"""
        return "test_user_123"
    
    @pytest.fixture
    async def system_components(self):
        """Initialize system components for testing"""
        # Initialize memory backend
        memory_backend = PostgreSQLMemoryBackend()
        await memory_backend.initialize()
        
        # Initialize event store
        event_store = EventStore()
        await event_store.initialize()
        
        # Initialize hypothesis validator
        hypothesis_validator = HypothesisValidator(event_store)
        
        # Initialize knowledge manager
        knowledge_manager = KnowledgeManager(
            memory_backend=memory_backend,
            event_store=event_store,
            hypothesis_validator=hypothesis_validator
        )
        
        yield {
            'memory_backend': memory_backend,
            'event_store': event_store,
            'hypothesis_validator': hypothesis_validator,
            'knowledge_manager': knowledge_manager
        }
        
        # Cleanup
        await memory_backend.cleanup()
        await event_store.cleanup()
    
    @pytest.mark.asyncio
    async def test_knowledge_item_creation(self, system_components, test_user_id):
        """Test knowledge item creation and storage"""
        
        knowledge_manager = system_components['knowledge_manager']
        
        # Create test knowledge
        knowledge = KnowledgeItem(
            knowledge_id=create_knowledge_id(),
            agent_id="test_agent",
            user_id=test_user_id,
            domain="neuroscience",
            knowledge_type=KnowledgeType.PATTERN,
            title="Test HRV Pattern",
            description="Test pattern for HRV improvement",
            content={"test": "data"},
            confidence=0.85,
            evidence_sources=["test_source"],
            validation_status=KnowledgeStatus.VALIDATED,
            related_knowledge=[],
            conflicts_with=[],
            supports=[],
            application_count=5,
            success_rate=0.90,
            last_applied=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata={"test": True}
        )
        
        # Add knowledge
        knowledge_id = await knowledge_manager.add_knowledge(knowledge)
        assert knowledge_id is not None
        
        # Retrieve knowledge
        retrieved = await knowledge_manager.get_knowledge(user_id=test_user_id)
        assert len(retrieved) > 0
        
        # Verify content
        retrieved_item = retrieved[0]
        assert retrieved_item['title'] == "Test HRV Pattern"
        assert retrieved_item['confidence'] == 0.85
        assert retrieved_item['domain'] == "neuroscience"
    
    @pytest.mark.asyncio
    async def test_hypothesis_validation(self, system_components, test_user_id):
        """Test hypothesis validation workflow"""
        
        hypothesis_validator = system_components['hypothesis_validator']
        
        # Create test hypothesis
        hypothesis = Hypothesis(
            hypothesis_id=create_hypothesis_id(),
            agent_id="test_agent",
            user_id=test_user_id,
            domain="neuroscience",
            description="Test hypothesis about HRV patterns",
            prediction={"expected": "pattern"},
            confidence=0.75,
            evidence_criteria=[{"type": "hrv", "minimum_days": 7}],
            formed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            status=HypothesisStatus.FORMED,
            metadata={"test": True}
        )
        
        # Add supporting evidence
        await hypothesis_validator.add_evidence(
            hypothesis_id=hypothesis.hypothesis_id,
            user_id=test_user_id,
            evidence_type="hrv",
            data={"value": 15, "supports": True},
            confidence=0.9,
            supports_hypothesis=True,
            strength=ValidationStrength.STRONG
        )
        
        # Add contradicting evidence
        await hypothesis_validator.add_evidence(
            hypothesis_id=hypothesis.hypothesis_id,
            user_id=test_user_id,
            evidence_type="hrv",
            data={"value": 5, "supports": False},
            confidence=0.7,
            supports_hypothesis=False,
            strength=ValidationStrength.MODERATE
        )
        
        # Validate hypothesis
        result = await hypothesis_validator.validate_hypothesis(hypothesis, test_user_id)
        
        assert result.hypothesis_id == hypothesis.hypothesis_id
        assert result.validation_score > 0.0
        assert result.supporting_evidence == 1
        assert result.contradicting_evidence == 1
    
    @pytest.mark.asyncio
    async def test_knowledge_graph_construction(self, system_components, test_user_id):
        """Test knowledge graph construction"""
        
        knowledge_manager = system_components['knowledge_manager']
        
        # Create related knowledge items
        domains = ["neuroscience", "nutrition", "training", "sleep"]
        
        for domain in domains:
            knowledge = KnowledgeItem(
                knowledge_id=create_knowledge_id(),
                agent_id=f"{domain}_agent",
                user_id=test_user_id,
                domain=domain,
                knowledge_type=KnowledgeType.PATTERN,
                title=f"{domain.title()} Pattern",
                description=f"Pattern for {domain}",
                content={"domain": domain},
                confidence=0.85,
                evidence_sources=[f"{domain}_source"],
                validation_status=KnowledgeStatus.VALIDATED,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                application_count=1,
                success_rate=0.9,
                last_applied=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata={}
            )
            
            await knowledge_manager.add_knowledge(knowledge)
        
        # Build knowledge graph
        graph = await knowledge_manager.get_knowledge_graph(test_user_id)
        
        assert len(graph) == 4
        assert all(k['user_id'] == test_user_id for k in graph)
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, system_components, test_user_id):
        """Test performance benchmarks"""
        
        knowledge_manager = system_components['knowledge_manager']
        
        # Create large dataset
        start_time = datetime.now()
        
        for i in range(50):  # Reduced for faster testing
            knowledge = KnowledgeItem(
                knowledge_id=create_knowledge_id(),
                agent_id="test_agent",
                user_id=test_user_id,
                domain="neuroscience",
                knowledge_type=KnowledgeType.PATTERN,
                title=f"Performance Test {i}",
                description=f"Performance test pattern {i}",
                content={"perf": i},
                confidence=0.85,
                evidence_sources=["perf_test"],
                validation_status=KnowledgeStatus.VALIDATED,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                application_count=1,
                success_rate=0.9,
                last_applied=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata={}
            )
            
            await knowledge_manager.add_knowledge(knowledge)
        
        # Test retrieval performance
        retrieval_start = datetime.now()
        knowledge_list = await knowledge_manager.get_knowledge(user_id=test_user_id, limit=25)
        retrieval_end = datetime.now()
        
        retrieval_time = (retrieval_end - retrieval_start).total_seconds()
        
        assert len(knowledge_list) == 25
        assert retrieval_time < 2.0  # Should be sub-2 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, system_components, test_user_id):
        """Test concurrent operations"""
        
        knowledge_manager = system_components['knowledge_manager']
        
        # Create concurrent tasks
        async def add_knowledge_task(task_id):
            knowledge = KnowledgeItem(
                knowledge_id=create_knowledge_id(),
                agent_id=f"agent_{task_id}",
                user_id=test_user_id,
                domain="neuroscience",
                knowledge_type=KnowledgeType.PATTERN,
                title=f"Concurrent Test {task_id}",
                description=f"Concurrent test {task_id}",
                content={"concurrent": task_id},
                confidence=0.85,
                evidence_sources=["concurrent"],
                validation_status=KnowledgeStatus.VALIDATED,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                application_count=1,
                success_rate=0.9,
                last_applied=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata={}
            )
            
            return await knowledge_manager.add_knowledge(knowledge)
        
        # Run concurrent operations
        tasks = [add_knowledge_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, system_components, test_user_id):
        """Test error handling"""
        
        knowledge_manager = system_components['knowledge_manager']
        
        # Test invalid knowledge retrieval
        invalid_knowledge = await knowledge_manager.get_knowledge(user_id="invalid_user")
        assert len(invalid_knowledge) == 0


@pytest.mark.asyncio
async def test_system_integration():
    """Test complete system integration"""
    
    # Initialize system
    from intelligence.initialize_intelligence import IntelligenceSystemInitializer
    
    initializer = IntelligenceSystemInitializer()
    
    try:
        # Initialize components
        success = await initializer.initialize()
        assert success
        
        # Load knowledge base
        knowledge_count = await initializer.load_knowledge_base("integration_test")
        assert knowledge_count > 0
        
        # Create hypotheses
        hypothesis_count = await initializer.create_sample_hypotheses("integration_test")
        assert hypothesis_count > 0
        
        # Run system test
        results = await initializer.run_system_test("integration_test")
        assert results["status"] == "success"
        assert results["knowledge_loaded"] > 0
        assert results["hypotheses_created"] > 0
        
    finally:
        await initializer.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
