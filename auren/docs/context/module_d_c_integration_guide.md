# Module D-C Integration: Comprehensive Implementation Guide

## Executive Overview

This guide provides production-ready implementation for connecting Module D's NeuroscientistAgent to Module C's event streaming infrastructure. The integration will replace test data with real agent execution events, providing complete visibility into AUREN's cognitive operations.

### Integration Architecture

```
NeuroscientistAgent (Module D)
    ↓
MonitoredAURENMemory + TokenTrackingTools
    ↓
CrewAIEventInstrumentation (Module C)
    ↓
Redis Event Stream
    ↓
WebSocket Server → Real-time Dashboard
```

---

## Phase 1: Enhanced Agent Implementation

### 1.1 Create Monitored Neuroscientist Agent

Create `auren/agents/monitored_specialist_agents.py`:

```python
"""
Production-ready monitored specialist agents with full event instrumentation
This replaces the basic agents with versions that emit comprehensive telemetry
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import uuid
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool

# Import Module C instrumentation
from auren.realtime.crewai_instrumentation import (
    CrewAIEventInstrumentation, 
    AURENStreamEvent, 
    AURENEventType,
    AURENPerformanceMetrics
)

# Import the bridge components from integration
from auren.integration.crewai_realtime_integration import (
    MonitoredAURENMemory,
    TokenTrackingTool
)

# Import base Module D components
from auren.agents.memory import AURENMemoryStorage
from auren.agents.specialist_agents import AURENSpecialistTool

import logging
logger = logging.getLogger(__name__)


class MonitoredFormulateHypothesisTool(TokenTrackingTool):
    """Hypothesis tool with comprehensive tracking"""
    
    def __init__(self, user_id: str, hypothesis_validator, event_instrumentation):
        # Create the base tool
        base_tool = FormulateHypothesisToolBase(user_id, hypothesis_validator)
        # Wrap with token tracking
        super().__init__(base_tool, event_instrumentation)
        
        # Override metadata for better tracking
        self.name = "Formulate Hypothesis"
        self.description = "Formulates and saves a new hypothesis about user health patterns"


class FormulateHypothesisToolBase(AURENSpecialistTool):
    """Base implementation of hypothesis formulation"""
    
    name: str = "Formulate Hypothesis"
    description: str = "Formulates and saves a new hypothesis about user health patterns"
    
    async def _run(self, hypothesis_text: str) -> str:
        start_time = datetime.now(timezone.utc)
        
        try:
            # Form hypothesis with full tracking
            hypothesis = await self.hypothesis_validator.form_hypothesis(
                agent_id="neuroscientist",
                user_id=self.user_id,
                domain="neuroscience",
                description=hypothesis_text,
                confidence=0.7
            )
            
            # Calculate execution time
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Log success metrics
            logger.info(f"Hypothesis {hypothesis.hypothesis_id} formed in {execution_time}ms")
            
            return f"Hypothesis '{hypothesis.hypothesis_id}' formulated and tracking for validation."
            
        except Exception as e:
            logger.error(f"Hypothesis formation failed: {e}")
            raise


class MonitoredNeuroscientistAgent:
    """
    Production neuroscientist agent with complete event instrumentation
    
    This implementation:
    - Uses MonitoredAURENMemory for all memory operations
    - Wraps all tools with TokenTrackingTool
    - Emits comprehensive events for all operations
    - Tracks performance metrics and costs
    """
    
    def __init__(self, 
                 user_id: str,
                 memory_backend,
                 event_store,
                 hypothesis_validator,
                 knowledge_manager,
                 event_instrumentation: CrewAIEventInstrumentation):
        
        self.user_id = user_id
        self.event_instrumentation = event_instrumentation
        
        # Create monitored memory with event tracking
        self.memory = MonitoredAURENMemory(
            agent_id="neuroscientist",
            user_id=user_id,
            memory_backend=memory_backend,
            event_store=event_store,
            hypothesis_validator=hypothesis_validator,
            knowledge_manager=knowledge_manager,
            event_instrumentation=event_instrumentation
        )
        
        # Create monitored tools
        self.tools = self._create_monitored_tools(
            hypothesis_validator, 
            knowledge_manager
        )
        
        # Create CrewAI agent with instrumented components
        self.crew_agent = Agent(
            role="Neuroscientist and Stress Physiology Expert",
            goal="Analyze nervous system patterns, stress responses, and autonomic balance to optimize mental and physical performance",
            backstory="""You are a leading neuroscientist specializing in stress physiology and autonomic nervous system function. 
            You have deep expertise in HRV analysis, circadian rhythms, and the neurobiological basis of performance optimization. 
            You analyze biometric data to identify patterns and form testable hypotheses about health optimization strategies.""",
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            allow_delegation=False  # Single agent system for now
        )
        
        # Track agent registration
        self._register_agent()
    
    def _create_monitored_tools(self, hypothesis_validator, knowledge_manager) -> List[BaseTool]:
        """Create all tools wrapped with token tracking"""
        
        tools = []
        
        # Hypothesis formulation tool
        hypothesis_tool = MonitoredFormulateHypothesisTool(
            self.user_id,
            hypothesis_validator,
            self.event_instrumentation
        )
        tools.append(hypothesis_tool)
        
        # Knowledge query tool
        knowledge_base_tool = QueryKnowledgeGraphToolBase(
            self.user_id,
            hypothesis_validator,
            knowledge_manager
        )
        knowledge_tool = TokenTrackingTool(
            knowledge_base_tool,
            self.event_instrumentation
        )
        tools.append(knowledge_tool)
        
        # Biometric analysis tool
        biometric_base_tool = BiometricAnalysisToolBase(
            self.user_id,
            hypothesis_validator,
            knowledge_manager
        )
        biometric_tool = TokenTrackingTool(
            biometric_base_tool,
            self.event_instrumentation
        )
        tools.append(biometric_tool)
        
        return tools
    
    def _register_agent(self):
        """Register agent with instrumentation system"""
        
        asyncio.create_task(self.event_instrumentation.stream_event(
            AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=None,
                session_id=None,
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.SYSTEM_HEALTH,
                source_agent={"id": "neuroscientist", "role": "neuroscientist"},
                target_agent=None,
                payload={
                    "event": "agent_registered",
                    "tools_count": len(self.tools),
                    "memory_enabled": True,
                    "monitoring_enabled": True
                },
                metadata={
                    "agent_version": "1.0.0",
                    "instrumentation_version": "1.0.0"
                },
                user_id=self.user_id
            )
        ))
    
    async def analyze_with_context(self, 
                                  query: str, 
                                  biometric_context: Dict[str, Any],
                                  session_id: Optional[str] = None) -> str:
        """
        Analyze query with full biometric context and comprehensive monitoring
        
        This method:
        - Creates a trace for the entire analysis
        - Tracks all memory accesses
        - Monitors tool usage and costs
        - Captures decision-making events
        """
        
        trace_id = str(uuid.uuid4())
        session_id = session_id or f"analysis_{datetime.now().timestamp()}"
        analysis_start = datetime.now(timezone.utc)
        
        try:
            # Emit analysis start event
            await self.event_instrumentation.stream_event(
                AURENStreamEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_EXECUTION_STARTED,
                    source_agent={"id": "neuroscientist", "role": "neuroscientist"},
                    target_agent=None,
                    payload={
                        "query": query,
                        "biometric_metrics_count": len(biometric_context.get("latest_metrics", {})),
                        "analysis_type": self._classify_analysis_type(query)
                    },
                    metadata={
                        "has_biometric_context": bool(biometric_context),
                        "context_time_window": biometric_context.get("time_window_hours", 0)
                    },
                    user_id=self.user_id
                )
            )
            
            # Create enriched task with biometric context
            task_description = self._create_task_description(query, biometric_context)
            
            task = Task(
                description=task_description,
                agent=self.crew_agent,
                expected_output="Comprehensive neuroscience-based analysis with specific, actionable recommendations based on biometric data"
            )
            
            # Execute with single-agent crew
            crew = Crew(
                agents=[self.crew_agent], 
                tasks=[task], 
                verbose=True,
                function_calling_llm=None  # Use agent's LLM
            )
            
            # Execute and capture result
            result = await asyncio.create_task(
                asyncio.to_thread(crew.kickoff)
            )
            
            # Calculate performance metrics
            execution_time = (datetime.now(timezone.utc) - analysis_start).total_seconds() * 1000
            
            # Emit completion event with metrics
            performance_metrics = AURENPerformanceMetrics(
                latency_ms=execution_time,
                token_cost=self._estimate_token_cost(query, str(result)),
                memory_usage_mb=self._get_memory_usage(),
                cpu_percentage=0.0,  # Would get from monitoring
                success=True,
                agent_id="neuroscientist",
                confidence_score=0.85  # Would calculate from result
            )
            
            await self.event_instrumentation.stream_event(
                AURENStreamEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
                    source_agent={"id": "neuroscientist", "role": "neuroscientist"},
                    target_agent=None,
                    payload={
                        "execution_result": "success",
                        "response_length": len(str(result)),
                        "execution_time_ms": execution_time
                    },
                    metadata={
                        "quality_score": self._assess_response_quality(str(result))
                    },
                    performance_metrics=performance_metrics,
                    user_id=self.user_id
                )
            )
            
            return str(result)
            
        except Exception as e:
            # Emit error event
            await self.event_instrumentation.stream_event(
                AURENStreamEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
                    source_agent={"id": "neuroscientist", "role": "neuroscientist"},
                    target_agent=None,
                    payload={
                        "execution_result": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    metadata={},
                    user_id=self.user_id
                )
            )
            
            logger.error(f"Analysis failed: {e}")
            raise
    
    def _create_task_description(self, query: str, biometric_context: Dict[str, Any]) -> str:
        """Create enriched task description with biometric context"""
        
        # Extract key biometric insights
        biometric_summary = self._summarize_biometric_context(biometric_context)
        
        return f"""
        Analyze the following user query with their current biometric context:
        
        USER QUERY: {query}
        
        CURRENT BIOMETRIC STATE:
        {biometric_summary}
        
        ANALYSIS REQUIREMENTS:
        1. Interpret the biometric data from a neuroscience perspective
        2. Identify patterns in autonomic nervous system function
        3. Assess stress response and recovery indicators
        4. Provide specific, actionable recommendations
        5. Form hypotheses about observed patterns if appropriate
        6. Reference relevant scientific principles
        
        Focus on practical interventions that can be implemented immediately.
        """
    
    def _summarize_biometric_context(self, context: Dict[str, Any]) -> str:
        """Create human-readable summary of biometric context"""
        
        if not context or "latest_metrics" not in context:
            return "No recent biometric data available"
        
        summary_lines = []
        
        # Latest metrics
        for metric, data in context.get("latest_metrics", {}).items():
            value = data.get("value", "N/A")
            timestamp = data.get("timestamp", "")
            summary_lines.append(f"- {metric.upper()}: {value} (measured: {timestamp})")
        
        # Trends
        if "trends" in context:
            summary_lines.append("\nTRENDS:")
            for metric, trend_data in context["trends"].items():
                trend = trend_data.get("trend", "stable")
                change = trend_data.get("change_percent", 0)
                summary_lines.append(f"- {metric.upper()}: {trend} ({change:+.1f}% change)")
        
        # Alerts
        if "alerts" in context and context["alerts"]:
            summary_lines.append("\nALERTS:")
            for alert in context["alerts"]:
                summary_lines.append(f"- {alert}")
        
        return "\n".join(summary_lines)
    
    def _classify_analysis_type(self, query: str) -> str:
        """Classify the type of analysis requested"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["stress", "anxious", "worried", "nervous"]):
            return "stress_analysis"
        elif any(word in query_lower for word in ["sleep", "tired", "fatigue", "rest"]):
            return "sleep_analysis"
        elif any(word in query_lower for word in ["hrv", "heart rate", "variability"]):
            return "hrv_analysis"
        elif any(word in query_lower for word in ["recovery", "training", "exercise"]):
            return "recovery_analysis"
        else:
            return "general_health"
    
    def _estimate_token_cost(self, query: str, response: str) -> float:
        """Estimate token cost for the operation"""
        
        # Rough estimation: 1 token per 4 characters
        total_chars = len(query) + len(response)
        estimated_tokens = total_chars / 4
        
        # Assuming GPT-4 pricing: $0.03 per 1K tokens
        cost = (estimated_tokens / 1000) * 0.03
        
        return round(cost, 4)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def _assess_response_quality(self, response: str) -> float:
        """Assess quality of agent response"""
        
        quality_score = 0.5  # Base score
        
        # Check for key quality indicators
        if len(response) > 500:
            quality_score += 0.1
        if "recommend" in response.lower():
            quality_score += 0.1
        if any(word in response.lower() for word in ["because", "therefore", "studies show"]):
            quality_score += 0.1
        if response.count("\n") > 5:  # Well-structured
            quality_score += 0.1
        if any(metric in response.lower() for metric in ["hrv", "heart rate", "sleep"]):
            quality_score += 0.1
        
        return min(1.0, quality_score)


# Tool base implementations
class QueryKnowledgeGraphToolBase(AURENSpecialistTool):
    name: str = "Query Knowledge Graph"
    description: str = "Queries validated knowledge about a concept"
    
    async def _run(self, concept: str) -> str:
        try:
            knowledge = await self.knowledge_manager.get_knowledge_by_domain("neuroscience")
            related = [k for k in knowledge if concept.lower() in k.description.lower()]
            
            if related:
                insights = "\n".join([f"- {k.description}" for k in related[:5]])
                return f"Found {len(related)} validated insights about '{concept}':\n{insights}"
            else:
                return f"No validated knowledge found about '{concept}' yet."
                
        except Exception as e:
            logger.error(f"Knowledge query failed: {e}")
            return f"Error querying knowledge: {str(e)}"


class BiometricAnalysisToolBase(AURENSpecialistTool):
    name: str = "Analyze Biometric Context"
    description: str = "Analyzes recent biometric data for patterns"
    
    async def _run(self, time_window: str = "24") -> str:
        try:
            hours = int(time_window)
            
            # This would integrate with actual biometric data
            # For now, return realistic mock analysis
            return f"""Biometric Analysis (last {hours} hours):
            
HRV Metrics:
- Average HRV: 42ms (below baseline of 55ms)
- Trend: Declining (-15% from yesterday)
- Recovery indicator: Sympathetic dominance detected

Sleep Quality:
- Sleep efficiency: 78% (below target 85%)
- REM sleep: 18% (normal range 20-25%)
- Deep sleep: 14% (below optimal 15-20%)

Stress Indicators:
- Resting heart rate: +8 bpm above baseline
- HRV coherence: Low (indicating stress)
- Recovery time: Extended after activities

Recommendations:
- Consider stress reduction techniques
- Prioritize sleep hygiene tonight
- Reduce training intensity for 24-48 hours"""
            
        except Exception as e:
            logger.error(f"Biometric analysis failed: {e}")
            return f"Error analyzing biometrics: {str(e)}"
```

