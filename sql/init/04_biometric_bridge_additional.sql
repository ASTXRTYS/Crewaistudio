-- Additional Biometric Bridge Tables
-- Tables required by the enhanced Kafka-LangGraph bridge implementation

-- Create user sessions table for tracking cognitive mode sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    current_mode VARCHAR(50),
    last_mode_switch TIMESTAMPTZ,
    last_switch_reason TEXT,
    mode_switch_count INTEGER DEFAULT 0
);

-- Create indexes for session queries
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(last_active DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_mode ON user_sessions(current_mode);

-- Create table for failed biometric events (for retry processing)
CREATE TABLE IF NOT EXISTS failed_biometric_events (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255),
    partition INTEGER,
    offset BIGINT,
    value JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0,
    processed BOOLEAN DEFAULT FALSE
);

-- Create indexes for retry processing
CREATE INDEX IF NOT EXISTS idx_failed_events_unprocessed ON failed_biometric_events(processed, created_at);
CREATE INDEX IF NOT EXISTS idx_failed_events_topic ON failed_biometric_events(topic, partition, offset);

-- Create table for failed mode switches (for analysis)
CREATE TABLE IF NOT EXISTS failed_mode_switches (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    target_mode VARCHAR(50),
    reason TEXT,
    confidence FLOAT,
    biometric_event JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for failure analysis
CREATE INDEX IF NOT EXISTS idx_failed_switches_user ON failed_mode_switches(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_failed_switches_mode ON failed_mode_switches(target_mode);

-- Create OAuth tokens table for wearable API authentication
CREATE TABLE IF NOT EXISTS user_oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- Create indexes for OAuth token queries
CREATE INDEX IF NOT EXISTS idx_oauth_user_provider ON user_oauth_tokens(user_id, provider);
CREATE INDEX IF NOT EXISTS idx_oauth_expires ON user_oauth_tokens(expires_at);

-- Create Kafka DLQ (Dead Letter Queue) table for monitoring
CREATE TABLE IF NOT EXISTS kafka_dlq (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    headers JSONB,
    value JSONB
);

-- Create indexes for DLQ management
CREATE INDEX IF NOT EXISTS idx_dlq_unprocessed ON kafka_dlq(processed_at NULLS FIRST, created_at);
CREATE INDEX IF NOT EXISTS idx_dlq_topic ON kafka_dlq(topic, created_at DESC);

-- Grant permissions to auren user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auren_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auren_user; 