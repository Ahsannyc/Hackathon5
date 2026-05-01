# Tool Migration: MCP to OpenAI Agents SDK

**Status:** ✅ COMPLETE - 5 tools successfully migrated  
**Date:** 2026-04-03  
**Exercise:** Step 3 of Transition Phase  
**File Created:** `production/agent/tools.py` (500+ lines)

---

## Executive Summary

Successfully converted 5 MCP server tools (Exercise 1.4) into production-ready @function_tool format for OpenAI Agents SDK. Each tool now includes:

- ✅ Pydantic input validation schemas
- ✅ Comprehensive error handling with fallbacks
- ✅ Structured JSON logging
- ✅ Type hints on all parameters
- ✅ Detailed docstrings explaining when/how to use
- ✅ Graceful degradation on failures

**Files Created:**
- `production/agent/tools.py` (500+ lines) — 5 tools + schemas
- `specs/tool-migration.md` (this file) — Documentation

---

## Before vs After Comparison

### Tool 1: search_knowledge_base

| Aspect | MCP (Incubation) | OpenAI SDK (Production) |
|--------|------------------|----------------------|
| **Input Validation** | Loose type hints | Pydantic BaseModel with constraints |
| **Error Handling** | Returns dict with error field | Try/catch with graceful fallback |
| **Logging** | No structured logging | JSON structured logging + context |
| **Documentation** | Basic docstring | Detailed docstring for LLM + examples |
| **Type Safety** | query: str, max_results: int | KnowledgeSearchInput with Field validation |
| **Database** | In-memory prototype dict | Placeholder for pgvector in Exercise 2.1 |
| **Search Method** | String keyword matching | Prepared for vector similarity |

**Before (MCP):**
```python
def search_knowledge_base(query: str, max_results: int = 5) -> Dict[str, Any]:
    if not query or not query.strip():
        return {"success": False, "error": "Query cannot be empty", "results": []}
    
    intent, confidence = prototype.detect_intent(query)
    kb_match = prototype.search_knowledge_base(query, intent)
    results = []
    # ... simple string matching ...
    return {"success": True, "results": results[:max_results]}
```

**After (OpenAI SDK):**
```python
class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)
    category: Optional[str] = None
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    try:
        logger.info("Knowledge base search initiated", extra={...})
        results = []
        # ... search logic with logging ...
        return json.dumps({"success": True, "results": results})
    except Exception as e:
        logger.error("Knowledge base search failed", exc_info=True)
        return json.dumps({"success": False, "error": "..."})
```

**Key Improvements:**
- ✅ Pydantic validation prevents invalid inputs
- ✅ @validator decorator ensures data quality
- ✅ Structured logging captures execution context
- ✅ Try/catch prevents crashes
- ✅ JSON returns parseable by agent

---

### Tool 2: create_ticket

| Aspect | MCP | OpenAI SDK |
|--------|-----|-----------|
| **Input Validation** | Basic checks in function | Pydantic BaseModel with validators |
| **Customer Lookup** | Uses prototype.memory.customers | Uses _customers_db placeholder |
| **Priority Validation** | List checking | Enum with predefined values |
| **Channel Validation** | Try/except on enum | Enum in Pydantic model |
| **ID Generation** | prototype.generate_ticket_id() | Deterministic format with counter |
| **SLA Mapping** | Dictionary lookup | Structured with minutes + label |
| **Error Responses** | Returns dict with error | Returns JSON string for consistency |
| **Logging** | No logging | Structured logging with context |

**Before (MCP):**
```python
def create_ticket(customer_id: str, issue: str, priority: str, channel: str):
    if customer_id not in prototype.memory.customers:
        return {"success": False, "error": f"Customer {customer_id} not found"}
    
    if priority.lower() not in ["low", "medium", "high", "critical"]:
        return {"success": False, "error": "Invalid priority"}
    
    ticket_id = prototype.generate_ticket_id()
    tickets_db[ticket_id] = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority.lower(),
        "status": "open",
        "created_at": datetime.now().isoformat(),
    }
    return {"success": True, "ticket_id": ticket_id, ...}
```

