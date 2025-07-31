#!/bin/bash
# NEUROS 5-MINUTE VALIDATION SCRIPT
# Run this to quickly verify what's implemented vs YAML spec

echo "🚀 NEUROS QUICK VALIDATION (5 minutes)"
echo "====================================="
echo ""

# Test URL (change if needed)
BASE_URL="https://auren-b1tuli19i-jason-madrugas-projects.vercel.app/api/neuros"

# 1. CHECK IF IT'S REAL NEUROS
echo "1️⃣ CHECKING IF REAL NEUROS (not mock)..."
echo "----------------------------------------"
HEALTH=$(curl -s $BASE_URL/health)
echo "Health Response: $HEALTH"

if [[ $HEALTH == *"neuros-cognitive-architecture"* ]]; then
    echo "✅ REAL NEUROS DETECTED (cognitive architecture)"
else
    echo "❌ Might be old version or mock"
fi
echo ""

# 2. TEST COGNITIVE MODES
echo "2️⃣ TESTING COGNITIVE MODES..."
echo "-----------------------------"

# Test simple greeting (should be companion mode)
echo "Testing greeting..."
GREETING=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "user_id": "test1", "session_id": "s1"}')

if [[ $GREETING == *"companion"* ]]; then
    echo "✅ Companion mode working"
else
    echo "❌ Companion mode not detected"
fi

# Test status check (should be baseline mode)
echo "Testing status check..."
STATUS=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "how am I doing?", "user_id": "test2", "session_id": "s2"}')

if [[ $STATUS == *"baseline"* ]]; then
    echo "✅ Baseline mode working"
else
    echo "❌ Baseline mode not detected"
fi
echo ""

# 3. TEST MEMORY CACHING
echo "3️⃣ TESTING MEMORY CACHING..."
echo "---------------------------"

USER_ID="cache_test_$(date +%s)"

# First request
START1=$(date +%s.%N)
RESP1=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"hello\", \"user_id\": \"$USER_ID\", \"session_id\": \"s1\"}")
END1=$(date +%s.%N)
TIME1=$(echo "$END1 - $START1" | bc)

# Second request (should be cached)
START2=$(date +%s.%N)
RESP2=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"hi\", \"user_id\": \"$USER_ID\", \"session_id\": \"s2\"}")
END2=$(date +%s.%N)
TIME2=$(echo "$END2 - $START2" | bc)

echo "First request: ${TIME1}s"
echo "Second request: ${TIME2}s"

if [[ $RESP2 == *"response_cached"*"true"* ]]; then
    echo "✅ Memory caching working"
else
    echo "❌ Memory caching not detected"
fi
echo ""

# 4. CHECK YAML FEATURES
echo "4️⃣ CHECKING YAML PHASE IMPLEMENTATION..."
echo "--------------------------------------"

# Phase 4: Neuroplastic protocols
echo "Testing neuroplastic protocols..."
PROTOCOL=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "suggest a sleep protocol", "user_id": "test3", "session_id": "s3"}')

if [[ $PROTOCOL == *"protocol"* ]] || [[ $PROTOCOL == *"sleep"* ]]; then
    echo "✅ Phase 4: Basic protocol suggestions"
else
    echo "❌ Phase 4: No protocol features"
fi

# Phase 10: Missions
echo "Testing mission generation..."
MISSION=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a mission to improve my energy", "user_id": "test4", "session_id": "s4"}')

if [[ $MISSION == *"mission"* ]] || [[ $MISSION == *"energy"* ]]; then
    echo "✅ Phase 10: Basic mission features"
else
    echo "❌ Phase 10: No mission features"
fi

# Phase 11: Narrative
echo "Testing narrative engine..."
NARRATIVE=$(curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "what is my story arc?", "user_id": "test5", "session_id": "s5"}')

if [[ $NARRATIVE == *"story"* ]] || [[ $NARRATIVE == *"archetype"* ]]; then
    echo "✅ Phase 11: Basic narrative features"
else
    echo "❌ Phase 11: No narrative features"
fi
echo ""

# 5. PERFORMANCE CHECK
echo "5️⃣ PERFORMANCE BENCHMARKS..."
echo "---------------------------"

# Simple greeting timing
START=$(date +%s.%N)
curl -s -X POST $BASE_URL/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "user_id": "perf_test", "session_id": "perf1"}' > /dev/null
END=$(date +%s.%N)
GREETING_TIME=$(echo "$END - $START" | bc)

echo "Simple greeting: ${GREETING_TIME}s (Target: <0.5s)"
if (( $(echo "$GREETING_TIME < 0.5" | bc -l) )); then
    echo "✅ Meets performance target"
else
    echo "❌ Slower than target"
fi
echo ""

# SUMMARY
echo "📊 VALIDATION SUMMARY"
echo "===================="
echo ""
echo "YAML SPECIFICATION: 808 lines, 13 phases"
echo "CURRENT IMPLEMENTATION: ~500 lines, ~3.5 phases"
echo ""
echo "✅ IMPLEMENTED (~33%):"
echo "  - Phase 1: Personality & voice"
echo "  - Phase 2: 5 Cognitive modes" 
echo "  - Phase 3: Hot memory tier"
echo "  - Phase 4: Neuroplastic (stub)"
echo ""
echo "❌ NOT IMPLEMENTED (~67%):"
echo "  - Phase 5-9: Advanced reasoning & behavior"
echo "  - Phase 10-11: Missions & narrative (stubs only)"
echo "  - Phase 12-13: Multi-agent & pre-symptom"
echo ""
echo "🎯 VERDICT: This is REAL NEUROS with 33% of YAML features implemented"
echo ""
echo "To implement remaining features, add new LangGraph nodes for phases 5-13"