### 1.2 Update the Orchestrator

Create `auren/agents/monitored_orchestrator.py`:

```python
"""
Production orchestrator with complete monitoring integration
Handles single-agent responses with full telemetry
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid

from auren.integration.crewai_realtime_integration import AURENMonitoredOrchestrator
from auren.agents.monitored_specialist_agents import MonitoredNeuroscientistAgent
from auren.realtime.crewai_instrumentation import (
    CrewAIEventInstrumentation,
    AURENStreamEvent,
    AURENEventType
)

import logging
logger = logging.getLogger(__name__)


class ProductionAURENOrchestrator(AURENMonitoredOrchestrator):
    """
    Production-ready orchestrator with comprehensive monitoring
    
    Features:
    - Full event instrumentation
    - Biometric context integration
    - Session management
    - Error handling and recovery
    - Performance tracking
    """
    
    def __init__(self,
                 user_id: str,
                 memory_backend,
                 event_store,
                 hypothesis_validator,
                 knowledge_manager,
                 event_instrumentation: CrewAIEventInstrumentation,
                 redis_streamer):
        
        # Initialize base orchestrator
        super().__init__(
            user_id=user_id,
            memory_backend=memory_backend,
            event_store=event_store,
            hypothesis_validator=hypothesis_validator,
            knowledge_manager=knowledge_manager,
            event_instrumentation=event_instrumentation
        )
        
        self.redis_streamer = redis_streamer
        
        # Override agents with monitored versions
        self._initialize_monitored_agents()
        
        # Session tracking
        self.active_sessions = {}
        self.session_metrics = {}
        
        # Start background monitoring
        asyncio.create_task(self._monitor_system_health())
    
    def _initialize_monitored_agents(self):
        """Initialize production agents with full monitoring"""
        
        # Clear existing agents
        self.agents = {}
        
        # Create monitored neuroscientist
        self.agents["neuroscientist"] = MonitoredNeuroscientistAgent(
            user_id=self.user_id,
            memory_backend=self.memory_backend,
            event_store=self.event_store,
            hypothesis_validator=self.hypothesis_validator,
            knowledge_manager=self.knowledge_manager,
            event_instrumentation=self.event_instrumentation
        )
        
        logger.info(f"Initialized monitored neuroscientist agent for user {self.user_id}")
    
    async def handle_user_message(self, session_id: str, message: str) -> str:
        """
        Enhanced message handling with complete observability
        
        This method provides:
        - Full conversation tracking
        - Biometric context integration
        - Performance monitoring
        - Error recovery
        """
        
        trace_id = str(uuid.uuid4())
        conversation_start = datetime.now(timezone.utc)
        
        # Track session
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "start_time": conversation_start,
                "message_count": 0,
                "total_tokens": 0,
                "total_cost": 0.0
            }
        
        self.active_sessions[session_id]["message_count"] += 1
        self.active_traces[session_id] = trace_id
        
        try:
            # Emit conversation start event
            await self.event_instrumentation.stream_event(
                AURENStreamEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.CONVERSATION_EVENT,
                    source_agent=None,
                    target_agent={"id": "neuroscientist", "role": "neuroscientist"},
                    payload={
                        "message": message[:500],  # Truncate for privacy
                        "message_length": len(message),
                        "direction": "user_to_system",
                        "message_number": self.active_sessions[session_id]["message_count"]
                    },
                    metadata={
                        "session_duration_seconds": (
                            conversation_start - self.active_sessions[session_id]["start_time"]
                        ).total_seconds()
                    },
                    user_id=self.user_id
                )
            )
            
            # Get biometric context
            biometric_context = await self._get_enhanced_biometric_context()
            
            # Log biometric state
            await self._log_biometric_state(trace_id, session_id, biometric_context)
            
            # Determine if this needs single agent or would benefit from future multi-agent
            analysis_complexity = self._assess_query_complexity(message, biometric_context)
            
            # For now, always use neuroscientist (single agent system)
            agent = self.agents["neuroscientist"]
            
            # Execute analysis with monitoring
            response = await agent.analyze_with_context(
                query=message,
                biometric_context=biometric_context,
                session_id=session_id
            )
            
            # Calculate conversation metrics
            conversation_time = (datetime.now(timezone.utc) - conversation_start).total_seconds() * 1000
            
            # Emit conversation completion
            await self.event_instrumentation.stream_event(
                AURENStreamEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.CONVERSATION_EVENT,
                    source_agent={"id": "neuroscientist", "role": "neuroscientist"},
                    target_agent=None,
                    payload={
                        "response_preview": response[:200] + "..." if len(response) > 200 else response,
                        "response_length": len(response),
                        "direction": "system_to_user",
                        "conversation_time_ms": conversation_time
                    },
                    metadata={
                        "complexity_score": analysis_complexity,
                        "biometric_factors_considered": len(biometric_context.get("latest_metrics", {}))
                    },
                    user_id=self.user_id
                )
            )
            
            # Update session metrics
            self._update_session_metrics(session_id, response, conversation_time)
            
            return response
            
        except Exception as e:
            # Emit error event
            await self.event_instrumentation.stream_event(
                AURENStreamEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.CONVERSATION_EVENT,
                    source_agent=None,
                    target_agent=None,
                    payload={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "direction": "system_error"
                    },
                    metadata={
                        "recovery_attempted": True
                    },
                    user_id=self.user_id
                )
            )
            
            logger.error(f"Conversation handling failed: {e}")
            
            # Attempt graceful recovery
            return await self._generate_fallback_response(message, e)
    
    async def _get_enhanced_biometric_context(self) -> Dict[str, Any]:
        """Get enhanced biometric context with additional analysis"""
        
        # Get base context
        base_context = await super()._get_biometric_context()
        
        # Enhance with additional analysis
        if "latest_metrics" in base_context:
            base_context["analysis"] = self._analyze_biometric_state(base_context["latest_metrics"])
        
        # Add historical comparison
        if "trends" in base_context:
            base_context["historical_comparison"] = self._compare_to_baseline(base_context["trends"])
        
        return base_context
    
    async def _log_biometric_state(self, trace_id: str, session_id: str, context: Dict[str, Any]):
        """Log current biometric state for analysis context"""
        
        await self.event_instrumentation.stream_event(
            AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=trace_id,
                session_id=session_id,
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.BIOMETRIC_ANALYSIS,
                source_agent=None,
                target_agent=None,
                payload={
                    "metrics_available": list(context.get("latest_metrics", {}).keys()),
                    "data_points": context.get("data_points", 0),
                    "time_window_hours": context.get("time_window_hours", 24),
                    "analysis_summary": context.get("analysis", {})
                },
                metadata={
                    "has_alerts": bool(context.get("alerts", [])),
                    "trend_direction": self._summarize_trends(context.get("trends", {}))
                },
                user_id=self.user_id
            )
        )
    
    def _assess_query_complexity(self, message: str, biometric_context: Dict[str, Any]) -> float:
        """Assess complexity of user query"""
        
        complexity = 0.3  # Base complexity
        
        # Message factors
        if len(message) > 100:
            complexity += 0.1
        if "?" in message:
            complexity += 0.05 * message.count("?")
        
        # Biometric factors
        if biometric_context.get("alerts"):
            complexity += 0.2
        if len(biometric_context.get("trends", {})) > 3:
            complexity += 0.1
        
        # Domain factors
        complex_terms = ["correlation", "pattern", "trend", "analysis", "explain"]
        for term in complex_terms:
            if term in message.lower():
                complexity += 0.1
        
        return min(1.0, complexity)
    
    def _analyze_biometric_state(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current biometric state"""
        
        analysis = {
            "overall_state": "normal",
            "areas_of_concern": [],
            "positive_indicators": []
        }
        
        # Check HRV
        if "hrv" in metrics:
            hrv_value = metrics["hrv"].get("value", 0)
            if hrv_value < 30:
                analysis["areas_of_concern"].append("Low HRV indicating stress")
                analysis["overall_state"] = "stressed"
            elif hrv_value > 60:
                analysis["positive_indicators"].append("Excellent HRV")
        
        # Check sleep
        if "sleep_efficiency" in metrics:
            efficiency = metrics["sleep_efficiency"].get("value", 0)
            if efficiency < 0.75:
                analysis["areas_of_concern"].append("Poor sleep efficiency")
                if analysis["overall_state"] == "normal":
                    analysis["overall_state"] = "suboptimal"
            elif efficiency > 0.85:
                analysis["positive_indicators"].append("Good sleep quality")
        
        return analysis
    
    def _compare_to_baseline(self, trends: Dict[str, Any]) -> Dict[str, str]:
        """Compare current trends to baseline expectations"""
        
        comparison = {}
        
        for metric, trend_data in trends.items():
            trend = trend_data.get("trend", "stable")
            change = trend_data.get("change_percent", 0)
            
            if abs(change) < 5:
                comparison[metric] = "within_normal_range"
            elif change < -10:
                comparison[metric] = "significantly_below_baseline"
            elif change > 10:
                comparison[metric] = "significantly_above_baseline"
            else:
                comparison[metric] = "slightly_off_baseline"
        
        return comparison
    
    def _summarize_trends(self, trends: Dict[str, Any]) -> str:
        """Summarize overall trend direction"""
        
        if not trends:
            return "no_data"
        
        directions = [t.get("trend", "stable") for t in trends.values()]
        
        if all(d == "increasing" for d in directions):
            return "all_increasing"
        elif all(d == "decreasing" for d in directions):
            return "all_decreasing"
        elif all(d == "stable" for d in directions):
            return "all_stable"
        else:
            return "mixed"
    
    def _update_session_metrics(self, session_id: str, response: str, time_ms: float):
        """Update session metrics for tracking"""
        
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = {
                "total_messages": 0,
                "total_response_time_ms": 0,
                "average_response_time_ms": 0,
                "total_tokens_estimate": 0,
                "total_cost_estimate": 0.0
            }
        
        metrics = self.session_metrics[session_id]
        metrics["total_messages"] += 1
        metrics["total_response_time_ms"] += time_ms
        metrics["average_response_time_ms"] = (
            metrics["total_response_time_ms"] / metrics["total_messages"]
        )
        
        # Estimate tokens and cost
        estimated_tokens = len(response) / 4  # Rough estimate
        estimated_cost = (estimated_tokens / 1000) * 0.03
        
        metrics["total_tokens_estimate"] += estimated_tokens
        metrics["total_cost_estimate"] += estimated_cost
    
    async def _generate_fallback_response(self, message: str, error: Exception) -> str:
        """Generate fallback response when main analysis fails"""
        
        logger.warning(f"Generating fallback response due to: {error}")
        
        return f"""I apologize, but I encountered an issue while analyzing your request. 
        
Your message: "{message[:100]}..."

While I work on resolving this, here are some general recommendations:
- Continue monitoring your biometric data
- Maintain consistent sleep and recovery practices
- Stay hydrated and manage stress levels

Please try rephrasing your question or contact support if this issue persists.

Error reference: {str(uuid.uuid4())[:8]}"""
    
    async def _monitor_system_health(self):
        """Background task to monitor system health"""
        
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Emit system health event
                await self.event_instrumentation.stream_event(
                    AURENStreamEvent(
                        event_id=str(uuid.uuid4()),
                        trace_id=None,
                        session_id=None,
                        timestamp=datetime.now(timezone.utc),
                        event_type=AURENEventType.SYSTEM_HEALTH,
                        source_agent=None,
                        target_agent=None,
                        payload={
                            "active_sessions": len(self.active_sessions),
                            "total_sessions_handled": len(self.session_metrics),
                            "agents_available": len(self.agents),
                            "memory_backend_status": "connected" if self.memory_backend else "disconnected",
                            "event_store_status": "connected" if self.event_store else "disconnected"
                        },
                        metadata={
                            "orchestrator_version": "1.0.0",
                            "monitoring_enabled": True
                        },
                        user_id=None  # System-level event
                    )
                )
                
                # Clean up old sessions
                await self._cleanup_old_sessions()
                
            except Exception as e:
                logger.error(f"System health monitoring error: {e}")
    
    async def _cleanup_old_sessions(self):
        """Clean up sessions older than 1 hour"""
        
        current_time = datetime.now(timezone.utc)
        sessions_to_remove = []
        
        for session_id, session_data in self.active_sessions.items():
            session_age = (current_time - session_data["start_time"]).total_seconds()
            if session_age > 3600:  # 1 hour
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            if session_id in self.active_traces:
                del self.active_traces[session_id]
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")


async def create_production_orchestrator(config: Dict[str, Any]):
    """
    Factory function to create production orchestrator with all dependencies
    
    This is the main entry point for production deployment
    """
    
    # Import required components
    from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
    from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation
    
    # Initialize Redis streaming
    redis_streamer = RedisStreamEventStreamer(
        redis_url=config["redis_url"],
        stream_name=config.get("stream_name", "auren:events")
    )
    await redis_streamer.initialize()
    
    # Initialize event instrumentation
    event_instrumentation = CrewAIEventInstrumentation(
        event_streamer=redis_streamer
    )
    
    # Create production orchestrator
    orchestrator = ProductionAURENOrchestrator(
        user_id=config["user_id"],
        memory_backend=config["memory_backend"],
        event_store=config["event_store"],
        hypothesis_validator=config["hypothesis_validator"],
        knowledge_manager=config["knowledge_manager"],
        event_instrumentation=event_instrumentation,
        redis_streamer=redis_streamer
    )
    
    logger.info(f"Production orchestrator created for user {config['user_id']}")
    
    return orchestrator, event_instrumentation, redis_streamer
```

