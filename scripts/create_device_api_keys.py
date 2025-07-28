#!/usr/bin/env python3
"""
Create API keys for biometric devices using the admin API
"""
import requests
import json
from datetime import datetime

# Configuration
ADMIN_API_URL = "http://144.126.215.218:8888/admin/api-keys"
ADMIN_API_KEY = "sk-admin-b8f9c2a1d4e6f8a2c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9"

# Device configurations
DEVICES = [
    {
        "name": "Oura Ring",
        "description": "Oura Ring webhook integration",
        "rate_limit": 1000,  # requests per hour
        "role": "user"
    },
    {
        "name": "WHOOP Strap",
        "description": "WHOOP webhook integration",
        "rate_limit": 1000,
        "role": "user"
    },
    {
        "name": "Apple HealthKit",
        "description": "Apple Health data sync",
        "rate_limit": 2000,  # Higher limit for batch updates
        "role": "user"
    },
    {
        "name": "Garmin Connect",
        "description": "Garmin device integration",
        "rate_limit": 1000,
        "role": "user"
    },
    {
        "name": "Fitbit",
        "description": "Fitbit webhook integration",
        "rate_limit": 1000,
        "role": "user"
    }
]

def create_api_key(device_config):
    """Create an API key for a device"""
    headers = {
        "Authorization": f"Bearer {ADMIN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        ADMIN_API_URL,
        headers=headers,
        json=device_config
    )
    
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print(f"Error creating key for {device_config['name']}: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    print("🔑 Creating API Keys for Biometric Devices")
    print("=" * 50)
    
    created_keys = []
    
    for device in DEVICES:
        print(f"\nCreating key for {device['name']}...")
        result = create_api_key(device)
        
        if result:
            created_keys.append({
                "device": device['name'],
                "api_key": result['api_key'],
                "key_id": result['key_id'],
                "description": device['description']
            })
            print(f"✅ Created: {result['api_key'][:20]}...")
        else:
            print(f"❌ Failed to create key for {device['name']}")
    
    # Save results
    if created_keys:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"device_api_keys_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(created_keys, f, indent=2)
        
        print(f"\n✅ Saved {len(created_keys)} API keys to {filename}")
        print("\n🔐 API Keys Summary:")
        print("-" * 80)
        for key_info in created_keys:
            print(f"{key_info['device']:<20} | {key_info['api_key']}")
        print("-" * 80)
        print("\n⚠️  IMPORTANT: Store these keys securely in CREDENTIALS_VAULT.md")

if __name__ == "__main__":
    main() 