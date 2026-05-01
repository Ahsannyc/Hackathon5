"""
Database Schemas - Pydantic Models for API Requests/Responses and Database Table Definitions

This module defines all Pydantic models for validation and API contracts, plus SQLAlchemy table
definitions that will be imported into models.py.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ChannelType(str, Enum):
    """Supported communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class PriorityLevel(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Ticket lifecycle status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SentimentLevel(str, Enum):
    """Customer sentiment classification."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerBase(BaseModel):
    """Base customer data."""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    plan: str = Field(default="free", max_length=50)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating customer."""
    name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    plan: Optional[str] = Field(None, max_length=50)


class CustomerResponse(CustomerBase):
    """Schema for customer API response."""
    id: str = Field(..., alias="customer_id")
    created_at: datetime
    updated_at: datetime
    total_messages: int = 0
    escalation_count: int = 0

    class Config:
        from_attributes = True


# ============================================================================
# CONVERSATION & MESSAGE SCHEMAS
# ============================================================================

class ConversationMessageSchema(BaseModel):
    """Single message in a conversation."""
    id: str
    content: str = Field(..., min_length=1, max_length=5000)
    sender: str = Field(..., description="customer or agent")
    channel: ChannelType
    sentiment: Optional[float] = Field(None, ge=0.0, le=1.0)
    intent: Optional[str] = None
    timestamp: datetime


class ConversationBase(BaseModel):
    """Base conversation data."""
    customer_id: str
    channel: ChannelType
    subject: Optional[str] = Field(None, max_length=500)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation API response."""
    id: str
    status: str
    messages: List[ConversationMessageSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TICKET SCHEMAS
# ============================================================================

class TicketBase(BaseModel):
    """Base ticket data."""
    customer_id: str
    issue: str = Field(..., min_length=5, max_length=2000)
    priority: PriorityLevel = PriorityLevel.MEDIUM
    channel: ChannelType


class TicketCreate(TicketBase):
    """Schema for creating a ticket."""
    pass


class TicketUpdate(BaseModel):
    """Schema for updating ticket."""
    issue: Optional[str] = Field(None, max_length=2000)
    priority: Optional[PriorityLevel] = None
    status: Optional[TicketStatus] = None


class TicketResponse(TicketBase):
    """Schema for ticket API response."""
    id: str = Field(..., alias="ticket_id")
    status: TicketStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    sla_minutes: int

    class Config:
        from_attributes = True


# ============================================================================
# ESCALATION SCHEMAS
# ============================================================================

class EscalationBase(BaseModel):
    """Base escalation data."""
    ticket_id: str
    reason: str = Field(..., min_length=5, max_length=1000)
    assigned_team: str = Field(..., max_length=100)


class EscalationCreate(EscalationBase):
    """Schema for creating escalation."""
    pass


class EscalationResponse(EscalationBase):
    """Schema for escalation API response."""
    id: str = Field(..., alias="escalation_id")
    priority: str
    sla_minutes: int
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# SEARCH & KNOWLEDGE BASE SCHEMAS
# ============================================================================

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)
    category: Optional[str] = None


class KnowledgeBaseEntry(BaseModel):
    """Single knowledge base entry."""
    id: str
    title: str = Field(..., max_length=255)
    content: str = Field(..., max_length=5000)
    category: str = Field(..., max_length=100)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchResponse(BaseModel):
    """Response from knowledge base search."""
    success: bool
    query: str
    detected_intent: str
    intent_confidence: float = Field(ge=0.0, le=1.0)
    results: List[KnowledgeBaseEntry]
    total_found: int


# ============================================================================
# SENTIMENT ANALYSIS SCHEMAS
# ============================================================================

class SentimentAnalysisInput(BaseModel):
    """Input for sentiment analysis."""
    message: str = Field(..., min_length=1, max_length=5000)
    context: Optional[List[str]] = None


class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis result."""
    primary_sentiment: SentimentLevel
    confidence: float = Field(ge=0.0, le=1.0)
    sentiment_scores: Dict[str, float] = Field(..., description="Confidence per sentiment type")
    emotion_tags: List[str]
    urgency_level: int = Field(ge=0, le=5)
    should_escalate: bool
    recommendation: str


# ============================================================================
# ESCALATION DECISION SCHEMAS
# ============================================================================

class EscalationDecisionInput(BaseModel):
    """Input for escalation decision."""
    ticket_id: str
    reason: str
    sentiment_score: float = Field(ge=0.0, le=5.0)
    attempt_count: int = Field(ge=0)
    conversation_history: Optional[List[Dict]] = None


class EscalationDecisionResponse(BaseModel):
    """Escalation decision result."""
    should_escalate: bool
    confidence: float = Field(ge=0.0, le=1.0)
    category: str
    assigned_team: str
    priority: PriorityLevel
    sla_minutes: int
    rules_triggered: List[str]
    reason: str


# ============================================================================
# RESPONSE FORMATTING SCHEMAS
# ============================================================================

class FormattedResponseInput(BaseModel):
    """Input for response formatting."""
    message: str = Field(..., min_length=1, max_length=5000)
    channel: ChannelType
    customer_name: Optional[str] = None
    sentiment: Optional[SentimentLevel] = None
    ticket_id: Optional[str] = None


class FormattedResponseOutput(BaseModel):
    """Formatted response output."""
    success: bool
    channel: ChannelType
    original_length: int
    formatted_message: str
    formatted_length: int
    character_count: int
    tone: str
    formatting_applied: List[str]
    within_constraints: bool


# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class DatabaseHealth(BaseModel):
    """Database health status."""
    status: str = Field(..., description="healthy or unhealthy")
    connection_pool: str = Field(..., description="pool status")
    response_time_ms: float


class CacheHealth(BaseModel):
    """Cache (Redis) health status."""
    status: str
    response_time_ms: float


class ServiceHealth(BaseModel):
    """Overall service health."""
    status: str = Field(..., description="healthy, degraded, or unhealthy")
    timestamp: datetime
    version: str
    database: DatabaseHealth
    cache: CacheHealth
    uptime_seconds: float


class HealthCheckResponse(BaseModel):
    """Health check API response."""
    status: str
    timestamp: datetime
    services: ServiceHealth
    message: str


# ============================================================================
# AGENT RESPONSE SCHEMAS
# ============================================================================

class ToolCall(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time_ms: float
    success: bool


class AgentResponse(BaseModel):
    """Response from agent processing."""
    success: bool
    message: str
    channel: ChannelType
    ticket_id: str
    customer_id: str
    escalated: bool
    escalation_reason: Optional[str] = None
    tool_calls: List[ToolCall]
    response_time_ms: float
    timestamp: datetime


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error_type: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime
    request_id: Optional[str] = None


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_customer_email_or_phone(customer: CustomerBase) -> CustomerBase:
    """Ensure customer has either email or phone."""
    if not customer.email and not customer.phone:
        raise ValueError("Customer must have either email or phone")
    return customer


# ============================================================================
# DATABASE TABLE DEFINITIONS (for reference, actual ORM in models.py)
# ============================================================================

"""
SQLAlchemy table definitions are in models.py and imported into database.py

Tables:
- customers: Core customer records
- conversations: Conversation sessions
- messages: Individual messages in conversations
- tickets: Support tickets
- escalations: Escalated tickets
- knowledge_base: Product documentation with embeddings
"""
