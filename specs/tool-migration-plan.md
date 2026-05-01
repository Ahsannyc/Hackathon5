# MCP Tool Migration Plan: Production Conversion

**Status:** ✅ Planning Complete  
**Date:** 2026-04-02  
**Phase:** Exercise 1.7 - Tool Migration  
**Timeline:** Week 3-4 of Transition  

---

## Overview

This document outlines the strategy for converting the 5 prototype MCP tools into production-grade tools with:
- ✅ Pydantic request/response models
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Input validation
- ✅ Performance monitoring
- ✅ Rate limiting
- ✅ Caching support

---

## Current State (Incubation)

### Existing Tools (mcp_server.py)

```python
# Current: Functions with dict I/O
def search_knowledge_base(query: str, max_results: int = 5) -> Dict[str, Any]
def create_ticket(customer_id: str, issue: str, priority: str, channel: str) -> Dict[str, Any]
def get_customer_history(customer_id: str) -> Dict[str, Any]
def escalate_to_human(ticket_id: str, reason: str) -> Dict[str, Any]
def send_response(ticket_id: str, message: str, channel: str) -> Dict[str, Any]
```

**Issues:**
- ❌ No input validation (accept any values)
- ❌ Untyped responses (Dict[str, Any])
- ❌ Ad-hoc error handling
- ❌ No logging
- ❌ No rate limiting
- ❌ No caching
- ❌ No monitoring

---

## Target State (Production)

### Production Tools with Pydantic

```python
from pydantic import BaseModel, Field
from typing import List, Optional

# Tool 1: SearchKnowledgeBase
class SearchKBRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500, description="Customer question")
    max_results: int = Field(5, ge=1, le=10, description="Number of results")

class SearchKBResponse(BaseModel):
    success: bool
    intent: str
    intent_confidence: float = Field(..., ge=0.0, le=1.0)
    matches_found: int
    results: List[Dict]

@mcp.tool(name="search_knowledge_base")
async def search_knowledge_base(request: SearchKBRequest) -> SearchKBResponse:
    """Search product documentation."""
    logger.info("KB search started", query=request.query[:50])
    return await skills.knowledge_retrieval.search(request)
```

---

## Tool-by-Tool Migration Plan

### Tool 1: search_knowledge_base

**Current Incubation Signature:**
```python
def search_knowledge_base(query: str, max_results: int = 5) -> Dict
```

**Production Signature with Pydantic:**
```python
from pydantic import BaseModel, Field, validator

class SearchKBRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Customer question or search query"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of results to return"
    )
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace")
        return v.strip().lower()

class SearchKBResult(BaseModel):
    rank: int
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    category: str
    title: str
    content: str
    article_id: str

class SearchKBResponse(BaseModel):
    success: bool = True
    intent: str
    intent_confidence: float = Field(..., ge=0.0, le=1.0)
    matches_found: int
    results: List[SearchKBResult] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "intent": "troubleshooting",
                "intent_confidence": 0.85,
                "matches_found": 3,
                "results": [...]
            }
        }

# Error Response
class SearchKBError(BaseModel):
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict] = None
```

