#!/usr/bin/env python3
"""Generate continuous events for AUREN dashboard demonstration"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime, timezone
import uuid
import random
import time

class DashboardEventGenerator:
    def __init__(self):
        self.client = None
        self.session_id = f"demo_{int(time.time())}"
        self.conversation_count = 0
        self.memory_count = 0
        self.hypothesis_count = 0
        
    async def connect(self):
        self.client = redis.from_url("redis://localhost:6379")
        print("✅ Connected to Redis")
        
    async def emit_event(self, event_data: dict, stream_type: str = "critical"):
        """Emit event to Redis stream"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "user_id": "demo_user",
            **event_data
        }
        
        stream = f"auren:events:{stream_type}"
        await self.client.xadd(stream, {"data": json.dumps(event)})
        
    async def generate_conversation(self):
        """Generate a conversation exchange"""
        self.conversation_count += 1
        
        messages = [
            "What's my current HRV trend?",
            "How's my recovery looking?",
            "Should I train hard today?",
            "My sleep was poor last night",
            "I'm feeling stressed"
        ]
        
        user_msg = random.choice(messages)
        
        # User message
        await self.emit_event({
            "event_type": "conversation_event",
            "payload": {
                "direction": "user_to_system",
                "message": user_msg,
                "conversation_id": self.conversation_count
            }
        }, "operational")
        
        print(f"💬 User: {user_msg}")
        await asyncio.sleep(0.5)
        
        # Agent thinking
        await self.emit_event({
            "event_type": "agent_execution_started",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {"query": user_msg}
        })
        
        await asyncio.sleep(1)
        
        # Tool usage
        tool = random.choice(["HRV Analyzer", "Recovery Calculator", "Sleep Analyzer"])
        await self.emit_event({
            "event_type": "tool_usage",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {
                "tool_name": tool,
                "estimated_cost": random.uniform(0.0001, 0.0005)
            },
            "performance_metrics": {"token_cost": random.uniform(0.0001, 0.0005)}
        }, "operational")
        
        # Agent completion
        await self.emit_event({
            "event_type": "agent_execution_completed",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "performance_metrics": {
                "latency_ms": random.randint(500, 1500),
                "token_cost": random.uniform(0.001, 0.003),
                "success": True,
                "confidence_score": random.uniform(0.8, 0.95)
            }
        })
        
        print(f"🧠 Agent completed analysis")
        
    async def generate_memory(self):
        """Generate memory formation event"""
        self.memory_count += 1
        
        insights = [
            "User responds well to morning cold exposure",
            "HRV improves after 20min meditation",
            "Sleep quality correlates with evening screen time",
            "Recovery enhanced by zone 2 cardio"
        ]
        
        await self.emit_event({
            "event_type": "memory_operation",
            "payload": {
                "operation": "store",
                "memory_type": "insight",
                "content": random.choice(insights),
                "confidence": random.uniform(0.8, 0.95)
            }
        }, "operational")
        
        print(f"💾 Memory #{self.memory_count} formed")
        
    async def generate_hypothesis(self):
        """Generate hypothesis event"""
        self.hypothesis_count += 1
        
        hypotheses = [
            "Cold exposure timing affects sleep quality",
            "HRV predicts training readiness",
            "Stress correlates with inflammation markers"
        ]
        
        await self.emit_event({
            "event_type": "hypothesis_event",
            "payload": {
                "status": "formed",
                "hypothesis": random.choice(hypotheses),
                "confidence": random.uniform(0.7, 0.9)
            }
        }, "analytical")
        
        print(f"🔬 Hypothesis #{self.hypothesis_count} formed")
        
    async def generate_cost_event(self):
        """Generate cost tracking event"""
        await self.emit_event({
            "event_type": "cost_event",
            "payload": {
                "token_count": random.randint(100, 500),
                "cost_usd": random.uniform(0.001, 0.005),
                "model": "gpt-4"
            }
        }, "operational")
        
    async def run_continuous(self, duration_seconds: int = 60):
        """Run continuous event generation"""
        print(f"\n🚀 Generating events for {duration_seconds} seconds...")
        print("Watch your dashboard at: http://localhost:8000/dashboard")
        print("="*50)
        
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Generate different event types with varying probabilities
            rand = random.random()
            
            if rand < 0.4:  # 40% chance
                await self.generate_conversation()
            elif rand < 0.6:  # 20% chance
                await self.generate_memory()
            elif rand < 0.75:  # 15% chance
                await self.generate_hypothesis()
            elif rand < 0.9:  # 15% chance
                await self.generate_cost_event()
            
            # Wait between events
            await asyncio.sleep(random.uniform(1, 3))
            
        print(f"\n✅ Generated:")
        print(f"   - {self.conversation_count} conversations")
        print(f"   - {self.memory_count} memories")
        print(f"   - {self.hypothesis_count} hypotheses")
        
    async def cleanup(self):
        if self.client:
            await self.client.aclose()

async def main():
    generator = DashboardEventGenerator()
    try:
        await generator.connect()
        await generator.run_continuous(duration_seconds=120)  # Run for 2 minutes
    finally:
        await generator.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 