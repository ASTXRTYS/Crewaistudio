#!/usr/bin/env python3
"""
Database Setup for Knowledge Injection
Creates and initializes database for clinical knowledge loading
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def setup_database_for_knowledge():
    """
    Set up PostgreSQL database for knowledge injection
    Creates database, user, and schema if needed
    """
    
    print("🏗️ SETTING UP DATABASE FOR KNOWLEDGE INJECTION")
    print("=" * 60)
    
    # Default PostgreSQL connection (as superuser)
    superuser_dsn = "postgresql://postgres:password@localhost:5432/postgres"
    
    try:
        # Connect as superuser
        conn = await asyncpg.connect(superuser_dsn)
        
        # Create database
        await create_database(conn)
        
        # Create user
        await create_user(conn)
        
        # Grant permissions
        await grant_permissions(conn)
        
        await conn.close()
        
        # Connect to new database and create schema
        await create_schema()
        
        print("🎉 DATABASE SETUP COMPLETE!")
        print("Ready for knowledge injection")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("Please ensure PostgreSQL is running and accessible")

async def create_database(conn):
    """Create the auren database"""
    
    try:
        await conn.execute("""
        CREATE DATABASE auren
        WITH 
        OWNER = postgres
        ENCODING = 'UTF8'
        LC_COLLATE = 'en_US.UTF-8'
        LC_CTYPE = 'en_US.UTF-8'
        TABLESPACE = pg_default
        CONNECTION LIMIT = -1
        """)
        print("✅ Database 'auren' created")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("ℹ️  Database 'auren' already exists")

async def create_user(conn):
    """Create auren_user with appropriate permissions"""
    
    try:
        await conn.execute("""
        CREATE USER auren_user WITH
        LOGIN
        NOSUPERUSER
        INHERIT
        NOCREATEDB
        NOCREATEROLE
        NOREPLICATION
        PASSWORD 'password'
        """)
        print("✅ User 'auren_user' created")
    except asyncpg.exceptions.DuplicateObjectError:
        print("ℹ️  User 'auren_user' already exists")

async def grant_permissions(conn):
    """Grant necessary permissions to auren_user"""
    
    await conn.execute("""
    GRANT ALL PRIVILEGES ON DATABASE auren TO auren_user
    """)
    print("✅ Permissions granted to auren_user")

async def create_schema():
    """Create database schema for knowledge injection"""
    
    dsn = "postgresql://auren_user:password@localhost:5432/auren"
    
    try:
        conn = await asyncpg.connect(dsn)
        
        # Create schema from our definitions
        schema_sql = """
        -- Create extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Create agent_memories table
        CREATE TABLE IF NOT EXISTS agent_memories (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(100) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            memory_type VARCHAR(50) NOT NULL,
            content JSONB NOT NULL,
            confidence_score FLOAT DEFAULT 0.5,
            validation_status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            version INTEGER DEFAULT 1,
            parent_id INTEGER REFERENCES agent_memories(id),
            metadata JSONB DEFAULT '{}',
            is_archived BOOLEAN DEFAULT false,
            archived_at TIMESTAMPTZ,
            archive_reason VARCHAR(100),
            
            INDEX idx_agent_user (agent_id, user_id),
            INDEX idx_memory_type (memory_type),
            INDEX idx_created_at (created_at DESC),
            INDEX idx_validation_status (validation_status),
            INDEX idx_confidence_score (confidence_score DESC),
            INDEX idx_archived (is_archived)
        );
        
        -- Create events table
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            stream_id VARCHAR(255) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            
            INDEX idx_stream_events (stream_id, created_at DESC),
            INDEX idx_event_type (event_type),
            INDEX idx_created_at (created_at DESC)
        );
        
        -- Create global_patterns table
        CREATE TABLE IF NOT EXISTS global_patterns (
            id SERIAL PRIMARY KEY,
            pattern_description TEXT NOT NULL,
            intervention TEXT NOT NULL,
            outcome TEXT NOT NULL,
            effectiveness_score FLOAT NOT NULL,
            user_count INTEGER NOT NULL DEFAULT 1,
            avg_confidence FLOAT NOT NULL,
            avg_effect_size FLOAT NOT NULL,
            confidence_std FLOAT DEFAULT 0.0,
            user_demographics JSONB DEFAULT '{}',
            contributing_agents TEXT[] DEFAULT '{}',
            first_user_id VARCHAR(255),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_updated TIMESTAMPTZ DEFAULT NOW(),
            is_active BOOLEAN DEFAULT true,
            
            INDEX idx_effectiveness_score (effectiveness_score DESC),
            INDEX idx_user_count (user_count DESC),
            INDEX idx_created_at (created_at DESC),
            INDEX idx_active_patterns (is_active, effectiveness_score DESC)
        );
        
        -- Create clinical_consultations table
        CREATE TABLE IF NOT EXISTS clinical_consultations (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            primary_concern TEXT NOT NULL,
            consultation_type VARCHAR(50) NOT NULL,
            urgency_level INTEGER NOT NULL DEFAULT 1,
            participating_specialists JSONB NOT NULL,
            specialist_inputs JSONB DEFAULT '{}',
            team_recommendation JSONB DEFAULT '{}',
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            
            INDEX idx_user_consultations (user_id, created_at DESC),
            INDEX idx_urgency_level (urgency_level),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at DESC)
        );
        
        -- Create hypothesis_validation table
        CREATE TABLE IF NOT EXISTS hypothesis_validation (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(100) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            hypothesis_text TEXT NOT NULL,
            initial_confidence FLOAT NOT NULL,
            current_confidence FLOAT NOT NULL,
            evidence_for JSONB DEFAULT '[]',
            evidence_against JSONB DEFAULT '[]',
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_tested_at TIMESTAMPTZ,
            test_count INTEGER DEFAULT 0,
            validation_outcomes JSONB DEFAULT '[]',
            
            INDEX idx_hypothesis_agent (agent_id, user_id),
            INDEX idx_hypothesis_status (status),
            INDEX idx_confidence_delta (current_confidence - initial_confidence)
        );
        
        -- Create data_access_audit table
        CREATE TABLE IF NOT EXISTS data_access_audit (
            id SERIAL PRIMARY KEY,
            access_timestamp TIMESTAMPTZ DEFAULT NOW(),
            agent_id VARCHAR(100) NOT NULL,
            agent_type VARCHAR(50) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            data_category VARCHAR(50) NOT NULL,
            access_purpose VARCHAR(50) NOT NULL,
            query_details JSONB NOT NULL,
            records_accessed INTEGER NOT NULL,
            response_time_ms INTEGER,
            correlation_id VARCHAR(100),
            
            INDEX idx_audit_agent (agent_id, access_timestamp DESC),
            INDEX idx_audit_user (user_id, access_timestamp DESC),
            INDEX idx_audit_purpose (access_purpose),
            INDEX idx_audit_correlation (correlation_id)
        );
        
        -- Create access_patterns table
        CREATE TABLE IF NOT EXISTS access_patterns (
            id SERIAL PRIMARY KEY,
            pattern_date DATE NOT NULL,
            agent_type VARCHAR(50) NOT NULL,
            data_category VARCHAR(50) NOT NULL,
            access_count INTEGER DEFAULT 1,
            avg_response_time_ms INTEGER,
            common_purposes JSONB DEFAULT '{}',
            
            UNIQUE(pattern_date, agent_type, data_category),
            INDEX idx_pattern_date (pattern_date DESC)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_agent_memories_agent_type 
        ON agent_memories(agent_id, memory_type);
        
        CREATE INDEX IF NOT EXISTS idx_agent_memories_confidence 
        ON agent_memories(confidence_score DESC);
        
        CREATE INDEX IF NOT EXISTS idx_events_stream_type 
        ON events(stream_id, event_type);
        """
        
        await conn.execute(schema_sql)
        print("✅ Schema created successfully")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database_for_knowledge())