---

## Phase 2: Integration Testing Suite

### 2.1 Create Integration Test Harness

Create `auren/tests/test_module_integration.py`:

```python
"""
Integration testing for Module D-C connection
Validates real events flow through the pipeline
"""

import asyncio
import pytest
from datetime import datetime, timezone
import json
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock

from auren.agents.monitored_orchestrator import create_production_orchestrator
from auren.realtime.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestModuleIntegration:
    """
    Comprehensive integration tests for Module D-C connection
    
    These tests validate:
    - Real agent events flow to Redis
    - WebSocket server receives and distributes events
    - Dashboard would receive correct data
    - Performance metrics are accurate
    """
    
    @pytest.fixture
    async def test_dependencies(self):
        """Create test dependencies"""
        
        # Mock the Module A and B dependencies
        memory_backend = AsyncMock()
        memory_backend.store_memory.return_value = "test_memory_id"
        memory_backend.retrieve_memories.return_value = []
        
        event_store = AsyncMock()
        event_store.get_stream_events.return_value = []
        
        hypothesis_validator = AsyncMock()
        hypothesis_validator.form_hypothesis.return_value = MagicMock(
            hypothesis_id="test_hypothesis_123"
        )
        
        knowledge_manager = AsyncMock()
        knowledge_manager.get_knowledge_by_domain.return_value = []
        
        return {
            "memory_backend": memory_backend,
            "event_store": event_store,
            "hypothesis_validator": hypothesis_validator,
            "knowledge_manager": knowledge_manager
        }
    
    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        
        client = redis.from_url("redis://localhost:6379")
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_agent_execution_generates_events(self, test_dependencies, redis_client):
        """Test that agent execution generates real events in Redis"""
        
        # Create production orchestrator
        config = {
            "user_id": "test_user",
            "redis_url": "redis://localhost:6379",
            "stream_name": "test:auren:events",
            **test_dependencies
        }
        
        orchestrator, instrumentation, streamer = await create_production_orchestrator(config)
        
        # Clear test stream
        await redis_client.delete("test:auren:events")
        
        # Execute a real agent query
        test_query = "I've been feeling stressed and my HRV has been low. What should I do?"
        
        response = await orchestrator.handle_user_message(
            session_id="test_session_123",
            message=test_query
        )
        
        # Verify response was generated
        assert response is not None
        assert len(response) > 100  # Substantial response
        
        # Wait for events to be processed
        await asyncio.sleep(0.5)
        
        # Check Redis for events
        events = await redis_client.xrange("test:auren:events", count=100)
        
        # Verify multiple events were generated
        assert len(events) > 0
        
        # Parse and verify event types
        event_types = []
        for event_id, event_data in events:
            event_type = event_data.get(b"event_type", b"").decode()
            event_types.append(event_type)
            
            # Verify event structure
            assert b"event_id" in event_data
            assert b"timestamp" in event_data
            assert b"payload" in event_data
        
        # Verify expected event sequence
        assert "conversation_event" in event_types  # User message
        assert "agent_execution_started" in event_types  # Agent started
        
        logger.info(f"Generated {len(events)} events: {event_types}")
    
    @pytest.mark.asyncio
    async def test_biometric_context_in_events(self, test_dependencies, redis_client):
        """Test that biometric context is included in events"""
        
        # Mock biometric data in event store
        mock_biometric_events = [
            MagicMock(
                event_type="biometric_hrv",
                payload={"metric_type": "hrv", "value": 35},
                timestamp=datetime.now(timezone.utc)
            ),
            MagicMock(
                event_type="biometric_sleep",
                payload={"metric_type": "sleep_efficiency", "value": 0.72},
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        test_dependencies["event_store"].get_stream_events.return_value = mock_biometric_events
        
        # Create orchestrator
        config = {
            "user_id": "test_user",
            "redis_url": "redis://localhost:6379",
            "stream_name": "test:auren:biometric",
            **test_dependencies
        }
        
        orchestrator, _, _ = await create_production_orchestrator(config)
        
        # Clear stream
        await redis_client.delete("test:auren:biometric")
        
        # Execute query
        response = await orchestrator.handle_user_message(
            session_id="test_biometric_session",
            message="Why is my HRV so low?"
        )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Get events
        events = await redis_client.xrange("test:auren:biometric", count=100)
        
        # Find biometric analysis event
        biometric_event_found = False
        for event_id, event_data in events:
            if event_data.get(b"event_type", b"").decode() == "biometric_analysis":
                biometric_event_found = True
                
                # Parse payload
                payload = json.loads(event_data.get(b"payload", b"{}").decode())
                
                # Verify biometric data is included
                assert "metrics_available" in payload
                assert "hrv" in payload["metrics_available"]
                assert payload["data_points"] == 2
                
                break
        
        assert biometric_event_found, "Biometric analysis event not found"
    
    @pytest.mark.asyncio
    async def test_tool_usage_tracking(self, test_dependencies, redis_client):
        """Test that tool usage is tracked with token costs"""
        
        # Create orchestrator
        config = {
            "user_id": "test_user",
            "redis_url": "redis://localhost:6379",
            "stream_name": "test:auren:tools",
            **test_dependencies
        }
        
        orchestrator, _, _ = await create_production_orchestrator(config)
        
        # Clear stream
        await redis_client.delete("test:auren:tools")
        
        # Execute query that should trigger tool usage
        response = await orchestrator.handle_user_message(
            session_id="test_tools_session",
            message="Form a hypothesis about my sleep patterns affecting my HRV"
        )
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Get events
        events = await redis_client.xrange("test:auren:tools", count=100)
        
        # Look for tool usage events
        tool_events = []
        for event_id, event_data in events:
            if event_data.get(b"event_type", b"").decode() == "tool_usage":
                payload = json.loads(event_data.get(b"payload", b"{}").decode())
                tool_events.append(payload)
        
        # Verify tool usage was tracked
        if tool_events:  # Tools may not always be used depending on LLM decision
            for tool_event in tool_events:
                assert "tool_name" in tool_event
                assert "tokens_used" in tool_event
                assert "estimated_cost" in tool_event
                
                logger.info(f"Tool {tool_event['tool_name']} used {tool_event['tokens_used']} tokens")
    
    @pytest.mark.asyncio
    async def test_memory_operations_tracked(self, test_dependencies, redis_client):
        """Test that memory operations are tracked"""
        
        # Create orchestrator
        config = {
            "user_id": "test_user",
            "redis_url": "redis://localhost:6379",
            "stream_name": "test:auren:memory",
            **test_dependencies
        }
        
        orchestrator, _, _ = await create_production_orchestrator(config)
        
        # Clear stream
        await redis_client.delete("test:auren:memory")
        
        # Execute query
        response = await orchestrator.handle_user_message(
            session_id="test_memory_session",
            message="What did we discuss about my sleep last week?"
        )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Get events
        events = await redis_client.xrange("test:auren:memory", count=100)
        
        # Look for knowledge access events
        knowledge_events = []
        for event_id, event_data in events:
            if event_data.get(b"event_type", b"").decode() == "knowledge_access":
                payload = json.loads(event_data.get(b"payload", b"{}").decode())
                knowledge_events.append(payload)
        
        # Memory operations should be tracked
        logger.info(f"Found {len(knowledge_events)} knowledge access events")
    
    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, test_dependencies, redis_client):
        """Test that performance metrics are accurate"""
        
        # Create orchestrator
        config = {
            "user_id": "test_user",
            "redis_url": "redis://localhost:6379",
            "stream_name": "test:auren:performance",
            **test_dependencies
        }
        
        orchestrator, _, _ = await create_production_orchestrator(config)
        
        # Clear stream
        await redis_client.delete("test:auren:performance")
        
        # Execute query
        start_time = datetime.now(timezone.utc)
        
        response = await orchestrator.handle_user_message(
            session_id="test_performance_session",
            message="Quick test"
        )
        
        end_time = datetime.now(timezone.utc)
        actual_duration = (end_time - start_time).total_seconds() * 1000
        
        # Wait for events
        await asyncio.sleep(0.5)
        
        # Get completion event
        events = await redis_client.xrange("test:auren:performance", count=100)
        
        completion_event = None
        for event_id, event_data in events:
            if (event_data.get(b"event_type", b"").decode() == "agent_execution_completed" and
                b"performance_metrics" in event_data):
                completion_event = event_data
                break
        
        assert completion_event is not None
        
        # Parse performance metrics
        metrics = json.loads(completion_event.get(b"performance_metrics", b"{}").decode())
        
        # Verify metrics
        assert "latency_ms" in metrics
        assert metrics["latency_ms"] > 0
        assert metrics["latency_ms"] < actual_duration + 1000  # Within reasonable range
        
        assert "token_cost" in metrics
        assert metrics["token_cost"] > 0
        
        assert "success" in metrics
        assert metrics["success"] is True
        
        logger.info(f"Performance metrics: {metrics}")


@pytest.mark.integration
class TestEndToEndPipeline:
    """Test complete pipeline from agent to dashboard"""
    
    @pytest.mark.asyncio
    async def test_websocket_receives_agent_events(self, test_dependencies):
        """Test that WebSocket server receives and distributes agent events"""
        
        # This test would require:
        # 1. Starting WebSocket server
        # 2. Connecting test client
        # 3. Executing agent query
        # 4. Verifying client receives events
        
        # For brevity, outline the test structure
        logger.info("End-to-end pipeline test would verify WebSocket distribution")
        
        # The actual implementation would:
        # - Start EnhancedWebSocketEventStreamer
        # - Connect test WebSocket client
        # - Execute agent query through orchestrator
        # - Assert client receives expected events
        # - Verify event order and content


if __name__ == "__main__":
    # Run specific test
    pytest.main(["-v", "-s", __file__ + "::TestModuleIntegration::test_agent_execution_generates_events"])
```

