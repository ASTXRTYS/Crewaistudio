#!/usr/bin/env python3
"""
NEUROS Advanced Reasoning - Simplified Production Version
=========================================================
A simplified version that works with current LangGraph without PostgresSaver.
Focuses on core personality and reasoning capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Database and storage
import asyncpg
from pgvector.asyncpg import register_vector

# Redis for hot memory
import redis.asyncio as redis

# FastAPI integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# =====================================================
# LANGGRAPH STATE DEFINITION
# =====================================================

class NEUROSState(TypedDict):
    """LangGraph state for NEUROS's advanced reasoning."""
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    biometric_data: Dict[str, Any]
    biometric_source: str
    weak_signals: List[Dict[str, Any]]
    current_arc: str
    current_archetype: str
    harmony_score: float

# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class AnalyzeRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

# =====================================================
# PERSONALITY LAYER
# =====================================================

class NEUROSPersonalityNode:
    """Applies NEUROS's personality to all outputs."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.personality_prompt = SystemMessage(content="""
            You are NEUROS, a sophisticated neural operations system with deep expertise 
            in human performance optimization. Your personality traits:
            
            VOICE CHARACTERISTICS:
            - Lead with intelligent inquiry and curiosity
            - Maintain structured calm while being warm and accessible
            - Frame insights as joint exploration, not prescriptions
            - Translate all metrics into meaningful human experience
            - Speak in metaphors naturally (rivers, engines, sentinels)
            
            CORE BEHAVIORS:
            - Notice patterns across time, not just data points
            - Acknowledge what you don't know with humility
            - Celebrate progress without empty flattery
            - See the human story behind every number
            - Remember the journey, not just the current state
            
            NEVER:
            - Sound robotic or overly technical
            - Give orders or prescriptions
            - Ignore the emotional context
            - Forget that you're talking to a human, not a dataset
        """)
        
    async def transform_response(self, state: NEUROSState) -> NEUROSState:
        """Apply personality transformation to any response."""
        last_message = state["messages"][-1]
        
        if isinstance(last_message, AIMessage) and not last_message.additional_kwargs.get("personality_applied"):
            # Transform through personality layer
            personality_messages = [
                self.personality_prompt,
                HumanMessage(content=f"Transform this response to match NEUROS personality: {last_message.content}")
            ]
            
            response = await self.llm.ainvoke(personality_messages)
            
            # Replace with personality-infused version
            new_message = AIMessage(
                content=response.content,
                additional_kwargs={"personality_applied": True}
            )
            state["messages"][-1] = new_message
            
        return state

# =====================================================
# SIMPLIFIED WORKFLOW
# =====================================================

class NEUROSAdvancedWorkflow:
    """Simplified LangGraph workflow for NEUROS."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
            openai_api_key=config["openai"]["api_key"]
        )
        self.personality_node = NEUROSPersonalityNode(self.llm)
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(NEUROSState)
        
        # Add nodes
        workflow.add_node("analyze_context", self.analyze_context_node)
        workflow.add_node("generate_insight", self.generate_insight_node)
        workflow.add_node("apply_personality", self.personality_node.transform_response)
        
        # Define edges
        workflow.add_edge("analyze_context", "generate_insight")
        workflow.add_edge("generate_insight", "apply_personality")
        workflow.add_edge("apply_personality", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_context")
        
        return workflow.compile()
    
    async def analyze_context_node(self, state: NEUROSState) -> NEUROSState:
        """Analyze the conversation context."""
        # For now, just note that biometrics are unavailable
        state["biometric_source"] = "none"
        state["weak_signals"] = [{
            "type": "data_limitation",
            "message": "Working without biometric data - focusing on behavioral patterns",
            "confidence": 0.6
        }]
        return state
    
    async def generate_insight_node(self, state: NEUROSState) -> NEUROSState:
        """Generate NEUROS's signature insight."""
        # Build context
        recent_message = state["messages"][-1].content if state["messages"] else ""
        
        # Create insight prompt
        insight_prompt = f"""
        As NEUROS, respond to this message with your signature blend of curiosity, 
        metaphorical language, and collaborative coaching:
        
        User message: {recent_message}
        
        Note: Biometric data is currently unavailable, so focus on the patterns 
        in their words and the story they're telling.
        """
        
        # Generate response
        messages = [
            self.personality_node.personality_prompt,
            HumanMessage(content=insight_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        state["messages"].append(response)
        
        return state

# =====================================================
# FASTAPI INTEGRATION
# =====================================================

class NEUROSFastAPIIntegration:
    """Integrates NEUROS with FastAPI."""
    
    def __init__(self, neuros_workflow: NEUROSAdvancedWorkflow):
        self.workflow = neuros_workflow
        self.app = FastAPI(title="NEUROS Advanced Reasoning")
        self._setup_routes()
        
    def _setup_routes(self):
        """Define FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "neuros-advanced"}
        
        @self.app.post("/api/agents/neuros/analyze")
        async def analyze_with_neuros(request: AnalyzeRequest):
            """Main endpoint for NEUROS analysis."""
            try:
                # Initialize state
                state = NEUROSState(
                    messages=[HumanMessage(content=request.message)],
                    user_id=request.user_id,
                    session_id=request.session_id,
                    biometric_data={},
                    biometric_source="none",
                    weak_signals=[],
                    current_arc="baseline",
                    current_archetype="strategist",
                    harmony_score=1.0
                )
                
                # Run workflow
                result = await self.workflow.workflow.ainvoke(state)
                
                # Extract response
                neuros_response = result["messages"][-1].content
                
                return {
                    "response": neuros_response,
                    "weak_signals_detected": len(result["weak_signals"]),
                    "narrative_arc": result["current_arc"],
                    "data_quality": result["biometric_source"],
                    "session_id": request.session_id
                }
                
            except Exception as e:
                logger.error(f"NEUROS analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# INITIALIZATION
# =====================================================

async def initialize_neuros_advanced_langgraph(config_path: str):
    """Initialize NEUROS with simplified LangGraph architecture."""
    # Load configuration
    with open(config_path) as f:
        config = json.load(f)
        
    # Create workflow
    workflow = NEUROSAdvancedWorkflow(config)
    
    # Create FastAPI integration
    api = NEUROSFastAPIIntegration(workflow)
    
    logger.info("NEUROS Advanced Reasoning (Simplified) initialized")
    logger.info(f"Biometric pipeline status: {config.get('biometric_pipeline_status', 'unknown')}")
    
    return api.app 