**After (OpenAI SDK):**
```python
class TicketInput(BaseModel):
    customer_id: str = Field(..., description="CUST-XXXXX format")
    issue: str = Field(..., min_length=5, max_length=2000)
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    channel: ChannelType = Field(...)
    
    @validator('customer_id')
    def validate_customer_id(cls, v):
        if not v.startswith("CUST-"):
            raise ValueError("Customer ID must start with 'CUST-'")
        return v

def create_ticket(input: TicketInput) -> str:
    try:
        if input.customer_id not in _customers_db:
            logger.warning("Customer not found", extra={"customer_id": input.customer_id})
            return json.dumps({"success": False, "error": "Customer not found"})
        
        sla = sla_mapping[input.priority]
        ticket = {...}
        _tickets_db[ticket_id] = ticket
        
        logger.info("Ticket created", extra={"ticket_id": ticket_id, ...})
        return json.dumps({"success": True, "ticket_id": ticket_id, ...})
    except Exception as e:
        logger.error("Ticket creation failed", exc_info=True)
        return json.dumps({"success": False, "error": "Failed to create ticket"})
```

**Key Improvements:**
- ✅ Enum prevents invalid priorities
- ✅ Format validation on customer_id
- ✅ Structured SLA mapping
- ✅ Complete error logging
- ✅ JSON return for consistency

---

### Tool 3: get_customer_history

| Aspect | MCP | OpenAI SDK |
|--------|-----|-----------|
| **Input Validation** | Just customer_id: str | CustomerHistoryInput with validators |
| **Limit Parameter** | Hardcoded -10 | Configurable with constraints |
| **Error Handling** | Checks if customer exists | Try/catch + logging |
| **Data Source** | prototype.memory.get_customer_state | Placeholder for DB queries |
| **Return Format** | Dict with nested structure | JSON string for consistency |
| **Logging** | No logging | Structured logging with plan info |

**Before (MCP):**
```python
def get_customer_history(customer_id: str) -> Dict[str, Any]:
    customer_state = prototype.memory.get_customer_state(customer_id)
    
    if not customer_state:
        return {"success": False, "error": f"Customer {customer_id} not found"}
    
    conversation_history = []
    for msg in customer_state.conversation_history[-10:]:
        conversation_history.append({...})
    
    return {
        "success": True,
        "customer_id": customer_id,
        "stats": {...},
        "conversation_history": conversation_history,
    }
```

**After (OpenAI SDK):**
```python
class CustomerHistoryInput(BaseModel):
    customer_id: str = Field(..., description="CUST-XXXXX format")
    limit: int = Field(default=10, ge=1, le=100)
    
    @validator('customer_id')
    def validate_customer_id(cls, v):
        if not v.startswith("CUST-"):
            raise ValueError("Customer ID must start with 'CUST-'")
        return v

def get_customer_history(input: CustomerHistoryInput) -> str:
    try:
        if input.customer_id not in _customers_db:
            logger.warning("Customer not found", extra={"customer_id": input.customer_id})
            return json.dumps({"success": False, "error": "Customer not found"})
        
        logger.info("Customer history retrieved", extra={"customer_id": input.customer_id, "plan": customer["plan"]})
        
        history_response = {
            "success": True,
            "customer_id": input.customer_id,
            "customer": {...},
            "stats": {...},
            "conversation_history": [],
        }
        return json.dumps(history_response)
    except Exception as e:
        logger.error("Customer history retrieval failed", exc_info=True)
        return json.dumps({"success": False, "error": "Failed to retrieve history"})
```

**Key Improvements:**
- ✅ Configurable limit (1-100)
- ✅ Input validation with format checking
- ✅ Complete error handling
- ✅ Structured logging
- ✅ JSON return for consistency

---

### Tool 4: escalate_to_human

