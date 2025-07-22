-- AUREN Production Database Schema
-- This script creates all necessary tables for the Neuroscientist MVP
-- Includes biometric data, memory systems, and hypothesis tracking

-- Note: Database creation is handled by init_db.py
-- This script assumes you're already connected to the correct database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable TimescaleDB for time-series data (install separately if needed)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable vector extension for embeddings (install separately if needed)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- Core User and System Tables
-- =====================================================

-- User profiles table with extended metadata
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL, -- WhatsApp/external user ID
    profile_data JSONB NOT NULL DEFAULT '{}',
    preference_evolution JSONB NOT NULL DEFAULT '{}',
    optimization_history JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_external_id ON user_profiles(external_id);

-- =====================================================
-- Memory System Tables (Three-Tier Architecture)
-- =====================================================

-- User facts table for structured long-term memory
CREATE TABLE IF NOT EXISTS user_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    fact_type VARCHAR(50) NOT NULL,
    fact_value JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_fact_type CHECK (fact_type IN (
        'fitness_level', 'sleep_goal', 'dietary_restriction', 
        'injury_history', 'training_preference', 'health_condition',
        'medication', 'goal', 'preference', 'custom'
    ))
);

CREATE INDEX idx_user_facts ON user_facts(user_id, fact_type);
CREATE INDEX idx_user_facts_expires ON user_facts(expires_at) WHERE expires_at IS NOT NULL;

-- Conversation insights with optional embeddings
CREATE TABLE IF NOT EXISTS conversation_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255),
    agent_role VARCHAR(50),
    insight_type VARCHAR(50),
    insight_data JSONB,
    embedding FLOAT[], -- Will use vector type if extension available
    confidence_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversation_user ON conversation_insights(user_id);
CREATE INDEX idx_conversation_id ON conversation_insights(conversation_id);
CREATE INDEX idx_conversation_agent ON conversation_insights(agent_role);
CREATE INDEX idx_conversation_time ON conversation_insights(created_at DESC);

-- =====================================================
-- Biometric Data Tables (Time-Series Optimized)
-- =====================================================

-- Biometric baselines for CEP calculations
CREATE TABLE IF NOT EXISTS biometric_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    baseline_value FLOAT NOT NULL,
    stddev_value FLOAT DEFAULT 0,
    sample_count INTEGER DEFAULT 0,
    date_range_start DATE,
    date_range_end DATE,
    calculation_method VARCHAR(50) DEFAULT 'rolling_average',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, metric_type)
);

CREATE INDEX idx_baseline_user_metric ON biometric_baselines(user_id, metric_type);

-- Biometric readings time-series table
CREATE TABLE IF NOT EXISTS biometric_readings (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    device_source VARCHAR(100),
    quality_score FLOAT DEFAULT 1.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    metadata JSONB DEFAULT '{}',
    PRIMARY KEY (user_id, metric_type, time)
);

-- Create indexes for efficient querying
CREATE INDEX idx_readings_user_metric ON biometric_readings(user_id, metric_type, time DESC);
CREATE INDEX idx_readings_time ON biometric_readings(time DESC);

-- If TimescaleDB is available, convert to hypertable
-- SELECT create_hypertable('biometric_readings', 'time', chunk_time_interval => INTERVAL '1 day');

-- =====================================================
-- Hypothesis and Learning Tables
-- =====================================================

-- Hypotheses tracking for compound intelligence
CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(user_id),
    created_by VARCHAR(50) NOT NULL, -- Which agent proposed this
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    hypothesis_text TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'proposed',
    confidence_score FLOAT,
    validation_evidence JSONB DEFAULT '{}',
    drift_detection_config JSONB DEFAULT '{}',
    statistical_summary JSONB DEFAULT '{}',
    test_count INTEGER DEFAULT 0,
    last_tested TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_status CHECK (status IN (
        'proposed', 'testing', 'validated', 'invalidated', 'drift_detected'
    )),
    CONSTRAINT valid_confidence CHECK (
        confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)
    )
);

CREATE INDEX idx_hypotheses_user ON hypotheses(user_id);
CREATE INDEX idx_hypotheses_status ON hypotheses(status);
CREATE INDEX idx_hypotheses_agent ON hypotheses(created_by);

-- Trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_hypotheses_updated_at 
    BEFORE UPDATE ON hypotheses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_facts_updated_at
    BEFORE UPDATE ON user_facts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_biometric_baselines_updated_at
    BEFORE UPDATE ON biometric_baselines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Agent Collaboration and Consultation Tables
-- =====================================================

