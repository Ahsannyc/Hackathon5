"""
Database Models - SQLAlchemy ORM Models for PostgreSQL

This module defines the SQLAlchemy models that map to the production PostgreSQL database.
All models use the schemas defined in schema.py for validation and API contracts.
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Boolean, Enum as SQLEnum,
    ForeignKey, Table, Index, UniqueConstraint, CheckConstraint, func,
    ARRAY, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from typing import Optional, List
import uuid

from .schema import (
    ChannelType, PriorityLevel, TicketStatus, SentimentLevel
)

# ============================================================================
# DATABASE BASE CLASS
# ============================================================================

Base = declarative_base()


# ============================================================================
# CUSTOMER MODEL
# ============================================================================

class Customer(Base):
    """Customer profile and metadata."""
    __tablename__ = "customers"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Core Fields
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    plan = Column(String(50), default="free", nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Statistics (cached)
    total_messages = Column(Integer, default=0)
    escalation_count = Column(Integer, default=0)
    average_sentiment = Column(Float, nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="customer", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="email_or_phone_required"),
        Index("idx_customer_email_phone", "email", "phone"),
    )

    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name}, email={self.email})>"


# ============================================================================
# CONVERSATION MODEL
# ============================================================================

class Conversation(Base):
    """Conversation session between customer and AI."""
    __tablename__ = "conversations"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Keys
    customer_id = Column(String(32), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core Fields
    channel = Column(SQLEnum(ChannelType), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Statistics
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="conversation")

    __table_args__ = (
        Index("idx_conversation_customer_channel", "customer_id", "channel"),
        Index("idx_conversation_status", "status"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, customer_id={self.customer_id}, channel={self.channel})>"


# ============================================================================
# MESSAGE MODEL
# ============================================================================

class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Keys
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(32), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Content
    content = Column(Text, nullable=False)
    sender = Column(String(50), nullable=False)  # 'customer' or 'agent'
    channel = Column(SQLEnum(ChannelType), nullable=False, index=True)

    # AI Analysis
    sentiment = Column(Float, nullable=True, index=True)  # 0.0-5.0
    sentiment_level = Column(SQLEnum(SentimentLevel), nullable=True, index=True)
    intent = Column(String(100), nullable=True, index=True)
    emotion_tags = Column(ARRAY(String), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Vector embedding for semantic search (if using pgvector)
    # embedding = Column(Vector(1536), nullable=True)  # Uncomment if using pgvector

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    customer = relationship("Customer", back_populates="messages")

    __table_args__ = (
        Index("idx_message_conversation_created", "conversation_id", "created_at"),
        Index("idx_message_sentiment", "sentiment"),
        Index("idx_message_intent", "intent"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, sender={self.sender})>"


# ============================================================================
# TICKET MODEL
# ============================================================================

class Ticket(Base):
    """Support ticket for tracking issues."""
    __tablename__ = "tickets"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Keys
    customer_id = Column(String(32), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    # Core Fields
    issue = Column(Text, nullable=False)
    priority = Column(SQLEnum(PriorityLevel), default=PriorityLevel.MEDIUM, nullable=False, index=True)
    channel = Column(SQLEnum(ChannelType), nullable=False, index=True)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)

    # SLA Management
    sla_minutes = Column(Integer, nullable=False)  # Based on priority
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Escalation Info
    escalated = Column(Boolean, default=False, index=True)
    escalation_reason = Column(Text, nullable=True)
    assigned_team = Column(String(100), nullable=True)

    # Metadata
    resolution_notes = Column(Text, nullable=True)
    response_count = Column(Integer, default=0)

    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    conversation = relationship("Conversation", back_populates="tickets")
    escalations = relationship("Escalation", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ticket_customer_status", "customer_id", "status"),
        Index("idx_ticket_priority_created", "priority", "created_at"),
        Index("idx_ticket_sla", "created_at", "sla_minutes"),
    )

    def __repr__(self):
        return f"<Ticket(id={self.id}, customer_id={self.customer_id}, status={self.status})>"


# ============================================================================
# ESCALATION MODEL
# ============================================================================

class Escalation(Base):
    """Escalation record for human handoff."""
    __tablename__ = "escalations"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Keys
    ticket_id = Column(String(32), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Escalation Details
    reason = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    assigned_team = Column(String(100), nullable=False, index=True)
    priority = Column(SQLEnum(PriorityLevel), nullable=False, index=True)

    # SLA Management
    sla_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True, index=True)

    # Status
    status = Column(String(50), default="open", nullable=False, index=True)
    acknowledgment_time = Column(DateTime, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="escalations")

    __table_args__ = (
        Index("idx_escalation_team_priority", "assigned_team", "priority"),
        Index("idx_escalation_created_resolved", "created_at", "resolved_at"),
    )

    def __repr__(self):
        return f"<Escalation(id={self.id}, ticket_id={self.ticket_id}, category={self.category})>"


# ============================================================================
# KNOWLEDGE BASE MODEL
# ============================================================================

class KnowledgeBase(Base):
    """Product documentation and FAQ entries."""
    __tablename__ = "knowledge_base"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Content
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author = Column(String(255), nullable=True)

    # Search & Relevance
    keywords = Column(ARRAY(String), nullable=True, index=True)
    usage_count = Column(Integer, default=0)

    # Vector embedding for semantic search (if using pgvector)
    # embedding = Column(Vector(1536), nullable=True)  # Uncomment if using pgvector

    __table_args__ = (
        Index("idx_kb_category_title", "category", "title"),
        Index("idx_kb_keywords", "keywords"),
    )

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title={self.title}, category={self.category})>"


# ============================================================================
# SENTIMENT TREND MODEL
# ============================================================================

class SentimentTrend(Base):
    """Customer sentiment trend tracking."""
    __tablename__ = "sentiment_trends"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key
    customer_id = Column(String(32), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sentiment History
    sentiment_values = Column(ARRAY(Float), nullable=False)  # Last N sentiment scores
    average_sentiment = Column(Float, nullable=False)
    trend = Column(String(50), nullable=False)  # improving, stable, declining

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_sentiment_customer_updated", "customer_id", "updated_at"),
    )

    def __repr__(self):
        return f"<SentimentTrend(customer_id={self.customer_id}, trend={self.trend})>"


# ============================================================================
# RESPONSE TEMPLATE MODEL
# ============================================================================

class ResponseTemplate(Base):
    """Channel-specific response templates."""
    __tablename__ = "response_templates"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Template Info
    name = Column(String(255), nullable=False, index=True)
    channel = Column(SQLEnum(ChannelType), nullable=False, index=True)
    intent = Column(String(100), nullable=True, index=True)

    # Template Content
    template_text = Column(Text, nullable=False)
    variables = Column(ARRAY(String), nullable=True)  # {{variable_names}}

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True, index=True)

    __table_args__ = (
        Index("idx_template_channel_intent", "channel", "intent"),
        Index("idx_template_active", "active"),
    )

    def __repr__(self):
        return f"<ResponseTemplate(name={self.name}, channel={self.channel})>"


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

class AuditLog(Base):
    """Audit trail for all important operations."""
    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Audit Fields
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(32), nullable=False, index=True)

    # Change Details
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Context
    actor = Column(String(255), nullable=True)  # User or system
    reason = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_created", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog(action={self.action}, entity_type={self.entity_type})>"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def init_db(engine):
    """Initialize all database tables."""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all database tables (for development/testing only)."""
    Base.metadata.drop_all(engine)


# ============================================================================
# DATABASE RELATIONSHIPS SUMMARY
# ============================================================================

"""
Entity Relationship Diagram:

Customer (1) ──→ (Many) Conversation
  │
  ├──→ (Many) Ticket
  │     │
  │     └──→ (Many) Escalation
  │
  ├──→ (Many) Message
  │
  └──→ (1) SentimentTrend


Conversation (1) ──→ (Many) Message
  │
  └──→ (Many) Ticket


Message:
  - Links Conversation & Customer
  - Stores AI analysis (sentiment, intent, emotions)
  - Indexed for efficient queries


KnowledgeBase:
  - Stores product documentation
  - Used by search tools
  - Tracks usage for analytics


ResponseTemplate:
  - Stores channel-specific templates
  - Used for response formatting


AuditLog:
  - Tracks all important operations
  - Supports compliance & debugging
"""
