# AUREN SYSTEM CONFIGURATION VALIDATION GUIDE
## A Comprehensive Test Suite to Verify System-Wide Configuration

*Last Updated: July 30, 2025*  
*Purpose: To equip engineers with a standardized process for validating that the system's live configuration perfectly matches this documentation.*
*Outcome: A verified, trusted baseline of the entire AUREN system configuration.*

---

## 🎯 **PURPOSE OF THIS GUIDE**

**To the Engineer:**

This document provides a comprehensive test suite designed to equip you with the tools to validate our system's live configuration against its documentation. The primary goal is to collaboratively verify that the `AUREN_COMPLETE_SYSTEM_REFERENCE` folder is a perfect, 1-to-1 representation of our production environment.

By running these tests, you will confirm that the documentation is accurate and that the system is behaving exactly as documented. This process establishes a trusted, verified baseline—our "source of truth"—for all future development, scaling, and troubleshooting.

Please use the reference documents listed in each section to understand the expected configurations as you perform this validation.

---

## 📚 **PRE-REQUISITES**

Before you begin, ensure you have the following, as detailed in the documentation:
- **SSH Access**: You will need `sshpass` and the credentials from the vault.
- **Tools**: You will need `curl`, `wrk` (or a similar load testing tool), and a JSON processor like `jq`.
- **Reference**: Have the `AUREN_COMPLETE_SYSTEM_REFERENCE/README.md` open as your primary guide.

---

## 🧪 **PHASE 1: FRONTEND & PUBLIC INTERFACE VALIDATION**

**Objective**: Verify that all public-facing assets are live, correctly configured, and proxying traffic as expected.
**Reference Documents**:
- `01_FRONTEND_CONFIGURATION/AUPEX_WEBSITE_CONFIGURATION.md`
- `01_FRONTEND_CONFIGURATION/PWA_CONFIGURATION.md`
- `01_FRONTEND_CONFIGURATION/VERCEL_PROXY_CONFIGURATION.md`

### **1.1: `aupex.ai` Website Accessibility & Redirection**
```bash
# Test 1: Verify HTTPS is serving content
echo "--> Testing HTTPS for aupex.ai..."
curl -s -I https://aupex.ai | grep "HTTP/2 200"
# EXPECTED: HTTP/2 200 OK

# Test 2: Verify HTTP redirects to HTTPS
echo "--> Testing HTTP to HTTPS redirect..."
curl -s -I http://aupex.ai | grep "HTTP/1.1 301"
# EXPECTED: HTTP/1.1 301 Moved Permanently
curl -s -I http://aupex.ai | grep "Location: https://aupex.ai/"
# EXPECTED: Location: https://aupex.ai/
```
**Verification**: Both tests pass, confirming the site is live and secure as per the Nginx configuration.

### **1.2: AUREN PWA Accessibility**
```bash
# Test 3: Verify the PWA is live and accessible
echo "--> Testing PWA accessibility..."
curl -s -I https://auren-omacln1ad-jason-madrugas-projects.vercel.app | grep "HTTP/2 200"
# EXPECTED: HTTP/2 200 OK
```
**Verification**: The PWA landing page loads correctly as documented.

### **1.3: Vercel & Nginx Proxy Validation**
This is a critical test of the entire frontend-to-backend connection.
```bash
# Test 4: Verify Vercel proxy to NEUROS AI
echo "--> Testing Vercel Proxy to NEUROS (Port 8000)..."
curl -s https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health | jq .
# EXPECTED: {"status": "healthy", "service": "neuros-advanced", ...}

# Test 5: Verify Vercel proxy to Enhanced Bridge
echo "--> Testing Vercel Proxy to Enhanced Bridge (Port 8889)..."
curl -s https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/bridge/health | jq .
# EXPECTED: {"status": "healthy", "service": "biometric-bridge", ...}

# Test 6: Verify Nginx proxy from aupex.ai
echo "--> Testing Nginx Proxy from aupex.ai..."
curl -s https://aupex.ai/api/health | jq .
# EXPECTED: A healthy status from the upstream API.
```
**Verification**: All three proxy routes return a `healthy` status, confirming the routing rules in `vercel.json` and `nginx.conf` are correct.

