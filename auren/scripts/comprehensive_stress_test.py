#!/usr/bin/env python3
"""
Comprehensive Stress Test for AUREN Framework
Tests all major components and generates detailed report
"""

import asyncio
import time
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import asyncpg
import redis
import aiohttp
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "environment": {
        "python_version": sys.version,
        "platform": sys.platform,
    },
    "components": {},
    "performance_metrics": {},
    "recommendations": []
}


async def test_postgresql():
    """Test PostgreSQL connectivity and performance"""
    print("\n🐘 Testing PostgreSQL...")
    results = {"status": "unknown", "details": {}}
    
    try:
        # Connection test
        start_time = time.time()
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        connection_time = time.time() - start_time
        results["details"]["connection_time"] = f"{connection_time:.3f}s"
        
        # Table count
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        results["details"]["table_count"] = len(tables)
        results["details"]["tables"] = [t['tablename'] for t in tables]
        
        # Performance test - Insert/Select
        start_time = time.time()
        for i in range(100):
            await conn.execute("""
                INSERT INTO user_profiles (external_id, profile_data)
                VALUES ($1, $2)
                ON CONFLICT (external_id) DO UPDATE
                SET profile_data = $2
            """, f"stress_test_{i}", json.dumps({"test": True, "index": i}))
        
        insert_time = time.time() - start_time
        results["details"]["insert_performance"] = f"{100/insert_time:.1f} ops/sec"
        
        # Query performance
        start_time = time.time()
        for i in range(100):
            await conn.fetchval(
                "SELECT profile_data FROM user_profiles WHERE external_id = $1",
                f"stress_test_{i}"
            )
        query_time = time.time() - start_time
        results["details"]["query_performance"] = f"{100/query_time:.1f} ops/sec"
        
        # Cleanup
        await conn.execute("DELETE FROM user_profiles WHERE external_id LIKE 'stress_test_%'")
        
        await conn.close()
        results["status"] = "operational"
        print(f"  ✅ PostgreSQL is operational")
        print(f"  📊 Connection time: {connection_time:.3f}s")
        print(f"  📊 Insert performance: {100/insert_time:.1f} ops/sec")
        print(f"  📊 Query performance: {100/query_time:.1f} ops/sec")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        print(f"  ❌ PostgreSQL test failed: {e}")
        
    test_results["components"]["postgresql"] = results
    return results


async def test_redis():
    """Test Redis connectivity and performance"""
    print("\n🔴 Testing Redis...")
    results = {"status": "unknown", "details": {}}
    
    try:
        # Connection test
        start_time = time.time()
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0))
        )
        r.ping()
        connection_time = time.time() - start_time
        results["details"]["connection_time"] = f"{connection_time:.3f}s"
        
        # Performance test - Set/Get
        start_time = time.time()
        for i in range(1000):
            r.set(f"stress_test:{i}", json.dumps({"index": i, "data": "test" * 10}))
        set_time = time.time() - start_time
        results["details"]["set_performance"] = f"{1000/set_time:.1f} ops/sec"
        
        start_time = time.time()
        for i in range(1000):
            r.get(f"stress_test:{i}")
        get_time = time.time() - start_time
        results["details"]["get_performance"] = f"{1000/get_time:.1f} ops/sec"
        
        # Memory usage
        info = r.info()
        results["details"]["memory_used"] = info.get('used_memory_human', 'N/A')
        
        # Cleanup
        for i in range(1000):
            r.delete(f"stress_test:{i}")
        
        results["status"] = "operational"
        print(f"  ✅ Redis is operational")
        print(f"  📊 Connection time: {connection_time:.3f}s")
        print(f"  📊 Set performance: {1000/set_time:.1f} ops/sec")
        print(f"  📊 Get performance: {1000/get_time:.1f} ops/sec")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        print(f"  ❌ Redis test failed: {e}")
        
    test_results["components"]["redis"] = results
    return results