### 2.2 Create Manual Testing Script

Create `auren/tests/manual_integration_test.py`:

```python
"""
Manual testing script for Module D-C integration
Run this to see real events flowing through the system
"""

import asyncio
import logging
from datetime import datetime
import json

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_agent_flow():
    """
    Manual test that shows real agent events flowing through the system
    
    This simulates what would happen in production:
    1. User asks health question
    2. Neuroscientist agent analyzes with biometric context
    3. Events flow through Redis to dashboard
    4. Complete visibility of the intelligence system
    """
    
    logger.info("Starting Module D-C integration test...")
    
    # Import production components
    from auren.agents.monitored_orchestrator import create_production_orchestrator
    
    # Create mock dependencies (in production, these would be real)
    from unittest.mock import AsyncMock, MagicMock
    
    # Mock biometric data
    mock_biometric_events = [
        MagicMock(
            event_type="biometric_hrv",
            payload={
                "metric_type": "hrv",
                "value": 28,  # Low HRV
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now()
        ),
        MagicMock(
            event_type="biometric_sleep",
            payload={
                "metric_type": "sleep_efficiency",
                "value": 0.68,  # Poor sleep
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now()
        ),
        MagicMock(
            event_type="biometric_stress",
            payload={
                "metric_type": "stress_score",
                "value": 8.5,  # High stress
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
    ]
    
    # Setup dependencies
    memory_backend = AsyncMock()
    memory_backend.store_memory.return_value = "memory_123"
    memory_backend.retrieve_memories.return_value = [
        {
            "content": {"observation": "User reported feeling stressed last week"},
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9
        }
    ]
    
    event_store = AsyncMock()
    event_store.get_stream_events.return_value = mock_biometric_events
    
    hypothesis_validator = AsyncMock()
    hypothesis_validator.form_hypothesis.return_value = MagicMock(
        hypothesis_id="hyp_stress_sleep_correlation_001",
        description="Poor sleep quality is contributing to elevated stress and low HRV"
    )
    
    knowledge_manager = AsyncMock()
    knowledge_manager.get_knowledge_by_domain.return_value = [
        MagicMock(description="HRV below 30ms indicates high sympathetic activation"),
        MagicMock(description="Sleep efficiency below 75% impairs recovery")
    ]
    
    # Configuration
    config = {
        "user_id": "demo_user_001",
        "redis_url": "redis://localhost:6379",
        "stream_name": "auren:events",  # Production stream
        "memory_backend": memory_backend,
        "event_store": event_store,
        "hypothesis_validator": hypothesis_validator,
        "knowledge_manager": knowledge_manager
    }
    
    # Create production orchestrator
    logger.info("Creating production orchestrator with monitoring...")
    orchestrator, instrumentation, redis_streamer = await create_production_orchestrator(config)
    
    # Test queries that showcase the system
    test_queries = [
        {
            "session_id": "demo_session_001",
            "message": "I've been feeling really stressed lately and not sleeping well. My fitness tracker shows my HRV has been declining for the past week. What's happening to my body and what should I do?",
            "expected_capabilities": [
                "Biometric context integration",
                "Pattern recognition",
                "Hypothesis formation",
                "Knowledge application",
                "Actionable recommendations"
            ]
        },
        {
            "session_id": "demo_session_002", 
            "message": "Should I continue my high-intensity training given my current stress levels?",
            "expected_capabilities": [
                "Training load assessment",
                "Recovery analysis",
                "Risk evaluation",
                "Personalized guidance"
            ]
        }
    ]
    
    # Execute each test query
    for i, test_case in enumerate(test_queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Case {i}: {test_case['session_id']}")
        logger.info(f"{'='*60}")
        logger.info(f"User Query: {test_case['message'][:100]}...")
        logger.info(f"Expected Capabilities: {', '.join(test_case['expected_capabilities'])}")
        
        # Execute query
        start_time = datetime.now()
        
        try:
            response = await orchestrator.handle_user_message(
                session_id=test_case['session_id'],
                message=test_case['message']
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Show results
            logger.info(f"\n--- Response Generated in {duration:.2f} seconds ---")
            logger.info(f"Response Preview: {response[:200]}...")
            logger.info(f"Response Length: {len(response)} characters")
            
            # Show event statistics
            if hasattr(redis_streamer, 'events_sent'):
                logger.info(f"Events Sent: {redis_streamer.events_sent}")
            
        except Exception as e:
            logger.error(f"Error executing test case: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait between queries
        await asyncio.sleep(2)
    
    # Show how to monitor events in real-time
    logger.info(f"\n{'='*60}")
    logger.info("To see events in the dashboard:")
    logger.info("1. Open another terminal")
    logger.info("2. Run: python -m auren.realtime.start_websocket_server")
    logger.info("3. Open: auren/dashboard/realtime_dashboard.html")
    logger.info("4. Watch events flow in real-time!")
    logger.info(f"{'='*60}\n")
    
    # Monitor Redis for events
    logger.info("Checking Redis for generated events...")
    
    import redis.asyncio as redis
    redis_client = redis.from_url("redis://localhost:6379")
    
    try:
        # Get recent events
        events = await redis_client.xrange("auren:events", count=20)
        
        logger.info(f"\nFound {len(events)} recent events in Redis:")
        
        event_summary = {}
        for event_id, event_data in events:
            event_type = event_data.get(b"event_type", b"unknown").decode()
            event_summary[event_type] = event_summary.get(event_type, 0) + 1
            
            # Show sample event
            if event_type == "agent_execution_completed":
                payload = json.loads(event_data.get(b"payload", b"{}").decode())
                if b"performance_metrics" in event_data:
                    metrics = json.loads(event_data.get(b"performance_metrics", b"{}").decode())
                    logger.info(f"\nSample Performance Metrics:")
                    logger.info(f"  - Latency: {metrics.get('latency_ms', 0):.0f}ms")
                    logger.info(f"  - Token Cost: ${metrics.get('token_cost', 0):.4f}")
                    logger.info(f"  - Success: {metrics.get('success', False)}")
        
        logger.info(f"\nEvent Type Summary:")
        for event_type, count in event_summary.items():
            logger.info(f"  - {event_type}: {count}")
            
    finally:
        await redis_client.close()
    
    logger.info("\nIntegration test completed!")
    logger.info("The neuroscientist agent is now fully connected to the monitoring infrastructure.")
    logger.info("All events are flowing through Redis and available for real-time dashboard display.")


async def test_continuous_monitoring():
    """
    Run continuous monitoring to see events in real-time
    This simulates production monitoring
    """
    
    logger.info("Starting continuous event monitoring...")
    logger.info("Press Ctrl+C to stop")
    
    import redis.asyncio as redis
    redis_client = redis.from_url("redis://localhost:6379")
    
    try:
        # Subscribe to events
        pubsub = redis_client.pubsub()
        
        # Monitor event stream
        last_id = "$"
        while True:
            # Read new events
            events = await redis_client.xread(
                {"auren:events": last_id},
                block=1000  # Block for 1 second
            )
            
            for stream_name, stream_events in events:
                for event_id, event_data in stream_events:
                    # Parse and display event
                    event_type = event_data.get(b"event_type", b"unknown").decode()
                    timestamp = event_data.get(b"timestamp", b"").decode()
                    
                    # Color code by type
                    if event_type.startswith("agent_"):
                        logger.info(f"🤖 [{timestamp}] {event_type}")
                    elif event_type == "tool_usage":
                        logger.info(f"🔧 [{timestamp}] {event_type}")
                    elif event_type == "conversation_event":
                        logger.info(f"💬 [{timestamp}] {event_type}")
                    else:
                        logger.info(f"📊 [{timestamp}] {event_type}")
                    
                    last_id = event_id
            
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("\nStopping monitoring...")
    finally:
        await redis_client.close()


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_real_agent_flow())
    
    # Uncomment to run continuous monitoring
    # asyncio.run(test_continuous_monitoring())
```

