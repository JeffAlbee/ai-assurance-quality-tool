#!/bin/bash

echo "[Kafka Init] Waiting for Kafka..."
RETRIES=10
until nc -z kafka 9092 || [ $RETRIES -eq 0 ]; do
  echo "[Kafka Init] Kafka not ready, retrying..."
  sleep 5
  ((RETRIES--))
done

echo "[Kafka Init] Kafka is ready. Creating topics..."

kafka-topics --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic live_model_metrics || echo "[Kafka Init] Topic live_model_metrics may already exist."

kafka-topics --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic scored_model_metrics || echo "[Kafka Init] Topic scored_model_metrics may already exist."
