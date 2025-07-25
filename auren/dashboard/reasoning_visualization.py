"""
auren/dashboard/reasoning_visualization.py
Real-time reasoning chain visualization - Chess engine transparency for AI coaching
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import redis.asyncio as redis
from collections import defaultdict, deque
import networkx as nx


@dataclass
class ReasoningNode:
    """Represents a single node in the reasoning chain"""
    node_id: str
    timestamp: datetime
    node_type: str  # "hypothesis", "tool_call", "memory_access", "decision"
    content: str
    confidence: float
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}


class ReasoningChainVisualizer:
    """
    Visualizes AI reasoning chains in real-time
    Shows how the AI thinks through problems step by step
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.reasoning_chains = defaultdict(list)  # session_id -> List[ReasoningNode]
        self.active_chains = {}  # session_id -> root_node_id
        
    async def connect(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(self.redis_url)
        
    async def process_event_stream(self):
        """Process events and build reasoning chains"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("auren:events:critical", "auren:events:operational")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    await self._process_event(event)
                except Exception as e:
                    st.error(f"Error processing event: {e}")
    
    async def _process_event(self, event: Dict[str, Any]):
        """Convert events into reasoning chain nodes"""
        event_type = event.get('event_type')
        session_id = event.get('session_id')
        
        if not session_id:
            return
            
        node = None
        
        # Map different event types to reasoning nodes
        if event_type == "hypothesis_formed":
            node = ReasoningNode(
                node_id=event.get('event_id'),
                timestamp=datetime.fromisoformat(event.get('timestamp')),
                node_type="hypothesis",
                content=event.get('data', {}).get('hypothesis', ''),
                confidence=event.get('data', {}).get('confidence', 0.5),
                metadata={
                    'supporting_evidence': event.get('data', {}).get('evidence', []),
                    'biometric_context': event.get('biometric_context', {})
                }
            )
            
        elif event_type == "tool_usage":
            node = ReasoningNode(
                node_id=event.get('event_id'),
                timestamp=datetime.fromisoformat(event.get('timestamp')),
                node_type="tool_call",
                content=f"{event.get('data', {}).get('tool_name', 'Unknown Tool')}: {event.get('data', {}).get('input', '')}",
                confidence=1.0,
                metadata={
                    'tool_name': event.get('data', {}).get('tool_name'),
                    'execution_time': event.get('data', {}).get('execution_time_ms', 0),
                    'result_summary': event.get('data', {}).get('result', '')[:200]
                }
            )
            
        elif event_type == "memory_accessed":
            node = ReasoningNode(
                node_id=event.get('event_id'),
                timestamp=datetime.fromisoformat(event.get('timestamp')),
                node_type="memory_access",
                content=f"Retrieved: {event.get('data', {}).get('memory_key', 'Unknown')}",
                confidence=event.get('data', {}).get('relevance_score', 0.7),
                metadata={
                    'memory_type': event.get('data', {}).get('memory_type'),
                    'relevance_score': event.get('data', {}).get('relevance_score')
                }
            )
            
        elif event_type == "agent_execution_completed":
            node = ReasoningNode(
                node_id=event.get('event_id'),
                timestamp=datetime.fromisoformat(event.get('timestamp')),
                node_type="decision",
                content=event.get('data', {}).get('result', 'Analysis completed'),
                confidence=event.get('data', {}).get('confidence', 0.8),
                metadata={
                    'execution_time': event.get('performance_metrics', {}).get('execution_time_ms'),
                    'tokens_used': event.get('performance_metrics', {}).get('total_tokens')
                }
            )
        
        if node:
            # Add to chain
            self.reasoning_chains[session_id].append(node)
            
            # Link nodes based on timing and context
            await self._link_nodes(session_id, node)
    
    async def _link_nodes(self, session_id: str, new_node: ReasoningNode):
        """Intelligently link nodes to form reasoning chains"""
        chain = self.reasoning_chains[session_id]
        
        if len(chain) > 1:
            # Find most likely parent based on timing and type
            potential_parents = [n for n in chain[:-1] 
                               if (new_node.timestamp - n.timestamp).total_seconds() < 30]
            
            if potential_parents:
                # Simple heuristic: most recent compatible node
                parent = max(potential_parents, key=lambda n: n.timestamp)
                new_node.parent_id = parent.node_id
                parent.children_ids.append(new_node.node_id)
    
    def create_reasoning_graph(self, session_id: str) -> go.Figure:
        """Create interactive reasoning chain visualization"""
        chain = self.reasoning_chains.get(session_id, [])
        
        if not chain:
            return go.Figure().add_annotation(
                text="No reasoning chain available yet",
                showarrow=False,
                font=dict(size=20)
            )
        
        # Build graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in chain:
            G.add_node(node.node_id, 
                      label=node.content[:50] + "..." if len(node.content) > 50 else node.content,
                      type=node.node_type,
                      confidence=node.confidence,
                      timestamp=node.timestamp.isoformat())
        
        # Add edges
        for node in chain:
            if node.parent_id:
                G.add_edge(node.parent_id, node.node_id)
        
        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines',
                line=dict(width=2, color='gray'),
                hoverinfo='none',
                showlegend=False
            ))
        
        # Add nodes
        for node_id, (x, y) in pos.items():
            node_data = G.nodes[node_id]
            node = next(n for n in chain if n.node_id == node_id)
            
            # Color based on node type
            colors = {
                'hypothesis': '#FF6B6B',
                'tool_call': '#4ECDC4',
                'memory_access': '#45B7D1',
                'decision': '#96CEB4'
            }
            
            # Size based on confidence
            size = 20 + (node.confidence * 30)
            
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers+text',
                marker=dict(
                    size=size,
                    color=colors.get(node.node_type, '#95A5A6'),
                    line=dict(width=2, color='white')
                ),
                text=node_data['label'],
                textposition="bottom center",
                hovertemplate=(
                    f"<b>{node.node_type.title()}</b><br>"
                    f"Content: {node.content}<br>"
                    f"Confidence: {node.confidence:.2f}<br>"
                    f"Time: {node.timestamp.strftime('%H:%M:%S')}<br>"
                    "<extra></extra>"
                ),
                showlegend=False
            ))
        
        fig.update_layout(
            title="AI Reasoning Chain Visualization",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            height=600
        )
        
        return fig
    
    def create_confidence_timeline(self, session_id: str) -> go.Figure:
        """Show confidence levels over the reasoning process"""
        chain = self.reasoning_chains.get(session_id, [])
        
        if not chain:
            return go.Figure()
        
        # Sort by timestamp
        sorted_chain = sorted(chain, key=lambda n: n.timestamp)
        
        # Create timeline
        fig = go.Figure()
        
        # Group by node type
        for node_type in ['hypothesis', 'tool_call', 'memory_access', 'decision']:
            nodes = [n for n in sorted_chain if n.node_type == node_type]
            
            if nodes:
                fig.add_trace(go.Scatter(
                    x=[n.timestamp for n in nodes],
                    y=[n.confidence for n in nodes],
                    mode='lines+markers',
                    name=node_type.replace('_', ' ').title(),
                    line=dict(width=2),
                    marker=dict(size=8)
                ))
        
        fig.update_layout(
            title="Reasoning Confidence Timeline",
            xaxis_title="Time",
            yaxis_title="Confidence",
            yaxis=dict(range=[0, 1]),
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_reasoning_stats(self, session_id: str) -> Dict[str, Any]:
        """Calculate statistics about the reasoning process"""
        chain = self.reasoning_chains.get(session_id, [])
        
        if not chain:
            return {}
        
        stats = {
            'total_steps': len(chain),
            'avg_confidence': sum(n.confidence for n in chain) / len(chain),
            'hypotheses_formed': len([n for n in chain if n.node_type == 'hypothesis']),
            'tools_used': len([n for n in chain if n.node_type == 'tool_call']),
            'memories_accessed': len([n for n in chain if n.node_type == 'memory_access']),
            'total_time': (max(n.timestamp for n in chain) - min(n.timestamp for n in chain)).total_seconds()
        }
        
        # Most used tools
        tool_calls = [n for n in chain if n.node_type == 'tool_call']
        if tool_calls:
            tool_counts = defaultdict(int)
            for node in tool_calls:
                tool_name = node.metadata.get('tool_name', 'Unknown')
                tool_counts[tool_name] += 1
            stats['most_used_tool'] = max(tool_counts, key=tool_counts.get)
        
        return stats


# Streamlit Dashboard
def create_reasoning_dashboard():
    """Main dashboard for reasoning visualization"""
    st.set_page_config(
        page_title="AUREN Reasoning Visualization",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 AUREN AI Reasoning Visualization")
    st.markdown("*See exactly how your AI performance coach thinks*")
    
    # Initialize visualizer
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = ReasoningChainVisualizer()
        asyncio.run(st.session_state.visualizer.connect())
    
    visualizer = st.session_state.visualizer
    
    # Session selector
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sessions = list(visualizer.reasoning_chains.keys())
        if sessions:
            selected_session = st.selectbox(
                "Select Session",
                sessions,
                format_func=lambda x: f"Session {x[:8]}..."
            )
        else:
            selected_session = None
            st.info("No active reasoning sessions yet. Start a conversation with AUREN to see reasoning chains.")
    
    with col2:
        if st.button("🔄 Refresh", help="Refresh reasoning data"):
            st.rerun()
    
    if selected_session:
        # Main visualization
        st.subheader("Reasoning Chain Graph")
        reasoning_graph = visualizer.create_reasoning_graph(selected_session)
        st.plotly_chart(reasoning_graph, use_container_width=True)
        
        # Confidence timeline
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Confidence Timeline")
            confidence_timeline = visualizer.create_confidence_timeline(selected_session)
            st.plotly_chart(confidence_timeline, use_container_width=True)
        
        with col2:
            st.subheader("Reasoning Statistics")
            stats = visualizer.create_reasoning_stats(selected_session)
            
            if stats:
                st.metric("Total Steps", stats.get('total_steps', 0))
                st.metric("Avg Confidence", f"{stats.get('avg_confidence', 0):.2%}")
                st.metric("Hypotheses", stats.get('hypotheses_formed', 0))
                st.metric("Tools Used", stats.get('tools_used', 0))
                st.metric("Memories", stats.get('memories_accessed', 0))
                st.metric("Total Time", f"{stats.get('total_time', 0):.1f}s")
                
                if 'most_used_tool' in stats:
                    st.info(f"Most used tool: {stats['most_used_tool']}")
        
        # Detailed reasoning steps
        with st.expander("Detailed Reasoning Steps", expanded=False):
            chain = visualizer.reasoning_chains[selected_session]
            
            for i, node in enumerate(sorted(chain, key=lambda n: n.timestamp)):
                node_color = {
                    'hypothesis': '🔴',
                    'tool_call': '🔧',
                    'memory_access': '💾',
                    'decision': '✅'
                }.get(node.node_type, '❓')
                
                st.markdown(f"""
                **{node_color} Step {i+1}: {node.node_type.replace('_', ' ').title()}**
                - **Content**: {node.content}
                - **Confidence**: {node.confidence:.2%}
                - **Time**: {node.timestamp.strftime('%H:%M:%S.%f')[:-3]}
                """)
                
                if node.metadata:
                    with st.expander(f"Metadata for step {i+1}"):
                        st.json(node.metadata)
    
    # Auto-refresh
    if st.checkbox("Auto-refresh (every 2 seconds)", value=True):
        st.empty()
        import time
        time.sleep(2)
        st.rerun()


if __name__ == "__main__":
    create_reasoning_dashboard() 