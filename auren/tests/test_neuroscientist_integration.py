"""
Integration tests for AUREN Neuroscientist MVP
Tests the complete flow from biometric event to agent response

These tests validate:
- Database connectivity and schema
- HRV event processing through CEP
- Neuroscientist agent analysis
- Response time requirements (<2 seconds)
- Token tracking and cost management
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import time

from src.database.connection import DatabaseConnection, init_db, close_db
from src.agents.specialists.neuroscientist import Neuroscientist, create_neuroscientist
from src.cep.hrv_rules import HRVRuleEngine, BiometricEvent, HRVMonitoringService
from src.auren.ai.gateway import AIGateway
from src.auren.ai.crewai_gateway_adapter import CrewAIGatewayAdapter
from src.auren.monitoring.decorators import get_token_tracker
from src.config.settings import get_settings


class TestNeuroscientistIntegration:
    """
    Comprehensive integration tests for the Neuroscientist MVP
    
    These tests ensure all components work together correctly and
    meet performance requirements.
    """
    
    @classmethod
    async def setup_class(cls):
        """Initialize test environment"""
        # Get settings
        settings = get_settings()
        
        # Initialize database connection using settings
        await init_db(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            database=settings.database.name
        )
        
        # Initialize AI components
        cls.gateway = AIGateway()
        cls.adapter = CrewAIGatewayAdapter(cls.gateway)
        cls.neuroscientist = create_neuroscientist(cls.adapter)
        
        # Initialize CEP engine
        cls.rule_engine = HRVRuleEngine()
        
        # Token tracker for cost verification
        cls.token_tracker = get_token_tracker()
    
    @classmethod
    async def teardown_class(cls):
        """Clean up test environment"""
        await cls.gateway.shutdown()
        await close_db()
    
    @pytest.mark.asyncio
    async def test_database_connectivity(self):
        """Test that database is properly connected and schema is correct"""
        # Test basic connectivity
        version = await DatabaseConnection.fetchval("SELECT version()")
        assert version is not None
        assert "PostgreSQL" in version
        
        # Test required tables exist
        tables = await DatabaseConnection.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        table_names = [t['tablename'] for t in tables]
        required_tables = [
            'user_profiles',
            'user_facts',
            'conversation_insights',
            'biometric_baselines',
            'biometric_readings',
            'hypotheses'
        ]
        
        for table in required_tables:
            assert table in table_names, f"Required table '{table}' not found"
    
    @pytest.mark.asyncio
    async def test_test_data_present(self):
        """Verify test data was inserted correctly"""
        # Check test user exists
        test_user = await DatabaseConnection.fetchrow(
            "SELECT * FROM user_profiles WHERE external_id = 'test_user_001'"
        )
        assert test_user is not None
        
        # Check baseline exists
        baseline = await DatabaseConnection.fetchrow(
            "SELECT * FROM biometric_baselines WHERE user_id = 'test_user_001' AND metric_type = 'hrv'"
        )
        assert baseline is not None
        assert baseline['baseline_value'] == 60.0
        assert baseline['sample_count'] == 30
    
    @pytest.mark.asyncio
    async def test_hrv_drop_detection(self):
        """Test that CEP correctly detects HRV drops"""
        # Create test event with 25% drop from baseline
        event = BiometricEvent(
            user_id='test_user_001',
            metric_type='hrv',
            value=45.0,  # 25% drop from 60
            timestamp=datetime.utcnow(),
            device_source='apple_watch',
            quality_score=0.95,
            metadata={}
        )
        
        # Process event
        trigger = await self.rule_engine.process_event(event)
        
        # Verify trigger was generated
        assert trigger is not None
        assert trigger.trigger_type == 'hrv_drop_critical'
        assert trigger.severity >= 0.9
        assert trigger.percentage_drop == pytest.approx(25.0, rel=0.1)
        assert trigger.baseline_value == 60.0
        assert "Significant HRV drop" in trigger.recommendation
    
    @pytest.mark.asyncio
    async def test_moderate_hrv_drop_detection(self):
        """Test detection of moderate HRV drops"""
        # Create test event with 20% drop
        event = BiometricEvent(
            user_id='test_user_001',
            metric_type='hrv',
            value=48.0,  # 20% drop from 60
            timestamp=datetime.utcnow(),
            device_source='apple_watch',
            quality_score=0.95,
            metadata={}
        )
        
        trigger = await self.rule_engine.process_event(event)
        
        assert trigger is not None
        assert trigger.trigger_type == 'hrv_drop_moderate'
        assert 0.5 <= trigger.severity <= 0.7
        assert "Moderate HRV drop" in trigger.recommendation
    
    @pytest.mark.asyncio
    async def test_normal_variation_no_trigger(self):
        """Test that normal HRV variation doesn't trigger alerts"""
        # Create test event with small variation (within 1 stddev)
        event = BiometricEvent(
            user_id='test_user_001',
            metric_type='hrv',
            value=57.0,  # 5% drop, within normal variation
            timestamp=datetime.utcnow(),
            device_source='apple_watch',
            quality_score=0.95,
            metadata={}
        )
        
        trigger = await self.rule_engine.process_event(event)
        
        # Should not trigger
        assert trigger is None
    
    @pytest.mark.asyncio
    async def test_neuroscientist_analysis(self):
        """Test Neuroscientist agent HRV analysis"""
        # Prepare test HRV data
        hrv_data = {
            'current': 45.0,
            'daily_avg': 48.0,
            'baseline': 60.0,
            'timestamp': datetime.utcnow().isoformat(),
            'sleep_duration': 6.5,
            'sleep_quality': 6,
            'conversation_id': 'test_integration_001'
        }
        
        # Perform analysis
        start_time = time.time()
        
        result = await self.neuroscientist.analyze_hrv_data(
            user_id='test_user_001',
            hrv_data=hrv_data,
            conversation_id='test_integration_001'
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Verify response structure
        assert 'cns_status' in result
        assert 'recovery_state' in result
        assert 'training_guidance' in result
        assert 'action_items' in result
        assert 'full_analysis' in result
        
        # Verify appropriate recommendations for 25% drop
        assert result['cns_status'] in ['elevated_fatigue', 'moderate_fatigue']
        assert result['recovery_state'] == 'needs_recovery'
        assert result['training_guidance'] in ['rest', 'light']
        
        # Verify action items
        assert len(result['action_items']) > 0
        high_priority_items = [item for item in result['action_items'] if item['priority'] == 'high']
        assert len(high_priority_items) > 0
        
        # Verify response time requirement
        assert response_time < 2.0, f"Response time {response_time}s exceeds 2s requirement"
        
        print(f"\nNeuroscientist response time: {response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_conversation_insight_storage(self):
        """Test that insights are properly stored in the database"""
        # Run an analysis
        hrv_data = {
            'current': 50.0,
            'baseline': 60.0,
            'timestamp': datetime.utcnow().isoformat(),
            'sleep_duration': 7.0,
            'sleep_quality': 7,
            'conversation_id': 'test_storage_001'
        }
        
        await self.neuroscientist.analyze_hrv_data(
            user_id='test_user_001',
            hrv_data=hrv_data,
            conversation_id='test_storage_001'
        )
        
        # Check insight was stored
        insights = await DatabaseConnection.fetch("""
            SELECT * FROM conversation_insights
            WHERE user_id = 'test_user_001' 
            AND conversation_id = 'test_storage_001'
            AND agent_role = 'Neuroscientist'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        assert len(insights) > 0
        insight = insights[0]
        assert insight['insight_type'] == 'hrv_analysis'
        
        # Verify insight data
        insight_data = json.loads(insight['insight_data'])
        assert 'hrv_current' in insight_data
        assert 'cns_status' in insight_data
        assert 'recovery_state' in insight_data
    
    @pytest.mark.asyncio
    async def test_token_tracking(self):
        """Test that token usage is properly tracked"""
        # Get initial stats
        initial_stats = await self.token_tracker.get_user_stats('test_user_001')
        initial_cost = initial_stats['today']['spent']
        
        # Run analysis
        await self.neuroscientist.analyze_hrv_data(
            user_id='test_user_001',
            hrv_data={
                'current': 55.0,
                'baseline': 60.0,
                'timestamp': datetime.utcnow().isoformat(),
                'conversation_id': 'test_token_001'
            },
            conversation_id='test_token_001'
        )
        
        # Get updated stats
        updated_stats = await self.token_tracker.get_user_stats('test_user_001')
        updated_cost = updated_stats['today']['spent']
        
        # Verify cost was tracked
        assert updated_cost > initial_cost
        assert updated_stats['today']['remaining'] < updated_stats['today']['limit']
        
        print(f"\nToken cost for analysis: ${updated_cost - initial_cost:.4f}")
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete flow from biometric event to agent response"""
        # Simulate biometric event
        event = BiometricEvent(
            user_id='test_user_001',
            metric_type='hrv',
            value=42.0,  # 30% drop - critical
            timestamp=datetime.utcnow(),
            device_source='apple_watch',
            quality_score=0.95,
            metadata={'sleep_duration': 5.5, 'sleep_quality': 4}
        )
        
        # Process through CEP
        trigger = await self.rule_engine.process_event(event)
        assert trigger is not None
        assert trigger.severity >= 0.9
        
        # Simulate trigger handling - analyze with Neuroscientist
        hrv_data = {
            'current': trigger.current_value,
            'baseline': trigger.baseline_value,
            'timestamp': trigger.timestamp.isoformat(),
            'sleep_duration': event.metadata.get('sleep_duration', 7),
            'sleep_quality': event.metadata.get('sleep_quality', 7),
            'conversation_id': f'trigger_{trigger.timestamp.timestamp()}'
        }
        
        start_time = time.time()
        
        analysis_result = await self.neuroscientist.analyze_hrv_data(
            user_id=trigger.user_id,
            hrv_data=hrv_data,
            conversation_id=hrv_data['conversation_id']
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify complete flow
        assert analysis_result['cns_status'] == 'elevated_fatigue'
        assert analysis_result['recovery_state'] == 'needs_recovery'
        assert analysis_result['training_guidance'] == 'rest'
        
        # High priority recommendations for critical drop
        high_priority = [item for item in analysis_result['action_items'] 
                        if item['priority'] == 'high']
        assert len(high_priority) >= 2
        
        # Total flow time should be under 2 seconds
        assert total_time < 2.0, f"End-to-end time {total_time}s exceeds requirement"
        
        print(f"\nEnd-to-end flow completed in {total_time:.3f}s")
        print(f"Critical HRV drop (30%) correctly identified and analyzed")
        print(f"Generated {len(analysis_result['action_items'])} action items")
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self):
        """Test system performance under concurrent load"""
        # Create multiple analysis tasks
        tasks = []
        num_concurrent = 5
        
        for i in range(num_concurrent):
            hrv_data = {
                'current': 50 + i,
                'baseline': 60.0,
                'timestamp': datetime.utcnow().isoformat(),
                'sleep_duration': 7.0,
                'sleep_quality': 7,
                'conversation_id': f'concurrent_test_{i}'
            }
            
            task = self.neuroscientist.analyze_hrv_data(
                user_id='test_user_001',
                hrv_data=hrv_data,
                conversation_id=hrv_data['conversation_id']
            )
            tasks.append(task)
        
        # Run concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / num_concurrent
        
        # All should complete successfully
        assert len(results) == num_concurrent
        for result in results:
            assert 'cns_status' in result
            assert 'action_items' in result
        
        # Average time should still be reasonable
        assert avg_time < 2.0, f"Average concurrent time {avg_time}s exceeds requirement"
        
        print(f"\nConcurrent analysis ({num_concurrent} requests):")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average time per request: {avg_time:.3f}s")


def run_integration_tests():
    """
    Run all integration tests
    
    This is a convenience function for running tests outside of pytest.
    """
    import sys
    
    # Run with pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-s'  # Show print statements
    ])
    
    sys.exit(exit_code)


if __name__ == "__main__":
    run_integration_tests()
