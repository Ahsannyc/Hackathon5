"""
Kafka Client - Production-grade FTE Kafka Producer and Consumer

Provides unified Kafka client configuration for the CloudFlow FTE system:
- FTEKafkaProducer: Sends messages to Kafka topics
- FTEKafkaConsumer: Consumes messages from Kafka topics
- FTEKafkaAdmin: Manages topics and cluster operations

Topics:
- fte.tickets.incoming: Customer inquiries from all channels
- fte.metrics: Agent metrics and performance data
- fte.escalations: Escalated tickets requiring human attention
- fte.responses: Agent responses ready to send to customers
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    KAFKA_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"Kafka not available: {e}. Running in degraded mode.")
    KAFKA_AVAILABLE = False
    AIOKafkaProducer = None
    AIOKafkaConsumer = None


# ============================================================================
# ENUMS
# ============================================================================

class FTETopics(str, Enum):
    """Kafka topics for the FTE system."""
    TICKETS_INCOMING = "fte.tickets.incoming"
    METRICS = "fte.metrics"
    ESCALATIONS = "fte.escalations"
    RESPONSES = "fte.responses"
    DEAD_LETTER = "fte.dead-letter"


# ============================================================================
# MESSAGE SCHEMAS
# ============================================================================

class FTEMessage:
    """Base message class for FTE Kafka topics."""

    def __init__(self, **kwargs):
        """Initialize message with provided fields."""
        self.timestamp = datetime.utcnow().isoformat()
        self.__dict__.update(kwargs)

    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps(self.__dict__, default=str)

    @classmethod
    def from_json(cls, json_str: str):
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.__dict__.copy()


class TicketMessage(FTEMessage):
    """Customer ticket message."""

    def __init__(
        self,
        customer_id: str,
        customer_email: str,
        customer_name: str,
        channel: str,
        subject: str,
        message: str,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            channel=channel,
            subject=subject,
            message=message,
            priority=priority,
            metadata=metadata or {},
            **kwargs
        )


class MetricMessage(FTEMessage):
    """Metrics message from agent processing."""

    def __init__(
        self,
        conversation_id: str,
        customer_id: str,
        channel: str,
        processing_time_ms: int,
        tools_used: List[str],
        status: str,
        escalated: bool,
        iterations: int,
        **kwargs
    ):
        super().__init__(
            conversation_id=conversation_id,
            customer_id=customer_id,
            channel=channel,
            processing_time_ms=processing_time_ms,
            tools_used=tools_used,
            status=status,
            escalated=escalated,
            iterations=iterations,
            **kwargs
        )


class EscalationMessage(FTEMessage):
    """Escalation message to human specialists."""

    def __init__(
        self,
        ticket_id: str,
        customer_id: str,
        customer_email: str,
        channel: str,
        reason: str,
        priority: str = "high",
        agent_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            ticket_id=ticket_id,
            customer_id=customer_id,
            customer_email=customer_email,
            channel=channel,
            reason=reason,
            priority=priority,
            agent_context=agent_context or {},
            **kwargs
        )


class ResponseMessage(FTEMessage):
    """Agent response ready to send to customer."""

    def __init__(
        self,
        ticket_id: str,
        customer_id: str,
        customer_email: str,
        channel: str,
        response_text: str,
        conversation_id: str,
        tools_used: List[str],
        **kwargs
    ):
        super().__init__(
            ticket_id=ticket_id,
            customer_id=customer_id,
            customer_email=customer_email,
            channel=channel,
            response_text=response_text,
            conversation_id=conversation_id,
            tools_used=tools_used,
            **kwargs
        )


# ============================================================================
# KAFKA PRODUCER
# ============================================================================

class FTEKafkaProducer:
    """
    Async Kafka producer for FTE system (aiokafka).

    Sends messages to Kafka topics with proper serialization and error handling.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092", **kwargs):
        """Initialize Kafka producer (not started until start() is called)."""
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

        producer_config = {
            "bootstrap_servers": bootstrap_servers.split(","),
            "value_serializer": lambda v: v.encode("utf-8") if isinstance(v, str) else v,
            "acks": "all",
            "retries": 3,
        }
        producer_config.update(kwargs)
        self.config = producer_config

        logger.info(f"FTEKafkaProducer created with servers: {bootstrap_servers}")

    async def start(self) -> None:
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(**self.config)
            await self.producer.start()
            logger.info("FTEKafkaProducer started")
        except Exception as e:
            logger.error(f"Failed to start KafkaProducer: {e}")
            raise

    async def send_ticket(self, ticket: TicketMessage) -> Optional[str]:
        """Send customer ticket to incoming topic."""
        if not self.producer:
            logger.error("Producer not started")
            return None

        try:
            msg_json = ticket.to_json()
            partition_and_offset = await self.producer.send_and_wait(
                FTETopics.TICKETS_INCOMING.value,
                value=msg_json.encode("utf-8"),
                key=ticket.customer_id.encode("utf-8"),
            )
            logger.info(f"Ticket sent: customer={ticket.customer_id}")
            return f"{partition_and_offset.partition}-{partition_and_offset.offset}"
        except Exception as e:
            logger.error(f"Error sending ticket: {e}")
            return None

    async def send_metric(self, metric: MetricMessage) -> bool:
        """Send metrics to metrics topic."""
        if not self.producer:
            return False

        try:
            msg_json = metric.to_json()
            await self.producer.send_and_wait(
                FTETopics.METRICS.value,
                value=msg_json.encode("utf-8"),
                key=metric.customer_id.encode("utf-8"),
            )
            logger.debug(f"Metric sent: customer={metric.customer_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending metric: {e}")
            return False

    async def send_escalation(self, escalation: EscalationMessage) -> bool:
        """Send escalation to escalations topic."""
        if not self.producer:
            return False

        try:
            msg_json = escalation.to_json()
            await self.producer.send_and_wait(
                FTETopics.ESCALATIONS.value,
                value=msg_json.encode("utf-8"),
                key=escalation.customer_id.encode("utf-8"),
            )
            logger.info(f"Escalation sent: ticket={escalation.ticket_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending escalation: {e}")
            return False

    async def send_response(self, response: ResponseMessage) -> bool:
        """Send agent response to responses topic."""
        if not self.producer:
            return False

        try:
            msg_json = response.to_json()
            await self.producer.send_and_wait(
                FTETopics.RESPONSES.value,
                value=msg_json.encode("utf-8"),
                key=response.customer_id.encode("utf-8"),
            )
            logger.debug(f"Response sent: ticket={response.ticket_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            return False

    async def close(self) -> None:
        """Close producer connection."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("FTEKafkaProducer stopped")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")


# ============================================================================
# KAFKA CONSUMER
# ============================================================================

class FTEKafkaConsumer:
    """
    Kafka consumer for FTE system.

    Consumes messages from Kafka topics with proper deserialization and error handling.
    """

    def __init__(
        self,
        topic: str,
        group_id: str,
        bootstrap_servers: str = "localhost:9092",
        auto_offset_reset: str = "earliest",
        **kwargs
    ):
        """
        Initialize Kafka consumer.

        Args:
            topic: Topic to consume from
            group_id: Consumer group ID
            bootstrap_servers: Kafka bootstrap servers (comma-separated)
            auto_offset_reset: Where to start reading (earliest/latest)
            **kwargs: Additional KafkaConsumer arguments
        """
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers

        consumer_config = {
            "bootstrap_servers": bootstrap_servers.split(","),
            "group_id": group_id,
            "auto_offset_reset": auto_offset_reset,
            "value_deserializer": lambda m: m.decode("utf-8") if m else None,
            "enable_auto_commit": False,  # Manual commit for reliability
            "session_timeout_ms": 30000,
            "max_poll_records": 100,
        }
        consumer_config.update(kwargs)

        try:
            self.consumer = KafkaConsumer(topic, **consumer_config)
            logger.info(f"FTEKafkaConsumer initialized: topic={topic}, group={group_id}")
        except Exception as e:
            logger.error(f"Failed to initialize KafkaConsumer: {e}")
            raise

    def consume_messages(self, timeout_ms: int = 1000, max_messages: Optional[int] = None):
        """
        Consume messages from topic.

        Args:
            timeout_ms: Poll timeout in milliseconds
            max_messages: Maximum messages to consume (None = unlimited)

        Yields:
            (message_key, message_value) tuples
        """
        message_count = 0

        try:
            while True:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=timeout_ms, max_records=max_messages)

                if not messages:
                    logger.debug("No messages received (poll timeout)")
                    continue

                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            key = record.key.decode("utf-8") if record.key else None
                            value = record.value

                            yield key, value

                            # Commit after successful processing
                            self.consumer.commit()
                            message_count += 1

                        except Exception as e:
                            logger.error(
                                f"Error processing message from {topic_partition}: {e}"
                            )
                            # Send to dead-letter topic
                            self._send_to_dead_letter(record)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise

    def seek_to_beginning(self) -> None:
        """Seek to beginning of topic."""
        try:
            self.consumer.seek_to_beginning()
            logger.info(f"Seeking to beginning of {self.topic}")
        except Exception as e:
            logger.error(f"Error seeking to beginning: {e}")

    def seek_to_end(self) -> None:
        """Seek to end of topic."""
        try:
            self.consumer.seek_to_end()
            logger.info(f"Seeking to end of {self.topic}")
        except Exception as e:
            logger.error(f"Error seeking to end: {e}")

    def get_position(self) -> Dict[TopicPartition, int]:
        """Get current consumer position."""
        try:
            return self.consumer.position(TopicPartition(self.topic, 0))
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return {}

    def commit(self) -> None:
        """Manually commit current offset."""
        try:
            self.consumer.commit()
            logger.debug("Consumer offset committed")
        except Exception as e:
            logger.error(f"Error committing offset: {e}")

    def close(self) -> None:
        """Close consumer connection."""
        try:
            self.consumer.close()
            logger.info("FTEKafkaConsumer closed")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")

    def _send_to_dead_letter(self, record) -> None:
        """Send failed message to dead-letter topic."""
        try:
            producer = FTEKafkaProducer(self.bootstrap_servers)
            producer.producer.send(
                FTETopics.DEAD_LETTER.value,
                value=record.value,
                key=record.key,
            )
            logger.warning(f"Message sent to dead-letter queue: {record.offset}")
        except Exception as e:
            logger.error(f"Failed to send to dead-letter queue: {e}")


# ============================================================================
# KAFKA ADMIN
# ============================================================================

class FTEKafkaAdmin:
    """
    Kafka admin operations for FTE system.

    Manages topics, cluster operations, and metadata.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka admin client.

        Args:
            bootstrap_servers: Kafka bootstrap servers (comma-separated)
        """
        self.bootstrap_servers = bootstrap_servers

        try:
            self.admin = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers.split(","),
                request_timeout_ms=30000,
            )
            logger.info(f"FTEKafkaAdmin initialized with servers: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize KafkaAdminClient: {e}")
            raise

    def create_topics(self, num_partitions: int = 3, replication_factor: int = 1) -> bool:
        """
        Create FTE topics.

        Args:
            num_partitions: Number of partitions per topic
            replication_factor: Replication factor

        Returns:
            True if successful
        """
        topics = [
            NewTopic(
                name=FTETopics.TICKETS_INCOMING.value,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
            ),
            NewTopic(
                name=FTETopics.METRICS.value,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
            ),
            NewTopic(
                name=FTETopics.ESCALATIONS.value,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
            ),
            NewTopic(
                name=FTETopics.RESPONSES.value,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
            ),
            NewTopic(
                name=FTETopics.DEAD_LETTER.value,
                num_partitions=1,
                replication_factor=replication_factor,
            ),
        ]

        try:
            fs = self.admin.create_topics(topics, validate_only=False)

            for topic, f in fs.items():
                try:
                    f.result(timeout=10)
                    logger.info(f"Topic created: {topic}")
                except TopicAlreadyExistsError:
                    logger.debug(f"Topic already exists: {topic}")
                except Exception as e:
                    logger.error(f"Failed to create topic {topic}: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error creating topics: {e}")
            return False

    def delete_topics(self, topics: Optional[List[str]] = None) -> bool:
        """
        Delete topics.

        Args:
            topics: List of topic names (defaults to all FTE topics)

        Returns:
            True if successful
        """
        if topics is None:
            topics = [t.value for t in FTETopics]

        try:
            fs = self.admin.delete_topics(topics)

            for topic, f in fs.items():
                try:
                    f.result(timeout=10)
                    logger.info(f"Topic deleted: {topic}")
                except Exception as e:
                    logger.error(f"Failed to delete topic {topic}: {e}")

            return True

        except Exception as e:
            logger.error(f"Error deleting topics: {e}")
            return False

    def list_topics(self) -> Dict[str, Any]:
        """Get all topics metadata."""
        try:
            metadata = self.admin.list_topics()
            logger.debug(f"Topics: {list(metadata.keys())}")
            return metadata
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            return {}

    def close(self) -> None:
        """Close admin connection."""
        try:
            self.admin.close()
            logger.info("FTEKafkaAdmin closed")
        except Exception as e:
            logger.error(f"Error closing admin: {e}")


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_producer(bootstrap_servers: str = "localhost:9092") -> FTEKafkaProducer:
    """Create FTE Kafka producer."""
    return FTEKafkaProducer(bootstrap_servers)


def create_consumer(
    topic: str,
    group_id: str,
    bootstrap_servers: str = "localhost:9092",
) -> FTEKafkaConsumer:
    """Create FTE Kafka consumer."""
    return FTEKafkaConsumer(topic, group_id, bootstrap_servers)


def create_admin(bootstrap_servers: str = "localhost:9092") -> FTEKafkaAdmin:
    """Create FTE Kafka admin client."""
    return FTEKafkaAdmin(bootstrap_servers)
