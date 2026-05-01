# Tool Migration Analysis: MCP → OpenAI Agents SDK

**Purpose:** Detailed analysis and plan for converting MCP tools to production tools  
**Date:** 2026-04-03  
**Exercise:** Step 3 of Transition Phase  
**Status:** ✅ Ready for Implementation

---

## Executive Summary

We have **5 working MCP tools** from `mcp_server.py` (Incubation Exercise 1.4) that need to be transformed into **production-grade @function_tool functions** for the OpenAI Agents SDK.

### Transformation Plan at a Glance

```
5 MCP Tools (Incubation)
    ↓
Add Pydantic input validation
Add comprehensive error handling
Replace in-memory storage with database queries
Add structured logging
Add metrics collection
    ↓
5 OpenAI SDK Tools (Production)
```

---

## Current State: 5 MCP Tools

### Tool #1: search_knowledge_base

**Current Implementation (Incubation):**
```python
def search_knowledge_base(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search KB - simple keyword matching."""
    if not query or not query.strip():
        return {"success": False, "error": "Query cannot be empty", "results": []}
    
    intent, confidence = prototype.detect_intent(query)
    kb_match = prototype.search_knowledge_base(query, intent)
    
    # Search in-memory knowledge_base dict
    results = []
    # ... string matching logic ...
    
    return {
        "success": True,
        "detected_intent": intent,
        "results": results[:max_results]
    }
```

**Challenges for Production:**
- ❌ String matching is inefficient (O(n) search)
- ❌ No semantic understanding (exact keyword match only)
- ❌ No structured logging
- ❌ No error handling
- ❌ No input validation
- ❌ In-memory storage (not persistent)

### Tool #2: create_ticket

**Current Implementation (Incubation):**
```python
def create_ticket(customer_id: str, issue: str, priority: str, channel: str) -> Dict[str, Any]:
    """Create ticket in in-memory dict."""
    # Validate inputs
    if customer_id not in prototype.memory.customers:
        return {"success": False, "error": "Customer not found"}
    
    # Create in-memory record
    ticket_id = prototype.generate_ticket_id()
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now().isoformat()
    }
    tickets_db[ticket_id] = ticket
    
    return {"success": True, "ticket_id": ticket_id, ...}
```