-- Consultation history graph nodes
CREATE TABLE IF NOT EXISTS consultation_nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50) NOT NULL, -- 'Agent', 'User', 'Hypothesis', 'Pattern'
    node_label TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Consultation history graph edges
CREATE TABLE IF NOT EXISTS consultation_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID REFERENCES consultation_nodes(node_id),
    target_node_id UUID REFERENCES consultation_nodes(node_id),
    edge_type VARCHAR(50) NOT NULL, -- 'consults', 'validates', 'proposes', 'refutes'
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    strength FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_strength CHECK (strength >= 0 AND strength <= 1)
);

-- Indexes for graph traversal performance
CREATE INDEX idx_edges_source ON consultation_edges(source_node_id);
CREATE INDEX idx_edges_target ON consultation_edges(target_node_id);
CREATE INDEX idx_edges_type_time ON consultation_edges(edge_type, timestamp DESC);

-- =====================================================
-- Event Sourcing Table (For audit and recovery)
-- =====================================================

CREATE TABLE IF NOT EXISTS events (
    sequence_id BIGSERIAL PRIMARY KEY,
    stream_id UUID NOT NULL, -- user_id or hypothesis_id
    event_type VARCHAR(100) NOT NULL,
    event_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_events_stream ON events(stream_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_time ON events(created_at DESC);

-- =====================================================
-- Milestones and Progress Tracking
-- =====================================================

CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(user_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    category VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    impact_metrics JSONB NOT NULL DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_milestones_user ON milestones(user_id);
CREATE INDEX idx_milestones_category ON milestones(category);
CREATE INDEX idx_milestones_timestamp ON milestones(timestamp DESC);

-- =====================================================
-- Biometric Timeline for Cognitive Twin Profile
-- =====================================================

CREATE TABLE IF NOT EXISTS biometric_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    measurement_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_biometric_timeline_user ON biometric_timeline(user_id);
CREATE INDEX idx_biometric_timeline_type ON biometric_timeline(measurement_type);
CREATE INDEX idx_biometric_timeline_timestamp ON biometric_timeline(timestamp DESC);

-- =====================================================
-- Test Data for Development
-- =====================================================

-- Insert test user
INSERT INTO user_profiles (external_id, profile_data)
VALUES ('test_user_001', '{"name": "Test User", "timezone": "America/New_York"}')
ON CONFLICT (external_id) DO NOTHING;

-- Get the user_id for test data
DO $$
DECLARE
    test_user_uuid UUID;
BEGIN
    SELECT user_id INTO test_user_uuid FROM user_profiles WHERE external_id = 'test_user_001';
    
    -- Insert test biometric baseline
    INSERT INTO biometric_baselines (user_id, metric_type, baseline_value, sample_count, stddev_value)
    VALUES ('test_user_001', 'hrv', 60.0, 30, 5.5)
    ON CONFLICT (user_id, metric_type) DO NOTHING;

    -- Insert test user facts
    INSERT INTO user_facts (user_id, fact_type, fact_value, confidence)
    VALUES 
        ('test_user_001', 'fitness_level', '{"level": "intermediate", "activities": ["running", "cycling"]}', 0.9),
        ('test_user_001', 'sleep_goal', '{"hours": 8, "bedtime": "22:00", "wake_time": "06:00"}', 0.85),
        ('test_user_001', 'dietary_restriction', '{"restrictions": ["gluten-free"], "allergies": []}', 1.0)
    ON CONFLICT DO NOTHING;

    -- Insert test hypothesis
    INSERT INTO hypotheses (user_id, created_by, hypothesis_text, status, confidence_score)
    VALUES (
        test_user_uuid,
        'Neuroscientist',
        'User''s HRV improves significantly after 8+ hours of sleep',
        'testing',
        0.75
    );

    -- Insert some test biometric readings
    INSERT INTO biometric_readings (time, user_id, metric_type, value, device_source, quality_score)
    VALUES 
        (NOW() - INTERVAL '1 day', 'test_user_001', 'hrv', 58.5, 'apple_watch', 0.95),
        (NOW() - INTERVAL '2 days', 'test_user_001', 'hrv', 62.3, 'apple_watch', 0.94),
        (NOW() - INTERVAL '3 days', 'test_user_001', 'hrv', 55.2, 'apple_watch', 0.92),
        (NOW() - INTERVAL '1 day', 'test_user_001', 'heart_rate', 72, 'apple_watch', 0.98),
        (NOW() - INTERVAL '1 day', 'test_user_001', 'sleep_duration', 7.5, 'apple_watch', 0.90)
    ON CONFLICT DO NOTHING;

END $$;

-- Grant permissions (adjust as needed for production)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auren_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auren_app;

-- Output success message
SELECT 'AUREN database schema created successfully!' as status;