| Aspect | MCP | OpenAI SDK |
|--------|-----|-----------|
| **Input Validation** | Loose strings | EscalationInput with validators |
| **Reason Classification** | prototype.detect_escalation_triggers | Category parameter + mapping |
| **Team Assignment** | Hard-coded mapping dict | Structured with team + SLA info |
| **Escalation ID** | Date + counter | Same format with global counter |
| **Error Handling** | Check if ticket exists | Try/catch + logging |
| **Return Format** | Dict | JSON string |
| **Logging** | No logging | Structured logging |

**Before (MCP):**
```python
def escalate_to_human(ticket_id: str, reason: str) -> Dict[str, Any]:
    if ticket_id not in tickets_db:
        return {"success": False, "error": f"Ticket {ticket_id} not found"}
    
    escalation_needed, category = prototype.detect_escalation_triggers(reason, 0.1, "general")
    
    team_mapping = {...}
    assigned_team = team_mapping.get(escalation_category, "General Support")
    
    escalation_id = f"ESC-{date_str}-{escalation_counter:04d}"
    escalations_db[escalation_id] = {...}
    
    return {"success": True, "escalation_id": escalation_id, ...}
```

**After (OpenAI SDK):**
```python
class EscalationInput(BaseModel):
    ticket_id: str = Field(..., description="T-XXXXX format")
    reason: str = Field(..., min_length=5, max_length=1000)
    category: Optional[str] = None
    
    @validator('ticket_id')
    def validate_ticket_id(cls, v):
        if not v.startswith("T-"):
            raise ValueError("Ticket ID must start with 'T-'")
        return v

def escalate_to_human(input: EscalationInput) -> str:
    try:
        if input.ticket_id not in _tickets_db:
            logger.warning("Escalation failed - ticket not found", extra={"ticket_id": input.ticket_id})
            return json.dumps({"success": False, "error": "Ticket not found"})
        
        category = (input.category or "default").lower()
        team_info = team_mapping.get(category, team_mapping["default"])
        
        escalation_id = f"ESC-{date_str}-{_escalation_counter:04d}"
        _escalations_db[escalation_id] = {...}
        
        logger.info("Escalation created", extra={"escalation_id": escalation_id, "category": category, ...})
        return json.dumps({"success": True, "escalation_id": escalation_id, ...})
    except Exception as e:
        logger.error("Escalation creation failed", exc_info=True)
        return json.dumps({"success": False, "error": "Failed to escalate"})
```

**Key Improvements:**
- ✅ Input validation on ticket_id format
- ✅ Optional category parameter
- ✅ SLA structured with team info
- ✅ Complete error handling
- ✅ Structured logging with context

---

### Tool 5: send_response

| Aspect | MCP | OpenAI SDK |
|--------|-----|-----------|
| **Input Validation** | Individual checks | ResponseInput BaseModel |
| **Channel Guidelines** | Lookup in prototype.brand_guidelines | Lookup in _brand_guidelines |
| **Message Formatting** | String concatenation | Structured with greeting + closing |
| **Length Validation** | No validation | Per-channel constraints enforced |
| **Error Handling** | Basic checks | Try/catch + detailed logging |
| **Return Format** | Dict | JSON string |
| **Personalization** | Hard-coded | Parameter with {name} substitution |

**Before (MCP):**
```python
def send_response(ticket_id: str, message: str, channel: str) -> Dict[str, Any]:
    if ticket_id not in tickets_db:
        return {"success": False, "error": f"Ticket {ticket_id} not found"}
    
    if not message or not message.strip():
        return {"success": False, "error": "Message cannot be empty"}
    
    guidelines = prototype.brand_guidelines.get(channel_value, {})
    greeting = guidelines.get("greeting", "Hi there!")
    closing = guidelines.get("closing", "Best regards")
    
    ticket = tickets_db[ticket_id]
    ticket["responses"].append({"message": message, "timestamp": ..., "channel": channel})
    
    return {"success": True, "delivery_status": "sent", ...}
```

