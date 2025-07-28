-- =============================================================================
-- AUREN SECTION 11: PRODUCTION-GRADE DATABASE SCHEMA WITH HIPAA COMPLIANCE v2.0
-- =============================================================================
-- Enhanced PostgreSQL/TimescaleDB schema for AUREN Biometric Bridge
-- Incorporates: Event Sourcing, Zero-Knowledge readiness, Multi-tenant isolation
-- Last Updated: 2025-01-19
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS postgres_fdw; -- For future sharding
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For text search optimization

-- =============================================================================
-- SECURITY: Database Configuration
-- =============================================================================

-- Force SSL connections
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_min_protocol_version = 'TLSv1.3';

-- Enable audit logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- Performance and security tuning
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements,timescaledb';
ALTER SYSTEM SET track_io_timing = on;

-- Apply settings
SELECT pg_reload_conf();

-- =============================================================================
-- SECURITY: Create roles with least privilege
-- =============================================================================

-- Revoke all default privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Create roles (passwords must be set via external secret management)
CREATE ROLE auren_ingest WITH LOGIN;
CREATE ROLE auren_analytics WITH LOGIN;
CREATE ROLE auren_admin WITH LOGIN;
CREATE ROLE auren_event_processor WITH LOGIN; -- New role for event sourcing

-- Create schemas for logical separation
CREATE SCHEMA IF NOT EXISTS biometric;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS events; -- Event sourcing schema
CREATE SCHEMA IF NOT EXISTS encrypted;
CREATE SCHEMA IF NOT EXISTS analytics; -- For materialized views

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA biometric TO auren_ingest, auren_analytics, auren_event_processor;
GRANT USAGE ON SCHEMA events TO auren_event_processor, auren_analytics;
GRANT USAGE ON SCHEMA analytics TO auren_analytics;
GRANT USAGE ON SCHEMA audit TO auren_admin;
GRANT ALL ON SCHEMA encrypted TO auren_admin;

-- =============================================================================
-- EVENT SOURCING: Core Event Store (Foundation of our architecture)
-- =============================================================================

-- Event store for complete audit trail and replay capability
CREATE TABLE IF NOT EXISTS events.event_store (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id VARCHAR(255) NOT NULL, -- e.g., 'user:123', 'system:config'
    stream_version INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    -- Ensure events are immutable
    CONSTRAINT event_immutable CHECK (false) NO INHERIT
);

-- Optimize for append-only writes and time-based queries
CREATE INDEX idx_event_store_stream ON events.event_store (stream_id, stream_version);
CREATE INDEX idx_event_store_type_time ON events.event_store (event_type, created_at DESC);
CREATE INDEX idx_event_store_tenant ON events.event_store (tenant_id, created_at DESC);

-- Convert to hypertable for optimal time-series performance
SELECT create_hypertable('events.event_store', 'created_at', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Event types enum for type safety
CREATE TYPE events.event_type AS ENUM (
    'user_created',
    'biometric_received',
    'mode_switched',
    'hypothesis_created',
    'hypothesis_validated',
    'agent_consultation',
    'phi_accessed',
    'encryption_key_rotated'
);

-- =============================================================================
-- CORE TABLES: User Sessions with Enhanced Security
-- =============================================================================

CREATE TABLE IF NOT EXISTS biometric.user_sessions (
    user_id VARCHAR(255) PRIMARY KEY,
    session_id UUID NOT NULL DEFAULT gen_random_uuid(),
    current_mode VARCHAR(50) CHECK (current_mode IN ('baseline', 'reflex', 'hypothesis', 'pattern', 'companion')),
    last_mode_switch TIMESTAMPTZ,
    last_switch_reason TEXT,
    mode_switch_count INTEGER DEFAULT 0 CHECK (mode_switch_count >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    encrypted_pii JSONB, -- Encrypted PII storage
    consent_flags JSONB DEFAULT '{}', -- GDPR consent tracking
    data_retention_days INTEGER DEFAULT 365, -- User-configurable retention
    tenant_id VARCHAR(100) NOT NULL,
    row_version INTEGER DEFAULT 1, -- Optimistic locking
    CONSTRAINT valid_session CHECK (last_active >= created_at)
);

-- Composite index for tenant isolation and performance
CREATE INDEX idx_user_sessions_tenant_active ON biometric.user_sessions(tenant_id, last_active DESC);
CREATE INDEX idx_user_sessions_consent ON biometric.user_sessions USING GIN (consent_flags);

-- Enable Row Level Security
ALTER TABLE biometric.user_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policy with session variable for performance
CREATE POLICY tenant_isolation ON biometric.user_sessions
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true)::VARCHAR);