**Implementation:**
```python
@mcp.tool(name="search_knowledge_base", description="Search knowledge base for relevant documentation")
@rate_limit(calls=100, period=60)  # 100 calls per minute
@log_execution
async def search_knowledge_base(request: SearchKBRequest) -> SearchKBResponse:
    """
    Search product documentation by query.
    
    This tool searches the CloudFlow knowledge base using intent-based routing
    and keyword matching to find relevant articles.
    
    Args:
        request: SearchKBRequest with query and optional max_results
        
    Returns:
        SearchKBResponse with matched articles and intent classification
        
    Raises:
        ValidationError: If input validation fails
        NotFoundError: If no results found (graceful, returns empty results)
    """
    try:
        # Log request
        logger.info(
            "KB search request received",
            query_length=len(request.query),
            max_results=request.max_results,
            session_id=get_session_id()
        )
        
        # Check cache
        cache_key = f"kb_search:{hash(request.query)}:{request.max_results}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info("Cache hit for KB search", cache_key=cache_key)
            return SearchKBResponse(**cached)
        
        # Execute search
        start_time = time.time()
        result = await skills.knowledge_retrieval.search(
            query=request.query,
            max_results=request.max_results
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # Convert to response
        response = SearchKBResponse(
            success=True,
            intent=result['intent'],
            intent_confidence=result['intent_confidence'],
            matches_found=len(result['results']),
            results=[SearchKBResult(**r) for r in result['results']]
        )
        
        # Cache result (5 minute TTL)
        await cache.set(cache_key, response.dict(), ttl=300)
        
        # Log success
        logger.info(
            "KB search completed",
            query=request.query[:50],
            matches=len(response.results),
            duration_ms=duration_ms,
            session_id=get_session_id()
        )
        
        # Track metrics
        metrics.kb_search_latency.observe(duration_ms)
        metrics.kb_search_matches.observe(len(response.results))
        
        return response
        
    except ValueError as e:
        logger.error("KB search validation error", error=str(e))
        raise ValidationError(str(e)) from e
    except Exception as e:
        logger.error("KB search failed", error=str(e), error_type=type(e).__name__)
        raise InternalError("Knowledge base search failed") from e
```

**Error Handling:**
```python
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": exc.message,
            "error_code": "VALIDATION_ERROR"
        }
    )

@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": exc.message,
            "error_code": "NOT_FOUND"
        }
    )
```

---

### Tool 2: create_ticket

**Current:**
```python
def create_ticket(customer_id: str, issue: str, priority: str, channel: str) -> Dict
```

**Production with Pydantic:**
```python
from enum import Enum

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ChannelEnum(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

class CreateTicketRequest(BaseModel):
    customer_id: str = Field(..., pattern="^CUST-\\d{5}$", description="Customer ID")
    issue: str = Field(..., min_length=10, max_length=1000, description="Problem description")
    priority: PriorityEnum = Field(..., description="Ticket priority")
    channel: ChannelEnum = Field(..., description="Communication channel")

class CreateTicketResponse(BaseModel):
    success: bool = True
    ticket_id: str = Field(..., pattern="^T\\d{8}-\\d{4}$")
    status: str = "open"
    priority: PriorityEnum
    estimated_response_minutes: int
    channel: ChannelEnum
    created_at: datetime

@mcp.tool(name="create_ticket")
@log_execution
async def create_ticket(request: CreateTicketRequest) -> CreateTicketResponse:
    """Create a new support ticket."""
    try:
        # Validate customer exists
        customer = await db.customers.get(request.customer_id)
        if not customer:
            raise NotFoundError("Customer", request.customer_id)
        
        # Calculate SLA
        sla_map = {
            PriorityEnum.CRITICAL: 15,
            PriorityEnum.HIGH: 30,
            PriorityEnum.MEDIUM: 120,
            PriorityEnum.LOW: 1440
        }
        
        # Create ticket
        ticket = Ticket(
            customer_id=request.customer_id,
            issue=request.issue,
            priority=request.priority,
            channel=request.channel,
            status="open",
            created_at=datetime.utcnow()
        )
        await db.tickets.add(ticket)
        await db.commit()
        
        logger.info(
            "Ticket created",
            ticket_id=ticket.ticket_id,
            customer_id=request.customer_id,
            priority=request.priority
        )
        
        return CreateTicketResponse(
            ticket_id=ticket.ticket_id,
            status="open",
            priority=request.priority,
            estimated_response_minutes=sla_map[request.priority],
            channel=request.channel,
            created_at=ticket.created_at
        )
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Ticket creation failed", error=str(e))
        raise InternalError("Failed to create ticket") from e
```

---

### Tool 3: get_customer_history

