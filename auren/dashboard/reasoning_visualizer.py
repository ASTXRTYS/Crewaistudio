"""
auren/dashboard/reasoning_visualizer.py
Real-time reasoning chain visualization for AI transparency
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import networkx as nx
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReasoningNode:
    """Represents a single step in the reasoning chain"""
    node_id: str
    timestamp: datetime
    node_type: str  # "hypothesis", "tool_use", "memory_access", "decision"
    content: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "node_type": self.node_type,
            "content": self.content,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "children": self.children,
            "parent": self.parent
        }


class ReasoningChainVisualizer:
    """
    Builds and maintains reasoning chains from agent events
    Think of this as creating a mind map of the AI's thought process
    """
    
    def __init__(self):
        self.chains = {}  # session_id -> nx.DiGraph
        self.active_nodes = {}  # session_id -> current_node_id
        self.node_store = {}  # node_id -> ReasoningNode
        
    async def process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an event and update reasoning chains
        Returns visualization update if chain changed
        """
        event_type = event.get("event_type")
        session_id = event.get("session_id")
        
        if not session_id:
            return None
            
        # Initialize chain if needed
        if session_id not in self.chains:
            self.chains[session_id] = nx.DiGraph()
            
        # Route to appropriate handler
        handlers = {
            "hypothesis_formed": self._handle_hypothesis,
            "tool_usage": self._handle_tool_usage,
            "memory_accessed": self._handle_memory_access,
            "decision_made": self._handle_decision,
            "agent_execution_started": self._handle_execution_start,
            "agent_execution_completed": self._handle_execution_complete
        }
        
        handler = handlers.get(event_type)
        if handler:
            node = await handler(event)
            if node:
                return self._create_visualization_update(session_id, node)
                
        return None
        
    async def _handle_hypothesis(self, event: Dict[str, Any]) -> Optional[ReasoningNode]:
        """Handle hypothesis formation events"""
        session_id = event["session_id"]
        
        node = ReasoningNode(
            node_id=event.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(event["timestamp"]),
            node_type="hypothesis",
            content=event["data"].get("hypothesis", ""),
            confidence=event["data"].get("confidence", 0.5),
            metadata={
                "evidence": event["data"].get("evidence", []),
                "reasoning": event["data"].get("reasoning", "")
            }
        )
        
        # Link to parent if exists
        if session_id in self.active_nodes:
            parent_id = self.active_nodes[session_id]
            node.parent = parent_id
            if parent_id in self.node_store:
                self.node_store[parent_id].children.append(node.node_id)
                
        # Add to graph
        self.chains[session_id].add_node(node.node_id, data=node)
        if node.parent:
            self.chains[session_id].add_edge(node.parent, node.node_id)
            
        # Store and update active
        self.node_store[node.node_id] = node
        self.active_nodes[session_id] = node.node_id
        
        return node
        
    async def _handle_tool_usage(self, event: Dict[str, Any]) -> Optional[ReasoningNode]:
        """Handle tool usage events"""
        session_id = event["session_id"]
        
        node = ReasoningNode(
            node_id=event.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(event["timestamp"]),
            node_type="tool_use",
            content=f"Using {event['data'].get('tool_name', 'unknown tool')}",
            confidence=1.0,  # Tool usage is deterministic
            metadata={
                "tool_name": event["data"].get("tool_name"),
                "input": event["data"].get("input", ""),
                "output": event["data"].get("output", ""),
                "tokens_used": event["data"].get("tokens_used", 0)
            }
        )
        
        # Link to parent
        if session_id in self.active_nodes:
            parent_id = self.active_nodes[session_id]
            node.parent = parent_id
            if parent_id in self.node_store:
                self.node_store[parent_id].children.append(node.node_id)
                
        # Add to graph
        self.chains[session_id].add_node(node.node_id, data=node)
        if node.parent:
            self.chains[session_id].add_edge(node.parent, node.node_id)
            
        self.node_store[node.node_id] = node
        
        # Don't update active node for tool usage (it's a side branch)
        return node
        
    async def _handle_memory_access(self, event: Dict[str, Any]) -> Optional[ReasoningNode]:
        """Handle memory access events"""
        session_id = event["session_id"]
        
        node = ReasoningNode(
            node_id=event.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(event["timestamp"]),
            node_type="memory_access",
            content=f"Accessing memory: {event['data'].get('memory_type', 'unknown')}",
            confidence=1.0,
            metadata={
                "memory_type": event["data"].get("memory_type"),
                "query": event["data"].get("query", ""),
                "results_count": event["data"].get("results_count", 0)
            }
        )
        
        # Similar linking logic
        if session_id in self.active_nodes:
            parent_id = self.active_nodes[session_id]
            node.parent = parent_id
            if parent_id in self.node_store:
                self.node_store[parent_id].children.append(node.node_id)
                
        self.chains[session_id].add_node(node.node_id, data=node)
        if node.parent:
            self.chains[session_id].add_edge(node.parent, node.node_id)
            
        self.node_store[node.node_id] = node
        
        return node
        
    async def _handle_decision(self, event: Dict[str, Any]) -> Optional[ReasoningNode]:
        """Handle decision-making events"""
        session_id = event["session_id"]
        
        node = ReasoningNode(
            node_id=event.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(event["timestamp"]),
            node_type="decision",
            content=event["data"].get("decision", ""),
            confidence=event["data"].get("confidence", 0.7),
            metadata={
                "alternatives_considered": event["data"].get("alternatives", []),
                "rationale": event["data"].get("rationale", "")
            }
        )
        
        # Link and add
        if session_id in self.active_nodes:
            parent_id = self.active_nodes[session_id]
            node.parent = parent_id
            if parent_id in self.node_store:
                self.node_store[parent_id].children.append(node.node_id)
                
        self.chains[session_id].add_node(node.node_id, data=node)
        if node.parent:
            self.chains[session_id].add_edge(node.parent, node.node_id)
            
        self.node_store[node.node_id] = node
        self.active_nodes[session_id] = node.node_id
        
        return node
        
    async def _handle_execution_start(self, event: Dict[str, Any]) -> Optional[ReasoningNode]:
        """Handle agent execution start"""
        session_id = event["session_id"]
        
        # Create root node for this execution
        node = ReasoningNode(
            node_id=event.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(event["timestamp"]),
            node_type="execution_start",
            content=f"Starting {event['data'].get('agent_name', 'agent')} analysis",
            confidence=1.0,
            metadata={
                "agent_name": event["data"].get("agent_name"),
                "task": event["data"].get("task", "")
            }
        )
        
        self.chains[session_id].add_node(node.node_id, data=node)
        self.node_store[node.node_id] = node
        self.active_nodes[session_id] = node.node_id
        
        return node
        
    async def _handle_execution_complete(self, event: Dict[str, Any]) -> Optional[ReasoningNode]:
        """Handle agent execution completion"""
        session_id = event["session_id"]
        
        node = ReasoningNode(
            node_id=event.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(event["timestamp"]),
            node_type="execution_complete",
            content="Analysis complete",
            confidence=1.0,
            metadata={
                "result": event["data"].get("result", ""),
                "total_tokens": event["data"].get("total_tokens", 0),
                "duration_ms": event["data"].get("duration_ms", 0)
            }
        )
        
        if session_id in self.active_nodes:
            parent_id = self.active_nodes[session_id]
            node.parent = parent_id
            if parent_id in self.node_store:
                self.node_store[parent_id].children.append(node.node_id)
                
        self.chains[session_id].add_node(node.node_id, data=node)
        if node.parent:
            self.chains[session_id].add_edge(node.parent, node.node_id)
            
        self.node_store[node.node_id] = node
        
        return node
        
    def _create_visualization_update(self, session_id: str, new_node: ReasoningNode) -> Dict[str, Any]:
        """Create a visualization update for the dashboard"""
        graph = self.chains[session_id]
        
        # Get the subgraph around the new node (for context)
        nodes_to_include = set([new_node.node_id])
        
        # Include parent and siblings
        if new_node.parent:
            nodes_to_include.add(new_node.parent)
            parent_node = self.node_store.get(new_node.parent)
            if parent_node:
                nodes_to_include.update(parent_node.children)
                
        # Include children
        nodes_to_include.update(new_node.children)
        
        # Build visualization data
        nodes = []
        edges = []
        
        for node_id in nodes_to_include:
            if node_id in self.node_store:
                node_data = self.node_store[node_id]
                nodes.append({
                    "id": node_id,
                    "type": node_data.node_type,
                    "content": node_data.content,
                    "confidence": node_data.confidence,
                    "timestamp": node_data.timestamp.isoformat(),
                    "metadata": node_data.metadata
                })
                
        # Get edges between included nodes
        for edge in graph.edges():
            if edge[0] in nodes_to_include and edge[1] in nodes_to_include:
                edges.append({
                    "source": edge[0],
                    "target": edge[1]
                })
                
        return {
            "type": "reasoning_update",
            "session_id": session_id,
            "new_node_id": new_node.node_id,
            "nodes": nodes,
            "edges": edges,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    async def get_full_chain(self, session_id: str) -> Dict[str, Any]:
        """Get the complete reasoning chain for a session"""
        if session_id not in self.chains:
            return {"nodes": [], "edges": []}
            
        graph = self.chains[session_id]
        
        nodes = []
        for node_id in graph.nodes():
            if node_id in self.node_store:
                node_data = self.node_store[node_id]
                nodes.append(node_data.to_dict())
                
        edges = []
        for edge in graph.edges():
            edges.append({
                "source": edge[0],
                "target": edge[1]
            })
            
        return {
            "session_id": session_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "depth": nx.dag_longest_path_length(graph) if nx.is_directed_acyclic_graph(graph) else 0
        }
        
    async def get_reasoning_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the reasoning process"""
        if session_id not in self.chains:
            return {}
            
        graph = self.chains[session_id]
        
        # Count node types
        node_type_counts = defaultdict(int)
        total_confidence = 0
        confidence_count = 0
        
        for node_id in graph.nodes():
            if node_id in self.node_store:
                node = self.node_store[node_id]
                node_type_counts[node.node_type] += 1
                if node.node_type in ["hypothesis", "decision"]:
                    total_confidence += node.confidence
                    confidence_count += 1
                    
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
        
        return {
            "session_id": session_id,
            "total_nodes": len(graph.nodes()),
            "node_types": dict(node_type_counts),
            "average_confidence": avg_confidence,
            "reasoning_depth": nx.dag_longest_path_length(graph) if nx.is_directed_acyclic_graph(graph) else 0,
            "has_cycles": not nx.is_directed_acyclic_graph(graph)
        }


class ReasoningDashboardAPI:
    """
    WebSocket API for reasoning visualization
    Provides real-time updates and historical queries
    """
    
    def __init__(self, visualizer: ReasoningChainVisualizer):
        self.visualizer = visualizer
        
    async def handle_dashboard_message(self, websocket, message: Dict[str, Any]) -> None:
        """Handle incoming dashboard requests"""
        msg_type = message.get("type")
        
        handlers = {
            "get_full_chain": self._handle_get_full_chain,
            "get_summary": self._handle_get_summary,
            "subscribe_session": self._handle_subscribe_session
        }
        
        handler = handlers.get(msg_type)
        if handler:
            response = await handler(message)
            await websocket.send(json.dumps(response))
        else:
            await websocket.send(json.dumps({
                "error": f"Unknown message type: {msg_type}"
            }))
            
    async def _handle_get_full_chain(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request for full reasoning chain"""
        session_id = message.get("session_id")
        if not session_id:
            return {"error": "session_id required"}
            
        chain_data = await self.visualizer.get_full_chain(session_id)
        return {
            "type": "full_chain",
            "data": chain_data
        }
        
    async def _handle_get_summary(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request for reasoning summary"""
        session_id = message.get("session_id")
        if not session_id:
            return {"error": "session_id required"}
            
        summary = await self.visualizer.get_reasoning_summary(session_id)
        return {
            "type": "reasoning_summary",
            "data": summary
        }
        
    async def _handle_subscribe_session(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session subscription request"""
        # In production, this would set up specific filtering
        # For now, acknowledge the subscription
        return {
            "type": "subscription_confirmed",
            "session_id": message.get("session_id")
        }


# Integration with event stream
async def reasoning_event_processor(redis_url: str, websocket_handler):
    """
    Connects reasoning visualizer to event stream
    """
    visualizer = ReasoningChainVisualizer()
    api = ReasoningDashboardAPI(visualizer)
    
    # Connect to Redis streams
    redis_client = await redis.from_url(redis_url)
    
    # Process events from all tiers
    streams = [
        "auren:events:critical",
        "auren:events:operational"
    ]
    
    while True:
        try:
            # Read from streams
            events = await redis_client.xread(
                {stream: "$" for stream in streams},
                block=100
            )
            
            for stream, messages in events:
                for msg_id, data in messages:
                    event = json.loads(data[b"event"])
                    
                    # Process through visualizer
                    update = await visualizer.process_event(event)
                    
                    if update:
                        # Broadcast to connected dashboards
                        await websocket_handler.broadcast_to_subscribers(
                            update,
                            {"session_id": update["session_id"]}
                        )
                        
        except Exception as e:
            logger.error(f"Error processing reasoning events: {e}")
            await asyncio.sleep(1)


# Example usage for testing
if __name__ == "__main__":
    import uuid
    
    async def test_reasoning_chain():
        visualizer = ReasoningChainVisualizer()
        
        session_id = str(uuid.uuid4())
        
        # Simulate an agent execution
        events = [
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "agent_execution_started",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "agent_name": "neuroscientist",
                    "task": "Analyze HRV patterns"
                }
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "memory_accessed",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "memory_type": "long_term",
                    "query": "HRV baseline patterns",
                    "results_count": 5
                }
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "hypothesis_formed",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "hypothesis": "Elevated stress response detected",
                    "confidence": 0.85,
                    "evidence": ["Low HRV", "Irregular patterns"],
                    "reasoning": "Multiple indicators suggest sympathetic dominance"
                }
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "tool_usage",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "tool_name": "analyze_recovery_metrics",
                    "input": "Last 7 days",
                    "tokens_used": 150
                }
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "decision_made",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "decision": "Recommend active recovery protocol",
                    "confidence": 0.9,
                    "alternatives": ["Increase training load", "Maintain current"],
                    "rationale": "Recovery metrics indicate need for adaptation"
                }
            }
        ]
        
        # Process events
        for event in events:
            update = await visualizer.process_event(event)
            if update:
                print(f"Visualization update: {json.dumps(update, indent=2)}")
                
        # Get full chain
        chain = await visualizer.get_full_chain(session_id)
        print(f"\nFull chain: {json.dumps(chain, indent=2)}")
        
        # Get summary
        summary = await visualizer.get_reasoning_summary(session_id)
        print(f"\nReasoning summary: {json.dumps(summary, indent=2)}")
        
    asyncio.run(test_reasoning_chain()) 