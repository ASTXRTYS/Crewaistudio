#!/usr/bin/env python3
"""Test AUREN without external dependencies"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.auren_ui_agent import AURENAgent
from src.integrations.whatsapp_mock import MockWhatsAppInterface
from src.core.tenant_manager import TenantManager
import asyncio

async def test_basic_flow():
    print("🚀 Testing AUREN Basic Flow...")
    
    # Initialize components
    tenant_mgr = TenantManager()
    tenant_ctx = tenant_mgr.get_tenant_context("+1234567890")
    
    auren = AURENAgent(tenant_ctx.tenant_id)
    whatsapp = MockWhatsAppInterface()
    
    # Simulate conversation
    test_messages = [
        "Hello AUREN",
        "I need help with a project",
        "Can I speak to the Journal specialist?"
    ]
    
    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        
        # Process message
        response = auren.process_message(msg, "+1234567890")
        
        # Send response
        await whatsapp.send_message("+1234567890", response["response"])
        
        await asyncio.sleep(1)
    
    print("\n✅ Basic flow test complete!")

if __name__ == "__main__":
    asyncio.run(test_basic_flow())
