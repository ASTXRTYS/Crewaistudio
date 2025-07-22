"""
Self-hosted model pricing calculator.

Provides accurate cost calculations for self-hosted models based on
actual infrastructure costs and utilization patterns.
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InfrastructureCosts:
    """Infrastructure cost breakdown for self-hosted models."""
    gpu_cost_per_hour: float
    electricity_cost_per_hour: float
    bandwidth_cost_per_gb: float
    operational_overhead: float  # Multiplier for engineering/monitoring
    utilization_rate: float  # 0.0 to 1.0


class SelfHostedPricingCalculator:
    """
    Calculator for self-hosted model pricing based on actual infrastructure costs.
    
    This calculator provides transparent pricing that reflects real operational
    costs rather than arbitrary API pricing, enabling data-driven decisions
    about when to use self-hosted versus commercial models.
    """
    
    def __init__(self):
        """Initialize pricing calculator with environment-based configuration."""
        self.config = self._load_configuration()
        
    def _load_configuration(self) -> InfrastructureCosts:
        """Load infrastructure costs from environment variables."""
        return InfrastructureCosts(
            gpu_cost_per_hour=float(os.getenv("GPU_COST_PER_HOUR", "2.50")),
            electricity_cost_per_hour=float(os.getenv("ELECTRICITY_COST_PER_HOUR", "0.50")),
            bandwidth_cost_per_gb=float(os.getenv("BANDWIDTH_COST_PER_GB", "0.05")),
            operational_overhead=float(os.getenv("OPERATIONAL_OVERHEAD", "1.3")),
            utilization_rate=float(os.getenv("GPU_UTILIZATION", "0.7"))
        )
        
    def calculate_cost_per_million_tokens(self, model_name: str) -> float:
        """
        Calculate cost per million tokens for a self-hosted model.
        
        Args:
            model_name: Name of the model (used for performance characteristics)
            
        Returns:
            Cost per million tokens in USD
        """
        # Model-specific performance characteristics
        model_performance = self._get_model_performance(model_name)
        
        # Calculate tokens per hour based on model performance
        tokens_per_second = model_performance["tokens_per_second"]
        tokens_per_hour = tokens_per_second * 3600 * self.config.utilization_rate
        
        # Calculate total hourly cost
        hourly_cost = (
            self.config.gpu_cost_per_hour +
            self.config.electricity_cost_per_hour
        ) * self.config.operational_overhead
        
        # Add bandwidth cost (estimated 1GB per 100K tokens)
        bandwidth_cost = (tokens_per_hour / 100_000) * self.config.bandwidth_cost_per_gb
        
        total_hourly_cost = hourly_cost + bandwidth_cost
        
        # Cost per million tokens
        cost_per_million = (total_hourly_cost / tokens_per_hour) * 1_000_000
        
        return max(cost_per_million, 0.10)  # Minimum $0.10 per million tokens
        
    def _get_model_performance(self, model_name: str) -> Dict[str, float]:
        """Get performance characteristics for different models."""
        performance_map = {
            "llama-3.1-70b": {
                "tokens_per_second": 100.0,
                "memory_gb": 140.0,
                "gpu_type": "A100"
            },
            "meditron-70b": {
                "tokens_per_second": 90.0,
                "memory_gb": 140.0,
                "gpu_type": "A100"
            },
            "llama-3.1-8b": {
                "tokens_per_second": 300.0,
                "memory_gb": 16.0,
                "gpu_type": "A100"
            },
            "mistral-7b": {
                "tokens_per_second": 350.0,
                "memory_gb": 14.0,
                "gpu_type": "A100"
            }
        }
        
        # Default fallback for unknown models
        return performance_map.get(model_name, {
            "tokens_per_second": 50.0,
            "memory_gb": 80.0,
            "gpu_type": "A100"
        })
        
    def get_cost_breakdown(self, model_name: str) -> Dict[str, float]:
        """
        Get detailed cost breakdown for transparency.
        
        Returns:
            Dictionary with detailed cost components
        """
        model_performance = self._get_model_performance(model_name)
        tokens_per_hour = model_performance["tokens_per_second"] * 3600 * self.config.utilization_rate
        
        # Calculate components
        gpu_hourly = self.config.gpu_cost_per_hour
        electricity_hourly = self.config.electricity_cost_per_hour
        bandwidth_hourly = (tokens_per_hour / 100_000) * self.config.bandwidth_cost_per_gb
        
        base_hourly = gpu_hourly + electricity_hourly
        total_hourly = base_hourly * self.config.operational_overhead + bandwidth_hourly
        
        cost_per_million = (total_hourly / tokens_per_hour) * 1_000_000
        
        return {
            "gpu_cost_per_hour": gpu_hourly,
            "electricity_cost_per_hour": electricity_hourly,
            "bandwidth_cost_per_hour": bandwidth_hourly,
            "operational_overhead": self.config.operational_overhead,
            "utilization_rate": self.config.utilization_rate,
            "tokens_per_hour": tokens_per_hour,
            "total_hourly_cost": total_hourly,
            "cost_per_million_tokens": cost_per_million,
            "cost_per_1k_input": cost_per_million / 1000,
            "cost_per_1k_output": cost_per_million / 1000
        }
        
    def optimize_utilization(self, target_utilization: float) -> Dict[str, float]:
        """
        Calculate optimal pricing based on target utilization.
        
        Args:
            target_utilization: Desired GPU utilization (0.0 to 1.0)
            
        Returns:
            Optimized pricing at target utilization
        """
        original_utilization = self.config.utilization_rate
        self.config.utilization_rate = target_utilization
        
        # Calculate for all supported models
        optimized_pricing = {}
        
        models = ["llama-3.1-70b", "meditron-70b", "llama-3.1-8b", "mistral-7b"]
        for model in models:
            optimized_pricing[model] = self.calculate_cost_per_million_tokens(model)
            
        # Restore original utilization
        self.config.utilization_rate = original_utilization
        
        return optimized_pricing
        
    def compare_with_commercial(self, model_name: str) -> Dict[str, float]:
        """
        Compare self-hosted costs with commercial alternatives.
        
        Args:
            model_name: Self-hosted model name
            
        Returns:
            Comparison with commercial pricing
        """
        self_hosted_cost = self.calculate_cost_per_million_tokens(model_name)
        
        # Commercial pricing (as of 2024)
        commercial_pricing = {
            "gpt-3.5-turbo": 1.50,  # $1.50 per million tokens
            "gpt-4-turbo": 10.00,   # $10.00 per million tokens
            "gpt-4": 30.00,         # $30.00 per million tokens
            "claude-3-sonnet": 3.00,  # $3.00 per million tokens
            "claude-3-opus": 15.00    # $15.00 per million tokens
        }
        
        comparison = {
            "self_hosted": self_hosted_cost,
            "commercial": commercial_pricing,
            "savings_percentage": {
                provider: ((commercial - self_hosted_cost) / commercial) * 100
                for provider, commercial in commercial_pricing.items()
            }
        }
        
        return comparison
        
    def get_monitoring_metrics(self) -> Dict[str, float]:
        """Get metrics for monitoring infrastructure costs."""
        return {
            "gpu_cost_per_hour": self.config.gpu_cost_per_hour,
            "utilization_rate": self.config.utilization_rate,
            "operational_overhead": self.config.operational_overhead,
            "total_hourly_cost": (
                (self.config.gpu_cost_per_hour + self.config.electricity_cost_per_hour) * 
                self.config.operational_overhead
            )
        }


# Global calculator instance
pricing_calculator = SelfHostedPricingCalculator()
