#!/bin/bash
# Test script for Section 11 deployment

set -e

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASSWORD=".HvddX+@6dArsKd"
DB_USER="auren_user"
DB_NAME="auren_production"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}SECTION 11 DEPLOYMENT TEST SUITE${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Test 1: Check schemas
echo -e "\n${YELLOW}Test 1: Checking schemas...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT nspname as schema_name,
       CASE 
         WHEN nspname IN ('events', 'analytics', 'encrypted', 'biometric') THEN '✓ Created'
         ELSE '✗ Missing'
       END as status
FROM pg_namespace
WHERE nspname IN ('events', 'analytics', 'encrypted', 'biometric', 'public')
ORDER BY nspname;
\""

# Test 2: Check event store
echo -e "\n${YELLOW}Test 2: Testing event store...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
-- Check if event_store exists
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'events' AND table_name = 'event_store')
        THEN 'Event store table exists'
        ELSE 'Event store table MISSING'
    END as status;

-- Try to insert a test event
INSERT INTO events.event_store (stream_id, stream_version, event_type, event_data, created_by)
VALUES ('test:suite', 1, 'test_event', '{\\\"test\\\": \\\"section_11\\\"}'::jsonb, 'test_script')
ON CONFLICT DO NOTHING;

-- Count events
SELECT COUNT(*) as event_count FROM events.event_store;
\""

# Test 3: Check hypertables
echo -e "\n${YELLOW}Test 3: Checking hypertables...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT 
    hypertable_name,
    num_chunks,
    CASE compression_enabled 
        WHEN true THEN 'Compression ON'
        ELSE 'Compression OFF'
    END as compression
FROM timescaledb_information.hypertables
ORDER BY hypertable_name;
\""

# Test 4: Check continuous aggregates
echo -e "\n${YELLOW}Test 4: Checking continuous aggregates...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT 
    view_name,
    refresh_interval,
    CASE 
        WHEN job_status = 'RUNNING' THEN '✓ Active'
        ELSE '✗ ' || COALESCE(job_status, 'Not scheduled')
    END as status
FROM timescaledb_information.continuous_aggregates
LEFT JOIN timescaledb_information.jobs 
    ON job_type = 'continuous_aggregate_refresh' 
    AND job_name LIKE '%' || view_name || '%'
WHERE view_schema = 'analytics';
\""

# Test 5: Test LISTEN/NOTIFY
echo -e "\n${YELLOW}Test 5: Testing LISTEN/NOTIFY...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
-- Send test notifications
NOTIFY mode_switch, '{\\\"user\\\": \\\"test\\\", \\\"mode\\\": \\\"hypothesis\\\"}';
NOTIFY memory_tier_change, '{\\\"action\\\": \\\"promote\\\", \\\"tier\\\": \\\"warm\\\"}';
SELECT 'LISTEN/NOTIFY test complete' as status;
\""

# Test 6: Check Section 9 integration
echo -e "\n${YELLOW}Test 6: Checking Section 9 integration...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT * FROM check_section_9_integration();
\""

# Test 7: Performance check
echo -e "\n${YELLOW}Test 7: Performance metrics...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT * FROM analytics.system_performance;
\""

# Test 8: Check triggers
echo -e "\n${YELLOW}Test 8: Checking triggers...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT 
    tgname as trigger_name,
    tgrelid::regclass as table_name,
    CASE 
        WHEN tgname LIKE '%notify%' THEN '✓ NOTIFY trigger'
        ELSE '✓ Other trigger'
    END as type
FROM pg_trigger
WHERE tgname LIKE '%notify%' OR tgname LIKE '%encrypt%'
ORDER BY tgname;
\""

# Summary
echo -e "\n${BLUE}==============================================================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}==============================================================================${NC}"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT 
    'Schemas' as component,
    COUNT(*) || ' of 4' as status
FROM pg_namespace
WHERE nspname IN ('events', 'analytics', 'encrypted', 'biometric')
UNION ALL
SELECT 
    'Event Store',
    CASE 
        WHEN EXISTS (SELECT 1 FROM events.event_store LIMIT 1) THEN 'Operational'
        ELSE 'Empty/Missing'
    END
UNION ALL
SELECT 
    'Hypertables',
    COUNT(*) || ' configured'
FROM timescaledb_information.hypertables
UNION ALL
SELECT 
    'Continuous Aggregates',
    COUNT(*) || ' created'
FROM timescaledb_information.continuous_aggregates
WHERE view_schema = 'analytics';
\""

echo -e "\n${GREEN}Test suite complete!${NC}" 