**Current:**
```python
def get_customer_history(customer_id: str) -> Dict
```

**Production with Pydantic:**
```python
class ConversationMessageModel(BaseModel):
    timestamp: datetime
    channel: ChannelEnum
    customer_message: str
    sentiment: str
    intent: str
    ai_response: str
    escalation: bool

class CustomerStatsModel(BaseModel):
    total_messages: int
    first_contact: Optional[datetime]
    last_contact: Optional[datetime]
    sentiment_trend: List[str]
    current_sentiment: str
    topics_discussed: List[str]
    resolution_status: str
    escalation_count: int

class GetCustomerHistoryResponse(BaseModel):
    success: bool = True
    customer_id: str
    customer_name: str
    customer_plan: str
    email: Optional[str]
    phone: Optional[str]
    channels_used: List[ChannelEnum]
    stats: CustomerStatsModel
    conversation_history: List[ConversationMessageModel]
    context_summary: str

@mcp.tool(name="get_customer_history")
@log_execution
@cache(ttl=60)  # Cache for 1 minute
async def get_customer_history(customer_id: str) -> GetCustomerHistoryResponse:
    """Retrieve customer's full conversation history."""
    try:
        # Validate format
        if not customer_id.startswith("CUST-"):
            raise ValidationError(f"Invalid customer ID format: {customer_id}")
        
        # Query database
        customer = await db.customers.get(customer_id)
        if not customer:
            raise NotFoundError("Customer", customer_id)
        
        # Get conversation history
        conversations = await db.conversations.filter_by(customer_id=customer_id).all()
        
        # Build response
        messages = [ConversationMessageModel(**c.dict()) for c in conversations]
        
        stats = CustomerStatsModel(
            total_messages=len(conversations),
            first_contact=conversations[0].created_at if conversations else None,
            last_contact=conversations[-1].created_at if conversations else None,
            sentiment_trend=[c.sentiment for c in conversations],
            current_sentiment=conversations[-1].sentiment if conversations else "neutral",
            topics_discussed=list(set(c.intent for c in conversations)),
            resolution_status=customer.resolution_status,
            escalation_count=sum(1 for c in conversations if c.escalation)
        )
        
        response = GetCustomerHistoryResponse(
            customer_id=customer.customer_id,
            customer_name=customer.customer_name,
            customer_plan=customer.customer_plan,
            email=customer.email,
            phone=customer.phone,
            channels_used=list(set(c.channel for c in conversations)),
            stats=stats,
            conversation_history=messages[:10],  # Last 10 messages
            context_summary=f"{customer.customer_name} ({customer.customer_plan}) - {len(conversations)} messages"
        )
        
        logger.info(
            "Customer history retrieved",
            customer_id=customer_id,
            message_count=len(conversations)
        )
        
        return response
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error("History retrieval failed", error=str(e), customer_id=customer_id)
        raise InternalError("Failed to retrieve customer history") from e
```

---

### Tool 4: escalate_to_human

**Current:**
```python
def escalate_to_human(ticket_id: str, reason: str) -> Dict
```

