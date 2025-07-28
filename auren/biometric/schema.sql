-- =============================================================================
-- AUREN BIOMETRIC BRIDGE DATABASE SCHEMA
-- =============================================================================
-- PostgreSQL schema for production-ready biometric processing system
-- Includes all tables needed for event storage, OAuth tokens, and DLQ
-- 
-- Created by: AUREN Engineering Team
-- Date: January 2025
-- Version: 2.0
-- =============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS biometric;

-- =============================================================================
-- MAIN BIOMETRIC EVENTS TABLE
-- =============================================================================
-- Stores all biometric events with JSONB for flexible schema evolution

CREATE TABLE IF NOT EXISTS biometric_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Composite unique constraint to prevent duplicates
    CONSTRAINT unique_biometric_event UNIQUE (user_id, device_type, timestamp)
);

-- Indexes for common queries
CREATE INDEX idx_biometric_events_user_id ON biometric_events(user_id);
CREATE INDEX idx_biometric_events_device_type ON biometric_events(device_type);
CREATE INDEX idx_biometric_events_timestamp ON biometric_events(timestamp DESC);
CREATE INDEX idx_biometric_events_user_device ON biometric_events(user_id, device_type);

-- GIN index for JSONB queries
CREATE INDEX idx_biometric_events_data ON biometric_events USING GIN (event_data);

-- =============================================================================
-- OAUTH TOKENS TABLE
-- =============================================================================
-- Stores OAuth refresh tokens for wearable API access

CREATE TABLE IF NOT EXISTS user_oauth_tokens (
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    refresh_token TEXT NOT NULL,
    access_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, provider)
);

CREATE INDEX idx_oauth_tokens_user_id ON user_oauth_tokens(user_id);
CREATE INDEX idx_oauth_tokens_provider ON user_oauth_tokens(provider);

-- =============================================================================
-- KAFKA DEAD LETTER QUEUE TABLE
-- =============================================================================
-- Stores messages that failed to be sent to Kafka

CREATE TABLE IF NOT EXISTS kafka_dlq (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    key BYTEA,
    value BYTEA NOT NULL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

CREATE INDEX idx_kafka_dlq_topic ON kafka_dlq(topic);
CREATE INDEX idx_kafka_dlq_created ON kafka_dlq(created_at);
CREATE INDEX idx_kafka_dlq_unprocessed ON kafka_dlq(processed_at) WHERE processed_at IS NULL;

-- =============================================================================
-- WEBHOOK PROCESSING LOG TABLE (Optional - for debugging)
-- =============================================================================
-- Tracks webhook processing for debugging and audit purposes

CREATE TABLE IF NOT EXISTS webhook_processing_log (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    source VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'duplicate'
    error_type VARCHAR(50),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_webhook_log_request_id ON webhook_processing_log(request_id);
CREATE INDEX idx_webhook_log_source ON webhook_processing_log(source);
CREATE INDEX idx_webhook_log_status ON webhook_processing_log(status);
CREATE INDEX idx_webhook_log_created ON webhook_processing_log(created_at DESC);

-- =============================================================================
-- UPDATE TRIGGER FOR updated_at COLUMNS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_biometric_events_updated_at 
    BEFORE UPDATE ON biometric_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_oauth_tokens_updated_at 
    BEFORE UPDATE ON user_oauth_tokens 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- GRANTS (Adjust based on your database users)
-- =============================================================================

-- Example: Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA biometric TO auren_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA biometric TO auren_app;

-- =============================================================================
-- SAMPLE DATA FOR TESTING (Optional - remove in production)
-- =============================================================================

-- Sample OAuth token (for testing only)
-- INSERT INTO user_oauth_tokens (user_id, provider, refresh_token)
-- VALUES ('test_user_001', 'whoop', 'test_refresh_token_abc123')
-- ON CONFLICT DO NOTHING;

-- =============================================================================
-- MAINTENANCE QUERIES
-- =============================================================================

-- Query to clean up old webhook logs (run periodically)
-- DELETE FROM webhook_processing_log WHERE created_at < NOW() - INTERVAL '30 days';

-- Query to retry failed Kafka messages
-- SELECT * FROM kafka_dlq WHERE processed_at IS NULL AND retry_count < 3; 