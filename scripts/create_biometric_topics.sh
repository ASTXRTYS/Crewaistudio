#!/bin/bash

# Script to create Kafka topics for AUREN Biometric Bridge

echo "Creating Kafka topics for biometric bridge..."

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 5

# Create biometric-events topic (main input)
docker exec -it auren-kafka kafka-topics.sh \
  --create \
  --topic biometric-events \
  --bootstrap-server localhost:29092 \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

# Create neuros-mode-switches topic (output)
docker exec -it auren-kafka kafka-topics.sh \
  --create \
  --topic neuros-mode-switches \
  --bootstrap-server localhost:29092 \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

# Create biometric-patterns topic (for detected patterns)
docker exec -it auren-kafka kafka-topics.sh \
  --create \
  --topic biometric-patterns \
  --bootstrap-server localhost:29092 \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

# Create biometric-alerts topic (for critical alerts)
docker exec -it auren-kafka kafka-topics.sh \
  --create \
  --topic biometric-alerts \
  --bootstrap-server localhost:29092 \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

# List all topics to verify
echo ""
echo "Listing all Kafka topics:"
docker exec -it auren-kafka kafka-topics.sh \
  --list \
  --bootstrap-server localhost:29092

echo ""
echo "Kafka topics created successfully!" 