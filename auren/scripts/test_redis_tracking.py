#!/usr/bin/env python3
"""
Manual test script for token tracking system
Run this to verify everything is working correctly
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from auren.monitoring.token_tracker import TokenTracker, BudgetExceededException
from auren.monitoring.decorators import track_tokens
from auren.monitoring.tokenizer_service import TokenizerService


# Example CrewAI agent simulation
class MockNeuroscientist:
    def __init__(self):
        self.role = "neuroscientist"
        self.id = "neuro_001"
    
    @track_tokens(model="gpt-4")
    async def analyze_biometrics(self, prompt: str, user_id: str, conversation_id: str):
        """Simulated agent method with token tracking"""
        # Simulate LLM response
        await asyncio.sleep(0.1)  # Simulate API call
        return f"Based on your HRV data showing a 15% decline... [simulated response of {len(prompt)} chars]"


async def test_token_tracking():
    """Test the complete token tracking system"""
    print("🚀 Testing AUREN Token Tracking System\n")
    
    # Initialize components
    tracker = TokenTracker()
    tokenizer = TokenizerService()
    agent = MockNeuroscientist()
    
    # Test data
    user_id = "test_user_123"
    conversation_id = "conv_abc123"
    test_prompt = "Analyze my HRV data from the past week and identify any concerning patterns."
    
    print("1️⃣ Testing tokenizer service...")
    token_count = tokenizer.count_tokens("gpt-4", test_prompt)
    print(f"✅ Prompt tokens: {token_count}")
    
    print("\n2️⃣ Testing manual token tracking...")
    async with tracker:
        try:
            usage = await tracker.track_usage(
                user_id=user_id,
                agent_id="neuroscientist",
                task_id="task_001",
                conversation_id=conversation_id,
                model="gpt-4",
                prompt_tokens=token_count,
                completion_tokens=150,
                metadata={"test": True}
            )
            print(f"✅ Tracked usage: {usage.total_tokens} tokens, ${usage.cost_usd:.4f}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n3️⃣ Testing decorator-based tracking...")
    try:
        response = await agent.analyze_biometrics(
            prompt=test_prompt,
            user_id=user_id,
            conversation_id=conversation_id
        )
        print(f"✅ Agent response tracked successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n4️⃣ Testing user statistics...")
    async with tracker:
        stats = await tracker.get_user_stats(user_id)
        print(f"✅ User stats: ${stats['today']['spent']:.4f} / ${stats['today']['limit']:.2f}")
        print(f"   Remaining: ${stats['today']['remaining']:.4f} ({stats['today']['percentage']:.1f}% used)")
    
    print("\n5️⃣ Testing budget limits...")
    async with tracker:
        # Set a low limit for testing
        await tracker.set_user_limit(user_id, 0.01)  # $0.01 limit
        
        try:
            # This should exceed the budget
            await tracker.track_usage(
                user_id=user_id,
                agent_id="neuroscientist",
                task_id="task_002",
                conversation_id=conversation_id,
                model="gpt-4",
                prompt_tokens=1000,  # Will exceed $0.01
                completion_tokens=1000
            )
            print("❌ Budget check failed - should have raised exception")
        except BudgetExceededException as e:
            print(f"✅ Budget protection working: {e}")
    
    print("\n✨ Token tracking system test complete!")


if __name__ == "__main__":
    asyncio.run(test_token_tracking())
