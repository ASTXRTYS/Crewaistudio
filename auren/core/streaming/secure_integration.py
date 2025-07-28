"""
Secure Integration - Adding Security Layer to Module C & D
Shows how to integrate security layer with existing monitoring
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from cryptography.fernet import Fernet
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation

# Import security layer
from auren.realtime.security_layer import SecureEventStreamer, SecurityPolicy, RoleBasedEventFilter

# Import from Module C
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
from auren.realtime.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer, ClientSubscription

# Import from Module D integration
from auren.agents.monitored_orchestrator import AURENMonitoredOrchestrator

logger = logging.getLogger(__name__)


async def setup_secure_monitored_auren_system(config: Dict[str, Any]):
    """
    Enhanced setup with security layer integrated
    This wraps the existing monitoring with security
    """
    
    # 1. Initialize base Redis streamer
    redis_streamer = RedisStreamEventStreamer(
        redis_url=config["redis_url"],
        stream_name="auren:events"
    )
    await redis_streamer.initialize()
    
    # 2. Wrap with security layer
    encryption_key = config.get("encryption_key", Fernet.generate_key())
    security_policy = SecurityPolicy(
        sanitize_user_ids=True,
        sanitize_biometrics=True,
        sanitize_conversations=True,
        encrypt_costs=True,
        encrypt_queries=True,
        max_content_length=500
    )
    
    secure_streamer = SecureEventStreamer(
        base_streamer=redis_streamer,
        encryption_key=encryption_key,
        security_policy=security_policy
    )
    
    logger.info("Security layer initialized with sanitization and encryption")
    
    # 3. Initialize event instrumentation with secure streamer
    event_instrumentation = CrewAIEventInstrumentation(
        event_streamer=secure_streamer  # Now all events go through security!
    )
    
    # 4. Create secure monitored orchestrator
    orchestrator = AURENMonitoredOrchestrator(
        user_id=config["user_id"],
        memory_backend=config["memory_backend"],
        event_store=config["event_store"],
        hypothesis_validator=config["hypothesis_validator"],
        knowledge_manager=config["knowledge_manager"],
        event_instrumentation=event_instrumentation
    )
    
    # 5. Initialize secure WebSocket server with role filtering
    websocket_streamer = SecureWebSocketEventStreamer(
        host=config.get("websocket_host", "localhost"),
        port=config.get("websocket_port", 8765),
        event_streamer=redis_streamer,  # Reads sanitized events from Redis
        jwt_secret=config.get("jwt_secret", "secure_secret"),
        role_filter=RoleBasedEventFilter()
    )
    
    # Start WebSocket server
    asyncio.create_task(websocket_streamer.start_server())
    
    logger.info("Secure AUREN system initialized with full monitoring and sanitization")
    
    return {
        "orchestrator": orchestrator,
        "event_instrumentation": event_instrumentation,
        "secure_streamer": secure_streamer,
        "websocket_streamer": websocket_streamer,
        "encryption_key": encryption_key
    }


class SecureWebSocketEventStreamer(EnhancedWebSocketEventStreamer):
    """Extended WebSocket streamer with role-based filtering"""
    
    def __init__(self, *args, role_filter: RoleBasedEventFilter = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_filter = role_filter or RoleBasedEventFilter()
    
    async def _send_to_connection(self, connection, event_data: Dict[str, Any]) -> bool:
        """Override to add role-based filtering"""
        
        # Get user role from connection (set during authentication)
        user_role = getattr(connection, 'user_role', 'viewer')
        
        # Filter event based on role
        if 'event' in event_data:
            filtered_event = self.role_filter.filter_event_for_role(
                event_data['event'], 
                user_role
            )
            
            if filtered_event is None:
                # User shouldn't see this event
                return False
            
            # Replace with filtered version
            event_data = dict(event_data)
            event_data['event'] = filtered_event
        
        # Send filtered event
        return await super()._send_to_connection(connection, event_data)


async def demonstrate_secure_monitoring():
    """Demonstrate the security layer in action"""
    
    # Configuration with security settings
    config = {
        "redis_url": "redis://localhost:6379",
        "user_id": "demo_user_12345",  # Will be hashed
        "encryption_key": Fernet.generate_key(),
        "jwt_secret": "your_jwt_secret_here",
        "websocket_host": "localhost",
        "websocket_port": 8765,
        # ... other Module A & B dependencies would go here
    }
    
    # Setup secure system
    system = await setup_secure_monitored_auren_system(config)
    
    # Now when we process a message with sensitive data...
    test_message = """
    My HRV has been at 28 for days and I'm stressed. 
    My email is john@example.com and phone is 555-123-4567.
    What should I do?
    """
    
    response = await system["orchestrator"].handle_user_message(
        "session_123",
        test_message
    )
    
    print("\n=== Security Layer Active ===")
    print(f"Original user_id: {config['user_id']}")
    print(f"Events will show hashed user_id: hash_xxxxx...")
    print(f"Biometric values will show as ranges: 'low', 'normal_high', etc.")
    print(f"Token costs will be encrypted")
    print(f"PII will be removed from messages")
    
    # Check security statistics
    stats = system["secure_streamer"].get_statistics()
    print(f"\nSecurity Statistics:")
    print(f"- Total events: {stats['total_events']}")
    print(f"- Sanitized: {stats['sanitized_events']}")
    print(f"- Fields encrypted: {stats['encrypted_fields']}")
    print(f"- Sanitization rate: {stats['sanitization_rate']:.2%}")
    
    # Dashboard will show different data based on user role:
    print("\n=== Dashboard Access by Role ===")
    print("Admin: Can see everything (decrypt costs, see hashed user IDs)")
    print("Developer: Can see performance data (costs hidden)")
    print("Analyst: Can see aggregated metrics only")
    print("Viewer: Can see public system health only")
    
    print("\n✅ Secure monitoring active! Check dashboard at http://localhost:3000")


def verify_security_implementation():
    """Verification checklist for security implementation"""
    
    checklist = {
        "User ID Sanitization": {
            "requirement": "All user_ids are hashed",
            "test": "Check events in Redis - no plain user IDs",
            "dashboard": "Should show 'hash_xxxx' format"
        },
        "Biometric Sanitization": {
            "requirement": "Exact values converted to ranges",
            "test": "HRV of 35 → 'normal_low'",
            "dashboard": "Should show descriptive ranges, not numbers"
        },
        "Conversation Sanitization": {
            "requirement": "PII removed, content truncated",
            "test": "Emails → '[email]', phones → '[phone]'",
            "dashboard": "No PII visible in messages"
        },
        "Cost Encryption": {
            "requirement": "Token costs encrypted",
            "test": "Check payload has encrypted values",
            "dashboard": "Only admins see actual costs"
        },
        "Query Encryption": {
            "requirement": "User queries encrypted",
            "test": "Query field is base64 encrypted string",
            "dashboard": "Queries visible only to authorized roles"
        },
        "Role-Based Filtering": {
            "requirement": "Events filtered by user role",
            "test": "Connect as 'viewer' - see only public events",
            "dashboard": "Different roles see different data"
        }
    }
    
    print("\n=== Security Implementation Checklist ===")
    for feature, details in checklist.items():
        print(f"\n{feature}:")
        print(f"  ✓ Requirement: {details['requirement']}")
        print(f"  ✓ Test: {details['test']}")
        print(f"  ✓ Dashboard: {details['dashboard']}")
    
    return checklist


if __name__ == "__main__":
    # Run verification
    verify_security_implementation()
    
    # Run demonstration
    asyncio.run(demonstrate_secure_monitoring()) 