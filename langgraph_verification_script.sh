#!/bin/bash
# =============================================================================
# LANGGRAPH MIGRATION VERIFICATION SCRIPT
# =============================================================================
# Purpose: Comprehensively verify the CrewAI → LangGraph migration claims
# Author: Lead Architect
# Date: January 29, 2025
# Expected Runtime: 15-20 minutes
# =============================================================================

echo "🔍 AUREN LangGraph Migration Verification Tool"
echo "============================================="
echo "Verifying claim: 100% production-ready with pure LangGraph"
echo ""

# Initialize verification report
REPORT_FILE="langgraph_verification_report_$(date +%Y%m%d_%H%M%S).md"
FAILED_TESTS=0
PASSED_TESTS=0

echo "# LangGraph Migration Verification Report" > $REPORT_FILE
echo "Generated: $(date)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Helper functions
pass_test() {
    echo "✅ PASS: $1" | tee -a $REPORT_FILE
    ((PASSED_TESTS++))
}

fail_test() {
    echo "❌ FAIL: $1" | tee -a $REPORT_FILE
    echo "   Details: $2" | tee -a $REPORT_FILE
    ((FAILED_TESTS++))
}

# =============================================================================
# SECTION 1: Verify No CrewAI Dependencies
# =============================================================================

echo -e "\n1️⃣ Verifying CrewAI has been completely removed..."
echo "## 1. CrewAI Dependency Check" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check requirements files
echo "### Checking requirements files..." | tee -a $REPORT_FILE

for req_file in requirements.txt requirements_langgraph.txt pyproject.toml setup.py; do
    if [ -f "auren/$req_file" ]; then
        if grep -i "crewai" "auren/$req_file" > /dev/null 2>&1; then
            fail_test "$req_file contains CrewAI" "Found: $(grep -i crewai auren/$req_file)"
        else
            pass_test "$req_file is clean of CrewAI"
        fi
    fi
done

# Check Python imports
echo -e "\n### Checking Python imports..." | tee -a $REPORT_FILE

CREWAI_IMPORTS=$(find auren -name "*.py" -type f -exec grep -l "from crewai\|import crewai" {} \; 2>/dev/null | grep -v __pycache__)

if [ -n "$CREWAI_IMPORTS" ]; then
    fail_test "Found CrewAI imports" "$CREWAI_IMPORTS"
else
    pass_test "No CrewAI imports found in Python files"
fi

# Check Docker containers
echo -e "\n### Checking running containers..." | tee -a $REPORT_FILE

if docker ps --format "{{.Names}}" | xargs -I {} docker exec {} pip list 2>/dev/null | grep -i crewai > /dev/null; then
    fail_test "CrewAI found in running containers" "Check containers with: docker exec <container> pip list"
else
    pass_test "No CrewAI in running containers"
fi

# =============================================================================
# SECTION 2: Verify LangGraph Implementation
# =============================================================================

echo -e "\n2️⃣ Verifying LangGraph implementation..."
echo -e "\n## 2. LangGraph Implementation Check" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check for LangGraph imports
echo "### Checking LangGraph imports..." | tee -a $REPORT_FILE

LANGGRAPH_FILES=$(find auren -name "*.py" -type f -exec grep -l "from langgraph\|import.*langgraph" {} \; 2>/dev/null | grep -v __pycache__)

if [ -n "$LANGGRAPH_FILES" ]; then
    pass_test "Found LangGraph imports" "Files: $(echo $LANGGRAPH_FILES | wc -l)"
    echo "Files with LangGraph:" >> $REPORT_FILE
    echo "$LANGGRAPH_FILES" | head -5 >> $REPORT_FILE
else
    fail_test "No LangGraph imports found" "Expected in main_langgraph.py"
fi

# Check for key LangGraph patterns
echo -e "\n### Checking LangGraph patterns..." | tee -a $REPORT_FILE

# Check for StateGraph usage
if grep -r "StateGraph" auren/ --include="*.py" > /dev/null 2>&1; then
    pass_test "StateGraph pattern found"
else
    fail_test "StateGraph pattern missing" "Core LangGraph concept not found"
fi

# Check for reducers
if grep -r "Annotated\[.*," auren/ --include="*.py" > /dev/null 2>&1; then
    pass_test "Reducer patterns found"
else
    fail_test "No reducers found" "Critical for parallel operations"
fi

# Check for checkpointing
if grep -r "PostgresSaver\|checkpointer" auren/ --include="*.py" > /dev/null 2>&1; then
    pass_test "Checkpointing implementation found"
else
    fail_test "No checkpointing found" "Required for state persistence"
fi

# =============================================================================
# SECTION 3: Test Runtime Components
# =============================================================================

echo -e "\n3️⃣ Testing runtime components..."
echo -e "\n## 3. Runtime Component Tests" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Test health endpoint
echo "### Testing health endpoint..." | tee -a $REPORT_FILE

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://144.126.215.218:8888/health 2>/dev/null | tail -1)

