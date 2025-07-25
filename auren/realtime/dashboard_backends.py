"""
AUREN Dashboard Backend Services
Provides data APIs for the three core visualizations
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReasoningStep:
    """Represents a step in agent reasoning chain"""
    step_id: str
    agent_id: str
    timestamp: datetime
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: float = 0.0
    parent_step_id: Optional[str] = None
    children_step_ids: List[str] = None
    
    def __post_init__(self):
        if self.children_step_ids is None:
            self.children_step_ids = []


@dataclass
class CostMetrics:
    """Real-time cost tracking metrics"""
    total_cost: float = 0.0
    token_count: int = 0
    api_calls: int = 0
    cache_hits: int = 0
    cost_by_agent: Dict[str, float] = None
    cost_by_model: Dict[str, float] = None
    hourly_costs: List[float] = None
    
    def __post_init__(self):
        if self.cost_by_agent is None:
            self.cost_by_agent = {}
        if self.cost_by_model is None:
            self.cost_by_model = {}
        if self.hourly_costs is None:
            self.hourly_costs = []


@dataclass
class LearningMetrics:
    """Knowledge accumulation and learning metrics"""
    total_memories: int = 0
    memories_by_type: Dict[str, int] = None
    hypotheses_formed: int = 0
    hypotheses_validated: int = 0
    knowledge_nodes: int = 0
    knowledge_connections: int = 0
    learning_rate: float = 0.0
    confidence_trend: List[float] = None
    
    def __post_init__(self):
        if self.memories_by_type is None:
            self.memories_by_type = {}
        if self.confidence_trend is None:
            self.confidence_trend = []


class ReasoningChainVisualizer:
    """
    Provides reasoning chain data for visualization
    Shows how agents think through problems step by step
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.reasoning_chains = {}  # session_id -> chain
        self.max_chains = 100
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        
    async def process_reasoning_event(self, event: Dict[str, Any]):
        """Process reasoning-related events"""
        event_type = event.get("event_type")
        session_id = event.get("session_id", "unknown")
        
        if event_type == "reasoning_step":
            await self._add_reasoning_step(session_id, event)
        elif event_type == "agent_thought":
            await self._add_thought(session_id, event)
        elif event_type == "tool_observation":
            await self._add_observation(session_id, event)
            
    async def _add_reasoning_step(self, session_id: str, event: Dict[str, Any]):
        """Add a new reasoning step to the chain"""
        step = ReasoningStep(
            step_id=event.get("step_id", str(datetime.now(timezone.utc).timestamp())),
            agent_id=event.get("agent_id", "unknown"),
            timestamp=datetime.now(timezone.utc),
            thought=event.get("thought", ""),
            action=event.get("action"),
            observation=event.get("observation"),
            confidence=event.get("confidence", 0.0),
            parent_step_id=event.get("parent_step_id")
        )
        
        # Initialize chain if needed
        if session_id not in self.reasoning_chains:
            self.reasoning_chains[session_id] = {
                "steps": {},
                "root_steps": [],
                "created_at": datetime.now(timezone.utc),
                "last_updated": datetime.now(timezone.utc)
            }
        
        chain = self.reasoning_chains[session_id]
        chain["steps"][step.step_id] = step
        chain["last_updated"] = datetime.now(timezone.utc)
        
        # Update parent-child relationships
        if step.parent_step_id and step.parent_step_id in chain["steps"]:
            parent = chain["steps"][step.parent_step_id]
            parent.children_step_ids.append(step.step_id)
        else:
            chain["root_steps"].append(step.step_id)
            
        # Limit chain storage
        if len(self.reasoning_chains) > self.max_chains:
            oldest_session = min(self.reasoning_chains.keys(), 
                               key=lambda k: self.reasoning_chains[k]["created_at"])
            del self.reasoning_chains[oldest_session]
            
    async def get_reasoning_chain(self, session_id: str) -> Dict[str, Any]:
        """Get complete reasoning chain for a session"""
        if session_id not in self.reasoning_chains:
            return {"error": "Chain not found"}
            
        chain = self.reasoning_chains[session_id]
        
        # Convert to serializable format
        return {
            "session_id": session_id,
            "created_at": chain["created_at"].isoformat(),
            "last_updated": chain["last_updated"].isoformat(),
            "steps": [asdict(step) for step in chain["steps"].values()],
            "root_steps": chain["root_steps"],
            "total_steps": len(chain["steps"])
        }
        
    async def get_active_chains(self) -> List[Dict[str, Any]]:
        """Get all active reasoning chains"""
        active_chains = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        for session_id, chain in self.reasoning_chains.items():
            if chain["last_updated"] > cutoff_time:
                active_chains.append({
                    "session_id": session_id,
                    "step_count": len(chain["steps"]),
                    "last_updated": chain["last_updated"].isoformat(),
                    "agents_involved": list(set(
                        step.agent_id for step in chain["steps"].values()
                    ))
                })
                
        return active_chains


