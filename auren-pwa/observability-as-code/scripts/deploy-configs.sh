#!/bin/bash
# Deploy observability configurations to production

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="144.126.215.218"
SERVER_PASS=".HvddX+@6dArsKd"
PROJECT_ROOT=$(cd "$(dirname "$0")/../../.." && pwd)

echo -e "${YELLOW}🚀 Deploying Observability Configurations${NC}"
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ File not found: $1${NC}"
        exit 1
    fi
}

# 1. Validate files exist
echo -e "${YELLOW}1. Validating files...${NC}"
check_file "$PROJECT_ROOT/prometheus/rules/kpi-generated.yml"
check_file "$PROJECT_ROOT/prometheus/alerts/kpi-generated.yml"
check_file "$PROJECT_ROOT/grafana/dashboards/kpi-generated.json"
echo -e "${GREEN}✅ All files found${NC}"
echo ""

# 2. Copy files to server
echo -e "${YELLOW}2. Copying files to server...${NC}"

# Copy Prometheus rules
echo "   Copying recording rules..."
sshpass -p "$SERVER_PASS" scp "$PROJECT_ROOT/prometheus/rules/kpi-generated.yml" \
    root@${SERVER_IP}:/opt/prometheus/rules/

# Copy Prometheus alerts
echo "   Copying alert rules..."
sshpass -p "$SERVER_PASS" scp "$PROJECT_ROOT/prometheus/alerts/kpi-generated.yml" \
    root@${SERVER_IP}:/opt/prometheus/alerts/

# Copy Grafana dashboard
echo "   Copying dashboard..."
sshpass -p "$SERVER_PASS" scp "$PROJECT_ROOT/grafana/dashboards/kpi-generated.json" \
    root@${SERVER_IP}:/opt/grafana/dashboards/

echo -e "${GREEN}✅ Files copied${NC}"
echo ""

# 3. Reload services
echo -e "${YELLOW}3. Reloading services...${NC}"

# Reload Prometheus
echo "   Reloading Prometheus..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} \
    'curl -s -X POST localhost:9090/-/reload'

# Restart Grafana to pick up new dashboard
echo "   Restarting Grafana..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} \
    'docker restart auren-grafana > /dev/null'

echo -e "${GREEN}✅ Services reloaded${NC}"
echo ""

# 4. Verify deployment
echo -e "${YELLOW}4. Verifying deployment...${NC}"

# Check Prometheus rules
RULES_COUNT=$(sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} \
    'curl -s localhost:9090/api/v1/rules | jq ".data.groups[].rules | length" | paste -sd+ | bc')
echo "   Prometheus rules loaded: $RULES_COUNT"

# Check Grafana
GRAFANA_STATUS=$(sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} \
    'curl -s localhost:3000/api/health | jq -r .database')
if [ "$GRAFANA_STATUS" = "ok" ]; then
    echo -e "   Grafana status: ${GREEN}✅ Healthy${NC}"
else
    echo -e "   Grafana status: ${RED}❌ Unhealthy${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Check Grafana dashboard: http://${SERVER_IP}:3000"
echo "2. Verify metrics: curl http://${SERVER_IP}:8002/api/metrics/catalog | jq"
echo "3. Test alerts: curl http://${SERVER_IP}:9090/api/v1/alerts | jq"