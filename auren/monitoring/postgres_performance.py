"""
PostgreSQL Performance Monitoring
Track query performance and automatically identify optimization opportunities
"""

import asyncio
import asyncpg
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from auren.core.logging_config import get_logger
from auren.config.production_settings import settings

logger = get_logger(__name__)


@dataclass
class QueryPerformance:
    """Query performance metrics"""
    query: str
    calls: int
    total_time_ms: float
    mean_time_ms: float
    max_time_ms: float
    rows_returned: int
    cache_hit_ratio: float


@dataclass
class TableStats:
    """Table statistics for optimization"""
    table_name: str
    row_count: int
    dead_tuples: int
    last_vacuum: Optional[datetime]
    last_analyze: Optional[datetime]
    index_scans: int
    seq_scans: int
    cache_hit_ratio: float


class PostgresPerformanceMonitor:
    """
    Monitor PostgreSQL performance and suggest optimizations.
    Based on production experience with high-throughput memory systems.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        
        # Thresholds for alerts
        self.slow_query_threshold_ms = 100
        self.high_seq_scan_threshold = 1000
        self.low_cache_hit_threshold = 0.9
        self.high_dead_tuple_ratio = 0.1
        
        # Performance history
        self.query_history: List[QueryPerformance] = []
        self.table_history: Dict[str, List[TableStats]] = {}
    
    async def initialize(self):
        """Initialize monitoring extensions and views"""
        async with self.db_pool.acquire() as conn:
            # Ensure pg_stat_statements is enabled
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
            
            # Reset stats for clean monitoring
            await conn.execute("SELECT pg_stat_statements_reset()")
            
        logger.info("PostgreSQL performance monitor initialized")
    
    async def get_slow_queries(self, limit: int = 20) -> List[QueryPerformance]:
        """Get slowest queries from pg_stat_statements"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    query,
                    calls,
                    total_time as total_time_ms,
                    mean_time as mean_time_ms,
                    max_time as max_time_ms,
                    rows,
                    100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0) as cache_hit_ratio
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat_statements%'
                    AND mean_time > $1
                ORDER BY mean_time DESC
                LIMIT $2
            """, self.slow_query_threshold_ms, limit)
            
            slow_queries = []
            for row in rows:
                slow_queries.append(QueryPerformance(
                    query=self._normalize_query(row['query']),
                    calls=row['calls'],
                    total_time_ms=row['total_time_ms'],
                    mean_time_ms=row['mean_time_ms'],
                    max_time_ms=row['max_time_ms'],
                    rows_returned=row['rows'],
                    cache_hit_ratio=row['cache_hit_ratio'] or 0.0
                ))
            
            self.query_history = slow_queries
            return slow_queries
    
    async def get_table_stats(self) -> List[TableStats]:
        """Get table statistics for optimization analysis"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup as row_count,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_analyze,
                    idx_scan as index_scans,
                    seq_scan as seq_scans,
                    CASE 
                        WHEN heap_blks_hit + heap_blks_read > 0 
                        THEN 100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read)
                        ELSE 0
                    END as cache_hit_ratio
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
            """)
            
            table_stats = []
            for row in rows:
                stats = TableStats(
                    table_name=f"{row['schemaname']}.{row['tablename']}",
                    row_count=row['row_count'],
                    dead_tuples=row['dead_tuples'],
                    last_vacuum=row['last_vacuum'],
                    last_analyze=row['last_analyze'],
                    index_scans=row['index_scans'],
                    seq_scans=row['seq_scans'],
                    cache_hit_ratio=row['cache_hit_ratio']
                )
                table_stats.append(stats)
                
                # Track history
                if stats.table_name not in self.table_history:
                    self.table_history[stats.table_name] = []
                self.table_history[stats.table_name].append(stats)
            
            return table_stats
    
    async def get_missing_indexes(self) -> List[Dict[str, Any]]:
        """Identify potential missing indexes based on query patterns"""
        async with self.db_pool.acquire() as conn:
            # Find tables with high sequential scan ratio
            rows = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    seq_scan,
                    idx_scan,
                    n_live_tup,
                    CASE 
                        WHEN seq_scan + idx_scan > 0 
                        THEN 100.0 * seq_scan / (seq_scan + idx_scan)
                        ELSE 0
                    END as seq_scan_ratio
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                    AND n_live_tup > 1000
                    AND seq_scan > $1
                    AND CASE 
                        WHEN seq_scan + idx_scan > 0 
                        THEN 100.0 * seq_scan / (seq_scan + idx_scan)
                        ELSE 0
                    END > 50
                ORDER BY seq_scan DESC
            """, self.high_seq_scan_threshold)
            
            missing_indexes = []
            for row in rows:
                suggestion = {
                    "table": f"{row['schemaname']}.{row['tablename']}",
                    "seq_scans": row['seq_scan'],
                    "seq_scan_ratio": row['seq_scan_ratio'],
                    "row_count": row['n_live_tup'],
                    "recommendation": f"Consider adding index on frequently queried columns"
                }
                
                # Try to find specific column recommendations from slow queries
                column_hints = await self._analyze_query_patterns(
                    conn, 
                    row['tablename']
                )
                if column_hints:
                    suggestion["recommended_columns"] = column_hints
                
                missing_indexes.append(suggestion)
            
            return missing_indexes
    
    async def _analyze_query_patterns(self, conn: asyncpg.Connection, table_name: str) -> List[str]:
        """Analyze query patterns to suggest index columns"""
        # Look for WHERE clauses in slow queries involving this table
        patterns = await conn.fetch("""
            SELECT query
            FROM pg_stat_statements
            WHERE query ILIKE $1
                AND query ILIKE '%WHERE%'
                AND mean_time > $2
            LIMIT 10
        """, f"%{table_name}%", self.slow_query_threshold_ms)
        
        # Simple pattern extraction (production would use proper SQL parsing)
        columns = set()
        for row in patterns:
            query = row['query'].lower()
            # Extract column names after WHERE (simplified)
            if 'where' in query:
                where_clause = query.split('where')[1].split('order by')[0]
                # Look for column = value patterns
                import re
                matches = re.findall(r'(\w+)\s*=', where_clause)
                columns.update(matches)
        
        return list(columns)[:3]  # Top 3 columns
    
    async def optimize_queries(self) -> Dict[str, Any]:
        """Analyze and provide optimization recommendations"""
        slow_queries = await self.get_slow_queries()
        table_stats = await self.get_table_stats()
        missing_indexes = await self.get_missing_indexes()
        
        recommendations = []
        
        # Analyze slow queries
        for query in slow_queries[:5]:  # Top 5 slowest
            if query.cache_hit_ratio < self.low_cache_hit_threshold:
                recommendations.append({
                    "type": "cache_miss",
                    "query": query.query[:100] + "...",
                    "impact": "high",
                    "suggestion": "Consider increasing shared_buffers or optimize query to access less data",
                    "metrics": {
                        "cache_hit_ratio": query.cache_hit_ratio,
                        "mean_time_ms": query.mean_time_ms
                    }
                })
        
        # Analyze table maintenance
        for stats in table_stats:
            if stats.row_count > 0:
                dead_tuple_ratio = stats.dead_tuples / stats.row_count
                if dead_tuple_ratio > self.high_dead_tuple_ratio:
                    recommendations.append({
                        "type": "maintenance",
                        "table": stats.table_name,
                        "impact": "medium",
                        "suggestion": f"Table needs VACUUM - {dead_tuple_ratio*100:.1f}% dead tuples",
                        "metrics": {
                            "dead_tuples": stats.dead_tuples,
                            "last_vacuum": stats.last_vacuum.isoformat() if stats.last_vacuum else None
                        }
                    })
            
            # Check for tables that need ANALYZE
            if stats.last_analyze is None or (
                datetime.now(stats.last_analyze.tzinfo) - stats.last_analyze > timedelta(days=7)
            ):
                recommendations.append({
                    "type": "statistics",
                    "table": stats.table_name,
                    "impact": "low",
                    "suggestion": "Table statistics are outdated, run ANALYZE",
                    "metrics": {
                        "last_analyze": stats.last_analyze.isoformat() if stats.last_analyze else None
                    }
                })
        
        # Add missing index recommendations
        for idx in missing_indexes:
            recommendations.append({
                "type": "missing_index",
                "table": idx["table"],
                "impact": "high",
                "suggestion": idx["recommendation"],
                "metrics": {
                    "seq_scans": idx["seq_scans"],
                    "seq_scan_ratio": idx["seq_scan_ratio"],
                    "recommended_columns": idx.get("recommended_columns", [])
                }
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "slow_queries": len(slow_queries),
                "tables_analyzed": len(table_stats),
                "missing_indexes": len(missing_indexes),
                "total_recommendations": len(recommendations)
            },
            "recommendations": recommendations,
            "top_slow_queries": [
                {
                    "query": q.query[:200] + "...",
                    "mean_time_ms": q.mean_time_ms,
                    "calls": q.calls
                }
                for q in slow_queries[:5]
            ]
        }
    
    async def auto_optimize(self) -> Dict[str, Any]:
        """Automatically apply safe optimizations"""
        applied = []
        
        async with self.db_pool.acquire() as conn:
            # Auto-VACUUM tables with high dead tuple ratio
            table_stats = await self.get_table_stats()
            
            for stats in table_stats:
                if stats.row_count > 0:
                    dead_tuple_ratio = stats.dead_tuples / stats.row_count
                    if dead_tuple_ratio > self.high_dead_tuple_ratio:
                        try:
                            await conn.execute(f"VACUUM ANALYZE {stats.table_name}")
                            applied.append({
                                "action": "VACUUM ANALYZE",
                                "table": stats.table_name,
                                "reason": f"{dead_tuple_ratio*100:.1f}% dead tuples"
                            })
                        except Exception as e:
                            logger.error(f"Failed to vacuum {stats.table_name}: {e}")
            
            # Update table statistics for tables with outdated stats
            for stats in table_stats:
                if stats.last_analyze is None or (
                    datetime.now(stats.last_analyze.tzinfo) - stats.last_analyze > timedelta(days=7)
                ):
                    try:
                        await conn.execute(f"ANALYZE {stats.table_name}")
                        applied.append({
                            "action": "ANALYZE",
                            "table": stats.table_name,
                            "reason": "Outdated statistics"
                        })
                    except Exception as e:
                        logger.error(f"Failed to analyze {stats.table_name}: {e}")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations_applied": applied,
            "count": len(applied)
        }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for analysis (remove parameters)"""
        # Replace numeric parameters with ?
        import re
        normalized = re.sub(r'\b\d+\b', '?', query)
        # Replace string literals
        normalized = re.sub(r"'[^']*'", '?', normalized)
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return normalized
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                    max(EXTRACT(EPOCH FROM (now() - state_change))) as longest_connection_seconds
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            
            return {
                "total_connections": stats['total_connections'],
                "active_connections": stats['active_connections'],
                "idle_connections": stats['idle_connections'],
                "idle_in_transaction": stats['idle_in_transaction'],
                "longest_connection_seconds": stats['longest_connection_seconds'],
                "pool_size": self.db_pool.get_size(),
                "pool_free": self.db_pool.get_idle_size()
            } 