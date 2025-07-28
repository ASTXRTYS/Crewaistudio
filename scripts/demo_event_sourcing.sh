#!/bin/bash
# Demo script for Section 11 Event Sourcing

set -e

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASSWORD=".HvddX+@6dArsKd"
DB_USER="auren_user"
DB_NAME="auren_production"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}SECTION 11 EVENT SOURCING DEMO${NC}"
echo -e "${BLUE}==============================================================================${NC}"

echo -e "\n${YELLOW}1. Creating sample events...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
-- User registration event
INSERT INTO events.event_store (stream_id, stream_version, event_type, event_data, created_by)
VALUES ('user:demo123', 1, 'user_registered', 
    '{\\\"user_id\\\": \\\"demo123\\\", \\\"email\\\": \\\"demo@aupex.ai\\\", \\\"timestamp\\\": \\\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\"}'::jsonb,
    'demo_script');

-- Biometric device connected
INSERT INTO events.event_store (stream_id, stream_version, event_type, event_data, created_by)
VALUES ('user:demo123', 2, 'device_connected', 
    '{\\\"device_type\\\": \\\"oura\\\", \\\"device_id\\\": \\\"ring_001\\\", \\\"timestamp\\\": \\\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\"}'::jsonb,
    'demo_script');

-- Mode switch event
INSERT INTO events.event_store (stream_id, stream_version, event_type, event_data, created_by)
VALUES ('user:demo123', 3, 'mode_switched', 
    '{\\\"from_mode\\\": \\\"baseline\\\", \\\"to_mode\\\": \\\"hypothesis\\\", \\\"reason\\\": \\\"elevated_stress\\\", \\\"confidence\\\": 0.87}'::jsonb,
    'demo_script');

-- Hypothesis validated
INSERT INTO events.event_store (stream_id, stream_version, event_type, event_data, created_by)
VALUES ('user:demo123', 4, 'hypothesis_validated', 
    '{\\\"hypothesis\\\": \\\"sleep_debt_causing_stress\\\", \\\"validation_score\\\": 0.92, \\\"action_taken\\\": \\\"recommended_sleep_protocol\\\"}'::jsonb,
    'demo_script');
\""

echo -e "\n${YELLOW}2. Querying event stream for user...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT 
    stream_version as seq,
    event_type,
    event_data->>'timestamp' as timestamp,
    CASE event_type
        WHEN 'user_registered' THEN 'User ' || (event_data->>'user_id') || ' registered'
        WHEN 'device_connected' THEN 'Connected ' || (event_data->>'device_type') || ' device'
        WHEN 'mode_switched' THEN 'Mode: ' || (event_data->>'from_mode') || ' → ' || (event_data->>'to_mode')
        WHEN 'hypothesis_validated' THEN 'Validated: ' || (event_data->>'hypothesis')
    END as description
FROM events.event_store
WHERE stream_id = 'user:demo123'
ORDER BY stream_version;
\""

echo -e "\n${YELLOW}3. Demonstrating LISTEN/NOTIFY...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
-- Simulate real-time mode switch notification
NOTIFY mode_switch, '{\\\"user_id\\\": \\\"demo123\\\", \\\"from_mode\\\": \\\"hypothesis\\\", \\\"to_mode\\\": \\\"companion\\\", \\\"timestamp\\\": \\\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\"}';

-- Simulate memory tier change
NOTIFY memory_tier_change, '{\\\"user_id\\\": \\\"demo123\\\", \\\"memory_key\\\": \\\"sleep_pattern_2025_01\\\", \\\"from_tier\\\": \\\"hot\\\", \\\"to_tier\\\": \\\"warm\\\", \\\"reason\\\": \\\"age_threshold\\\"}';

SELECT 'Real-time notifications sent!' as status;
\""

echo -e "\n${YELLOW}4. Event statistics...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
SELECT 
    event_type,
    COUNT(*) as event_count,
    MIN(created_at) as first_event,
    MAX(created_at) as last_event
FROM events.event_store
GROUP BY event_type
ORDER BY event_count DESC;
\""

echo -e "\n${GREEN}✅ Event Sourcing Demo Complete!${NC}"
echo -e "${GREEN}The system can now:${NC}"
echo -e "${GREEN}  • Track complete audit trail of all user actions${NC}"
echo -e "${GREEN}  • Replay events to reconstruct system state${NC}"
echo -e "${GREEN}  • Send real-time notifications for UI updates${NC}"
echo -e "${GREEN}  • Query event history for analytics${NC}" 