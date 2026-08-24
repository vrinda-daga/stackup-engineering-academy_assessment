"""
=============================================================
StackUp Engineering Academy - Data Engineering Assessment
Pillar: Big Data Processing - Task 3.2
=============================================================

Kafka real-time streaming pipeline.

How to run:
  docker-compose up -d

  python solutions/submissions/vrinda-daga/03_big_data/kafka_streaming.py --mode producer
  python solutions/submissions/vrinda-daga/03_big_data/kafka_streaming.py --mode consumer

  # Produce, then consume in one process for testing:
  python solutions/submissions/vrinda-daga/03_big_data/kafka_streaming.py --mode both --delay 0 --reset-topics
"""

import argparse
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import (
    KafkaConfigurationError,
    KafkaError,
    TopicAlreadyExistsError,
)
from kafka.serializer import Deserializer, Serializer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("kafka").setLevel(logging.WARNING)


# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
EVENTS_DIR = os.path.join(
    BASE_DIR,
    "datasets",
    "events_stream",
)
OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs",
    "results",
    "vrinda-daga",
    "03_big_data",
    "kafka",
)


# ------------------------------------------------------------------------------
# Kafka config
# ------------------------------------------------------------------------------

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_EVENTS = "presight.project.events"
TOPIC_ESCALATIONS = "presight.escalations.critical"
CONSUMER_GROUP_ID = "presight-assessment-consumer"
REQUIRED_TOPICS = {
    TOPIC_EVENTS: 3,
    TOPIC_ESCALATIONS: 1,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def discover_event_files(events_dir: str) -> list[str]:
    """
    Return all monthly event JSONL files in deterministic order.
    """
    if not os.path.isdir(events_dir):
        raise FileNotFoundError(f"Events directory not found: {events_dir}")

    event_files = sorted(
        os.path.join(events_dir, filename)
        for filename in os.listdir(events_dir)
        if filename.startswith("events_") and filename.endswith(".jsonl")
    )

    if not event_files:
        raise FileNotFoundError(f"No events_*.jsonl files found in: {events_dir}")

    return event_files


class JsonValueSerializer(Serializer):
    def serialize(self, topic: str, headers, data: dict) -> bytes:
        return json.dumps(data, default=str).encode("utf-8")


class JsonValueDeserializer(Deserializer):
    def deserialize(self, topic: str, headers, data: bytes) -> dict:
        return json.loads(data.decode("utf-8"))


class TextKeySerializer(Serializer):
    def serialize(self, topic: str, headers, data: str) -> bytes:
        return str(data).encode("utf-8") if data is not None else None


class TextKeyDeserializer(Deserializer):
    def deserialize(self, topic: str, headers, data: bytes) -> str:
        return data.decode("utf-8") if data is not None else None


# ==============================================================================
# 3.2a - Setup
# ==============================================================================

def build_admin_client():
    logger.info("Connecting to Kafka admin at %s", KAFKA_BOOTSTRAP)

    try:
        return KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            client_id="presight-topic-admin",
            request_timeout_ms=15000,
        )
    except KafkaConfigurationError:
        raise
    except KafkaError as exc:
        raise RuntimeError(
            "Kafka broker is not available at localhost:9092. "
            "Start Kafka first with: docker-compose up -d"
        ) from exc


def reset_topics():
    """
    Delete the assessment topics so a local test run starts from empty topics.
    """
    admin_client = build_admin_client()

    try:
        existing_topics = set(admin_client.list_topics())
        topics_to_delete = [
            topic_name
            for topic_name in REQUIRED_TOPICS
            if topic_name in existing_topics
        ]

        if not topics_to_delete:
            logger.info("No existing assessment Kafka topics to reset.")
            return

        logger.info(
            "Deleting existing Kafka topics: %s",
            ", ".join(topics_to_delete),
        )
        admin_client.delete_topics(topics=topics_to_delete, timeout_ms=30000)
        time.sleep(2)

    finally:
        admin_client.close()


def create_topics(reset_existing: bool = False):
    """
    Create required Kafka topics:
      - presight.project.events with 3 partitions
      - presight.escalations.critical with 1 partition
    """
    if reset_existing:
        reset_topics()

    admin_client = build_admin_client()

    existing_topics = set(admin_client.list_topics())
    topics_to_create = [
        NewTopic(
            name=topic_name,
            num_partitions=partitions,
            replication_factor=1,
        )
        for topic_name, partitions in REQUIRED_TOPICS.items()
    ]

    missing_topics = [
        topic
        for topic in topics_to_create
        if topic.name not in existing_topics
    ]

    if not missing_topics:
        logger.info("Kafka topics already exist.")
        admin_client.close()
        return

    try:
        admin_client.create_topics(
            new_topics=missing_topics,
            validate_only=False,
        )
        logger.info(
            "Created Kafka topics: %s",
            ", ".join(topic.name for topic in missing_topics),
        )
    except TopicAlreadyExistsError:
        logger.info("Kafka topics already exist.")
    finally:
        admin_client.close()


# ==============================================================================
# 3.2b - Producer
# ==============================================================================

def build_producer():
    """
    Build a Kafka producer that serializes values as JSON and keys as UTF-8 text.
    """
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        key_serializer=TextKeySerializer(),
        value_serializer=JsonValueSerializer(),
        acks="all",
        retries=3,
        request_timeout_ms=30000,
        max_block_ms=30000,
    )