**After (OpenAI SDK):**
```python
class ResponseInput(BaseModel):
    ticket_id: str = Field(..., description="T-XXXXX format")
    message: str = Field(..., min_length=1, max_length=5000)
    channel: ChannelType = Field(...)
    customer_name: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace")
        return v.strip()
    
    @validator('ticket_id')
    def validate_ticket_id(cls, v):
        if not v.startswith("T-"):
            raise ValueError("Ticket ID must start with 'T-'")
        return v

def send_response(input: ResponseInput) -> str:
    try:
        if input.ticket_id not in _tickets_db:
            logger.warning("Response send failed - ticket not found", extra={"ticket_id": input.ticket_id})
            return json.dumps({"success": False, "error": "Ticket not found"})
        
        guidelines = _brand_guidelines.get(input.channel.value)
        greeting = guidelines["greeting"].format(name=input.customer_name or "valued customer")
        formatted_message = f"{greeting}\n\n{input.message}\n\n{closing}"
        
        # Validate length
        if len(formatted_message) > length_limits[input.channel.value]:
            return json.dumps({"success": False, "error": "Message exceeds limit"})
        
        logger.info("Response sent successfully", extra={"ticket_id": input.ticket_id, "channel": input.channel.value})
        return json.dumps({"success": True, "delivery_status": "sent", ...})
    except Exception as e:
        logger.error("Response send failed", exc_info=True)
        return json.dumps({"success": False, "error": "Failed to send response"})
```

**Key Improvements:**
- ✅ Enum for channel type
- ✅ Optional customer name for personalization
- ✅ Per-channel length validation
- ✅ Message stripping validation
- ✅ Detailed error logging

---

## Summary of Improvements

| Improvement | Impact | Tools |
|-------------|--------|-------|
| **Input Validation** | Prevents invalid data from reaching core logic | All 5 |
| **Error Handling** | Graceful degradation instead of crashes | All 5 |
| **Structured Logging** | Observable execution for debugging | All 5 |
| **Type Safety** | IDE autocomplete + runtime validation | All 5 |
| **Detailed Docstrings** | LLM understands when/how to use tools | All 5 |
| **Per-Channel Constraints** | Channel-specific formatting rules enforced | send_response |
| **SLA Mapping** | Clear escalation timing | create_ticket, escalate_to_human |
| **Personalization** | Customer name substitution | send_response |

---

## Test Plan for Production Tools

### Unit Tests: Input Validation

#### KnowledgeSearchInput

```python
@pytest.mark.asyncio
async def test_knowledge_search_valid_input():
    """Valid input passes validation."""
    input = KnowledgeSearchInput(query="password reset", max_results=5)
    assert input.query == "password reset"
    assert input.max_results == 5

@pytest.mark.asyncio
async def test_knowledge_search_empty_query():
    """Empty query raises validation error."""
    with pytest.raises(ValueError, match="cannot be empty"):
        KnowledgeSearchInput(query="")

@pytest.mark.asyncio
async def test_knowledge_search_whitespace_only():
    """Whitespace-only query raises validation error."""
    with pytest.raises(ValueError, match="cannot be empty"):
        KnowledgeSearchInput(query="   ")

@pytest.mark.asyncio
async def test_knowledge_search_max_results_bounds():
    """Max results must be 1-20."""
    with pytest.raises(ValueError):
        KnowledgeSearchInput(query="test", max_results=0)
    
    with pytest.raises(ValueError):
        KnowledgeSearchInput(query="test", max_results=21)

@pytest.mark.asyncio
async def test_knowledge_search_defaults():
    """Default values applied."""
    input = KnowledgeSearchInput(query="test")
    assert input.max_results == 5
    assert input.category is None
```

#### TicketInput

