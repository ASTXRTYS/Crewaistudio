#!/bin/bash
# NEUROS Mock Biometric Test for LIVE BACKEND
# This sends real data to your production AUREN system!

echo "========================================"
echo "🚀 AUREN LIVE BACKEND TEST"
echo "========================================"
echo "Sending mock biometric data to: http://144.126.215.218:8888"
echo "Watch your Grafana dashboards for activity!"
echo ""

BASE_URL="http://localhost:8888"  # Will run on server, so localhost is the backend

# Function to send webhook data
send_webhook() {
    local device=$1
    local data=$2
    local user=$3
    
    echo "📡 Sending $device data for $user..."
    curl -X POST "$BASE_URL/webhooks/$device" \
        -H "Content-Type: application/json" \
        -d "$data" \
        -s | jq . || echo "Response received"
    
    sleep 1
}

echo "=== PHASE 1: TESTING 3 MOCK ATHLETES ==="
echo ""

# Athlete 1: High Performance State
echo "👤 ATHLETE 1: Elite Performer"
echo "--------------------------------"

# Day 1-7 Oura data showing excellent recovery
for day in {0..6}; do
    READINESS=$((85 + RANDOM % 10))
    HRV=$((65 + RANDOM % 15))
    
    DATA=$(cat <<EOF
{
    "event_type": "daily_readiness",
    "user_id": "athlete_elite_001",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "data": {
        "readiness_score": $READINESS,
        "hrv_balance": $HRV,
        "body_temperature": 36.4,
        "resting_heart_rate": 48,
        "respiratory_rate": 13.5,
        "sleep_score": $((80 + RANDOM % 15)),
        "activity_balance": $((85 + RANDOM % 10))
    }
}
EOF
)
    send_webhook "oura" "$DATA" "athlete_elite_001"
done

# WHOOP recovery data
echo -e "\n💪 Sending WHOOP data..."
for i in {1..3}; do
    RECOVERY=$((80 + RANDOM % 15))
    STRAIN=$((12 + RANDOM % 6))
    
    DATA=$(cat <<EOF
{
    "event_type": "recovery_update",
    "user_id": "athlete_elite_001",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "data": {
        "recovery_score": $RECOVERY,
        "hrv_rmssd": $((60 + RANDOM % 20)),
        "sleep_performance": $((85 + RANDOM % 10)),
        "strain_score": $STRAIN,
        "calories_burned": $((2500 + STRAIN * 100))
    }
}
EOF
)
    send_webhook "whoop" "$DATA" "athlete_elite_001"
done

# Athlete 2: Recovery Needed
echo -e "\n👤 ATHLETE 2: Overtrained"
echo "--------------------------------"

for day in {0..6}; do
    READINESS=$((45 + RANDOM % 15))
    HRV=$((35 + RANDOM % 10))
    
    DATA=$(cat <<EOF
{
    "event_type": "daily_readiness",
    "user_id": "athlete_overtrained_002",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "data": {
        "readiness_score": $READINESS,
        "hrv_balance": $HRV,
        "body_temperature": 36.8,
        "resting_heart_rate": 62,
        "respiratory_rate": 16,
        "sleep_score": $((55 + RANDOM % 15)),
        "activity_balance": $((40 + RANDOM % 20))
    }
}
EOF
)
    send_webhook "oura" "$DATA" "athlete_overtrained_002"
done

# Athlete 3: Adapting/Improving
echo -e "\n👤 ATHLETE 3: Adaptation Phase"
echo "--------------------------------"

# Show improving trend
START_HRV=45
for day in {0..6}; do
    HRV=$((START_HRV + day * 3 + RANDOM % 5))
    READINESS=$((65 + day * 2 + RANDOM % 10))
    
    DATA=$(cat <<EOF
{
    "event_type": "daily_readiness",
    "user_id": "athlete_adapting_003",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "data": {
        "readiness_score": $READINESS,
        "hrv_balance": $HRV,
        "body_temperature": 36.5,
        "resting_heart_rate": 55,
        "respiratory_rate": 14.5,
        "sleep_score": $((70 + RANDOM % 15)),
        "activity_balance": $((75 + RANDOM % 15))
    }
}
EOF
)
    send_webhook "oura" "$DATA" "athlete_adapting_003"
done

# Real-time Apple Health data
echo -e "\n⌚ Sending Apple Health real-time data..."
for athlete in "athlete_elite_001" "athlete_overtrained_002" "athlete_adapting_003"; do
    for i in {1..3}; do
        HR=$((65 + RANDOM % 40))
        SPO2=$((95 + RANDOM % 4))
        
        DATA=$(cat <<EOF
{
    "event_type": "realtime_vitals",
    "user_id": "$athlete",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "data": {
        "heart_rate": $HR,
        "hrv_instantaneous": $((40 + RANDOM % 30)),
        "blood_oxygen": $SPO2,
        "respiratory_rate": $((14 + RANDOM % 4)),
        "activity_calories": $((100 + RANDOM % 400)),
        "step_count": $((5000 + RANDOM % 10000))
    }
}
EOF
)
        send_webhook "apple_health" "$DATA" "$athlete"
    done
done

echo -e "\n=== PHASE 2: CHECKING SYSTEM STATUS ==="
echo ""

# Check health
echo "🏥 System Health:"
curl -s "$BASE_URL/health" | jq . || echo "Health check complete"

echo -e "\n📊 Metrics Status:"
curl -s "$BASE_URL/metrics" | head -20 || echo "Metrics endpoint needs implementation"

echo -e "\n=== NEUROS ANALYSIS SIMULATION ==="
echo "Based on the data sent, NEUROS would determine:"
echo ""
echo "🧠 Athlete 1 (Elite): PERFORMANCE MODE"
echo "   - Excellent HRV (65-80)"
echo "   - High readiness (85-95)"
echo "   - Ready for high-intensity training"
echo ""
echo "🧠 Athlete 2 (Overtrained): RECOVERY MODE"
echo "   - Low HRV (35-45)"
echo "   - Poor readiness (45-60)"
echo "   - Needs recovery protocols"
echo ""
echo "🧠 Athlete 3 (Adapting): ADAPTATION MODE"
echo "   - Improving HRV trend (+18 over week)"
echo "   - Rising readiness"
echo "   - Body responding well to training"
echo ""
echo "✅ TEST COMPLETE!"
echo ""
echo "🎯 CHECK GRAFANA NOW!"
echo "   - System metrics should show the data flow"
echo "   - If biometric metrics aren't visible, /metrics needs implementation"
echo "   - PostgreSQL should show webhook events stored"
echo "" 