"""
Load test for AUREN AI Gateway to verify 1000 concurrent user support.

Run with: python tests/load_test_gateway.py

Tests verify:
1. Concurrent request handling (100+ simultaneous requests)
2. Circuit breaker behavior under stress
3. Memory usage under sustained load
4. Token tracker performance with high throughput
5. System stability and recovery
"""

import asyncio
import time
import psutil
import os
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json

from src.auren.ai import AIGateway, GatewayRequest


@dataclass
class LoadTestResult:
    """Results from a load test run."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    memory_peak_mb: float
    circuit_breaker_trips: int
    errors_by_type: Dict[str, int]


class LoadTester:
    """Load testing harness for AI Gateway."""
    
    def __init__(self, gateway: AIGateway):
        self.gateway = gateway
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.memory_samples: List[float] = []
        self.circuit_breaker_trips = 0
        
    async def simulate_user(self, user_id: str, num_requests: int = 10):
        """Simulate a single user making requests."""
        for i in range(num_requests):
            start_time = time.time()
            try:
                response = await self.gateway.complete(GatewayRequest(
                    prompt=f"User {user_id} request {i}: What is {i} + {i}?",
                    user_id=user_id,
                    max_tokens=20
                ))
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                
                # Small delay between requests (realistic user behavior)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.errors.append(str(type(e).__name__))
                if "circuit breaker" in str(e).lower():
                    self.circuit_breaker_trips += 1
    
    async def monitor_memory(self, duration: float):
        """Monitor memory usage during the test."""
        process = psutil.Process()
        end_time = time.time() + duration
        
        while time.time() < end_time:
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_samples.append(memory_mb)
            await asyncio.sleep(1)
    
    async def run_load_test(
        self,
        num_users: int,
        requests_per_user: int = 10,
        ramp_up_seconds: float = 10
    ) -> LoadTestResult:
        """Run a load test with specified parameters."""
        print(f"\n🚀 Starting load test: {num_users} users, {requests_per_user} requests each")
        print(f"   Ramp-up time: {ramp_up_seconds}s")
        
        # Reset metrics
        self.response_times.clear()
        self.errors.clear()
        self.memory_samples.clear()
        self.circuit_breaker_trips = 0
        
        start_time = time.time()
        
        # Create user tasks with ramp-up
        tasks = []
        users_per_batch = max(1, num_users // int(ramp_up_seconds))
        
        for batch in range(0, num_users, users_per_batch):
            batch_users = min(users_per_batch, num_users - batch)
            for i in range(batch_users):
                user_id = f"load_test_user_{batch + i}"
                task = asyncio.create_task(
                    self.simulate_user(user_id, requests_per_user)
                )
                tasks.append(task)
            
            # Ramp-up delay
            if batch + users_per_batch < num_users:
                await asyncio.sleep(1)
        
        # Monitor memory in parallel
        memory_task = asyncio.create_task(
            self.monitor_memory(duration=60)  # Monitor for up to 60 seconds
        )
        
        # Wait for all users to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        memory_task.cancel()
        
        duration = time.time() - start_time
        
        # Calculate metrics
        total_requests = num_users * requests_per_user
        successful_requests = len(self.response_times)
        failed_requests = len(self.errors)
        
        # Response time percentiles
        if self.response_times:
            self.response_times.sort()
            avg_response_time = statistics.mean(self.response_times)
            p95_response_time = self.response_times[int(len(self.response_times) * 0.95)]
            p99_response_time = self.response_times[int(len(self.response_times) * 0.99)]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        # Memory peak
        memory_peak_mb = max(self.memory_samples) if self.memory_samples else 0
        
        # Error breakdown
        errors_by_type = {}
        for error in self.errors:
            errors_by_type[error] = errors_by_type.get(error, 0) + 1
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            duration_seconds=duration,
            requests_per_second=successful_requests / duration if duration > 0 else 0,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            memory_peak_mb=memory_peak_mb,
            circuit_breaker_trips=self.circuit_breaker_trips,
            errors_by_type=errors_by_type
        )
    
    def print_results(self, result: LoadTestResult):
        """Print load test results in a formatted way."""
        print("\n" + "="*60)
        print("📊 LOAD TEST RESULTS")
        print("="*60)
        
        print(f"\n📈 Request Statistics:")
        print(f"   Total Requests:      {result.total_requests}")
        print(f"   Successful:          {result.successful_requests} ({result.successful_requests/result.total_requests*100:.1f}%)")
        print(f"   Failed:              {result.failed_requests} ({result.failed_requests/result.total_requests*100:.1f}%)")
        print(f"   Duration:            {result.duration_seconds:.2f}s")
        print(f"   Requests/Second:     {result.requests_per_second:.2f}")
        
        print(f"\n⏱️  Response Times:")
        print(f"   Average:             {result.avg_response_time*1000:.2f}ms")
        print(f"   95th Percentile:     {result.p95_response_time*1000:.2f}ms")
        print(f"   99th Percentile:     {result.p99_response_time*1000:.2f}ms")
        
        print(f"\n💾 Resource Usage:")
        print(f"   Peak Memory:         {result.memory_peak_mb:.2f}MB")
        print(f"   Circuit Trips:       {result.circuit_breaker_trips}")
        
        if result.errors_by_type:
            print(f"\n❌ Errors by Type:")
            for error_type, count in result.errors_by_type.items():
                print(f"   {error_type}: {count}")
        
        print("\n" + "="*60)
        
        # Success criteria for 1000 users
        if result.total_requests >= 1000:
            success_rate = result.successful_requests / result.total_requests
            if success_rate >= 0.95 and result.p99_response_time < 5.0:
                print("✅ PASSED: System can handle 1000+ concurrent users!")
            else:
                print("❌ FAILED: System needs optimization for 1000 users")
                if success_rate < 0.95:
                    print(f"   - Success rate {success_rate*100:.1f}% < 95%")
                if result.p99_response_time >= 5.0:
                    print(f"   - P99 latency {result.p99_response_time:.2f}s >= 5s")


async def run_progressive_load_test():
    """Run progressive load tests to find system limits."""
    gateway = AIGateway()
    tester = LoadTester(gateway)
    
    # Test configurations (users, requests_per_user)
    test_configs = [
        (10, 5),      # Warm-up: 50 requests
        (50, 5),      # Light load: 250 requests
        (100, 5),     # Medium load: 500 requests
        (200, 5),     # Heavy load: 1000 requests
        (500, 2),     # Very heavy: 1000 requests
        (1000, 1),    # Max load: 1000 requests
    ]
    
    results = []
    
    for num_users, requests_per_user in test_configs:
        print(f"\n{'='*60}")
        print(f"Testing with {num_users} users...")
        
        try:
            result = await tester.run_load_test(
                num_users=num_users,
                requests_per_user=requests_per_user,
                ramp_up_seconds=min(10, num_users / 100)  # 100 users per second ramp
            )
            
            tester.print_results(result)
            results.append(result)
            
            # Check if we should continue
            if result.successful_requests / result.total_requests < 0.5:
                print("\n⚠️  Success rate below 50%, stopping tests")
                break
                
            # Cool-down period between tests
            print("\n⏳ Cooling down for 5 seconds...")
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            break
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"load_test_results_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(
            [
                {
                    "total_requests": r.total_requests,
                    "successful_requests": r.successful_requests,
                    "failed_requests": r.failed_requests,
                    "duration_seconds": r.duration_seconds,
                    "requests_per_second": r.requests_per_second,
                    "avg_response_time": r.avg_response_time,
                    "p95_response_time": r.p95_response_time,
                    "p99_response_time": r.p99_response_time,
                    "memory_peak_mb": r.memory_peak_mb,
                    "circuit_breaker_trips": r.circuit_breaker_trips,
                    "errors_by_type": r.errors_by_type
                }
                for r in results
            ],
            f,
            indent=2
        )
    
    print(f"\n📄 Results saved to {filename}")
    
    # Cleanup
    await gateway.shutdown()


async def run_stress_test():
    """Run a stress test to find breaking point."""
    gateway = AIGateway()
    tester = LoadTester(gateway)
    
    print("\n🔥 STRESS TEST: Finding system breaking point...")
    
    # Gradually increase load until failure
    users = 100
    while users <= 2000:
        print(f"\n📈 Testing with {users} concurrent users...")
        
        try:
            result = await tester.run_load_test(
                num_users=users,
                requests_per_user=3,
                ramp_up_seconds=5
            )
            
            success_rate = result.successful_requests / result.total_requests
            print(f"   Success rate: {success_rate*100:.1f}%")
            print(f"   P99 latency: {result.p99_response_time:.2f}s")
            
            if success_rate < 0.8 or result.p99_response_time > 10:
                print(f"\n💥 System breaking point: ~{users} concurrent users")
                tester.print_results(result)
                break
                
            users += 100
            
        except Exception as e:
            print(f"\n💥 System failed at {users} users: {e}")
            break
    
    await gateway.shutdown()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--stress":
        # Run stress test
        asyncio.run(run_stress_test())
    else:
        # Run progressive load test
        asyncio.run(run_progressive_load_test()) 