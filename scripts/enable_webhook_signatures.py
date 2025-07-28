#!/usr/bin/env python3
"""
Example script showing how to enable webhook signatures on biometric endpoints
This demonstrates the integration needed for Section 9 security
"""

print("""
🔐 WEBHOOK SIGNATURE INTEGRATION GUIDE
=====================================

To enable webhook signatures on the biometric system, the following changes
are needed in the biometric API code:

1. IMPORT THE SECURITY MODULE
-----------------------------
In auren/biometric/api.py, add:

```python
from app.section_9_security import require_webhook_signature
```

2. ADD WEBHOOK SECRETS TO ENVIRONMENT
-------------------------------------
The following webhook secrets are available in CREDENTIALS_VAULT.md:

- OURA_WEBHOOK_SECRET: oura_secret_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
- WHOOP_WEBHOOK_SECRET: whoop_secret_q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
- APPLE_WEBHOOK_SECRET: apple_secret_g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8
- GARMIN_WEBHOOK_SECRET: garmin_secret_w9x0y1z2a3b4c5d6e7f8g9h0i1j2k3l4
- FITBIT_WEBHOOK_SECRET: fitbit_secret_m5n6o7p8q9r0s1t2u3v4w5x6y7z8a9b0

3. APPLY DECORATORS TO WEBHOOK ENDPOINTS
----------------------------------------
Update each webhook endpoint with the signature verification:

```python
# Oura webhook
@router.post("/webhooks/oura")
@require_webhook_signature(
    secret_env_var="OURA_WEBHOOK_SECRET",
    header_name="X-Oura-Signature"
)
async def handle_oura_webhook(
    request: Request,
    body: dict = Body(...)
):
    # Existing webhook logic
    pass

# WHOOP webhook  
@router.post("/webhooks/whoop")
@require_webhook_signature(
    secret_env_var="WHOOP_WEBHOOK_SECRET",
    header_name="X-WHOOP-Signature"
)
async def handle_whoop_webhook(
    request: Request,
    body: dict = Body(...)
):
    # Existing webhook logic
    pass

# Apple HealthKit webhook
@router.post("/webhooks/apple")
@require_webhook_signature(
    secret_env_var="APPLE_WEBHOOK_SECRET",
    header_name="X-Apple-Signature"
)
async def handle_apple_webhook(
    request: Request,
    body: dict = Body(...)
):
    # Existing webhook logic
    pass

# Garmin webhook
@router.post("/webhooks/garmin")  
@require_webhook_signature(
    secret_env_var="GARMIN_WEBHOOK_SECRET",
    header_name="X-Garmin-Signature"
)
async def handle_garmin_webhook(
    request: Request,
    body: dict = Body(...)
):
    # Existing webhook logic
    pass

# Fitbit webhook
@router.post("/webhooks/fitbit")
@require_webhook_signature(
    secret_env_var="FITBIT_WEBHOOK_SECRET",
    header_name="X-Fitbit-Signature"
)
async def handle_fitbit_webhook(
    request: Request,
    body: dict = Body(...)
):
    # Existing webhook logic
    pass
```

4. CONFIGURE DEVICE PROVIDERS
-----------------------------
Each device provider needs to be configured with their webhook secret:

OURA:
- Login to Oura Cloud API dashboard
- Navigate to Webhook Settings
- Set Secret: oura_secret_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
- Enable HMAC-SHA256 signatures

WHOOP:
- Access WHOOP Developer Portal
- Go to App Settings > Webhooks
- Set Signing Secret: whoop_secret_q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
- Save changes

APPLE HEALTHKIT:
- In Apple Developer Console
- Configure webhook endpoint security
- Add secret: apple_secret_g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8

GARMIN:
- Garmin Connect Developer site
- Webhook configuration
- Set HMAC secret: garmin_secret_w9x0y1z2a3b4c5d6e7f8g9h0i1j2k3l4

FITBIT:
- Fitbit Web API settings
- Subscriber verification
- Configure secret: fitbit_secret_m5n6o7p8q9r0s1t2u3v4w5x6y7z8a9b0

5. TEST WEBHOOK SIGNATURES
--------------------------
Use this curl command to test signature verification:

```bash
# Generate test signature
PAYLOAD='{"test": "data"}'
SECRET="oura_secret_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
TIMESTAMP=$(date +%s)
SIGNATURE=$(echo -n "${TIMESTAMP}.${PAYLOAD}" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)

# Send test webhook
curl -X POST http://144.126.215.218:8888/webhooks/oura \\
  -H "Content-Type: application/json" \\
  -H "X-Oura-Signature: ${SIGNATURE}" \\
  -H "X-Oura-Timestamp: ${TIMESTAMP}" \\
  -d '${PAYLOAD}'
```

IMPORTANT NOTES:
===============
- Webhook signatures prevent replay attacks and verify authenticity
- Each provider may use different header names (check their docs)
- Signatures typically include timestamp to prevent replay
- Store secrets securely (already in CREDENTIALS_VAULT.md)
- Test thoroughly before enabling in production

This integration is part of Section 9 Security Enhancement Layer.
""") 