if [ "$HEALTH_RESPONSE" = "200" ]; then
    pass_test "Health endpoint responding"
else
    fail_test "Health endpoint not responding" "HTTP code: $HEALTH_RESPONSE"
fi

# Test async Redis
echo -e "\n### Testing async Redis..." | tee -a $REPORT_FILE

python3 -c "
import asyncio
import sys
try:
    import redis.asyncio as aioredis
    print('✓ redis.asyncio imported successfully')
    sys.exit(0)
except ImportError:
    print('✗ redis.asyncio not available')
    sys.exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    pass_test "Async Redis available"
else
    fail_test "Async Redis not available" "Check redis[hiredis] installation"
fi

# Test async Kafka
echo -e "\n### Testing async Kafka..." | tee -a $REPORT_FILE

python3 -c "
import sys
try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    print('✓ aiokafka imported successfully')
    sys.exit(0)
except ImportError:
    print('✗ aiokafka not available')
    sys.exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    pass_test "Async Kafka available"
else
    fail_test "Async Kafka not available" "Check aiokafka installation"
fi

# =============================================================================
# SECTION 4: Integration Tests
# =============================================================================

echo -e "\n4️⃣ Running integration tests..."
echo -e "\n## 4. Integration Tests" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Test biometric event processing
echo "### Testing biometric event flow..." | tee -a $REPORT_FILE

TEST_EVENT='{
  "user_id": "test_langgraph_001",
  "device_type": "oura",
  "event_type": "readiness.updated",
  "data": {
    "readiness_score": 75,
    "hrv": 45
  }
}'

# Send test event
RESPONSE=$(curl -s -X POST \
    http://144.126.215.218:8888/webhooks/oura \
    -H "Content-Type: application/json" \
    -d "$TEST_EVENT" 2>/dev/null)

if echo "$RESPONSE" | grep -q "success\|processed"; then
    pass_test "Biometric event processing working"
else
    fail_test "Biometric event processing failed" "Response: $RESPONSE"
fi

# =============================================================================
# SECTION 5: Production Readiness Checks
# =============================================================================

echo -e "\n5️⃣ Verifying production readiness claims..."
echo -e "\n## 5. Production Readiness" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check graceful shutdown
echo "### Checking graceful shutdown..." | tee -a $REPORT_FILE

if grep -r "signal\.signal\|SIGTERM\|shutdown_event" auren/main_langgraph.py > /dev/null 2>&1; then
    pass_test "Graceful shutdown implemented"
else
    fail_test "No graceful shutdown found" "Missing signal handlers"
fi

# Check retry logic
echo -e "\n### Checking retry logic..." | tee -a $REPORT_FILE

if grep -r "@retry\|tenacity\|exponential_backoff" auren/ --include="*.py" > /dev/null 2>&1; then
    pass_test "Retry logic implemented"
else
    fail_test "No retry logic found" "Missing resilience patterns"
fi

# Check health probes
echo -e "\n### Checking Kubernetes probes..." | tee -a $REPORT_FILE

for probe in health readiness metrics; do
    if grep -r "/$probe" auren/main_langgraph.py > /dev/null 2>&1; then
        pass_test "$probe endpoint implemented"
    else
        fail_test "$probe endpoint missing" "Required for K8s"
    fi
done

# =============================================================================
# SECTION 6: Security Integration
# =============================================================================

echo -e "\n6️⃣ Verifying Section 9 security integration..."
echo -e "\n## 6. Security Integration" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check for security.py
if [ -f "auren/security.py" ]; then
    pass_test "security.py exists"
    
    # Check for key security functions
    if grep -q "verify_api_key\|encrypt_phi" auren/security.py 2>/dev/null; then
        pass_test "Security functions implemented"
    else
        fail_test "Security functions missing" "Expected API key and PHI encryption"
    fi
else
    fail_test "security.py not found" "Section 9 integration missing"
fi

# =============================================================================
# SECTION 7: Performance Benchmarks
# =============================================================================

echo -e "\n7️⃣ Running performance benchmarks..."
echo -e "\n## 7. Performance Benchmarks" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Test response time
echo "### Testing response times..." | tee -a $REPORT_FILE

START_TIME=$(date +%s.%N)
curl -s http://144.126.215.218:8888/health > /dev/null 2>&1
END_TIME=$(date +%s.%N)
RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc)

if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
    pass_test "Health check < 1s" "Response time: ${RESPONSE_TIME}s"
else
    fail_test "Health check slow" "Response time: ${RESPONSE_TIME}s"
fi

# =============================================================================
# SECTION 8: Documentation Verification
# =============================================================================

echo -e "\n8️⃣ Verifying documentation..."
echo -e "\n## 8. Documentation Check" >> $REPORT_FILE
echo "" >> $REPORT_FILE

