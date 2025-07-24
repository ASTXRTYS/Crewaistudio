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

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai.agents.events import (
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    LLMCallStartedEvent,
    LLMCallCompletedEvent,
    ToolUsageStartedEvent,
    ToolUsageCompletedEvent
)
from crewai.events import EventBus

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
        self.event_bus = EventBus()
        self.active_sessions = {}
        self.agent_registry = {}
        self.performance_tracker = {}
        
        # Setup event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Register comprehensive event listeners"""
        
        # Agent lifecycle events
        self.event_bus.on(AgentExecutionStartedEvent, self._on_agent_execution_started)
        self.event_bus.on(AgentExecutionCompletedEvent, self._on_agent_execution_completed)
        
        # Task lifecycle events
        self.event_bus.on(TaskStartedEvent, self._on_task_started)
        self.event_bus.on(TaskCompletedEvent, self._on_task_completed)
        
        # LLM usage events (critical for cost tracking)
        self.event_bus.on(LLMCallStartedEvent, self._on_llm_call_started)
        self.event_bus.on(LLMCallCompletedEvent, self._on_llm_call_completed)
        
        # Tool usage events
        self.event_bus.on(ToolUsageStartedEvent, self._on_tool_usage_started)
        self.event_bus.on(ToolUsageCompletedEvent, self._on_tool_usage_completed)
    
    async def _on_agent_execution_started(self, event: AgentExecutionStartedEvent):
        """Capture agent execution start with enhanced telemetry"""
        
        session_id = f"{event.agent.role}_{datetime.now().timestamp()}"
        trace_id = str(uuid.uuid4())
        
        # Initialize performance tracking
        self.performance_tracker[session_id] = {
            "start_time": datetime.now(timezone.utc),
            "agent_id": event.agent.role,
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
                "id": event.agent.role,
                "role": event.agent.role,
                "goal": event.agent.goal,
                "backstory": event.agent.backstory[:200] + "..." if len(event.agent.backstory) > 200 else event.agent.backstory
            },
            target_agent=None,
            payload={
                "execution_mode": "autonomous" if event.agent.allow_delegation else "directed",
                "tools_available": len(event.agent.tools) if event.agent.tools else 0,
                "memory_enabled": hasattr(event.agent, 'memory') and event.agent.memory is not None
            },
            metadata={
                "platform": "crewai",
                "agent_version": getattr(event.agent, 'version', '1.0'),
                "execution_context": "production"
            }
        )
        
        await self._emit_event(stream_event)
    
    async def _on_agent_execution_completed(self, event: AgentExecutionCompletedEvent):
        """Capture agent execution completion with performance metrics"""
        
        session_id = f"{event.agent.role}_{datetime.now().timestamp()}"
        tracker = self.performance_tracker.get(session_id, {})
        
        # Calculate performance metrics
        start_time = tracker.get("start_time", datetime.now(timezone.utc))
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        performance_metrics = AURENPerformanceMetrics(
            latency_ms=execution_time,
            token_cost=tracker.get("cost_accumulated", 0.0),
            memory_usage_mb=self._get_memory_usage(),
            cpu_percentage=self._get_cpu_usage(),
            success=not hasattr(event, 'error') or event.error is None,
            error_type=type(event.error).__name__ if hasattr(event, 'error') and event.error else None,
            agent_id=event.agent.role,
            collaboration_depth=tracker.get("collaboration_events", 0),
            knowledge_items_accessed=tracker.get("knowledge_accesses", 0),
            hypotheses_formed=tracker.get("hypotheses_formed", 0),
            confidence_score=getattr(event, 'confidence', 0.0)
        )
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=tracker.get("trace_id"),
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
            source_agent={
                "id": event.agent.role,
                "role": event.agent.role
            },
            target_agent=None,
            payload={
                "execution_result": "success" if performance_metrics.success else "error",
                "output_length": len(str(getattr(event, 'output', ''))) if hasattr(event, 'output') else 0,
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
    
    async def _on_llm_call_started(self, event: LLMCallStartedEvent):
        """Track LLM call initiation"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=getattr(event, 'trace_id', None),
            session_id=getattr(event, 'session_id', None),
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.LLM_CALL,
            source_agent={
                "id": event.agent.role if hasattr(event, 'agent') else "unknown",
                "role": event.agent.role if hasattr(event, 'agent') else "unknown"
            },
            target_agent=None,
            payload={
                "model": getattr(event, 'model', 'unknown'),
                "prompt_length": len(str(getattr(event, 'prompt', ''))),
                "max_tokens": getattr(event, 'max_tokens', 0),
                "temperature": getattr(event, 'temperature', 0.7),
                "call_purpose": getattr(event, 'purpose', 'generation')
            },
            metadata={
                "provider": getattr(event, 'provider', 'unknown'),
                "call_type": "async" if getattr(event, 'async_call', False) else "sync"
            }
        )
        
        await self._emit_event(stream_event)
    
    async def _on_llm_call_completed(self, event: LLMCallCompletedEvent):
        """Track LLM call completion with cost analysis"""
        
        # Update performance tracker
        session_id = getattr(event, 'session_id', 'unknown')
        if session_id in self.performance_tracker:
            self.performance_tracker[session_id]['llm_calls'] += 1
            self.performance_tracker[session_id]['tokens_used'] += getattr(event, 'tokens_used', 0)
            self.performance_tracker[session_id]['cost_accumulated'] += getattr(event, 'cost', 0.0)
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=getattr(event, 'trace_id', None),
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.LLM_CALL,
            source_agent={
                "id": event.agent.role if hasattr(event, 'agent') else "unknown",
                "role": event.agent.role if hasattr(event, 'agent') else "unknown"
            },
            target_agent=None,
            payload={
                "tokens_used": getattr(event, 'tokens_used', 0),
                "cost": getattr(event, 'cost', 0.0),
                "response_length": len(str(getattr(event, 'response', ''))),
                "success": not hasattr(event, 'error') or event.error is None,
                "latency_ms": getattr(event, 'latency_ms', 0)
            },
            metadata={
                "model_efficiency": self._calculate_token_efficiency(event),
                "response_quality": getattr(event, 'quality_score', 0.0)
            }
        )
        
        await self._emit_event(stream_event)
    
    async def _on_tool_usage_started(self, event: ToolUsageStartedEvent):
        """Track tool usage initiation"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=getattr(event, 'trace_id', None),
            session_id=getattr(event, 'session_id', None),
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.TOOL_USAGE,
            source_agent={
                "id": event.agent.role if hasattr(event, 'agent') else "unknown",
                "role": event.agent.role if hasattr(event, 'agent') else "unknown"
            },
            target_agent=None,
            payload={
                "tool_name": getattr(event, 'tool_name', 'unknown'),
                "tool_input": str(getattr(event, 'tool_input', ''))[:500],  # Truncate long inputs
                "tool_type": getattr(event, 'tool_type', 'unknown'),
                "expected_output_type": getattr(event, 'expected_output', 'string')
            },
            metadata={
                "tool_category": self._categorize_tool(getattr(event, 'tool_name', '')),
                "input_complexity": self._assess_input_complexity(getattr(event, 'tool_input', ''))
            }
        )
        
        await self._emit_event(stream_event)
    
    async def _on_tool_usage_completed(self, event: ToolUsageCompletedEvent):
        """Track tool usage completion"""
        
        # Update performance tracker
        session_id = getattr(event, 'session_id', 'unknown')
        if session_id in self.performance_tracker:
            self.performance_tracker[session_id]['tool_uses'] += 1
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=getattr(event, 'trace_id', None),
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.TOOL_USAGE,
            source_agent={
                "id": event.agent.role if hasattr(event, 'agent') else "unknown",
                "role": event.agent.role if hasattr(event, 'agent') else "unknown"
            },
            target_agent=None,
            payload={
                "tool_name": getattr(event, 'tool_name', 'unknown'),
                "success": not hasattr(event, 'error') or event.error is None,
                "output_length": len(str(getattr(event, 'output', ''))),
                "execution_time_ms": getattr(event, 'execution_time', 0),
                "output_type": type(getattr(event, 'output', '')).__name__
            },
            metadata={
                "tool_efficiency": self._calculate_tool_efficiency(event),
                "output_quality": getattr(event, 'quality_score', 0.0)
            }
        )
        
        await self._emit_event(stream_event)
    
    async def _on_task_started(self, event: TaskStartedEvent):
        """Track task initiation"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=getattr(event, 'trace_id', None),
            session_id=getattr(event, 'session_id', None),
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_STARTED,
            source_agent={
                "id": event.agent.role if hasattr(event, 'agent') else "unknown",
                "role": event.agent.role if hasattr(event, 'agent') else "unknown"
            },
            target_agent=None,
            payload={
                "task_description": str(getattr(event, 'description', ''))[:500],
                "expected_output": str(getattr(event, 'expected_output', ''))[:200]
            },
            metadata={
                "task_complexity": self._assess_task_complexity(event)
            }
        )
        
        await self._emit_event(stream_event)
    
    async def _on_task_completed(self, event: TaskCompletedEvent):
        """Track task completion"""
        
        stream_event = AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=getattr(event, 'trace_id', None),
            session_id=getattr(event, 'session_id', None),
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
            source_agent={
                "id": event.agent.role if hasattr(event, 'agent') else "unknown",
                "role": event.agent.role if hasattr(event, 'agent') else "unknown"
            },
            target_agent=None,
            payload={
                "task_result": "success" if not hasattr(event, 'error') or event.error is None else "error",
                "output_length": len(str(getattr(event, 'output', ''))) if hasattr(event, 'output') else 0
            },
            metadata={
                "task_duration_ms": getattr(event, 'duration_ms', 0)
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
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        import psutil
        return psutil.cpu_percent(interval=0.1)
    
    def _calculate_efficiency_score(self, metrics: AURENPerformanceMetrics) -> float:
        """Calculate resource efficiency score"""
        if metrics.latency_ms == 0:
            return 1.0
        
        # Simple efficiency calculation based on latency and success
        base_score = 1.0 if metrics.success else 0.5
        latency_factor = max(0.1, 1.0 - (metrics.latency_ms / 10000))  # Penalize >10s latency
        return base_score * latency_factor
    
    def _calculate_token_efficiency(self, event) -> float:
        """Calculate token efficiency for LLM calls"""
        tokens = getattr(event, 'tokens_used', 0)
        response_length = len(str(getattr(event, 'response', '')))
        if tokens == 0:
            return 0.0
        return min(1.0, response_length / tokens)  # Characters per token
    
    def _calculate_tool_efficiency(self, event) -> float:
        """Calculate tool execution efficiency"""
        execution_time = getattr(event, 'execution_time', 0)
        success = not hasattr(event, 'error') or event.error is None
        if execution_time == 0:
            return 1.0 if success else 0.0
        
        # Efficiency based on speed and success
        speed_factor = max(0.1, 1.0 - (execution_time / 30000))  # Penalize >30s execution
        return (1.0 if success else 0.5) * speed_factor
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name"""
        tool_categories = {
            "search": ["search", "google", "web"],
            "analysis": ["analyze", "calculate", "process"],
            "communication": ["email", "slack", "message"],
            "data": ["database", "query", "fetch"],
            "ai": ["llm", "gpt", "claude", "model"]
        }
        
        tool_name_lower = tool_name.lower()
        for category, keywords in tool_categories.items():
            if any(keyword in tool_name_lower for keyword in keywords):
                return category
        return "unknown"
    
    def _assess_input_complexity(self, tool_input) -> str:
        """Assess complexity of tool input"""
        input_str = str(tool_input)
        if len(input_str) < 50:
            return "simple"
        elif len(input_str) < 200:
            return "medium"
        else:
            return "complex"
    
    def _assess_task_complexity(self, event) -> str:
        """Assess task complexity based on description"""
        description = str(getattr(event, 'description', ''))
        if len(description) < 100:
            return "simple"
        elif len(description) < 300:
            return "medium"
        else:
            return "complex"
    
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