async def test_kafka():
    """Test Kafka connectivity"""
    print("\n📨 Testing Kafka...")
    results = {"status": "unknown", "details": {}}
    
    try:
        from kafka import KafkaProducer, KafkaConsumer
        from kafka.admin import KafkaAdminClient
        
        # Admin client test
        admin = KafkaAdminClient(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            client_id='stress-test-admin'
        )
        
        # Get topics
        topics = admin.list_topics()
        results["details"]["topic_count"] = len(topics)
        results["details"]["topics"] = list(topics)[:10]  # First 10 topics
        
        # Producer test
        producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        start_time = time.time()
        for i in range(100):
            producer.send('stress-test', {'index': i, 'timestamp': time.time()})
        producer.flush()
        produce_time = time.time() - start_time
        results["details"]["produce_performance"] = f"{100/produce_time:.1f} msgs/sec"
        
        results["status"] = "operational"
        print(f"  ✅ Kafka is operational")
        print(f"  📊 Topics found: {len(topics)}")
        print(f"  📊 Produce performance: {100/produce_time:.1f} msgs/sec")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        print(f"  ❌ Kafka test failed: {e}")
        
    test_results["components"]["kafka"] = results
    return results


async def test_openai_api():
    """Test OpenAI API connectivity"""
    print("\n🤖 Testing OpenAI API...")
    results = {"status": "unknown", "details": {}}
    
    try:
        from openai import AsyncOpenAI
        
        # Create client
        client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Test completion
        start_time = time.time()
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful' in 5 words or less"}],
            max_tokens=10
        )
        response_time = time.time() - start_time
        
        results["details"]["response_time"] = f"{response_time:.3f}s"
        results["details"]["model_used"] = response.model
        results["details"]["tokens_used"] = response.usage.total_tokens
        results["status"] = "operational"
        
        print(f"  ✅ OpenAI API is operational")
        print(f"  📊 Response time: {response_time:.3f}s")
        print(f"  📊 Tokens used: {response.usage.total_tokens}")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        print(f"  ❌ OpenAI API test failed: {e}")
        
    test_results["components"]["openai_api"] = results
    return results


async def test_framework_components():
    """Test AUREN framework specific components"""
    print("\n🧠 Testing AUREN Framework Components...")
    results = {"status": "unknown", "modules": {}}
    
    # Test imports
    modules_to_test = [
        ("AI Gateway", "src.auren.ai.gateway"),
        ("Token Tracker", "src.auren.monitoring.token_tracker"),
        ("Database Connection", "src.database.connection"),
        ("Config Settings", "src.config.settings"),
        ("CEP HRV Rules", "src.cep.hrv_rules"),
        ("Kafka Producer", "src.infrastructure.kafka.producer"),
        ("Kafka Consumer", "src.infrastructure.kafka.consumer"),
    ]
    
    for name, module_path in modules_to_test:
        try:
            __import__(module_path)
            results["modules"][name] = "loaded"
            print(f"  ✅ {name} module loaded successfully")
        except Exception as e:
            results["modules"][name] = f"failed: {str(e)}"
            print(f"  ❌ {name} module failed to load: {e}")
    
    # Count successful loads
    successful = sum(1 for status in results["modules"].values() if status == "loaded")
    total = len(modules_to_test)
    
    if successful == total:
        results["status"] = "operational"
    elif successful > total / 2:
        results["status"] = "partial"
    else:
        results["status"] = "failed"
    
    test_results["components"]["framework"] = results
    return results


