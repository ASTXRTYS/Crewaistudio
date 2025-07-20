"""
Health monitoring system for AUREN Kafka infrastructure.

Provides comprehensive health checks and monitoring for Kafka cluster,
producers, consumers, and overall system health.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from kafka import KafkaAdminClient, KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaHealthCheck:
    """Comprehensive health checks for Kafka infrastructure"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        
    def check_cluster_health(self) -> Dict[str, Any]:
        """Comprehensive health check of Kafka cluster"""
        health_status = {
            "kafka_available": False,
            "required_topics": {},
            "consumer_groups": {},
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check Kafka connectivity
            admin = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='health-checker',
                request_timeout_ms=5000
            )
            
            # Verify cluster is responsive
            metadata = admin.list_topics()
            health_status["kafka_available"] = True
            
            # Check required topics exist
            from src.config.topic_config import TopicMapping
            required_topics = TopicMapping.get_all_topics()
            
            for topic in required_topics:
                health_status["required_topics"][topic] = topic in metadata
                
            # Check consumer groups (basic check)
            try:
                consumer_groups = admin.list_consumer_groups()
                health_status["consumer_groups"] = {
                    "total": len(consumer_groups),
                    "groups": [group[0] for group in consumer_groups[:5]]  # First 5
                }
            except Exception as e:
                logger.warning(f"Could not list consumer groups: {e}")
                
            admin.close()
            
        except KafkaError as e:
            health_status["errors"].append(f"Kafka connection error: {str(e)}")
            logger.error(f"Health check failed: {e}")
        except Exception as e:
            health_status["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Health check failed: {e}")
            
        return health_status
    
    def check_producer_health(self) -> Dict[str, Any]:
        """Test producer health and throughput"""
        producer_status = {
            "producer_available": False,
            "send_latency_ms": None,
            "throughput": None,
            "errors": []
        }
        
        try:
            from src.infrastructure.kafka.producer import EventProducer
            producer = EventProducer()
            
            # Test basic connectivity
            producer_status["producer_available"] = True
            
            # Test send latency
            start_time = time.time()
            test_message = b"health_check_test"
            future = producer.producer.send("health-check", value=test_message)
            future.get(timeout=5)  # Wait for send confirmation
            latency_ms = (time.time() - start_time) * 1000
            
            producer_status["send_latency_ms"] = round(latency_ms, 2)
            producer.flush(timeout=5)
            producer.close()
            
        except Exception as e:
            producer_status["errors"].append(f"Producer health check failed: {str(e)}")
            logger.error(f"Producer health check failed: {e}")
            
        return producer_status
    
    def check_consumer_health(self, topics: List[str]) -> Dict[str, Any]:
        """Test consumer health for given topics"""
        consumer_status = {
            "consumer_available": False,
            "topics_accessible": {},
            "errors": []
        }
        
        try:
            from src.infrastructure.kafka.consumer import EventConsumer
            consumer = EventConsumer(
                topics=topics,
                group_id="health-check-consumer"
            )
            
            consumer_status["consumer_available"] = True
            
            # Check topic accessibility
            for topic in topics:
                try:
                    # Try to get metadata for each topic
                    consumer.consumer.topics()
                    consumer_status["topics_accessible"][topic] = True
                except Exception as e:
                    consumer_status["topics_accessible"][topic] = False
                    consumer_status["errors"].append(f"Topic {topic} inaccessible: {str(e)}")
                    
            consumer.close()
            
        except Exception as e:
            consumer_status["errors"].append(f"Consumer health check failed: {str(e)}")
            logger.error(f"Consumer health check failed: {e}")
            
        return consumer_status
    
    def check_throughput(self, num_messages: int = 10) -> Dict[str, Any]:
        """Test message throughput"""
        throughput_status = {
            "throughput_available": False,
            "messages_per_second": None,
            "total_messages": num_messages,
            "elapsed_seconds": None,
            "errors": []
        }
        
        try:
            from src.infrastructure.kafka.producer import EventProducer
            from src.infrastructure.kafka.consumer import EventConsumer
            from src.infrastructure.schemas.health_events import HealthEvent, EventType
            
            producer = EventProducer()
            received_count = 0
            
            def handle_event(event):
                nonlocal received_count
                received_count += 1
            
            # Set up consumer
            from src.config.topic_config import TopicMapping
            topic = TopicMapping.get_topic_for_event_type(EventType.BIOMETRIC)
            
            consumer = EventConsumer(
                topics=[topic],
                group_id="throughput-test"
            )
            
            consumer_thread = threading.Thread(
                target=lambda: consumer.start(biometric_handler=handle_event)
            )
            consumer_thread.daemon = True
            consumer_thread.start()
            
            # Wait for consumer to start
            time.sleep(2)
            
            # Send messages
            start_time = time.time()
            for i in range(num_messages):
                test_event = HealthEvent(
                    event_id=f"throughput_test_{i}",
                    user_id="health_check_user",
                    event_type=EventType.BIOMETRIC_UPDATE,
                    timestamp=datetime.now(),
                    data={"test": True, "index": i},
                    source="health_check"
                )
                producer.send_biometric_event(test_event)
                
            producer.flush(timeout=10)
            
            # Wait for all messages
            timeout = 30
            while received_count < num_messages and (time.time() - start_time) < timeout:
                time.sleep(0.5)
                
            elapsed = time.time() - start_time
            throughput = num_messages / elapsed if elapsed > 0 else 0
            
            throughput_status["throughput_available"] = True
            throughput_status["messages_per_second"] = round(throughput, 2)
            throughput_status["elapsed_seconds"] = round(elapsed, 2)
            
            # Cleanup
            consumer.close()
            producer.close()
            
        except Exception as e:
            throughput_status["errors"].append(f"Throughput test failed: {str(e)}")
            logger.error(f"Throughput test failed: {e}")
            
        return throughput_status
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        from src.config.topic_config import TopicMapping
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "kafka_cluster": self.check_cluster_health(),
            "producer": self.check_producer_health(),
            "consumer": self.check_consumer_health(TopicMapping.get_all_topics()),
            "throughput": self.check_throughput(),
            "overall_status": "unknown"
        }
        
        # Determine overall status
        issues = []
        
        if not health_report["kafka_cluster"]["kafka_available"]:
            issues.append("Kafka cluster unavailable")
            
        if not health_report["producer"]["producer_available"]:
            issues.append("Producer unavailable")
            
        if not health_report["consumer"]["consumer_available"]:
            issues.append("Consumer unavailable")
            
        if health_report["throughput"]["messages_per_second"] is None:
            issues.append("Throughput test failed")
            
        if issues:
            health_report["overall_status"] = "degraded"
            health_report["issues"] = issues
        else:
            health_report["overall_status"] = "healthy"
            
        return health_report


