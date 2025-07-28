#!/bin/bash
# Fix script for Section 11 deployment issues

set -e

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASSWORD=".HvddX+@6dArsKd"
DB_USER="auren_user"
DB_PASSWORD="auren_secure_2025"
DB_NAME="auren_production"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}SECTION 11 DEPLOYMENT FIX${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Execute SQL fixes
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec -i auren-postgres psql -U $DB_USER -d $DB_NAME" << 'EOSQL'

-- Fix 1: Create missing schemas
CREATE SCHEMA IF NOT EXISTS encrypted;
CREATE SCHEMA IF NOT EXISTS biometric;
GRANT USAGE ON SCHEMA encrypted TO auren_user;
GRANT USAGE ON SCHEMA biometric TO auren_user;
GRANT ALL ON ALL TABLES IN SCHEMA encrypted TO auren_user;
GRANT ALL ON ALL TABLES IN SCHEMA biometric TO auren_user;

-- Fix 2: Create key mappings table in encrypted schema
CREATE TABLE IF NOT EXISTS encrypted.key_mappings (
    section_11_key_id INTEGER,
    section_9_key_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (section_11_key_id, section_9_key_hash)
);

-- Fix 3: Create event store with proper hypertable configuration
DROP TABLE IF EXISTS events.event_store CASCADE;
CREATE TABLE events.event_store (
    event_id UUID DEFAULT gen_random_uuid(),
    stream_id VARCHAR(255) NOT NULL,
    stream_version INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(100) DEFAULT 'default',
    PRIMARY KEY (created_at, event_id)  -- Include partition key in primary key
);

-- Create indexes
CREATE INDEX idx_event_store_stream ON events.event_store (stream_id, stream_version DESC);
CREATE INDEX idx_event_store_type_time ON events.event_store (event_type, created_at DESC);
CREATE UNIQUE INDEX idx_event_store_stream_version ON events.event_store (stream_id, stream_version);

-- Convert to hypertable
SELECT create_hypertable('events.event_store', 'created_at', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Fix 4: Create continuous aggregates using correct column names
DROP MATERIALIZED VIEW IF EXISTS analytics.user_metrics_5min CASCADE;
CREATE MATERIALIZED VIEW analytics.user_metrics_5min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', timestamp) AS bucket,
    user_id,
    device_type,
    metric_type,
    COUNT(*) as reading_count,
    AVG(value) as avg_value,
    MAX(value) as max_value,
    MIN(value) as min_value
FROM biometric_events
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY bucket, user_id, device_type, metric_type
WITH NO DATA;

-- Fix 5: Create hourly aggregate
DROP MATERIALIZED VIEW IF EXISTS analytics.user_metrics_hourly CASCADE;
CREATE MATERIALIZED VIEW analytics.user_metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    user_id,
    COUNT(DISTINCT device_type) as active_devices,
    COUNT(*) as total_readings,
    AVG(value) as avg_value
FROM biometric_events
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY hour, user_id
WITH NO DATA;

-- Fix 6: Add refresh policies
SELECT add_continuous_aggregate_policy('analytics.user_metrics_5min',
    start_offset => INTERVAL '15 minutes',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy('analytics.user_metrics_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Fix 7: Create zk_proofs table in biometric schema
CREATE TABLE IF NOT EXISTS biometric.zk_proofs (
    proof_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    proof_type VARCHAR(100) NOT NULL,
    statement VARCHAR(255) NOT NULL,
    proof_data BYTEA NOT NULL,
    public_inputs JSONB,
    verification_key_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    verified_at TIMESTAMPTZ,
    verification_result BOOLEAN,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

CREATE INDEX idx_zk_proofs_user_time ON biometric.zk_proofs (user_id, created_at DESC);
CREATE INDEX idx_zk_proofs_type ON biometric.zk_proofs (proof_type, created_at DESC);

-- Fix 8: Enable compression on biometric_events (TimescaleDB way)
ALTER TABLE biometric_events SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'user_id,device_type',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Add compression policy
SELECT add_compression_policy('biometric_events', 
    compress_after => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Fix 9: Add retention policy to event store
SELECT add_retention_policy('events.event_store', 
    drop_after => INTERVAL '2 years',
    if_not_exists => TRUE
);

-- Verify fixes
SELECT 'Schemas created:' as status, string_agg(nspname, ', ') as schemas
FROM pg_namespace
WHERE nspname IN ('events', 'analytics', 'encrypted', 'biometric');

SELECT 'Event store created:' as status, 
       EXISTS(SELECT 1 FROM events.event_store LIMIT 1) as exists;

SELECT 'Continuous aggregates:' as status, 
       COUNT(*) as count
FROM timescaledb_information.continuous_aggregates
WHERE view_name LIKE 'user_metrics_%';

EOSQL

echo -e "${GREEN}✓ Section 11 deployment fixes applied!${NC}"

# Test event sourcing
echo -e "\n${YELLOW}Testing event sourcing...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
INSERT INTO events.event_store (stream_id, stream_version, event_type, event_data, created_by)
VALUES ('test:001', 1, 'test_event', '{\"action\": \"deployment_test\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}', 'fix_script');

SELECT event_id, event_type, event_data FROM events.event_store WHERE stream_id = 'test:001';
\""

# Refresh aggregates with initial data
echo -e "\n${YELLOW}Refreshing continuous aggregates...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec auren-postgres psql -U $DB_USER -d $DB_NAME -c \"
CALL refresh_continuous_aggregate('analytics.user_metrics_5min', NULL, NULL);
CALL refresh_continuous_aggregate('analytics.user_metrics_hourly', NULL, NULL);
\""

echo -e "\n${GREEN}Section 11 deployment fixes complete!${NC}" 