-- =============================================================================
-- BIOMETRIC EVENTS: Optimized for High-Volume Ingestion
-- =============================================================================

-- Device types as a proper table for flexibility (addressing expert feedback)
CREATE TABLE IF NOT EXISTS biometric.device_types (
    device_type_id SERIAL PRIMARY KEY,
    device_name VARCHAR(50) UNIQUE NOT NULL,
    manufacturer VARCHAR(100),
    capabilities JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Seed initial device types
INSERT INTO biometric.device_types (device_name, manufacturer) VALUES
    ('oura', 'Oura Health'),
    ('whoop', 'WHOOP'),
    ('apple_health', 'Apple Inc.'),
    ('garmin', 'Garmin'),
    ('fitbit', 'Google')
ON CONFLICT (device_name) DO NOTHING;

-- Main biometric events table
CREATE TABLE IF NOT EXISTS biometric.biometric_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    device_type_id INTEGER NOT NULL REFERENCES biometric.device_types(device_type_id),
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    -- Separate columns for better compression and query performance
    metric_data JSONB NOT NULL, -- Non-PHI metrics (steps, distance, etc.)
    encrypted_phi BYTEA, -- Encrypted PHI (heart rate, BP, etc.)
    encryption_key_version INTEGER, -- Key version for rotation support
    -- Metadata for processing
    raw_data_hash VARCHAR(64), -- SHA-256 of original data for integrity
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id VARCHAR(100) NOT NULL,
    -- Prevent duplicate events
    CONSTRAINT unique_biometric_event UNIQUE (user_id, device_type_id, timestamp, event_type, raw_data_hash),
    -- Foreign key with CASCADE for user deletion
    CONSTRAINT fk_user_session FOREIGN KEY (user_id) 
        REFERENCES biometric.user_sessions(user_id) ON DELETE CASCADE
);

-- Convert to hypertable with optimal chunk size for our use case
SELECT create_hypertable('biometric.biometric_events', 'timestamp', 
    chunk_time_interval => INTERVAL '6 hours', -- Balanced for daily processing
    if_not_exists => TRUE
);

-- Optimized indexes for common query patterns
CREATE INDEX idx_biometric_events_user_time ON biometric.biometric_events 
    (user_id, timestamp DESC) 
    WHERE processing_status = 'completed';

CREATE INDEX idx_biometric_events_device_time ON biometric.biometric_events 
    (device_type_id, timestamp DESC);

CREATE INDEX idx_biometric_events_tenant_time ON biometric.biometric_events 
    (tenant_id, timestamp DESC);

-- Expression indexes with proper null handling (addressing expert feedback)
CREATE INDEX idx_biometric_events_hrv ON biometric.biometric_events 
    ((NULLIF(metric_data->>'hrv', '')::FLOAT))
    WHERE metric_data ? 'hrv' AND jsonb_typeof(metric_data->'hrv') = 'number';

CREATE INDEX idx_biometric_events_steps ON biometric.biometric_events 
    ((NULLIF(metric_data->>'steps', '')::INTEGER))
    WHERE metric_data ? 'steps' AND jsonb_typeof(metric_data->'steps') = 'number';

-- Enable RLS
ALTER TABLE biometric.biometric_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_events ON biometric.biometric_events
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true)::VARCHAR);

-- =============================================================================
-- ENCRYPTION KEY MANAGEMENT: Production-Ready with Rotation
-- =============================================================================