REQUIRED_DOCS=(
    "AUREN_DOCS/02_DEPLOYMENT/SECTION_12_MAIN_EXECUTION_GUIDE.md"
    "auren/AUREN_STATE_OF_READINESS_REPORT.md"
    "auren/main_langgraph.py"
    "auren/requirements_langgraph.txt"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        pass_test "Found: $doc"
    else
        fail_test "Missing: $doc" "Required documentation"
    fi
done

# =============================================================================
# FINAL SUMMARY
# =============================================================================

echo -e "\n==================== SUMMARY ===================="
echo -e "\n# Summary" >> $REPORT_FILE
echo "" >> $REPORT_FILE

TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo "Total Tests: $TOTAL_TESTS" | tee -a $REPORT_FILE
echo "Passed: $PASSED_TESTS" | tee -a $REPORT_FILE
echo "Failed: $FAILED_TESTS" | tee -a $REPORT_FILE
echo "Success Rate: ${SUCCESS_RATE}%" | tee -a $REPORT_FILE
echo "" >> $REPORT_FILE

# Determine verdict
if [ $FAILED_TESTS -eq 0 ]; then
    echo "## ✅ VERDICT: Migration VERIFIED SUCCESSFUL!" | tee -a $REPORT_FILE
    echo "The 100% claim appears to be accurate." | tee -a $REPORT_FILE
elif [ $SUCCESS_RATE -ge 90 ]; then
    echo "## ⚠️ VERDICT: Migration MOSTLY COMPLETE (${SUCCESS_RATE}%)" | tee -a $REPORT_FILE
    echo "Minor issues need addressing." | tee -a $REPORT_FILE
elif [ $SUCCESS_RATE -ge 75 ]; then
    echo "## ⚠️ VERDICT: Migration PARTIALLY COMPLETE (${SUCCESS_RATE}%)" | tee -a $REPORT_FILE
    echo "Significant work remains." | tee -a $REPORT_FILE
else
    echo "## ❌ VERDICT: Migration INCOMPLETE (${SUCCESS_RATE}%)" | tee -a $REPORT_FILE
    echo "Major issues found. 100% claim is inaccurate." | tee -a $REPORT_FILE
fi

# =============================================================================
# ACTIONABLE NEXT STEPS
# =============================================================================

echo -e "\n## Recommended Next Steps" >> $REPORT_FILE
echo "" >> $REPORT_FILE

if [ $FAILED_TESTS -gt 0 ]; then
    echo "### Critical Issues to Address:" >> $REPORT_FILE
    grep "❌ FAIL" $REPORT_FILE | while read -r line; do
        echo "- Fix: ${line#*FAIL: }" >> $REPORT_FILE
    done
fi

echo -e "\n### Additional Verification Steps:" >> $REPORT_FILE
echo "1. Run load testing with concurrent users" >> $REPORT_FILE
echo "2. Test failover scenarios (kill services)" >> $REPORT_FILE
echo "3. Verify memory usage under load" >> $REPORT_FILE
echo "4. Test Kubernetes deployment" >> $REPORT_FILE
echo "5. Validate all API endpoints" >> $REPORT_FILE

# =============================================================================
# MANUAL VERIFICATION CHECKLIST
# =============================================================================

cat << 'EOF' >> $REPORT_FILE

## Manual Verification Checklist

Complete these manual checks:

- [ ] SSH to server and check process status
- [ ] Review Docker logs for errors
- [ ] Test WebSocket connections
- [ ] Verify PostgreSQL checkpointing works
- [ ] Test biometric event → mode switch flow
- [ ] Verify memory tier transitions
- [ ] Check Prometheus metrics
- [ ] Test graceful shutdown/restart
- [ ] Validate Section 9 security (API keys, PHI encryption)
- [ ] Load test with 100 concurrent connections

## Deep Dive Commands

```bash
# Check running processes
ssh root@144.126.215.218 'ps aux | grep langgraph'

# View recent logs
ssh root@144.126.215.218 'docker logs --tail 100 biometric-production'

# Test checkpointing
ssh root@144.126.215.218 'docker exec auren-postgres psql -U auren_user -d auren_production -c "SELECT * FROM checkpoints LIMIT 1;"'

# Verify no CrewAI in production
ssh root@144.126.215.218 'docker exec biometric-production pip list | grep -i crew'

# Check memory usage
ssh root@144.126.215.218 'docker stats --no-stream'
```

EOF

echo -e "\n📄 Full report saved to: $REPORT_FILE"
echo "🔍 Review the report and complete manual verification steps"

# Open report if possible
if command -v code &> /dev/null; then
    code $REPORT_FILE
elif command -v less &> /dev/null; then
    less $REPORT_FILE
fi

# =============================================================================
# END OF VERIFICATION SCRIPT
# ============================================================================= 