def run_producer(producer, events_dir: str, delay_seconds: float = 0.05):
    """
    Read all events_*.jsonl files and publish each event to Kafka.
    """
    event_files = discover_event_files(events_dir)
    logger.info("Starting producer. Source directory: %s", events_dir)
    logger.info("Event files found: %s", len(event_files))

    start_time = time.time()
    total_sent = 0

    for event_file in event_files:
        file_sent = 0
        logger.info("Streaming file: %s", os.path.basename(event_file))

        with open(event_file, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(
                        "Skipping invalid JSON in %s on line %s",
                        os.path.basename(event_file),
                        line_number,
                    )
                    continue

                event["produced_at"] = utc_now_iso()
                event_type = event.get("event_type", "unknown")

                producer.send(
                    TOPIC_EVENTS,
                    key=event_type,
                    value=event,
                )

                total_sent += 1
                file_sent += 1

                if total_sent % 100 == 0:
                    logger.info(
                        "Sent %s messages. Latest event_id=%s event_type=%s",
                        total_sent,
                        event.get("event_id"),
                        event_type,
                    )

                time.sleep(delay_seconds)

        logger.info(
            "Finished %s (%s messages)",
            os.path.basename(event_file),
            file_sent,
        )

    producer.flush()
    producer.close()

    elapsed = time.time() - start_time
    throughput = total_sent / elapsed if elapsed > 0 else 0

    logger.info("Producer finished. Total messages sent: %s", total_sent)
    logger.info("Producer throughput: %.2f messages/second", throughput)

    return total_sent


# ==============================================================================
# 3.2c and 3.2d - Consumer and Escalation Forwarding
# ==============================================================================

def build_consumer(topic: str):
    """
    Build a Kafka consumer subscribed to the requested topic.
    """
    return KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=CONSUMER_GROUP_ID,
        key_deserializer=TextKeyDeserializer(),
        value_deserializer=JsonValueDeserializer(),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=10000,
        request_timeout_ms=30000,
    )


def is_critical_escalation(event: dict) -> bool:
    payload = event.get("payload") or {}

    return (
        event.get("event_type") == "escalation_raised"
        and payload.get("severity") == "Critical"
    )


def write_summary(
    event_counts: dict,
    total_consumed: int,
    critical_forwarded: int,
    elapsed_seconds: float,
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    throughput = total_consumed / elapsed_seconds if elapsed_seconds > 0 else 0
    summary = {
        "run_at": utc_now_iso(),
        "source_topic": TOPIC_EVENTS,
        "critical_escalation_topic": TOPIC_ESCALATIONS,
        "total_messages_consumed": total_consumed,
        "event_counts": dict(sorted(event_counts.items())),
        "critical_escalations_forwarded": critical_forwarded,
        "throughput_messages_per_second": round(throughput, 2),
    }

    summary_path = os.path.join(OUTPUT_DIR, "summary.json")

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    logger.info("Summary written to: %s", summary_path)

    return summary


def run_consumer(consumer):
    """
    Consume events, count event types, and forward critical escalations.
    """
    logger.info("Starting consumer. Topic: %s", TOPIC_EVENTS)

    forwarding_producer = build_producer()
    event_counts = defaultdict(int)
    total_consumed = 0
    critical_forwarded = 0
    start_time = time.time()

    try:
        for message in consumer:
            event = message.value
            event_type = event.get("event_type", "unknown")
            project_id = event.get("project_id")

            total_consumed += 1
            event_counts[event_type] += 1

            if total_consumed % 100 == 0:
                logger.info(
                    "Consumed %s messages. Latest event_id=%s "
                    "event_type=%s project_id=%s",
                    total_consumed,
                    event.get("event_id"),
                    event_type,
                    project_id,
                )

            if is_critical_escalation(event):
                forwarding_producer.send(
                    TOPIC_ESCALATIONS,
                    key=event_type,
                    value=event,
                )
                critical_forwarded += 1

        forwarding_producer.flush()

    finally:
        forwarding_producer.close()
        consumer.close()

    elapsed_seconds = time.time() - start_time

    logger.info("Consumer finished. Total consumed: %s", total_consumed)
    logger.info(
        "Critical escalations forwarded: %s",
        critical_forwarded,
    )

    return write_summary(
        event_counts=event_counts,
        total_consumed=total_consumed,
        critical_forwarded=critical_forwarded,
        elapsed_seconds=elapsed_seconds,
    )


# ==============================================================================
# Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kafka real-time streaming pipeline for Task 3.2"
    )
    parser.add_argument(
        "--mode",
        choices=["producer", "consumer", "both"],
        default="both",
        help="Run as producer, consumer, or both",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Producer sleep interval in seconds. Default: 0.05",
    )
    parser.add_argument(
        "--reset-topics",
        action="store_true",
        help=(
            "Delete and recreate the two assessment topics before running. "
            "Use this for an exact fresh summary."
        ),
    )

    args = parser.parse_args()

    create_topics(reset_existing=args.reset_topics)

    if args.mode == "producer":
        producer = build_producer()
        total_sent = run_producer(
            producer,
            EVENTS_DIR,
            delay_seconds=args.delay,
        )
        print(f"\nTotal messages sent: {total_sent}")

    elif args.mode == "consumer":
        consumer = build_consumer(TOPIC_EVENTS)
        summary = run_consumer(consumer)
        print("\nConsumer summary:")
        print(json.dumps(summary, indent=2))

    elif args.mode == "both":
        producer = build_producer()
        total_sent = run_producer(
            producer,
            EVENTS_DIR,
            delay_seconds=args.delay,
        )

        consumer = build_consumer(TOPIC_EVENTS)
        summary = run_consumer(consumer)

        print(f"\nTotal messages sent: {total_sent}")
        print("Consumer summary:")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