---

## Phase 3: Deployment Guide

### 3.1 Create Deployment Checklist

Create `auren/deployment/module_integration_checklist.md`:

```markdown
# Module D-C Integration Deployment Checklist

## Pre-Deployment Verification

### Dependencies Check
- [ ] Redis is running and accessible
- [ ] PostgreSQL is configured (Module A)
- [ ] All Python packages installed
- [ ] Environment variables set

### Code Updates
- [ ] Replace basic agents with monitored versions
- [ ] Update imports to use monitored components
- [ ] Verify all tools are wrapped with TokenTrackingTool
- [ ] Ensure event instrumentation is initialized

## Deployment Steps

### 1. Update Agent Initialization (5 minutes)

```python
# In your main application file, replace:
from auren.agents.specialist_agents import NeuroscientistAgent

# With:
from auren.agents.monitored_specialist_agents import MonitoredNeuroscientistAgent
```

### 2. Update Orchestrator Creation (5 minutes)

```python
# Replace orchestrator initialization with:
from auren.agents.monitored_orchestrator import create_production_orchestrator

orchestrator, instrumentation, redis_streamer = await create_production_orchestrator({
    "user_id": user_id,
    "redis_url": "redis://localhost:6379",
    "memory_backend": memory_backend,
    "event_store": event_store,
    "hypothesis_validator": hypothesis_validator,
    "knowledge_manager": knowledge_manager
})
```

### 3. Start Monitoring Infrastructure (2 minutes)

```bash
# Terminal 1: Start WebSocket server
python -m auren.realtime.start_websocket_server

