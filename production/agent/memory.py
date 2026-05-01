"""
Agent Memory Management - Separate memory logic for conversation and customer context

This module provides dedicated memory management classes to decouple memory handling
from the main agent logic. Supports:
- ConversationMemory: Tracks conversation history per session
- CustomerContextMemory: Stores customer context across multiple conversations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Message:
    """Single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    tools_used: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tools_used": self.tools_used or [],
            "metadata": self.metadata or {},
        }


@dataclass
class CustomerContext:
    """Customer information persisted across conversations."""
    customer_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    plan: Optional[str] = None
    total_conversations: int = 0
    last_interaction: Optional[datetime] = None
    sentiment_history: List[str] = field(default_factory=list)
    escalation_count: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "plan": self.plan,
            "total_conversations": self.total_conversations,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "sentiment_history": self.sentiment_history,
            "escalation_count": self.escalation_count,
            "preferences": self.preferences,
        }


# ============================================================================
# CONVERSATION MEMORY
# ============================================================================

class ConversationMemory:
    """
    Manages conversation history for a single conversation session.

    Supports:
    - Append messages (user/assistant)
    - Retrieve conversation history
    - Get context window (last N messages)
    - Clear history
    - Search messages by content
    """

    def __init__(self, conversation_id: str, max_size: int = 100):
        """
        Initialize conversation memory.

        Args:
            conversation_id: Unique conversation identifier
            max_size: Maximum messages to keep (older messages pruned)
        """
        self.conversation_id = conversation_id
        self.max_size = max_size
        self.messages: List[Message] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        logger.debug(f"ConversationMemory initialized: {conversation_id}")

    def add_message(
        self,
        role: str,
        content: str,
        tools_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            role: "user" or "assistant"
            content: Message content
            tools_used: List of tools used (for assistant messages)
            metadata: Additional metadata
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            tools_used=tools_used,
            metadata=metadata,
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

        # Prune old messages if exceeding max_size
        if len(self.messages) > self.max_size:
            removed = self.messages.pop(0)
            logger.debug(f"Pruned old message: {removed.timestamp}")

        logger.debug(f"Message added to {self.conversation_id}: {role}")

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in conversation."""
        return [msg.to_dict() for msg in self.messages]

    def get_context_window(self, window_size: int = 10) -> List[Dict[str, Any]]:
        """
        Get last N messages for context window.

        Args:
            window_size: Number of recent messages to return

        Returns:
            List of recent messages (oldest to newest)
        """
        return [msg.to_dict() for msg in self.messages[-window_size:]]

    def get_last_message(self, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get last message, optionally filtered by role.

        Args:
            role: Filter by role (e.g., "user", "assistant") or None for any

        Returns:
            Last matching message or None
        """
        if not self.messages:
            return None

        filtered = [msg for msg in reversed(self.messages) if role is None or msg.role == role]
        return filtered[0].to_dict() if filtered else None

    def search_messages(self, query: str) -> List[Dict[str, Any]]:
        """
        Search messages by content.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching messages
        """
        query_lower = query.lower()
        return [
            msg.to_dict()
            for msg in self.messages
            if query_lower in msg.content.lower()
        ]

    def get_message_count(self, role: Optional[str] = None) -> int:
        """
        Get message count, optionally filtered by role.

        Args:
            role: Filter by role or None for total

        Returns:
            Message count
        """
        if role is None:
            return len(self.messages)
        return sum(1 for msg in self.messages if msg.role == role)

    def get_tools_used(self) -> List[str]:
        """Get list of all tools used in this conversation."""
        tools = set()
        for msg in self.messages:
            if msg.tools_used:
                tools.update(msg.tools_used)
        return sorted(list(tools))

    def clear(self) -> None:
        """Clear all messages from conversation."""
        self.messages.clear()
        self.updated_at = datetime.utcnow()
        logger.info(f"Conversation memory cleared: {self.conversation_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation memory to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages),
            "user_message_count": self.get_message_count("user"),
            "assistant_message_count": self.get_message_count("assistant"),
            "tools_used": self.get_tools_used(),
            "messages": self.get_messages(),
        }


# ============================================================================
# CUSTOMER CONTEXT MEMORY
# ============================================================================

class CustomerContextMemory:
    """
    Manages customer context across multiple conversations.

    Persists customer information, sentiment history, escalation patterns,
    and preferences across conversation sessions.
    """

    def __init__(self):
        """Initialize customer context memory."""
        self.customers: Dict[str, CustomerContext] = {}
        logger.debug("CustomerContextMemory initialized")

    def get_or_create(self, customer_id: str) -> CustomerContext:
        """
        Get existing customer context or create new one.

        Args:
            customer_id: Unique customer identifier

        Returns:
            CustomerContext instance
        """
        if customer_id not in self.customers:
            self.customers[customer_id] = CustomerContext(customer_id=customer_id)
            logger.debug(f"Created new customer context: {customer_id}")
        return self.customers[customer_id]

    def update_customer(
        self,
        customer_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        plan: Optional[str] = None,
        **preferences
    ) -> CustomerContext:
        """
        Update customer information.

        Args:
            customer_id: Unique customer identifier
            name: Customer name
            email: Customer email
            phone: Customer phone
            plan: Customer plan/tier
            **preferences: Any additional preferences

        Returns:
            Updated CustomerContext
        """
        context = self.get_or_create(customer_id)

        if name:
            context.name = name
        if email:
            context.email = email
        if phone:
            context.phone = phone
        if plan:
            context.plan = plan

        context.preferences.update(preferences)
        logger.debug(f"Updated customer context: {customer_id}")

        return context

    def add_sentiment(self, customer_id: str, sentiment: str) -> None:
        """
        Add sentiment to customer history.

        Args:
            customer_id: Unique customer identifier
            sentiment: Sentiment value (e.g., "positive", "negative", "neutral")
        """
        context = self.get_or_create(customer_id)
        context.sentiment_history.append(sentiment)
        logger.debug(f"Added sentiment for {customer_id}: {sentiment}")

    def get_sentiment_summary(self, customer_id: str) -> Dict[str, int]:
        """
        Get sentiment distribution for customer.

        Args:
            customer_id: Unique customer identifier

        Returns:
            Dict with sentiment counts
        """
        context = self.get_or_create(customer_id)
        summary = {}
        for sentiment in context.sentiment_history:
            summary[sentiment] = summary.get(sentiment, 0) + 1
        return summary

    def record_conversation(self, customer_id: str) -> None:
        """
        Record a conversation for customer.

        Args:
            customer_id: Unique customer identifier
        """
        context = self.get_or_create(customer_id)
        context.total_conversations += 1
        context.last_interaction = datetime.utcnow()
        logger.debug(f"Recorded conversation for {customer_id}")

    def record_escalation(self, customer_id: str) -> None:
        """
        Record an escalation for customer.

        Args:
            customer_id: Unique customer identifier
        """
        context = self.get_or_create(customer_id)
        context.escalation_count += 1
        logger.debug(f"Recorded escalation for {customer_id}")

    def get_customer(self, customer_id: str) -> Optional[CustomerContext]:
        """
        Get customer context if exists.

        Args:
            customer_id: Unique customer identifier

        Returns:
            CustomerContext or None
        """
        return self.customers.get(customer_id)

    def get_all_customers(self) -> List[CustomerContext]:
        """Get all customer contexts."""
        return list(self.customers.values())

    def clear_customer(self, customer_id: str) -> None:
        """
        Clear customer context.

        Args:
            customer_id: Unique customer identifier
        """
        if customer_id in self.customers:
            del self.customers[customer_id]
            logger.info(f"Cleared customer context: {customer_id}")

    def clear_all(self) -> None:
        """Clear all customer contexts."""
        self.customers.clear()
        logger.info("Cleared all customer contexts")

    def to_dict(self) -> Dict[str, Any]:
        """Convert all customer contexts to dictionary."""
        return {
            "total_customers": len(self.customers),
            "customers": {cid: ctx.to_dict() for cid, ctx in self.customers.items()},
        }
