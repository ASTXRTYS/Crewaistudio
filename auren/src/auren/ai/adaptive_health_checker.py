"""
Adaptive health checking with intelligent frequency adjustment.

Adjusts health check frequency based on service stability patterns,
reducing unnecessary checks for stable services while maintaining
quick detection for unstable ones.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    healthy: bool
    response_time: float
    timestamp: datetime
    error: Optional[str] = None


class AdaptiveHealthChecker:
    """
    Health checker that adapts check frequency based on service stability.
    
    This checker learns from service behavior to optimize:
    - Check frequency (stable services get longer intervals)
    - Response time thresholds (based on historical performance)
    - Error tolerance (adapts to service characteristics)
    """
    
    def __init__(
        self,
        check_function: Callable[[], Awaitable[bool]],
        name: str,
        min_interval: int = 10,      # Minimum 10 seconds
        max_interval: int = 300,     # Maximum 5 minutes
        initial_interval: int = 30      # Start with 30 seconds
    ):
        """
        Initialize adaptive health checker.
        
        Args:
            check_function: Async function that returns health status
            name: Name of the service being checked
            min_interval: Minimum seconds between checks
            max_interval: Maximum seconds between checks
            initial_interval: Starting interval
        """
        self.check_function = check_function
        self.name = name
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.current_interval = initial_interval
        
        self.check_history: deque[HealthCheckResult] = deque(maxlen=50)
        self.stability_score = 1.0  # 0.0 (unstable) to 1.0 (stable)
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def check_health(self) -> HealthCheckResult:
        """Perform a single health check."""
        start_time = time.time()
        
        try:
            healthy = await self.check_function()
            response_time = time.time() - start_time
            
            result = HealthCheckResult(
                healthy=healthy,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
            self.check_history.append(result)
            self._update_stability_score(result)
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            result = HealthCheckResult(
                healthy=False,
                response_time=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
            
            self.check_history.append(result)
            self._update_stability_score(result)
            
            return result
            
    def _update_stability_score(self, result: HealthCheckResult):
        """Update stability score based on check result."""
        if result.healthy:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            
            # Increase stability for successful checks
            self.stability_score = min(1.0, self.stability_score + 0.1)
            
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
            # Decrease stability for failures
            self.stability_score = max(0.0, self.stability_score - 0.2)
            
    def calculate_next_interval(self) -> int:
        """
        Calculate next check interval based on stability patterns.
        
        Uses multiple factors:
        - Stability score (stable services get longer intervals)
        - Response time trends (slower services get more frequent checks)
        - Recent failure patterns (recent failures trigger more checks)
        """
        if not self.check_history:
            return self.current_interval
            
        # Base adjustment on stability score
        base_interval = self.min_interval + (
            (self.max_interval - self.min_interval) * self.stability_score
        )
        
        # Adjust based on response time trends
        recent_checks = list(self.check_history)[-10:]
        if recent_checks:
            avg_response_time = sum(
                check.response_time for check in recent_checks
            ) / len(recent_checks)
            
            # Faster response times allow longer intervals
            response_factor = min(1.0, 1.0 / (avg_response_time + 0.1))
            base_interval *= response_factor
            
        # Adjust based on recent failures
        if self.consecutive_failures > 0:
            # Reduce interval for consecutive failures
            failure_factor = max(0.1, 1.0 / (self.consecutive_failures + 1))
            base_interval *= failure_factor
            
        # Ensure bounds
        next_interval = max(self.min_interval, min(self.max_interval, int(base_interval)))
        
        # Smooth transitions to avoid oscillation
        change_limit = max(5, int(self.current_interval * 0.5))
        next_interval = max(
            self.current_interval - change_limit,
            min(self.current_interval + change_limit, next_interval)
        )
        
        self.current_interval = next_interval
        return next_interval
        
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started adaptive monitoring for {self.name}")
        
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped adaptive monitoring for {self.name}")
        
    async def _monitor_loop(self):
        """Main monitoring loop with adaptive intervals."""
        while self._running:
            try:
                result = await self.check_health()
                
                if result.healthy:
                    logger.debug(
                        f"{self.name} health check passed "
                        f"({result.response_time:.2f}s)"
                    )
                else:
                    logger.warning(
                        f"{self.name} health check failed: {result.error} "
                        f"({result.response_time:.2f}s)"
                    )
                    
                # Calculate next interval
                next_interval = self.calculate_next_interval()
                
                logger.debug(
                    f"{self.name} next check in {next_interval}s "
                    f"(stability: {self.stability_score:.2f})"
                )
                
                await asyncio.sleep(next_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for {self.name}: {e}")
                await asyncio.sleep(self.min_interval)
                
    def get_health_insights(self) -> Dict[str, Any]:
        """Get insights about service health patterns."""
        if not self.check_history:
            return {
                "name": self.name,
                "status": "no_data",
                "stability_score": self.stability_score,
                "current_interval": self.current_interval
            }
            
        recent_checks = list(self.check_history)[-10:]
        healthy_checks = [c for c in recent_checks if c.healthy]
        
        return {
            "name": self.name,
            "status": "healthy" if self.stability_score > 0.7 else "unstable",
            "stability_score": self.stability_score,
            "current_interval": self.current_interval,
            "total_checks": len(self.check_history),
            "healthy_ratio": len(healthy_checks) / len(recent_checks) if recent_checks else 0,
            "average_response_time": sum(
                c.response_time for c in recent_checks
            ) / len(recent_checks) if recent_checks else 0,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_check": self.check_history[-1].timestamp.isoformat() if self.check_history else None
        }


class AdaptiveHealthManager:
    """
    Manager for multiple adaptive health checkers.
    
    Provides centralized management and monitoring of all health checkers
    in the system.
    """
    
    def __init__(self):
        self.checkers: Dict[str, AdaptiveHealthChecker] = {}
        
    def register_checker(self, checker: AdaptiveHealthChecker):
        """Register a new health checker."""
        self.checkers[checker.name] = checker
        
    async def start_all(self):
        """Start monitoring for all registered checkers."""
        for checker in self.checkers.values():
            await checker.start_monitoring()
            
    async def stop_all(self):
        """Stop monitoring for all registered checkers."""
        for checker in self.checkers.values():
            await checker.stop_monitoring()
            
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health overview."""
        health_data = {
            "total_checkers": len(self.checkers),
            "checkers": {},
            "system_stability": 0.0,
            "recommendations": []
        }
        
        total_stability = 0.0
        
        for name, checker in self.checkers.items():
            insights = checker.get_health_insights()
            health_data["checkers"][name] = insights
            total_stability += insights["stability_score"]
            
            # Generate recommendations
            if insights["stability_score"] < 0.3:
                health_data["recommendations"].append(
                    f"Critical: {name} is unstable - investigate immediately"
                )
            elif insights["stability_score"] < 0.7:
                health_data["recommendations"].append(
                    f"Warning: {name} showing instability - monitor closely"
                )
            elif insights["consecutive_failures"] > 5:
                health_data["recommendations"].append(
                    f"Alert: {name} has {insights['consecutive_failures']} consecutive failures"
                )
                
        health_data["system_stability"] = (
            total_stability / len(self.checkers) if self.checkers else 0.0
        )
        
        return health_data
        
    async def check_all_now(self) -> Dict[str, HealthCheckResult]:
        """Force immediate health check for all services."""
        results = {}
        
        for name, checker in self.checkers.items():
            results[name] = await checker.check_health()
            
        return results


# Global manager instance
health_manager = AdaptiveHealthManager()
