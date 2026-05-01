"""
FTE Message Processor Worker - Kafka Consumer → Agent → Kafka Producer

This worker:
1. Consumes customer tickets from fte.tickets.incoming
2. Routes to CustomerSuccessAgent for processing
3. Publishes metrics to fte.metrics
4. Publishes escalations to fte.escalations
5. Publishes responses to fte.responses
6. Handles all 3 channels (email, whatsapp, web_form)
7. Includes retry logic and error handling

Architecture:
┌─────────────────────┐
│  fte.tickets.incoming │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │   Consumer   │
    └──────┬───────┘
           │
           ▼
    ┌────────────────────────┐
    │ CustomerSuccessAgent   │
    │ (Cohere Backend)       │
    └──────┬───────────────┬──┘
           │               │
           ▼               ▼
    ┌──────────────┐  ┌─────────────┐
    │ fte.responses│  │fte.escalations│
    └──────────────┘  └─────────────┘
           │               │
           └───┬───────────┘
               ▼
        ┌──────────────┐
        │ fte.metrics  │
        └──────────────┘
"""

import asyncio
import logging
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from production.kafka_client import (
    FTEKafkaConsumer,
    FTEKafkaProducer,
    FTETopics,
    TicketMessage,
    MetricMessage,
    EscalationMessage,
    ResponseMessage,
)
from production.agent.customer_success_agent import create_customer_success_agent
from production.database.schema import ChannelType

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

class ProcessorConfig:
    """Message processor configuration."""

    KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    CONSUMER_GROUP_ID = "fte-message-processor"
    CONSUMER_TIMEOUT_MS = 1000
    MAX_RETRIES = 3
    RETRY_BACKOFF_MS = 1000

    # Channel mapping
    CHANNEL_MAPPING = {
        "email": ChannelType.EMAIL,
        "whatsapp": ChannelType.WHATSAPP,
        "web_form": ChannelType.WEB_FORM,
    }

    # Metrics collection
    METRICS_ENABLED = True


# ============================================================================
# MESSAGE PROCESSOR
# ============================================================================

