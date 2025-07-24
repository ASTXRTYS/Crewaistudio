"""
CrewAI Integration for AUREN Intelligence System
Provides seamless integration between CrewAI agents and the intelligence system
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone

from crewai import Agent, Task, Crew
from crewai_tools import BaseTool

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
        
        class KnowledgeTool(BaseTool):
            name: str = "knowledge_manager"
            description: str = "Manage and retrieve knowledge for intelligent decision making"
            
            def __init__(self, adapter, agent_id, domain, user_id):
                super().__init__()
                self.adapter = adapter
                self.agent_id = agent_id
                self.domain = domain
                self.user_id = user_id
            
            def _run(self, action: str, **kwargs) -> str:
                """Run knowledge management action"""
                return asyncio.run(self._async_run(action, **kwargs))
            
            async def _async_run(self, action: str, **kwargs) -> str:
                """Async implementation"""
                try:
                    if action == "store":
                        return await self._store_knowledge(**kwargs)
                    elif action == "retrieve":
                        return await self._retrieve_knowledge(**kwargs)
                    elif action == "search":
                        return await self._search_knowledge(**kwargs)
                    elif action == "update":
                        return await self._update_knowledge(**kwargs)
                    else:
                        return f"Unknown action: {action}"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            async def _store_knowledge(self, **kwargs) -> str:
                """Store knowledge item"""
                knowledge = KnowledgeItem(
                    knowledge_id=create_knowledge_id(),
                    agent_id=self.agent_id,
                    user_id=self.user_id,
                    domain=self.domain,
                    knowledge_type=kwargs.get('knowledge_type', 'pattern'),
                    title=kwargs.get('title', 'Untitled Knowledge'),
                    description=kwargs.get('description', ''),
                    content=kwargs.get('content', {}),
                    confidence=kwargs.get('confidence', 0.5),
                    evidence_sources=kwargs.get('evidence_sources', []),
                    validation_status=kwargs.get('validation_status', 'provisional'),
                    metadata=kwargs.get('metadata', {})
                )
                
                knowledge_id = await self.adapter.memory_backend.store_knowledge(
                    knowledge.__dict__
                )
                
                # Log event
                await self.adapter.event_store.append_event(
                    stream_id=self.user_id,
                    stream_type=EventStreamType.KNOWLEDGE,
                    event_type="knowledge_stored",
                    event_data={
                        'knowledge_id': knowledge_id,
                        'agent_id': self.agent_id,
                        'domain': self.domain,
                        'title': knowledge.title
                    }
                )
                
                return f"Knowledge stored: {knowledge_id}"
            
            async def _retrieve_knowledge(self, **kwargs) -> str:
                """Retrieve knowledge items"""
                knowledge_list = await self.adapter.memory_backend.get_knowledge(
                    user_id=self.user_id,
                    domain=self.domain,
                    limit=kwargs.get('limit', 10)
                )
                
                return json.dumps(knowledge_list, default=str)
            
            async def _search_knowledge(self, **kwargs) -> str:
                """Search knowledge items"""
                results = await self.adapter.memory_backend.search_knowledge(
                    user_id=self.user_id,
                    query=kwargs.get('query', ''),
                    limit=kwargs.get('limit', 10)
                )
                
                return json.dumps(results, default=str)
            
            async def _update_knowledge(self, **kwargs) -> str:
                """Update knowledge item"""
                success = await self.adapter.memory_backend.update_knowledge(
                    knowledge_id=kwargs.get('knowledge_id'),
                    user_id=self.user_id,
                    updates=kwargs.get('updates', {})
                )
                
                return "Updated successfully" if success else "Update failed"
        
        return KnowledgeTool(self, agent_id, domain, user_id)
    
    def _create_hypothesis_tool(self, agent_id: str, domain: str, user_id: str) -> BaseTool:
        """Create hypothesis management tool"""
        
        class HypothesisTool(BaseTool):
            name: str = "hypothesis_manager"
            description: str = "Form and validate hypotheses about user patterns"
            
            def __init__(self, adapter, agent_id, domain, user_id):
                super().__init__()
                self.adapter = adapter
                self.agent_id = agent_id
                self.domain = domain
                self.user_id = user_id
            
            def _run(self, action: str, **kwargs) -> str:
                """Run hypothesis management action"""
                return asyncio.run(self._async_run(action, **kwargs))
            
            async def _async_run(self, action: str, **kwargs) -> str:
                """Async implementation"""
                try:
                    if action == "form":
                        return await self._form_hypothesis(**kwargs)
                    elif action == "validate":
                        return await self._validate_hypothesis(**kwargs)
                    elif action == "list":
                        return await self._list_hypotheses(**kwargs)
                    else:
                        return f"Unknown action: {action}"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            async def _form_hypothesis(self, **kwargs) -> str:
                """Form new hypothesis"""
                hypothesis = Hypothesis(
                    hypothesis_id=create_hypothesis_id(),
                    agent_id=self.agent_id,
                    user_id=self.user_id,
                    domain=self.domain,
                    description=kwargs.get('description', ''),
                    prediction=kwargs.get('prediction', {}),
                    confidence=kwargs.get('confidence', 0.5),
                    evidence_criteria=kwargs.get('evidence_criteria', []),
                    formed_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                    status=HypothesisStatus.FORMED,
                    metadata=kwargs.get('metadata', {})
                )
                
                # Store hypothesis (would need hypothesis storage method)
                # For now, log as event
                await self.adapter.event_store.append_event(
                    stream_id=self.user_id,
                    stream_type=EventStreamType.HYPOTHESIS,
                    event_type="hypothesis_formed",
                    event_data={
                        'hypothesis_id': hypothesis.hypothesis_id,
                        'agent_id': self.agent_id,
                        'domain': self.domain,
                        'description': hypothesis.description,
                        'confidence': hypothesis.confidence
                    }
                )
                
                return f"Hypothesis formed: {hypothesis.hypothesis_id}"
            
            async def _validate_hypothesis(self, **kwargs) -> str:
                """Validate hypothesis with evidence"""
                # This would integrate with hypothesis validator
                # For now, log validation event
                await self.adapter.event_store.append_event(
                    stream_id=self.user_id,
                    stream_type=EventStreamType.VALIDATION,
                    event_type="hypothesis_validated",
                    event_data={
                        'hypothesis_id': kwargs.get('hypothesis_id'),
                        'evidence': kwargs.get('evidence', {}),
                        'result': kwargs.get('result', 'pending')
                    }
                )
                
                return "Hypothesis validation logged"
            
            async def _list_hypotheses(self, **kwargs) -> str:
                """List active hypotheses"""
                # This would retrieve from storage
                # For now, return placeholder
                return json.dumps([
                    {
                        'hypothesis_id': 'hyp_001',
                        'description': 'User HRV improves with consistent sleep',
                        'confidence': 0.75,
                        'status': 'active'
                    }
                ])
        
        return HypothesisTool(self, agent_id, domain, user_id)
    
    def _create_event_tool(self, agent_id: str, domain: str, user_id: str) -> BaseTool:
        """Create event logging tool"""
        
        class EventTool(BaseTool):
            name: str = "event_logger"
            description: str = "Log events for audit trails and analytics"
            
            def __init__(self, adapter, agent_id, domain, user_id):
                super().__init__()
                self.adapter = adapter
                self.agent_id = agent_id
                self.domain = domain
                self.user_id = user_id
            
            def _run(self, event_type: str, event_data: Dict[str, Any], **kwargs) -> str:
                """Log event"""
                return asyncio.run(self._async_run(event_type, event_data, **kwargs))
            
            async def _async_run(self, event_type: str, event_data: Dict[str, Any], **kwargs) -> str:
                """Async implementation"""
                try:
                    await self.adapter.event_store.append_event(
                        stream_id=self.user_id,
                        stream_type=EventStreamType.SYSTEM,
                        event_type=event_type,
                        event_data={
                            **event_data,
                            'agent_id': self.agent_id,
                            'domain': self.domain
                        },
                        metadata=kwargs.get('metadata', {})
                    )
                    
                    return f"Event logged: {event_type}"
                except Exception as e:
                    return f"Error logging event: {str(e)}"
        
        return EventTool(self, agent_id, domain, user_id)
    
    async def _store_agent_metadata(self, agent_id: str, metadata: Dict[str, Any]):
        """Store agent metadata"""
        await self.event_store.append_event(
            stream_id=agent_id,
            stream_type=EventStreamType.SYSTEM,
            event_type="agent_created",
            event_data=metadata
        )
    
    async def create_intelligent_crew(self,
                                   crew_name: str,
                                   agents: List[Agent],
                                   tasks: List[Task],
                                   user_id: str) -> Crew:
        """
        Create intelligent crew with AUREN integration
        
        Args:
            crew_name: Crew name
            agents: List of agents
            tasks: List of tasks
            user_id: User ID
            
        Returns:
            Configured Crew
        """
        
        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=True,
            process="sequential"
        )
        
        # Log crew creation
        await self.event_store.append_event(
            stream_id=user_id,
            stream_type=EventStreamType.COLLABORATION,
            event_type="crew_created",
            event_data={
                'crew_name': crew_name,
                'agent_count': len(agents),
                'task_count': len(tasks),
                'agents': [agent.role for agent in agents]
            }
        )
        
        return crew
    
    async def run_intelligent_crew(self,
                                crew: Crew,
                                user_id: str,
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run intelligent crew with AUREN integration
        
        Args:
            crew: Crew to run
            user_id: User ID
            context: Optional context
            
        Returns:
            Crew execution results
        """
        
        # Log crew execution start
        await self.event_store.append_event(
            stream_id=user_id,
            stream_type=EventStreamType.COLLABORATION,
            event_type="crew_execution_started",
            event_data={
                'crew_name': getattr(crew, 'name', 'unnamed'),
                'context': context or {},
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        try:
            # Run crew
            result = crew.kickoff()
            
            # Log crew execution completion
            await self.event_store.append_event(
                stream_id=user_id,
                stream_type=EventStreamType.COLLABORATION,
                event_type="crew_execution_completed",
                event_data={
                    'crew_name': getattr(crew, 'name', 'unnamed'),
                    'result_summary': str(result)[:500],  # Truncate for storage
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return {
                'success': True,
                'result': result,
                'events_logged': True
            }
            
        except Exception as e:
            # Log crew execution error
            await self.event_store.append_event(
                stream_id=user_id,
                stream_type=EventStreamType.COLLABORATION,
                event_type="crew_execution_error",
                event_data={
                    'crew_name': getattr(crew, 'name', 'unnamed'),
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return {
                'success': False,
                'error': str(e),
                'events_logged': True
            }
    
    async def get_agent_performance(self,
                                 agent_id: str,
                                 user_id: str,
                                 days: int = 7) -> Dict[str, Any]:
        """
        Get agent performance metrics
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            days: Days back
            
        Returns:
            Performance metrics
        """
        
        # Get events for agent
        events = await self.event_store.get_events_by_user(
            user_id=user_id,
            stream_type=EventStreamType.SYSTEM,
            limit=1000
        )
        
        # Filter agent events
        agent_events = [
            event for event in events
            if event.get('event_data', {}).get('agent_id') == agent_id
        ]
        
        # Calculate metrics
        knowledge_created = len([
            e for e in agent_events
            if e.get('event_type') == 'knowledge_stored'
        ])
        
        hypotheses_formed = len([
            e for e in agent_events
            if e.get('event_type') == 'hypothesis_formed'
        ])
        
        return {
            'agent_id': agent_id,
            'total_events': len(agent_events),
            'knowledge_created': knowledge_created,
            'hypotheses_formed': hypotheses_formed,
            'period_days': days
        }
    
    async def cleanup(self):
        """Clean up resources"""
        if self.memory_backend:
            await self.memory_backend.cleanup()
        if self.event_store:
            await self.event_store.cleanup()


# Utility functions
async def create_intelligence_adapter() -> CrewAIIntelligenceAdapter:
    """
    Create and initialize intelligence adapter
    
    Returns:
        Initialized intelligence adapter
    """
    adapter = CrewAIIntelligenceAdapter()
    await adapter.initialize()
    return adapter


async def test_crewai_integration():
    """
    Test CrewAI integration
    """
    adapter = await create_intelligence_adapter()
    
    try:
        # Create test agent
        from crewai_tools import SerperDevTool
        
        search_tool = SerperDevTool()
        
        agent = adapter.create_intelligent_agent(
            agent_id="test_neuroscientist",
            role="Neuroscientist",
            goal="Optimize user CNS performance through data analysis",
            backstory="Expert in neuroscience with focus on HRV and recovery optimization",
            domain="neuroscience",
            user_id="test_user",
            tools=[search_tool]
        )
        
        print(f"Created agent: {agent.role}")
        
        # Test knowledge tool
        knowledge_tool = agent.tools[0]
        result = knowledge_tool._run("store", title="Test Knowledge", content={"test": "data"})
        print(f"Knowledge tool result: {result}")
        
        # Test hypothesis tool
        hypothesis_tool = agent.tools[1]
        result = hypothesis_tool._run("form", description="Test hypothesis", prediction={"test": True})
        print(f"Hypothesis tool result: {result}")
        
        # Test event tool
        event_tool = agent.tools[2]
        result = event_tool._run("test_event", {"message": "Integration test"})
        print(f"Event tool result: {result}")
        
    finally:
        await adapter.cleanup()


if __name__ == "__main__":
    asyncio.run(test_crewai_integration())
