"""
Unit tests for token tracking system
"""

import pytest
import asyncio
from datetime import date
from src.monitoring.token_tracker import TokenTracker, BudgetExceededException
from src.monitoring.tokenizer_service import TokenizerService


@pytest.fixture
async def tracker():
    """Create a token tracker instance"""
    t = TokenTracker()
    await t.connect()
    yield t
    await t.disconnect()


@pytest.fixture
def tokenizer():
    """Create a tokenizer service instance"""
    return TokenizerService()


class TestTokenTracker:
    @pytest.mark.asyncio
    async def test_track_usage(self, tracker):
        """Test basic usage tracking"""
        usage = await tracker.track_usage(
            user_id="test_user",
            agent_id="test_agent",
            task_id="test_task",
            conversation_id="test_conv",
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            completion_tokens=50
        )
        
        assert usage.total_tokens == 150
        assert usage.cost_usd > 0
        assert usage.model == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_budget_enforcement(self, tracker):
        """Test that budget limits are enforced"""
        user_id = "budget_test_user"
        
        # Set a tiny limit
        await tracker.set_user_limit(user_id, 0.001)
        
        # This should exceed the budget
        with pytest.raises(BudgetExceededException):
            await tracker.track_usage(
                user_id=user_id,
                agent_id="test_agent",
                task_id="test_task",
                conversation_id="test_conv",
                model="gpt-4",
                prompt_tokens=1000,
                completion_tokens=1000
            )
    
    @pytest.mark.asyncio
    async def test_user_stats(self, tracker):
        """Test user statistics retrieval"""
        user_id = "stats_test_user"
        
        # Track some usage
        await tracker.track_usage(
            user_id=user_id,
            agent_id="test_agent",
            task_id="test_task",
            conversation_id="test_conv",
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            completion_tokens=50
        )
        
        # Get stats
        stats = await tracker.get_user_stats(user_id)
        
        assert stats["user_id"] == user_id
        assert stats["today"]["spent"] > 0
        assert stats["today"]["remaining"] < stats["today"]["limit"]


class TestTokenizerService:
    def test_count_tokens(self, tokenizer):
        """Test token counting"""
        text = "Hello, this is a test message for token counting."
        count = tokenizer.count_tokens("gpt-4", text)
        
        assert count > 0
        assert count < len(text)  # Should be less than character count
    
    def test_model_support(self, tokenizer):
        """Test different model support"""
        text = "Test message"
        
        # Should handle various models
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "llama-3.1-70b"]
        for model in models:
            count = tokenizer.count_tokens(model, text)
            assert count > 0