class FTEMessageProcessor:
    """
    Kafka-based message processor for Customer Success FTE.

    Workflow:
    1. Consume ticket from fte.tickets.incoming
    2. Parse and validate message
    3. Route to CustomerSuccessAgent
    4. Collect metrics during processing
    5. Publish response or escalation
    6. Publish metrics to fte.metrics
    """

    def __init__(
        self,
        bootstrap_servers: str = ProcessorConfig.KAFKA_BOOTSTRAP_SERVERS,
        enable_debug: bool = False,
    ):
        """
        Initialize message processor.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            enable_debug: Enable debug logging
        """
        self.bootstrap_servers = bootstrap_servers
        self.enable_debug = enable_debug

        # Initialize Kafka clients
        self.consumer = FTEKafkaConsumer(
            topic=FTETopics.TICKETS_INCOMING.value,
            group_id=ProcessorConfig.CONSUMER_GROUP_ID,
            bootstrap_servers=bootstrap_servers,
        )

        self.producer = FTEKafkaProducer(bootstrap_servers)

        # Initialize agent (lazy loading)
        self.agent = None
        self.agent_lock = asyncio.Lock()

        # Metrics
        self.metrics = {
            "messages_processed": 0,
            "messages_successful": 0,
            "messages_escalated": 0,
            "messages_failed": 0,
            "total_processing_time_ms": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"FTEMessageProcessor initialized: bootstrap_servers={bootstrap_servers}"
        )

    async def _ensure_agent_initialized(self) -> None:
        """Lazy initialize agent (thread-safe)."""
        if self.agent is None:
            async with self.agent_lock:
                if self.agent is None:
                    logger.info("Initializing CustomerSuccessAgent...")
                    self.agent = await create_customer_success_agent(
                        enable_debug=self.enable_debug
                    )
                    logger.info("CustomerSuccessAgent initialized successfully")

    async def run(self) -> None:
        """
        Main processor loop.

        Consumes messages indefinitely and processes them.
        """
        logger.info("Starting FTE Message Processor...")

        try:
            for key, message_json in self.consumer.consume_messages(
                timeout_ms=ProcessorConfig.CONSUMER_TIMEOUT_MS,
            ):
                try:
                    logger.debug(f"Received message for customer: {key}")

                    # Process message
                    await self._process_message(key, message_json)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    self.metrics["messages_failed"] += 1

        except KeyboardInterrupt:
            logger.info("Processor interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error in processor: {e}", exc_info=True)
        finally:
            self._cleanup()

    async def _process_message(self, customer_id: str, message_json: str) -> None:
        """
        Process a single message.

        Args:
            customer_id: Customer identifier
            message_json: Message JSON string
        """
        start_time = time.time()

        try:
            # Parse message
            message_data = json.loads(message_json)
            logger.info(
                f"Processing message: customer={customer_id}, "
                f"channel={message_data.get('channel')}"
            )

            # Validate required fields
            required_fields = ["customer_id", "channel", "subject", "message"]
            for field in required_fields:
                if field not in message_data:
                    raise ValueError(f"Missing required field: {field}")

            # Extract fields
            channel_str = message_data.get("channel", "email").lower()
            channel = ProcessorConfig.CHANNEL_MAPPING.get(
                channel_str, ChannelType.EMAIL
            )

            customer_name = message_data.get("customer_name", "Valued Customer")
            customer_email = message_data.get("customer_email", "")
            subject = message_data.get("subject", "")
            customer_message = message_data.get("message", "")
            priority = message_data.get("priority", "medium")
            metadata = message_data.get("metadata", {})

            # Initialize agent if needed
            await self._ensure_agent_initialized()

            # Process message with agent
            logger.debug(
                f"Sending to agent: customer={customer_id}, "
                f"message={customer_message[:50]}..."
            )

            agent_result = await self.agent.process_message(
                customer_message=customer_message,
                customer_id=customer_id,
                channel=channel,
                conversation_id=metadata.get("conversation_id"),
                customer_context={
                    "name": customer_name,
                    "email": customer_email,
                    "phone": metadata.get("phone"),
                    "plan": metadata.get("plan"),
                },
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Handle based on status
            if agent_result.get("status") == "escalated":
                await self._handle_escalation(
                    ticket_id=metadata.get("ticket_id", f"T-{customer_id}"),
                    customer_id=customer_id,
                    customer_email=customer_email,
                    channel=channel_str,
                    subject=subject,
                    reason=agent_result.get("escalation_reason", "Complex issue"),
                    agent_context=agent_result,
                )
                self.metrics["messages_escalated"] += 1

            else:
                # Send response
                await self._send_response(
                    ticket_id=metadata.get("ticket_id", f"T-{customer_id}"),
                    customer_id=customer_id,
                    customer_email=customer_email,
                    channel=channel_str,
                    response_text=agent_result.get("response", ""),
                    conversation_id=agent_result.get("conversation_id", ""),
                    tools_used=agent_result.get("tools_used", []),
                )
                self.metrics["messages_successful"] += 1

            # Publish metrics
            if ProcessorConfig.METRICS_ENABLED:
                await self._publish_metrics(
                    customer_id=customer_id,
                    channel=channel_str,
                    processing_time_ms=processing_time_ms,
                    tools_used=agent_result.get("tools_used", []),
                    status=agent_result.get("status", "success"),
                    escalated=agent_result.get("escalated", False),
                    iterations=agent_result.get("iterations", 1),
                    conversation_id=agent_result.get("conversation_id", ""),
                )

            self.metrics["messages_processed"] += 1
            self.metrics["total_processing_time_ms"] += processing_time_ms

            logger.info(
                f"Message processed successfully: "
                f"customer={customer_id}, "
                f"status={agent_result.get('status')}, "
                f"time_ms={processing_time_ms}"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            self.metrics["messages_failed"] += 1
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            self.metrics["messages_failed"] += 1
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            self.metrics["messages_failed"] += 1

    async def _handle_escalation(
        self,
        ticket_id: str,
        customer_id: str,
        customer_email: str,
        channel: str,
        subject: str,
        reason: str,
        agent_context: Dict[str, Any],
    ) -> None:
        """
        Handle message escalation.

        Args:
            ticket_id: Ticket identifier
            customer_id: Customer identifier
            customer_email: Customer email
            channel: Communication channel
            subject: Issue subject
            reason: Escalation reason
            agent_context: Agent processing context
        """
        escalation = EscalationMessage(
            ticket_id=ticket_id,
            customer_id=customer_id,
            customer_email=customer_email,
            channel=channel,
            reason=reason,
            priority="high",
            agent_context=agent_context,
        )

        if self.producer.send_escalation(escalation):
            logger.info(f"Escalation published: ticket={ticket_id}, reason={reason}")
        else:
            logger.error(f"Failed to publish escalation: ticket={ticket_id}")

    async def _send_response(
        self,
        ticket_id: str,
        customer_id: str,
        customer_email: str,
        channel: str,
        response_text: str,
        conversation_id: str,
        tools_used: list,
    ) -> None:
        """
        Send agent response.

        Args:
            ticket_id: Ticket identifier
            customer_id: Customer identifier
            customer_email: Customer email
            channel: Communication channel
            response_text: Response text
            conversation_id: Conversation identifier
            tools_used: Tools used by agent
        """
        response = ResponseMessage(
            ticket_id=ticket_id,
            customer_id=customer_id,
            customer_email=customer_email,
            channel=channel,
            response_text=response_text,
            conversation_id=conversation_id,
            tools_used=tools_used,
        )

        if self.producer.send_response(response):
            logger.debug(f"Response published: ticket={ticket_id}")
        else:
            logger.error(f"Failed to publish response: ticket={ticket_id}")

    async def _publish_metrics(
        self,
        customer_id: str,
        channel: str,
        processing_time_ms: int,
        tools_used: list,
        status: str,
        escalated: bool,
        iterations: int,
        conversation_id: str,
    ) -> None:
        """
        Publish processing metrics.

        Args:
            customer_id: Customer identifier
            channel: Communication channel
            processing_time_ms: Processing time in milliseconds
            tools_used: Tools used by agent
            status: Processing status
            escalated: Whether escalated
            iterations: Number of iterations
            conversation_id: Conversation identifier
        """
        metric = MetricMessage(
            conversation_id=conversation_id,
            customer_id=customer_id,
            channel=channel,
            processing_time_ms=processing_time_ms,
            tools_used=tools_used,
            status=status,
            escalated=escalated,
            iterations=iterations,
        )

        if self.producer.send_metric(metric):
            logger.debug(f"Metrics published: customer={customer_id}")
        else:
            logger.error(f"Failed to publish metrics: customer={customer_id}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current processor metrics."""
        uptime_seconds = (
            datetime.utcnow() - datetime.fromisoformat(self.metrics["started_at"])
        ).total_seconds()

        avg_processing_time = (
            self.metrics["total_processing_time_ms"] / self.metrics["messages_processed"]
            if self.metrics["messages_processed"] > 0
            else 0
        )

        return {
            **self.metrics,
            "uptime_seconds": int(uptime_seconds),
            "average_processing_time_ms": avg_processing_time,
            "success_rate": (
                self.metrics["messages_successful"]
                / self.metrics["messages_processed"]
                * 100
                if self.metrics["messages_processed"] > 0
                else 0
            ),
        }

    def _cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.consumer.close()
            self.producer.close()
            logger.info("Message processor cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for message processor."""
    import logging.config

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 80)
    logger.info("FTE Message Processor - Kafka Consumer → Agent → Kafka Producer")
    logger.info("=" * 80)

    # Create and run processor
    processor = FTEMessageProcessor(enable_debug=False)

    logger.info("Starting message processor loop...")
    logger.info(f"Listening to topic: {FTETopics.TICKETS_INCOMING.value}")
    logger.info(f"Publishing to topics: {FTETopics.RESPONSES.value}, {FTETopics.ESCALATIONS.value}, {FTETopics.METRICS.value}")
    logger.info("=" * 80)

    try:
        await processor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Print final metrics
        metrics = processor.get_metrics()
        logger.info("=" * 80)
        logger.info("Final Metrics:")
        logger.info(f"  Messages Processed: {metrics['messages_processed']}")
        logger.info(f"  Successful: {metrics['messages_successful']}")
        logger.info(f"  Escalated: {metrics['messages_escalated']}")
        logger.info(f"  Failed: {metrics['messages_failed']}")
        logger.info(f"  Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"  Average Processing Time: {metrics['average_processing_time_ms']:.0f}ms")
        logger.info(f"  Uptime: {metrics['uptime_seconds']}s")
        logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