class CostAnalyticsDashboard:
    """
    Real-time cost tracking and analytics
    Provides detailed breakdowns of AI resource usage
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.current_metrics = CostMetrics()
        self.hourly_buckets = deque(maxlen=24)  # Last 24 hours
        self.cost_history = deque(maxlen=1000)  # Last 1000 events
        
        # Model pricing (simplified)
        self.model_pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-2": {"input": 0.008, "output": 0.024},
            "llama-70b": {"input": 0.001, "output": 0.001}  # Self-hosted
        }
        
    async def initialize(self):
        """Initialize Redis connection and load historical data"""
        self.redis_client = redis.from_url(self.redis_url)
        await self._load_historical_costs()
        
    async def _load_historical_costs(self):
        """Load cost data from Redis"""
        try:
            # Load today's costs
            today_key = f"costs:{datetime.now().date()}"
            cost_data = await self.redis_client.get(today_key)
            if cost_data:
                saved_metrics = json.loads(cost_data)
                self.current_metrics.total_cost = saved_metrics.get("total_cost", 0)
                self.current_metrics.token_count = saved_metrics.get("token_count", 0)
        except Exception as e:
            logger.error(f"Failed to load historical costs: {e}")
            
    async def process_cost_event(self, event: Dict[str, Any]):
        """Process cost-related events"""
        event_type = event.get("event_type")
        
        if event_type == "llm_call_completed":
            await self._process_llm_cost(event)
        elif event_type == "tool_usage_completed":
            await self._process_tool_cost(event)
        elif event_type == "cache_hit":
            self.current_metrics.cache_hits += 1
            
    async def _process_llm_cost(self, event: Dict[str, Any]):
        """Calculate and track LLM costs"""
        model = event.get("model", "gpt-3.5-turbo")
        input_tokens = event.get("input_tokens", 0)
        output_tokens = event.get("output_tokens", 0)
        agent_id = event.get("agent_id", "unknown")
        
        # Calculate cost
        pricing = self.model_pricing.get(model, self.model_pricing["gpt-3.5-turbo"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Update metrics
        self.current_metrics.total_cost += total_cost
        self.current_metrics.token_count += input_tokens + output_tokens
        self.current_metrics.api_calls += 1
        
        # Track by agent
        if agent_id not in self.current_metrics.cost_by_agent:
            self.current_metrics.cost_by_agent[agent_id] = 0
        self.current_metrics.cost_by_agent[agent_id] += total_cost
        
        # Track by model
        if model not in self.current_metrics.cost_by_model:
            self.current_metrics.cost_by_model[model] = 0
        self.current_metrics.cost_by_model[model] += total_cost
        
        # Add to history
        self.cost_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost": total_cost,
            "tokens": input_tokens + output_tokens,
            "model": model,
            "agent": agent_id
        })
        
        # Update hourly bucket
        await self._update_hourly_bucket(total_cost)
        
        # Persist to Redis
        await self._save_costs()
        
    async def _update_hourly_bucket(self, cost: float):
        """Update hourly cost tracking"""
        current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        
        if not self.hourly_buckets or self.hourly_buckets[-1]["hour"] != current_hour:
            self.hourly_buckets.append({
                "hour": current_hour,
                "cost": 0,
                "calls": 0
            })
            
        self.hourly_buckets[-1]["cost"] += cost
        self.hourly_buckets[-1]["calls"] += 1
        
    async def _save_costs(self):
        """Persist cost data to Redis"""
        try:
            today_key = f"costs:{datetime.now().date()}"
            cost_data = {
                "total_cost": self.current_metrics.total_cost,
                "token_count": self.current_metrics.token_count,
                "api_calls": self.current_metrics.api_calls,
                "cache_hits": self.current_metrics.cache_hits,
                "cost_by_agent": self.current_metrics.cost_by_agent,
                "cost_by_model": self.current_metrics.cost_by_model
            }
            
            await self.redis_client.setex(
                today_key,
                86400 * 7,  # Keep for 7 days
                json.dumps(cost_data)
            )
        except Exception as e:
            logger.error(f"Failed to save costs: {e}")
            
    async def get_cost_metrics(self) -> Dict[str, Any]:
        """Get current cost metrics"""
        return {
            "current": asdict(self.current_metrics),
            "hourly": [
                {
                    "hour": bucket["hour"].isoformat(),
                    "cost": bucket["cost"],
                    "calls": bucket["calls"]
                }
                for bucket in self.hourly_buckets
            ],
            "recent_events": list(self.cost_history)[-50:],  # Last 50 events
            "cost_per_token": self.current_metrics.total_cost / max(self.current_metrics.token_count, 1),
            "cache_hit_rate": (self.current_metrics.cache_hits / 
                             max(self.current_metrics.api_calls + self.current_metrics.cache_hits, 1))
        }


class LearningSystemVisualizer:
    """
    Visualizes the compound intelligence system
    Shows memory formation, hypothesis validation, and knowledge growth
    """
    
    def __init__(self, redis_url: str, memory_backend=None, hypothesis_validator=None):
        self.redis_url = redis_url
        self.redis_client = None
        self.memory_backend = memory_backend
        self.hypothesis_validator = hypothesis_validator
        self.learning_metrics = LearningMetrics()
        self.memory_timeline = deque(maxlen=100)
        self.hypothesis_timeline = deque(maxlen=50)
        
    async def initialize(self):
        """Initialize connections and load current state"""
        self.redis_client = redis.from_url(self.redis_url)
        await self._load_current_state()
        
    async def _load_current_state(self):
        """Load current learning state from backends"""
        if self.memory_backend:
            try:
                # Get memory counts
                memories = await self.memory_backend.get_all_memories(limit=1000)
                self.learning_metrics.total_memories = len(memories)
                
                # Count by type
                for memory in memories:
                    mem_type = memory.get("memory_type", "unknown")
                    if mem_type not in self.learning_metrics.memories_by_type:
                        self.learning_metrics.memories_by_type[mem_type] = 0
                    self.learning_metrics.memories_by_type[mem_type] += 1
                    
            except Exception as e:
                logger.error(f"Failed to load memory state: {e}")
                
        if self.hypothesis_validator:
            try:
                # Get hypothesis counts
                hypotheses = await self.hypothesis_validator.get_all_hypotheses()
                self.learning_metrics.hypotheses_formed = len(hypotheses)
                self.learning_metrics.hypotheses_validated = sum(
                    1 for h in hypotheses if h.get("status") == "validated"
                )
            except Exception as e:
                logger.error(f"Failed to load hypothesis state: {e}")
                
    async def process_learning_event(self, event: Dict[str, Any]):
        """Process learning-related events"""
        event_type = event.get("event_type")
        
        if event_type == "memory_stored":
            await self._process_memory_event(event)
        elif event_type == "hypothesis_formed":
            await self._process_hypothesis_formed(event)
        elif event_type == "hypothesis_validated":
            await self._process_hypothesis_validated(event)
        elif event_type == "knowledge_created":
            await self._process_knowledge_event(event)
            
    async def _process_memory_event(self, event: Dict[str, Any]):
        """Track memory formation"""
        self.learning_metrics.total_memories += 1
        
        mem_type = event.get("memory_type", "unknown")
        if mem_type not in self.learning_metrics.memories_by_type:
            self.learning_metrics.memories_by_type[mem_type] = 0
        self.learning_metrics.memories_by_type[mem_type] += 1
        
        # Add to timeline
        self.memory_timeline.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": mem_type,
            "agent_id": event.get("agent_id"),
            "confidence": event.get("confidence", 0.5)
        })
        
        # Update confidence trend
        recent_confidences = [m["confidence"] for m in self.memory_timeline]
        if recent_confidences:
            avg_confidence = sum(recent_confidences) / len(recent_confidences)
            self.learning_metrics.confidence_trend.append(avg_confidence)
            if len(self.learning_metrics.confidence_trend) > 100:
                self.learning_metrics.confidence_trend.pop(0)
                
    async def _process_hypothesis_formed(self, event: Dict[str, Any]):
        """Track hypothesis formation"""
        self.learning_metrics.hypotheses_formed += 1
        
        self.hypothesis_timeline.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hypothesis_id": event.get("hypothesis_id"),
            "domain": event.get("domain"),
            "confidence": event.get("confidence", 0.5),
            "status": "formed"
        })
        
    async def _process_hypothesis_validated(self, event: Dict[str, Any]):
        """Track hypothesis validation"""
        self.learning_metrics.hypotheses_validated += 1
        
        # Update hypothesis in timeline
        hypothesis_id = event.get("hypothesis_id")
        for h in self.hypothesis_timeline:
            if h["hypothesis_id"] == hypothesis_id:
                h["status"] = "validated"
                h["validation_time"] = datetime.now(timezone.utc).isoformat()
                break
                
    async def _process_knowledge_event(self, event: Dict[str, Any]):
        """Track knowledge graph growth"""
        if event.get("action") == "node_created":
            self.learning_metrics.knowledge_nodes += 1
        elif event.get("action") == "connection_created":
            self.learning_metrics.knowledge_connections += 1
            
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get current learning system metrics"""
        # Calculate learning rate (memories per hour)
        if self.memory_timeline:
            oldest_memory = datetime.fromisoformat(self.memory_timeline[0]["timestamp"])
            time_span = (datetime.now(timezone.utc) - oldest_memory).total_seconds() / 3600
            self.learning_metrics.learning_rate = len(self.memory_timeline) / max(time_span, 1)
            
        return {
            "metrics": asdict(self.learning_metrics),
            "memory_timeline": list(self.memory_timeline)[-20:],
            "hypothesis_timeline": list(self.hypothesis_timeline)[-10:],
            "knowledge_graph": {
                "nodes": self.learning_metrics.knowledge_nodes,
                "edges": self.learning_metrics.knowledge_connections,
                "density": (self.learning_metrics.knowledge_connections / 
                          max(self.learning_metrics.knowledge_nodes * (self.learning_metrics.knowledge_nodes - 1) / 2, 1))
            }
        }