```python
@pytest.mark.asyncio
async def test_ticket_valid_input():
    """Valid ticket input."""
    input = TicketInput(
        customer_id="CUST-001",
        issue="Cannot login to account",
        priority=PriorityLevel.HIGH,
        channel=ChannelType.EMAIL
    )
    assert input.customer_id == "CUST-001"
    assert input.priority == PriorityLevel.HIGH

@pytest.mark.asyncio
async def test_ticket_invalid_customer_id():
    """Customer ID must start with CUST-."""
    with pytest.raises(ValueError, match="must start with"):
        TicketInput(
            customer_id="USER-001",
            issue="Test issue",
            channel=ChannelType.EMAIL
        )

@pytest.mark.asyncio
async def test_ticket_issue_length_validation():
    """Issue must be 5-2000 characters."""
    with pytest.raises(ValueError):
        TicketInput(
            customer_id="CUST-001",
            issue="abc",  # Too short
            channel=ChannelType.EMAIL
        )

@pytest.mark.asyncio
async def test_ticket_default_priority():
    """Default priority is MEDIUM."""
    input = TicketInput(
        customer_id="CUST-001",
        issue="Test issue",
        channel=ChannelType.EMAIL
    )
    assert input.priority == PriorityLevel.MEDIUM
```

#### ResponseInput

```python
@pytest.mark.asyncio
async def test_response_valid_input():
    """Valid response input."""
    input = ResponseInput(
        ticket_id="T-20260403-0001",
        message="Your issue has been resolved",
        channel=ChannelType.EMAIL,
        customer_name="John Smith"
    )
    assert input.ticket_id == "T-20260403-0001"
    assert input.customer_name == "John Smith"

@pytest.mark.asyncio
async def test_response_invalid_ticket_id():
    """Ticket ID must start with T-."""
    with pytest.raises(ValueError, match="must start with"):
        ResponseInput(
            ticket_id="TICKET-001",
            message="Test response",
            channel=ChannelType.EMAIL
        )

@pytest.mark.asyncio
async def test_response_empty_message():
    """Message cannot be empty or whitespace."""
    with pytest.raises(ValueError):
        ResponseInput(
            ticket_id="T-20260403-0001",
            message="   ",
            channel=ChannelType.EMAIL
        )

@pytest.mark.asyncio
async def test_response_message_stripping():
    """Message whitespace is stripped."""
    input = ResponseInput(
        ticket_id="T-20260403-0001",
        message="  Test message  ",
        channel=ChannelType.EMAIL
    )
    assert input.message == "Test message"
```

### Integration Tests: Tool Execution

#### search_knowledge_base

```python
@pytest.mark.asyncio
async def test_search_knowledge_base_found():
    """Tool returns results when found."""
    result_json = search_knowledge_base(
        KnowledgeSearchInput(query="upgrade plan")
    )
    result = json.loads(result_json)
    assert result["success"] == True
    assert len(result["results"]) > 0

@pytest.mark.asyncio
async def test_search_knowledge_base_not_found():
    """Tool returns empty results gracefully."""
    result_json = search_knowledge_base(
        KnowledgeSearchInput(query="xyznonexistent")
    )
    result = json.loads(result_json)
    assert result["success"] == True
    assert result["results_count"] == 0
    assert "Consider" in result.get("message", "")

@pytest.mark.asyncio
async def test_search_knowledge_base_with_category():
    """Tool filters by category."""
    result_json = search_knowledge_base(
        KnowledgeSearchInput(query="upgrade", category="billing")
    )
    result = json.loads(result_json)
    assert result["success"] == True
```

#### create_ticket

