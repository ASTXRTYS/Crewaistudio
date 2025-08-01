#!/bin/bash
# AUREN Load Testing Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BASE_URL=${BASE_URL:-"http://144.126.215.218:8000"}
TEST_TYPE=${1:-"smoke"}

echo -e "${GREEN}🚀 AUREN Load Testing Suite${NC}"
echo "================================"
echo "Target: $BASE_URL"
echo "Test Type: $TEST_TYPE"
echo "================================"

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo -e "${YELLOW}k6 is not installed. Installing...${NC}"
    
    # Detect OS and install k6
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install k6
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
    else
        echo -e "${RED}Unsupported OS. Please install k6 manually.${NC}"
        exit 1
    fi
fi

# Create results directory
mkdir -p k6/results

# Run the appropriate test
case $TEST_TYPE in
    "smoke")
        echo -e "${GREEN}Running smoke test...${NC}"
        k6 run --env BASE_URL=$BASE_URL --env TEST_TYPE=smoke k6/auren-load-test-suite.js
        ;;
    "load")
        echo -e "${GREEN}Running load test...${NC}"
        k6 run --env BASE_URL=$BASE_URL --env TEST_TYPE=load k6/auren-load-test-suite.js
        ;;
    "stress")
        echo -e "${YELLOW}Running stress test...${NC}"
        k6 run --env BASE_URL=$BASE_URL --env TEST_TYPE=stress k6/auren-load-test-suite.js
        ;;
    "spike")
        echo -e "${YELLOW}Running spike test...${NC}"
        k6 run --env BASE_URL=$BASE_URL --env TEST_TYPE=spike k6/auren-load-test-suite.js
        ;;
    "soak")
        echo -e "${RED}Running soak test (2 hours)...${NC}"
        k6 run --env BASE_URL=$BASE_URL --env TEST_TYPE=soak k6/auren-load-test-suite.js
        ;;
    "ci")
        echo -e "${GREEN}Running CI performance gate...${NC}"
        k6 run --env BASE_URL=$BASE_URL k6/ci-performance-gate.js
        
        # Check exit code
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Performance gate passed!${NC}"
            exit 0
        else
            echo -e "${RED}❌ Performance gate failed!${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Available test types: smoke, load, stress, spike, soak, ci"
        exit 1
        ;;
esac

# Move results to timestamped file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "./k6-results-${TEST_TYPE}-"*.json ]; then
    mv ./k6-results-${TEST_TYPE}-*.json "k6/results/${TEST_TYPE}_${TIMESTAMP}.json"
    echo -e "${GREEN}Results saved to: k6/results/${TEST_TYPE}_${TIMESTAMP}.json${NC}"
fi

echo -e "${GREEN}✅ Test completed!${NC}"