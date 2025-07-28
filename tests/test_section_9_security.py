#!/usr/bin/env python3
"""
Test Suite for Section 9 Security Enhancement Layer
Tests API key management, PHI encryption, rate limiting, and webhook security
"""

import os
import sys
import asyncio
import pytest
import time
import hmac
import hashlib
import json
import base64
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from section_9_security import (
    APIKeyManager,
    PHIEncryption,
    HIPAAAuditLogger,
    AdaptiveRateLimiter,
    require_webhook_signature,
    RequestIDMiddleware,
    AuthMiddleware,
    get_authenticated_user_id,
    encrypt_phi_field,
    decrypt_phi_field
)

import asyncpg
import redis
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


class TestAPIKeyManagement:
    """Test API key management functionality"""
    
    @pytest.fixture
    async def setup(self):
        """Setup test database and Redis connections"""
        # Use test database
        db_pool = await asyncpg.create_pool(
            "postgresql://auren_user:auren_secure_2025@localhost/auren_test",
            min_size=1,
            max_size=5
        )
        
        # Use test Redis database
        redis_client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        
        # Clear test data
        redis_client.flushdb()
        
        # Create API key manager
        api_key_manager = APIKeyManager(db_pool, redis_client)
        
        yield api_key_manager, db_pool, redis_client
        
        # Cleanup
        await db_pool.close()
        redis_client.close()
    
    @pytest.mark.asyncio
    async def test_create_api_key(self, setup):
        """Test API key creation"""
        api_key_manager, _, _ = setup
        
        # Create a new API key
        result = await api_key_manager.create_api_key(
            user_id="test_user",
            description="Test API key",
            role="user",
            created_by="test",
            rate_limit=60
        )
        
        assert "key_id" in result
        assert "api_key" in result
        assert result["api_key"].startswith("auren_")
        assert result["user_id"] == "test_user"
        assert result["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_verify_api_key(self, setup):
        """Test API key verification with O(1) lookup"""
        api_key_manager, _, redis_client = setup
        
        # Create a key
        result = await api_key_manager.create_api_key(
            user_id="test_user",
            description="Test key",
            role="admin"
        )
        
        api_key = result["api_key"]
        
        # Verify the key
        start_time = time.time()
        key_info = await api_key_manager.verify_api_key(api_key)
        lookup_time = time.time() - start_time
        
        assert key_info is not None
        assert key_info["user_id"] == "test_user"
        assert key_info["role"] == "admin"
        assert lookup_time < 0.01  # Should be very fast (< 10ms)
        
        # Verify caching works
        cached_key = f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        assert redis_client.exists(cached_key)
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, setup):
        """Test invalid API key rejection"""
        api_key_manager, _, _ = setup
        
        # Test invalid key
        key_info = await api_key_manager.verify_api_key("invalid_key")
        assert key_info is None
        
        # Test key with wrong prefix
        key_info = await api_key_manager.verify_api_key("wrong_prefix_abc123")
        assert key_info is None
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self, setup):
        """Test API key revocation"""
        api_key_manager, _, _ = setup
        
        # Create and then revoke a key
        result = await api_key_manager.create_api_key(
            user_id="test_user",
            description="To be revoked"
        )
        
        key_id = result["key_id"]
        api_key = result["api_key"]
        
        # Revoke the key
        success = await api_key_manager.revoke_api_key(key_id, "test_admin")
        assert success is True
        
        # Verify revoked key cannot be used
        key_info = await api_key_manager.verify_api_key(api_key)
        assert key_info is None