```python
@pytest.mark.asyncio
async def test_create_ticket_success():
    """Tool creates ticket successfully."""
    result_json = create_ticket(
        TicketInput(
            customer_id="CUST-001",
            issue="Cannot login",
            priority=PriorityLevel.HIGH,
            channel=ChannelType.EMAIL
        )
    )
    result = json.loads(result_json)
    assert result["success"] == True
    assert result["ticket_id"].startswith("T-")
    assert result["status"] == "open"

@pytest.mark.asyncio
async def test_create_ticket_customer_not_found():
    """Tool returns error if customer not found."""
    result_json = create_ticket(
        TicketInput(
            customer_id="CUST-999",
            issue="Test issue",
            channel=ChannelType.EMAIL
        )
    )
    result = json.loads(result_json)
    assert result["success"] == False
    assert "not found" in result["error"].lower()

@pytest.mark.asyncio
async def test_create_ticket_sla_by_priority():
    """Tool sets correct SLA based on priority."""
    priorities_and_slas = [
        (PriorityLevel.CRITICAL, 15),
        (PriorityLevel.HIGH, 30),
        (PriorityLevel.MEDIUM, 120),
        (PriorityLevel.LOW, 1440),
    ]
    
    for priority, expected_sla in priorities_and_slas:
        result_json = create_ticket(
            TicketInput(
                customer_id="CUST-001",
                issue="Test issue",
                priority=priority,
                channel=ChannelType.EMAIL
            )
        )
        result = json.loads(result_json)
        assert result["sla_minutes"] == expected_sla
```

#### get_customer_history

```python
@pytest.mark.asyncio
async def test_get_customer_history_success():
    """Tool returns customer history."""
    result_json = get_customer_history(
        CustomerHistoryInput(customer_id="CUST-001")
    )
    result = json.loads(result_json)
    assert result["success"] == True
    assert result["customer"]["name"] == "John Smith"
    assert "stats" in result

@pytest.mark.asyncio
async def test_get_customer_history_not_found():
    """Tool returns error if customer not found."""
    result_json = get_customer_history(
        CustomerHistoryInput(customer_id="CUST-999")
    )
    result = json.loads(result_json)
    assert result["success"] == False
    assert "not found" in result["error"].lower()
```

#### escalate_to_human

```python
@pytest.mark.asyncio
async def test_escalate_to_human_success():
    """Tool escalates ticket successfully."""
    # First create a ticket
    ticket_result = create_ticket(...)
    ticket_id = json.loads(ticket_result)["ticket_id"]
    
    # Then escalate it
    result_json = escalate_to_human(
        EscalationInput(
            ticket_id=ticket_id,
            reason="Customer requesting refund",
            category="refund"
        )
    )
    result = json.loads(result_json)
    assert result["success"] == True
    assert result["escalation_id"].startswith("ESC-")
    assert result["assigned_team"] == "Finance Team"

@pytest.mark.asyncio
async def test_escalate_to_human_ticket_not_found():
    """Tool returns error if ticket not found."""
    result_json = escalate_to_human(
        EscalationInput(
            ticket_id="T-99999999-9999",
            reason="Test escalation"
        )
    )
    result = json.loads(result_json)
    assert result["success"] == False
```

#### send_response

```python
@pytest.mark.asyncio
async def test_send_response_success():
    """Tool sends response successfully."""
    # First create a ticket
    ticket_result = create_ticket(...)
    ticket_id = json.loads(ticket_result)["ticket_id"]
    
    # Then send response
    result_json = send_response(
        ResponseInput(
            ticket_id=ticket_id,
            message="Your issue has been resolved",
            channel=ChannelType.EMAIL,
            customer_name="John Smith"
        )
    )
    result = json.loads(result_json)
    assert result["success"] == True
    assert result["delivery_status"] == "sent"
    assert "Dear John Smith" in result["formatted_message"]

@pytest.mark.asyncio
async def test_send_response_length_validation():
    """Tool validates message length per channel."""
    ticket_result = create_ticket(...)
    ticket_id = json.loads(ticket_result)["ticket_id"]
    
    # WhatsApp has 300 char limit
    long_message = "x" * 400
    result_json = send_response(
        ResponseInput(
            ticket_id=ticket_id,
            message=long_message,
            channel=ChannelType.WHATSAPP
        )
    )
    result = json.loads(result_json)
    assert result["success"] == False
    assert "exceeds" in result.get("error", "").lower()
```

### Error Scenario Tests

