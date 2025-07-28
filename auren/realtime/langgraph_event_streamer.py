"""
LangGraph Event Streamer - Replacement for LangGraphEventStreamer
Purpose: Provides event streaming capabilities using LangGraph patterns
Author: Senior Engineer
Date: January 29, 2025
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import uuid
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer

from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)


class AURENEventType(str, Enum):
    """Event types for AUREN system (matching CrewAI event types)"""
    # Agent Events
    AGENT_CREATED = "agent_created"
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTING = "agent_acting"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Task Events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_OUTPUT = "task_output"
    TASK_COMPLETED = "task_completed"
    TASK_ERROR = "task_error"
    
    # Memory Events
    MEMORY_ACCESSED = "memory_accessed"
    MEMORY_UPDATED = "memory_updated"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    
    # System Events
    SYSTEM_STATUS = "system_status"
    HEALTH_CHECK = "health_check"
    ERROR = "error"


class LangGraphEventStreamer:
    """
    LangGraph-based event streaming system
    Drop-in replacement for LangGraphEventStreamer
    """
    
    def __init__(self, 
                 agent_name: str = "AUREN",
                 enable_streaming: bool = True,
                 event_callbacks: Optional[List[Callable]] = None):
        """
        Initialize event streamer
        
        Args:
            agent_name: Name of the agent
            enable_streaming: Whether to enable event streaming
            event_callbacks: Optional callbacks for events
        """
        self.agent_name = agent_name
        self.enable_streaming = enable_streaming
        self.event_callbacks = event_callbacks or []
        self.event_stream = []
        self.session_id = str(uuid.uuid4())
        self._start_time = datetime.now(timezone.utc)
        
        # Event subscribers
        self._subscribers: Dict[str, List[Callable]] = {}
        
        logger.info(f"LangGraphEventStreamer initialized for {agent_name}")
    
    async def stream_event(self, 
                          event_type: AURENEventType, 
                          data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Stream an event
        
        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional metadata
        """
        if not self.enable_streaming:
            return
            
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type.value if isinstance(event_type, AURENEventType) else str(event_type),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "data": data,
            "metadata": metadata or {}
        }
        
        # Store event
        self.event_stream.append(event)
        
        # Call callbacks
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        
        # Notify subscribers
        await self._notify_subscribers(event_type, event)
        
        logger.debug(f"Streamed event: {event_type.value}")
    
    def subscribe(self, event_type: AURENEventType, callback: Callable) -> None:
        """Subscribe to specific event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def _notify_subscribers(self, event_type: AURENEventType, event: Dict[str, Any]) -> None:
        """Notify all subscribers of an event"""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")
    
    def get_events(self, 
                   event_type: Optional[AURENEventType] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get stored events
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
        """
        events = self.event_stream
        
        if event_type:
            events = [e for e in events if e["type"] == event_type.value]
        
        if limit:
            events = events[-limit:]
            
        return events
    
    def clear_events(self) -> None:
        """Clear stored events"""
        self.event_stream = []
    
    async def agent_started(self, agent_data: Dict[str, Any]) -> None:
        """Convenience method for agent started event"""
        await self.stream_event(
            AURENEventType.AGENT_STARTED,
            {
                "agent": self.agent_name,
                **agent_data
            }
        )
    
    async def agent_thinking(self, thought: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Convenience method for agent thinking event"""
        await self.stream_event(
            AURENEventType.AGENT_THINKING,
            {
                "thought": thought,
                "context": context or {}
            }
        )
    
    async def agent_acting(self, action: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Convenience method for agent acting event"""
        await self.stream_event(
            AURENEventType.AGENT_ACTING,
            {
                "action": action,
                "parameters": parameters or {}
            }
        )
    
    async def task_started(self, task_id: str, task_description: str) -> None:
        """Convenience method for task started event"""
        await self.stream_event(
            AURENEventType.TASK_STARTED,
            {
                "task_id": task_id,
                "description": task_description
            }
        )
    
    async def task_completed(self, task_id: str, output: Any) -> None:
        """Convenience method for task completed event"""
        await self.stream_event(
            AURENEventType.TASK_COMPLETED,
            {
                "task_id": task_id,
                "output": output
            }
        )
    
    async def memory_accessed(self, memory_type: str, key: str, value: Any) -> None:
        """Convenience method for memory accessed event"""
        await self.stream_event(
            AURENEventType.MEMORY_ACCESSED,
            {
                "memory_type": memory_type,
                "key": key,
                "value": value
            }
        )
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get metrics for the current session"""
        duration = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        event_counts = {}
        for event in self.event_stream:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "duration_seconds": duration,
            "total_events": len(self.event_stream),
            "event_counts": event_counts,
            "start_time": self._start_time.isoformat(),
            "current_time": datetime.now(timezone.utc).isoformat()
        }
    
    # Compatibility methods for CrewAI patterns
    def __call__(self, *args, **kwargs):
        """Make the class callable for compatibility"""
        return self
    
    @property
    def enabled(self) -> bool:
        """Check if streaming is enabled"""
        return self.enable_streaming
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable/disable streaming"""
        self.enable_streaming = value


# Alias for backward compatibility
LangGraphEventStreamer = LangGraphEventStreamer 