**Challenges for Production:**
- ❌ No database persistence (lost on restart)
- ❌ No transaction support (no ACID guarantees)
- ❌ No audit trail (can't see who created what when)
- ❌ No event publishing (downstream systems don't know)
- ❌ No rate limiting (no protection against spam)

### Tool #3: get_customer_history

**Current Implementation (Incubation):**
```python
def get_customer_history(customer_id: str) -> Dict[str, Any]:
    """Get customer state from in-memory storage."""
    customer_state = prototype.memory.get_customer_state(customer_id)
    
    if not customer_state:
        return {"success": False, "error": "Customer not found"}
    
    # Extract from in-memory structure
    conversation_history = []
    for msg in customer_state.conversation_history[-10:]:
        conversation_history.append({...})
    
    return {"success": True, "customer": {...}, "history": conversation_history}
```

**Challenges for Production:**
- ❌ No SQL queries (inefficient for large datasets)
- ❌ No pagination (memory overhead with thousands of messages)
- ❌ No filtering/sorting (limited query flexibility)
- ❌ No caching (repeated queries = repeated computation)
- ❌ No aggregation (can't compute statistics efficiently)

### Tool #4: escalate_to_human

**Current Implementation (Incubation):**
```python
def escalate_to_human(ticket_id: str, reason: str) -> Dict[str, Any]:
    """Escalate to in-memory escalations dict."""
    if ticket_id not in tickets_db:
        return {"success": False, "error": "Ticket not found"}
    
    # Detect escalation category
    escalation_needed, category = prototype.detect_escalation_triggers(...)
    
    # Create escalation record
    escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d')}-{escalation_counter:04d}"
    escalations_db[escalation_id] = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "assigned_team": team_for_category(category)
    }
    
    return {"success": True, "escalation_id": escalation_id, ...}
```

**Challenges for Production:**
- ❌ No event publishing (no queue for notification workers)
- ❌ No SLA tracking (escalations not monitored for timeliness)
- ❌ No team availability checking (could assign to offline team)
- ❌ No escalation routing rules (single logic, no flexibility)
- ❌ No callback mechanism (AI doesn't know escalation result)

### Tool #5: send_response

**Current Implementation (Incubation):**
```python
def send_response(ticket_id: str, message: str, channel: str) -> Dict[str, Any]:
    """Send response - just formats and stores."""
    if ticket_id not in tickets_db:
        return {"success": False, "error": "Ticket not found"}
    
    # Format for channel
    if channel == "email":
        formatted = f"Dear [Name],\n\n{message}\n\nBest regards"
    elif channel == "whatsapp":
        formatted = message  # Keep short
    else:
        formatted = message
    
    # Store in ticket
    ticket = tickets_db[ticket_id]
    ticket["responses"].append({
        "message": formatted,
        "timestamp": datetime.now().isoformat(),
        "channel": channel
    })
    
    return {"success": True, "delivery_status": "sent", ...}
```

**Challenges for Production:**
- ❌ No actual channel delivery (doesn't contact Gmail/WhatsApp/Web)
- ❌ No template engine (formatting is hardcoded)
- ❌ No rate limiting (could spam customer)
- ❌ No retry logic (failed sends = lost messages)
- ❌ No delivery tracking (no confirmation of receipt)

---

## Production Requirements Analysis

### By Tool: What Needs to Change

#### search_knowledge_base

| Requirement | Current | Production |
|---|---|---|
| **Search Type** | String matching | Vector similarity (embeddings) |
| **Performance** | O(n) scan | O(1) vector search with pgvector |
| **Relevance** | Exact match | Semantic similarity (0.0-1.0) |
| **Data Source** | In-memory dict | PostgreSQL table + pgvector |
| **Fallback** | Empty list | "No match found, escalating..." |
| **Logging** | Print statements | Structured JSON logs + Prometheus |
| **Error Handling** | Crashes | Try/catch with graceful messages |
| **Input Validation** | Loose | Pydantic BaseModel |
| **Response Time** | <1s | <2s (including embedding generation) |

**Implementation Strategy:**
1. Create `KnowledgeSearchInput` Pydantic model
2. Add async database connection pool
3. Implement embedding generation (via OpenAI API)
4. Create SQL query with pgvector distance operator
5. Add structured logging at each step
6. Add try/catch with fallback messages
7. Add prometheus metrics for success/failure/latency

#### create_ticket

| Requirement | Current | Production |
|---|---|---|
| **Storage** | In-memory dict | PostgreSQL INSERT |
| **Persistence** | Lost on restart | ACID guaranteed |
| **Validation** | Basic checks | Pydantic + DB constraints |
| **ID Generation** | Counter | Database sequence |
| **Event Publishing** | None | Kafka event to escalation topic |
| **Auditability** | None | created_by, created_at, updated_at |
| **Concurrency** | Single-threaded | Async + connection pool |
| **Rate Limiting** | None | Per-customer rate limit check |
| **Idempotency** | Not guaranteed | Unique ticket_id per customer |
| **Error Handling** | Crashes | Graceful with message |

**Implementation Strategy:**
1. Create `CreateTicketInput` Pydantic model with all validations
2. Add database transaction (BEGIN ... COMMIT)
3. Verify customer exists (foreign key constraint)
4. Generate ticket_id via database sequence
5. Insert into tickets table with all metadata
6. Publish Kafka event (topic: "ticket.created")
7. Log creation with customer context
8. Return ticket_id + SLA estimate

#### get_customer_history

| Requirement | Current | Production |
|---|---|---|
| **Query** | In-memory lookup | SQL JOINs across tables |
| **Pagination** | Hardcoded limit | Configurable limit + offset |
| **Filtering** | None | By channel, date range, status |
| **Aggregation** | Manual counting | SQL aggregates (COUNT, AVG) |
| **Sorting** | None | By timestamp, relevance |
| **Caching** | None | Redis cache with TTL |
| **Performance** | O(n) memory scan | O(log n) index lookup |
| **Completeness** | Last 10 messages | All messages + aggregates |
| **Data Freshness** | Instant | Cache → DB (configurable) |
| **Error Handling** | Crashes if missing | Graceful with empty history |

**Implementation Strategy:**
1. Create `GetCustomerHistoryInput` model with filter options
2. Check Redis cache first (key: f"customer:{customer_id}:history")
3. If cache miss, query database:
   - SELECT from messages WHERE customer_id = $1 ORDER BY created_at DESC LIMIT $2
   - SELECT COUNT(*), AVG(sentiment) FROM messages WHERE customer_id = $1
   - SELECT DISTINCT channels FROM messages WHERE customer_id = $1
4. Format response with all aggregates
5. Cache result in Redis with 5-minute TTL
6. Log query with duration + cache hit/miss
7. Return with metadata

#### escalate_to_human

| Requirement | Current | Production |
|---|---|---|
| **Storage** | In-memory dict | PostgreSQL + event queue |
| **Team Assignment** | Hard-coded map | Rules engine + availability check |
| **SLA Tracking** | Not tracked | Database column + alert rule |
| **Routing** | Static | Dynamic based on load + skill |
| **Notification** | None | Kafka event to team queue |
| **Acknowledgment** | None | Callback mechanism |
| **Urgency** | Not tracked | Priority matrix |
| **Handoff Quality** | Minimal context | Full conversation + KB results |
| **Metrics** | Not collected | Time to acknowledgment, resolution |
| **Idempotency** | Not guaranteed | Prevent duplicate escalations |

**Implementation Strategy:**
1. Create `EscalateToHumanInput` model with reason + context
2. Classify reason using LLM or rules engine
3. Check team availability (from team_status table)
4. Determine SLA based on priority + category
5. Create escalation record in database
6. Publish Kafka event: {escalation_id, ticket_id, team, priority, sla_minutes, full_context}
7. Create callback channel for AI to receive result
8. Log escalation with all metadata
9. Update ticket status to "escalated"
10. Return escalation_id + SLA + team assignment

#### send_response

| Requirement | Current | Production |
|---|---|---|
| **Channel Integration** | None (mock) | Real API calls (Gmail, WhatsApp, Web) |
| **Template Engine** | Hardcoded strings | Jinja2 templates + parameters |
| **Formatting Validation** | None | Check length limits per channel |
| **Delivery** | Not sent | Actually send to customer |
| **Rate Limiting** | None | Per-customer, per-channel limits |
| **Retry Logic** | None | Exponential backoff on failure |
| **Delivery Tracking** | None | Log message_id + timestamp |
| **Error Recovery** | Crashes | Dead letter queue for failed sends |
| **Personalization** | None | {{customer_name}}, {{ticket_id}} |
| **Audit Trail** | None | Complete history of all sends |

**Implementation Strategy:**
1. Create `SendResponseInput` with message + channel + personalization
2. Load channel-specific template from database or file
3. Render template with Jinja2 (substitute {{variables}})
4. Validate output length (Email <500w, WhatsApp <300c, Web <300w)
5. Check rate limits (Redis counter: f"{customer_id}:{channel}:messages_today")
6. Call appropriate channel handler:
   - Email: Gmail API (with retry + error handling)
   - WhatsApp: Twilio API (with retry + error handling)
   - Web: Database + webhook trigger (with retry)
7. Log delivery event
8. On success: return message_id + timestamp
9. On failure: publish to dead letter queue (Kafka topic)
10. Publish delivery event (for analytics)

---

## Implementation Checklist

### Phase 1: Tool Input Validation (Pydantic Models)

- [ ] Create `SearchKBInput` with query + max_results + category
- [ ] Create `CreateTicketInput` with all fields + validation
- [ ] Create `GetCustomerHistoryInput` with filters
- [ ] Create `EscalateToHumanInput` with context
- [ ] Create `SendResponseInput` with personalization

**Time Estimate:** 1 hour  
**File:** `production/agent/tools.py` (top section)

### Phase 2: Database Layer Setup

- [ ] Verify PostgreSQL schema exists (from production/database/schema.sql)
- [ ] Verify SQLAlchemy models created (from production/database/models.py)
- [ ] Add pgvector extension for semantic search
- [ ] Create knowledge_base table with embedding column
- [ ] Create indexes on frequently queried columns

**Time Estimate:** 2 hours  
**Files:** `production/database/schema.sql`, `production/database/models.py`

### Phase 3: Core Tool Implementation

- [ ] Implement search_knowledge_base (with vector search)
- [ ] Implement create_ticket (with database + Kafka)
- [ ] Implement get_customer_history (with caching)
- [ ] Implement escalate_to_human (with event publishing)
- [ ] Implement send_response (with template rendering)

**Time Estimate:** 6 hours  
**File:** `production/agent/tools.py` (main section)

### Phase 4: Error Handling & Logging

- [ ] Add try/catch to all tools
- [ ] Add structured logging (JSON format)
- [ ] Add Prometheus metrics for each tool
- [ ] Add graceful fallback messages
- [ ] Add error recovery (retries, circuit breakers)

**Time Estimate:** 3 hours  
**Files:** `production/agent/tools.py`, `production/monitoring/logging_config.py`

### Phase 5: Testing

- [ ] Unit tests for each tool with mocked DB
- [ ] Integration tests with real database
- [ ] Edge case tests (empty results, errors, timeouts)
- [ ] Performance tests (latency, throughput)
- [ ] Concurrency tests (multiple requests)

**Time Estimate:** 4 hours  
**File:** `production/tests/test_tools.py`

---

## Error Handling Strategy

### Common Failure Modes

| Failure | Probability | Impact | Solution |
|---|---|---|---|
| **Database connection fails** | High | Tool crashes | Connection pool + retry logic |
| **API timeout (embeddings)** | Medium | Response slow | Timeout + fallback to keyword |
| **Channel API down** | Medium | Can't send response | Queue + retry later (DLQ) |
| **Customer not found** | Low | Validation fails | Check before querying |
| **KB has no results** | Medium | Unhelpful response | Suggest escalation |
| **Concurrent escalations** | Low | Duplicate records | Database unique constraint |
| **Rate limit hit** | Low | Can't send msg | Queue + exponential backoff |

### Error Handling Pattern (All Tools)

```python
@function_tool
async def tool_name(input: ToolInput) -> str:
    """Tool description."""
    try:
        # Main logic
        result = await perform_operation(input)
        
        # Logging
        logger.info("Operation successful", extra={...})
        metrics.tool_success.inc()
        
        return format_result(result)
        
    except SpecificError as e:
        # Known error - handle gracefully
        logger.warning("Known error occurred", exc_info=True)
        metrics.tool_specific_errors.inc()
        return GRACEFUL_MESSAGE
        
    except asyncio.TimeoutError:
        # Timeout - try fallback
        logger.error("Operation timeout", exc_info=True)
        metrics.tool_timeouts.inc()
        return FALLBACK_MESSAGE
        
    except Exception as e:
        # Unexpected - log and escalate
        logger.error("Unexpected error", exc_info=True)
        metrics.tool_errors.inc()
        return ESCALATE_MESSAGE
```

---

## Performance Optimization

### Caching Strategy

```python
# Redis cache for frequently accessed data
customer_history_cache = redis.Redis(host="localhost", port=6379, db=1)

async def get_customer_history(input):
    cache_key = f"customer:{input.customer_id}:history"
    
    # Try cache first
    cached = await customer_history_cache.get(cache_key)
    if cached:
        metrics.cache_hits.inc()
        return json.loads(cached)
    
    # Cache miss - query database
    result = await query_database(input.customer_id)
    
    # Store in cache for 5 minutes
    await customer_history_cache.setex(
        cache_key,
        300,  # 5 minutes
        json.dumps(result)
    )
    
    metrics.cache_misses.inc()
    return result
```

### Database Indexes

```sql
-- Performance-critical indexes
CREATE INDEX idx_messages_customer_id ON messages(customer_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding);
```

### Query Optimization

```python
# Bad: Load all messages, filter in Python
messages = await session.execute(select(Message))
filtered = [m for m in messages.scalars() if m.sentiment > 0.5]

# Good: Filter in database
query = select(Message).where(Message.sentiment > 0.5)
filtered = await session.execute(query)
```

---

## Monitoring & Observability

### Metrics to Collect

```python
from prometheus_client import Counter, Histogram, Gauge

# Per-tool metrics
kb_search_duration = Histogram(
    'tool_kb_search_duration_seconds',
    'KB search execution time'
)
kb_search_results = Counter(
    'tool_kb_search_results_total',
    'KB search result count',
    ['result_type']  # with_results, no_results
)

# Cross-tool metrics
tool_execution_time = Histogram(
    'tool_execution_seconds',
    'Tool execution time',
    ['tool_name']
)
tool_errors = Counter(
    'tool_errors_total',
    'Tool errors',
    ['tool_name', 'error_type']
)
```

### Logging Examples

```python
# Structured logging
logger.info(
    "Knowledge base search completed",
    extra={
        "tool": "search_knowledge_base",
        "query": input.query,
        "results_count": len(results),
        "execution_time_ms": elapsed_ms,
        "intent": detected_intent
    }
)

logger.error(
    "Database connection failed",
    extra={
        "tool": "create_ticket",
        "customer_id": input.customer_id,
        "error_type": type(e).__name__,
        "retry_attempt": 1
    },
    exc_info=True
)
```

---

## Testing Strategy

### Unit Tests (Per Tool)

```python
@pytest.mark.asyncio
async def test_search_knowledge_base_with_results():
    """Happy path: search finds results."""
    input_data = SearchKBInput(query="password reset")
    result = await search_knowledge_base(input_data)
    assert "password" in result.lower()

@pytest.mark.asyncio
async def test_search_knowledge_base_no_results():
    """Edge case: no results found."""
    input_data = SearchKBInput(query="xyznonexistent")
    result = await search_knowledge_base(input_data)
    assert "not found" in result.lower() or "escalat" in result.lower()

@pytest.mark.asyncio
async def test_create_ticket_persists():
    """Persistence: ticket survives restart."""
    input_data = CreateTicketInput(customer_id="CUST-001", ...)
    result = await create_ticket(input_data)
    
    # Verify in database
    ticket = await db_session.execute(
        select(Ticket).where(Ticket.ticket_id == result['ticket_id'])
    )
    assert ticket is not None
```

### Integration Tests (Database)

```python
@pytest.mark.asyncio
async def test_customer_history_cross_channel():
    """Cross-channel: customer history merges all channels."""
    # Create messages in different channels
    await create_message(customer_id="CUST-001", channel="email", ...)
    await create_message(customer_id="CUST-001", channel="whatsapp", ...)
    
    history = await get_customer_history(GetCustomerHistoryInput(customer_id="CUST-001"))
    
    # Should see both channels
    assert len(history["messages"]) >= 2
    assert "email" in [m["channel"] for m in history["messages"]]
    assert "whatsapp" in [m["channel"] for m in history["messages"]]
```

---

## Success Criteria

Tool migration is **complete** when:

- [x] All 5 Pydantic input models defined
- [ ] All 5 tools implemented with @function_tool
- [ ] All tools have error handling + logging
- [ ] All tools pass unit tests
- [ ] All tools pass integration tests  
- [ ] All tools perform <2s (p95 latency)
- [ ] All tools handle edge cases gracefully
- [ ] Prometheus metrics working
- [ ] Documentation complete (docstrings + examples)
- [ ] Ready for Exercise 1.6 (Monitoring & Logging)

---

*Tool Migration Analysis - Complete*  
*Date: 2026-04-03*  
*Next Step: Exercise 3 of Transition Phase (Implementation)*
