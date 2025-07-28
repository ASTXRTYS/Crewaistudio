#!/usr/bin/env python3
"""
AUREN Backend Comprehensive Test Suite
Simulates real AI agent biometric processing workflow
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
import httpx
from typing import List, Dict
import uuid

# Test configuration
BASE_URL = "http://144.126.215.218:8888"
TEST_USERS = ["test_user_1", "test_user_2", "test_user_3", "founder", "alpha_tester"]
DEVICES = ["oura", "whoop", "apple_health", "garmin", "fitbit"]

class BiometricSimulator:
    """Simulates realistic biometric data from various devices"""
    
    @staticmethod
    def generate_oura_event(user_id: str) -> Dict:
        """Generate realistic Oura Ring data"""
        return {
            "event_type": random.choice(["readiness.updated", "sleep.created", "activity.updated"]),
            "user_id": user_id,
            "data": {
                "readiness_score": random.randint(60, 95),
                "hrv_balance": random.randint(40, 85),
                "body_temperature": round(random.uniform(36.0, 37.5), 1),
                "resting_heart_rate": random.randint(45, 75),
                "respiratory_rate": round(random.uniform(12, 18), 1),
                "sleep_score": random.randint(65, 95),
                "total_sleep": random.randint(360, 540),  # 6-9 hours in minutes
                "rem_sleep": random.randint(60, 150),
                "deep_sleep": random.randint(40, 120),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def generate_whoop_event(user_id: str) -> Dict:
        """Generate realistic WHOOP data"""
        return {
            "event_type": "recovery.updated",
            "user_id": user_id,
            "data": {
                "recovery_score": random.randint(30, 95),
                "hrv": random.randint(35, 120),
                "rhr": random.randint(45, 75),
                "strain": round(random.uniform(5.0, 20.0), 1),
                "sleep_performance": random.randint(70, 100),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def generate_apple_health_event(user_id: str) -> Dict:
        """Generate realistic Apple Health data"""
        return {
            "event_type": "health_data.batch",
            "user_id": user_id,
            "data": {
                "samples": [
                    {
                        "type": "HRV",
                        "value": random.randint(20, 100),
                        "unit": "ms",
                        "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat()
                    } for i in range(5)
                ] + [
                    {
                        "type": "HeartRate",
                        "value": random.randint(60, 180),
                        "unit": "bpm",
                        "timestamp": (datetime.utcnow() - timedelta(minutes=i*10)).isoformat()
                    } for i in range(3)
                ]
            }
        }

async def test_webhook_endpoint(client: httpx.AsyncClient, device: str, user_id: str):
    """Test a single webhook endpoint"""
    # Generate appropriate data based on device
    if device == "oura":
        data = BiometricSimulator.generate_oura_event(user_id)
    elif device == "whoop":
        data = BiometricSimulator.generate_whoop_event(user_id)
    elif device == "apple_health":
        data = BiometricSimulator.generate_apple_health_event(user_id)
    else:
        # Generic data for other devices
        data = {
            "event_type": "measurement.created",
            "user_id": user_id,
            "data": {
                "heart_rate": random.randint(60, 100),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    start_time = time.time()
    try:
        response = await client.post(
            f"{BASE_URL}/webhooks/{device}",
            json=data,
            timeout=10.0
        )
        latency = (time.time() - start_time) * 1000  # ms
        
        return {
            "device": device,
            "user_id": user_id,
            "status": response.status_code,
            "latency_ms": latency,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "device": device,
            "user_id": user_id,
            "status": "error",
            "error": str(e),
            "success": False
        }

async def test_baseline_endpoint(client: httpx.AsyncClient, user_id: str):
    """Test baseline calculation endpoint"""
    metrics = ["hrv", "resting_heart_rate", "readiness_score"]
    results = []
    
    for metric in metrics:
        try:
            response = await client.get(f"{BASE_URL}/baselines/{user_id}/{metric}")
            results.append({
                "user_id": user_id,
                "metric": metric,
                "status": response.status_code,
                "data": response.json() if response.status_code == 200 else None
            })
        except Exception as e:
            results.append({
                "user_id": user_id,
                "metric": metric,
                "error": str(e)
            })
    
    return results

async def test_pattern_detection(client: httpx.AsyncClient, user_id: str):
    """Test pattern detection endpoint"""
    try:
        response = await client.get(f"{BASE_URL}/patterns/{user_id}")
        return {
            "user_id": user_id,
            "status": response.status_code,
            "patterns": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "error": str(e)
        }

async def stress_test_webhooks(num_requests: int = 100):
    """Stress test webhook endpoints with concurrent requests"""
    print(f"\n🚀 Starting stress test with {num_requests} requests...")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        
        # Create concurrent webhook requests
        for i in range(num_requests):
            device = random.choice(DEVICES)
            user_id = random.choice(TEST_USERS)
            task = test_webhook_endpoint(client, device, user_id)
            tasks.append(task)
        
        # Execute all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        avg_latency = sum(r.get("latency_ms", 0) for r in results if "latency_ms" in r) / len(results)
        
        print(f"\n📊 Stress Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {successful} ({successful/num_requests*100:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Requests/sec: {num_requests/total_time:.1f}")
        print(f"Average Latency: {avg_latency:.1f}ms")
        
        # Show latency distribution
        latencies = [r.get("latency_ms", 0) for r in results if "latency_ms" in r]
        if latencies:
            latencies.sort()
            print(f"\nLatency Distribution:")
            print(f"  Min: {latencies[0]:.1f}ms")
            print(f"  P50: {latencies[len(latencies)//2]:.1f}ms")
            print(f"  P95: {latencies[int(len(latencies)*0.95)]:.1f}ms")
            print(f"  P99: {latencies[int(len(latencies)*0.99)]:.1f}ms")
            print(f"  Max: {latencies[-1]:.1f}ms")

async def test_full_workflow():
    """Test the complete AI agent workflow"""
    print("\n🔄 Testing Full AI Agent Workflow...")
    
    async with httpx.AsyncClient() as client:
        test_user = "workflow_test_user"
        
        # Step 1: Send multiple biometric events
        print("\n1️⃣ Sending biometric events...")
        for i in range(10):
            for device in ["oura", "whoop", "apple_health"]:
                result = await test_webhook_endpoint(client, device, test_user)
                print(f"  {device}: {result['status']} ({result.get('latency_ms', 0):.0f}ms)")
            await asyncio.sleep(0.5)  # Simulate real-time data
        
        # Wait for processing
        print("\n⏳ Waiting for AI processing...")
        await asyncio.sleep(5)
        
        # Step 2: Check baselines
        print("\n2️⃣ Checking calculated baselines...")
        baseline_results = await test_baseline_endpoint(client, test_user)
        for result in baseline_results:
            if "data" in result and result["data"]:
                print(f"  {result['metric']}: {result['data'].get('baseline', 'N/A')}")
        
        # Step 3: Check patterns
        print("\n3️⃣ Checking detected patterns...")
        pattern_result = await test_pattern_detection(client, test_user)
        if pattern_result.get("patterns"):
            patterns = pattern_result["patterns"].get("patterns", [])
            if patterns:
                for pattern in patterns:
                    print(f"  Detected: {pattern.get('pattern_type', 'Unknown')} - "
                          f"Severity: {pattern.get('severity', 'N/A')}")
            else:
                print("  No patterns detected yet")

async def test_component_health():
    """Test all system components"""
    print("\n🏥 Testing System Component Health...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            health = response.json()
            
            print(f"\nOverall Status: {health['status'].upper()}")
            print("\nComponents:")
            for component, status in health.get("components", {}).items():
                emoji = "✅" if status else "❌"
                print(f"  {emoji} {component}: {status}")
            
            print("\nSections Ready:")
            for section, ready in health.get("sections_ready", {}).items():
                emoji = "✅" if ready else "❌"
                print(f"  {emoji} {section}: {ready}")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")

async def main():
    """Run all tests"""
    print("="*60)
    print("AUREN BACKEND COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # 1. Component health check
    await test_component_health()
    
    # 2. Full workflow test
    await test_full_workflow()
    
    # 3. Stress test
    await stress_test_webhooks(num_requests=50)  # Start with 50 for initial test
    
    print("\n✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main()) 