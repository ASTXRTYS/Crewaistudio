#!/bin/bash
# AUREN Chaos Engineering Test Runner
# Simple chaos experiments without external dependencies

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS=".HvddX+@6dArsKd"
FRONTEND_URL="https://auren-omacln1ad-jason-madrugas-projects.vercel.app"

echo -e "${GREEN}🔥 AUREN Chaos Engineering Tests${NC}"
echo "====================================="

# Function to run SSH commands
run_ssh() {
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "$1"
}

# Function to check service health
check_health() {
    local service=$1
    local url=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $service is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ $service is down${NC}"
        return 1
    fi
}

# Test 1: Container Kill Test
test_container_kill() {
    echo -e "\n${YELLOW}Test 1: Container Kill Chaos${NC}"
    echo "Killing NEUROS container..."
    
    # Record initial state
    echo "Initial state:"
    check_health "NEUROS" "http://$SERVER_IP:8000/health"
    check_health "Frontend" "$FRONTEND_URL"
    
    # Kill container
    run_ssh "docker kill neuros-advanced" || true
    
    echo -e "\n${RED}Container killed. Waiting 10s...${NC}"
    sleep 10
    
    # Check degraded state
    echo -e "\nDegraded state:"
    check_health "NEUROS" "http://$SERVER_IP:8000/health" || true
    check_health "Frontend" "$FRONTEND_URL"
    
    # Check if Prometheus detected the outage
    NEUROS_UP=$(curl -s "http://$SERVER_IP:9090/api/v1/query?query=up{job=\"neuros-advanced-prod\"}" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")
    if [ "$NEUROS_UP" = "0" ]; then
        echo -e "${GREEN}✓ Prometheus correctly detected service down${NC}"
    fi
    
    # Rollback
    echo -e "\n${GREEN}Rolling back...${NC}"
    run_ssh "docker start neuros-advanced"
    sleep 10
    
    # Verify recovery
    echo -e "\nRecovery state:"
    check_health "NEUROS" "http://$SERVER_IP:8000/health"
    check_health "Frontend" "$FRONTEND_URL"
}

# Test 2: Resource Stress Test
test_resource_stress() {
    echo -e "\n${YELLOW}Test 2: Resource Stress Test${NC}"
    echo "Applying CPU and memory stress..."
    
    # Get container ID
    CONTAINER_ID=$(run_ssh "docker ps -q -f name=neuros-advanced")
    
    # Apply resource limits temporarily
    echo "Limiting resources to 50% CPU and 256MB memory..."
    run_ssh "docker update --cpus=\"0.5\" --memory=\"256m\" neuros-advanced"
    
    echo "Running load test under constrained resources..."
    # Simple load test
    for i in {1..20}; do
        curl -s -X POST "http://$SERVER_IP:8000/api/agents/neuros/analyze" \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"Stress test $i\", \"user_id\": \"chaos-test\"}" &
    done
    wait
    
    # Check metrics during stress
    echo -e "\nChecking performance under stress:"
    LATENCY=$(curl -s "http://$SERVER_IP:9090/api/v1/query?query=http_request_duration_seconds_sum/http_request_duration_seconds_count" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")
    echo "Average latency during stress: ${LATENCY}ms"
    
    # Restore normal limits
    echo -e "\n${GREEN}Restoring normal resource limits...${NC}"
    run_ssh "docker update --cpus=\"2\" --memory=\"1g\" neuros-advanced"
    
    echo -e "${GREEN}✓ Resource stress test completed${NC}"
}

# Test 3: Network Delay Injection
test_network_chaos() {
    echo -e "\n${YELLOW}Test 3: Network Delay Test${NC}"
    echo "Adding 500ms network delay..."
    
    # Add network delay using tc (traffic control)
    run_ssh "docker exec neuros-advanced tc qdisc add dev eth0 root netem delay 500ms" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Network delay injection requires tc tools${NC}"
        echo "Skipping network chaos test"
        return
    }
    
    # Test with delay
    START_TIME=$(date +%s%N)
    curl -s "http://$SERVER_IP:8000/health" > /dev/null
    END_TIME=$(date +%s%N)
    DURATION=$((($END_TIME - $START_TIME) / 1000000))
    
    echo "Response time with 500ms delay: ${DURATION}ms"
    
    # Remove delay
    echo -e "\n${GREEN}Removing network delay...${NC}"
    run_ssh "docker exec neuros-advanced tc qdisc del dev eth0 root" 2>/dev/null || true
    
    echo -e "${GREEN}✓ Network chaos test completed${NC}"
}

# Test 4: Rapid Restart Test
test_rapid_restart() {
    echo -e "\n${YELLOW}Test 4: Rapid Restart Resilience${NC}"
    echo "Performing 5 rapid restarts..."
    
    for i in {1..5}; do
        echo -e "\nRestart $i/5"
        run_ssh "docker restart neuros-advanced"
        sleep 5
        
        # Check if service comes back
        if check_health "NEUROS" "http://$SERVER_IP:8000/health"; then
            echo -e "${GREEN}✓ Service recovered after restart $i${NC}"
        else
            echo -e "${RED}✗ Service failed to recover after restart $i${NC}"
            break
        fi
    done
    
    # Final health check
    sleep 10
    echo -e "\nFinal state after rapid restarts:"
    check_health "NEUROS" "http://$SERVER_IP:8000/health"
}

# Main execution
main() {
    echo "Starting chaos engineering tests..."
    echo "Target server: $SERVER_IP"
    echo ""
    
    # Run tests based on argument
    case ${1:-all} in
        kill)
            test_container_kill
            ;;
        stress)
            test_resource_stress
            ;;
        network)
            test_network_chaos
            ;;
        restart)
            test_rapid_restart
            ;;
        all)
            test_container_kill
            test_resource_stress
            test_network_chaos
            test_rapid_restart
            ;;
        *)
            echo "Usage: $0 [kill|stress|network|restart|all]"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}🎉 Chaos engineering tests completed!${NC}"
    echo "Review the results above to identify areas for improvement."
}

# Run main with arguments
main "$@"