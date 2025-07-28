"""
NEUROS Cognitive Graph for Biometric-Driven AI
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, SystemMessage

from ..biometric.types import NEUROSState, CognitiveMode


def reflex_agent(state: NEUROSState) -> NEUROSState:
    """
    Reflex mode: High-stress immediate response
    - Quick decisions
    - Pattern matching
    - Stress reduction focus
    """
    messages = state.get("messages", [])
    messages.append(
        SystemMessage(content="[REFLEX MODE] Responding with immediate stress-reduction focus.")
    )
    
    # In reflex mode, prioritize quick, calming responses
    state["messages"] = messages
    return state


def pattern_agent(state: NEUROSState) -> NEUROSState:
    """
    Pattern mode: Normal operation
    - Analyze patterns
    - Learn from history
    - Standard processing
    """
    messages = state.get("messages", [])
    messages.append(
        SystemMessage(content="[PATTERN MODE] Analyzing patterns and historical data.")
    )
    
    # Standard cognitive processing
    state["messages"] = messages
    return state


def hypothesis_agent(state: NEUROSState) -> NEUROSState:
    """
    Hypothesis mode: Exploration and testing
    - Investigate anomalies
    - Form hypotheses
    - Test theories
    """
    messages = state.get("messages", [])
    messages.append(
        SystemMessage(content="[HYPOTHESIS MODE] Exploring anomaly and forming hypotheses.")
    )
    
    # Explore unusual patterns
    state["messages"] = messages
    state["active_hypothesis"] = "Investigating biometric anomaly"
    return state


def guardian_agent(state: NEUROSState) -> NEUROSState:
    """
    Guardian mode: Low energy protection
    - Conserve resources
    - Protective responses
    - Recovery focus
    """
    messages = state.get("messages", [])
    messages.append(
        SystemMessage(content="[GUARDIAN MODE] Conserving energy and focusing on recovery.")
    )
    
    # Protective, low-energy responses
    state["messages"] = messages
    return state


def mode_router(state: NEUROSState) -> Literal["reflex", "pattern", "hypothesis", "guardian", "end"]:
    """
    Route to appropriate cognitive mode based on state
    """
    current_mode = state.get("current_mode", CognitiveMode.PATTERN)
    
    # Check if we should end the conversation
    if state.get("processing_lock", False):
        return "end"
    
    # Route based on current cognitive mode
    if current_mode == CognitiveMode.REFLEX:
        return "reflex"
    elif current_mode == CognitiveMode.HYPOTHESIS:
        return "hypothesis"
    elif current_mode == CognitiveMode.GUARDIAN:
        return "guardian"
    else:
        return "pattern"


def create_neuros_graph():
    """
    Create the NEUROS cognitive graph with mode-based routing
    """
    # Initialize the state graph
    workflow = StateGraph(NEUROSState)
    
    # Add nodes for each cognitive mode
    workflow.add_node("reflex", reflex_agent)
    workflow.add_node("pattern", pattern_agent)
    workflow.add_node("hypothesis", hypothesis_agent)
    workflow.add_node("guardian", guardian_agent)
    
    # Set entry point with routing
    workflow.set_entry_point("pattern")
    
    # Add conditional edges based on cognitive mode
    workflow.add_conditional_edges(
        "pattern",
        mode_router,
        {
            "reflex": "reflex",
            "guardian": "guardian",
            "hypothesis": "hypothesis",
            "pattern": "pattern",
            "end": END
        }
    )
    
    # Add edges from other modes back to router
    workflow.add_conditional_edges(
        "reflex",
        mode_router,
        {
            "pattern": "pattern",
            "guardian": "guardian",
            "hypothesis": "hypothesis",
            "reflex": "reflex",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "hypothesis",
        mode_router,
        {
            "pattern": "pattern",
            "reflex": "reflex",
            "guardian": "guardian",
            "hypothesis": "hypothesis",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "guardian",
        mode_router,
        {
            "pattern": "pattern",
            "reflex": "reflex",
            "hypothesis": "hypothesis",
            "guardian": "guardian",
            "end": END
        }
    )
    
    # Compile the graph
    return workflow.compile()


# Example usage with PostgreSQL checkpointing
def create_neuros_graph_with_checkpointing(postgres_pool):
    """
    Create NEUROS graph with PostgreSQL checkpoint support
    """
    checkpointer = PostgresSaver(postgres_pool)
    graph = create_neuros_graph()
    # Note: In newer LangGraph versions, checkpointing is configured differently
    # This is a placeholder for the actual implementation
    return graph 