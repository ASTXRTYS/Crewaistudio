#!/bin/bash
# Create Kafka topics for AUREN system

echo "Creating Kafka topics..."

# Wait for Kafka to be ready
sleep 10

# Create topics
docker exec auren-kafka kafka-topics --create --topic agent-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec auren-kafka kafka-topics --create --topic memory-access --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec auren-kafka kafka-topics --create --topic hypothesis-updates --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 --if-not-exists
docker exec auren-kafka kafka-topics --create --topic breakthrough-alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 --if-not-exists
docker exec auren-kafka kafka-topics --create --topic biometric-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists

# List topics
echo "Topics created. Current topics:"
docker exec auren-kafka kafka-topics --list --bootstrap-server localhost:9092 