#!/bin/bash
# Section 11: Native PostgreSQL partitioning (alternative to hypertables)
# Stays within database scope - no application changes

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
echo -e "${BLUE}SECTION 11: NATIVE PARTITIONING IMPLEMENTATION${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Deploy native partitioning solution
echo -e "\n${YELLOW}Implementing PostgreSQL native partitioning...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "docker exec -i auren-postgres psql -U $DB_USER -d $DB_NAME" << 'EOSQL'

-- =============================================================================
-- NATIVE PARTITIONING FOR EVENT STORE (Already working, optimize it)
-- =============================================================================

-- Create partitions for next 6 months
DO $$
DECLARE
    start_date DATE := '2025-02-01';
    end_date DATE := '2025-08-01';
    partition_date DATE;
    partition_name TEXT;
BEGIN
    partition_date := start_date;
    WHILE partition_date < end_date LOOP
        partition_name := 'event_store_' || to_char(partition_date, 'YYYY_MM');
        
        -- Check if partition exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_class 
            WHERE relname = partition_name 
            AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'events')
        ) THEN
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS events.%I PARTITION OF events.event_store
                FOR VALUES FROM (%L) TO (%L)',
                partition_name,
                partition_date,
                partition_date + INTERVAL '1 month'
            );
            RAISE NOTICE 'Created partition: %', partition_name;
        END IF;
        
        partition_date := partition_date + INTERVAL '1 month';
    END LOOP;
END $$;

-- =============================================================================
-- HELPER FUNCTIONS FOR EVENT SOURCING
-- =============================================================================

