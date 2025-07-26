-- PostgreSQL Performance Optimization for AUREN Memory System
-- This script creates optimized indexes and configurations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For text search optimization
CREATE EXTENSION IF NOT EXISTS btree_gin; -- For composite indexes

-- Create optimized indexes for the events table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_created_at 
    ON events(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_stream_id 
    ON events(stream_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_type 
    ON events(event_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_stream_version 
    ON events(stream_id, version DESC);

-- Composite index for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_type_created 
    ON events(event_type, created_at DESC);

-- Create optimized indexes for agent_memories table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_agent_id 
    ON agent_memories(agent_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_memory_type 
    ON agent_memories(memory_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_importance 
    ON agent_memories(importance DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_created_at 
    ON agent_memories(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_updated_at 
    ON agent_memories(updated_at DESC);

-- Composite indexes for common access patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_agent_type_importance 
    ON agent_memories(agent_id, memory_type, importance DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_agent_created 
    ON agent_memories(agent_id, created_at DESC);

-- GIN index for JSONB metadata searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_metadata 
    ON agent_memories USING gin(metadata);

-- Text search index for content
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_content_search 
    ON agent_memories USING gin(to_tsvector('english', content));

-- Partial indexes for active memories
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_active 
    ON agent_memories(agent_id, memory_type) 
    WHERE deleted_at IS NULL;

-- Index for hot memory candidates (high importance, recent)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_memories_hot_candidates 
    ON agent_memories(importance DESC, created_at DESC) 
    WHERE importance > 0.7 AND deleted_at IS NULL;

-- Create indexes for agents table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_agent_type 
    ON agents(agent_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_last_active 
    ON agents(last_active DESC);

-- Create materialized view for memory statistics (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS memory_stats_by_agent AS
SELECT 
    agent_id,
    COUNT(*) as total_memories,
    COUNT(*) FILTER (WHERE memory_type = 'EXPERIENCE') as experience_memories,
    COUNT(*) FILTER (WHERE memory_type = 'KNOWLEDGE') as knowledge_memories,
    COUNT(*) FILTER (WHERE memory_type = 'SKILL') as skill_memories,
    AVG(importance) as avg_importance,
    MAX(created_at) as last_memory_created,
    SUM(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) as memories_last_24h,
    SUM(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as memories_last_7d
FROM agent_memories
WHERE deleted_at IS NULL
GROUP BY agent_id;

CREATE UNIQUE INDEX ON memory_stats_by_agent(agent_id);

-- Create materialized view for event statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS event_stats_hourly AS
SELECT 
    date_trunc('hour', created_at) as hour,
    event_type,
    COUNT(*) as event_count,
    AVG(EXTRACT(EPOCH FROM (LEAD(created_at) OVER (ORDER BY created_at) - created_at))) as avg_interval_seconds
FROM events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', created_at), event_type;

CREATE INDEX ON event_stats_hourly(hour DESC, event_type);

-- Performance tuning configurations
-- These would typically be set in postgresql.conf, but we document them here

-- Memory Configuration (for a server with 8GB RAM)
-- shared_buffers = 2GB  # 25% of RAM
-- effective_cache_size = 6GB  # 75% of RAM
-- maintenance_work_mem = 512MB
-- work_mem = 16MB

-- Write Performance
-- checkpoint_segments = 32
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB

-- Query Planning
-- random_page_cost = 1.1  # For SSD storage
-- effective_io_concurrency = 200  # For SSD
-- default_statistics_target = 100

-- Parallel Query Execution
-- max_worker_processes = 8
-- max_parallel_workers_per_gather = 4
-- max_parallel_workers = 8

-- Connection Pooling
-- max_connections = 200

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_memory_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY memory_stats_by_agent;
    REFRESH MATERIALIZED VIEW CONCURRENTLY event_stats_hourly;
END;
$$ LANGUAGE plpgsql;

-- Create a job to refresh stats every hour (requires pg_cron extension)
-- SELECT cron.schedule('refresh-memory-stats', '0 * * * *', 'SELECT refresh_memory_stats();');

-- Analyze tables to update statistics
ANALYZE events;
ANALYZE agent_memories;
ANALYZE agents;

-- Grant appropriate permissions
GRANT SELECT ON memory_stats_by_agent TO auren_user;
GRANT SELECT ON event_stats_hourly TO auren_user; 