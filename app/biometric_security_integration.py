#!/usr/bin/env python3
"""
=============================================================================
BIOMETRIC SYSTEM WITH SECTION 9 SECURITY INTEGRATION
=============================================================================
This example shows how to integrate the Section 9 security enhancement layer
with an existing biometric system. It demonstrates:
1. Adding authentication middleware
2. Implementing webhook signature verification
3. Encrypting PHI data
4. Audit logging
5. Rate limiting
=============================================================================
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from contextlib import asynccontextmanager
import os

# Import Section 9 security components
from section_9_security import (
    AuthMiddleware,
    RequestIDMiddleware,
    admin_router,
    require_webhook_signature,
    encrypt_phi_field,
    decrypt_phi_field,
    get_authenticated_user_id,
    lifespan as security_lifespan,
    get_audit_logger,
    get_rate_limiter,
    get_phi_encryption
)

# =============================================================================
# ENHANCED BIOMETRIC SYSTEM WITH SECURITY
# =============================================================================

# Create FastAPI app with security lifespan
app = FastAPI(
    title="AUREN Biometric System",
    description="Biometric processing with enterprise security",
    version="3.0.0",
    lifespan=security_lifespan  # Use security lifespan for initialization
)

# =============================================================================
# MIDDLEWARE CONFIGURATION (Order matters!)
# =============================================================================

# 1. Request ID middleware must come first
app.add_middleware(RequestIDMiddleware)

# 2. Authentication middleware
app.add_middleware(AuthMiddleware)

# 3. Include admin routes
app.include_router(admin_router)

# =============================================================================
# EXAMPLE: SECURED WEBHOOK ENDPOINT
# =============================================================================

@app.post("/webhooks/{device_type}")
@require_webhook_signature("{device_type}")  # Add signature verification
async def receive_webhook(
    device_type: str,
    request: Request,
    audit_logger = Depends(get_audit_logger)
):
    """
    Secured webhook endpoint with:
    - Signature verification (via decorator)
    - Authentication (via middleware)
    - Audit logging
    """
    # Get authenticated user from request state
    user_id = get_authenticated_user_id(request)
    
    # Get webhook body (already verified by decorator)
    body = await request.body()
    
    # Log the webhook receipt
    await audit_logger.log_access(
        user_id=user_id,
        action="webhook_received",
        resource=f"/webhooks/{device_type}",
        request=request,
        outcome="success",
        details={
            "device_type": device_type,
            "body_size": len(body)
        }
    )
    
    # Process webhook data...
    # (Your existing webhook processing logic here)
    
    return {"status": "received", "device": device_type}

# =============================================================================
# EXAMPLE: BIOMETRIC DATA ENDPOINT WITH PHI ENCRYPTION
# =============================================================================

@app.post("/api/biometrics/heart-rate")
async def store_heart_rate(
    request: Request,
    heart_rate: int,
    timestamp: str,
    phi_encryption = Depends(get_phi_encryption),
    audit_logger = Depends(get_audit_logger),
    rate_limiter = Depends(get_rate_limiter)
):
    """
    Store heart rate data with:
    - PHI encryption
    - Rate limiting
    - Audit logging
    """
    # Get user context
    user_id = get_authenticated_user_id(request)
    api_key_id = request.state.api_key_id
    rate_limit = request.state.rate_limit
    
    # Check rate limit
    allowed, remaining = await rate_limiter.check_rate_limit(api_key_id, rate_limit)
    if not allowed:
        await audit_logger.log_access(
            user_id=user_id,
            api_key_id=api_key_id,
            action="create",
            resource="/api/biometrics/heart-rate",
            request=request,
            outcome="rate_limited"
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limit),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "60"
            }
        )
    
    # Encrypt PHI data
    encrypted_hr = await encrypt_phi_field(heart_rate, user_id)
    
    # Store encrypted data in database
    # ... your database storage logic here ...
    
    # Log successful access
    await audit_logger.log_access(
        user_id=user_id,
        api_key_id=api_key_id,
        action="create",
        resource="/api/biometrics/heart-rate",
        request=request,
        outcome="success",
        details={
            "timestamp": timestamp,
            # Don't log actual heart rate (PHI)
        }
    )
    
    return {
        "status": "stored",
        "encrypted": True,
        "rate_limit_remaining": remaining
    }

# =============================================================================
# EXAMPLE: RETRIEVING ENCRYPTED PHI DATA
# =============================================================================

@app.get("/api/biometrics/heart-rate/{record_id}")
async def get_heart_rate(
    record_id: str,
    request: Request,
    phi_encryption = Depends(get_phi_encryption),
    audit_logger = Depends(get_audit_logger)
):
    """Retrieve and decrypt heart rate data"""
    user_id = get_authenticated_user_id(request)
    
    # Fetch encrypted data from database
    # encrypted_data = fetch_from_db(record_id)
    # For this example:
    encrypted_data = {
        "ciphertext": "example_encrypted_data",
        "nonce": "example_nonce",
        "tag": "example_tag"
    }
    
    # Decrypt PHI data
    try:
        heart_rate = await decrypt_phi_field(encrypted_data, user_id)
        
        # Log successful access
        await audit_logger.log_access(
            user_id=user_id,
            api_key_id=request.state.api_key_id,
            action="read",
            resource="/api/biometrics/heart-rate",
            resource_id=record_id,
            request=request,
            outcome="success"
        )
        
        return {
            "record_id": record_id,
            "heart_rate": heart_rate,
            "decrypted": True
        }
        
    except Exception as e:
        # Log failed access
        await audit_logger.log_access(
            user_id=user_id,
            api_key_id=request.state.api_key_id,
            action="read",
            resource="/api/biometrics/heart-rate",
            resource_id=record_id,
            request=request,
            outcome="error",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Decryption failed")

# =============================================================================
# EXAMPLE: HEALTH CHECK (PUBLIC ENDPOINT)
# =============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint - remains public (no auth required)
    AuthMiddleware automatically skips this endpoint
    """
    return {
        "status": "healthy",
        "service": "biometric-system",
        "security": "enabled",
        "version": "3.0.0"
    }