class TestPHIEncryption:
    """Test PHI encryption functionality"""
    
    @pytest.fixture
    async def setup(self):
        """Setup test encryption"""
        db_pool = await asyncpg.create_pool(
            "postgresql://auren_user:auren_secure_2025@localhost/auren_test",
            min_size=1,
            max_size=5
        )
        
        # Use test master key
        master_key = base64.b64decode("OIixes55QW8WL7ky0Q7HDHYRTwKld8U0kQvrZnFrRhA=")
        phi_encryption = PHIEncryption(master_key, db_pool)
        
        yield phi_encryption, db_pool
        
        await db_pool.close()
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_phi(self, setup):
        """Test PHI encryption and decryption"""
        phi_encryption, _ = setup
        
        # Test data
        sensitive_data = "Heart Rate: 72 bpm"
        context = "user_123"
        
        # Encrypt
        encrypted = await phi_encryption.encrypt_phi(sensitive_data, context)
        
        assert "ciphertext" in encrypted
        assert "nonce" in encrypted
        assert "tag" in encrypted
        assert encrypted["ciphertext"] != sensitive_data
        
        # Decrypt
        decrypted = await phi_encryption.decrypt_phi(encrypted, context)
        assert decrypted == sensitive_data
    
    @pytest.mark.asyncio
    async def test_encryption_with_different_contexts(self, setup):
        """Test that different contexts produce different ciphertexts"""
        phi_encryption, _ = setup
        
        data = "Blood Pressure: 120/80"
        
        # Encrypt with different contexts
        encrypted1 = await phi_encryption.encrypt_phi(data, "user_1")
        encrypted2 = await phi_encryption.encrypt_phi(data, "user_2")
        
        # Ciphertexts should be different
        assert encrypted1["ciphertext"] != encrypted2["ciphertext"]
        
        # But both should decrypt correctly with their contexts
        assert await phi_encryption.decrypt_phi(encrypted1, "user_1") == data
        assert await phi_encryption.decrypt_phi(encrypted2, "user_2") == data
    
    @pytest.mark.asyncio
    async def test_key_caching_performance(self, setup):
        """Test that key derivation caching improves performance"""
        phi_encryption, _ = setup
        
        # First encryption (cold cache)
        start = time.time()
        for i in range(100):
            await phi_encryption.encrypt_phi(f"Data {i}", "same_context")
        cold_time = time.time() - start
        
        # Second batch (warm cache)
        start = time.time()
        for i in range(100):
            await phi_encryption.encrypt_phi(f"Data {i}", "same_context")
        warm_time = time.time() - start
        
        # Warm cache should be significantly faster
        assert warm_time < cold_time * 0.5  # At least 50% faster


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @pytest.fixture
    def setup(self):
        """Setup test rate limiter"""
        redis_client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        redis_client.flushdb()
        
        rate_limiter = AdaptiveRateLimiter(redis_client)
        
        yield rate_limiter, redis_client
        
        redis_client.close()
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, setup):
        """Test that rate limits are enforced"""
        rate_limiter, _ = setup
        
        key_id = "test_key"
        limit = 5
        
        # Make requests up to the limit
        for i in range(limit):
            allowed, remaining = await rate_limiter.check_rate_limit(key_id, limit)
            assert allowed is True
            assert remaining == limit - i - 1
        
        # Next request should be blocked
        allowed, remaining = await rate_limiter.check_rate_limit(key_id, limit)
        assert allowed is False
        assert remaining == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_reset(self, setup):
        """Test that rate limits reset after window expires"""
        rate_limiter, redis_client = setup
        
        key_id = "test_key_2"
        limit = 3
        
        # Use up the limit
        for _ in range(limit):
            await rate_limiter.check_rate_limit(key_id, limit)
        
        # Should be blocked now
        allowed, _ = await rate_limiter.check_rate_limit(key_id, limit)
        assert allowed is False
        
        # Simulate time passing by clearing the key
        redis_client.delete(f"rate_limit:{key_id}")
        
        # Should be allowed again
        allowed, remaining = await rate_limiter.check_rate_limit(key_id, limit)
        assert allowed is True
        assert remaining == limit - 1
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self, setup):
        """Test that rate limiting is race-proof under concurrent access"""
        rate_limiter, _ = setup
        
        key_id = "concurrent_test"
        limit = 10
        
        # Simulate concurrent requests
        async def make_request():
            return await rate_limiter.check_rate_limit(key_id, limit)
        
        # Run many concurrent requests
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Count allowed requests
        allowed_count = sum(1 for allowed, _ in results if allowed)
        
        # Should allow exactly the limit
        assert allowed_count == limit