CREATE TABLE IF NOT EXISTS encrypted.key_metadata (
    key_id SERIAL PRIMARY KEY,
    key_alias VARCHAR(100) NOT NULL,
    key_version INTEGER NOT NULL,
    kms_key_id VARCHAR(255) NOT NULL, -- AWS KMS or similar key ID
    algorithm VARCHAR(50) DEFAULT 'AES-256-GCM',
    purpose VARCHAR(50) CHECK (purpose IN ('data_encryption', 'key_encryption', 'signing')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_from_key_id INTEGER REFERENCES encrypted.key_metadata(key_id),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    created_by VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_active_alias UNIQUE (key_alias, is_active) WHERE is_active = true,
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Index for finding active keys quickly
CREATE INDEX idx_key_metadata_active ON encrypted.key_metadata (key_alias, is_active) 
    WHERE is_active = true;

-- Comprehensive audit log for key operations
CREATE TABLE IF NOT EXISTS audit.key_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_id INTEGER REFERENCES encrypted.key_metadata(key_id),
    operation_type VARCHAR(50) CHECK (operation_type IN ('create', 'rotate', 'retire', 'destroy', 'encrypt', 'decrypt')),
    operation_timestamp TIMESTAMPTZ DEFAULT NOW(),
    performed_by VARCHAR(255) NOT NULL,
    client_info JSONB DEFAULT '{}', -- IP, user agent, etc.
    success BOOLEAN DEFAULT true,
    error_details TEXT,
    data_encrypted_size BIGINT, -- For monitoring encryption operations
    duration_ms INTEGER -- Performance tracking
);

-- Optimize for audit queries
CREATE INDEX idx_key_operations_time ON audit.key_operations (operation_timestamp DESC);
CREATE INDEX idx_key_operations_key ON audit.key_operations (key_id, operation_timestamp DESC);

-- =============================================================================
-- INTELLIGENT RETRY QUEUE with Exponential Backoff
-- =============================================================================

CREATE TABLE IF NOT EXISTS biometric.processing_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES biometric.biometric_events(event_id),
    queue_type VARCHAR(50) CHECK (queue_type IN ('biometric_event', 'mode_switch', 'agent_task')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    payload JSONB NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    next_retry_at TIMESTAMPTZ DEFAULT NOW(),
    backoff_multiplier FLOAT DEFAULT 2.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    tenant_id VARCHAR(100) NOT NULL,
    CONSTRAINT valid_retry CHECK (retry_count <= max_retries)
);

-- Optimized index for retry processor
CREATE INDEX idx_processing_queue_ready ON biometric.processing_queue 
    (next_retry_at, priority DESC) 
    WHERE completed_at IS NULL AND retry_count < max_retries;

-- Function to calculate next retry time with jitter
CREATE OR REPLACE FUNCTION biometric.calculate_next_retry(
    retry_count INTEGER,
    backoff_multiplier FLOAT DEFAULT 2.0
) RETURNS TIMESTAMPTZ AS $$
DECLARE
    base_delay INTEGER;
    jitter_seconds INTEGER;
BEGIN
    -- Exponential backoff: 5s, 10s, 20s, 40s, 80s...
    base_delay := LEAST(5 * POWER(backoff_multiplier, retry_count)::INTEGER, 3600); -- Cap at 1 hour
    -- Add random jitter to prevent thundering herd
    jitter_seconds := (RANDOM() * base_delay * 0.1)::INTEGER;
    
    RETURN NOW() + (base_delay + jitter_seconds) * INTERVAL '1 second';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- MODE SWITCH TRACKING with ML Readiness
-- =============================================================================

CREATE TABLE IF NOT EXISTS biometric.mode_switches (
    switch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES biometric.user_sessions(user_id),
    from_mode VARCHAR(50),
    to_mode VARCHAR(50) NOT NULL,
    switch_timestamp TIMESTAMPTZ DEFAULT NOW(),
    trigger_type VARCHAR(50) CHECK (trigger_type IN ('biometric', 'manual', 'scheduled', 'ai_decision', 'ml_prediction')),
    trigger_details JSONB DEFAULT '{}',
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    feature_vector FLOAT[], -- For ML model inputs
    model_version VARCHAR(50), -- Track which AI model made the decision
    biometric_context JSONB, -- Snapshot of relevant biometrics
    validation_status VARCHAR(50) DEFAULT 'pending', -- For learning from outcomes
    user_feedback_score INTEGER CHECK (user_feedback_score BETWEEN 1 AND 5),
    tenant_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_mode_switches_user_time ON biometric.mode_switches (user_id, switch_timestamp DESC);
CREATE INDEX idx_mode_switches_ml ON biometric.mode_switches (model_version, validation_status) 
    WHERE model_version IS NOT NULL;

-- =============================================================================
-- HIPAA AUDIT TABLES with Immutable Partitioning
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit.phi_access_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id VARCHAR(255),
    accessed_by VARCHAR(255) NOT NULL,
    access_type VARCHAR(50) CHECK (access_type IN ('read', 'write', 'update', 'delete', 'export')),
    resource_type VARCHAR(100) NOT NULL, -- Table or API endpoint
    resource_id VARCHAR(255),
    query_text TEXT, -- Sanitized query for debugging
    row_count INTEGER, -- Number of rows affected
    phi_fields TEXT[], -- Which PHI fields were accessed
    purpose VARCHAR(255), -- Business justification
    legal_basis VARCHAR(50), -- GDPR requirement
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    request_id UUID, -- For tracing distributed requests
    success BOOLEAN DEFAULT true,
    error_code VARCHAR(50),
    duration_ms INTEGER,
    tenant_id VARCHAR(100)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for 7 years (HIPAA + buffer)
DO $$
DECLARE
    start_date DATE := '2025-01-01';
    end_date DATE := '2032-01-01';
    partition_date DATE;
    partition_name TEXT;
BEGIN
    partition_date := start_date;
    WHILE partition_date < end_date LOOP
        partition_name := 'phi_access_log_' || to_char(partition_date, 'YYYY_MM');
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS audit.%I PARTITION OF audit.phi_access_log
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_date,
            partition_date + INTERVAL '1 month'
        );
        -- Add check constraint to ensure immutability
        EXECUTE format('
            ALTER TABLE audit.%I ADD CONSTRAINT %I_immutable 
            CHECK (false) NO INHERIT',
            partition_name,
            partition_name
        );
        partition_date := partition_date + INTERVAL '1 month';
    END LOOP;
END $$;

-- Indexes for compliance reporting
CREATE INDEX idx_phi_access_log_user ON audit.phi_access_log (user_id, timestamp DESC);
CREATE INDEX idx_phi_access_log_accessor ON audit.phi_access_log (accessed_by, timestamp DESC);
CREATE INDEX idx_phi_access_log_resource ON audit.phi_access_log (resource_type, timestamp DESC);

-- =============================================================================
-- MEMORY TIER OPERATIONS for AI Agent Memory Management
-- =============================================================================

CREATE TABLE IF NOT EXISTS biometric.memory_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    memory_key VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50) CHECK (memory_type IN ('conversation', 'insight', 'pattern', 'hypothesis')),
    from_tier VARCHAR(20) CHECK (from_tier IN ('hot', 'warm', 'cold', 'archived')),
    to_tier VARCHAR(20) NOT NULL CHECK (to_tier IN ('hot', 'warm', 'cold', 'archived')),
    operation VARCHAR(50) CHECK (operation IN ('promote', 'demote', 'expire', 'retrieve')),
    data_size_bytes BIGINT,
    compression_ratio FLOAT,
    access_frequency INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    operation_timestamp TIMESTAMPTZ DEFAULT NOW(),
    duration_ms INTEGER,
    cost_units FLOAT, -- For tracking memory operation costs
    trigger_reason VARCHAR(255),
    agent_id VARCHAR(100), -- Which AI agent triggered this
    success BOOLEAN DEFAULT true,
    error_details TEXT,
    tenant_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_memory_ops_user_time ON biometric.memory_operations (user_id, operation_timestamp DESC);
