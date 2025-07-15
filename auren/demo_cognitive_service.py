"""
Demo script for CognitiveTwinService integration.
Shows how AUREN can track biometrics through natural conversation.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.database import db
from services.cognitive_twin_service import CognitiveTwinService
from core.config import validate_environment

async def demo_cognitive_service():
    """Demonstrate the complete CognitiveTwinService integration."""
    
    print("🧠 AUREN Cognitive Twin Service Demo")
    print("=" * 50)
    
    try:
        # Validate environment
        validate_environment()
        
        # Initialize database
        print("1. Initializing database connection...")
        await db.initialize()
        print("   ✅ Database connected")
        
        # Create service
        service = CognitiveTwinService(db.pool)
        user_id = "demo_user_astxryts"
        
        print(f"\n2. Testing with user: {user_id}")
        
        # Test weight tracking
        print("\n3. Testing weight tracking...")
        weight_result = await service.track_weight(user_id, 218.5, "lbs")
        print(f"   {weight_result.message}")
        
        # Test energy tracking
        print("\n4. Testing energy tracking...")
        energy_result = await service.track_energy(user_id, 8, "morning")
        print(f"   {energy_result['message']}")
        
        # Test sleep tracking
        print("\n5. Testing sleep tracking...")
        sleep_result = await service.track_sleep(user_id, 7.5, 8)
        print(f"   {sleep_result['message']}")
        
        # Test milestone tracking
        print("\n6. Testing milestone tracking...")
        milestone_result = await service.track_milestone(
            user_id,
            "weight_loss",
            "First Week Success",
            "Lost 2.5 lbs in first week through morning workouts",
            {"weight_change": -2.5, "weeks": 1}
        )
        print(f"   {milestone_result['message']}")
        
        # Test insights
        print("\n7. Testing insights retrieval...")
        weight_insights = await service.get_weight_insights(user_id)
        print(f"   {weight_insights.message}")
        
        # Test natural language extraction
        print("\n8. Testing natural language extraction...")
        
        test_texts = [
            "I weighed 215 lbs this morning",
            "Energy is 9 out of 10 today",
            "Got 8 hours of sleep last night",
            "Down to 212 pounds!",
            "Feeling great - energy at 8/10"
        ]
        
        for text in test_texts:
            weight = service.extract_weight_from_text(text)
            energy = service.extract_energy_from_text(text)
            sleep = service.extract_sleep_from_text(text)
            
            if weight:
                print(f"   📊 '{text}' → Weight: {weight['weight']} {weight['unit']}")
            if energy:
                print(f"   ⚡ '{text}' → Energy: {energy}/10")
            if sleep:
                print(f"   😴 '{text}' → Sleep: {sleep['hours']} hours")
        
        # Get user summary
        print("\n9. User summary...")
        summary = await service.get_user_summary(user_id)
        print(f"   📈 Total milestones: {summary.get('total_milestones', 0)}")
        print(f"   📊 Latest biometrics: {len(summary.get('latest_biometrics', {}))} entries")
        
        print("\n✅ Demo complete! AUREN can now track biometrics naturally.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is configured")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(demo_cognitive_service())