# =============================================================================
# MIGRATION GUIDE FOR EXISTING ENDPOINTS
# =============================================================================

"""
To migrate your existing biometric endpoints:

1. Update user_id retrieval:
   OLD: user_id = "test_user"  # or from custom auth
   NEW: user_id = get_authenticated_user_id(request)

2. Add webhook signature verification:
   OLD: @app.post("/webhook")
   NEW: @app.post("/webhook")
        @require_webhook_signature("device_name")

3. Encrypt sensitive data before storage:
   OLD: db.store(user_id, heart_rate)
   NEW: encrypted = await encrypt_phi_field(heart_rate, user_id)
        db.store(user_id, encrypted)

4. Add audit logging:
   NEW: await audit_logger.log_access(
            user_id=user_id,
            action=request.method.lower(),
            resource=request.url.path,
            request=request,
            outcome="success"
        )

5. Check rate limits in high-volume endpoints:
   NEW: allowed, remaining = await rate_limiter.check_rate_limit(
            request.state.api_key_id,
            request.state.rate_limit
        )
        if not allowed:
            raise HTTPException(429, "Rate limit exceeded")

6. Update your deployment:
   - Run the database migration
   - Set environment variables
   - Create initial admin API key
   - Update clients to use Bearer tokens
"""

# =============================================================================
# EXAMPLE: CUSTOM DEPENDENCY FOR ROLE-BASED ACCESS
# =============================================================================

def require_role(required_role: str):
    """Dependency to require specific role"""
    def role_checker(request: Request):
        user_role = getattr(request.state, 'user_role', None)
        if user_role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"{required_role} role required"
            )
        return request.state.user_id
    return role_checker

@app.delete("/api/biometrics/{record_id}")
async def delete_biometric_record(
    record_id: str,
    request: Request,
    admin_user: str = Depends(require_role("admin")),
    audit_logger = Depends(get_audit_logger)
):
    """Delete biometric record - admin only"""
    # Delete logic here...
    
    await audit_logger.log_access(
        user_id=admin_user,
        api_key_id=request.state.api_key_id,
        action="delete",
        resource="/api/biometrics",
        resource_id=record_id,
        request=request,
        outcome="success"
    )
    
    return {"deleted": record_id}

# =============================================================================
# RUNNING THE APPLICATION
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run with security enabled
    uvicorn.run(
        "biometric_security_integration:app",
        host="0.0.0.0",
        port=8888,
        reload=False,  # Disable in production
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    ) 