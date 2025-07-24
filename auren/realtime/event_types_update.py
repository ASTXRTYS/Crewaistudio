"""
Update to add MEMORY_TIER_ACCESS event type
This should be added to the existing AURENEventType enum in crewai_instrumentation.py
"""

from enum import Enum

# This is the updated AURENEventType enum with MEMORY_TIER_ACCESS added
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
    MEMORY_TIER_ACCESS = "memory_tier_access"  # NEW: Added for memory tier tracking

# Example of how the event is used in memory tier tracking
async def emit_memory_tier_event(event_streamer, tier_data):
    """Example of emitting a memory tier access event"""
    
    from auren.realtime.crewai_instrumentation import AURENStreamEvent
    from datetime import datetime, timezone
    import uuid
    
    event = AURENStreamEvent(
        event_id=str(uuid.uuid4()),
        trace_id=tier_data.get('trace_id'),
        session_id=tier_data.get('session_id'),
        timestamp=datetime.now(timezone.utc),
        event_type=AURENEventType.MEMORY_TIER_ACCESS,  # Using the new event type
        source_agent={"id": tier_data.get('agent_id', 'memory_system')},
        target_agent=None,
        payload={
            'query': tier_data['query'],
            'tier_accessed': tier_data['tier_accessed'],
            'tier_latencies': tier_data['tier_latencies'],
            'total_latency_ms': tier_data['total_latency_ms'],
            'cache_hit': tier_data['cache_hit'],
            'query_type': tier_data['query_type'],
            'result_count': tier_data['result_count']
        },
        metadata={
            'cache_effectiveness': tier_data.get('cache_effectiveness', 0.0),
            'optimization_available': len(tier_data.get('optimization_suggestions', [])) > 0
        },
        user_id=tier_data.get('user_id')
    )
    
    await event_streamer.stream_event(event) 