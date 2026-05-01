"""
Database Module - Persistence Layer

Exports ORM models, schemas, and database utilities.
"""

# SQLAlchemy ORM Models
from .models import (
    Base,
    Customer,
    Conversation,
    Message,
    Ticket,
    Escalation,
    KnowledgeBase,
    SentimentTrend,
    ResponseTemplate,
    AuditLog,
    init_db,
    drop_all_tables,
)

# Pydantic Schemas (for API validation)
from .schema import (
    # Enums
    ChannelType,
    PriorityLevel,
    TicketStatus,
    SentimentLevel,
    # Customer Schemas
    CustomerBase,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    # Conversation Schemas
    ConversationBase,
    ConversationCreate,
    ConversationResponse,
    ConversationMessageSchema,
    # Ticket Schemas
    TicketBase,
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    # Escalation Schemas
    EscalationBase,
    EscalationCreate,
    EscalationResponse,
    # Search Schemas
    KnowledgeSearchInput,
    KnowledgeBaseEntry,
    KnowledgeSearchResponse,
    # Sentiment Schemas
    SentimentAnalysisInput,
    SentimentAnalysisResponse,
    # Response Schemas
    FormattedResponseInput,
    FormattedResponseOutput,
    # Health Check
    HealthCheckResponse,
    ServiceHealth,
    # Error Handling
    ErrorResponse,
)

__all__ = [
    # Base
    "Base",
    # Models
    "Customer",
    "Conversation",
    "Message",
    "Ticket",
    "Escalation",
    "KnowledgeBase",
    "SentimentTrend",
    "ResponseTemplate",
    "AuditLog",
    # DB Functions
    "init_db",
    "drop_all_tables",
    # Enums
    "ChannelType",
    "PriorityLevel",
    "TicketStatus",
    "SentimentLevel",
    # Schemas
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "ConversationBase",
    "ConversationCreate",
    "ConversationResponse",
    "ConversationMessageSchema",
    "TicketBase",
    "TicketCreate",
    "TicketUpdate",
    "TicketResponse",
    "EscalationBase",
    "EscalationCreate",
    "EscalationResponse",
    "KnowledgeSearchInput",
    "KnowledgeBaseEntry",
    "KnowledgeSearchResponse",
    "SentimentAnalysisInput",
    "SentimentAnalysisResponse",
    "FormattedResponseInput",
    "FormattedResponseOutput",
    "HealthCheckResponse",
    "ServiceHealth",
    "ErrorResponse",
]
