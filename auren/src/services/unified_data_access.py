"""
Unified Data Access Layer
Provides all agents with read access to all user data while maintaining
complete audit trails for security and debugging.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncpg
from dataclasses import dataclass

class DataAccessPurpose(Enum):
    """Why an agent is accessing data"""
    HYPOTHESIS_FORMATION = "hypothesis_formation"
    PATTERN_ANALYSIS = "pattern_analysis"
    CROSS_VALIDATION = "cross_validation"
    USER_QUERY_RESPONSE = "user_query_response"
    BACKGROUND_LEARNING = "background_learning"
    SPECIALIST_CONSULTATION = "specialist_consultation"

@dataclass
class DataAccessContext:
    """Context for data access request"""
    agent_id: str
    agent_type: str
    purpose: DataAccessPurpose
    query_context: Dict[str, Any]
    correlation_id: Optional[str] = None

class UnifiedDataAccess:
    """
    Central service providing all agents with read access to all user data.
    
    Key principles:
    - No data isolation between agents (per founder requirement)
    - Complete audit trail for every access
    - Performance optimized for hypothesis formation
    - Supports cross-agent learning and validation
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool
        
    async def initialize(self):
        """Set up audit infrastructure"""
        async with self.pool.acquire() as conn:
            # Create enum type if not exists
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE data_access_purpose_enum AS ENUM (
                        'hypothesis_formation', 'pattern_analysis',
                        'cross_validation', 'user_query_response',
                        'background_learning', 'specialist_consultation'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            # Comprehensive audit table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_access_audit (
                    id SERIAL PRIMARY KEY,
                    access_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    agent_id VARCHAR(100) NOT NULL,
                    agent_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    data_category VARCHAR(50) NOT NULL,
                    access_purpose data_access_purpose_enum NOT NULL,
                    query_details JSONB NOT NULL,
                    records_accessed INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    correlation_id VARCHAR(100),
                    
                    INDEX idx_audit_agent (agent_id, access_timestamp DESC),
                    INDEX idx_audit_user (user_id, access_timestamp DESC),
                    INDEX idx_audit_purpose (access_purpose),
                    INDEX idx_audit_correlation (correlation_id)
                );
            """)
            
            # Access patterns analysis table
            await conn.execute("""
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
            """)
    
    async def get_user_biometric_data(self,
                                    user_id: str,
                                    context: DataAccessContext,
                                    time_range: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all biometric data for a user."""
        start_time = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            # Build query based on time range
            query = """
                SELECT 
                    measurement_type,
                    value,
                    unit,
                    recorded_at,
                    source,
                    metadata
                FROM biometric_readings
                WHERE user_id = $1
            """
            
            params = [user_id]
            
            if time_range:
                if 'start' in time_range:
                    query += " AND recorded_at >= $2"
                    params.append(time_range['start'])
                if 'end' in time_range:
                    query += f" AND recorded_at <= ${len(params) + 1}"
                    params.append(time_range['end'])
            
            query += " ORDER BY recorded_at DESC"
            
            # Execute query
            results = await conn.fetch(query, *params)
            
            # Convert to list of dicts
            data = [dict(row) for row in results]
            
            # Record access in audit trail
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._record_access(
                context=context,
                user_id=user_id,
                data_category='biometric',
                query_details={
                    'time_range': time_range,
                    'measurement_types': list(set(r['measurement_type'] for r in data))
                },
                records_accessed=len(data),
                response_time_ms=response_time
            )
            
            return data
    
    async def get_user_facts(self,
                           user_id: str,
                           context: DataAccessContext,
                           fact_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get all known facts about a user."""
        start_time = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    fact_type,
                    fact_value,
                    confidence_score,
                    discovered_by,
                    discovered_at,
                    last_validated_at,
                    metadata
                FROM user_facts
                WHERE user_id = $1
            """
            
            params = [user_id]
            
            if fact_types:
                placeholders = ','.join(f'${i+2}' for i in range(len(fact_types)))
                query += f" AND fact_type IN ({placeholders})"
                params.extend(fact_types)
            
            query += " ORDER BY confidence_score DESC, discovered_at DESC"
            
            results = await conn.fetch(query, *params)
            facts = [dict(row) for row in results]
            
            # Audit the access
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._record_access(
                context=context,
                user_id=user_id,
                data_category='facts',
                query_details={'fact_types': fact_types},
                records_accessed=len(facts),
                response_time_ms=response_time
            )
            
            return facts
    
    async def get_user_hypotheses(self,
                                user_id: str,
                                context: DataAccessContext,
                                include_other_agents: bool = True) -> List[Dict[str, Any]]:
        """Get all hypotheses about a user from all specialists."""
        start_time = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            # Base query gets user-specific hypotheses
            query = """
                SELECT 
                    h.id,
                    h.specialist_type,
                    h.hypothesis_text,
                    h.initial_confidence,
                    h.current_confidence,
                    h.status,
                    h.test_count,
                    h.created_at,
                    h.last_tested_at,
                    h.evidence_for,
                    h.evidence_against
                FROM specialist_hypotheses h
                WHERE h.user_id = $1
            """
            
            # Optionally filter to just requesting agent's hypotheses
            if not include_other_agents:
                query += " AND h.specialist_type = $2"
                results = await conn.fetch(query, user_id, context.agent_type)
            else:
                results = await conn.fetch(query, user_id)
            
            hypotheses = []
            for row in results:
                hypothesis = dict(row)
                # Parse JSON fields
                hypothesis['evidence_for'] = json.loads(hypothesis['evidence_for'])
                hypothesis['evidence_against'] = json.loads(hypothesis['evidence_against'])
                hypotheses.append(hypothesis)
            
            # Audit the access
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._record_access(
                context=context,
                user_id=user_id,
                data_category='hypotheses',
                query_details={
                    'include_other_agents': include_other_agents,
                    'specialists_accessed': list(set(h['specialist_type'] for h in hypotheses))
                },
                records_accessed=len(hypotheses),
                response_time_ms=response_time
            )
            
            return hypotheses
    
    async def get_user_conversations(self,
                                   user_id: str,
                                   context: DataAccessContext,
                                   time_range: Optional[Dict[str, Any]] = None,
                                   with_agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        start_time = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    conversation_id,
                    agent_type,
                    message_type,
                    content,
                    timestamp,
                    metadata
                FROM conversation_history
                WHERE user_id = $1
            """
            
            params = [user_id]
            param_count = 1
            
            if with_agent:
                param_count += 1
                query += f" AND agent_type = ${param_count}"
                params.append(with_agent)
            
            if time_range:
                if 'start' in time_range:
                    param_count += 1
                    query += f" AND timestamp >= ${param_count}"
                    params.append(time_range['start'])
                if 'end' in time_range:
                    param_count += 1
                    query += f" AND timestamp <= ${param_count}"
                    params.append(time_range['end'])
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            results = await conn.fetch(query, *params)
            conversations = [dict(row) for row in results]
            
            # Audit the access
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._record_access(
                context=context,
                user_id=user_id,
                data_category='conversations',
                query_details={
                    'time_range': time_range,
                    'with_agent': with_agent
                },
                records_accessed=len(conversations),
                response_time_ms=response_time
            )
            
            return conversations
    
    async def get_complete_user_context(self,
                                      user_id: str,
                                      context: DataAccessContext) -> Dict[str, Any]:
        """Get comprehensive user context for hypothesis formation."""
        # Parallel fetch all data categories
        biometric_task = self.get_user_biometric_data(
            user_id, context, 
            time_range={'start': datetime.utcnow() - timedelta(days=30)}
        )
        facts_task = self.get_user_facts(user_id, context)
        hypotheses_task = self.get_user_hypotheses(user_id, context)
        conversations_task = self.get_user_conversations(
            user_id, context,
            time_range={'start': datetime.utcnow() - timedelta(days=7)}
        )
        
        # Wait for all data
        biometric_data, facts, hypotheses, conversations = await asyncio.gather(
            biometric_task, facts_task, hypotheses_task, conversations_task
        )
        
        # Get user profile
        async with self.pool.acquire() as conn:
            profile = await conn.fetchrow("""
                SELECT 
                    user_id, created_at, goals, preferences,
                    demographics, metadata
                FROM user_profiles
                WHERE user_id = $1
            """, user_id)
        
        return {
            'user_profile': dict(profile) if profile else None,
            'biometric_data': biometric_data,
            'facts': facts,
            'hypotheses': hypotheses,
            'recent_conversations': conversations,
            'data_summary': {
                'total_biometric_readings': len(biometric_data),
                'total_facts': len(facts),
                'active_hypotheses': sum(1 for h in hypotheses if h['status'] == 'active'),
                'recent_interaction_count': len(conversations)
            }
        }
    
    async def _record_access(self,
                           context: DataAccessContext,
                           user_id: str,
                           data_category: str,
                           query_details: Dict[str, Any],
                           records_accessed: int,
                           response_time_ms: int):
        """Record data access in audit trail"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_access_audit
                (agent_id, agent_type, user_id, data_category,
                 access_purpose, query_details, records_accessed,
                 response_time_ms, correlation_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, context.agent_id, context.agent_type, user_id,
                data_category, context.purpose.value,
                json.dumps(query_details), records_accessed,
                response_time_ms, context.correlation_id)
            
            # Update access patterns for analysis
            await conn.execute("""
                INSERT INTO access_patterns
                (pattern_date, agent_type, data_category, access_count, avg_response_time_ms)
                VALUES (CURRENT_DATE, $1, $2, 1, $3)
                ON CONFLICT (pattern_date, agent_type, data_category)
                DO UPDATE SET
                    access_count = access_patterns.access_count + 1,
                    avg_response_time_ms = (
                        access_patterns.avg_response_time_ms * access_patterns.access_count 
                        + $3
                    ) / (access_patterns.access_count + 1)
            """, context.agent_type, data_category, response_time_ms)
    
    async def get_access_analytics(self,
                                 time_range: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze data access patterns for optimization and security"""
        
        async with self.pool.acquire() as conn:
            # Get access summary by agent
            agent_summary = await conn.fetch("""
                SELECT 
                    agent_type,
                    COUNT(*) as total_accesses,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT data_category) as data_categories,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(response_time_ms) as max_response_time
                FROM data_access_audit
                WHERE ($1::TIMESTAMPTZ IS NULL OR access_timestamp >= $1)
                  AND ($2::TIMESTAMPTZ IS NULL OR access_timestamp <= $2)
                GROUP BY agent_type
                ORDER BY total_accesses DESC
            """, time_range.get('start') if time_range else None,
                time_range.get('end') if time_range else None)
            
            # Get most accessed data categories
            category_summary = await conn.fetch("""
                SELECT 
                    data_category,
                    COUNT(*) as access_count,
                    AVG(records_accessed) as avg_records,
                    AVG(response_time_ms) as avg_response_time
                FROM data_access_audit
                WHERE ($1::TIMESTAMPTZ IS NULL OR access_timestamp >= $1)
                  AND ($2::TIMESTAMPTZ IS NULL OR access_timestamp <= $2)
                GROUP BY data_category
                ORDER BY access_count DESC
            """, time_range.get('start') if time_range else None,
                time_range.get('end') if time_range else None)
            
            # Get access patterns over time
            temporal_patterns = await conn.fetch("""
                SELECT 
                    pattern_date,
                    SUM(access_count) as daily_accesses,
                    AVG(avg_response_time_ms) as avg_response_time
                FROM access_patterns
                WHERE ($1::DATE IS NULL OR pattern_date >= $1)
                  AND ($2::DATE IS NULL OR pattern_date <= $2)
                GROUP BY pattern_date
                ORDER BY pattern_date DESC
                LIMIT 30
            """, time_range.get('start') if time_range else None,
                time_range.get('end') if time_range else None)
            
            return {
                'agent_summary': [dict(r) for r in agent_summary],
                'category_summary': [dict(r) for r in category_summary],
                'temporal_patterns': [dict(r) for r in temporal_patterns],
                'analysis_period': time_range or {'start': 'all_time', 'end': 'now'}
            }