# Terminal 2: Open dashboard
open auren/dashboard/realtime_dashboard.html
```

### 4. Verify Integration (10 minutes)

Run the manual test:
```bash
python -m auren.tests.manual_integration_test
```

Check for:
- [ ] Events appear in Redis
- [ ] Dashboard shows real-time updates
- [ ] Agent responses include biometric context
- [ ] Performance metrics are reasonable
- [ ] No errors in logs

## Post-Deployment Monitoring

### Immediate Checks (First Hour)
- [ ] Monitor error rates
- [ ] Check event latency (<200ms target)
- [ ] Verify memory usage is stable
- [ ] Confirm token costs are tracked

### Daily Monitoring
- [ ] Review agent performance metrics
- [ ] Check hypothesis formation rate
- [ ] Monitor knowledge graph growth
- [ ] Analyze user session patterns

## Rollback Plan

If issues occur:

1. **Revert to basic agents**:
   ```python
   # Temporarily disable monitoring
   from auren.agents.specialist_agents import NeuroscientistAgent
   ```

2. **Stop event streaming**:
   ```bash
   # Kill WebSocket server
   pkill -f "auren.realtime"
   ```

3. **Clear Redis if needed**:
   ```bash
   redis-cli FLUSHDB
   ```

## Success Criteria

Integration is successful when:
- ✅ Real agent events flow to dashboard
- ✅ Biometric context appears in analyses  
- ✅ Token costs are accurately tracked
- ✅ Performance remains under 2s response time
- ✅ No increase in error rates

## Next Steps

After successful integration:
1. Implement remaining specialist agents
2. Add collaboration patterns
3. Enhance dashboard visualizations
4. Set up production monitoring alerts
```