```python
@pytest.mark.asyncio
async def test_tools_handle_database_errors():
    """Tools gracefully handle database errors."""
    # Simulate database error
    _customers_db.clear()
    
    result_json = create_ticket(
        TicketInput(
            customer_id="CUST-001",
            issue="Test",
            channel=ChannelType.EMAIL
        )
    )
    result = json.loads(result_json)
    assert result["success"] == False
    assert "error" in result

@pytest.mark.asyncio
async def test_tools_log_execution():
    """Tools generate structured logs."""
    # Check that logs are generated with context
    with caplog.at_level(logging.INFO):
        search_knowledge_base(
            KnowledgeSearchInput(query="test")
        )
    
    assert any("Knowledge base search" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_response_formatting_by_channel():
    """Response formatting differs by channel."""
    ticket_result = create_ticket(...)
    ticket_id = json.loads(ticket_result)["ticket_id"]
    
    # Test Email formatting
    email_result = send_response(
        ResponseInput(
            ticket_id=ticket_id,
            message="Test",
            channel=ChannelType.EMAIL
        )
    )
    email_msg = json.loads(email_result)["formatted_message"]
    assert "Dear" in email_msg
    
    # Test WhatsApp formatting
    whatsapp_result = send_response(
        ResponseInput(
            ticket_id=ticket_id,
            message="Test",
            channel=ChannelType.WHATSAPP
        )
    )
    whatsapp_msg = json.loads(whatsapp_result)["formatted_message"]
    assert "👋" in whatsapp_msg or "Hi" in whatsapp_msg
```

---

## Key Differences: MCP to OpenAI SDK

| Area | MCP | OpenAI SDK |
|------|-----|-----------|
| **Framework** | Server pattern (async, streaming) | Function tool pattern (pure functions) |
| **Input Type** | Individual parameters | Single Pydantic model |
| **Return Type** | Dict (unstructured) | JSON string (LLM parseable) |
| **Error Handling** | In-band (error field in dict) | Out-of-band (try/catch) |
| **Logging** | Manual print statements | Structured JSON via logger |
| **Validation** | Manual in function body | Declarative via Pydantic |
| **Documentation** | Docstring for tool | Detailed docstring + examples for LLM |
| **Type Safety** | Hints only | Enforced at runtime |

---

## Next Steps

### For Exercise 2.1 (Database Schema)
- Replace `_customers_db`, `_tickets_db`, `_escalations_db` placeholders with SQLAlchemy queries
- Replace `_knowledge_base` placeholder with pgvector semantic search
- Use database models from `production/database/models.py`

### For Exercise 2.2 (Channel Integrations)
- Implement actual Gmail API calls in send_response for EMAIL channel
- Implement Twilio WhatsApp API calls for WHATSAPP channel
- Implement webhook calls for WEB_FORM channel

### For Exercise 2.3 (OpenAI Agents SDK)
- Import these tools into the agent definition
- Use Pydantic schemas for automatic LLM input validation
- Wrap with @tool decorator from OpenAI Agents SDK

### For Exercise 2.4 (Kafka Integration)
- Publish events to Kafka when tickets created
- Publish events when escalations triggered
- Subscribe to response confirmation events

---

## Migration Summary

**Status:** ✅ COMPLETE

- [x] 5 MCP tools analyzed and documented
- [x] Pydantic input models created for each tool
- [x] Error handling implemented with fallbacks
- [x] Structured logging added
- [x] Detailed docstrings for LLM understanding
- [x] Type hints on all parameters
- [x] JSON return format (consistent, parseable)
- [x] Channel-specific formatting (send_response)
- [x] SLA mapping (create_ticket, escalate_to_human)
- [x] Test plan defined for all tools
- [x] Placeholder data stores ready for Exercise 2.1

**Files Created:**
- ✅ `production/agent/tools.py` (500+ lines)
- ✅ `specs/tool-migration.md` (this file, 800+ lines)

---

*Tool Migration Complete*  
*Date: 2026-04-03*  
*Next: Step 4 - Transform System Prompt (production-ready system prompt)*
