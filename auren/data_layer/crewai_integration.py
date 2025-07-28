"""
CrewAI Integration for AUREN Intelligence System
Provides seamless integration between CrewAI agents and the intelligence system
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END, Task, Crew
from langchain.tools import Tool

from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore, EventStreamType
from intelligence.data_structures import (
    KnowledgeItem, KnowledgeType, KnowledgeStatus,
    Hypothesis, HypothesisStatus, create_knowledge_id, create_hypothesis_id
)

logger = logging.getLogger(__name__)


class CrewAIIntelligenceAdapter:
    """
    Adapter for integrating CrewAI agents with AUREN intelligence system
    
    Features:
    - Automatic knowledge persistence
    - Hypothesis tracking
    - Event sourcing
    - Cross-agent knowledge sharing
    - Performance analytics
    """
    
    def __init__(self,
                 memory_backend: Optional[PostgreSQLMemoryBackend] = None,
                 event_store: Optional[EventStore] = None):
        """
        Initialize CrewAI intelligence adapter
        
        Args:
            memory_backend: Memory backend instance
            event_store: Event store instance
        """
        self.memory_backend = memory_backend
        self.event_store = event_store
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize the adapter
        
        Returns:
            True if initialization successful
        """
        try:
            if not self.memory_backend:
                from data_layer.memory_backend import create_memory_backend
                self.memory_backend = await create_memory_backend()
            
            if not self.event_store:
                from data_layer.event_store import create_event_store
                self.event_store = await create_event_store()
            
            self._initialized = True
            logger.info("✅ CrewAI intelligence adapter initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CrewAI adapter: {e}")
            return False
    
    def create_intelligent_agent(self,
                               agent_id: str,
                               role: str,
                               goal: str,
                               backstory: str,
                               domain: str,
                               user_id: str,
                               tools: List[BaseTool] = None,
                               verbose: bool = False) -> Agent:
        """
        Create an intelligent CrewAI agent with AUREN integration
        
        Args:
            agent_id: Unique agent identifier
            role: Agent role description
            goal: Agent goal
            backstory: Agent backstory
            domain: Knowledge domain
            user_id: User ID
            tools: List of tools
            verbose: Verbose mode
            
        Returns:
            Configured CrewAI agent
        """
        
        # Create knowledge tool
        knowledge_tool = self._create_knowledge_tool(agent_id, domain, user_id)
        
        # Create hypothesis tool
        hypothesis_tool = self._create_hypothesis_tool(agent_id, domain, user_id)
        
        # Create event tool
        event_tool = self._create_event_tool(agent_id, domain, user_id)
        
        # Combine tools
        all_tools = [knowledge_tool, hypothesis_tool, event_tool]
        if tools:
            all_tools.extend(tools)
        
        # Create agent
        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=all_tools,
            verbose=verbose,
            allow_delegation=True
        )
        
        # Store agent metadata
        asyncio.create_task(self._store_agent_metadata(agent_id, {
            'role': role,
            'goal': goal,
            'backstory': backstory,
            'domain': domain,
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }))
        
        return agent
    
    def _create_knowledge_tool(self, agent_id: str, domain: str, user_id: str) -> BaseTool:
        """Create knowledge management tool"""
        
        class KnowledgeToolInput(BaseModel):
    """Input for KnowledgeTool"""
    query: str = Field(description="Input query")

def knowledgetool_func(query: str) -> str:
    """KnowledgeTool tool"""
    pass

knowledgetool_tool = Tool(
    name="KnowledgeTool",
    func=knowledgetool_func,
    description="""KnowledgeTool tool""",
    args_schema=KnowledgeToolInput
)class HypothesisToolInput(BaseModel):
    """Input for HypothesisTool"""
    query: str = Field(description="Input query")

def hypothesistool_func(query: str) -> str:
    """HypothesisTool tool"""
    pass

hypothesistool_tool = Tool(
    name="HypothesisTool",
    func=hypothesistool_func,
    description="""HypothesisTool tool""",
    args_schema=HypothesisToolInput
)class EventToolInput(BaseModel):
    """Input for EventTool"""
    query: str = Field(description="Input query")

def eventtool_func(query: str) -> str:
    """Test hypothesis"""
    pass

eventtool_tool = Tool(
    name="EventTool",
    func=eventtool_func,
    description="""Test hypothesis""",
    args_schema=EventToolInput
)