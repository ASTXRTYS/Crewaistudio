"""
CrewAI Gateway Adapter - Bridges AI Gateway with CrewAI agent execution.

This adapter enables CrewAI agents (specifically the Neuroscientist specialist)
to make LLM calls through the production-ready AI Gateway while maintaining
full observability, cost tracking, and memory integration.

Key features:
- Seamless integration with @track_tokens decorator
- Memory-aware context building
- Model selection based on task complexity
- Full OpenTelemetry instrumentation
- Sub-2 second response times
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..gateway import AIGateway, GatewayRequest
from ..models import ModelConfig
from ...monitoring.decorators import track_tokens
from ...memory.cognitive_twin_profile import CognitiveTwinProfile

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class AgentContext:
    """Context for agent execution including memory and metadata."""
    agent_name: str
    user_id: str
    task_id: str
    conversation_id: str
    memory_context: List[str]
    biometric_data: Optional[Dict[str, Any]] = None
    task_complexity: str = "medium"  # low, medium, high
    require_fast_response: bool = False


class CrewAIGatewayAdapter:
    """
    Adapter that bridges CrewAI agents with the AI Gateway.
    
    This adapter handles:
    - Model selection based on task complexity
    - Memory context injection
    - Token tracking integration
    - OpenTelemetry instrumentation
    - Response time optimization
    """
    
    def __init__(
        self,
        ai_gateway: AIGateway,
        memory_profile: Optional[CognitiveTwinProfile] = None,
        default_model: str = "gpt-3.5-turbo",
        complex_model: str = "gpt-4",
        max_context_tokens: int = 2000
    ):
        """
        Initialize the adapter.
        
        Args:
            ai_gateway: The AI Gateway instance
            memory_profile: Optional cognitive twin profile for memory access
            default_model: Model for standard tasks
            complex_model: Model for complex analysis
            max_context_tokens: Maximum tokens for memory context
        """
        self.gateway = ai_gateway
        self.memory_profile = memory_profile
        self.default_model = default_model
        self.complex_model = complex_model
        self.max_context_tokens = max_context_tokens
        
        # Model selection thresholds
        self.complexity_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.9
        }
    
    @track_tokens(extract_metadata=True)
    async def execute_for_agent(
        self,
        prompt: str,
        context: AgentContext,
        **kwargs
    ) -> str:
        """
        Execute a prompt for a CrewAI agent with full tracking.
        
        This method is decorated with @track_tokens to automatically
        track token usage, costs, and rate limits.
        
        Args:
            prompt: The prompt to execute
            context: Agent execution context
            **kwargs: Additional arguments passed to gateway
            
        Returns:
            The LLM response content
        """
        with tracer.start_as_current_span(
            f"agent_execution.{context.agent_name}"
        ) as span:
            try:
                # Add span attributes
                span.set_attribute("agent.name", context.agent_name)
                span.set_attribute("task.id", context.task_id)
                span.set_attribute("task.complexity", context.task_complexity)
                span.set_attribute("user.id", context.user_id)
                
                # Build contextual prompt with memory
                full_prompt = await self._build_contextual_prompt(
                    prompt, context, span
                )
                
                # Select appropriate model
                model = self._select_model(context)
                span.set_attribute("model.selected", model)
                
                # Create gateway request
                request = GatewayRequest(
                    prompt=full_prompt,
                    user_id=context.user_id,
                    model=model,
                    max_tokens=kwargs.get("max_tokens", 500),
                    temperature=kwargs.get("temperature", 0.7),
                    metadata={
                        "agent": context.agent_name,
                        "task_id": context.task_id,
                        "conversation_id": context.conversation_id,
                        "task_complexity": context.task_complexity
                    }
                )
                
                # Execute through gateway
                start_time = time.time()
                response = await self.gateway.complete(request)
                execution_time = time.time() - start_time
                
                # Record metrics
                span.set_attribute("execution.time_seconds", execution_time)
                span.set_attribute("tokens.prompt", response.prompt_tokens)
                span.set_attribute("tokens.completion", response.completion_tokens)
                span.set_attribute("tokens.total", response.total_tokens)
                span.set_attribute("cost.usd", response.cost)
                
                # Log performance warning if needed
                if execution_time > 2.0:
                    logger.warning(
                        f"Slow response for {context.agent_name}: {execution_time:.2f}s"
                    )
                
                return response.content
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(f"Agent execution failed: {e}")
                raise
    
    async def _build_contextual_prompt(
        self,
        base_prompt: str,
        context: AgentContext,
        span: trace.Span
    ) -> str:
        """
        Build a prompt with relevant memory context.
        
        For the Neuroscientist specialist, this includes:
        - Recent HRV trends
        - Previous recovery recommendations
        - User's baseline metrics
        - Relevant biometric patterns
        """
        with tracer.start_as_current_span("build_contextual_prompt") as prompt_span:
            prompt_parts = []
            
            # Add role context for Neuroscientist
            if context.agent_name.lower() == "neuroscientist":
                prompt_parts.append(
                    "You are a Neuroscientist specialist focused on HRV analysis, "
                    "CNS fatigue assessment, and recovery optimization."
                )
            
            # Add memory context if available
            if context.memory_context:
                prompt_span.set_attribute("memory.items_count", len(context.memory_context))
                
                # Limit memory context to avoid token overflow
                memory_text = "\n".join(context.memory_context[:5])
                prompt_parts.append(f"Relevant context:\n{memory_text}")
            
            # Add biometric data if available
            if context.biometric_data:
                biometric_summary = self._summarize_biometric_data(context.biometric_data)
                prompt_parts.append(f"Current biometric data:\n{biometric_summary}")
            
            # Add the actual prompt
            prompt_parts.append(f"User query: {base_prompt}")
            
            # Add response guidelines
            prompt_parts.append(
                "\nProvide a clear, actionable response based on the data. "
                "Focus on practical recommendations backed by the biometric evidence."
            )
            
            full_prompt = "\n\n".join(prompt_parts)
            prompt_span.set_attribute("prompt.length", len(full_prompt))
            
            return full_prompt
    
    def _select_model(self, context: AgentContext) -> str:
        """
        Select the appropriate model based on task complexity.
        
        For the Neuroscientist MVP:
        - Complex HRV analysis → GPT-4
        - Simple queries → GPT-3.5-turbo
        - Fast responses needed → GPT-3.5-turbo
        """
        # Fast response always uses default model
        if context.require_fast_response:
            return self.default_model
        
        # Complex analysis uses advanced model
        if context.task_complexity == "high":
            return self.complex_model
        
        # Neuroscientist-specific logic
        if context.agent_name.lower() == "neuroscientist":
            # HRV trend analysis is complex
            if context.biometric_data and "hrv_trend" in context.biometric_data:
                hrv_variance = context.biometric_data.get("hrv_variance", 0)
                if hrv_variance > 20:  # High variance needs deeper analysis
                    return self.complex_model
        
        return self.default_model
    
    def _summarize_biometric_data(self, biometric_data: Dict[str, Any]) -> str:
        """
        Summarize biometric data for prompt inclusion.
        
        Focuses on key metrics for the Neuroscientist:
        - HRV values and trends
        - Sleep quality metrics
        - Recovery indicators
        """
        summary_parts = []
        
        # HRV data
        if "hrv_current" in biometric_data:
            summary_parts.append(f"Current HRV: {biometric_data['hrv_current']}ms")
        
        if "hrv_baseline" in biometric_data:
            summary_parts.append(f"Baseline HRV: {biometric_data['hrv_baseline']}ms")
        
        if "hrv_trend" in biometric_data:
            summary_parts.append(f"HRV Trend: {biometric_data['hrv_trend']}")
        
        # Sleep data
        if "sleep_quality" in biometric_data:
            summary_parts.append(f"Sleep Quality: {biometric_data['sleep_quality']}/10")
        
        if "sleep_duration" in biometric_data:
            summary_parts.append(f"Sleep Duration: {biometric_data['sleep_duration']} hours")
        
        # Recovery metrics
        if "recovery_score" in biometric_data:
            summary_parts.append(f"Recovery Score: {biometric_data['recovery_score']}%")
        
        return "\n".join(summary_parts)
    
    # Synchronous wrapper for CrewAI compatibility
    def execute_for_agent_sync(
        self,
        prompt: str,
        context: AgentContext,
        **kwargs
    ) -> str:
        """
        Synchronous wrapper for CrewAI integration.
        
        CrewAI tasks are synchronous, so this wrapper allows
        the adapter to be used in standard CrewAI workflows.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.execute_for_agent(prompt, context, **kwargs)
        )
    
    async def execute_specialist_task(
        self,
        specialist: Any,  # BaseSpecialist instance
        task_description: str,
        user_id: str,
        conversation_id: str,
        biometric_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a task for a specialist with full integration.
        
        This method bridges the BaseSpecialist framework with the gateway,
        handling all the context building and tracking automatically.
        """
        # Build context from specialist
        context = AgentContext(
            agent_name=specialist.identity,
            user_id=user_id,
            task_id=f"task_{int(time.time())}",
            conversation_id=conversation_id,
            memory_context=[],  # Will be populated from memory system
            biometric_data=biometric_data,
            task_complexity=self._assess_task_complexity(task_description)
        )
        
        # Load memory context if available
        if self.memory_profile:
            try:
                # Get relevant memories for this specialist
                memories = await self._load_specialist_memories(
                    specialist.get_domain().value,
                    user_id
                )
                context.memory_context = memories
            except Exception as e:
                logger.warning(f"Failed to load memories: {e}")
        
        # Execute through the adapter
        return await self.execute_for_agent(
            prompt=task_description,
            context=context,
            # Pass through specialist's token limits
            max_tokens=getattr(specialist, "max_response_tokens", 500)
        )
    
    async def _load_specialist_memories(
        self,
        domain: str,
        user_id: str,
        limit: int = 5
    ) -> List[str]:
        """
        Load relevant memories for a specialist domain.
        
        For the Neuroscientist, this includes:
        - Previous HRV analyses
        - Recovery recommendations
        - Identified patterns
        """
        if not self.memory_profile:
            return []
        
        # This would integrate with the memory system
        # For now, return empty list as memory system is pending
        return []
    
    def _assess_task_complexity(self, task_description: str) -> str:
        """
        Assess the complexity of a task based on its description.
        
        Returns: "low", "medium", or "high"
        """
        # Keywords indicating complex analysis
        complex_keywords = [
            "analyze", "trend", "pattern", "correlation",
            "comprehensive", "detailed", "in-depth"
        ]
        
        # Keywords indicating simple queries
        simple_keywords = [
            "what is", "current", "latest", "quick", "brief"
        ]
        
        task_lower = task_description.lower()
        
        # Count keyword matches
        complex_count = sum(1 for kw in complex_keywords if kw in task_lower)
        simple_count = sum(1 for kw in simple_keywords if kw in task_lower)
        
        # Determine complexity
        if complex_count >= 2:
            return "high"
        elif simple_count >= 2:
            return "low"
        else:
            return "medium" 