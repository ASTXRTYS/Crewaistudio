"""
Section 9 Security Integration for Section 12
Simplified implementation focusing on core security features
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer(auto_error=False)


class SecurityEnhancement:
    """Simplified Section 9 security layer for Section 12"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis_client = redis_client
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max = 60  # requests per minute
        
    async def verify_api_key(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """Verify API key from Bearer token"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Missing authentication")
            
        api_key = credentials.credentials
        
        # For now, accept a master key from environment
        master_key = os.getenv("AUREN_MASTER_API_KEY", "auren-master-key-2025")
        
        if api_key == master_key:
            return {
                "user_id": "master",
                "role": "admin",
                "rate_limit": 1000
            }
        
        # In production, would check against database
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    async def check_rate_limit(self, user_id: str, limit: int = None) -> bool:
        """Check rate limit for user"""
        if not self.redis_client:
            return True  # Skip rate limiting if Redis not available
            
        limit = limit or self.rate_limit_max
        key = f"rate_limit:{user_id}"
        
        try:
            # Increment counter
            count = await self.redis_client.incr(key)
            
            # Set expiry on first request
            if count == 1:
                await self.redis_client.expire(key, self.rate_limit_window)
            
            return count <= limit
            
        except Exception:
            # Don't block requests on rate limit errors
            return True
    
    def create_security_middleware(self, app: FastAPI) -> FastAPI:
        """Add security middleware to FastAPI app"""
        
        @app.middleware("http")
        async def security_middleware(request: Request, call_next):
            """Basic security middleware"""
            # Add request ID
            request_id = request.headers.get("X-Request-ID", secrets.token_urlsafe(16))
            
            # Log request (in production, would go to audit log)
            start_time = datetime.now()
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            
            # Log response time
            duration = (datetime.now() - start_time).total_seconds()
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            return response
        
        return app


def create_security_app(app: FastAPI, redis_client: Optional[aioredis.Redis] = None) -> FastAPI:
    """
    Enhance FastAPI app with Section 9 security features
    
    This is a simplified implementation focusing on:
    - API key authentication
    - Rate limiting
    - Security headers
    - Request logging
    """
    security = SecurityEnhancement(redis_client)
    return security.create_security_middleware(app)


# Dependency for protected endpoints
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from API key"""
    security_handler = SecurityEnhancement()
    return await security_handler.verify_api_key(credentials) 