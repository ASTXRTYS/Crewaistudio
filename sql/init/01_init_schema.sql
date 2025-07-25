-- Initialize AUREN database schema
-- This creates the basic structure for event sourcing and agent memory

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;

-- Create events table for event sourcing
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_version INTEGER NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Convert to TimescaleDB hypertable for better time-series performance
SELECT create_hypertable('events', 'created_at', if_not_exists => TRUE);

-- Create indexes for event queries
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, event_version);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

-- Create agent memories table
CREATE TABLE IF NOT EXISTS agent_memories (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    embedding vector(1536), -- For future semantic search
    confidence FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Create indexes for memory retrieval
CREATE INDEX IF NOT EXISTS idx_memories_agent_user ON agent_memories(agent_id, user_id, active);
CREATE INDEX IF NOT EXISTS idx_memories_type ON agent_memories(memory_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_confidence ON agent_memories(confidence DESC) WHERE active = TRUE;

-- Create hypotheses table
CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    validation_status VARCHAR(50) DEFAULT 'pending',
    evidence JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validated_at TIMESTAMPTZ,
    validation_result JSONB
);

-- Create indexes for hypothesis tracking
CREATE INDEX IF NOT EXISTS idx_hypotheses_agent_user ON hypotheses(agent_id, user_id);
CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses(validation_status, created_at DESC);

-- Create learning progress table
CREATE TABLE IF NOT EXISTS learning_progress (
    progress_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to hypertable for time-series tracking
SELECT create_hypertable('learning_progress', 'recorded_at', if_not_exists => TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auren;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auren; 