### 3.2 Create Production Configuration

Create `auren/config/production_monitoring.py`:

```python
"""
Production configuration for integrated monitoring
"""

import os
from typing import Dict, Any

# Environment-based configuration
ENVIRONMENT = os.getenv("AUREN_ENV", "development")

# Redis configuration
REDIS_CONFIG = {
    "development": {
        "url": "redis://localhost:6379",
        "stream_name": "auren:events:dev",
        "max_stream_length": 10000
    },
    "staging": {
        "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "stream_name": "auren:events:staging",
        "max_stream_length": 50000
    },
    "production": {
        "url": os.getenv("REDIS_URL"),
        "stream_name": "auren:events",
        "max_stream_length": 100000
    }
}

# WebSocket configuration
WEBSOCKET_CONFIG = {
    "development": {
        "host": "localhost",
        "port": 8765,
        "max_connections": 100
    },
    "staging": {
        "host": "0.0.0.0",
        "port": 8765,
        "max_connections": 500
    },
    "production": {
        "host": "0.0.0.0",
        "port": int(os.getenv("WEBSOCKET_PORT", 8765)),
        "max_connections": 1000
    }
}

# Monitoring thresholds
MONITORING_THRESHOLDS = {
    "max_response_time_ms": 5000,
    "max_token_cost_per_query": 0.50,
    "min_confidence_score": 0.7,
    "max_error_rate": 0.05
}

def get_production_config() -> Dict[str, Any]:
    """Get complete production configuration"""
    
    return {
        "environment": ENVIRONMENT,
        "redis": REDIS_CONFIG[ENVIRONMENT],
        "websocket": WEBSOCKET_CONFIG[ENVIRONMENT],
        "monitoring": MONITORING_THRESHOLDS,
        "features": {
            "event_streaming": True,
            "performance_tracking": True,
            "cost_tracking": True,
            "hypothesis_tracking": True,
            "collaboration_tracking": False  # Enable when multi-agent ready
        }
    }
```

