-- =============================================================================
-- SECTION 9: Security & Compliance Database Migration
-- =============================================================================
-- Adds security tables for authentication, PHI encryption, audit logging,
-- and rate limiting to support the biometric system security enhancement layer.
-- 
-- Run this migration to add security features to the existing AUREN database.
-- Created: 2025-01-28
-- =============================================================================

-- API Key Management Table with Prefix Indexing for O(1) lookup
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(16) UNIQUE NOT NULL,  -- Public identifier
    key_prefix VARCHAR(16) NOT NULL,     -- SHA-256 prefix for fast lookup
    key_hash VARCHAR(255) NOT NULL,      -- Bcrypt hash of actual key
    user_id VARCHAR(255) NOT NULL,
    description TEXT,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    rate_limit_per_minute INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    active BOOLEAN DEFAULT true,
    created_by VARCHAR(255)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_key_prefix ON api_keys(key_prefix);  -- B-tree index for O(1) performance (non-unique for collision handling)
CREATE INDEX IF NOT EXISTS idx_key_id ON api_keys(key_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_active_expires ON api_keys(active, expires_at);

-- PHI Audit Log Table (HIPAA 6-year retention) with monthly partitioning
CREATE TABLE IF NOT EXISTS phi_audit_log (
    id SERIAL,
    request_id VARCHAR(26) NOT NULL,  -- ULID for request correlation
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(255) NOT NULL,
    api_key_id VARCHAR(16),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    outcome VARCHAR(50) DEFAULT 'success',
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    PRIMARY KEY (timestamp, id)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for efficient retention
DO $$
DECLARE
    start_date date := '2025-01-01';
    end_date date := '2027-01-01';
    partition_date date;
    partition_name text;
BEGIN
    partition_date := start_date;
    WHILE partition_date < end_date LOOP
        partition_name := 'phi_audit_log_' || to_char(partition_date, 'YYYY_MM');
        BEGIN
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS %I PARTITION OF phi_audit_log
                FOR VALUES FROM (%L) TO (%L)',
                partition_name,
                partition_date,
                partition_date + interval '1 month'
            );
            RAISE NOTICE 'Created partition %', partition_name;
        EXCEPTION
            WHEN duplicate_table THEN
                RAISE NOTICE 'Partition % already exists', partition_name;
        END;
        partition_date := partition_date + interval '1 month';
    END LOOP;
END $$;

-- Rate Limit Tracking with persistent bans
CREATE TABLE IF NOT EXISTS rate_limit_violations (
    id SERIAL PRIMARY KEY,
    api_key_id VARCHAR(16),
    ip_address INET,
    endpoint VARCHAR(255),
    violations_count INTEGER DEFAULT 1,
    first_violation TIMESTAMP DEFAULT NOW(),
    last_violation TIMESTAMP DEFAULT NOW(),
    blocked_until TIMESTAMP
);

-- Create indexes for rate limit tracking
CREATE INDEX IF NOT EXISTS idx_key_ip ON rate_limit_violations(api_key_id, ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked ON rate_limit_violations(blocked_until);

-- PHI Encryption Keys Table with rotation support
CREATE TABLE IF NOT EXISTS phi_encryption_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(32) UNIQUE NOT NULL,
    encrypted_key TEXT NOT NULL,  -- Master key encrypted
    algorithm VARCHAR(50) DEFAULT 'AES-256-GCM',
    created_at TIMESTAMP DEFAULT NOW(),
    rotated_at TIMESTAMP,
    rotated_from VARCHAR(32),  -- Previous key_id for rotation tracking
    active BOOLEAN DEFAULT true
);

-- Create indexes for encryption keys
CREATE INDEX IF NOT EXISTS idx_active ON phi_encryption_keys(active);
CREATE INDEX IF NOT EXISTS idx_created_at ON phi_encryption_keys(created_at);

-- Webhook Replay Protection
CREATE TABLE IF NOT EXISTS webhook_replay_protection (
    signature_hash VARCHAR(64) PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '5 minutes')
);

-- Create index for automatic cleanup
CREATE INDEX IF NOT EXISTS idx_webhook_replay_expires ON webhook_replay_protection(expires_at);

-- =============================================================================
-- Automated Maintenance Functions
-- =============================================================================

-- Function to clean up expired webhook replay records
CREATE OR REPLACE FUNCTION cleanup_expired_webhook_replays()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM webhook_replay_protection
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to create new monthly partitions for audit logs
CREATE OR REPLACE FUNCTION create_monthly_audit_partition()
RETURNS void AS $$
DECLARE
    partition_date date;
    partition_name text;
BEGIN
    -- Create partition for next month
    partition_date := date_trunc('month', CURRENT_DATE + interval '1 month');
    partition_name := 'phi_audit_log_' || to_char(partition_date, 'YYYY_MM');
    
    BEGIN
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF phi_audit_log
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_date,
            partition_date + interval '1 month'
        );
        RAISE NOTICE 'Created future partition %', partition_name;
    EXCEPTION
        WHEN duplicate_table THEN
            RAISE NOTICE 'Partition % already exists', partition_name;
    END;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant permissions to auren_user (adjust based on your actual database user)
GRANT SELECT, INSERT, UPDATE ON api_keys TO auren_user;
GRANT SELECT, INSERT ON phi_audit_log TO auren_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON rate_limit_violations TO auren_user;
GRANT SELECT, INSERT, UPDATE ON phi_encryption_keys TO auren_user;
GRANT SELECT, INSERT, DELETE ON webhook_replay_protection TO auren_user;

-- Grant sequence permissions
GRANT USAGE ON SEQUENCE api_keys_id_seq TO auren_user;
GRANT USAGE ON SEQUENCE phi_audit_log_id_seq TO auren_user;
GRANT USAGE ON SEQUENCE rate_limit_violations_id_seq TO auren_user;
GRANT USAGE ON SEQUENCE phi_encryption_keys_id_seq TO auren_user;

-- =============================================================================
-- Initial Data
-- =============================================================================

-- Insert a comment about initial setup
-- The initial admin API key will be created by the deployment script
-- to ensure the key is never stored in version control

-- =============================================================================
-- Rollback Script (commented out for safety)
-- =============================================================================

/*
-- To rollback these changes, run:

DROP TABLE IF EXISTS webhook_replay_protection CASCADE;
DROP TABLE IF EXISTS phi_encryption_keys CASCADE;
DROP TABLE IF EXISTS rate_limit_violations CASCADE;
DROP TABLE IF EXISTS phi_audit_log CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;

DROP FUNCTION IF EXISTS cleanup_expired_webhook_replays();
DROP FUNCTION IF EXISTS create_monthly_audit_partition();
*/ 