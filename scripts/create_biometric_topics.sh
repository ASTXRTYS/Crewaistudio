#!/bin/bash
# Create Kafka topics for AUREN Biometric Bridge

echo "Creating Kafka topics for Biometric Bridge..."

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 10

# Create biometric-events topic (main event stream)
docker exec -it auren-kafka kafka-topics.sh --create \
  --topic biometric-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

echo "✅ Created biometric-events topic"

# Create neuros-mode-switches topic (cognitive mode changes)
docker exec -it auren-kafka kafka-topics.sh --create \
  --topic neuros-mode-switches \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

echo "✅ Created neuros-mode-switches topic"

# Create system-metrics topic (monitoring data)
docker exec -it auren-kafka kafka-topics.sh --create \
  --topic system-metrics \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

echo "✅ Created system-metrics topic"

# Create biometric-events.dlq topic (dead letter queue)
docker exec -it auren-kafka kafka-topics.sh --create \
  --topic biometric-events.dlq \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

echo "✅ Created biometric-events.dlq topic"

# List all topics to verify
echo ""
echo "All Kafka topics:"
docker exec -it auren-kafka kafka-topics.sh --list \
  --bootstrap-server localhost:9092

echo ""
echo "✅ All biometric topics created successfully!" 