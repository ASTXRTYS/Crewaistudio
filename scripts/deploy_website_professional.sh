#!/bin/bash
set -e

echo "🚀 PROFESSIONAL WEBSITE DEPLOYMENT"
echo "=================================="
echo "Date: $(date)"
echo "User: $(whoami)"
echo ""

# 1. Validate source files exist
echo "🔍 Validating source files..."
if [ ! -f "auren/dashboard_v2/index.html" ]; then
    echo "❌ ERROR: Source files missing at auren/dashboard_v2/"
    echo "   Expected: auren/dashboard_v2/index.html"
    exit 1
fi

if [ ! -f "auren/dashboard_v2/agents/index.html" ]; then
    echo "❌ ERROR: Agents page missing at auren/dashboard_v2/agents/"
    exit 1
fi

echo "✅ Source files validated"

# 2. Deploy to correct nginx location
echo ""
echo "📤 Deploying to production server..."
echo "Target: /usr/share/nginx/html/"

# Use sshpass for automated deployment
sshpass -p '.HvddX+@6dArsKd' scp -r -o StrictHostKeyChecking=no auren/dashboard_v2/* root@144.126.215.218:/usr/share/nginx/html/

echo "✅ Files uploaded successfully"

# 3. Validate deployment with content verification
echo ""
echo "🔍 Validating deployment (checking live website)..."

# Give nginx a moment to refresh
sleep 2

# Check for expected agents
EXPECTED_AGENTS=("NUTROS" "KINETOS" "HYPERTROS" "CARDIOS" "SOMNOS" "OPTICOS" "ENDOS" "AUREN")
FAILED_AGENTS=()

for agent in "${EXPECTED_AGENTS[@]}"; do
    if curl -s http://aupex.ai/agents/ | grep -q "$agent"; then
        echo "✅ $agent confirmed live"
    else
        echo "❌ $agent missing!"
        FAILED_AGENTS+=("$agent")
    fi
done

# Check for active NEUROS
if curl -s http://aupex.ai/agents/ | grep -q "🧠 NEUROS"; then
    echo "✅ NEUROS (active agent) confirmed with emoji"
else
    echo "❌ NEUROS not showing properly!"
    FAILED_AGENTS+=("NEUROS-EMOJI")
fi

# Final validation
if [ ${#FAILED_AGENTS[@]} -eq 0 ]; then
    echo ""
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "✅ All 9 agents confirmed live at http://aupex.ai/agents/"
    echo "✅ Website deployment completed successfully"
    echo ""
    echo "🔗 Live URLs:"
    echo "   - Agents: http://aupex.ai/agents/"
    echo "   - NEUROS Dashboard: http://aupex.ai/agents/neuroscientist.html"
    exit 0
else
    echo ""
    echo "❌ DEPLOYMENT VALIDATION FAILED!"
    echo "Failed agents: ${FAILED_AGENTS[*]}"
    echo "Manual verification required at http://aupex.ai/agents/"
    exit 1
fi 