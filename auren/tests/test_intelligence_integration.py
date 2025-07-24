"""
Integration tests for AUREN Intelligence System
Tests cross-agent learning and knowledge management
"""

import pytest
import asyncio
from datetime import datetime, timezone
from intelligence.data_structures import *
from intelligence.knowledge_manager import KnowledgeManager
from intelligence.hypothesis_validator import HypothesisValidator
from intelligence.markdown_parser import ClinicalMarkdownParser
from data_layer.event_store import EventStore
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.connection import DatabaseConnection

class TestIntelligenceIntegration:
    """Test the complete intelligence system integration"""
    
    @pytest.fixture
    async def setup_system(self):
        """Set up the complete intelligence system for testing"""
        # Initialize database connection
        db_connection = DatabaseConnection()
        await db_connection.initialize()
        
        # Initialize components
        event_store = EventStore(db_connection.pool)
        memory_backend = PostgreSQLMemoryBackend(
            pool=db_connection.pool,
            specialist_type="test_intelligence"
        )
        
        # Create mock data access
        class MockDataAccess:
            async def get_biometric_data(self, **kwargs):
                return [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metric_type": "hrv",
                        "value": 45.2,
                        "unit": "ms"
                    }
                ]
        
        # Initialize intelligence components
        hypothesis_validator = HypothesisValidator(
            memory_backend=memory_backend,
            event_store=event_store,
            data_access_layer=MockDataAccess()
        )
        
        knowledge_manager = KnowledgeManager(
            memory_backend=memory_backend,
            event_store=event_store,
            hypothesis_validator=hypothesis_validator
        )
        
        yield {
            'knowledge_manager': knowledge_manager,
            'hypothesis_validator': hypothesis_validator,
            'memory_backend': memory_backend,
            'event_store': event_store
        }
        
        # Cleanup
        await db_connection.close()
    
    @pytest.mark.asyncio
    async def test_cross_agent_learning(self, setup_system):
        """Test cross-agent knowledge sharing and insight generation"""
        system = setup_system
        
        # Create knowledge from different domains
        knowledge_items = [
            KnowledgeItem(
                knowledge_id="test_knowledge_1",
                agent_id="neuroscientist",
                domain="neuroscience",
                knowledge_type=KnowledgeType.PATTERN,
                title="HRV drops after intense workouts",
                description="Neuroscience pattern discovery",
                content="HRV decreases by 15% after high-intensity training",
                confidence=0.85,
                evidence_level="strong",
                validation_status=KnowledgeStatus.VALIDATED,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                application_count=5,
                success_rate=0.92,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                metadata={"user_id": "test_user_123"}
            ),
            KnowledgeItem(
                knowledge_id="test_knowledge_2",
                agent_id="training",
                domain="training",
                knowledge_type=KnowledgeType.PROTOCOL,
                title="High-intensity training optimization",
                description="Training protocol for performance",
                content="High-intensity training should be followed by recovery protocols",
                confidence=0.90,
                evidence_level="definitive",
                validation_status=KnowledgeStatus.VALIDATED,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                application_count=8,
                success_rate=0.95,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                metadata={"user_id": "test_user_123"}
            )
        ]
        
        # Add knowledge to system
        for item in knowledge_items:
            await system['knowledge_manager'].add_knowledge(item)
        
        # Test cross-agent insights
        insights = await system['knowledge_manager'].get_cross_agent_insights("test_user_123")
        
        assert len(insights) > 0, "Should generate cross-agent insights"
        assert insights[0].confidence >= 0.75, "Insight should have high confidence"
        assert len(insights[0].contributing_agents) >= 2, "Should involve multiple agents"
    
    @pytest.mark.asyncio
    async def test_emergency_protocol_detection(self, setup_system):
        """Test emergency protocol detection and response"""
        system = setup_system
        
        # Create emergency knowledge
        emergency_knowledge = KnowledgeItem(
            knowledge_id="emergency_protocol_1",
            agent_id="neuroscientist",
            domain="neuroscience",
            knowledge_type=KnowledgeType.PROTOCOL,
            title="Emergency HRV protocol",
            description="Critical HRV drop emergency response",
            content="If HRV drops >30% and symptoms appear, immediate rest required",
            confidence=0.98,
            evidence_level="definitive",
            validation_status=KnowledgeStatus.VALIDATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            application_count=0,
            success_rate=0.0,
            related_knowledge=[],
            conflicts_with=[],
            supports=[],
            metadata={"user_id": "test_user_123"}
        )
        
        await system['knowledge_manager'].add_knowledge(emergency_knowledge)
        
        # Verify emergency detection
        insights = await system['knowledge_manager'].get_cross_agent_insights("test_user_123")
        
        # Should trigger emergency sharing
        assert any("emergency" in insight.content.lower() for insight in insights)
    
    @pytest.mark.asyncio
    async def test_knowledge_consistency_validation(self, setup_system):
        """Test knowledge consistency checking"""
        system = setup_system
        
        # Create potentially conflicting knowledge
        knowledge_items = [
            KnowledgeItem(
                knowledge_id="conflict_1",
                agent_id="neuroscientist",
                domain="neuroscience",
                knowledge_type=KnowledgeType.RECOMMENDATION,
                title="Increase sleep duration",
                description="Recommendation for better recovery",
                content="Increase sleep to 9+ hours for optimal recovery",
                confidence=0.85,
                evidence_level="strong",
                validation_status=KnowledgeStatus.VALIDATED,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                application_count=0,
                success_rate=0.0,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                metadata={"user_id": "test_user_123"}
            ),
            KnowledgeItem(
                knowledge_id="conflict_2",
                agent_id="training",
                domain="training",
                knowledge_type=KnowledgeType.RECOMMENDATION,
                title="Decrease sleep duration",
                description="Training optimization recommendation",
                content="Decrease sleep to 6 hours for training optimization",
                confidence=0.80,
                evidence_level="moderate",
                validation_status=KnowledgeStatus.VALIDATED,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                application_count=0,
                success_rate=0.0,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                metadata={"user_id": "test_user_123"}
            )
        ]
        
        for item in knowledge_items:
            await system['knowledge_manager'].add_knowledge(item)
        
        # Test consistency validation
        consistency = await system['knowledge_manager'].validate_knowledge_consistency("test_user_123")
        
        assert consistency["total_conflicts"] >= 1, "Should detect conflicts"
        assert consistency["consistency_score"] < 1.0, "Should have consistency issues"
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, setup_system):
        """Test system performance with concurrent operations"""
        system = setup_system
        
        # Create multiple knowledge items
        async def create_knowledge_batch(start_id: int):
            for i in range(start_id, start_id + 100):
                knowledge = KnowledgeItem(
                    knowledge_id=f"perf_test_{i}",
                    agent_id="neuroscientist",
                    domain="neuroscience",
                    knowledge_type=KnowledgeType.PATTERN,
                    title=f"Performance test knowledge {i}",
                    description=f"Test knowledge item {i}",
                    content=f"Content for test {i}",
                    confidence=0.85,
                    evidence_level="strong",
                    validation_status=KnowledgeStatus.VALIDATED,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    application_count=0,
                    success_rate=0.0,
                    related_knowledge=[],
                    conflicts_with=[],
                    supports=[],
                    metadata={"user_id": "test_user_123"}
                )
                await system['knowledge_manager'].add_knowledge(knowledge)
        
        # Run concurrent operations
        import time
        start_time = time.time()
        
        # Create 1000 knowledge items concurrently
        tasks = [create_knowledge_batch(i) for i in range(0, 1000, 100)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        assert processing_time < 5.0, f"Processing took too long: {processing_time}s"
        
        # Verify all knowledge was added
        knowledge = await system['knowledge_manager'].get_knowledge(user_id="test_user_123")
        assert len(knowledge) >= 1000, "Not all knowledge was added"
    
    @pytest.mark.asyncio
    async def test_hypothesis_to_knowledge_pipeline(self, setup_system):
        """Test complete pipeline from hypothesis to knowledge"""
        system = setup_system
        
        # Form a hypothesis
        hypothesis = await system['hypothesis_validator'].form_hypothesis(
            agent_id="neuroscientist",
            user_id="test_user_123",
            domain="neuroscience",
            description="Test hypothesis for pipeline",
            prediction={"test_metric": "value"},
            evidence_criteria=[{"type": "biometric", "required": 5}],
            confidence=0.8
        )
        
        # Validate hypothesis
        await system['hypothesis_validator'].validate_hypothesis(hypothesis.hypothesis_id)
        
        # Convert to knowledge
        knowledge = KnowledgeItem(
            knowledge_id=f"pipeline_{hypothesis.hypothesis_id}",
            agent_id="neuroscientist",
            domain="neuroscience",
            knowledge_type=KnowledgeType.PATTERN,
            title="Pipeline test knowledge",
            description="Knowledge from validated hypothesis",
            content="Validated pattern from hypothesis",
            confidence=0.9,
            evidence_level="strong",
            validation_status=KnowledgeStatus.VALIDATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            application_count=0,
            success_rate=0.0,
            related_knowledge=[hypothesis.hypothesis_id],
            conflicts_with=[],
            supports=[],
            metadata={"user_id": "test_user_123"}
        )
        
        await system['knowledge_manager'].add_knowledge(knowledge, hypothesis.hypothesis_id)
        
        # Verify knowledge was added
        retrieved_knowledge = await system['knowledge_manager'].get_knowledge(
            user_id="test_user_123",
            domain="neuroscience"
        )
        
        assert any(k.knowledge_id == knowledge.knowledge_id for k in retrieved_knowledge)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