class TestWebhookSecurity:
    """Test webhook signature verification"""
    
    def test_webhook_signature_generation(self):
        """Test webhook signature generation"""
        secret = "test_secret_key"
        timestamp = str(int(time.time()))
        body = '{"event": "heart_rate", "value": 72}'
        
        # Generate signature
        message = f"{timestamp}.{body}"
        expected_sig = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify format
        assert len(expected_sig) == 64  # SHA-256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in expected_sig)
    
    @pytest.mark.asyncio
    async def test_webhook_replay_protection(self):
        """Test that replay attacks are prevented"""
        # This would require a full FastAPI app setup
        # Simplified test showing the concept
        
        db_pool = await asyncpg.create_pool(
            "postgresql://auren_user:auren_secure_2025@localhost/auren_test",
            min_size=1,
            max_size=5
        )
        
        signature_hash = hashlib.sha256(b"test_signature").hexdigest()
        timestamp = int(time.time())
        
        # First insertion should succeed
        try:
            await db_pool.execute("""
                INSERT INTO webhook_replay_protection (signature_hash, timestamp)
                VALUES ($1, $2)
            """, signature_hash, timestamp)
            first_insert = True
        except asyncpg.UniqueViolationError:
            first_insert = False
        
        assert first_insert is True
        
        # Second insertion should fail (replay attack)
        try:
            await db_pool.execute("""
                INSERT INTO webhook_replay_protection (signature_hash, timestamp)
                VALUES ($1, $2)
            """, signature_hash, timestamp)
            second_insert = True
        except asyncpg.UniqueViolationError:
            second_insert = False
        
        assert second_insert is False
        
        await db_pool.close()


class TestAuditLogging:
    """Test HIPAA-compliant audit logging"""
    
    @pytest.fixture
    async def setup(self):
        """Setup test audit logger"""
        db_pool = await asyncpg.create_pool(
            "postgresql://auren_user:auren_secure_2025@localhost/auren_test",
            min_size=1,
            max_size=5
        )
        
        audit_logger = HIPAAAuditLogger(db_pool)
        
        yield audit_logger, db_pool
        
        await db_pool.close()
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self, setup):
        """Test that audit logs are created correctly"""
        audit_logger, db_pool = setup
        
        # Create a mock request
        class MockRequest:
            class State:
                request_id = "test_request_123"
            
            state = State()
            headers = {"user-agent": "Test Agent"}
            client = type('obj', (object,), {'host': '127.0.0.1'})
        
        request = MockRequest()
        
        # Log an access
        await audit_logger.log_access(
            user_id="test_user",
            action="read",
            resource="/api/biometrics",
            request=request,
            response_time_ms=50,
            outcome="success",
            details={"heart_rate": 72},  # Should be masked
            api_key_id="test_key"
        )
        
        # Verify log was created
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM phi_audit_log 
                WHERE request_id = 'test_request_123'
            """)
            
            assert row is not None
            assert row['user_id'] == "test_user"
            assert row['action'] == "read"
            assert row['outcome'] == "success"
            
            # Check PHI was masked
            details = json.loads(row['details'])
            assert details['heart_rate'] == "***MASKED***"


class TestIntegration:
    """Integration tests for the complete security system"""
    
    @pytest.mark.asyncio
    async def test_full_request_flow(self):
        """Test a complete request flow with all security features"""
        # This would require setting up a full FastAPI app
        # with all middleware and testing the complete flow
        pass


# Test configuration for pytest
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 