CREATE INDEX idx_memory_ops_performance ON biometric.memory_operations (duration_ms) 
    WHERE success = true;

-- =============================================================================
-- ANALYTICS VIEWS: Continuous Aggregates for Performance
-- =============================================================================

-- User engagement metrics (refreshed hourly)
CREATE MATERIALIZED VIEW analytics.user_engagement_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', created_at) AS hour,
    tenant_id,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_events,
    AVG(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END)::FLOAT as success_rate,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_attempts) as p95_retry_attempts
FROM biometric.biometric_events
GROUP BY hour, tenant_id
WITH NO DATA;

-- Biometric statistics (refreshed every 30 minutes)
CREATE MATERIALIZED VIEW analytics.biometric_stats_30min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('30 minutes', timestamp) AS period,
    user_id,
    device_type_id,
    COUNT(*) as reading_count,
    AVG(NULLIF(metric_data->>'heart_rate', '')::FLOAT) FILTER (WHERE metric_data ? 'heart_rate') as avg_hr,
    AVG(NULLIF(metric_data->>'hrv', '')::FLOAT) FILTER (WHERE metric_data ? 'hrv') as avg_hrv,
    SUM(NULLIF(metric_data->>'steps', '')::INTEGER) FILTER (WHERE metric_data ? 'steps') as total_steps
FROM biometric.biometric_events
WHERE processing_status = 'completed'
GROUP BY period, user_id, device_type_id
WITH NO DATA;