class UnifiedDashboardAPI:
    """
    Unified API for all dashboard visualizations
    Coordinates between the three dashboard backends
    """
    
    def __init__(self, redis_url: str, memory_backend=None, hypothesis_validator=None):
        self.redis_url = redis_url
        self.reasoning_viz = ReasoningChainVisualizer(redis_url)
        self.cost_analytics = CostAnalyticsDashboard(redis_url)
        self.learning_viz = LearningSystemVisualizer(
            redis_url, memory_backend, hypothesis_validator
        )
        
    async def initialize(self):
        """Initialize all dashboard components"""
        await self.reasoning_viz.initialize()
        await self.cost_analytics.initialize()
        await self.learning_viz.initialize()
        
        # Start event processing
        asyncio.create_task(self._process_events())
        
    async def _process_events(self):
        """Process events from Redis streams"""
        redis_client = redis.from_url(self.redis_url)
        
        while True:
            try:
                # Read from all event streams
                streams = await redis_client.xread({
                    "auren:events:critical": "$",
                    "auren:events:operational": "$",
                    "auren:events:analytical": "$"
                }, block=1000)
                
                for stream_name, events in streams:
                    for event_id, event_data in events:
                        event = json.loads(event_data.get(b"data", b"{}"))
                        
                        # Route to appropriate visualizer
                        if event.get("event_type") in ["reasoning_step", "agent_thought", "tool_observation"]:
                            await self.reasoning_viz.process_reasoning_event(event)
                        
                        if event.get("event_type") in ["llm_call_completed", "tool_usage_completed", "cache_hit"]:
                            await self.cost_analytics.process_cost_event(event)
                            
                        if event.get("event_type") in ["memory_stored", "hypothesis_formed", 
                                                       "hypothesis_validated", "knowledge_created"]:
                            await self.learning_viz.process_learning_event(event)
                            
            except Exception as e:
                logger.error(f"Event processing error: {e}")
                await asyncio.sleep(1)
                
    async def get_dashboard_data(self, dashboard_type: str, **kwargs) -> Dict[str, Any]:
        """Get data for specific dashboard"""
        if dashboard_type == "reasoning":
            if "session_id" in kwargs:
                return await self.reasoning_viz.get_reasoning_chain(kwargs["session_id"])
            return {"active_chains": await self.reasoning_viz.get_active_chains()}
            
        elif dashboard_type == "cost":
            return await self.cost_analytics.get_cost_metrics()
            
        elif dashboard_type == "learning":
            return await self.learning_viz.get_learning_metrics()
            
        else:
            return {"error": f"Unknown dashboard type: {dashboard_type}"}


# FastAPI endpoints for dashboard data
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="AUREN Dashboard API")

# Global dashboard API instance
dashboard_api = None


@app.on_event("startup")
async def startup_event():
    """Initialize dashboard API on startup"""
    global dashboard_api
    
    redis_url = "redis://localhost:6379"
    # In production, would get actual backends
    dashboard_api = UnifiedDashboardAPI(redis_url)
    await dashboard_api.initialize()


@app.get("/api/dashboard/{dashboard_type}")
async def get_dashboard_data(dashboard_type: str, session_id: Optional[str] = None):
    """Get dashboard data via REST API"""
    kwargs = {}
    if session_id:
        kwargs["session_id"] = session_id
        
    return await dashboard_api.get_dashboard_data(dashboard_type, **kwargs)


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send updates every second
            await asyncio.sleep(1)
            
            # Get all dashboard data
            data = {
                "reasoning": await dashboard_api.get_dashboard_data("reasoning"),
                "cost": await dashboard_api.get_dashboard_data("cost"),
                "learning": await dashboard_api.get_dashboard_data("learning"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await websocket.send_json(data)
            
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        

if __name__ == "__main__":
    # Run the dashboard API server
    uvicorn.run(app, host="0.0.0.0", port=8001) 