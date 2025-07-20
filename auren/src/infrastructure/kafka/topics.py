from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from typing import List
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


class TopicManager:
    """Manages Kafka topic creation and configuration"""
    
    def __init__(self):
        self.admin_client = KafkaAdminClient(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            client_id='auren-topic-manager'
        )
    
    def create_topics(self) -> None:
        """Create all required Kafka topics"""
        topics = [
            NewTopic(
                name=settings.kafka.health_biometrics_topic,
                num_partitions=3,
                replication_factor=1
            ),
            NewTopic(
                name=settings.kafka.triggers_detected_topic,
                num_partitions=3,
                replication_factor=1
            ),
            NewTopic(
                name=settings.kafka.conversations_events_topic,
                num_partitions=3,
                replication_factor=1
            ),
            NewTopic(
                name="system.events",
                num_partitions=1,
                replication_factor=1
            ),
            NewTopic(
                name="auren.health.biometrics",
                num_partitions=3,
                replication_factor=1
            ),
            NewTopic(
                name="auren.triggers.detected",
                num_partitions=3,
                replication_factor=1
            ),
            NewTopic(
                name="auren.conversations.events",
                num_partitions=3,
                replication_factor=1
            )
        ]
        
        for topic in topics:
            try:
                self.admin_client.create_topics([topic])
                logger.info(f"Created topic: {topic.name}")
            except TopicAlreadyExistsError:
                logger.info(f"Topic already exists: {topic.name}")
    
    def create_topic(self, name: str, partitions: int = 3, replication: int = 1) -> None:
        """Create a single topic"""
        topic = NewTopic(
            name=name,
            num_partitions=partitions,
            replication_factor=replication
        )
        
        try:
            self.admin_client.create_topics([topic])
            logger.info(f"Created topic: {name}")
        except TopicAlreadyExistsError:
            logger.info(f"Topic already exists: {name}")
    
    def list_topics(self) -> List[str]:
        """List all topics in the cluster"""
        metadata = self.admin_client.list_topics()
        return list(metadata)
    
    def delete_topic(self, name: str) -> None:
        """Delete a topic (use with caution)"""
        try:
            self.admin_client.delete_topics([name])
            logger.info(f"Deleted topic: {name}")
        except Exception as e:
            logger.error(f"Error deleting topic {name}: {e}")
    
    def close(self):
        """Close admin client connection"""
        self.admin_client.close()