---

## 🧪 **PHASE 2: BACKEND API & SERVICE VALIDATION**

**Objective**: Verify that all backend services are running, healthy, and their core API endpoints are functional directly on the server.
**Reference Documents**:
- `02_BACKEND_CONFIGURATION/NEUROS_AI_CONFIGURATION.md`
- `02_BACKEND_CONFIGURATION/BIOMETRIC_BRIDGE_CONFIGURATION.md`
- `AUREN_DOCS/00_QUICK_START/CREDENTIALS_VAULT.md`

### **2.1: SSH and Environment Access**
```bash
# Test 7: SSH into the production server
echo "--> Attempting to SSH into the server..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'echo "SSH Connection Successful"'
# EXPECTED: SSH Connection Successful
```
**Verification**: Server access is configured as documented.

### **2.2: Direct Service Health Checks**
```bash
# Test 8: NEUROS AI direct health check
echo "--> Testing NEUROS AI health directly..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'curl -s http://localhost:8000/health' | jq .
# EXPECTED: {"status": "healthy", "service": "neuros-advanced", ...}

# Test 9: Enhanced Biometric Bridge direct health check
echo "--> Testing Enhanced Bridge health directly..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'curl -s http://localhost:8889/health' | jq .
# EXPECTED: {"status": "healthy", "service": "biometric-bridge", ...}
```
**Verification**: Both services report a `healthy` status from within the server's Docker network.

### **2.3: Core API Functionality Test**
```bash
# Test 10: NEUROS AI analysis endpoint test
echo "--> Testing NEUROS AI analysis endpoint..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "curl -s -X POST http://localhost:8000/api/agents/neuros/analyze -H 'Content-Type: application/json' -d '{\"message\": \"Validation test\", \"user_id\": \"validator\", \"session_id\": \"challenge\"}'" | jq .
# EXPECTED: A valid JSON response from the NEUROS agent.

# Test 11: Biometric Bridge webhook simulation
echo "--> Testing Biometric Bridge webhook endpoint..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "curl -s -X POST http://localhost:8889/webhook/terra -H 'Content-Type: application/json' -d '{\"type\": \"test_event\"}'" | jq .
# EXPECTED: {"status": "processed", "device": "terra"}
```
**Verification**: Core API endpoints process requests and return successful responses, confirming their documented functionality.

---

## 🧪 **PHASE 3: END-TO-END DATA FLOW VALIDATION**

**Objective**: Verify the entire data pipeline works as documented, from data ingestion to AI processing.
**Reference Documents**:
- `03_INFRASTRUCTURE_CONFIGURATION/DOCKER_CONFIGURATION.md`
- `02_BACKEND_CONFIGURATION/BIOMETRIC_BRIDGE_CONFIGURATION.md`

### **3.1: Kafka Topic Verification**
```bash
# Test 12: Check for required Kafka topics
echo "--> Verifying Kafka topics..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "docker exec auren-kafka kafka-topics.sh --bootstrap-server localhost:9092 --list"
# EXPECTED: Must contain 'biometric-events' and 'terra-biometric-events'
```
**Verification**: Kafka topics are configured as required by the backend services.

