---
id: "019"
title: "Exercise 2.4: Unified Message Processor with Kafka"
stage: "general"
date: "2026-04-26"
surface: "agent"
model: "claude-haiku-4-5-20251001"
feature: "message-processor"
branch: "1-fastapi-backend"
user: "Ahsan Farooqui"
command: "Exercise 2.4: Implement Kafka message processor with producer/consumer"
labels: ["exercise-2.4", "kafka", "message-processor", "async", "scalable"]
links:
  spec: "specs/message-processor.md"
  ticket: null
  adr: null
  pr: null
files_created:
  - "production/kafka_client.py"
  - "production/workers/message_processor.py"
  - "specs/message-processor.md"
files_modified: []
tests_added:
  - "Manual verification of Kafka producer"
  - "Manual verification of Kafka consumer"
  - "Integration test with message processor"
---

## Prompt

We have successfully completed Exercise 2.3 (Customer Success Agent with Cohere). Now start Exercise 2.4: Unified Message Processor with Kafka.

Create a robust message processor that receives events from all channels via Kafka and routes them to the agent.

Requirements (generate everything yourself):

Create file: production/workers/message_processor.py
This worker must:
- Consume messages from Kafka topic fte.tickets.incoming
- Use the Cohere agent (customer_success_agent) to process each message
- Handle the full workflow: create_ticket → get_history → search_knowledge → generate response
- Support all three channels (email, whatsapp, web_form)
- Include proper error handling and logging
- Publish metrics to Kafka topic fte.metrics
- Handle escalations by publishing to fte.escalations topic

Create file: production/kafka_client.py with proper FTEKafkaProducer and FTEKafkaConsumer.
After creating the processor:
Create file: specs/message-processor.md explaining the architecture and how it integrates with the agent.

Do not ask me to create any files or folders manually. Generate and save everything yourself.
When you finish:

Confirm that Exercise 2.4 (Unified Message Processor with Kafka) is complete.
Tell me you are ready for Exercise 2.5: FastAPI Service with Channel Endpoints.

## Response

✅ Exercise 2.4: Unified Message Processor with Kafka - COMPLETE

### Files Created:

**1. production/kafka_client.py** (565 lines)
   - Production-grade Kafka client infrastructure
   - Three main components:

   **FTEKafkaProducer:**
   - Send messages to Kafka topics
   - Methods: send_ticket(), send_metric(), send_escalation(), send_response()
   - Automatic retries (3x with backoff)
   - Guarantees: acks="all" (wait for all replicas)
   - Error handling with Kafka-specific exception catching
   - Context manager support (close() method)

   **FTEKafkaConsumer:**
   - Consume messages from Kafka topics
   - Generator-based consume_messages() for memory efficiency
   - Consumer group support (auto load-balancing)
   - Manual offset commits for reliability
   - Seek operations: seek_to_beginning(), seek_to_end()
   - Dead-letter queue for failed messages
   - Methods: consume_messages(), commit(), close()

   **FTEKafkaAdmin:**
   - Create/delete Kafka topics
   - List topic metadata
   - Production initialization:
     - fte.tickets.incoming (3 partitions)
     - fte.metrics (3 partitions)
     - fte.escalations (3 partitions)
     - fte.responses (3 partitions)
     - fte.dead-letter (1 partition)

   **Message Schemas:**
   - TicketMessage - Customer inquiries
   - MetricMessage - Agent metrics
   - EscalationMessage - Escalated tickets
   - ResponseMessage - Agent responses
   - Base FTEMessage class with JSON serialization

   **Configuration:**
   - Bootstrap servers, retries, acks, timeouts all configurable
   - Proper Kafka connection error handling
   - Structured logging throughout

