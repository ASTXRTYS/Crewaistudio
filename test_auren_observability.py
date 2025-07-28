# =============================================================================
# SECTION 10: AMPLIFIED INTEGRATION TESTING WITH OBSERVABILITY-FIRST APPROACH
# =============================================================================
# Tests that not only verify functionality but generate observable metrics,
# populate Grafana dashboards, and test the observability stack itself
# =============================================================================

import pytest
import asyncio
import httpx
import asyncpg
import redis
import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, push_to_gateway, CollectorRegistry

# For structured logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auren.tests.observability")

# Test configuration
TEST_CONFIG = {
    "api_base_url": os.getenv("TEST_API_URL", "http://144.126.215.218:8888"),
    "postgres_url": os.getenv("TEST_DATABASE_URL", "postgresql://auren_user:auren_secure_2025@144.126.215.218:5432/auren_production"),
    "redis_url": os.getenv("TEST_REDIS_URL", "redis://144.126.215.218:6379/1"),
    "kafka_bootstrap": os.getenv("TEST_KAFKA_BOOTSTRAP", "144.126.215.218:9092"),
    "chromadb_url": os.getenv("TEST_CHROMADB_URL", "http://144.126.215.218:8001"),
    "grafana_url": os.getenv("GRAFANA_URL", "http://144.126.215.218:3000"),
    "prometheus_url": os.getenv("PROMETHEUS_URL", "http://144.126.215.218:9090"),
    "test_user_id": "test_user_observability",
    "enable_observability": True
}

# =============================================================================
# TEST METRICS FOR GRAFANA OBSERVABILITY
# =============================================================================

