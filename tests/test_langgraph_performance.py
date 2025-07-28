"""
LangGraph Performance Tests
Created: 2025-01-29
Purpose: Ensure LangGraph flows meet performance targets
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import pytest
import aiohttp
from faker import Faker

# Performance target configuration
LATENCY_TARGET_P95_MS = 500  # 500ms p95 latency target
LATENCY_TARGET_P99_MS = 1000  # 1s p99 latency target
THROUGHPUT_TARGET_RPS = 100  # 100 requests per second target
CONCURRENT_USERS = 50  # Simulate 50 concurrent users


@dataclass
class PerformanceResult:
    """Container for performance test results"""
    request_count: int
    success_count: int
    error_count: int
    latencies_ms: List[float]
    errors: List[str]
    duration_seconds: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.request_count == 0:
            return 0.0
        return (self.success_count / self.request_count) * 100
    
    @property
    def throughput_rps(self) -> float:
        """Calculate requests per second"""
        if self.duration_seconds == 0:
            return 0.0
        return self.request_count / self.duration_seconds
    
    @property
    def p50_latency_ms(self) -> float:
        """Get 50th percentile latency"""
        if not self.latencies_ms:
            return 0.0
        return statistics.quantiles(self.latencies_ms, n=100)[49]
    
    @property
    def p95_latency_ms(self) -> float:
        """Get 95th percentile latency"""
        if not self.latencies_ms:
            return 0.0
        return statistics.quantiles(self.latencies_ms, n=100)[94]
    
    @property
    def p99_latency_ms(self) -> float:
        """Get 99th percentile latency"""
        if not self.latencies_ms:
            return 0.0
        return statistics.quantiles(self.latencies_ms, n=100)[98]
    
    def print_summary(self):
        """Print performance summary"""
        print(f"\n{'='*60}")
        print("PERFORMANCE TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Requests: {self.request_count}")
        print(f"Success Rate: {self.success_rate:.2f}%")
        print(f"Throughput: {self.throughput_rps:.2f} RPS")
        print(f"\nLatency Percentiles:")
        print(f"  P50: {self.p50_latency_ms:.2f}ms")
        print(f"  P95: {self.p95_latency_ms:.2f}ms {'✅' if self.p95_latency_ms <= LATENCY_TARGET_P95_MS else '❌'}")
        print(f"  P99: {self.p99_latency_ms:.2f}ms {'✅' if self.p99_latency_ms <= LATENCY_TARGET_P99_MS else '❌'}")
        print(f"\nDuration: {self.duration_seconds:.2f}s")
        print(f"{'='*60}\n")


class LangGraphPerformanceTester:
    """Performance testing harness for LangGraph flows"""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.faker = Faker()
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, payload: dict) -> tuple[float, bool, str]:
        """
        Make a single request and measure latency
        
        Returns:
            Tuple of (latency_ms, success, error_message)
        """
        start_time = time.time()
        error_msg = ""
        success = False
        
        try:
            async with session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                await response.json()
                success = response.status == 200
                if not success:
                    error_msg = f"HTTP {response.status}"
        except asyncio.TimeoutError:
            error_msg = "Timeout"
        except Exception as e:
            error_msg = str(e)
        
        latency_ms = (time.time() - start_time) * 1000
        return latency_ms, success, error_msg
    
    def generate_biometric_payload(self) -> dict:
        """Generate realistic biometric event payload"""
        device_types = ["oura", "whoop", "apple_health"]
        
        return {
            "user_id": f"user_{self.faker.random_int(1, 1000)}",
            "event_id": self.faker.uuid4(),
            "device_type": self.faker.random_element(device_types),
            "timestamp": self.faker.date_time_this_month().isoformat(),
            "raw_data": {
                "hrv_rmssd": self.faker.random_int(20, 80),
                "heart_rate": self.faker.random_int(50, 120),
                "readiness_score": self.faker.random_int(40, 100),
                "sleep_score": self.faker.random_int(50, 95),
                "steps": self.faker.random_int(1000, 20000),
                "temperature_deviation": round(self.faker.random.uniform(-1.5, 1.5), 2)
            }
        }
    
    async def run_load_test(
        self, 
        endpoint: str,
        duration_seconds: int = 30,
        concurrent_users: int = CONCURRENT_USERS
    ) -> PerformanceResult:
        """
        Run load test against endpoint
        
        Args:
            endpoint: API endpoint to test
            duration_seconds: How long to run the test
            concurrent_users: Number of concurrent users to simulate
            
        Returns:
            PerformanceResult with metrics
        """
        print(f"\n🚀 Starting load test: {endpoint}")
        print(f"   Duration: {duration_seconds}s")
        print(f"   Concurrent users: {concurrent_users}")
        
        latencies = []
        errors = []
        success_count = 0
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            while time.time() - start_time < duration_seconds:
                # Create batch of concurrent requests
                batch_tasks = []
                for _ in range(concurrent_users):
                    payload = self.generate_biometric_payload()
                    task = self.make_request(session, endpoint, payload)
                    batch_tasks.append(task)
                
                # Execute batch
                results = await asyncio.gather(*batch_tasks)
                
                # Process results
                for latency, success, error in results:
                    latencies.append(latency)
                    if success:
                        success_count += 1
                    else:
                        errors.append(error)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
        
        duration = time.time() - start_time
        
        return PerformanceResult(
            request_count=len(latencies),
            success_count=success_count,
            error_count=len(errors),
            latencies_ms=latencies,
            errors=errors,
            duration_seconds=duration
        )
    
    async def run_spike_test(self, endpoint: str, spike_multiplier: int = 3) -> PerformanceResult:
        """Test system behavior under sudden load spike"""
        print(f"\n⚡ Starting spike test: {endpoint}")
        print(f"   Spike multiplier: {spike_multiplier}x")
        
        # Normal load for 10 seconds
        normal_result = await self.run_load_test(endpoint, 10, CONCURRENT_USERS)
        
        # Spike load for 10 seconds
        spike_result = await self.run_load_test(
            endpoint, 
            10, 
            CONCURRENT_USERS * spike_multiplier
        )
        
        # Return to normal for 10 seconds
        recovery_result = await self.run_load_test(endpoint, 10, CONCURRENT_USERS)
        
        print(f"\n📊 Spike Test Results:")
        print(f"Normal P95: {normal_result.p95_latency_ms:.2f}ms")
        print(f"Spike P95: {spike_result.p95_latency_ms:.2f}ms")
        print(f"Recovery P95: {recovery_result.p95_latency_ms:.2f}ms")
        
        return spike_result


class TestLangGraphPerformance:
    """Performance test suite"""
    
    @pytest.fixture
    def tester(self):
        """Create performance tester instance"""
        return LangGraphPerformanceTester()
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_biometric_webhook_performance(self, tester):
        """Test biometric webhook endpoint performance"""
        result = await tester.run_load_test(
            "/webhooks/biometric",
            duration_seconds=30
        )
        
        result.print_summary()
        
        # Assert performance targets
        assert result.p95_latency_ms <= LATENCY_TARGET_P95_MS, \
            f"P95 latency {result.p95_latency_ms}ms exceeds target {LATENCY_TARGET_P95_MS}ms"
        
        assert result.p99_latency_ms <= LATENCY_TARGET_P99_MS, \
            f"P99 latency {result.p99_latency_ms}ms exceeds target {LATENCY_TARGET_P99_MS}ms"
        
        assert result.success_rate >= 99.0, \
            f"Success rate {result.success_rate}% below 99% target"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_analysis_endpoint_performance(self, tester):
        """Test analysis endpoint performance"""
        # Modify endpoint for analysis
        tester.base_url = "http://localhost:8888"
        
        result = await tester.run_load_test(
            "/analyze",
            duration_seconds=20,
            concurrent_users=25  # Lower concurrency for heavier endpoint
        )
        
        result.print_summary()
        
        # Analysis might have higher latency targets
        assert result.p95_latency_ms <= 1000, "Analysis P95 exceeds 1s"
        assert result.p99_latency_ms <= 2000, "Analysis P99 exceeds 2s"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_spike_handling(self, tester):
        """Test system behavior under load spikes"""
        result = await tester.run_spike_test("/webhooks/biometric")
        
        # System should handle 3x spike without crashing
        assert result.success_rate >= 95.0, \
            f"Success rate {result.success_rate}% too low during spike"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_graph_execution(self, tester):
        """Test multiple graphs executing concurrently"""
        # This would test the actual graph execution
        # For now, we test the API endpoint
        
        endpoints = [
            "/webhooks/oura",
            "/webhooks/whoop", 
            "/webhooks/apple_health"
        ]
        
        tasks = []
        for endpoint in endpoints:
            task = tester.run_load_test(endpoint, 10, 20)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(results):
            print(f"\nEndpoint {endpoints[i]}:")
            result.print_summary()
            assert result.p95_latency_ms <= LATENCY_TARGET_P95_MS


if __name__ == "__main__":
    # Run performance tests directly
    async def main():
        tester = LangGraphPerformanceTester()
        
        # Run basic load test
        result = await tester.run_load_test(
            "/webhooks/biometric",
            duration_seconds=30
        )
        result.print_summary()
        
        # Run spike test
        spike_result = await tester.run_spike_test("/webhooks/biometric")
    
    asyncio.run(main()) 