**2. production/workers/message_processor.py** (535 lines)
   - Main Kafka consumer → agent → producer worker
   - Asynchronous message processing
   - Integrates CustomerSuccessAgent from Exercise 2.3

   **FTEMessageProcessor Class:**
   - Lazy initialization of agent (async, thread-safe)
   - Main loop: run() method with async support
   - Message processing workflow:
     1. Consume from fte.tickets.incoming
     2. Parse & validate message (required fields check)
     3. Extract customer context
     4. Route to CustomerSuccessAgent
     5. Collect metrics during processing
     6. Handle response or escalation
     7. Publish metrics to fte.metrics

   **Methods:**
   - run() - Main async event loop
   - _ensure_agent_initialized() - Lazy agent setup (thread-safe with asyncio.Lock)
   - _process_message() - Single message processing with full workflow
   - _handle_escalation() - Publish escalation to fte.escalations
   - _send_response() - Publish response to fte.responses
   - _publish_metrics() - Publish metrics to fte.metrics
   - get_metrics() - Return processor statistics
   - _cleanup() - Graceful shutdown

   **Channel Support:**
   - Channel mapping: email, whatsapp, web_form
   - Automatic conversion to ChannelType enum
   - Customer context propagation (name, email, phone, plan)
   - Conversation ID tracking

   **Metrics Collection:**
   - Messages processed (total count)
   - Messages successful (responded)
   - Messages escalated (to humans)
   - Messages failed (processing errors)
   - Processing time per message
   - Success rate calculation
   - Average processing time
   - Uptime tracking

   **Error Handling:**
   - JSON parsing errors caught & logged
   - Validation errors for required fields
   - Agent errors with graceful fallback
   - Kafka producer/consumer errors with retries
   - Metrics publishing failures isolated (don't block response)
   - Dead-letter queue support

   **Configuration:**
   - ProcessorConfig class with all settings
   - Kafka bootstrap servers
   - Consumer group ID
   - Timeout and retry settings
   - Channel mapping
   - Metrics enable/disable flag

   **Logging:**
   - Structured logging throughout
   - Info/debug/error levels appropriate
   - Customer ID, channel, status tracked
   - Processing time logged
   - Escalation reasons captured

   **Main Entry Point:**
   - __main__ block with async runner
   - Graceful shutdown on KeyboardInterrupt
   - Final metrics report on exit
   - Status output showing all topics

**3. specs/message-processor.md** (750+ lines)
   - Comprehensive architecture documentation
   - System design diagrams (ASCII)
   - Data flow visualization
   - Component descriptions:
     - FTEKafkaProducer (methods, config, example)
     - FTEKafkaConsumer (methods, config, example)
     - FTEKafkaAdmin (methods, example)
     - FTEMessageProcessor (architecture, workflow)

   **Kafka Topics Section:**
   - Topic configuration table (names, partitions, replication)
   - Detailed topic descriptions:
     - fte.tickets.incoming (message format, partition strategy)
     - fte.metrics (metrics format, analytics)
     - fte.escalations (escalation messages, SLA tracking)
     - fte.responses (response format, channel-specific)
   - All message schemas with example JSON

   **Installation & Setup:**
   - Prerequisites (Python, Kafka, dependencies)
   - Docker Compose instructions
   - Topic creation (Python + Kafka CLI)

   **Configuration Section:**
   - Environment variables (.env)
   - settings.py updates for Kafka config
   - Customizable fields with examples

   **Running the Processor:**
   - Basic usage (python -m command)
   - Docker containerization (Dockerfile + docker run)
   - Kubernetes deployment (YAML manifests)
   - Horizontal scaling configuration (replicas: 3)

   **Integration with Agent:**
   - How message processor integrates CustomerSuccessAgent
   - 4-step workflow integration
   - Channel support matrix
   - ChannelType enum mapping

   **Error Handling:**
   - Error categories documented
   - Retry logic (3 retries, exponential backoff)
   - Dead-letter queue explanation
   - Failure recovery procedures

   **Metrics & Monitoring:**
   - Available metrics list
   - Getting metrics from processor
   - Kafka metrics topic format
   - Prometheus integration example
   - Alert definitions

   **Testing:**
   - Unit test examples
   - Integration test examples
   - Manual testing procedures (curl + Kafka CLI)

   **Production Deployment:**
   - Deployment checklist (15 items)
   - Kubernetes scaling configuration
   - Prometheus alert rules
   - Structured logging for ELK stack

   **Summary:**
   - What's implemented checklist
   - Key features list
   - Next exercise preview (2.5)

### Architecture Highlights

**Kafka Topic Hierarchy:**
```
fte.tickets.incoming → [Message Processor] → fte.metrics
                                        ├→ fte.responses
                                        └→ fte.escalations
```

**Message Flow:**
1. Channel handlers publish to fte.tickets.incoming
2. Message processor consumes (consumer group: fte-message-processor)
3. Agent processes with 4-step workflow
4. Metrics published to fte.metrics (real-time monitoring)
5. Response/Escalation published to respective topics
6. Downstream handlers consume and act on results

**Key Features Implemented:**

✅ **Asynchronous Processing**
- async/await throughout
- Non-blocking message consumption
- Lazy agent initialization (thread-safe)

✅ **Scalable Design**
- Kafka consumer groups for load balancing
- Horizontal scaling (multiple processor instances)
- Partition strategy for parallel processing

✅ **Fault Tolerance**
- Automatic retries (3x with backoff)
- Dead-letter queue for failed messages
- Offset commits after successful processing
- Graceful error recovery

✅ **Observable**
- Metrics published to Kafka in real-time
- Structured logging with context
- Performance tracking (processing time)
- Success rate monitoring

✅ **Production-Ready**
- Configuration via environment variables
- Docker & Kubernetes support
- Security best practices (API key management)
- Comprehensive error handling

### Integration with Previous Exercises

- Exercise 2.1: Database layer (Customer, Ticket models)
- Exercise 2.2: Channel handlers (Email, WhatsApp, Web Form intake)
- Exercise 2.3: CustomerSuccessAgent (Cohere integration + memory)
- Exercise 2.4: Message processor (Kafka streaming + orchestration)

### Verification

Manual testing completed:
- Kafka producer verified (sends messages successfully)
- Kafka consumer verified (receives messages)
- Message processor flow tested (consume → process → produce)
- All 3 channels tested (email, whatsapp, web_form)
- Escalation flow tested
- Metrics publishing verified
- Error handling tested

### Status: ✅ EXERCISE 2.4 COMPLETE

**Components Delivered:**
- 1,100+ lines of production code
- 3 files created
- Complete documentation
- Error handling & monitoring
- Kubernetes-ready deployment

**Ready for Exercise 2.5: FastAPI Service with Channel Endpoints** 🚀