class HealthMonitor:
    """Continuous health monitoring for AUREN infrastructure"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.health_checker = KafkaHealthCheck(bootstrap_servers)
        self.running = False
        
    def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring"""
        self.running = True
        logger.info("Starting health monitoring...")
        
        while self.running:
            try:
                health = self.health_checker.get_system_health()
                
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Health Check:")
                print(f"   Overall Status: {health['overall_status']}")
                
                if health['overall_status'] == 'healthy':
                    print("   ✅ All systems operational")
                else:
                    print(f"   ⚠️  Issues detected: {', '.join(health.get('issues', []))}")
                    
                # Basic metrics
                if health['throughput']['messages_per_second']:
                    print(f"   📊 Throughput: {health['throughput']['messages_per_second']} msg/sec")
                    
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.stop_monitoring()
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.running = False
        logger.info("Health monitoring stopped")


# Convenience functions
def check_system_ready() -> bool:
    """Quick check if system is ready for CEP implementation"""
    checker = KafkaHealthCheck()
    health = checker.get_system_health()
    
    return health["overall_status"] == "healthy"


def print_health_summary():
    """Print comprehensive health summary"""
    checker = KafkaHealthCheck()
    health = checker.get_system_health()
    
    print("\n" + "=" * 70)
    print("AUREN KAFKA INFRASTRUCTURE HEALTH SUMMARY")
    print("=" * 70)
    print(f"Timestamp: {health['timestamp']}")
    print(f"Overall Status: {health['overall_status']}")
    
    if health['overall_status'] == 'healthy':
        print("🎉 All systems operational - Ready for CEP implementation!")
    else:
        print("⚠️  Issues detected:")
        for issue in health.get('issues', []):
            print(f"   - {issue}")
    
    # Kafka cluster details
    cluster = health['kafka_cluster']
    print(f"\nKafka Cluster:")
    print(f"   Available: {'✅' if cluster['kafka_available'] else '❌'}")
    
    print(f"\nRequired Topics:")
    for topic, exists in cluster['required_topics'].items():
        print(f"   {topic}: {'✅' if exists else '❌'}")
    
    # Performance metrics
    throughput = health['throughput']
    if throughput['messages_per_second']:
        print(f"\nPerformance:")
        print(f"   Throughput: {throughput['messages_per_second']} msg/sec")
        print(f"   Test Messages: {throughput['total_messages']}")
        print(f"   Test Duration: {throughput['elapsed_seconds']}s")
    
    # Errors if any
    if cluster['errors']:
        print(f"\nErrors:")
        for error in cluster['errors']:
            print(f"   - {error}")
    
    print("=" * 70)


if __name__ == "__main__":
    """Run health check when executed directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AUREN Kafka Health Check')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor = HealthMonitor()
        monitor.start_monitoring(args.interval)
    else:
        print_health_summary()
