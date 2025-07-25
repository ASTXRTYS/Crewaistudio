"""
Production WebSocket server with enhanced agent monitoring capabilities
Combines the best of real-time streaming with agent-specific telemetry
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
import jwt
from collections import defaultdict, deque
import uuid

from auren.realtime.crewai_instrumentation import AURENStreamEvent, AURENEventType, AURENPerformanceMetrics
from auren.realtime.multi_protocol_streaming import EventStreamer

logger = logging.getLogger(__name__)

class ClientSubscription(Enum):
    """Enhanced client subscription types"""
    ALL_EVENTS = "all_events"
    AGENT_ACTIVITY = "agent_activity"
    AGENT_COLLABORATION = "agent_collaboration"
    AGENT_PERFORMANCE = "agent_performance"
    BIOMETRIC_STREAM = "biometric_stream"
    INTELLIGENCE_EVENTS = "intelligence_events"
    SYSTEM_MONITORING = "system_monitoring"
    USER_SPECIFIC = "user_specific"
    LLM_USAGE = "llm_usage"
    TOOL_USAGE = "tool_usage"

@dataclass
class EnhancedClientConnection:
    """Enhanced WebSocket client connection with agent monitoring features"""
    connection_id: str
    websocket: WebSocketServerProtocol
    user_id: str
    subscriptions: Set[ClientSubscription]
    connected_at: datetime
    last_ping: datetime
    is_authenticated: bool = False
    rate_limit_tokens: int = 100
    agent_filter: Set[str] = None  # Filter by specific agents
    performance_threshold: float = 0.0  # Only show events above threshold
    
    def __post_init__(self):
        if not hasattr(self, 'subscriptions'):
            self.subscriptions = set()
        if self.agent_filter is None:
            self.agent_filter = set()

class EnhancedWebSocketEventStreamer:
    """
    Enhanced WebSocket server with agent-specific monitoring and performance analytics
    
    Features:
    - Agent-specific filtering and subscriptions
    - Performance threshold filtering
    - Enhanced collaboration event tracking
    - Real-time agent performance metrics
    - Advanced rate limiting and connection management
    """
    
    def __init__(self,
                 host: str = "localhost",
                 port: int = 8765,
                 event_streamer: EventStreamer = None,
                 jwt_secret: str = "auren_secret",
                 max_connections: int = 1000,
                 rate_limit_per_minute: int = 1000):
        self.host = host
        self.port = port
        self.event_streamer = event_streamer
        self.jwt_secret = jwt_secret
        self.max_connections = max_connections
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Enhanced connection management
        self.active_connections: Dict[str, EnhancedClientConnection] = {}
        self.subscription_map: Dict[ClientSubscription, Set[str]] = defaultdict(set)
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.agent_connections: Dict[str, Set[str]] = defaultdict(set)  # Connections interested in specific agents
        
        # Enhanced event buffering with categories
        self.event_buffers = {
            "agent_activity": deque(maxlen=500),
            "collaboration": deque(maxlen=200),
            "performance": deque(maxlen=300),
            "system": deque(maxlen=200)
        }
        
        # Real-time performance tracking
        self.connection_count = 0
        self.events_sent = 0
        self.agent_performance_cache = {}
        self.collaboration_metrics = {}
        self.last_activity = datetime.now(timezone.utc)
    
    async def start_server(self) -> None:
        """Start the enhanced WebSocket server"""
        
        logger.info(f"Starting enhanced WebSocket server on {self.host}:{self.port}")
        
        # Start background tasks
        asyncio.create_task(self._connection_health_monitor())
        asyncio.create_task(self._rate_limit_refresh())
        asyncio.create_task(self._performance_metrics_collector())
        
        if self.event_streamer:
            asyncio.create_task(self._event_stream_listener())
        
        # Start WebSocket server
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            max_size=2**20,  # 1MB max message size
            compression="deflate"
        ):
            logger.info("Enhanced WebSocket server started successfully")
            await asyncio.Future()  # Run forever
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Handle new WebSocket connection with enhanced authentication"""
        
        connection_id = str(uuid.uuid4())
        
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(1013, "Server at capacity")
            return
        
        try:
            # Wait for authentication
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)
            
            # Enhanced authentication
            user_id, permissions = await self._authenticate_connection(auth_data)
            if not user_id:
                await websocket.close(1008, "Authentication failed")
                return
            
            # Create enhanced connection record
            connection = EnhancedClientConnection(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                subscriptions=set(),
                connected_at=datetime.now(timezone.utc),
                last_ping=datetime.now(timezone.utc),
                is_authenticated=True,
                agent_filter=set(auth_data.get("agent_filter", [])),
                performance_threshold=auth_data.get("performance_threshold", 0.0)
            )
            
            self.active_connections[connection_id] = connection
            self.user_connections[user_id].add(connection_id)
            self.connection_count += 1
            
            # Register agent-specific connections
            for agent_id in connection.agent_filter:
                self.agent_connections[agent_id].add(connection_id)
            
            # Send enhanced connection confirmation
            await self._send_to_connection(connection, {
                "type": "connection_established",
                "connection_id": connection_id,
                "server_time": datetime.now(timezone.utc).isoformat(),
                "available_subscriptions": [sub.value for sub in ClientSubscription],
                "agent_filter": list(connection.agent_filter),
                "performance_threshold": connection.performance_threshold
            })
            
            # Handle connection messages
            await self._handle_connection_messages(connection)
            
        except asyncio.TimeoutError:
            await websocket.close(1008, "Authentication timeout")
        except ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await websocket.close(1011, "Internal server error")
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _authenticate_connection(self, auth_data: Dict[str, Any]) -> tuple[Optional[str], Dict[str, Any]]:
        """Enhanced authentication with permissions"""
        
        try:
            token = auth_data.get("token")
            if not token:
                return None, {}
            
            # For testing/development, accept test tokens
            if token.startswith("test"):
                return "test_user", {"permissions": ["all"]}
            
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload.get("user_id")
            permissions = payload.get("permissions", {})
            
            # Additional validation could be added here
            return user_id, permissions
            
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token provided")
            return None, {}
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None, {}
    
    async def _handle_connection_messages(self, connection: EnhancedClientConnection) -> None:
        """Handle incoming messages from client"""
        
        try:
            async for message in connection.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "subscribe":
                        await self._handle_subscription(connection, data)
                    elif message_type == "unsubscribe":
                        await self._handle_unsubscription(connection, data)
                    elif message_type == "ping":
                        connection.last_ping = datetime.now(timezone.utc)
                        await self._send_to_connection(connection, {"type": "pong"})
                    elif message_type == "filter_update":
                        await self._handle_filter_update(connection, data)
                    elif message_type == "get_recent":
                        await self._handle_recent_events_request(connection, data)
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from client")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except ConnectionClosed:
            logger.info(f"Connection {connection.connection_id} closed")
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
    
    async def _handle_subscription(self, connection: EnhancedClientConnection, data: Dict) -> None:
        """Handle subscription request"""
        
        subscription_type = data.get("subscription")
        if not subscription_type:
            return
        
        try:
            sub = ClientSubscription(subscription_type)
            connection.subscriptions.add(sub)
            self.subscription_map[sub].add(connection.connection_id)
            
            await self._send_to_connection(connection, {
                "type": "subscription_confirmed",
                "subscription": subscription_type
            })
            
            logger.info(f"Connection {connection.connection_id} subscribed to {subscription_type}")
            
        except ValueError:
            logger.warning(f"Invalid subscription type: {subscription_type}")
    
    async def _handle_unsubscription(self, connection: EnhancedClientConnection, data: Dict) -> None:
        """Handle unsubscription request"""
        
        subscription_type = data.get("subscription")
        if not subscription_type:
            return
        
        try:
            sub = ClientSubscription(subscription_type)
            connection.subscriptions.discard(sub)
            self.subscription_map[sub].discard(connection.connection_id)
            
            await self._send_to_connection(connection, {
                "type": "unsubscription_confirmed",
                "subscription": subscription_type
            })
            
        except ValueError:
            pass
    
    async def _handle_filter_update(self, connection: EnhancedClientConnection, data: Dict) -> None:
        """Handle filter update request"""
        
        # Update agent filter
        new_agent_filter = set(data.get("agent_filter", []))
        old_agent_filter = connection.agent_filter
        
        # Remove from old agent connections
        for agent_id in old_agent_filter - new_agent_filter:
            self.agent_connections[agent_id].discard(connection.connection_id)
        
        # Add to new agent connections
        for agent_id in new_agent_filter - old_agent_filter:
            self.agent_connections[agent_id].add(connection.connection_id)
        
        connection.agent_filter = new_agent_filter
        
        # Update performance threshold
        connection.performance_threshold = data.get("performance_threshold", 0.0)
        
        await self._send_to_connection(connection, {
            "type": "filter_updated",
            "agent_filter": list(connection.agent_filter),
            "performance_threshold": connection.performance_threshold
        })
    
    async def _handle_recent_events_request(self, connection: EnhancedClientConnection, data: Dict) -> None:
        """Handle request for recent events"""
        
        if not self.event_streamer:
            return
        
        limit = min(data.get("limit", 100), 1000)  # Cap at 1000
        event_types = data.get("event_types", [])
        
        recent_events = await self.event_streamer.get_recent_events(limit, event_types)
        
        await self._send_to_connection(connection, {
            "type": "recent_events",
            "events": recent_events,
            "count": len(recent_events)
        })
    
    async def broadcast_event(self, event: AURENStreamEvent) -> None:
        """Enhanced event broadcasting with agent-specific filtering"""
        
        # Add to appropriate event buffer
        buffer_key = self._determine_event_buffer(event)
        if buffer_key in self.event_buffers:
            self.event_buffers[buffer_key].append(event)
        
        # Update performance cache if it's a performance event
        if event.performance_metrics:
            self._update_performance_cache(event)
        
        # Update collaboration metrics if it's a collaboration event
        if event.event_type == AURENEventType.AGENT_COLLABORATION:
            self._update_collaboration_metrics(event)
        
        # Determine target connections with enhanced filtering
        target_connections = await self._determine_target_connections(event)
        
        # Send to target connections
        event_data = {
            "type": "stream_event",
            "event": self._serialize_event_for_client(event)
        }
        
        sent_count = 0
        for connection_id in target_connections:
            connection = self.active_connections.get(connection_id)
            if connection and await self._send_to_connection(connection, event_data):
                sent_count += 1
        
        self.events_sent += sent_count
        self.last_activity = datetime.now(timezone.utc)
        
        logger.debug(f"Broadcast event {event.event_id} to {sent_count} connections")
    
    async def _determine_target_connections(self, event: AURENStreamEvent) -> Set[str]:
        """Enhanced connection targeting with agent filtering"""
        
        target_connections = set()
        
        # Add connections subscribed to all events
        target_connections.update(self.subscription_map[ClientSubscription.ALL_EVENTS])
        
        # Add connections subscribed to specific event types
        if event.event_type in [AURENEventType.AGENT_EXECUTION_STARTED, AURENEventType.AGENT_EXECUTION_COMPLETED, AURENEventType.AGENT_DECISION]:
            target_connections.update(self.subscription_map[ClientSubscription.AGENT_ACTIVITY])
        
        if event.event_type == AURENEventType.AGENT_COLLABORATION:
            target_connections.update(self.subscription_map[ClientSubscription.AGENT_COLLABORATION])
        
        if event.performance_metrics:
            target_connections.update(self.subscription_map[ClientSubscription.AGENT_PERFORMANCE])
        
        if event.event_type == AURENEventType.LLM_CALL:
            target_connections.update(self.subscription_map[ClientSubscription.LLM_USAGE])
        
        if event.event_type == AURENEventType.TOOL_USAGE:
            target_connections.update(self.subscription_map[ClientSubscription.TOOL_USAGE])
        
        # Add agent-specific connections
        if event.source_agent and event.source_agent.get("id"):
            agent_id = event.source_agent["id"]
            target_connections.update(self.agent_connections.get(agent_id, set()))
        
        # Add user-specific connections if event has user_id
        if event.user_id:
            target_connections.update(self.user_connections.get(event.user_id, set()))
        
        # Filter by performance threshold and agent filters
        filtered_connections = set()
        for connection_id in target_connections:
            connection = self.active_connections.get(connection_id)
            if not connection:
                continue
            
            # Check performance threshold
            if (connection.performance_threshold > 0.0 and 
                event.performance_metrics and 
                event.performance_metrics.confidence_score < connection.performance_threshold):
                continue
            
            # Check agent filter
            if (connection.agent_filter and 
                event.source_agent and 
                event.source_agent.get("id") not in connection.agent_filter):
                continue
            
            filtered_connections.add(connection_id)
        
        return filtered_connections
    
    def _determine_event_buffer(self, event: AURENStreamEvent) -> str:
        """Determine which buffer to use for the event"""
        
        if event.event_type == AURENEventType.AGENT_COLLABORATION:
            return "collaboration"
        elif event.performance_metrics:
            return "performance"
        elif event.event_type in [AURENEventType.AGENT_EXECUTION_STARTED, AURENEventType.AGENT_EXECUTION_COMPLETED, AURENEventType.AGENT_DECISION]:
            return "agent_activity"
        else:
            return "system"
    
    def _update_performance_cache(self, event: AURENStreamEvent):
        """Update real-time performance cache"""
        
        if not event.performance_metrics or not event.source_agent:
            return
        
        agent_id = event.source_agent.get("id")
        if not agent_id:
            return
        
        if agent_id not in self.agent_performance_cache:
            self.agent_performance_cache[agent_id] = {
                "recent_latencies": deque(maxlen=20),
                "recent_successes": deque(maxlen=20),
                "total_operations": 0,
                "total_success": 0,
                "last_update": datetime.now(timezone.utc)
            }
        
        cache = self.agent_performance_cache[agent_id]
        cache["recent_latencies"].append(event.performance_metrics.latency_ms)
        cache["recent_successes"].append(event.performance_metrics.success)
        cache["total_operations"] += 1
        if event.performance_metrics.success:
            cache["total_success"] += 1
        cache["last_update"] = datetime.now(timezone.utc)
    
    def _update_collaboration_metrics(self, event: AURENStreamEvent):
        """Update collaboration metrics"""
        
        if event.event_type != AURENEventType.AGENT_COLLABORATION:
            return
        
        payload = event.payload
        primary_agent = payload.get("primary_agent")
        collaborating_agents = payload.get("collaborating_agents", [])
        
        for agent in [primary_agent] + collaborating_agents:
            if agent not in self.collaboration_metrics:
                self.collaboration_metrics[agent] = {
                    "total_collaborations": 0,
                    "successful_collaborations": 0,
                    "partners": set(),
                    "last_collaboration": datetime.now(timezone.utc)
                }
            
            metrics = self.collaboration_metrics[agent]
            metrics["total_collaborations"] += 1
            if payload.get("consensus_reached", False):
                metrics["successful_collaborations"] += 1
            metrics["partners"].update(collaborating_agents)
            metrics["last_collaboration"] = datetime.now(timezone.utc)
    
    def _serialize_event_for_client(self, event: AURENStreamEvent) -> Dict[str, Any]:
        """Serialize event for client with performance data"""
        
        serialized = {
            "event_id": event.event_id,
            "trace_id": event.trace_id,
            "session_id": event.session_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "source_agent": event.source_agent,
            "target_agent": event.target_agent,
            "payload": event.payload,
            "metadata": event.metadata,
            "user_id": event.user_id
        }
        
        if event.performance_metrics:
            serialized["performance_metrics"] = asdict(event.performance_metrics)
        
        return serialized
    
    async def _send_to_connection(self, connection: EnhancedClientConnection, data: Dict) -> bool:
        """Send data to a specific connection with rate limiting"""
        
        # Check rate limit
        if connection.rate_limit_tokens <= 0:
            logger.warning(f"Rate limit exceeded for connection {connection.connection_id}")
            return False
        
        try:
            await connection.websocket.send(json.dumps(data))
            connection.rate_limit_tokens -= 1
            return True
        except Exception as e:
            logger.error(f"Error sending to connection {connection.connection_id}: {e}")
            return False
    
    async def _cleanup_connection(self, connection_id: str) -> None:
        """Clean up connection on disconnect"""
        
        connection = self.active_connections.get(connection_id)
        if not connection:
            return
        
        # Remove from all tracking structures
        del self.active_connections[connection_id]
        self.user_connections[connection.user_id].discard(connection_id)
        
        for sub in connection.subscriptions:
            self.subscription_map[sub].discard(connection_id)
        
        for agent_id in connection.agent_filter:
            self.agent_connections[agent_id].discard(connection_id)
        
        self.connection_count -= 1
        logger.info(f"Cleaned up connection {connection_id}")
    
    async def _connection_health_monitor(self) -> None:
        """Monitor connection health and clean up stale connections"""
        
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                now = datetime.now(timezone.utc)
                stale_connections = []
                
                for conn_id, connection in self.active_connections.items():
                    # Check if connection is stale (no ping in 60 seconds)
                    if (now - connection.last_ping).total_seconds() > 60:
                        stale_connections.append(conn_id)
                
                # Clean up stale connections
                for conn_id in stale_connections:
                    logger.warning(f"Cleaning up stale connection {conn_id}")
                    await self._cleanup_connection(conn_id)
                    
            except Exception as e:
                logger.error(f"Error in connection health monitor: {e}")
    
    async def _rate_limit_refresh(self) -> None:
        """Refresh rate limit tokens periodically"""
        
        while True:
            await asyncio.sleep(60)  # Refresh every minute
            
            for connection in self.active_connections.values():
                connection.rate_limit_tokens = min(
                    self.rate_limit_per_minute,
                    connection.rate_limit_tokens + self.rate_limit_per_minute
                )
    
    async def _performance_metrics_collector(self):
        """Background task to collect and broadcast performance metrics"""
        
        while True:
            try:
                await asyncio.sleep(30)  # Collect every 30 seconds
                
                # Generate performance summary
                performance_summary = self._generate_performance_summary()
                
                # Broadcast to performance subscribers
                target_connections = self.subscription_map[ClientSubscription.AGENT_PERFORMANCE]
                
                performance_event = {
                    "type": "performance_summary",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": performance_summary
                }
                
                for connection_id in target_connections:
                    connection = self.active_connections.get(connection_id)
                    if connection:
                        await self._send_to_connection(connection, performance_event)
                
            except Exception as e:
                logger.error(f"Performance metrics collector error: {e}")
    
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate real-time performance summary"""
        
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": {},
            "system": {
                "active_connections": len(self.active_connections),
                "events_sent": self.events_sent,
                "uptime_seconds": (datetime.now(timezone.utc) - self.last_activity).total_seconds()
            }
        }
        
        # Agent performance summaries
        for agent_id, cache in self.agent_performance_cache.items():
            if cache["recent_latencies"]:
                avg_latency = sum(cache["recent_latencies"]) / len(cache["recent_latencies"])
                success_rate = sum(cache["recent_successes"]) / len(cache["recent_successes"])
                
                summary["agents"][agent_id] = {
                    "average_latency_ms": avg_latency,
                    "success_rate": success_rate,
                    "total_operations": cache["total_operations"],
                    "last_update": cache["last_update"].isoformat()
                }
        
        # Collaboration summaries
        summary["collaboration"] = {}
        for agent_id, metrics in self.collaboration_metrics.items():
            if metrics["total_collaborations"] > 0:
                success_rate = metrics["successful_collaborations"] / metrics["total_collaborations"]
                summary["collaboration"][agent_id] = {
                    "total_collaborations": metrics["total_collaborations"],
                    "success_rate": success_rate,
                    "unique_partners": len(metrics["partners"]),
                    "last_collaboration": metrics["last_collaboration"].isoformat()
                }
        
        return summary
    
    async def _event_stream_listener(self):
        """Listen for events from the event streamer"""
        
        if not self.event_streamer:
            return
        
        try:
            consumer_id = f"websocket_server_{datetime.now().timestamp()}"
            
            async for event_data in self.event_streamer.subscribe_to_events(consumer_id):
                try:
                    # Convert event data back to AURENStreamEvent
                    event = self._deserialize_event(event_data)
                    if event:
                        await self.broadcast_event(event)
                        
                except Exception as e:
                    logger.error(f"Error processing streamed event: {e}")
                    
        except Exception as e:
            logger.error(f"Event stream listener error: {e}")
    
    def _deserialize_event(self, event_data: Dict) -> Optional[AURENStreamEvent]:
        """Deserialize event data from stream"""
        
        try:
            # Parse performance metrics if present
            performance_metrics = None
            if "performance_metrics" in event_data and event_data["performance_metrics"]:
                performance_metrics = AURENPerformanceMetrics(**event_data["performance_metrics"])
            
            return AURENStreamEvent(
                event_id=event_data["event_id"],
                trace_id=event_data.get("trace_id"),
                session_id=event_data.get("session_id"),
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                event_type=AURENEventType(event_data["event_type"]),
                source_agent=event_data.get("source_agent"),
                target_agent=event_data.get("target_agent"),
                payload=event_data["payload"],
                metadata=event_data["metadata"],
                performance_metrics=performance_metrics,
                user_id=event_data.get("user_id")
            )
            
        except Exception as e:
            logger.error(f"Error deserializing event: {e}")
            return None


# Helper function to run the WebSocket server
async def run_websocket_server(host: str = "localhost", 
                              port: int = 8765,
                              event_streamer: EventStreamer = None) -> None:
    """Helper function to run the WebSocket server"""
    
    server = EnhancedWebSocketEventStreamer(
        host=host,
        port=port,
        event_streamer=event_streamer
    )
    
    await server.start_server()


if __name__ == "__main__":
    # Example usage
    asyncio.run(run_websocket_server()) 