async def run_stress_tests():
    """Run all stress tests"""
    print("🚀 Starting Comprehensive AUREN Framework Stress Test")
    print("=" * 60)
    
    # Run all tests
    await test_postgresql()
    await test_redis()
    await test_kafka()
    await test_openai_api()
    await test_framework_components()
    
    # Generate recommendations
    generate_recommendations()
    
    # Save results
    with open('stress_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    # Generate report
    generate_report()


def generate_recommendations():
    """Generate recommendations based on test results"""
    recommendations = []
    
    # PostgreSQL recommendations
    pg_status = test_results["components"].get("postgresql", {}).get("status")
    if pg_status == "failed":
        recommendations.append({
            "component": "PostgreSQL",
            "severity": "critical",
            "recommendation": "PostgreSQL is not accessible. Ensure Docker container 'auren-postgres' is running and credentials in .env are correct."
        })
    
    # Redis recommendations
    redis_status = test_results["components"].get("redis", {}).get("status")
    if redis_status == "failed":
        recommendations.append({
            "component": "Redis",
            "severity": "high",
            "recommendation": "Redis is not accessible. The system will fall back to local memory for token tracking, but persistence will be lost."
        })
    
    # Kafka recommendations
    kafka_status = test_results["components"].get("kafka", {}).get("status")
    if kafka_status == "failed":
        recommendations.append({
            "component": "Kafka",
            "severity": "medium",
            "recommendation": "Kafka is not accessible. Real-time event streaming will not work. Ensure Kafka container is running."
        })
    
    # OpenAI API recommendations
    api_status = test_results["components"].get("openai_api", {}).get("status")
    if api_status == "failed":
        recommendations.append({
            "component": "OpenAI API",
            "severity": "critical",
            "recommendation": "OpenAI API is not accessible. Check your API key in .env file and ensure it's valid."
        })
    
    # Framework recommendations
    framework_status = test_results["components"].get("framework", {}).get("status")
    if framework_status != "operational":
        failed_modules = [name for name, status in test_results["components"]["framework"]["modules"].items() 
                         if status != "loaded"]
        recommendations.append({
            "component": "Framework",
            "severity": "high",
            "recommendation": f"Some framework modules failed to load: {', '.join(failed_modules)}. Check import paths and dependencies."
        })
    
    test_results["recommendations"] = recommendations


def generate_report():
    """Generate executive report"""
    print("\n" + "=" * 80)
    print("AUREN FRAMEWORK STRESS TEST REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📊 EXECUTIVE SUMMARY")
    print("-" * 40)
    
    # Component status summary
    operational = 0
    failed = 0
    partial = 0
    
    for component, data in test_results["components"].items():
        status = data.get("status", "unknown")
        if status == "operational":
            operational += 1
        elif status == "failed":
            failed += 1
        elif status == "partial":
            partial += 1
    
    total = operational + failed + partial
    
    print(f"Total Components Tested: {total}")
    print(f"✅ Operational: {operational}")
    print(f"⚠️  Partial: {partial}")
    print(f"❌ Failed: {failed}")
    
    # Overall health score
    health_score = (operational * 100 + partial * 50) / (total * 100) * 100
    print(f"\n🏥 Overall Health Score: {health_score:.1f}%")
    
    # Component details
    print("\n📋 COMPONENT STATUS")
    print("-" * 40)
    
    for component, data in test_results["components"].items():
        status = data.get("status", "unknown")
        emoji = "✅" if status == "operational" else "⚠️" if status == "partial" else "❌"
        print(f"{emoji} {component.upper()}: {status}")
        
        if status == "operational" and "details" in data:
            for key, value in data["details"].items():
                if "performance" in key or "time" in key:
                    print(f"   - {key}: {value}")
    
    # Recommendations
    if test_results["recommendations"]:
        print("\n🎯 RECOMMENDATIONS")
        print("-" * 40)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_recs = sorted(test_results["recommendations"], 
                           key=lambda x: severity_order.get(x["severity"], 99))
        
        for rec in sorted_recs:
            emoji = "🔴" if rec["severity"] == "critical" else "🟡" if rec["severity"] == "high" else "🟢"
            print(f"\n{emoji} {rec['component']} ({rec['severity'].upper()})")
            print(f"   {rec['recommendation']}")
    
    # Performance metrics
    print("\n⚡ PERFORMANCE METRICS")
    print("-" * 40)
    
    # PostgreSQL metrics
    pg_data = test_results["components"].get("postgresql", {}).get("details", {})
    if pg_data:
        print("PostgreSQL:")
        print(f"  - Connection time: {pg_data.get('connection_time', 'N/A')}")
        print(f"  - Insert performance: {pg_data.get('insert_performance', 'N/A')}")
        print(f"  - Query performance: {pg_data.get('query_performance', 'N/A')}")
    
    # Redis metrics
    redis_data = test_results["components"].get("redis", {}).get("details", {})
    if redis_data:
        print("\nRedis:")
        print(f"  - Connection time: {redis_data.get('connection_time', 'N/A')}")
        print(f"  - Set performance: {redis_data.get('set_performance', 'N/A')}")
        print(f"  - Get performance: {redis_data.get('get_performance', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("Full results saved to: stress_test_results.json")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_stress_tests()) 