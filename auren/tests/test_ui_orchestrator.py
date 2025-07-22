"""
Tests for AUREN UI Orchestrator
==============================

Comprehensive test suite for the AUREN cognitive twin interface.
Tests memory persistence, pattern recognition, and conversational intelligence.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.agents.ui_orchestrator import AUREN, create_auren, AURENContext


class TestAUREN:
    """Test suite for AUREN cognitive twin interface"""
    
    @pytest.fixture
    def mock_memory(self):
        """Mock memory system for testing"""
        mock = MagicMock()
        mock.store_interaction = AsyncMock()
        mock.get_sleep_data = AsyncMock(return_value={
            "avg_wake_time": datetime.now().replace(hour=7, minute=0),
            "sleep_quality": 85
        })
        mock.get_workout_recovery_status = AsyncMock(return_value={
            "cns_recovery": "good",
            "last_workout_date": datetime.now() - timedelta(days=2)
        })
        mock.get_total_days_tracked = AsyncMock(return_value=90)
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_pattern_analyzer(self):
        """Mock pattern analyzer for testing"""
        mock = MagicMock()
        mock.get_recent_patterns = AsyncMock(return_value={
            "optimal_workout_time": "morning",
            "energy_patterns": {"morning": 85, "evening": 65}
        })
        mock.get_nutrition_patterns = AsyncMock(return_value={
            "optimal_breakfast_macros": {"protein": 40, "carbs": 30, "fat": 15}
        })
        mock.get_workout_patterns = AsyncMock(return_value={
            "optimal_weekly_volume": 4,
            "optimal_training_split": "upper/lower"
        })
        mock.get_energy_patterns = AsyncMock(return_value={
            "optimal_workout_time": "morning"
        })
        mock.get_all_patterns = AsyncMock(return_value={"nutrition": {}, "workout": {}})
        return mock
    
    @pytest.fixture
    def mock_milestone_tracker(self):
        """Mock milestone tracker for testing"""
        mock = MagicMock()
        mock.get_recent_milestones = AsyncMock(return_value=[
            {
                "milestone": "100lb bench press",
                "description": "First time hitting triple digits",
                "days_to_achieve": 45
            }
        ])
        mock.get_all_milestones = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def mock_specialist_coordinator(self):
        """Mock specialist coordinator for testing"""
        mock = MagicMock()
        mock.get_recommendations = AsyncMock(return_value={
            "neuroscientist": "Focus on sleep quality",
            "nutritionist": "Increase protein intake"
        })
        return mock
    
    @pytest.fixture
    def mock_insight_generator(self):
        """Mock insight generator for testing"""
        mock = MagicMock()
        mock.get_recent_insights = AsyncMock(return_value=[
            {
                "insight": "morning workouts correlate with 25% higher energy",
                "data_points": 30
            }
        ])
        mock.get_current_insights = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def mock_protocol_manager(self):
        """Mock protocol manager for testing"""
        mock = MagicMock()
        return mock
    
    @pytest.fixture
    async def auren_instance(self, mock_memory, mock_pattern_analyzer, mock_milestone_tracker,
                           mock_specialist_coordinator, mock_insight_generator, mock_protocol_manager):
        """Create AUREN instance with mocked dependencies"""
        with patch('auren.src.agents.ui_orchestrator.CognitiveTwinMemory', return_value=mock_memory), \
             patch('auren.src.agents.ui_orchestrator.PatternAnalyzer', return_value=mock_pattern_analyzer), \
             patch('auren.src.agents.ui_orchestrator.MilestoneTracker', return_value=mock_milestone_tracker), \
             patch('auren.src.agents.ui_orchestrator.SpecialistCoordinator', return_value=mock_specialist_coordinator), \
             patch('auren.src.agents.ui_orchestrator.InsightGenerator', return_value=mock_insight_generator), \
             patch('auren.src.agents.ui_orchestrator.ProtocolManager', return_value=mock_protocol_manager):
            
            auren = AUREN(user_id="test_user")
            await auren.initialize()
            yield auren
            await auren.close()
    
    @pytest.mark.asyncio
    async def test_auren_initialization(self, auren_instance):
        """Test AUREN initialization"""
        auren = await anext(auren_instance)
        assert auren.name == "AUREN"
        assert auren.role == "Personal Optimization Companion"
        assert auren.user_id == "test_user"
        assert len(auren.attributes) == 6
    
    @pytest.mark.asyncio
    async def test_contextual_greeting_morning(self, auren_instance):
        """Test contextual morning greeting"""
        auren = await anext(auren_instance)
        
        # Mock datetime to be morning
        with patch('auren.src.agents.ui_orchestrator.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 8
            response = await auren.process_message("Good morning")
            
            assert "Good morning!" in response
            assert "CNS recovery" in response
            assert "How are you feeling today?" in response
    
    @pytest.mark.asyncio
    async def test_contextual_greeting_afternoon(self, auren_instance):
        """Test contextual afternoon greeting"""
        auren = await anext(auren_instance)
        
        with patch('auren.src.agents.ui_orchestrator.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 14
            response = await auren.process_message("Good afternoon")
            
            assert "Good afternoon!" in response
    
    @pytest.mark.asyncio
    async def test_contextual_greeting_evening(self, auren_instance):
        """Test contextual evening greeting"""
        auren = await anext(auren_instance)
        
        with patch('auren.src.agents.ui_orchestrator.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 19
            response = await auren.process_message("Good evening")
            
            assert "Good evening!" in response
    
    @pytest.mark.asyncio
    async def test_nutrition_query_with_context(self, auren_instance):
        """Test nutrition query with historical context"""
        auren = await anext(auren_instance)
        
        response = await auren.process_message("What should I eat for breakfast?")
        
        assert "protein-forward breakfast" in response
        assert "40g protein" in response
        assert "30g carbs" in response
        assert "15g fat" in response
    
    @pytest.mark.asyncio
    async def test_nutrition_query_with_presentation_context(self, auren_instance):
        """Test nutrition query with presentation context"""
        auren = await anext(auren_instance)
        
        response = await auren.process_message(
            "What should I eat for breakfast? I have an important presentation today"
        )
        
        assert "presentation today" in response
        assert "egg white omelet" in response
        assert "sweet potato hash" in response
        assert "10am crash" in response
    
    @pytest.mark.asyncio
    async def test_workout_query_with_patterns(self, auren_instance):
        """Test workout query with historical patterns"""
        auren = await anext(auren_instance)
        
        response = await auren.process_message("Should I workout today?")
        
        assert "4 training sessions per week" in response
        assert "upper/lower split" in response
        assert "CNS recovery indicators" in response
    
    @pytest.mark.asyncio
    async def test_progress_query_with_data(self, auren_instance):
        """Test progress query with historical data"""
        auren = await anext(auren_instance)
        
        response = await auren.process_message("How is my progress?")
        
        assert "Amazing progress" in response
        assert "lost" in response
        assert "gained" in response
        assert "lean mass" in response
    
    @pytest.mark.asyncio
    async def test_milestone_query_with_celebration(self, auren_instance):
        """Test milestone query with celebration"""
        auren = await anext(auren_instance)
        
        response = await auren.process_message("I hit a new milestone!")
        
        assert "Congratulations" in response
        assert "100lb bench press" in response
        assert "45 days" in response
    
    @pytest.mark.asyncio
    async def test_intent_analysis_nutrition(self, auren_instance):
        """Test nutrition intent detection"""
        auren = await anext(auren_instance)
        
        context = AURENContext(
            user_id="test_user",
            timestamp=datetime.now(),
            message="what should I eat for lunch",
            session_id="test_session",
            metadata={}
        )
        
        intent = await auren._analyze_intent(context)
        assert intent["type"] == "nutrition"
        assert "eat" in intent["keywords"]
    
    @pytest.mark.asyncio
    async def test_intent_analysis_workout(self, auren_instance):
        """Test workout intent detection"""
        auren = await anext(auren_instance)
        
        context = AURENContext(
            user_id="test_user",
            timestamp=datetime.now(),
            message="should I go to the gym today",
            session_id="test_session",
            metadata={}
        )
        
        intent = await auren._analyze_intent(context)
        assert intent["type"] == "workout"
        assert "gym" in intent["keywords"]
    
    @pytest.mark.asyncio
    async def test_intent_analysis_progress(self, auren_instance):
        """Test progress intent detection"""
        auren = await anext(auren_instance)
        
        context = AURENContext(
            user_id="test_user",
            timestamp=datetime.now(),
            message="how is my weight loss going",
            session_id="test_session",
            metadata={}
        )
        
        intent = await auren._analyze_intent(context)
        assert intent["type"] == "progress"
        assert "weight" in intent["keywords"]
    
    @pytest.mark.asyncio
    async def test_intent_analysis_milestone(self, auren_instance):
        """Test milestone intent detection"""
        auren = await anext(auren_instance)
        
        context = AURENContext(
            user_id="test_user",
            timestamp=datetime.now(),
            message="I reached my goal",
            session_id="test_session",
            metadata={}
        )
        
        intent = await auren._analyze_intent(context)
        assert intent["type"] == "milestone"
        assert "reached" in intent["keywords"]
    
    @pytest.mark.asyncio
    async def test_general_query_with_context(self, auren_instance):
        """Test general query with personalized context"""
        auren = await anext(auren_instance)
        
        response = await auren.process_message("tell me about my journey")
        
        assert "tracking your" in response
        assert "fascinating patterns" in response
    
    @pytest.mark.asyncio
    async def test_error_handling(self, auren_instance):
        """Test error handling in message processing"""
        auren = await anext(auren_instance)
        
        # Mock an exception in memory access
        with patch.object(auren.memory, 'get_sleep_data', side_effect=Exception("Test error")):
            response = await auren.process_message("Good morning")
            assert "How are you feeling today?" in response
    
    @pytest.mark.asyncio
    async def test_comprehensive_summary(self, auren_instance):
        """Test comprehensive summary generation"""
        auren = await anext(auren_instance)
        
        summary = await auren.get_comprehensive_summary()
        
        assert summary["user_id"] == "test_user"
        assert "total_days_tracked" in summary
        assert "patterns_discovered" in summary
        assert "milestones_achieved" in summary
        assert "current_insights" in summary
        assert "specialist_recommendations" in summary
    
    @pytest.mark.asyncio
    async def test_create_auren_function(self):
        """Test create_auren convenience function"""
        with patch('auren.src.agents.ui_orchestrator.AUREN') as mock_auren_class:
            mock_instance = AsyncMock()
            mock_instance.initialize = AsyncMock()
            mock_auren_class.return_value = mock_instance
            
            result = await create_auren("test_user")
            
            mock_auren_class.assert_called_once_with(user_id="test_user")
            mock_instance.initialize.assert_called_once()
            assert result == mock_instance
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self, auren_instance):
        """Test that interactions are stored in memory"""
        auren = await anext(auren_instance)
        
        await auren.process_message("test message")
        
        # Verify interaction was stored
        auren.memory.store_interaction.assert_called_once()
        call_args = auren.memory.store_interaction.call_args[0][0]
        assert call_args.user_id == "test_user"
        assert call_args.message == "test message"
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, auren_instance):
        """Test complete conversation flow"""
        auren = await anext(auren_instance)
        
        # Simulate a conversation
        responses = []
        messages = [
            "Good morning",
            "What should I eat for breakfast?",
            "How's my progress?",
            "Thanks AUREN!"
        ]
        
        for message in messages:
            response = await auren.process_message(message)
            responses.append(response)
            assert isinstance(response, str)
            assert len(response) > 0
        
        # Verify we got contextual responses
        assert any("Good morning" in resp for resp in responses)
        assert any("protein" in resp for resp in responses)
        assert any("progress" in resp.lower() for resp in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
