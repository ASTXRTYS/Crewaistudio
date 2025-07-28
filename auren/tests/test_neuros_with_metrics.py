#!/usr/bin/env python3
"""
NEUROS Mock Biometric Test with Full Metrics Implementation
Purpose: Test NEUROS reasoning with mock data and push metrics to Prometheus/Grafana
"""

import asyncio
import json
import time
import random
from datetime import datetime, timedelta
import httpx
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Define Prometheus metrics
webhook_events = Counter('auren_webhook_events_total', 'Total webhook events received', ['device_type', 'event_type'])
processing_time = Histogram('auren_processing_duration_seconds', 'Time spent processing events')
active_users = Gauge('auren_active_users', 'Number of active users')
neuros_mode = Gauge('auren_neuros_mode', 'Current NEUROS mode', ['mode'])
hrv_score = Gauge('auren_hrv_score', 'Latest HRV score by user', ['user_id'])
readiness_score = Gauge('auren_readiness_score', 'Latest readiness score by user', ['user_id'])
recovery_score = Gauge('auren_recovery_score', 'Latest recovery score by user', ['user_id'])

# NEUROS modes from config
NEUROS_MODES = {
    "baseline": "Establishing patterns",
    "recovery": "Active recovery needed", 
    "performance": "Peak performance window",
    "adaptation": "Training adaptation phase",
    "alert": "Stress response detected"
}

