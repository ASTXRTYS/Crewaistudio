"""
Adaptive circuit breaker with learning capabilities.

This circuit breaker adapts recovery times based on actual failure patterns
rather than using fixed assumptions.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


@dataclass
class FailurePattern:
    """Record of a failure event."""
    timestamp: float
    duration: float
    error_type: str
    recovery_time: float


class AdaptiveCircuitBreaker(CircuitBreaker):
    """
    Circuit breaker that learns from failure patterns.
    
    This breaker adapts recovery timeouts based on actual system behavior,
    becoming more responsive to real failure patterns while avoiding
    unnecessary delays for stable services.
    """
    
    def __init__(self, config: CircuitBreakerConfig, model_name: str):
        super().__init__(config)
        self.model_name = model_name
        self.failure_history: deque[FailurePattern] = deque(maxlen=100)
        self.recovery_history: deque[float] = deque(maxlen=50)
        self.stability_score = 1.0  # 0.0 (unstable) to 1.0 (stable)
        
    def calculate_adaptive_recovery_time(self) -> float:
        """
        Calculate recovery time based on recent failure patterns.
        
        Uses machine learning approach to adapt to actual system behavior:
        - Stable services get longer recovery times (less frequent checks)
        - Unstable services get shorter recovery times (more frequent checks)
        - Recent failures have more weight than older ones
        """
        if len(self.failure_history) < 3:
            # Not enough data, use configured default
            return self.config.recovery_timeout
            
        # Calculate stability score based on recent patterns
        now = time.time()
        recent_failures = [
            f for f in self.failure_history 
            if now - f.timestamp < 3600  # Last hour
        ]
        
        if not recent_failures:
            # No recent failures, service is stable
            self.stability_score = min(1.0, self.stability_score + 0.1)
            return self.config.recovery_timeout * 2.0  # Longer for stable services
            
        # Calculate average recovery time from history
        if self.recovery_history:
            avg_recovery = sum(self.recovery_history) / len(self.recovery_history)
            recent_avg = sum(f.recovery_time for f in recent_failures[-5:]) / len(recent_failures[-5:])
            
            # Weight recent patterns more heavily
            weighted_recovery = (avg_recovery * 0.3) + (recent_avg * 0.7)
            
            # Adjust based on failure frequency
            failure_rate = len(recent_failures) / 60.0  # failures per hour
            
            if failure_rate > 1.0:  # More than 1 failure per hour
                # Service is unstable, reduce recovery time
                self.stability_score = max(0.1, self.stability_score - 0.2)
                return max(10, weighted_recovery * 0.5)  # Minimum 10 seconds
            elif failure_rate > 0.1:  # 1 failure per 10 hours
                # Moderate instability
                self.stability_score = max(0.5, self.stability_score - 0.1)
                return weighted_recovery
            else:
                # Stable service
                self.stability_score = min(1.0, self.stability_score + 0.05)
                return min(weighted_recovery * 1.5, 300)  # Cap at 5 minutes
                
        return self.config.recovery_timeout
        
    def record_failure(self, error_type: str, duration: float):
        """Record a failure event with timing information."""
        failure = FailurePattern(
            timestamp=time.time(),
            duration=duration,
            error_type=error_type,
            recovery_time=self.config.recovery_timeout
        )
        self.failure_history.append(failure)
        
        logger.info(
            f"Recorded failure for {self.model_name}: "
            f"type={error_type}, duration={duration:.2f}s"
        )
        
    def record_recovery(self, actual_recovery_time: float):
        """Record the actual time it took for service to recover."""
        self.recovery_history.append(actual_recovery_time)
        
        # Update the last failure pattern with actual recovery time
        if self.failure_history:
            self.failure_history[-1].recovery_time = actual_recovery_time
            
        logger.info(
            f"Recorded recovery for {self.model_name}: "
            f"actual_time={actual_recovery_time:.2f}s"
        )
        
    def get_stability_insights(self) -> Dict[str, Any]:
        """Get insights about service stability."""
        now = time.time()
        
        # Recent failure analysis
        recent_failures = [
            f for f in self.failure_history 
            if now - f.timestamp < 3600
        ]
        
        failure_types = {}
        for failure in recent_failures:
            failure_types[failure.error_type] = failure_types.get(failure.error_type, 0) + 1
            
        return {
            "stability_score": self.stability_score,
            "recent_failures": len(recent_failures),
            "failure_types": failure_types,
            "average_recovery_time": (
                sum(self.recovery_history) / len(self.recovery_history)
                if self.recovery_history else None
            ),
            "current_recovery_timeout": self.calculate_adaptive_recovery_time(),
            "failure_rate_per_hour": len(recent_failures) / 60.0
        }
        
    def should_attempt_recovery(self) -> bool:
        """
        Determine if we should attempt recovery based on stability patterns.
        
        Uses stability score to make intelligent decisions about when to
        attempt recovery, reducing unnecessary health checks for stable services.
        """
        if self.stats["state"] != "open":
            return True
            
        # For stable services, wait longer before checking
        if self.stability_score > 0.8:
            return time.time() - self.stats["last_failure_time"] > 60
            
        # For unstable services, check more frequently
        return time.time() - self.stats["last_failure_time"] > 10
        
    def reset(self):
        """Reset the circuit breaker and clear learning data."""
        super().reset()
        self.failure_history.clear()
        self.recovery_history.clear()
        self.stability_score = 1.0
        logger.info(f"Reset adaptive circuit breaker for {self.model_name}")


class AdaptiveCircuitBreakerManager:
    """
    Manager for multiple adaptive circuit breakers.
    
    Provides centralized monitoring and management of all adaptive breakers
    in the system.
    """
    
    def __init__(self):
        self.breakers: Dict[str, AdaptiveCircuitBreaker] = {}
        
    def register_breaker(self, breaker: AdaptiveCircuitBreaker):
        """Register a new adaptive circuit breaker."""
        self.breakers[breaker.model_name] = breaker
        
    def get_system_insights(self) -> Dict[str, Any]:
        """Get insights about the entire circuit breaker system."""
        insights = {
            "total_breakers": len(self.breakers),
            "breakers": {},
            "system_stability": 0.0
        }
        
        total_stability = 0.0
        
        for name, breaker in self.breakers.items():
            breaker_insights = breaker.get_stability_insights()
            insights["breakers"][name] = breaker_insights
            total_stability += breaker_insights["stability_score"]
            
        insights["system_stability"] = (
            total_stability / len(self.breakers) if self.breakers else 0.0
        )
        
        return insights
        
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on system patterns."""
        recommendations = []
        
        for name, breaker in self.breakers.items():
            insights = breaker.get_stability_insights()
            
            if insights["stability_score"] < 0.3:
                recommendations.append(
                    f"Consider investigating {name} - high failure rate detected"
                )
            elif insights["failure_rate_per_hour"] > 2.0:
                recommendations.append(
                    f"Monitor {name} closely - frequent failures"
                )
            elif insights["stability_score"] > 0.9 and insights["recent_failures"] == 0:
                recommendations.append(
                    f"{name} is very stable - consider longer recovery timeouts"
                )
                
        return recommendations


# Global manager instance
adaptive_manager = AdaptiveCircuitBreakerManager()