-- Function to insert events with automatic versioning
CREATE OR REPLACE FUNCTION events.append_event(
    p_stream_id VARCHAR,
    p_event_type VARCHAR,
    p_event_data JSONB,
    p_created_by VARCHAR DEFAULT 'system',
    p_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
    v_stream_version INTEGER;
BEGIN
    -- Get next version for stream
    SELECT COALESCE(MAX(stream_version), 0) + 1
    INTO v_stream_version
    FROM events.event_store
    WHERE stream_id = p_stream_id;
    
    -- Insert event
    INSERT INTO events.event_store (
        stream_id, stream_version, event_type, 
        event_data, metadata, created_by
    ) VALUES (
        p_stream_id, v_stream_version, p_event_type,
        p_event_data, p_metadata, p_created_by
    ) RETURNING event_id INTO v_event_id;
    
    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to replay events for a stream
CREATE OR REPLACE FUNCTION events.replay_stream(
    p_stream_id VARCHAR,
    p_from_version INTEGER DEFAULT 1,
    p_to_version INTEGER DEFAULT NULL
) RETURNS TABLE (
    event_id UUID,
    stream_version INTEGER,
    event_type VARCHAR,
    event_data JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.event_id,
        e.stream_version,
        e.event_type,
        e.event_data,
        e.created_at
    FROM events.event_store e
    WHERE e.stream_id = p_stream_id
    AND e.stream_version >= p_from_version
    AND (p_to_version IS NULL OR e.stream_version <= p_to_version)
    ORDER BY e.stream_version;
END;
$$ LANGUAGE plpgsql;

-- Function to get current state from event stream
CREATE OR REPLACE FUNCTION events.get_stream_state(
    p_stream_id VARCHAR
) RETURNS JSONB AS $$
DECLARE
    v_state JSONB := '{}';
    v_event RECORD;
BEGIN
    -- Replay all events and build state
    FOR v_event IN 
        SELECT event_type, event_data 
        FROM events.event_store 
        WHERE stream_id = p_stream_id 
        ORDER BY stream_version
    LOOP
        -- Apply event to state (simplified - real implementation would use event handlers)
        v_state := v_state || jsonb_build_object(
            v_event.event_type, 
            v_event.event_data
        );
    END LOOP;
    
    RETURN v_state;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Add missing indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_event_store_created_at 
    ON events.event_store (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_event_store_event_data_gin 
    ON events.event_store USING GIN (event_data);

CREATE INDEX IF NOT EXISTS idx_event_store_metadata_gin 
    ON events.event_store USING GIN (metadata);

-- Index for common query patterns
CREATE INDEX IF NOT EXISTS idx_biometric_events_user_device_time 
    ON biometric_events (user_id, device_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_biometric_events_metric_time 
    ON biometric_events (metric_type, timestamp DESC);

-- =============================================================================
-- MATERIALIZED VIEWS AS ALTERNATIVE TO CONTINUOUS AGGREGATES
-- =============================================================================

-- Create standard materialized views instead of continuous aggregates
DROP MATERIALIZED VIEW IF EXISTS analytics.user_metrics_daily;
CREATE MATERIALIZED VIEW analytics.user_metrics_daily AS
SELECT 
    DATE(timestamp) as day,
    user_id,
    device_type,
    metric_type,
    COUNT(*) as reading_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    STDDEV(value) as stddev_value
FROM biometric_events
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY 1, 2, 3, 4;

-- Create indexes on materialized view
CREATE INDEX idx_user_metrics_daily_user 
    ON analytics.user_metrics_daily (user_id, day DESC);

-- Create refresh function
CREATE OR REPLACE FUNCTION analytics.refresh_user_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.user_metrics_daily;
    RAISE NOTICE 'Refreshed user_metrics_daily at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PARTITION MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function to create future partitions automatically
CREATE OR REPLACE FUNCTION events.create_monthly_partitions(
    p_months_ahead INTEGER DEFAULT 3
) RETURNS void AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_partition_date DATE;
    v_partition_name TEXT;
BEGIN
    v_start_date := DATE_TRUNC('month', CURRENT_DATE);
    v_end_date := v_start_date + (p_months_ahead || ' months')::INTERVAL;
    v_partition_date := v_start_date;
    
    WHILE v_partition_date < v_end_date LOOP
        v_partition_name := 'event_store_' || to_char(v_partition_date, 'YYYY_MM');
        
        IF NOT EXISTS (
            SELECT 1 FROM pg_class 
            WHERE relname = v_partition_name 
            AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'events')
        ) THEN
            EXECUTE format('
                CREATE TABLE events.%I PARTITION OF events.event_store
                FOR VALUES FROM (%L) TO (%L)',
                v_partition_name,
                v_partition_date,
                v_partition_date + INTERVAL '1 month'
            );
            RAISE NOTICE 'Created partition: %', v_partition_name;
        END IF;
        
        v_partition_date := v_partition_date + INTERVAL '1 month';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule partition creation (would use pg_cron in production)
-- SELECT cron.schedule('create-partitions', '0 0 1 * *', 'SELECT events.create_monthly_partitions()');

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Check what we created
SELECT 'Event sourcing functions:' as component, COUNT(*) as count
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'events')
UNION ALL
SELECT 'Performance indexes:', COUNT(*)
FROM pg_indexes
WHERE tablename IN ('event_store', 'biometric_events')
AND indexname LIKE 'idx_%'
UNION ALL
SELECT 'Event store partitions:', COUNT(*)
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'events' 
AND c.relname LIKE 'event_store_%'
AND c.relkind = 'r'
UNION ALL
SELECT 'Materialized views:', COUNT(*)
FROM pg_matviews
WHERE schemaname = 'analytics';

EOSQL

echo -e "\n${GREEN}✅ Native partitioning implementation complete!${NC}"
echo -e "${GREEN}Added:${NC}"
echo -e "${GREEN}  • Event sourcing helper functions${NC}"
echo -e "${GREEN}  • Native PostgreSQL partitions${NC}"
echo -e "${GREEN}  • Performance indexes${NC}"
echo -e "${GREEN}  • Materialized views (alternative to continuous aggregates)${NC}" 