class MockBiometricGenerator:
    """Generate realistic biometric data patterns"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_hrv = 45 + random.randint(-5, 15)
        self.base_rhr = 52 + random.randint(-3, 5)
        self.stress_level = random.uniform(0.3, 0.7)
        
    def generate_oura_daily(self, day_offset: int = 0):
        """Generate Oura ring daily readiness data"""
        # Simulate circadian rhythm and weekly patterns
        weekday = (datetime.now() - timedelta(days=day_offset)).weekday()
        
        # Lower readiness on Mondays, higher on weekends
        weekday_modifier = {0: -10, 1: -5, 2: 0, 3: 0, 4: -5, 5: 5, 6: 8}
        
        readiness = 70 + random.randint(-10, 15) + weekday_modifier.get(weekday, 0)
        hrv = self.base_hrv + random.randint(-8, 12) + (readiness - 70) * 0.5
        
        return {
            "event_type": "daily_readiness",
            "user_id": self.user_id,
            "timestamp": (datetime.now() - timedelta(days=day_offset)).isoformat(),
            "data": {
                "readiness_score": max(40, min(95, readiness)),
                "hrv_balance": max(20, min(100, hrv)),
                "body_temperature": 36.5 + random.uniform(-0.3, 0.3),
                "resting_heart_rate": self.base_rhr + random.randint(-3, 3),
                "respiratory_rate": 14 + random.uniform(-1, 1),
                "sleep_score": 70 + random.randint(-15, 20),
                "activity_balance": 80 + random.randint(-20, 10)
            }
        }
    
    def generate_whoop_recovery(self, hour_offset: int = 0):
        """Generate WHOOP recovery data"""
        # Simulate post-workout recovery patterns
        recovery = 65 + random.randint(-20, 25)
        strain = 8 + random.uniform(-3, 6)
        
        return {
            "event_type": "recovery_update", 
            "user_id": self.user_id,
            "timestamp": (datetime.now() - timedelta(hours=hour_offset)).isoformat(),
            "data": {
                "recovery_score": max(20, min(95, recovery)),
                "hrv_rmssd": self.base_hrv + random.randint(-10, 15),
                "sleep_performance": 75 + random.randint(-20, 20),
                "strain_score": max(0, min(20, strain)),
                "calories_burned": 2000 + strain * 100 + random.randint(-200, 300)
            }
        }
    
    def generate_apple_health(self):
        """Generate Apple Health real-time data"""
        return {
            "event_type": "realtime_vitals",
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "heart_rate": 65 + random.randint(-10, 40),  # Can spike during activity
                "hrv_instantaneous": self.base_hrv + random.randint(-5, 8),
                "blood_oxygen": 95 + random.randint(0, 4),
                "respiratory_rate": 15 + random.uniform(-2, 3),
                "activity_calories": random.randint(50, 500),
                "step_count": random.randint(1000, 15000)
            }
        }

class NEUROSMockTester:
    """Test NEUROS with mock data and metrics"""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_webhook(self, device: str, data: dict):
        """Send webhook and measure response"""
        start_time = time.time()
        
        try:
            # Send to webhook endpoint
            response = await self.client.post(
                f"{self.base_url}/webhooks/{device}",
                json=data
            )
            
            # Record metrics
            processing_duration = time.time() - start_time
            webhook_events.labels(device_type=device, event_type=data["event_type"]).inc()
            processing_time.observe(processing_duration)
            
            # Update gauges based on data
            if "readiness_score" in data.get("data", {}):
                readiness_score.labels(user_id=data["user_id"]).set(data["data"]["readiness_score"])
            if "hrv_balance" in data.get("data", {}):
                hrv_score.labels(user_id=data["user_id"]).set(data["data"]["hrv_balance"])
            if "recovery_score" in data.get("data", {}):
                recovery_score.labels(user_id=data["user_id"]).set(data["data"]["recovery_score"])
            
            return response.json(), processing_duration
            
        except Exception as e:
            print(f"Error sending webhook: {e}")
            return None, processing_duration
    
    async def simulate_neuros_reasoning(self, user_data: list):
        """Simulate NEUROS analyzing patterns and changing modes"""
        print("\n🧠 NEUROS REASONING SIMULATION")
        print("================================")
        
        # Analyze patterns
        hrv_values = [d["data"].get("hrv_balance", d["data"].get("hrv_rmssd", 50)) 
                      for d in user_data if "hrv" in str(d["data"])]
        readiness_values = [d["data"].get("readiness_score", 70) 
                           for d in user_data if "readiness_score" in d["data"]]
        
        avg_hrv = sum(hrv_values) / len(hrv_values) if hrv_values else 50
        avg_readiness = sum(readiness_values) / len(readiness_values) if readiness_values else 70
        hrv_trend = hrv_values[-1] - hrv_values[0] if len(hrv_values) > 1 else 0
        
        # NEUROS reasoning logic
        current_mode = "baseline"
        reasoning = []
        
        if avg_readiness < 60 or avg_hrv < 40:
            current_mode = "recovery"
            reasoning.append("Low readiness and HRV indicate need for recovery focus")
        elif avg_readiness > 85 and avg_hrv > 60:
            current_mode = "performance"
            reasoning.append("Excellent biometrics suggest peak performance window")
        elif hrv_trend < -10:
            current_mode = "alert"
            reasoning.append("Declining HRV trend detected - monitoring stress response")
        elif abs(hrv_trend) > 5:
            current_mode = "adaptation"
            reasoning.append("Significant HRV changes indicate adaptation phase")
        
        # Update mode metric
        for mode in NEUROS_MODES:
            neuros_mode.labels(mode=mode).set(1 if mode == current_mode else 0)
        
        # Generate NEUROS response
        neuros_response = {
            "mode": current_mode,
            "analysis": {
                "avg_hrv": round(avg_hrv, 1),
                "avg_readiness": round(avg_readiness, 1),
                "hrv_trend": round(hrv_trend, 1),
                "pattern": "improving" if hrv_trend > 0 else "declining" if hrv_trend < 0 else "stable"
            },
            "reasoning": reasoning,
            "recommendations": self.generate_recommendations(current_mode, avg_readiness, avg_hrv),
            "confidence": 0.85 if len(user_data) > 5 else 0.65
        }
        
        return neuros_response
    
    def generate_recommendations(self, mode: str, readiness: float, hrv: float):
        """Generate mode-specific recommendations"""
        recs = {
            "recovery": [
                "Prioritize sleep quality - aim for 8+ hours",
                "Reduce training intensity by 30-40%",
                "Focus on parasympathetic activation: breathwork, yoga",
                "Increase protein intake to 1.2g/lb bodyweight"
            ],
            "performance": [
                "Optimal window for high-intensity training",
                "Consider PR attempts or skill acquisition",
                "Maintain current sleep and nutrition protocols",
                "Track performance metrics closely"
            ],
            "alert": [
                "Monitor stress levels throughout the day",
                "Implement 5-minute breathing breaks every 2 hours",
                "Avoid additional stressors if possible",
                "Consider adaptogenic support"
            ],
            "adaptation": [
                "Body is responding to training - maintain consistency",
                "Focus on recovery between sessions",
                "Monitor for signs of overreaching",
                "Ensure adequate micronutrient intake"
            ],
            "baseline": [
                "Continue current protocols",
                "Establish consistent sleep/wake times",
                "Build progressive training volume",
                "Focus on habit formation"
            ]
        }
        return recs.get(mode, ["Continue monitoring patterns"])
    
    async def run_comprehensive_test(self):
        """Run full test scenario with multiple users"""
        print("🚀 STARTING COMPREHENSIVE NEUROS TEST")
        print("=====================================")
        
        # Create multiple test users
        users = [
            MockBiometricGenerator(f"athlete_{i}") 
            for i in range(1, 4)
        ]
        
        active_users.set(len(users))
        
        # Generate historical data for each user
        all_results = []
        
        for user_idx, user_gen in enumerate(users):
            print(f"\n👤 Testing User: {user_gen.user_id}")
            print("-" * 40)
            
            user_data = []
            
            # Generate 7 days of Oura data
            print("📊 Sending Oura daily readiness data...")
            for day in range(7):
                data = user_gen.generate_oura_daily(day)
                result, duration = await self.test_webhook("oura", data)
                user_data.append(data)
                print(f"  Day -{day}: Readiness={data['data']['readiness_score']}, "
                      f"HRV={data['data']['hrv_balance']:.1f} "
                      f"(processed in {duration:.3f}s)")
                await asyncio.sleep(0.5)
            
            # Generate WHOOP recovery data
            print("\n💪 Sending WHOOP recovery data...")
            for hour in [0, 12, 24]:
                data = user_gen.generate_whoop_recovery(hour)
                result, duration = await self.test_webhook("whoop", data)
                user_data.append(data)
                print(f"  -{hour}h: Recovery={data['data']['recovery_score']}, "
                      f"Strain={data['data']['strain_score']:.1f} "
                      f"(processed in {duration:.3f}s)")
                await asyncio.sleep(0.5)
            
            # Generate real-time Apple Health data
            print("\n⌚ Sending Apple Health real-time data...")
            for _ in range(3):
                data = user_gen.generate_apple_health()
                result, duration = await self.test_webhook("apple_health", data)
                user_data.append(data)
                print(f"  HR={data['data']['heart_rate']}, "
                      f"SpO2={data['data']['blood_oxygen']}% "
                      f"(processed in {duration:.3f}s)")
                await asyncio.sleep(0.5)
            
            # Simulate NEUROS reasoning
            neuros_analysis = await self.simulate_neuros_reasoning(user_data)
            
            print(f"\n🧠 NEUROS Analysis for {user_gen.user_id}:")
            print(f"  Mode: {neuros_analysis['mode'].upper()} - {NEUROS_MODES[neuros_analysis['mode']]}")
            print(f"  Pattern: {neuros_analysis['analysis']['pattern']}")
            print(f"  Avg HRV: {neuros_analysis['analysis']['avg_hrv']}")
            print(f"  Avg Readiness: {neuros_analysis['analysis']['avg_readiness']}")
            print(f"  Confidence: {neuros_analysis['confidence']*100:.0f}%")
            print(f"\n  Reasoning: {neuros_analysis['reasoning'][0]}")
            print(f"  Top Recommendation: {neuros_analysis['recommendations'][0]}")
            
            all_results.append({
                "user": user_gen.user_id,
                "events_sent": len(user_data),
                "neuros_analysis": neuros_analysis
            })
        
        # Final metrics update
        print("\n📊 UPDATING PROMETHEUS METRICS...")
        print("-" * 40)
        
        # Get current metrics
        metrics_data = generate_latest()
        
        # Show summary
        print(f"Total webhook events: {webhook_events._value.sum()}")
        print(f"Active users: {active_users._value.get()}")
        print(f"Processing times: {processing_time._sum.sum():.2f}s total")
        
        return all_results
    
    async def update_api_metrics_endpoint(self):
        """Update the API to return proper Prometheus metrics"""
        print("\n🔧 Implementing Prometheus metrics endpoint...")
        
        # This would normally be done in the API code, but we'll test it
        try:
            # Test if metrics endpoint exists
            response = await self.client.get(f"{self.base_url}/metrics")
            if response.status_code == 404 or "Not Found" in response.text:
                print("  ❌ /metrics endpoint returns 404 - needs implementation")
                print("  📝 To fix: Add prometheus_client to API and return generate_latest()")
            else:
                print("  ✅ /metrics endpoint exists")
        except Exception as e:
            print(f"  ❌ Error checking metrics: {e}")
    
    async def close(self):
        """Clean up"""
        await self.client.aclose()

async def main():
    """Run the complete test"""
    tester = NEUROSMockTester()
    
    try:
        # Check API health first
        print("🏥 Checking API health...")
        health = await tester.client.get(f"{tester.base_url}/health")
        print(f"API Status: {health.json().get('status', 'unknown')}")
        
        # Run comprehensive test
        results = await tester.run_comprehensive_test()
        
        # Check metrics endpoint
        await tester.update_api_metrics_endpoint()
        
        # Summary
        print("\n✅ TEST COMPLETE!")
        print("=" * 50)
        print(f"Tested {len(results)} users")
        print(f"Total events processed: {sum(r['events_sent'] for r in results)}")
        print("\nNEUROS Mode Distribution:")
        for r in results:
            print(f"  {r['user']}: {r['neuros_analysis']['mode'].upper()}")
        
        print("\n🎯 Next Steps:")
        print("1. Implement /metrics endpoint in biometric API")
        print("2. Add prometheus_client to requirements")
        print("3. Return generate_latest() with proper content type")
        print("4. Restart container and check Grafana dashboards")
        
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main()) 