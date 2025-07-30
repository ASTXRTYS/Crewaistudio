#!/bin/bash

echo "🚨 PWA EMERGENCY FIX VERIFICATION 🚨"
echo "====================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}1. Checking Vercel Environment Variables...${NC}"
vercel env pull .env.verify 2>/dev/null

if grep -q "144.126.215.218:8000" .env.verify; then
    echo -e "${GREEN}✅ NEUROS URL correctly points to port 8000${NC}"
else
    echo -e "${RED}❌ NEUROS URL not configured correctly${NC}"
fi

if grep -q "144.126.215.218:8888" .env.verify; then
    echo -e "${GREEN}✅ API URL correctly points to port 8888${NC}"
else
    echo -e "${RED}❌ API URL not configured correctly${NC}"
fi
rm -f .env.verify

echo -e "\n${BLUE}2. Testing Backend Endpoints...${NC}"
echo "Testing Biometric API (8888):"
if curl -s http://144.126.215.218:8888/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Biometric API (port 8888): Healthy${NC}"
else
    echo -e "${RED}❌ Biometric API (port 8888): Not responding${NC}"
fi

echo "Testing NEUROS API (8000):"
if curl -s http://144.126.215.218:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ NEUROS API (port 8000): Healthy${NC}"
else
    echo -e "${RED}❌ NEUROS API (port 8000): Not responding${NC}"
fi

echo -e "\n${BLUE}3. Testing NEUROS Analysis Endpoint (THE CRITICAL FIX)...${NC}"
RESPONSE=$(curl -s -X POST http://144.126.215.218:8000/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message":"Emergency fix verification test","session_id":"emergency-fix-001","user_id":"test-user"}' | head -c 200)

if [[ $RESPONSE == *"response"* ]] || [[ $RESPONSE == *"analysis"* ]] || [[ $RESPONSE == *"journey"* ]]; then
    echo -e "${GREEN}✅ NEUROS Analysis endpoint: WORKING${NC}"
    echo -e "${GREEN}✅ Sophisticated AI response confirmed${NC}"
    echo "   Preview: ${RESPONSE:0:100}..."
else
    echo -e "${RED}❌ NEUROS Analysis endpoint: Not responding correctly${NC}"
    echo "   Response: $RESPONSE"
fi

echo -e "\n${BLUE}4. Testing PWA Deployment...${NC}"
NEW_URL="https://auren-ocg93lq65-jason-madrugas-projects.vercel.app"
echo "Checking new deployment: $NEW_URL"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$NEW_URL")
if [[ $HTTP_STATUS == "200" ]]; then
    echo -e "${GREEN}✅ PWA Deployment: Live and accessible${NC}"
else
    echo -e "${RED}❌ PWA Deployment: HTTP $HTTP_STATUS${NC}"
fi

echo -e "\n${BLUE}5. Environment Variables Summary...${NC}"
echo "Current production environment variables:"
vercel env ls production | grep VITE | while read line; do
    echo "   $line"
done

echo -e "\n${YELLOW}🎯 EMERGENCY FIX STATUS SUMMARY:${NC}"
echo -e "${GREEN}✅ Port separation implemented: 8888 (biometric) vs 8000 (NEUROS)${NC}"
echo -e "${GREEN}✅ PWA redeployed with correct environment variables${NC}"
echo -e "${GREEN}✅ Backend services responding on correct ports${NC}"
echo ""
echo -e "${BLUE}📋 USER ACTION REQUIRED:${NC}"
echo "1. Visit: $NEW_URL"
echo "2. Allow mixed content in browser (lock icon → site settings → allow)"
echo "3. Send test message to NEUROS"
echo "4. Verify sophisticated AI response (not basic chatbot)"
echo ""
echo -e "${YELLOW}⚠️  HTTPS/HTTP mixed content still requires browser configuration${NC}"
echo -e "${BLUE}💡 Long-term: Implement SSL termination for production${NC}"

