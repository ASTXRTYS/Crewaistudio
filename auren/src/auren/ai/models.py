"""
Model configurations and intelligent selection logic for the AUREN AI Gateway.

This module defines the available models, their characteristics, and the
logic for selecting the optimal model based on query complexity, budget,
and availability.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Classification of query complexity for model selection."""
    SIMPLE = "simple"        # Basic queries, low token count
    MODERATE = "moderate"    # Standard queries, medium complexity
    COMPLEX = "complex"      # Complex analysis, high token requirements
    CRITICAL = "critical"    # Critical decisions requiring best model


@dataclass
class ModelConfig:
    """
    Configuration for a specific LLM model.
    
    Contains pricing, capabilities, and selection criteria for each model.
    """
    name: str
    provider: str
    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    max_tokens: int
    supports_streaming: bool = True
    quality_tier: str = "medium"  # low, medium, high, premium
    speed_tier: str = "medium"    # slow, medium, fast
    description: str = ""
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate the cost for a given token usage."""
        input_cost = (prompt_tokens / 1000) * self.input_cost_per_1k
        output_cost = (completion_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "provider": self.provider,
            "input_cost_per_1k": self.input_cost_per_1k,
            "output_cost_per_1k": self.output_cost_per_1k,
            "max_tokens": self.max_tokens,
            "supports_streaming": self.supports_streaming,
            "quality_tier": self.quality_tier,
            "speed_tier": self.speed_tier,
            "description": self.description
        }


class ModelSelector:
    """
    Intelligent model selection based on query complexity, budget, and availability.
    
    This class implements the core logic for choosing which model to use
    for a given query, considering:
    - User's remaining budget
    - Query complexity and requirements
    - Model availability and health
    - Cost optimization strategies
    """
    
    def __init__(self):
        """Initialize the model selector with available models."""
        self.models = self._load_model_configs()
        
    def _load_model_configs(self) -> Dict[str, ModelConfig]:
        """Load model configurations from environment or defaults."""
        # Try to load from environment variable
        pricing_json = os.getenv("MODEL_PRICING_CONFIG")
        
        if pricing_json:
            try:
                pricing_data = json.loads(pricing_json)
                return {
                    name: ModelConfig(name=name, **config)
                    for name, config in pricing_data.items()
                }
            except json.JSONDecodeError:
                logger.warning("Invalid MODEL_PRICING_CONFIG, using defaults")
        
        # Default model configurations
        return {
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                provider="openai",
                input_cost_per_1k=1.50,
                output_cost_per_1k=2.00,
                max_tokens=4096,
                quality_tier="medium",
                speed_tier="fast",
                description="Fast, cost-effective general purpose model"
            ),
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                provider="openai",
                input_cost_per_1k=10.00,
                output_cost_per_1k=30.00,
                max_tokens=4096,
                quality_tier="high",
                speed_tier="medium",
                description="High-quality reasoning and analysis"
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider="openai",
                input_cost_per_1k=30.00,
                output_cost_per_1k=60.00,
                max_tokens=8192,
                quality_tier="premium",
                speed_tier="slow",
                description="Best quality for complex reasoning"
            ),
            "llama-3.1-70b": ModelConfig(
                name="llama-3.1-70b",
                provider="self_hosted",
                input_cost_per_1k=0.50,
                output_cost_per_1k=0.50,
                max_tokens=4096,
                quality_tier="high",
                speed_tier="medium",
                description="Self-hosted Llama 3.1 70B for cost optimization"
            ),
            "meditron-70b": ModelConfig(
                name="meditron-70b",
                provider="self_hosted",
                input_cost_per_1k=0.50,
                output_cost_per_1k=0.50,
                max_tokens=4096,
                quality_tier="high",
                speed_tier="medium",
                description="Medical domain specialist model"
            )
        }
    
    def analyze_complexity(self, prompt: str) -> QueryComplexity:
        """
        Analyze the complexity of a prompt to determine appropriate model tier.
        
        Uses simple heuristics based on:
        - Prompt length
        - Technical terminology
        - Multi-step reasoning indicators
        """
        prompt_lower = prompt.lower()
        
        # Length-based complexity
        token_count = len(prompt.split())
        
        # Technical indicators
        technical_indicators = [
            "analyze", "correlation", "optimize", "algorithm", "protocol",
            "biometric", "inflammation", "ptosis", "cortisol", "hormone",
            "metabolic", "neurotransmitter", "autonomic", "vagus"
        ]
        
        tech_count = sum(1 for indicator in technical_indicators if indicator in prompt_lower)
        
        # Multi-step indicators
        multi_step_indicators = [
            "then", "after", "next", "finally", "step", "phase", "stage"
        ]
        
        step_count = sum(1 for indicator in multi_step_indicators if indicator in prompt_lower)
        
        # Complexity scoring
        complexity_score = 0
        
        # Length contribution
        if token_count > 200:
            complexity_score += 2
        elif token_count > 100:
            complexity_score += 1
            
        # Technical complexity
        complexity_score += min(tech_count, 3)
        
        # Multi-step complexity
        complexity_score += min(step_count, 2)
        
        # Determine complexity level
        if complexity_score >= 5:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 3:
            return QueryComplexity.MODERATE
        elif complexity_score >= 1:
            return QueryComplexity.SIMPLE
        else:
            return QueryComplexity.SIMPLE
    
    def select_model(
        self,
        prompt: str,
        remaining_budget: float,
        available_models: List[str],
        prefer_fast: bool = False
    ) -> Optional[str]:
        """
        Select the optimal model based on budget, complexity, and availability.
        
        Args:
            prompt: The input prompt
            remaining_budget: User's remaining daily budget
            available_models: List of healthy, available models
            prefer_fast: Whether to prioritize speed over quality
            
        Returns:
            Selected model name or None if no suitable model
        """
        if not available_models:
            return None
            
        complexity = self.analyze_complexity(prompt)
        
        # Budget thresholds for routing decisions
        budget_thresholds = {
            "low": 0.3,      # Below 30% - economy only
            "medium": 0.7,   # Below 70% - no premium
            "high": 1.0      # Above 70% - all models available
        }
        
        # Determine budget tier
        if remaining_budget < 0.5:  # Less than $0.50
            budget_tier = "low"
        elif remaining_budget < 2.0:  # Less than $2.00
            budget_tier = "medium"
        else:
            budget_tier = "high"
        
        # Filter models by availability
        candidate_models = [
            self.models[name] for name in available_models
            if name in self.models
        ]
        
        if not candidate_models:
            return None
            
        # Sort by priority based on complexity and budget
        def model_priority(model: ModelConfig) -> tuple:
            # Priority scoring
            score = 0
            
            # Budget compatibility
            if budget_tier == "low" and model.quality_tier in ["low", "medium"]:
                score += 3
            elif budget_tier == "medium" and model.quality_tier in ["medium", "high"]:
                score += 2
            elif budget_tier == "high":
                score += 1
                
            # Complexity matching
            if complexity == QueryComplexity.SIMPLE and model.quality_tier in ["low", "medium"]:
                score += 2
            elif complexity == QueryComplexity.MODERATE and model.quality_tier in ["medium", "high"]:
                score += 2
            elif complexity == QueryComplexity.COMPLEX and model.quality_tier in ["high", "premium"]:
                score += 2
                
            # Speed preference
            if prefer_fast and model.speed_tier == "fast":
                score += 1
                
            # Cost efficiency (lower cost = higher priority)
            cost_factor = 1.0 / (model.input_cost_per_1k + model.output_cost_per_1k)
            
            return (-score, -cost_factor)  # Higher score first, then lower cost
            
        # Sort candidates by priority
        candidate_models.sort(key=model_priority)
        
        # Return the best available model
        return candidate_models[0].name if candidate_models else None
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.models.get(model_name)
    
    def get_all_models(self) -> Dict[str, ModelConfig]:
        """Get all available model configurations."""
        return self.models.copy()
    
    def get_models_by_provider(self, provider: str) -> List[str]:
        """Get all models for a specific provider."""
        return [
            name for name, config in self.models.items()
            if config.provider == provider
        ]