**Production with Pydantic:**
```python
class EscalationCategoryEnum(str, Enum):
    URGENT = "urgent"
    COMPLIANCE = "compliance"
    BILLING = "billing"
    DATA_LOSS = "data_loss"
    ANGRY_CUSTOMER = "angry_customer"
    FOLLOWUP_STALLED = "followup_stalled"

class EscalationTrigger(BaseModel):
    trigger_type: str
    trigger_value: str
    weight: str
    reason: str

class EscalateRequest(BaseModel):
    ticket_id: str = Field(..., pattern="^T\\d{8}-\\d{4}$")
    reason: str = Field(..., min_length=10, max_length=500)

class EscalateResponse(BaseModel):
    success: bool = True
    escalation_id: str = Field(..., pattern="^ESC-\\d{8}-\\d{4}$")
    category: EscalationCategoryEnum
    assigned_team: str
    sla_minutes: int
    status: str = "assigned"
    triggers: List[EscalationTrigger]
    customer_risk_level: str

@mcp.tool(name="escalate_to_human")
@log_execution
async def escalate_to_human(request: EscalateRequest) -> EscalateResponse:
    """Escalate ticket to specialist team."""
    try:
        # Validate ticket exists
        ticket = await db.tickets.get(request.ticket_id)
        if not ticket:
            raise NotFoundError("Ticket", request.ticket_id)
        
        # Analyze reason for escalation
        category = await skills.escalation_decision.classify_reason(request.reason)
        
        # Get team assignment
        team_map = {
            EscalationCategoryEnum.URGENT: "Technical Support",
            EscalationCategoryEnum.COMPLIANCE: "Legal/Compliance",
            EscalationCategoryEnum.BILLING: "Finance",
            EscalationCategoryEnum.DATA_LOSS: "Technical Recovery",
            EscalationCategoryEnum.ANGRY_CUSTOMER: "Priority Support",
            EscalationCategoryEnum.FOLLOWUP_STALLED: "General Support"
        }
        
        sla_map = {
            EscalationCategoryEnum.URGENT: 15,
            EscalationCategoryEnum.COMPLIANCE: 120,
            EscalationCategoryEnum.BILLING: 240,
            EscalationCategoryEnum.DATA_LOSS: 30,
            EscalationCategoryEnum.ANGRY_CUSTOMER: 30,
            EscalationCategoryEnum.FOLLOWUP_STALLED: 120
        }
        
        # Create escalation
        escalation = Escalation(
            ticket_id=request.ticket_id,
            reason=request.reason,
            category=category,
            assigned_team=team_map[category],
            sla_minutes=sla_map[category],
            status="assigned",
            created_at=datetime.utcnow()
        )
        await db.escalations.add(escalation)
        
        # Update ticket status
        ticket.status = "escalated"
        await db.commit()
        
        logger.info(
            "Escalation created",
            escalation_id=escalation.escalation_id,
            ticket_id=request.ticket_id,
            category=category,
            team=team_map[category]
        )
        
        return EscalateResponse(
            escalation_id=escalation.escalation_id,
            category=category,
            assigned_team=team_map[category],
            sla_minutes=sla_map[category],
            status="assigned",
            triggers=[],  # Would populate from analysis
            customer_risk_level="high" if category in [EscalationCategoryEnum.URGENT, EscalationCategoryEnum.DATA_LOSS] else "medium"
        )
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Escalation failed", error=str(e), ticket_id=request.ticket_id)
        raise InternalError("Escalation failed") from e
```

---

### Tool 5: send_response

**Current:**
```python
def send_response(ticket_id: str, message: str, channel: str) -> Dict
```

**Production with Pydantic:**
```python
class SendResponseRequest(BaseModel):
    ticket_id: str = Field(..., pattern="^T\\d{8}-\\d{4}$")
    message: str = Field(..., min_length=1, max_length=2000)
    channel: ChannelEnum

class SendResponseResponse(BaseModel):
    success: bool = True
    delivery_status: str = "sent"
    channel: ChannelEnum
    formatted_message: str
    timestamp: datetime
    character_count: int
    message_id: str

@mcp.tool(name="send_response")
@log_execution
async def send_response(request: SendResponseRequest) -> SendResponseResponse:
    """Send formatted response to customer."""
    try:
        # Validate ticket exists
        ticket = await db.tickets.get(request.ticket_id)
        if not ticket:
            raise NotFoundError("Ticket", request.ticket_id)
        
        # Get customer for personalization
        customer = await db.customers.get(ticket.customer_id)
        
        # Format message for channel
        formatted = await skills.channel_adaptation.adapt(
            message=request.message,
            channel=request.channel,
            customer_name=customer.customer_name
        )
        
        # Create response record
        response = Response(
            ticket_id=request.ticket_id,
            message=request.message,
            formatted_message=formatted,
            channel=request.channel,
            status="sent",
            created_at=datetime.utcnow()
        )
        await db.responses.add(response)
        
        # Update ticket
        ticket.status = "responded"
        await db.commit()
        
        logger.info(
            "Response sent",
            ticket_id=request.ticket_id,
            channel=request.channel,
            char_count=len(formatted)
        )
        
        return SendResponseResponse(
            delivery_status="sent",
            channel=request.channel,
            formatted_message=formatted,
            timestamp=response.created_at,
            character_count=len(formatted),
            message_id=response.message_id
        )
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Response delivery failed", error=str(e))
        raise InternalError("Failed to send response") from e
```

