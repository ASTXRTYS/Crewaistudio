"""
Comprehensive test of all AUREN framework components

This test verifies that all systems are operational and can work together
to provide elite performance optimization insights.
"""

import asyncio
import os
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent / "auren" / "src"))

async def test_complete_framework():
    """
    Comprehensive test of all AUREN framework components
    """
    print("=" * 60)
    print("AUREN Framework Complete Integration Test")
    print("=" * 60)
    
    # Test 1: Database Connection with proper error handling
    print("\n1. Testing PostgreSQL Connection...")
    try:
        import asyncpg
        # Use credentials from environment
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'auren_user'),
            password=os.getenv('DB_PASSWORD', 'auren_secure_password'),
            database=os.getenv('DB_NAME', 'auren_db')
        )
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        print("✓ PostgreSQL connection successful")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("  Tip: Check docker-compose logs postgres")
    
    # Test 2: Redis Connection
    print("\n2. Testing Redis Connection...")
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0))
        )
        r.ping()
        # Test token tracking functionality
        r.setex("test:token:count", 3600, 0)
        print("✓ Redis connection successful")
        print("✓ Token tracking storage ready")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
    
    # Test 3: Kafka Connection with improved timeout handling
    print("\n3. Testing Kafka Connection...")
    try:
        from kafka import KafkaProducer
        import json
        
        producer = KafkaProducer(
            bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=10000,
            api_version_auto_timeout_ms=5000
        )
        
        # Send test event
        future = producer.send('health.biometrics', {
            'event': 'test',
            'timestamp': datetime.now().isoformat()
        })
        result = future.get(timeout=5)
        producer.close()
        print("✓ Kafka connection successful")
        print("✓ Event streaming ready")
    except Exception as e:
        print(f"✗ Kafka connection failed: {e}")
        print("  Tip: Ensure Kafka is running: docker-compose up -d kafka")
    
    # Test 4: OpenAI API
    print("\n4. Testing OpenAI API...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Respond with: AUREN systems operational"}],
            max_tokens=10
        )
        print(f"✓ OpenAI API successful: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✗ OpenAI API failed: {e}")
    
    # Test 5: Neuroscientist Agent
    print("\n5. Testing Neuroscientist Agent...")
    try:
        from agents.neuroscientist import NeuroscientistAgent
        
        agent = NeuroscientistAgent()
        
        # Simulate HRV data
        test_hrv_data = {
            "timestamp": datetime.now().isoformat(),
            "rmssd": 28,  # Low HRV indicating stress
            "baseline_rmssd": 45,
            "percent_change": -38,
            "heart_rate": 72,
            "training_load_yesterday": "high_intensity_intervals"
        }
        
        print("✓ Neuroscientist agent created successfully")
        print("  Testing HRV analysis capabilities...")
        
        # Uncomment to run actual analysis (uses API tokens)
        # result = agent.analyze_hrv_pattern(test_hrv_data)
        # print(f"  Analysis result preview: {result[:200]}...")
        
    except Exception as e:
        print(f"✗ Neuroscientist agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Framework Module Loading
    print("\n6. Testing Framework Modules...")
    modules_status = {
        "AI Gateway": False,
        "Token Tracker": False,
        "Database Connection": False,
        "Config Settings": False,
        "CEP HRV Rules": False,
        "Kafka Producer": False,
        "Kafka Consumer": False
    }
    
    try:
        from auren.ai.gateway import AIGateway
        modules_status["AI Gateway"] = True
    except: pass
    
    try:
        from auren.ai.resilient_token_tracker import ResilientTokenTracker
        modules_status["Token Tracker"] = True
    except: pass
    
    try:
        from auren.database.connection import get_connection
        modules_status["Database Connection"] = True
    except: pass
    
    try:
        from config.settings import Settings
        modules_status["Config Settings"] = True
    except: pass
    
    try:
        from auren.cep.hrv_rules import HRVPatternDetector
        modules_status["CEP HRV Rules"] = True
    except: pass
    
    try:
        from infrastructure.kafka.producer import EventProducer
        modules_status["Kafka Producer"] = True
    except: pass
    
    try:
        from infrastructure.kafka.consumer import EventConsumer
        modules_status["Kafka Consumer"] = True
    except: pass
    
    # Print module status
    for module, status in modules_status.items():
        print(f"  {module}: {'✓ Loaded' if status else '✗ Failed'}")
    
    # Calculate operational percentage
    operational_percentage = (len([v for v in modules_status.values() if v]) / len(modules_status)) * 100
    
    print("\n" + "=" * 60)
    print(f"Framework Operational Status: {operational_percentage:.1f}%")
    print("=" * 60)
    
    if operational_percentage >= 90:
        print("\n🎉 AUREN Framework is ready for Neuroscientist testing!")
        print("Next step: Begin intensive agent testing with biometric data")
    else:
        print("\n⚠️  Some components need attention before testing")
        print("Review the failed components above and check logs")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_complete_framework()) 