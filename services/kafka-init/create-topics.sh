#!/bin/bash

set -e

echo "[Kafka Init] Waiting for Kafka to become available..."
RETRIES=10
while ! nc -z kafka 9092; do
  if [ $RETRIES -le 0 ]; then
    echo "[Kafka Init] ❌ Kafka did not become ready in time. Exiting."
    exit 1
  fi
  echo "[Kafka Init] Kafka not ready, retrying... ($RETRIES retries left)"
  sleep 5
  ((RETRIES--))
done

echo "[Kafka Init] ✅ Kafka is ready. Creating topics..."

create_topic() {
  local topic=$1
  kafka-topics --bootstrap-server kafka:9092 \
    --create \
    --replication-factor 1 \
    --partitions 1 \
    --topic "$topic" \
    && echo "[Kafka Init] ✅ Created topic: $topic" \
    || echo "[Kafka Init] ⚠️ Topic $topic may already exist or failed to create."
}

create_topic "live_model_metrics"
create_topic "scored_model_metrics"

echo "[Kafka Init] 🏁 Topic creation script completed."