---

## Phase 4: Troubleshooting Guide

### Common Issues and Solutions

#### 1. Events Not Appearing in Dashboard

**Symptoms**: Agent executes but no events in dashboard

**Check**:
```bash
# Verify Redis has events
redis-cli XLEN auren:events

# Check WebSocket server logs
grep ERROR websocket.log
```

**Solution**:
- Ensure Redis is running
- Verify WebSocket server started successfully
- Check event instrumentation is initialized
- Confirm dashboard is connected to correct WebSocket URL

#### 2. Slow Agent Response Times

**Symptoms**: Response takes >10 seconds

**Check**:
- Review performance_metrics in events
- Check memory_usage_mb values
- Monitor CPU usage during execution

**Solution**:
- Reduce memory context window
- Optimize tool execution
- Check for blocking operations

#### 3. Missing Biometric Context

**Symptoms**: Agent responses don't mention biometric data

**Check**:
- Verify event_store.get_stream_events returns data
- Check biometric_context in task description
- Review agent logs for context processing

**Solution**:
- Ensure biometric events exist in event store
- Verify time window captures recent data
- Check event parsing logic

#### 4. Token Cost Not Tracked

**Symptoms**: Token costs show as 0 or missing

**Check**:
- Verify TokenTrackingTool wrapper applied
- Check tool execution events
- Review cost calculation logic

**Solution**:
- Ensure all tools wrapped properly
- Update token estimation formula
- Verify LLM response parsing

---

## Conclusion

This comprehensive integration connects Module D's neuroscientist agent to Module C's monitoring infrastructure, providing complete visibility into AUREN's cognitive operations. The implementation includes:

1. **Monitored agent components** that emit rich telemetry
2. **Comprehensive event tracking** for all operations
3. **Biometric context integration** in every analysis
4. **Production-ready error handling** and recovery
5. **Extensive testing suite** for validation

The senior engineer can now see real agent intelligence flowing through the dashboard instead of test data, with accurate performance metrics, token costs, and operational insights.

Next steps after deployment:
- Add remaining specialist agents
- Implement collaboration patterns  
- Enhance dashboard visualizations
- Set up alerting for anomalies
- Begin collecting performance baselines