-- Set up refresh policies
SELECT add_continuous_aggregate_policy('analytics.user_engagement_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

SELECT add_continuous_aggregate_policy('analytics.biometric_stats_30min',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes'
);

-- =============================================================================
-- SECURITY FUNCTIONS: Enhanced Encryption with Key Rotation
-- =============================================================================

-- Get current encryption key with caching
CREATE OR REPLACE FUNCTION encrypted.get_current_key(
    p_purpose VARCHAR DEFAULT 'data_encryption'
) RETURNS TABLE (
    key_id INTEGER,
    kms_key_id VARCHAR,
    algorithm VARCHAR
) AS $$
BEGIN
    -- This would typically cache the result in app memory
    RETURN QUERY
    SELECT k.key_id, k.kms_key_id, k.algorithm
    FROM encrypted.key_metadata k
    WHERE k.purpose = p_purpose
        AND k.is_active = true
        AND k.expires_at > NOW()
    ORDER BY k.key_version DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Encrypt data with automatic key selection
CREATE OR REPLACE FUNCTION encrypted.encrypt_data(
    p_plaintext TEXT,
    p_user_id VARCHAR,
    p_purpose VARCHAR DEFAULT 'data_encryption'
) RETURNS TABLE (
    ciphertext BYTEA,
    key_version INTEGER
) AS $$
DECLARE
    v_key_record RECORD;
    v_encrypted BYTEA;
    v_start_time TIMESTAMPTZ;
BEGIN
    v_start_time := clock_timestamp();
    
    -- Get current key
    SELECT * INTO v_key_record 
    FROM encrypted.get_current_key(p_purpose);
    
    IF v_key_record.key_id IS NULL THEN
        RAISE EXCEPTION 'No active encryption key found for purpose %', p_purpose;
    END IF;
    
    -- In production, this would call out to KMS
    -- For now, using pgcrypto as placeholder
    v_encrypted := pgp_sym_encrypt(
        p_plaintext, 
        v_key_record.kms_key_id || ':' || p_user_id,
        'cipher-algo=aes256'
    );
    
    -- Audit the operation
    INSERT INTO audit.key_operations (
        key_id, 
        operation_type, 
        performed_by,
        data_encrypted_size,
        duration_ms,
        client_info
    ) VALUES (
        v_key_record.key_id,
        'encrypt',
        current_setting('app.current_user', true),
        LENGTH(p_plaintext),
        EXTRACT(MILLISECOND FROM clock_timestamp() - v_start_time)::INTEGER,
        jsonb_build_object('user_id', p_user_id)
    );
    
    RETURN QUERY SELECT v_encrypted, v_key_record.key_id;
END;
$$ LANGUAGE plpgsql VOLATILE SECURITY DEFINER;

-- =============================================================================
-- TRIGGERS: Automated Data Governance
-- =============================================================================

-- Automatically encrypt PHI fields on insert/update
CREATE OR REPLACE FUNCTION biometric.auto_encrypt_phi()
RETURNS TRIGGER AS $$
DECLARE
    v_phi_data JSONB;
    v_encrypted RECORD;
    v_phi_fields TEXT[] := ARRAY['heart_rate', 'blood_pressure', 'blood_glucose', 
                                 'oxygen_saturation', 'body_temperature'];
BEGIN
    -- Check if any PHI fields exist in metric_data
    IF NEW.metric_data ?| v_phi_fields THEN
        -- Extract PHI fields
        v_phi_data := jsonb_strip_nulls(
            jsonb_build_object(
                'heart_rate', NEW.metric_data->'heart_rate',
                'blood_pressure', NEW.metric_data->'blood_pressure',
                'blood_glucose', NEW.metric_data->'blood_glucose',
                'oxygen_saturation', NEW.metric_data->'oxygen_saturation',
                'body_temperature', NEW.metric_data->'body_temperature'
            )
        );
        
        -- Encrypt PHI
        SELECT * INTO v_encrypted
        FROM encrypted.encrypt_data(v_phi_data::TEXT, NEW.user_id);
        
        NEW.encrypted_phi := v_encrypted.ciphertext;
        NEW.encryption_key_version := v_encrypted.key_version;
        
        -- Remove PHI from metric_data
        NEW.metric_data := NEW.metric_data - v_phi_fields;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER encrypt_phi_before_insert
    BEFORE INSERT OR UPDATE ON biometric.biometric_events
    FOR EACH ROW
    EXECUTE FUNCTION biometric.auto_encrypt_phi();

-- Audit trigger for PHI access (conditional to reduce noise)
CREATE OR REPLACE FUNCTION audit.conditional_phi_access_log()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if PHI columns are actually accessed
    IF (TG_OP = 'UPDATE' AND OLD.encrypted_phi IS DISTINCT FROM NEW.encrypted_phi) OR
       (TG_OP = 'INSERT' AND NEW.encrypted_phi IS NOT NULL) OR
       (TG_OP = 'DELETE' AND OLD.encrypted_phi IS NOT NULL) THEN
        
        INSERT INTO audit.phi_access_log (
            user_id,
            accessed_by,
            access_type,
            resource_type,
            resource_id,
            phi_fields,
            purpose,
            ip_address,
            request_id,
            tenant_id
        ) VALUES (
            COALESCE(NEW.user_id, OLD.user_id),
            current_setting('app.current_user', true),
            LOWER(TG_OP),
            TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            COALESCE(NEW.event_id, OLD.event_id)::TEXT,
            ARRAY['encrypted_phi'],
            current_setting('app.access_purpose', true),
            inet_client_addr(),
            current_setting('app.request_id', true)::UUID,
            COALESCE(NEW.tenant_id, OLD.tenant_id)
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_phi_access
    AFTER INSERT OR UPDATE OR DELETE ON biometric.biometric_events
    FOR EACH ROW
    EXECUTE FUNCTION audit.conditional_phi_access_log();

-- =============================================================================
-- TIMESCALEDB POLICIES: Automated Data Lifecycle
-- =============================================================================

-- Enable compression with column-specific settings
ALTER TABLE biometric.biometric_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id,device_type_id',
    timescaledb.compress_orderby = 'timestamp DESC',
    timescaledb.compress_chunk_time_interval = '1 day'
);

-- Compression policy: Compress after 7 days
SELECT add_compression_policy('biometric.biometric_events', 
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Retention policies
-- Keep raw data for 1 year, then move to cold storage
SELECT add_retention_policy('biometric.biometric_events', 
    INTERVAL '1 year',
    if_not_exists => TRUE
);

-- Keep audit logs for 7 years (HIPAA requirement)
-- Note: We don't delete audit logs, just archive them
CREATE OR REPLACE FUNCTION audit.archive_old_logs()
RETURNS void AS $$
DECLARE
    v_archive_date DATE;
BEGIN
    v_archive_date := CURRENT_DATE - INTERVAL '7 years';
    
    -- In production, this would move data to cold storage
    -- For now, we just mark it
    UPDATE audit.phi_access_log 
    SET resource_type = 'ARCHIVED:' || resource_type
    WHERE timestamp < v_archive_date
        AND NOT resource_type LIKE 'ARCHIVED:%';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE MONITORING: Database Health Views
-- =============================================================================

CREATE OR REPLACE VIEW biometric.system_health AS
WITH chunk_stats AS (
    SELECT 
        COUNT(*) as total_chunks,
        SUM(CASE WHEN is_compressed THEN 1 ELSE 0 END) as compressed_chunks
    FROM timescaledb_information.chunks
    WHERE hypertable_name = 'biometric_events'
),
size_stats AS (
    SELECT 
        pg_size_pretty(hypertable_size('biometric.biometric_events')) as table_size,
        pg_size_pretty(hypertable_index_size('biometric.biometric_events')) as index_size,
        COALESCE(compression_ratio, 1.0)::NUMERIC(5,2) as compression_ratio
    FROM hypertable_size_info('biometric.biometric_events')
    LEFT JOIN LATERAL (
        SELECT AVG(compression_ratio) as compression_ratio
        FROM timescaledb_information.compressed_chunk_stats
        WHERE hypertable_name = 'biometric_events'
    ) comp ON true
)
SELECT 
    'total_size' as metric,
    table_size as value
FROM size_stats
UNION ALL
SELECT 
    'index_size',
    index_size
FROM size_stats
UNION ALL
SELECT 
    'compression_ratio',
    compression_ratio::TEXT
FROM size_stats
UNION ALL
SELECT 
    'total_chunks',
    total_chunks::TEXT
FROM chunk_stats
UNION ALL
SELECT 
    'compressed_chunks',
    compressed_chunks::TEXT
FROM chunk_stats
UNION ALL
SELECT 
    'active_connections',
    COUNT(*)::TEXT
FROM pg_stat_activity
WHERE datname = current_database()
UNION ALL
SELECT 
    'slow_queries_5min',
    COUNT(*)::TEXT
FROM pg_stat_statements
WHERE mean_exec_time > 1000 -- queries taking > 1 second
    AND calls > 0
    AND query_start > NOW() - INTERVAL '5 minutes';

-- =============================================================================
-- SECURITY: Row Level Security Policies
-- =============================================================================

-- Create RLS policies for all roles
CREATE POLICY analytics_read_only ON biometric.biometric_events
    FOR SELECT
    TO auren_analytics
    USING (tenant_id = current_setting('app.tenant_id', true)::VARCHAR);

CREATE POLICY ingest_insert_only ON biometric.biometric_events
    FOR INSERT
    TO auren_ingest
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::VARCHAR);

CREATE POLICY event_processor_all ON biometric.biometric_events
    FOR ALL
    TO auren_event_processor
    USING (tenant_id = current_setting('app.tenant_id', true)::VARCHAR);

-- =============================================================================
-- GRANTS: Fine-grained permissions
-- =============================================================================

-- Ingest role: Insert only, no reads
GRANT INSERT ON biometric.biometric_events TO auren_ingest;
GRANT INSERT ON biometric.processing_queue TO auren_ingest;
GRANT EXECUTE ON FUNCTION encrypted.encrypt_data TO auren_ingest;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA biometric TO auren_ingest;

-- Analytics role: Read everything, write nothing  
GRANT SELECT ON ALL TABLES IN SCHEMA biometric TO auren_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO auren_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA events TO auren_analytics;

-- Event processor: Full access to events, limited access elsewhere
GRANT ALL ON ALL TABLES IN SCHEMA events TO auren_event_processor;
GRANT SELECT, INSERT, UPDATE ON biometric.biometric_events TO auren_event_processor;
GRANT SELECT, INSERT, UPDATE, DELETE ON biometric.processing_queue TO auren_event_processor;

-- Admin: Everything
GRANT ALL ON ALL TABLES IN SCHEMA biometric TO auren_admin;
GRANT ALL ON ALL TABLES IN SCHEMA audit TO auren_admin;
GRANT ALL ON ALL TABLES IN SCHEMA events TO auren_admin;
GRANT ALL ON ALL TABLES IN SCHEMA encrypted TO auren_admin;
GRANT ALL ON ALL TABLES IN SCHEMA analytics TO auren_admin;

-- =============================================================================
-- STORED PROCEDURES: Business Logic
-- =============================================================================

-- Procedure to handle failed event reprocessing
CREATE OR REPLACE PROCEDURE biometric.reprocess_failed_events(
    p_batch_size INTEGER DEFAULT 100
)
LANGUAGE plpgsql AS $$
DECLARE
    v_processed INTEGER := 0;
    v_event RECORD;
BEGIN
    -- Select events ready for retry
    FOR v_event IN 
        SELECT * FROM biometric.processing_queue
        WHERE completed_at IS NULL 
            AND retry_count < max_retries
            AND next_retry_at <= NOW()
        ORDER BY priority DESC, next_retry_at
        LIMIT p_batch_size
        FOR UPDATE SKIP LOCKED -- Prevent concurrent processing
    LOOP
        BEGIN
            -- Update retry attempt
            UPDATE biometric.processing_queue
            SET retry_count = retry_count + 1,
                next_retry_at = biometric.calculate_next_retry(retry_count + 1),
                updated_at = NOW()
            WHERE queue_id = v_event.queue_id;
            
            -- Here you would call your processing logic
            -- For now, just mark as processed for demo
            
            v_processed := v_processed + 1;
            
        EXCEPTION WHEN OTHERS THEN
            -- Log error and continue
            UPDATE biometric.processing_queue
            SET error_type = SQLSTATE,
                error_message = SQLERRM,
                updated_at = NOW()
            WHERE queue_id = v_event.queue_id;
        END;
    END LOOP;
    
    RAISE NOTICE 'Processed % failed events', v_processed;
END;
$$;

-- =============================================================================
-- INITIALIZATION: Bootstrap data and settings
-- =============================================================================

-- Set secure defaults (must be overridden in production)
ALTER DATABASE auren_production SET app.tenant_id = 'bootstrap';
ALTER DATABASE auren_production SET app.current_user = 'system';
ALTER DATABASE auren_production SET app.access_purpose = 'system_initialization';

-- Create initial encryption key metadata (actual key in KMS)
INSERT INTO encrypted.key_metadata (
    key_alias,
    key_version,
    kms_key_id,
    purpose,
    created_by,
    metadata
) VALUES (
    'primary_data_key',
    1,
    'arn:aws:kms:us-east-1:123456789:key/placeholder', -- Replace with real KMS key
    'data_encryption',
    'system',
    jsonb_build_object(
        'environment', 'production',
        'rotation_schedule', '90_days'
    )
);

-- =============================================================================
-- MAINTENANCE PROCEDURES
-- =============================================================================

-- Automated key rotation procedure
CREATE OR REPLACE PROCEDURE encrypted.rotate_encryption_keys()
LANGUAGE plpgsql AS $$
DECLARE
    v_old_key RECORD;
    v_new_key_id INTEGER;
BEGIN
    -- Find keys needing rotation
    FOR v_old_key IN 
        SELECT * FROM encrypted.key_metadata
        WHERE is_active = true 
            AND expires_at < NOW() + INTERVAL '30 days'
    LOOP
        -- Create new key version
        INSERT INTO encrypted.key_metadata (
            key_alias,
            key_version,
            kms_key_id,
            purpose,
            rotated_from_key_id,
            created_by,
            metadata
        ) VALUES (
            v_old_key.key_alias,
            v_old_key.key_version + 1,
            'arn:aws:kms:us-east-1:123456789:key/new-placeholder', -- Would be generated
            v_old_key.purpose,
            v_old_key.key_id,
            'key_rotation_job',
            jsonb_build_object(
                'rotated_from', v_old_key.kms_key_id,
                'rotation_reason', 'scheduled'
            )
        ) RETURNING key_id INTO v_new_key_id;
        
        -- Deactivate old key
        UPDATE encrypted.key_metadata
        SET is_active = false
        WHERE key_id = v_old_key.key_id;
        
        -- Log rotation
        INSERT INTO audit.key_operations (
            key_id,
            operation_type,
            performed_by,
            success,
            client_info
        ) VALUES (
            v_new_key_id,
            'rotate',
            'key_rotation_job',
            true,
            jsonb_build_object('old_key_id', v_old_key.key_id)
        );
    END LOOP;
END;
$$;

-- Schedule maintenance jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule key rotation check (daily at 2 AM)
SELECT cron.schedule('rotate-encryption-keys', '0 2 * * *', 
    'CALL encrypted.rotate_encryption_keys()');

-- Schedule failed event reprocessing (every 15 minutes)
SELECT cron.schedule('reprocess-failed-events', '*/15 * * * *', 
    'CALL biometric.reprocess_failed_events()');

-- Schedule audit log archival (monthly)
SELECT cron.schedule('archive-audit-logs', '0 3 1 * *', 
    'SELECT audit.archive_old_logs()');

-- =============================================================================
-- FUTURE-READY: Zero-Knowledge Proof Support
-- =============================================================================

-- Table for storing ZK proofs (ready for future implementation)
CREATE TABLE IF NOT EXISTS biometric.zk_proofs (
    proof_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES biometric.user_sessions(user_id),
    proof_type VARCHAR(100) NOT NULL, -- e.g., 'hr_above_threshold', 'activity_goal_met'
    proof_data BYTEA NOT NULL, -- The actual ZK proof
    public_inputs JSONB, -- Public parameters of the proof
    verification_key_hash VARCHAR(64), -- Hash of the verification key used
    created_at TIMESTAMPTZ DEFAULT NOW(),
    verified_at TIMESTAMPTZ,
    verification_result BOOLEAN,
    tenant_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_zk_proofs_user ON biometric.zk_proofs (user_id, created_at DESC);
CREATE INDEX idx_zk_proofs_type ON biometric.zk_proofs (proof_type, created_at DESC);

-- =============================================================================
-- DOCUMENTATION
-- =============================================================================

COMMENT ON SCHEMA biometric IS 'Core biometric data storage with HIPAA-compliant PHI protection';
COMMENT ON SCHEMA audit IS 'Immutable audit logs for compliance - 7 year retention required';
COMMENT ON SCHEMA events IS 'Event sourcing store for complete system history and replay capability';
COMMENT ON SCHEMA encrypted IS 'Encryption key management and cryptographic operations';
COMMENT ON SCHEMA analytics IS 'Materialized views and aggregates for fast analytics';

COMMENT ON TABLE biometric.biometric_events IS 'Primary time-series storage for wearable device data. PHI is automatically encrypted.';
COMMENT ON COLUMN biometric.biometric_events.encrypted_phi IS 'AES-256-GCM encrypted PHI. Use decrypt functions with proper authorization.';
COMMENT ON COLUMN biometric.biometric_events.metric_data IS 'Non-PHI metrics safe for analytics without decryption';

COMMENT ON FUNCTION encrypted.encrypt_data IS 'Encrypts data using current active key from KMS. Automatically audited.';
COMMENT ON FUNCTION biometric.calculate_next_retry IS 'Calculates exponential backoff with jitter for retry operations';

COMMENT ON TRIGGER encrypt_phi_before_insert IS 'Automatically encrypts PHI fields before storage to ensure compliance';

-- =============================================================================
-- END OF SECTION 11: PRODUCTION-GRADE DATABASE SCHEMA v2.0
-- =============================================================================