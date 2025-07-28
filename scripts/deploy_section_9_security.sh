#!/bin/bash
# =============================================================================
# SECTION 9 SECURITY ENHANCEMENT DEPLOYMENT SCRIPT
# =============================================================================
# This script deploys the security enhancement layer to the AUREN biometric system
# Created: 2025-01-28
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}SECTION 9: SECURITY ENHANCEMENT LAYER DEPLOYMENT${NC}"
echo -e "${GREEN}==============================================================================${NC}"

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASSWORD='.HvddX+@6dArsKd'
DEPLOY_PATH="/opt/auren_deploy"

# Function to execute remote commands
remote_exec() {
    sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "$1"
}

# Function to copy files to server
remote_copy() {
    sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no "$1" root@$SERVER_IP:"$2"
}

echo -e "\n${YELLOW}Step 1: Checking server connectivity...${NC}"
if remote_exec "echo 'Connected successfully'"; then
    echo -e "${GREEN}✅ Server connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to server${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 2: Creating deployment directory...${NC}"
remote_exec "mkdir -p $DEPLOY_PATH/app $DEPLOY_PATH/migrations"

echo -e "\n${YELLOW}Step 3: Copying security module...${NC}"
remote_copy "app/section_9_security.py" "$DEPLOY_PATH/app/"
echo -e "${GREEN}✅ Security module copied${NC}"

echo -e "\n${YELLOW}Step 4: Copying migration script...${NC}"
remote_copy "migrations/add_security_tables.sql" "$DEPLOY_PATH/migrations/"
echo -e "${GREEN}✅ Migration script copied${NC}"

echo -e "\n${YELLOW}Step 5: Copying admin key creation script...${NC}"
remote_copy "scripts/create_initial_admin_key.py" "$DEPLOY_PATH/"
echo -e "${GREEN}✅ Admin key script copied${NC}"

echo -e "\n${YELLOW}Step 6: Creating environment file with security credentials...${NC}"
cat > /tmp/security.env << EOF
# Security Enhancement Environment Variables
PHI_MASTER_KEY=OIixes55QW8WL7ky0Q7HDHYRTwKld8U0kQvrZnFrRhA=
REDIS_URL=redis://localhost:6379

# Webhook Secrets (comma-separated for rotation)
OURA_WEBHOOK_SECRET=f62f68881a767d70e68c33ea6838ee30cc184236fe246eea2949d8e0b0e8a90f,48472b2ac542d7a09be5aaff871de00a82ca44afe29caa520281d0d57afe25f0
WHOOP_WEBHOOK_SECRET=3cffe8ff206c9981ae10dab70fd99c40d7d107cbe25e5afdc2406b0b2512334c,2078799b92d7ac64a9b5fa85e1f4c4b484fea3dec3af470ebe9109f9bedfbeda
APPLEHEALTH_WEBHOOK_SECRET=4251ed6108a8834e62447fb7565dd1da313135b2e6f5f8dd0cd03f9681583528,bf5b6cea694d0c9fabd5f1cfceb641e8de63835ab5db483fed183c386cde109f
GARMIN_WEBHOOK_SECRET=b1d9c59063acb8c36d8050ab996c43613186a92917de0715c57f9e3ece4ad6c1,b62003b2a4ba2155b00ab4f37070dffde052f0b45e45af2e3a24795d36dc00a2
FITBIT_WEBHOOK_SECRET=15e94fccfc0f657c533c4e9271bad165ccf30275797de585c2d2ac2aa64455cd,d46540be4c4f9f6f01be90bce89caa1895deda4715bcc579578682079ac0f9fa

# Database URL for security tables
DATABASE_URL=postgresql://auren_user:auren_secure_2025@localhost/auren_production
EOF

remote_copy "/tmp/security.env" "$DEPLOY_PATH/"
rm /tmp/security.env
echo -e "${GREEN}✅ Environment file created${NC}"

echo -e "\n${YELLOW}Step 7: Running database migration...${NC}"
remote_exec "cd $DEPLOY_PATH && docker exec -i auren-postgres psql -U auren_user -d auren_production < migrations/add_security_tables.sql"
echo -e "${GREEN}✅ Database migration completed${NC}"

echo -e "\n${YELLOW}Step 8: Installing Python dependencies...${NC}"
remote_exec "docker exec biometric-system-100 pip install ulid-py redis passlib slowapi structlog cryptography"
echo -e "${GREEN}✅ Dependencies installed${NC}"

echo -e "\n${YELLOW}Step 9: Creating initial admin API key...${NC}"
echo -e "${YELLOW}Running key generation script...${NC}"

# Execute the admin key creation script
ADMIN_KEY_OUTPUT=$(remote_exec "cd $DEPLOY_PATH && source security.env && python3 create_initial_admin_key.py" 2>&1)

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Admin API key created successfully!${NC}"
    echo -e "\n${YELLOW}Admin Key Details:${NC}"
    echo "$ADMIN_KEY_OUTPUT" | grep -E "(Key ID:|API Key:|Role:|User ID:|Authorization:)"
    
    # Extract the API key for documentation
    API_KEY=$(echo "$ADMIN_KEY_OUTPUT" | grep "API Key:" | awk '{print $3}')
    KEY_ID=$(echo "$ADMIN_KEY_OUTPUT" | grep "Key ID:" | awk '{print $3}')
    
    echo -e "\n${YELLOW}⚠️  IMPORTANT: Save these credentials in CREDENTIALS_VAULT.md${NC}"
else
    echo -e "${RED}❌ Failed to create admin API key${NC}"
    echo "$ADMIN_KEY_OUTPUT"
fi

echo -e "\n${YELLOW}Step 10: Testing security endpoints...${NC}"

# Test health endpoint (should still be public)
echo -e "${YELLOW}Testing public health endpoint...${NC}"
if remote_exec "curl -s http://localhost:8888/health"; then
    echo -e "${GREEN}✅ Health endpoint accessible${NC}"
fi

# Test admin endpoint without auth (should fail)
echo -e "\n${YELLOW}Testing admin endpoint without auth (should fail)...${NC}"
HTTP_CODE=$(remote_exec "curl -s -o /dev/null -w '%{http_code}' http://localhost:8888/admin/api-keys" || echo "000")
if [[ "$HTTP_CODE" == "401" ]]; then
    echo -e "${GREEN}✅ Admin endpoint properly secured (401 Unauthorized)${NC}"
else
    echo -e "${RED}⚠️  Unexpected response code: $HTTP_CODE${NC}"
fi

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}DEPLOYMENT SUMMARY${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "✅ Security module deployed"
echo -e "✅ Database migration completed"
echo -e "✅ Environment variables configured"
echo -e "✅ Initial admin API key created"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Update CREDENTIALS_VAULT.md with the admin API key"
echo -e "2. Test the admin endpoints using: curl -H 'Authorization: Bearer $API_KEY' http://$SERVER_IP:8888/admin/api-keys"
echo -e "3. Create additional API keys for users"
echo -e "4. Monitor audit logs at http://$SERVER_IP:8888/admin/audit-logs"
echo -e "\n${YELLOW}Integration Notes:${NC}"
echo -e "- The existing biometric system will need to be updated to use the security module"
echo -e "- All webhook endpoints now require signature verification"
echo -e "- All API endpoints (except health) now require authentication"
echo -e "${GREEN}==============================================================================${NC}" 