"""
Test Memory Tier Tracking Implementation
Verifies tier access patterns, latency measurements, and cache effectiveness
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import time

from auren.realtime.memory_tier_tracking import (
    MemoryTierTracker,
    MemoryTier,
    TierAccessMetrics,
    TieredMemoryBackend
)


@pytest.fixture
def mock_event_streamer():
    """Create mock event streamer"""
    streamer = AsyncMock()
    streamer.stream_event.return_value = True
    return streamer


@pytest.fixture
def memory_tier_tracker(mock_event_streamer):
    """Create memory tier tracker"""
    return MemoryTierTracker(
        event_streamer=mock_event_streamer,
        metrics_window_size=100,
        stats_update_interval=5
    )


@pytest.fixture
def tiered_backend(memory_tier_tracker):
    """Create tiered memory backend"""
    return TieredMemoryBackend(
        redis_client=AsyncMock(),
        postgresql_client=AsyncMock(),
        chromadb_client=AsyncMock(),
        tier_tracker=memory_tier_tracker
    )


class TestMemoryTierTracker:
    
    @pytest.mark.asyncio
    async def test_redis_hit_tracking(self, memory_tier_tracker):
        """Test tracking when Redis cache hits"""
        
        # Mock Redis to return data
        with patch.object(memory_tier_tracker, '_try_redis_tier', 
                         return_value=[{"data": "cached_value"}]):
            
            result, metrics = await memory_tier_tracker.track_memory_access(
                query="test query",
                user_id="user123"
            )
            
            # Verify result
            assert result is not None
            assert len(result) == 1
            assert result[0]["data"] == "cached_value"
            
            # Verify metrics
            assert metrics['tier_accessed'] == MemoryTier.REDIS.value
            assert metrics['total_latency_ms'] < 20  # Should be fast
            assert len(metrics['access_chain']) == 1  # Only Redis accessed
            
            # Verify Redis metrics recorded
            redis_metrics = memory_tier_tracker.tier_metrics[MemoryTier.REDIS]
            assert len(redis_metrics) == 1
            assert redis_metrics[0].hit is True
            assert redis_metrics[0].latency_ms < 20
    
    @pytest.mark.asyncio
    async def test_postgresql_fallback(self, memory_tier_tracker):
        """Test fallback to PostgreSQL when Redis misses"""
        
        # Mock Redis miss, PostgreSQL hit
        with patch.object(memory_tier_tracker, '_try_redis_tier', 
                         return_value=None):
            with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                             return_value=[{"data": "pg_value"}]):
                
                result, metrics = await memory_tier_tracker.track_memory_access(
                    query="test query",
                    user_id="user123"
                )
                
                # Verify result
                assert result is not None
                assert result[0]["data"] == "pg_value"
                
                # Verify metrics
                assert metrics['tier_accessed'] == MemoryTier.POSTGRESQL.value
                assert 20 < metrics['total_latency_ms'] < 100  # Medium latency
                assert len(metrics['access_chain']) == 2  # Redis + PostgreSQL
                
                # Verify both tiers were accessed
                assert memory_tier_tracker.tier_metrics[MemoryTier.REDIS][-1].hit is False
                assert memory_tier_tracker.tier_metrics[MemoryTier.POSTGRESQL][-1].hit is True
    
    @pytest.mark.asyncio
    async def test_chromadb_final_fallback(self, memory_tier_tracker):
        """Test fallback to ChromaDB when all faster tiers miss"""
        
        # Mock all misses except ChromaDB
        with patch.object(memory_tier_tracker, '_try_redis_tier', 
                         return_value=None):
            with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                             return_value=None):
                with patch.object(memory_tier_tracker, '_try_chromadb_tier',
                                 return_value=[{"data": "semantic_match", "similarity": 0.85}]):
                    
                    result, metrics = await memory_tier_tracker.track_memory_access(
                        query="complex semantic query",
                        user_id="user123"
                    )
                    
                    # Verify result
                    assert result is not None
                    assert result[0]["data"] == "semantic_match"
                    
                    # Verify metrics
                    assert metrics['tier_accessed'] == MemoryTier.CHROMADB.value
                    assert metrics['total_latency_ms'] > 100  # Slowest tier
                    assert len(metrics['access_chain']) == 3  # All tiers accessed
                    
                    # Verify cascade through all tiers
                    assert memory_tier_tracker.tier_metrics[MemoryTier.REDIS][-1].hit is False
                    assert memory_tier_tracker.tier_metrics[MemoryTier.POSTGRESQL][-1].hit is False
                    assert memory_tier_tracker.tier_metrics[MemoryTier.CHROMADB][-1].hit is True
    
    @pytest.mark.asyncio
    async def test_latency_measurements(self, memory_tier_tracker):
        """Test accurate latency measurements for each tier"""
        
        # Custom mock with controlled delays
        async def mock_redis_with_delay(query, user_id):
            await asyncio.sleep(0.005)  # 5ms
            return [{"data": "redis"}]
        
        async def mock_pg_with_delay(query, user_id):
            await asyncio.sleep(0.025)  # 25ms
            return [{"data": "postgresql"}]
        
        async def mock_chroma_with_delay(query, user_id):
            await asyncio.sleep(0.150)  # 150ms
            return [{"data": "chromadb"}]
        
        # Test each tier's latency
        with patch.object(memory_tier_tracker, '_try_redis_tier', mock_redis_with_delay):
            result, metrics = await memory_tier_tracker.track_memory_access("test", "user123")
            redis_latency = metrics['access_chain'][0]['latency_ms']
            assert 4 < redis_latency < 10  # ~5ms with some overhead
        
        # Test PostgreSQL latency
        with patch.object(memory_tier_tracker, '_try_redis_tier', return_value=None):
            with patch.object(memory_tier_tracker, '_try_postgresql_tier', mock_pg_with_delay):
                result, metrics = await memory_tier_tracker.track_memory_access("test", "user123")
                pg_latency = metrics['access_chain'][1]['latency_ms']
                assert 20 < pg_latency < 35  # ~25ms with overhead
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness_calculation(self, memory_tier_tracker):
        """Test cache effectiveness metric calculation"""
        
        # Simulate multiple accesses with different hit patterns
        hit_pattern = [True, True, False, True, False, True, True, False, True, True]
        
        for i, should_hit in enumerate(hit_pattern):
            with patch.object(memory_tier_tracker, '_try_redis_tier',
                             return_value=[{"data": f"hit_{i}"}] if should_hit else None):
                if not should_hit:
                    with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                                     return_value=[{"data": f"pg_{i}"}]):
                        await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
                else:
                    await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
        
        # Calculate cache effectiveness
        effectiveness = memory_tier_tracker.calculate_cache_effectiveness()
        
        # Should be 70% (7 hits out of 10)
        assert 0.69 < effectiveness < 0.71
    
    @pytest.mark.asyncio
    async def test_query_pattern_tracking(self, memory_tier_tracker):
        """Test query pattern analysis"""
        
        # Simulate repeated similar queries
        queries = [
            "What is my HRV trend?",
            "What is my sleep quality?",
            "What is my stress level?",
            "Show my HRV data",
            "What is my recovery status?"
        ]
        
        for query in queries * 3:  # Repeat each query 3 times
            with patch.object(memory_tier_tracker, '_try_redis_tier',
                             return_value=[{"data": "cached"}] if "HRV" in query else None):
                with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                                 return_value=[{"data": "pg_data"}]):
                    await memory_tier_tracker.track_memory_access(query, "user123")
        
        # Get query patterns
        patterns = memory_tier_tracker.get_query_patterns()
        
        assert patterns['total_unique_patterns'] >= 3
        top_patterns = patterns['top_patterns']
        
        # "what is my" should be most common pattern
        assert any("what is my" in p['pattern'] for p in top_patterns)
        
        # Verify pattern counts
        what_is_pattern = next(p for p in top_patterns if "what is my" in p['pattern'])
        assert what_is_pattern['count'] >= 6  # At least 2 queries * 3 repetitions
    
    @pytest.mark.asyncio
    async def test_tier_statistics_aggregation(self, memory_tier_tracker):
        """Test tier performance statistics aggregation"""
        
        # Force stats update interval to be very short
        memory_tier_tracker.stats_update_interval = 0.1
        
        # Generate some access patterns
        for i in range(20):
            # 60% Redis hits
            redis_hit = i % 10 < 6
            
            with patch.object(memory_tier_tracker, '_try_redis_tier',
                             return_value=[{"data": f"redis_{i}"}] if redis_hit else None):
                if not redis_hit:
                    with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                                     return_value=[{"data": f"pg_{i}"}]):
                        await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
                else:
                    await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
        
        # Wait for stats update
        await asyncio.sleep(0.2)
        
        # Force stats update
        await memory_tier_tracker._update_tier_statistics()
        
        # Get statistics
        stats = memory_tier_tracker.get_tier_statistics()
        
        # Verify Redis stats
        redis_stats = stats.get(MemoryTier.REDIS.value, {})
        assert 0.55 < redis_stats['hit_rate'] < 0.65  # ~60% hit rate
        assert redis_stats['total_accesses'] == 20
        
        # Verify PostgreSQL stats
        pg_stats = stats.get(MemoryTier.POSTGRESQL.value, {})
        assert pg_stats['hit_rate'] == 1.0  # Always hits when accessed
        assert pg_stats['total_accesses'] == 8  # 40% of queries
    
    @pytest.mark.asyncio
    async def test_optimization_suggestions(self, memory_tier_tracker):
        """Test generation of optimization suggestions"""
        
        # Simulate a frequently accessed slow query
        slow_query = "complex analytical query about sleep patterns"
        
        for _ in range(15):  # Make it frequent
            with patch.object(memory_tier_tracker, '_try_redis_tier', return_value=None):
                with patch.object(memory_tier_tracker, '_try_postgresql_tier', return_value=None):
                    with patch.object(memory_tier_tracker, '_try_chromadb_tier',
                                     return_value=[{"data": "semantic_result"}]):
                        await memory_tier_tracker.track_memory_access(slow_query, "user123")
        
        # Get optimization suggestions
        suggestions = memory_tier_tracker.get_optimization_suggestions()
        
        assert len(suggestions) > 0
        
        # Should suggest caching the slow query
        top_suggestion = suggestions[0]
        assert "complex analytical query" in top_suggestion['pattern']
        assert top_suggestion['frequency'] >= 15
        assert top_suggestion['suggestion'] == 'Pre-cache this query pattern in Redis'
        assert top_suggestion['potential_savings_ms'] > 100  # Significant savings
    
    @pytest.mark.asyncio
    async def test_cost_analysis(self, memory_tier_tracker):
        """Test cost tracking and analysis"""
        
        # Generate access patterns with known costs
        for i in range(100):
            if i % 10 < 5:  # 50% Redis
                with patch.object(memory_tier_tracker, '_try_redis_tier',
                                 return_value=[{"data": "redis"}]):
                    await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
            elif i % 10 < 8:  # 30% PostgreSQL
                with patch.object(memory_tier_tracker, '_try_redis_tier', return_value=None):
                    with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                                     return_value=[{"data": "pg"}]):
                        await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
            else:  # 20% ChromaDB
                with patch.object(memory_tier_tracker, '_try_redis_tier', return_value=None):
                    with patch.object(memory_tier_tracker, '_try_postgresql_tier', return_value=None):
                        with patch.object(memory_tier_tracker, '_try_chromadb_tier',
                                         return_value=[{"data": "chroma"}]):
                            await memory_tier_tracker.track_memory_access(f"query_{i}", "user123")
        
        # Get cost analysis
        cost_analysis = memory_tier_tracker.get_cost_analysis()
        
        # Verify cost breakdown
        assert cost_analysis['current_cost'] > 0
        
        breakdown = cost_analysis['cost_breakdown']
        assert MemoryTier.REDIS.value in breakdown
        assert MemoryTier.POSTGRESQL.value in breakdown
        assert MemoryTier.CHROMADB.value in breakdown
        
        # ChromaDB should be most expensive despite fewer accesses
        assert breakdown[MemoryTier.CHROMADB.value]['cost'] > breakdown[MemoryTier.REDIS.value]['cost']
        
        # Verify projected daily cost
        assert cost_analysis['projected_daily_cost'] > cost_analysis['current_cost']
        assert cost_analysis['cost_per_request'] > 0


class TestTieredMemoryBackend:
    
    @pytest.mark.asyncio
    async def test_backend_with_tracking(self, tiered_backend):
        """Test memory backend with tier tracking enabled"""
        
        # Mock Redis to return data
        tiered_backend.redis_client.get.return_value = json.dumps([
            {"content": "cached memory", "timestamp": "2025-01-24T10:00:00Z"}
        ])
        
        with patch.object(tiered_backend.tier_tracker, '_try_redis_tier',
                         return_value=[{"content": "cached memory"}]):
            
            result = await tiered_backend.retrieve_memories(
                query="test query",
                user_id="user123",
                agent_id="neuroscientist"
            )
            
            assert len(result) == 1
            assert result[0]["content"] == "cached memory"
    
    @pytest.mark.asyncio
    async def test_backend_without_tracking(self, tiered_backend):
        """Test memory backend fallback when tracking is disabled"""
        
        # Disable tracking
        tiered_backend.tier_tracker = None
        
        # Mock Redis miss, PostgreSQL hit
        tiered_backend.redis_client.get.return_value = None
        tiered_backend.postgresql_client.fetch.return_value = [
            {"content": "pg memory", "metadata": {}}
        ]
        
        result = await tiered_backend.retrieve_memories(
            query="test query",
            user_id="user123"
        )
        
        assert len(result) == 1
        assert result[0]["content"] == "pg memory"


@pytest.mark.integration
class TestMemoryTierIntegration:
    
    @pytest.mark.asyncio
    async def test_full_tier_cascade_with_event_emission(self, memory_tier_tracker, mock_event_streamer):
        """Test complete tier cascade with event emission"""
        
        # Mock all tiers to show cascade
        with patch.object(memory_tier_tracker, '_try_redis_tier', return_value=None):
            with patch.object(memory_tier_tracker, '_try_postgresql_tier', return_value=None):
                with patch.object(memory_tier_tracker, '_try_chromadb_tier',
                                 return_value=[{"data": "final_result", "score": 0.92}]):
                    
                    result, metrics = await memory_tier_tracker.track_memory_access(
                        query="complex knowledge query about HRV patterns",
                        user_id="user123",
                        agent_id="neuroscientist"
                    )
                    
                    # Verify event was emitted
                    assert mock_event_streamer.stream_event.called
                    
                    # Get the emitted event
                    event = mock_event_streamer.stream_event.call_args[0][0]
                    
                    # Verify event structure
                    assert event.event_type.value == "memory_tier_access"
                    assert event.payload['tier_accessed'] == MemoryTier.CHROMADB.value
                    assert event.payload['query_type'] == "biometric"  # HRV query
                    assert event.payload['cache_hit'] is False
                    
                    # Verify tier latencies in event
                    tier_latencies = event.payload['tier_latencies']
                    assert MemoryTier.REDIS.value in tier_latencies
                    assert MemoryTier.POSTGRESQL.value in tier_latencies
                    assert MemoryTier.CHROMADB.value in tier_latencies
                    
                    # Verify latencies increase with tier depth
                    assert tier_latencies[MemoryTier.REDIS.value]['latency_ms'] < \
                           tier_latencies[MemoryTier.POSTGRESQL.value]['latency_ms'] < \
                           tier_latencies[MemoryTier.CHROMADB.value]['latency_ms']
    
    @pytest.mark.asyncio
    async def test_realistic_access_patterns(self, memory_tier_tracker):
        """Test with realistic access patterns over time"""
        
        # Simulate a day's worth of access patterns
        queries = [
            ("What is my average HRV?", True),    # Likely cached
            ("Show sleep patterns", True),         # Likely cached
            ("Analyze stress correlation with moon phases", False),  # Unusual query
            ("What is my average HRV?", True),    # Repeated query
            ("Recent workout performance", False), # Medium frequency
            ("Show sleep patterns", True),         # Repeated
            ("Hypotheses about recovery", False),  # Complex query
            ("What is my average HRV?", True),    # Very frequent
        ]
        
        for query, likely_cached in queries:
            # Simulate realistic hit rates
            import random
            redis_hit = likely_cached and random.random() < 0.8
            pg_hit = not redis_hit and random.random() < 0.9
            
            with patch.object(memory_tier_tracker, '_try_redis_tier',
                             return_value=[{"data": "cached"}] if redis_hit else None):
                with patch.object(memory_tier_tracker, '_try_postgresql_tier',
                                 return_value=[{"data": "pg"}] if pg_hit else None):
                    with patch.object(memory_tier_tracker, '_try_chromadb_tier',
                                     return_value=[{"data": "semantic"}]):
                        
                        await memory_tier_tracker.track_memory_access(query, "user123")
        
        # Verify patterns were detected
        patterns = memory_tier_tracker.get_query_patterns()
        hrv_pattern = next((p for p in patterns['top_patterns'] if "average hrv" in p['pattern'].lower()), None)
        
        assert hrv_pattern is not None
        assert hrv_pattern['count'] >= 3  # Query repeated 3 times
        
        # Verify cache effectiveness
        effectiveness = memory_tier_tracker.calculate_cache_effectiveness()
        assert 0.4 < effectiveness < 0.8  # Reasonable cache hit rate
        
        # Check for optimization suggestions
        suggestions = memory_tier_tracker.get_optimization_suggestions()
        # Should have suggestions for frequently accessed patterns
        assert any(s for s in suggestions if s['frequency'] >= 3)
        
        print(f"✅ Memory tier tracking test passed - Cache effectiveness: {effectiveness:.1%}")


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 