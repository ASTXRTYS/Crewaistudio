"""
Complete CrewAI instrumentation for event generation
This is the source of all events that get streamed to dashboards
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation

# CrewAI imports
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END, Task, Crew, Process

# Note: CrewAI event system has changed - using custom event capturing instead
# from crewai.agents.events import (
#     AgentExecutionStartedEvent,
#     AgentExecutionCompletedEvent,
#     TaskStartedEvent,
#     TaskCompletedEvent,
#     LLMCallStartedEvent,
#     LLMCallCompletedEvent,
#     ToolUsageStartedEvent,
#     ToolUsageCompletedEvent
# )
# from crewai.events import EventBus

logger = logging.getLogger(__name__)

@dataclass
class AURENPerformanceMetrics:
    """Enhanced performance metrics for AUREN agent operations"""
    latency_ms: float
    token_cost: float
    memory_usage_mb: float
    cpu_percentage: float
    success: bool
    error_type: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    collaboration_depth: int = 0
    knowledge_items_accessed: int = 0
    hypotheses_formed: int = 0
    confidence_score: float = 0.0

class AURENEventType(Enum):
    """Extended event types for AUREN monitoring"""
    AGENT_EXECUTION_STARTED = "agent_execution_started"
    AGENT_EXECUTION_COMPLETED = "agent_execution_completed"
    AGENT_COLLABORATION = "agent_collaboration"
    AGENT_DECISION = "agent_decision"
    TOOL_USAGE = "tool_usage"
    LLM_CALL = "llm_call"
    HYPOTHESIS_FORMATION = "hypothesis_formation"
    KNOWLEDGE_ACCESS = "knowledge_access"
    BIOMETRIC_ANALYSIS = "biometric_analysis"
    CONVERSATION_EVENT = "conversation_event"
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE_METRIC = "performance_metric"
    MEMORY_TIER_ACCESS = "memory_tier_access"  # Added for memory tier tracking

@dataclass
class AURENStreamEvent:
    """Standardized event for AUREN streaming"""
    event_id: str
    trace_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    event_type: AURENEventType
    source_agent: Optional[Dict[str, Any]]
    target_agent: Optional[Dict[str, Any]]
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    performance_metrics: Optional[AURENPerformanceMetrics] = None
    user_id: Optional[str] = None

class CrewAIEventInstrumentation:
    """
    Complete instrumentation system for CrewAI agents
    Captures all agent activities and generates standardized events
    """
    
    def __init__(self, event_streamer=None):
        self.event_streamer = event_streamer
        # Since EventBus is not available, we'll track manually
        self.active_sessions = {}
        self.agent_registry = {}
        self.performance_tracker = {}
        
        # Setup event listeners (using custom approach)
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Register comprehensive event listeners"""
        # Since CrewAI doesn't expose events directly in current version,
        # we'll need to instrument agents manually when they're created
        logger.info("Event instrumentation initialized - manual tracking mode")
    
    async def track_agent_start(self, agent: Agent, session_id: str = None, trace_id: str = None):
        """Manually track agent execution start"""
        
        if not session_id:
            session_id = f"{agent.role}_{datetime.now().timestamp()}"
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # Initialize performance tracking
        self.performance_tracker[session_id] = {
            "start_time": datetime.now(timezone.utc),
            "agent_id": agent.role,
            "trace_id": trace_id,
            "llm_calls": 0,
            "tool_uses": 0,
            "tokens_used": 0,
            "cost_accumulated": 0.0
        }
        
        # Create enhanced event
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=trace_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_STARTED,
            source_agent={
                "id": agent.role,
                "role": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory[:200] + "..." if len(agent.backstory) > 200 else agent.backstory
            },
            target_agent=None,
            payload={
                "execution_mode": "autonomous" if agent.allow_delegation else "directed",
                "tools_available": len(agent.tools) if agent.tools else 0,
                "memory_enabled": hasattr(agent, 'memory') and agent.memory is not None
            },
            metadata={
                "platform": "langgraph",
                "agent_version": getattr(agent, 'version', '1.0'),
                "execution_context": "production"
            }
        )
        
        await self._emit_event(stream_event)
        return session_id, trace_id
    
    async def track_agent_complete(self, agent: Agent, session_id: str, success: bool = True, error: Exception = None):
        """Manually track agent execution completion"""
        
        tracker = self.performance_tracker.get(session_id, {})
        
        # Calculate performance metrics
        start_time = tracker.get("start_time", datetime.now(timezone.utc))
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        performance_metrics = AURENPerformanceMetrics(
            latency_ms=execution_time,
            token_cost=tracker.get("cost_accumulated", 0.0),
            memory_usage_mb=self._get_memory_usage(),
            cpu_percentage=self._get_cpu_usage(),
            success=success,
            error_type=type(error).__name__ if error else None,
            agent_id=agent.role,
            collaboration_depth=tracker.get("collaboration_events", 0),
            knowledge_items_accessed=tracker.get("knowledge_accesses", 0),
            hypotheses_formed=tracker.get("hypotheses_formed", 0),
            confidence_score=0.85  # Default confidence
        )
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=tracker.get("trace_id"),
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
            source_agent={
                "id": agent.role,
                "role": agent.role
            },
            target_agent=None,
            payload={
                "execution_result": "success" if success else "error",
                "output_length": 0,  # Would need actual output
                "llm_calls_made": tracker.get("llm_calls", 0),
                "tools_used": tracker.get("tool_uses", 0)
            },
            metadata={
                "session_duration_ms": execution_time,
                "resource_efficiency": self._calculate_efficiency_score(performance_metrics)
            },
            performance_metrics=performance_metrics
        )
        
        await self._emit_event(stream_event)
        
        # Cleanup tracker
        if session_id in self.performance_tracker:
            del self.performance_tracker[session_id]
    
    async def track_llm_call(self, agent_id: str, model: str, tokens_used: int, cost: float, success: bool = True):
        """Track LLM usage"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=None,
            session_id=None,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.LLM_CALL,
            source_agent={
                "id": agent_id,
                "role": agent_id
            },
            target_agent=None,
            payload={
                "model": model,
                "tokens_used": tokens_used,
                "cost": cost,
                "success": success,
                "latency_ms": 0  # Would need actual latency
            },
            metadata={
                "provider": "openai",  # Default provider
                "model_efficiency": tokens_used / 1000 if tokens_used > 0 else 0
            }
        )
        
        await self._emit_event(stream_event)
    
    async def capture_agent_collaboration(self,
                                        primary_agent: str,
                                        collaborating_agents: List[str],
                                        collaboration_type: str,
                                        result: Dict[str, Any],
                                        trace_id: str = None):
        """Capture agent collaboration events"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4()),
            session_id=f"collab_{datetime.now().timestamp()}",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_COLLABORATION,
            source_agent={"id": primary_agent, "role": primary_agent},
            target_agent=None,
            payload={
                "primary_agent": primary_agent,
                "collaborating_agents": collaborating_agents,
                "collaboration_type": collaboration_type,
                "consensus_reached": result.get("consensus", False),
                "confidence_scores": result.get("confidence_scores", {}),
                "resolution_time_ms": result.get("resolution_time", 0),
                "knowledge_shared": result.get("knowledge_items", 0)
            },
            metadata={
                "domains_involved": [self._get_agent_domain(a) for a in collaborating_agents],
                "collaboration_complexity": len(collaborating_agents),
                "outcome_quality": result.get("quality_score", 0.0)
            }
        )
        
        await self._emit_event(stream_event)
    
    async def capture_agent_decision(self,
                                   agent_id: str,
                                   user_id: str,
                                   decision: Dict[str, Any],
                                   context: Dict[str, Any],
                                   confidence: float,
                                   trace_id: str = None):
        """Capture agent decision events with rich context"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4()),
            session_id=f"decision_{datetime.now().timestamp()}",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_DECISION,
            source_agent={"id": agent_id, "role": agent_id},
            target_agent=None,
            payload={
                "decision": decision,
                "confidence": confidence,
                "reasoning_chain": context.get("reasoning", []),
                "data_sources": context.get("data_sources", []),
                "alternatives_considered": context.get("alternatives", []),
                "decision_impact": context.get("impact_assessment", "unknown")
            },
            metadata={
                "decision_category": decision.get("category", "general"),
                "urgency": context.get("urgency", "normal"),
                "user_context": context.get("user_state", {})
            },
            user_id=user_id
        )
        
        await self._emit_event(stream_event)
    
    async def _emit_event(self, event: AURENStreamEvent):
        """Emit event to the streaming system"""
        
        if self.event_streamer:
            try:
                await self.event_streamer.stream_event(event)
            except Exception as e:
                logger.error(f"Failed to emit event {event.event_id}: {e}")
        else:
            logger.debug(f"Event {event.event_id} captured but no streamer configured")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0
    
    def _calculate_efficiency_score(self, metrics: AURENPerformanceMetrics) -> float:
        """Calculate resource efficiency score"""
        if metrics.latency_ms == 0:
            return 1.0
        
        # Simple efficiency calculation based on latency and success
        base_score = 1.0 if metrics.success else 0.5
        latency_factor = max(0.1, 1.0 - (metrics.latency_ms / 10000))  # Penalize >10s latency
        return base_score * latency_factor
    
    def _get_agent_domain(self, agent_id: str) -> str:
        """Get agent domain from agent ID"""
        domain_map = {
            "neuroscientist": "neuroscience",
            "nutritionist": "nutrition",
            "training_agent": "training",
            "recovery_agent": "recovery",
            "sleep_agent": "sleep",
            "mental_health_agent": "mental_health"
        }
        return domain_map.get(agent_id, "unknown") 