### **3.2: Full Pipeline Test (Webhook -> Kafka -> NEUROS)**
This test validates the entire real-time data flow.
```bash
# Step 1: Start a consumer on the 'biometric-events' topic to watch for the message
echo "--> Starting Kafka consumer to monitor the event..."
# (Run this in a separate terminal or backgrounded)
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "docker exec auren-kafka kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic biometric-events --from-beginning --timeout-ms 15000" > kafka_output.log &
CONSUMER_PID=$!

# Give the consumer a moment to start
sleep 5

# Step 2: Send a webhook with a critically low HRV to the Enhanced Bridge
echo "--> Sending low HRV webhook to trigger a HIGH priority event..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "curl -s -X POST http://localhost:8889/webhook/oura -H 'Content-Type: application/json' -H 'Signature: test' -d '{\"user_id\":\"validator\",\"timestamp\":\"2025-07-30T12:00:00Z\",\"hrv_data\":{\"rmssd\":20}}'"

# Step 3: Wait for the consumer to capture the message
echo "--> Waiting for event to pass through Kafka..."
wait $CONSUMER_PID

# Test 13: Verify the message appeared in Kafka
echo "--> Verifying message in Kafka..."
cat kafka_output.log | jq .
grep '"hrv":20' kafka_output.log
# EXPECTED: The command should find a message containing '"hrv":20'.

# Test 14: Verify the message was consumed by NEUROS
echo "--> Verifying NEUROS processed the event..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "docker logs neuros-advanced --tail 50" | grep "URGENT_INTERVENTION"
# EXPECTED: The NEUROS logs should show processing of a critical/urgent intervention.

# Clean up
rm kafka_output.log
```
**Verification**: A webhook is successfully processed by the bridge, sent to Kafka with high priority (based on HRV trigger logic), and consumed by the NEUROS agent, which logs the correct intervention. This confirms the entire data pipeline is functional.

---

## 🧪 **PHASE 4: INFRASTRUCTURE & DATABASE INTEGRITY**

**Objective**: Verify that all underlying infrastructure components and databases are running and interconnected as documented.
**Reference Documents**:
- `03_INFRASTRUCTURE_CONFIGURATION/DOCKER_CONFIGURATION.md`

### **4.1: Container Status Check**
```bash
# Test 15: Verify all critical containers are running and healthy
echo "--> Verifying status of all critical containers..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "/root/monitor-auren.sh | grep '❌'"
# EXPECTED: No output. The command should return nothing, indicating no services are down.
```
**Verification**: All containers listed in the `DOCKER_CONFIGURATION` document are running.

### **4.2: Database Connectivity**
```bash
# Test 16: Verify connection to PostgreSQL
echo "--> Testing PostgreSQL connection..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "docker exec auren-postgres psql -U auren_user -d auren_production -c 'SELECT 1;'" | grep "1"
# EXPECTED: (1 row)

# Test 17: Verify connection to Redis
echo "--> Testing Redis connection..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "docker exec auren-redis redis-cli ping"
# EXPECTED: PONG
```
**Verification**: The primary databases are responsive and accessible from within the Docker network.

---

## 🧪 **PHASE 5: PERFORMANCE & CAPABILITY VERIFICATION**

**Objective**: Run simple checks to confirm the system's performance capabilities match the documentation.
**Reference Documents**:
- `05_PERFORMANCE_AND_CAPABILITIES/README.md`

### **5.1: Webhook Concurrency Check**
```bash
# Test 18: Send 5 concurrent webhooks to the bridge
echo "--> Sending 5 concurrent webhooks..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "for i in {1..5}; do curl -s -X POST http://localhost:8889/webhook/terra -H 'Content-Type: application/json' -d '{\"type\":\"concurrent_test_$i\"}' & done; wait" | jq -s .
# EXPECTED: An array of 5 successful {"status": "processed", "device": "terra"} responses.
```
**Verification**: The bridge handles a small burst of concurrent requests, confirming its multi-worker configuration is active.

### **5.2: Circuit Breaker State Check**
```bash
# Test 19: Verify the circuit breaker is in a CLOSED state
echo "--> Checking Circuit Breaker state..."
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'curl -s http://localhost:8889/metrics' | jq .circuit_breaker_openings
# EXPECTED: A low number (ideally 0), indicating it has not been recently tripped.
```
**Verification**: The circuit breaker is not open, confirming system stability as documented.

---

## 🏆 **VALIDATION CONCLUSION**

Upon successful completion of all tests in this guide, the `AUREN_COMPLETE_SYSTEM_REFERENCE` is hereby validated as the official **source of truth** for the AUREN system's configuration.

This verified documentation should be treated as a "lock and key" blueprint. All future system modifications must be reflected in this documentation to maintain its accuracy and value as our primary reference. 