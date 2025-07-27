-- Biometric Bridge Database Schema for NEUROS
-- Requires TimescaleDB extension (already enabled)

-- Create neuros checkpoints table for LangGraph state persistence
CREATE TABLE IF NOT EXISTS neuros_checkpoints (
    thread_id VARCHAR(255) PRIMARY KEY,
    checkpoint JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for checkpoint queries
CREATE INDEX IF NOT EXISTS idx_checkpoints_updated ON neuros_checkpoints(updated_at DESC);

-- Create biometric events table with TimescaleDB hypertable
CREATE TABLE IF NOT EXISTS biometric_events (
    user_id VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, device_type, timestamp)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('biometric_events', 'timestamp', if_not_exists => TRUE);

-- Create indexes for biometric queries
CREATE INDEX IF NOT EXISTS idx_biometric_user ON biometric_events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_biometric_device ON biometric_events(device_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_biometric_event_data ON biometric_events USING GIN(event_data);

-- Create cognitive mode transitions table
CREATE TABLE IF NOT EXISTS cognitive_mode_transitions (
    transition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    from_mode VARCHAR(50),
    to_mode VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    trigger_type VARCHAR(100),
    trigger_data JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('cognitive_mode_transitions', 'timestamp', if_not_exists => TRUE);

-- Create indexes for mode analysis
CREATE INDEX IF NOT EXISTS idx_mode_user_session ON cognitive_mode_transitions(user_id, session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mode_transitions ON cognitive_mode_transitions(from_mode, to_mode);

-- Create biometric patterns table for detected patterns
CREATE TABLE IF NOT EXISTS biometric_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    first_detected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_detected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    occurrence_count INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE
);

-- Create indexes for pattern queries
CREATE INDEX IF NOT EXISTS idx_patterns_user ON biometric_patterns(user_id, active);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON biometric_patterns(pattern_type, confidence DESC);

-- Create biometric alerts table
CREATE TABLE IF NOT EXISTS biometric_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    alert_data JSONB NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ
);

-- Convert to hypertable
SELECT create_hypertable('biometric_alerts', 'triggered_at', if_not_exists => TRUE);

-- Create indexes for alert management
CREATE INDEX IF NOT EXISTS idx_alerts_user_active ON biometric_alerts(user_id, resolved, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON biometric_alerts(severity, resolved);

-- Grant permissions to auren user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auren_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auren_user; 