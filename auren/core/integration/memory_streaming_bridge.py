"""
Memory-Streaming Bridge
Connects the three-tier memory system to WebSocket streaming for real-time dashboard updates
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from ..memory import UnifiedMemorySystem
from ..streaming.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer, ClientSubscription
from ..streaming.crewai_instrumentation import AURENStreamEvent, AURENEventType

logger = logging.getLogger(__name__)


@dataclass
class MemoryEvent:
    """Memory system event for streaming"""
    event_type: str
    tier: str
    memory_id: str
    agent_id: str
    user_id: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_stream_event(self) -> AURENStreamEvent:
        """Convert to AUREN stream event format"""
        return AURENStreamEvent(
            event_type=AURENEventType.INTELLIGENCE_EVENT,
            timestamp=self.timestamp,
            event_id=f"mem_{self.memory_id}_{int(self.timestamp.timestamp())}",
            source="memory_system",
            data={
                "memory_event_type": self.event_type,
                "tier": self.tier,
                "memory_id": self.memory_id,
                "agent_id": self.agent_id,
                "user_id": self.user_id,
                "metadata": self.metadata
            }
        )


class MemoryStreamingBridge:
    """
    Bridge between UnifiedMemorySystem and WebSocket streaming
    
    Features:
    - Real-time memory event broadcasting
    - Dashboard integration
    - Performance metrics
    - Event filtering and routing
    """
    
    def __init__(self,
                 memory_system: UnifiedMemorySystem,
                 websocket_streamer: EnhancedWebSocketEventStreamer):
        self.memory_system = memory_system
        self.websocket_streamer = websocket_streamer
        self._connected = False
        
        # Event queue for buffering
        self.event_queue = asyncio.Queue(maxsize=1000)
        
        # Metrics
        self.events_processed = 0
        self.events_dropped = 0
        
    async def connect(self):
        """Connect memory system to streaming"""
        if self._connected:
            return
        
        try:
            # Set this bridge as the event emitter for memory system
            self.memory_system.event_streamer = self
            
            # Also set for individual tiers
            self.memory_system.redis_tier.event_emitter = self
            self.memory_system.postgres_tier.event_emitter = self
            self.memory_system.chromadb_tier.event_emitter = self
            
            # Start event processing task
            asyncio.create_task(self._process_events())
            
            self._connected = True
            logger.info("Memory-Streaming bridge connected successfully")
            
            # Send initial connection event
            await self.emit({
                'type': 'bridge_connected',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': {
                    'bridge': 'memory_streaming',
                    'status': 'active'
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to connect memory-streaming bridge: {e}")
            raise
    
    async def emit(self, event_data: Dict[str, Any]):
        """
        Emit event from memory system to WebSocket
        
        This is called by the memory system when events occur
        """
        try:
            # Add to queue for processing
            if self.event_queue.full():
                self.events_dropped += 1
                logger.warning("Event queue full, dropping event")
                return
            
            await self.event_queue.put(event_data)
            
        except Exception as e:
            logger.error(f"Failed to emit memory event: {e}")
    
    async def _process_events(self):
        """Process events from memory system and send to WebSocket"""
        while True:
            try:
                # Get event from queue
                event_data = await self.event_queue.get()
                
                # Parse event type
                event_type = event_data.get('type', 'unknown')
                timestamp = event_data.get('timestamp', datetime.now(timezone.utc).isoformat())
                data = event_data.get('data', {})
                
                # Extract tier information
                tier = 'unknown'
                if 'redis_tier' in event_type:
                    tier = 'redis'
                elif 'postgres_tier' in event_type:
                    tier = 'postgresql'
                elif 'chromadb_tier' in event_type:
                    tier = 'chromadb'
                elif 'unified_memory' in event_type:
                    tier = 'unified'
                
                # Create memory event
                memory_event = MemoryEvent(
                    event_type=event_type,
                    tier=tier,
                    memory_id=data.get('memory_id', ''),
                    agent_id=data.get('agent_id', ''),
                    user_id=data.get('user_id', ''),
                    timestamp=datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp,
                    metadata=data
                )
                
                # Convert to stream event
                stream_event = memory_event.to_stream_event()
                
                # Send to WebSocket clients
                await self._broadcast_event(stream_event)
                
                # Track metrics
                self.events_processed += 1
                
                # Specific handling for different event types
                if event_type == 'memory_stored':
                    await self._handle_memory_stored(memory_event)
                elif event_type == 'memory_retrieved':
                    await self._handle_memory_retrieved(memory_event)
                elif event_type == 'memory_promoted':
                    await self._handle_memory_promoted(memory_event)
                elif event_type == 'memory_evicted':
                    await self._handle_memory_evicted(memory_event)
                elif event_type == 'patterns_discovered':
                    await self._handle_patterns_discovered(memory_event)
                
            except Exception as e:
                logger.error(f"Error processing memory event: {e}")
                await asyncio.sleep(0.1)  # Prevent tight loop on errors
    
    async def _broadcast_event(self, event: AURENStreamEvent):
        """Broadcast event to WebSocket clients"""
        try:
            # Get interested clients
            subscriptions = [
                ClientSubscription.ALL_EVENTS,
                ClientSubscription.INTELLIGENCE_EVENTS,
                ClientSubscription.AGENT_ACTIVITY
            ]
            
            # Find all clients interested in this event
            client_ids = set()
            for sub in subscriptions:
                client_ids.update(self.websocket_streamer.subscription_map.get(sub, set()))
            
            # Also find clients interested in specific agents
            agent_id = event.data.get('agent_id')
            if agent_id:
                agent_clients = self.websocket_streamer.agent_connections.get(agent_id, set())
                client_ids.update(agent_clients)
            
            # Send to all interested clients
            for client_id in client_ids:
                client = self.websocket_streamer.active_connections.get(client_id)
                if client:
                    try:
                        await client.websocket.send(json.dumps(asdict(event)))
                    except Exception as e:
                        logger.warning(f"Failed to send to client {client_id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast memory event: {e}")
    
    async def _handle_memory_stored(self, event: MemoryEvent):
        """Handle memory stored events"""
        # Create dashboard-specific event
        dashboard_event = AURENStreamEvent(
            event_type=AURENEventType.INTELLIGENCE_EVENT,
            timestamp=event.timestamp,
            event_id=f"mem_stored_{event.memory_id}",
            source="memory_system",
            data={
                "event": "memory_stored",
                "tier": event.tier,
                "memory_id": event.memory_id,
                "agent_id": event.agent_id,
                "user_id": event.user_id,
                "priority": event.metadata.get('priority', 1.0),
                "confidence": event.metadata.get('confidence', 1.0),
                "memory_type": event.metadata.get('memory_type', 'unknown')
            }
        )
        
        # Add to agent activity buffer
        self.websocket_streamer.event_buffers['agent_activity'].append(asdict(dashboard_event))
    
    async def _handle_memory_retrieved(self, event: MemoryEvent):
        """Handle memory retrieved events"""
        # Track access patterns
        dashboard_event = AURENStreamEvent(
            event_type=AURENEventType.AGENT_ACTIVITY,
            timestamp=event.timestamp,
            event_id=f"mem_retrieved_{event.memory_id}",
            source="memory_system",
            data={
                "event": "memory_accessed",
                "tier": event.tier,
                "memory_id": event.memory_id,
                "agent_id": event.agent_id,
                "access_count": event.metadata.get('access_count', 0)
            }
        )
        
        await self._broadcast_event(dashboard_event)
    
    async def _handle_memory_promoted(self, event: MemoryEvent):
        """Handle memory promotion events"""
        dashboard_event = AURENStreamEvent(
            event_type=AURENEventType.SYSTEM_EVENT,
            timestamp=event.timestamp,
            event_id=f"mem_promoted_{event.memory_id}",
            source="memory_system",
            data={
                "event": "memory_promoted",
                "memory_id": event.memory_id,
                "from_tier": event.metadata.get('from_tier', 'unknown'),
                "to_tier": event.metadata.get('to_tier', 'unknown'),
                "reason": event.metadata.get('reason', 'tier_transition')
            }
        )
        
        # Add to system buffer
        self.websocket_streamer.event_buffers['system'].append(asdict(dashboard_event))
    
    async def _handle_memory_evicted(self, event: MemoryEvent):
        """Handle memory eviction events"""
        dashboard_event = AURENStreamEvent(
            event_type=AURENEventType.SYSTEM_EVENT,
            timestamp=event.timestamp,
            event_id=f"mem_evicted_{event.memory_id}",
            source="memory_system",
            data={
                "event": "memory_evicted",
                "memory_id": event.memory_id,
                "tier": event.tier,
                "reason": event.metadata.get('reason', 'memory_pressure'),
                "priority": event.metadata.get('priority', 0)
            }
        )
        
        await self._broadcast_event(dashboard_event)
    
    async def _handle_patterns_discovered(self, event: MemoryEvent):
        """Handle pattern discovery events"""
        dashboard_event = AURENStreamEvent(
            event_type=AURENEventType.INTELLIGENCE_EVENT,
            timestamp=event.timestamp,
            event_id=f"patterns_{event.user_id}_{int(event.timestamp.timestamp())}",
            source="memory_system",
            data={
                "event": "patterns_discovered",
                "user_id": event.user_id,
                "patterns_count": event.metadata.get('patterns_count', 0),
                "memories_analyzed": event.metadata.get('total_memories_clustered', 0),
                "tier": "chromadb"
            }
        )
        
        # Add to intelligence buffer
        self.websocket_streamer.event_buffers['performance'].append(asdict(dashboard_event))
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics"""
        return {
            "connected": self._connected,
            "events_processed": self.events_processed,
            "events_dropped": self.events_dropped,
            "queue_size": self.event_queue.qsize(),
            "active_connections": len(self.websocket_streamer.active_connections),
            "subscriptions": {
                sub.value: len(clients) 
                for sub, clients in self.websocket_streamer.subscription_map.items()
            }
        }
    
    async def close(self):
        """Close the bridge"""
        self._connected = False
        logger.info("Memory-Streaming bridge closed") 