#!/usr/bin/env python3
"""
Live Simulation for AUREN Dashboard
Generates realistic health optimization events to showcase the system
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timezone
import uuid
import random
import math

class AURENLiveSimulation:
    """Simulates a realistic health optimization journey"""
    
    def __init__(self):
        self.client = None
        self.session_id = f"live_demo_{int(datetime.now().timestamp())}"
        self.user_id = "demo_user_001"
        self.conversation_count = 0
        self.memory_count = 0
        self.hypothesis_count = 0
        self.total_cost = 0.0
        
        # Health metrics that evolve
        self.current_hrv = 35
        self.current_stress = 7.5
        self.current_sleep = 0.72
        self.current_recovery = 45
        
    async def connect(self):
        """Connect to Redis"""
        self.client = redis.from_url("redis://localhost:6379")
        print("✅ Connected to Redis")
        
    async def emit_event(self, event_data: dict, stream_type: str = "critical"):
        """Emit an event to Redis stream"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            **event_data
        }
        
        stream = f"auren:events:{stream_type}"
        await self.client.xadd(stream, {"data": json.dumps(event)})
        
    async def simulate_conversation(self, user_message: str, ai_response: str):
        """Simulate a conversation exchange"""
        self.conversation_count += 1
        
        # User message
        await self.emit_event({
            "event_type": "conversation_event",
            "payload": {
                "direction": "user_to_system",
                "message": user_message,
                "conversation_id": self.conversation_count
            }
        }, "operational")
        
        await asyncio.sleep(0.5)
        
        # AI thinking
        await self.emit_event({
            "event_type": "agent_execution_started",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {
                "query": user_message,
                "context": "Analyzing biometric patterns..."
            },
            "performance_metrics": {"latency_ms": random.randint(100, 200)}
        })
        
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Tool usage
        tools = ["Biometric Analyzer", "Pattern Recognition", "Recovery Calculator", "HRV Analyzer"]
        tool = random.choice(tools)
        tool_cost = random.uniform(0.0002, 0.0008)
        
        await self.emit_event({
            "event_type": "tool_usage",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {
                "tool_name": tool,
                "tool_input": "Analyzing current state",
                "estimated_cost": tool_cost
            },
            "performance_metrics": {"token_cost": tool_cost}
        }, "operational")
        
        await asyncio.sleep(0.3)
        
        # AI response
        response_cost = random.uniform(0.001, 0.003)
        self.total_cost += response_cost + tool_cost
        
        await self.emit_event({
            "event_type": "agent_execution_completed",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {
                "response_preview": ai_response[:100] + "..."
            },
            "performance_metrics": {
                "latency_ms": random.randint(800, 1500),
                "token_cost": response_cost,
                "tokens_used": int(response_cost / 0.00003 * 1000),
                "success": True,
                "confidence_score": random.uniform(0.85, 0.95)
            }
        })
        
        await asyncio.sleep(0.3)
        
        # System response
        await self.emit_event({
            "event_type": "conversation_event",
            "payload": {
                "direction": "system_to_user",
                "message": ai_response,
                "conversation_id": self.conversation_count
            }
        }, "operational")
        
    async def simulate_memory_formation(self, content: str, confidence: float = 0.9):
        """Simulate memory formation"""
        self.memory_count += 1
        
        await self.emit_event({
            "event_type": "memory_operation",
            "payload": {
                "operation": "store",
                "memory_type": random.choice(["observation", "insight", "pattern"]),
                "content": content,
                "confidence": confidence,
                "memory_id": f"mem_{self.memory_count}"
            },
            "performance_metrics": {"success": True}
        }, "operational")
        
    async def simulate_hypothesis(self, hypothesis: str, confidence: float = 0.85):
        """Simulate hypothesis formation and validation"""
        self.hypothesis_count += 1
        
        # Form hypothesis
        await self.emit_event({
            "event_type": "hypothesis_event",
            "payload": {
                "status": "formed",
                "hypothesis": hypothesis,
                "domain": "neuroscience",
                "confidence": confidence,
                "hypothesis_id": f"hyp_{self.hypothesis_count}"
            },
            "performance_metrics": {"confidence_score": confidence}
        }, "analytical")
        
        await asyncio.sleep(2)
        
        # Validate hypothesis
        if random.random() > 0.3:  # 70% chance of validation
            await self.emit_event({
                "event_type": "hypothesis_event",
                "payload": {
                    "status": "validated",
                    "hypothesis": hypothesis,
                    "evidence_count": random.randint(3, 8),
                    "confidence": min(confidence + 0.1, 0.95),
                    "hypothesis_id": f"hyp_{self.hypothesis_count}"
                },
                "performance_metrics": {"confidence_score": confidence + 0.1}
            }, "analytical")
            
    async def simulate_biometric_update(self):
        """Simulate gradual biometric improvements"""
        # Gradual improvements
        self.current_hrv += random.uniform(0.5, 2.0)
        self.current_stress -= random.uniform(0.1, 0.3)
        self.current_sleep += random.uniform(0.01, 0.03)
        self.current_recovery += random.uniform(1, 3)
        
        # Keep within bounds
        self.current_hrv = min(self.current_hrv, 55)
        self.current_stress = max(self.current_stress, 4.2)
        self.current_sleep = min(self.current_sleep, 0.86)
        self.current_recovery = min(self.current_recovery, 75)
        
        await self.emit_event({
            "event_type": "biometric_analysis",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {
                "metrics_available": ["hrv", "stress", "sleep_efficiency", "recovery"],
                "current_values": {
                    "hrv": round(self.current_hrv, 1),
                    "stress": round(self.current_stress, 1),
                    "sleep_efficiency": round(self.current_sleep, 2),
                    "recovery_score": round(self.current_recovery, 0)
                },
                "analysis_depth": "comprehensive"
            },
            "performance_metrics": {"success": True}
        }, "operational")
        
    async def run_simulation(self, duration_minutes: int = 2):
        """Run the complete simulation"""
        print(f"\n🚀 Starting {duration_minutes}-minute health optimization simulation...")
        print("📊 Watch your dashboard at: http://localhost:8000/dashboard")
        print("="*60)
        
        # Simulation timeline
        conversations = [
            ("I've been feeling really stressed lately", 
             "I see your stress levels are elevated at 7.5/10. Your HRV of 35ms confirms this. Let me help you with evidence-based stress reduction protocols."),
            
            ("What can I do to improve my HRV?",
             "Based on your patterns, I recommend starting with 4-7-8 breathing exercises. Also, cold exposure for 2-3 minutes can boost HRV by 15-20%."),
            
            ("My sleep has been terrible",
             "Your sleep efficiency is at 72%, which is below optimal. I notice you're experiencing high sympathetic activation before bed. Let's work on your wind-down routine."),
            
            ("Should I try cold plunges?",
             "Given your current recovery score of 45%, start with cold showers (30-60 seconds) before progressing to full immersion. This will help HRV without overtaxing your system."),
            
            ("I tried the breathing exercises",
             "Excellent! I'm already seeing improvements - your HRV has increased to 42ms. Continue this practice, especially before stressful meetings."),
            
            ("How's my recovery looking?",
             "Your recovery score has improved to 58%! The combination of better sleep hygiene and stress management is working. Keep this consistency."),
            
            ("Can I increase my training?",
             "With your HRV now at 49ms and recovery at 65%, you can add one more moderate intensity session. Monitor morning HRV to avoid overtraining."),
            
            ("I feel so much better!",
             "The data confirms it! HRV up 40%, stress down to 5.2/10, sleep efficiency at 83%. This is what happens when we optimize systematically!")
        ]
        
        # Key insights to form as memories
        insights = [
            "Morning HRV measurements provide best baseline accuracy",
            "Cold exposure before bed improves deep sleep by 23%",
            "4-7-8 breathing reduces acute stress response within 90 seconds",
            "Optimal recovery window identified: 48-72 hours between high-intensity sessions",
            "Caffeine cutoff at 2 PM improves sleep latency by 18 minutes",
            "Zone 2 cardio enhances HRV recovery rate by 35%"
        ]
        
        # Hypotheses to test
        hypotheses = [
            "Cold exposure timing affects sleep quality differently based on chronotype",
            "HRV improvement rate correlates with baseline fitness level",
            "Stress reduction techniques have compounding effects over 30 days",
            "Recovery scores predict training adaptation capacity"
        ]
        
        start_time = datetime.now()
        end_time = start_time.timestamp() + (duration_minutes * 60)
        
        conversation_idx = 0
        insight_idx = 0
        hypothesis_idx = 0
        
        while datetime.now().timestamp() < end_time:
            # Emit events in realistic sequence
            
            # Conversations (most frequent)
            if conversation_idx < len(conversations) and random.random() > 0.3:
                user_msg, ai_response = conversations[conversation_idx]
                await self.simulate_conversation(user_msg, ai_response)
                conversation_idx += 1
                
            # Biometric updates
            if random.random() > 0.6:
                await self.simulate_biometric_update()
                
            # Memory formation
            if insight_idx < len(insights) and random.random() > 0.7:
                await self.simulate_memory_formation(insights[insight_idx])
                insight_idx += 1
                
            # Hypothesis formation
            if hypothesis_idx < len(hypotheses) and random.random() > 0.8:
                await self.simulate_hypothesis(hypotheses[hypothesis_idx])
                hypothesis_idx += 1
                
            # System health check
            if random.random() > 0.95:
                await self.emit_event({
                    "event_type": "system_health",
                    "payload": {
                        "status": "healthy",
                        "metrics": {
                            "memory_usage_mb": random.randint(100, 300),
                            "cpu_percent": random.randint(5, 25),
                            "active_sessions": 1,
                            "redis_latency_ms": random.randint(1, 5)
                        }
                    }
                }, "analytical")
                
            # Wait between events
            await asyncio.sleep(random.uniform(2, 5))
            
            # Progress indicator
            elapsed = datetime.now().timestamp() - start_time.timestamp()
            progress = (elapsed / (duration_minutes * 60)) * 100
            print(f"\r⏱️  Progress: {progress:.0f}% | 💰 Cost: ${self.total_cost:.4f} | 🧠 Memories: {self.memory_count} | 🔬 Hypotheses: {self.hypothesis_count}", end="")
        
        print(f"\n\n✅ Simulation complete!")
        print(f"📊 Final stats:")
        print(f"   - Total cost: ${self.total_cost:.4f}")
        print(f"   - Conversations: {self.conversation_count}")
        print(f"   - Memories formed: {self.memory_count}")
        print(f"   - Hypotheses: {self.hypothesis_count}")
        print(f"   - HRV improved: {35}ms → {round(self.current_hrv, 1)}ms")
        print(f"   - Stress reduced: 7.5 → {round(self.current_stress, 1)}")
        
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()

async def main():
    """Run the simulation"""
    simulation = AURENLiveSimulation()
    
    try:
        await simulation.connect()
        await simulation.run_simulation(duration_minutes=3)
    finally:
        await simulation.cleanup()

if __name__ == "__main__":
    print("🧠 AUREN Live Dashboard Simulation")
    print("==================================")
    asyncio.run(main()) 