---

## Cross-Cutting Concerns

### Error Handling Strategy

```python
# production/api/exceptions.py
class CloudFlowException(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class ValidationError(CloudFlowException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class NotFoundError(CloudFlowException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            f"{resource} not found: {id}",
            "NOT_FOUND",
            404
        )

class InternalError(CloudFlowException):
    def __init__(self, message: str):
        super().__init__(message, "INTERNAL_ERROR", 500)

class RateLimitExceeded(CloudFlowException):
    def __init__(self):
        super().__init__(
            "Rate limit exceeded",
            "RATE_LIMIT_EXCEEDED",
            429
        )
```

### Logging Strategy

```python
# production/monitoring/logger.py
import structlog

logger = structlog.get_logger()

def log_execution(func):
    """Decorator to log tool execution."""
    async def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()
        
        try:
            logger.info(
                f"{func_name} started",
                function=func_name,
                session_id=get_session_id()
            )
            
            result = await func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"{func_name} completed",
                function=func_name,
                duration_ms=duration_ms,
                status="success"
            )
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"{func_name} failed",
                function=func_name,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    return wrapper
```

### Rate Limiting Strategy

```python
# production/api/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def rate_limit(calls: int, period: int):
    """Decorator for rate limiting."""
    def decorator(func):
        return limiter.limit(f"{calls}/{period}s")(func)
    return decorator
```

### Caching Strategy

```python
# production/cache/cache_manager.py
class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str):
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600):
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

def cache(ttl: int = 3600):
    """Decorator for result caching."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = await get_cache().get(cache_key)
            if cached:
                return cached
            
            result = await func(*args, **kwargs)
            await get_cache().set(cache_key, result.dict(), ttl=ttl)
            return result
        
        return wrapper
    return decorator
```

---

## Implementation Timeline

### Week 3 (Exercise 1.7, Part 1): Tool 1 & 2 Migration
- [ ] Design Pydantic models for search_knowledge_base
- [ ] Design Pydantic models for create_ticket
- [ ] Implement error handling middleware
- [ ] Add logging decorators
- [ ] Test locally

### Week 3-4 (Exercise 1.7, Part 2): Tool 3, 4, & 5 Migration
- [ ] Design Pydantic models for remaining tools
- [ ] Implement rate limiting
- [ ] Add caching layer
- [ ] Update tool registry
- [ ] Integration testing

### Week 4 (Exercise 1.7, Part 3): Polish & Testing
- [ ] Comprehensive error handling tests
- [ ] Edge case testing
- [ ] Performance testing
- [ ] Documentation update
- [ ] Code review

---

## Success Criteria

✅ **All 5 tools migrated** to Pydantic pattern  
✅ **100% input validation** on all parameters  
✅ **Typed responses** (no Dict[str, Any])  
✅ **Error codes** for all failure scenarios  
✅ **Logging** on all requests/responses  
✅ **Rate limiting** on compute-heavy tools  
✅ **Caching** for read-heavy operations  
✅ **100% test coverage** for each tool  
✅ **Documentation** with examples  

---

**Document Status:** ✅ PLANNING COMPLETE  
**Ready for Implementation:** Exercise 1.7  
**Estimated Duration:** 2 weeks
