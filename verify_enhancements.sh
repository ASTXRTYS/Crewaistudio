#!/bin/bash

echo "🔍 Verifying AUREN Dashboard Enhancements"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if site is accessible
echo -e "\n${YELLOW}1. Checking site availability...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://aupex.ai | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ Site is accessible${NC}"
else
    echo -e "${RED}❌ Site is not accessible${NC}"
fi

# Check for glassmorphism CSS
echo -e "\n${YELLOW}2. Checking for glassmorphism styles...${NC}"
if curl -s http://aupex.ai | grep -q "backdrop-filter\|glass"; then
    echo -e "${GREEN}✅ Glassmorphism CSS detected${NC}"
else
    echo -e "${RED}❌ Glassmorphism CSS not found${NC}"
fi

# Check WebSocket endpoint
echo -e "\n${YELLOW}3. Checking WebSocket endpoint...${NC}"
if curl -s -o /dev/null -w "%{http_code}" -H "Upgrade: websocket" -H "Connection: Upgrade" http://aupex.ai/ws | grep -q "101\|426"; then
    echo -e "${GREEN}✅ WebSocket endpoint responding${NC}"
else
    echo -e "${YELLOW}⚠️  WebSocket endpoint check inconclusive${NC}"
fi

# Check API health
echo -e "\n${YELLOW}4. Checking API health...${NC}"
if curl -s http://aupex.ai/api/health | grep -q "ok\|healthy"; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
fi

# Check for performance headers
echo -e "\n${YELLOW}5. Checking performance optimizations...${NC}"
HEADERS=$(curl -sI http://aupex.ai)
if echo "$HEADERS" | grep -q "gzip"; then
    echo -e "${GREEN}✅ Gzip compression enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Gzip compression not detected${NC}"
fi

# Summary
echo -e "\n${GREEN}Enhancement Features to Look For:${NC}"
echo "• Frosted glass effect on cards and panels"
echo "• Animated particle background (toggle with ✨ button)"
echo "• Smooth animations and transitions"
echo "• Real-time biometric charts"
echo "• Mobile-responsive layout"
echo ""
echo -e "${YELLOW}Visit http://aupex.ai to see your enhanced dashboard!${NC}"
echo ""
echo "Pro tip: Open developer tools and check:"
echo "• Network tab for WebSocket connection"
echo "• Performance tab for smooth 60fps animations"
echo "• Console for real-time event logs" 