class TestMetrics:
    """Prometheus metrics generated during tests for Grafana visualization"""
    
    def __init__(self, registry=None):
        self.registry = registry or CollectorRegistry()
        
        # Four Golden Signals
        self.request_rate = Counter(
            'auren_test_requests_total',
            'Total number of test requests',
            ['endpoint', 'method', 'test_name'],
            registry=self.registry
        )
        
        self.error_rate = Counter(
            'auren_test_errors_total',
            'Total number of test errors',
            ['endpoint', 'error_type', 'test_name'],
            registry=self.registry
        )
        
        self.latency = Histogram(
            'auren_test_request_duration_seconds',
            'Request latency in seconds',
            ['endpoint', 'method', 'test_name'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        
        self.saturation = Gauge(
            'auren_test_saturation_ratio',
            'System saturation during tests',
            ['resource_type', 'test_name'],
            registry=self.registry
        )
        
        # Additional observability metrics
        self.biometric_events_processed = Counter(
            'auren_test_biometric_events_total',
            'Total biometric events processed in tests',
            ['device_type', 'event_type', 'test_name'],
            registry=self.registry
        )
    
    def push_to_grafana(self):
        """Push metrics to Prometheus Pushgateway for Grafana"""
        push_gateway_url = os.getenv('PROMETHEUS_PUSHGATEWAY_URL', '144.126.215.218:9091')
        try:
            push_to_gateway(
                push_gateway_url,
                job='auren_integration_tests',
                registry=self.registry
            )
            logger.info(f"Test metrics pushed to Grafana via {push_gateway_url}")
        except Exception as e:
            logger.error(f"Failed to push metrics: {e}")

# Global test metrics instance
test_metrics = TestMetrics()

# =============================================================================
# OBSERVABILITY-ENHANCED TEST SUITE
# =============================================================================

class TestAURENObservability:
    """
    Integration tests that generate observable metrics and test the observability stack
    
    Run with: pytest -v test_auren_observability.py --asyncio-mode=auto
    """
    
    @pytest.fixture(scope="session")
    async def setup_test_environment(self):
        """Setup test environment with database and Redis connections"""
        # Create test database connection
        self.db_pool = await asyncpg.create_pool(TEST_CONFIG["postgres_url"])
        
        # Create test Redis connection
        self.redis = redis.from_url(TEST_CONFIG["redis_url"])
        
        # Clean test data
        await self._cleanup_test_data()
        
        yield
        
        # Cleanup
        await self._cleanup_test_data()
        await self.db_pool.close()
        self.redis.close()
        
        # Push final metrics
        test_metrics.push_to_grafana()
    
    async def _cleanup_test_data(self):
        """Clean up test data from previous runs"""
        async with self.db_pool.acquire() as conn:
            # Clean biometric events for test user
            await conn.execute("""
                DELETE FROM biometric_events 
                WHERE user_id = $1
            """, TEST_CONFIG["test_user_id"])
    
    @pytest.mark.asyncio
    async def test_webhook_with_observability_metrics(self, setup_test_environment):
        """Test webhook processing while generating observable metrics"""
        test_name = "webhook_observability"
        
        async with httpx.AsyncClient() as client:
            # Prepare webhook data
            webhook_data = {
                "event_type": "daily_activity",
                "user_id": TEST_CONFIG["test_user_id"],
                "data": {
                    "id": "test_activity_123",
                    "date": datetime.utcnow().date().isoformat(),
                    "steps": 10000,
                    "calories": 500,
                    "average_heart_rate": 72,
                    "hrv": 65
                }
            }
            
            # Measure request latency
            start_time = time.time()
            
            response = await client.post(
                f"{TEST_CONFIG['api_base_url']}/webhooks/oura",
                json=webhook_data
            )
            
            latency = time.time() - start_time
            
            # Record metrics
            test_metrics.request_rate.labels(
                endpoint="/webhooks/oura",
                method="POST",
                test_name=test_name
            ).inc()
            
            test_metrics.latency.labels(
                endpoint="/webhooks/oura",
                method="POST",
                test_name=test_name
            ).observe(latency)
            
            if response.status_code != 200:
                test_metrics.error_rate.labels(
                    endpoint="/webhooks/oura",
                    error_type=f"http_{response.status_code}",
                    test_name=test_name
                ).inc()
            
            assert response.status_code == 200
            
            # Record biometric event metric
            test_metrics.biometric_events_processed.labels(
                device_type="oura",
                event_type="daily_activity",
                test_name=test_name
            ).inc()
            
            logger.info(f"Webhook test completed in {latency:.3f}s")
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint_availability(self, setup_test_environment):
        """Test that metrics endpoint is available and returns Prometheus format"""
        test_name = "metrics_availability"
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            response = await client.get(f"{TEST_CONFIG['api_base_url']}/metrics")
            
            latency = time.time() - start_time
            
            # Record metrics
            test_metrics.request_rate.labels(
                endpoint="/metrics",
                method="GET",
                test_name=test_name
            ).inc()
            
            test_metrics.latency.labels(
                endpoint="/metrics",
                method="GET",
                test_name=test_name
            ).observe(latency)
            
            assert response.status_code == 200
            assert "# HELP" in response.text
            assert "# TYPE" in response.text
            
            logger.info("Metrics endpoint is working correctly")
    
    @pytest.mark.asyncio
    async def test_prometheus_scraping(self, setup_test_environment):
        """Test that Prometheus is successfully scraping the biometric API"""
        test_name = "prometheus_scraping"
        
        async with httpx.AsyncClient() as client:
            # Query Prometheus targets
            response = await client.get(
                f"{TEST_CONFIG['prometheus_url']}/api/v1/targets"
            )
            
            assert response.status_code == 200
            
            targets = response.json()["data"]["activeTargets"]
            
            # Find biometric-api target
            biometric_target = None
            for target in targets:
                if target.get("labels", {}).get("job") == "biometric-api":
                    biometric_target = target
                    break
            
            assert biometric_target is not None, "Biometric API not found in Prometheus targets"
            assert biometric_target["health"] == "up", "Biometric API is not healthy in Prometheus"
            
            logger.info("Prometheus is successfully scraping the biometric API")
    
    @pytest.mark.asyncio
    async def test_grafana_dashboards_availability(self, setup_test_environment):
        """Test that Grafana dashboards are available"""
        test_name = "grafana_availability"
        
        async with httpx.AsyncClient() as client:
            # Test Grafana API
            grafana_auth = ("admin", "auren_grafana_2025")
            
            # Check dashboards
            response = await client.get(
                f"{TEST_CONFIG['grafana_url']}/api/search",
                auth=grafana_auth
            )
            
            if response.status_code == 200:
                dashboards = response.json()
                dashboard_titles = [d.get("title", "") for d in dashboards]
                
                # Check for our created dashboards
                assert any("AUREN" in title for title in dashboard_titles), "AUREN dashboards not found"
                
                logger.info(f"Found {len(dashboards)} Grafana dashboards")
            
            test_metrics.request_rate.labels(
                endpoint="grafana_api",
                method="GET",
                test_name=test_name
            ).inc()
    
    @pytest.mark.asyncio
    async def test_concurrent_webhook_processing(self, setup_test_environment):
        """Test system handles concurrent webhooks with metrics"""
        test_name = "concurrent_webhooks"
        
        async with httpx.AsyncClient() as client:
            # Create 20 concurrent webhook requests
            tasks = []
            for i in range(20):
                webhook_data = {
                    "event_type": "activity.created",
                    "user_id": TEST_CONFIG["test_user_id"],
                    "data": {
                        "id": f"activity_{i}",
                        "calories": 100 + i,
                        "distance": 1000 + i * 100,
                        "average_heart_rate": 120 + i
                    }
                }
                
                task = client.post(
                    f"{TEST_CONFIG['api_base_url']}/webhooks/whoop",
                    json=webhook_data
                )
                tasks.append(task)
            
            # Execute all requests concurrently
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Count successes and failures
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            # Record metrics
            test_metrics.saturation.labels(
                resource_type="concurrent_requests",
                test_name=test_name
            ).set(len(tasks))
            
            # All should succeed
            assert success_count == len(tasks), f"Only {success_count}/{len(tasks)} requests succeeded"
            
            logger.info(f"Processed {len(tasks)} concurrent requests in {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, setup_test_environment):
        """Test health endpoint performance under load"""
        test_name = "health_performance"
        
        async with httpx.AsyncClient() as client:
            # Measure response times for 50 requests
            response_times = []
            
            for i in range(50):
                start_time = time.time()
                
                response = await client.get(
                    f"{TEST_CONFIG['api_base_url']}/health"
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                assert response.status_code == 200
                
                # Record each request
                test_metrics.request_rate.labels(
                    endpoint="/health",
                    method="GET",
                    test_name=test_name
                ).inc()
                
                test_metrics.latency.labels(
                    endpoint="/health",
                    method="GET",
                    test_name=test_name
                ).observe(response_time)
            
            # Check performance metrics
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 0.1  # Average should be under 100ms
            assert max_response_time < 0.5  # Max should be under 500ms
            
            logger.info(f"Health endpoint performance: Avg={avg_response_time:.3f}s, Max={max_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_database_connectivity(self, setup_test_environment):
        """Test database connectivity and performance"""
        test_name = "database_connectivity"
        
        async with self.db_pool.acquire() as conn:
            # Test simple query
            start_time = time.time()
            result = await conn.fetchval("SELECT 1")
            query_time = time.time() - start_time
            
            assert result == 1
            
            # Test biometric_events table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'biometric_events'
                )
            """)
            
            assert table_exists
            
            test_metrics.latency.labels(
                endpoint="postgres_query",
                method="SELECT",
                test_name=test_name
            ).observe(query_time)
            
            logger.info(f"Database query completed in {query_time:.3f}s")

# =============================================================================
# TEST RUNNER
# =============================================================================

if __name__ == "__main__":
    # Run tests with enhanced observability
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",
        "--asyncio-mode=auto"
    ]) 