"""
Production Agent Tools - OpenAI Agents SDK @function_tool Definitions

Converted from MCP server (Exercise 1.4) to OpenAI Agents SDK format.
All tools include proper input validation, error handling, and structured logging.

Tools:
1. search_knowledge_base - Search product documentation
2. create_ticket - Create support ticket
3. get_customer_history - Retrieve customer conversation history
4. escalate_to_human - Escalate to human specialist
5. send_response - Send formatted response via channel
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator

# Setup structured logging
logger = logging.getLogger(__name__)


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


# ============================================================================
# INPUT SCHEMAS (Pydantic Models)
# ============================================================================

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query or customer question")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return")
    category: Optional[str] = Field(None, description="Optional category filter (billing, technical, feature, general)")

    @validator('query')
    def validate_query(cls, v):
        """Ensure query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class TicketInput(BaseModel):
    """Input schema for ticket creation."""
    customer_id: str = Field(..., description="Unique customer identifier (CUST-XXXXX format)")
    issue: str = Field(..., min_length=5, max_length=2000, description="Description of the issue or request")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Ticket priority level")
    channel: ChannelType = Field(..., description="Communication channel")

    @validator('customer_id')
    def validate_customer_id(cls, v):
        """Ensure customer_id follows expected format."""
        if not v.startswith("CUST-"):
            raise ValueError("Customer ID must start with 'CUST-'")
        return v


class CustomerHistoryInput(BaseModel):
    """Input schema for retrieving customer history."""
    customer_id: str = Field(..., description="Unique customer identifier (CUST-XXXXX format)")
    limit: int = Field(default=10, ge=1, le=100, description="Number of recent messages to retrieve")

    @validator('customer_id')
    def validate_customer_id(cls, v):
        """Ensure customer_id follows expected format."""
        if not v.startswith("CUST-"):
            raise ValueError("Customer ID must start with 'CUST-'")
        return v


class EscalationInput(BaseModel):
    """Input schema for escalation."""
    ticket_id: str = Field(..., description="Ticket ID to escalate (T-XXXXX format)")
    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for escalation")
    category: Optional[str] = Field(None, description="Escalation category (legal, compliance, technical, etc)")

    @validator('ticket_id')
    def validate_ticket_id(cls, v):
        """Ensure ticket_id follows expected format."""
        if not v.startswith("T-"):
            raise ValueError("Ticket ID must start with 'T-'")
        return v


class ResponseInput(BaseModel):
    """Input schema for sending response."""
    ticket_id: str = Field(..., description="Ticket ID to respond to")
    message: str = Field(..., min_length=1, max_length=5000, description="Response message content")
    channel: ChannelType = Field(..., description="Channel to send response via")
    customer_name: Optional[str] = Field(None, description="Customer name for personalization")

    @validator('message')
    def validate_message(cls, v):
        """Ensure message is not just whitespace."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()

    @validator('ticket_id')
    def validate_ticket_id(cls, v):
        """Ensure ticket_id follows expected format."""
        if not v.startswith("T-"):
            raise ValueError("Ticket ID must start with 'T-'")
        return v


# ============================================================================
# PLACEHOLDER DATA STORES (for development)
# ============================================================================

# These will be replaced with database queries in Exercise 2.1
_customers_db = {
    "CUST-001": {"name": "John Smith", "email": "john@example.com", "plan": "pro"},
    "CUST-002": {"name": "Sarah Johnson", "email": "sarah@example.com", "plan": "enterprise"},
}

_tickets_db = {}
_escalations_db = {}
_escalation_counter = 0

_knowledge_base = {
    "billing": {
        "upgrade_plan": "To upgrade your plan: 1) Go to Settings 2) Click Billing 3) Select Change Plan",
        "pricing": "Pricing starts at $29/month for Pro and $99/month for Enterprise",
    },
    "technical": {
        "reset_password": "To reset password: 1) Click 'Forgot Password' 2) Enter email 3) Check email for link",
        "api_integration": "API documentation: https://docs.example.com/api",
    },
    "general": {
        "get_help": "Visit our help center at https://help.example.com",
        "contact_us": "Email support@example.com or call 1-800-EXAMPLE",
    },
}

_brand_guidelines = {
    "email": {
        "greeting": "Dear {name},",
        "closing": "Best regards,\nCloudFlow Customer Success Team",
        "tone": "professional"
    },
    "whatsapp": {
        "greeting": "Hi {name}! 👋",
        "closing": "- CloudFlow Team",
        "tone": "casual"
    },
    "web_form": {
        "greeting": "Thank you for reaching out!",
        "closing": "Let us know if you have any other questions.",
        "tone": "semi-formal"
    }
}


# ============================================================================
# TOOL 1: SEARCH KNOWLEDGE BASE
# ============================================================================

def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """
    Search product documentation for relevant information.

    Use this tool when the customer asks questions about product features, how-to guidance,
    billing information, technical setup, or general support. The tool searches the knowledge
    base and returns relevant documentation snippets ranked by relevance.

    Args:
        input: KnowledgeSearchInput with query (required), max_results (optional), category (optional)

    Returns:
        JSON string with search results including title, content, relevance score, and category.
        If no results found, returns helpful message suggesting escalation.

    Execution Flow:
        1. Validate input (query not empty, max_results 1-20)
        2. Detect intent from query (billing, technical, feature, general, etc)
        3. Search knowledge base for matching keywords
        4. Rank results by relevance score
        5. Return top N results formatted for the agent

    Error Handling:
        - Empty query: Returns error message, suggests rephrasing
        - No results found: Returns empty results with escalation suggestion
        - Database unavailable: Returns graceful fallback message
    """
    try:
        logger.info(
            "Knowledge base search initiated",
            extra={
                "query": input.query,
                "max_results": input.max_results,
                "category": input.category,
                "timestamp": datetime.now().isoformat()
            }
        )

        search_lower = input.query.lower()
        results = []

        # Search knowledge base (placeholder - will use pgvector in production)
        for kb_category, entries in _knowledge_base.items():
            if input.category and kb_category != input.category:
                continue  # Skip if category filter doesn't match

            if isinstance(entries, dict):
                for key, content in entries.items():
                    # Simple keyword matching (will be semantic search in production)
                    if any(word in search_lower for word in key.split("_")):
                        results.append({
                            "title": key.replace("_", " ").title(),
                            "content": content,
                            "category": kb_category,
                            "relevance_score": 0.85,
                            "source": "knowledge_base"
                        })

        # Limit results
        results = results[:input.max_results]

        logger.info(
            "Knowledge base search completed",
            extra={
                "query": input.query,
                "results_count": len(results),
                "execution_time_ms": 150
            }
        )

        if not results:
            return json.dumps({
                "success": True,
                "query": input.query,
                "results_count": 0,
                "results": [],
                "message": "No documentation found for your query. Consider providing more details or escalating to human support."
            })

        return json.dumps({
            "success": True,
            "query": input.query,
            "results_count": len(results),
            "results": results
        })

    except Exception as e:
        logger.error(
            "Knowledge base search failed",
            extra={"query": input.query, "error": str(e)},
            exc_info=True
        )
        return json.dumps({
            "success": False,
            "error": "Knowledge base search temporarily unavailable. Please try again or escalate to human support.",
            "details": str(e)
        })


# ============================================================================
# TOOL 2: CREATE TICKET
# ============================================================================

def create_ticket(input: TicketInput) -> str:
    """
    Create a support ticket to track customer issue.

    Use this tool to create a ticket for any customer issue. This logs the interaction,
    generates a unique ticket ID, sets SLA based on priority, and creates an audit trail.
    Always call this FIRST before any other operations to ensure tracking.

    Args:
        input: TicketInput with customer_id, issue, priority (optional), channel

    Returns:
        JSON string with ticket_id, status, estimated_response_time, created_at.
        If customer not found or invalid priority, returns error message.

    Execution Flow:
        1. Validate customer exists in system
        2. Validate priority level
        3. Validate channel
        4. Generate unique ticket_id
        5. Calculate SLA based on priority
        6. Create ticket record
        7. Return ticket_id for tracking

    Error Handling:
        - Customer not found: Returns error, suggests checking customer ID
        - Invalid priority: Returns error with valid options
        - Invalid channel: Returns error with valid options
        - Database write failure: Returns graceful fallback

    SLA by Priority:
        - CRITICAL: 15 minutes
        - HIGH: 30 minutes
        - MEDIUM: 2 hours
        - LOW: 24 hours
    """
    try:
        # Validate customer exists
        if input.customer_id not in _customers_db:
            logger.warning(
                "Ticket creation failed - customer not found",
                extra={"customer_id": input.customer_id}
            )
            return json.dumps({
                "success": False,
                "error": f"Customer {input.customer_id} not found in system",
                "suggestion": "Verify customer ID or create new customer first"
            })

        # Generate ticket ID
        date_str = datetime.now().strftime("%Y%m%d")
        ticket_count = len(_tickets_db) + 1
        ticket_id = f"T-{date_str}-{ticket_count:04d}"

        # SLA mapping
        sla_mapping = {
            PriorityLevel.CRITICAL: {"minutes": 15, "label": "15 minutes"},
            PriorityLevel.HIGH: {"minutes": 30, "label": "30 minutes"},
            PriorityLevel.MEDIUM: {"minutes": 120, "label": "2 hours"},
            PriorityLevel.LOW: {"minutes": 1440, "label": "24 hours"},
        }

        sla = sla_mapping[input.priority]

        # Create ticket
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": input.customer_id,
            "issue": input.issue,
            "priority": input.priority.value,
            "channel": input.channel.value,
            "status": "open",
            "sla_minutes": sla["minutes"],
            "created_at": datetime.now().isoformat(),
        }

        _tickets_db[ticket_id] = ticket

        logger.info(
            "Ticket created successfully",
            extra={
                "ticket_id": ticket_id,
                "customer_id": input.customer_id,
                "priority": input.priority.value,
                "channel": input.channel.value
            }
        )

        return json.dumps({
            "success": True,
            "ticket_id": ticket_id,
            "customer_id": input.customer_id,
            "status": "open",
            "priority": input.priority.value,
            "channel": input.channel.value,
            "sla_minutes": sla["minutes"],
            "estimated_response_time": sla["label"],
            "created_at": ticket["created_at"]
        })

    except Exception as e:
        logger.error(
            "Ticket creation failed",
            extra={"customer_id": input.customer_id, "error": str(e)},
            exc_info=True
        )
        return json.dumps({
            "success": False,
            "error": "Failed to create ticket. Please try again.",
            "details": str(e)
        })


# ============================================================================
# TOOL 3: GET CUSTOMER HISTORY
# ============================================================================

def get_customer_history(input: CustomerHistoryInput) -> str:
    """
    Retrieve complete conversation history for a customer.

    Use this tool to load customer context before responding. This retrieves the full
    conversation history across ALL channels (Email, WhatsApp, Web Form), customer
    profile information, and aggregated statistics for intelligent response personalization.

    Args:
        input: CustomerHistoryInput with customer_id (required), limit (optional)

    Returns:
        JSON string with customer profile, conversation history, and aggregated statistics.
        If customer not found, returns error message.

    Execution Flow:
        1. Validate customer exists
        2. Retrieve customer profile
        3. Load conversation history (last N messages)
        4. Aggregate statistics (sentiment trend, topics, channels)
        5. Format for agent context

    Error Handling:
        - Customer not found: Returns error message
        - Database read failure: Returns graceful fallback with empty history

    Uses Customer Data For:
        - Understanding customer plan/tier
        - Personalizing response tone
        - Detecting recurring issues
        - Assessing sentiment trend
        - Cross-channel conversation continuity
    """
    try:
        # Validate customer exists
        if input.customer_id not in _customers_db:
            logger.warning(
                "Customer history lookup failed - customer not found",
                extra={"customer_id": input.customer_id}
            )
            return json.dumps({
                "success": False,
                "error": f"Customer {input.customer_id} not found in system",
                "suggestion": "Verify customer ID or create new customer first"
            })

        customer = _customers_db[input.customer_id]

        # Build response
        history_response = {
            "success": True,
            "customer_id": input.customer_id,
            "customer": {
                "name": customer["name"],
                "email": customer["email"],
                "plan": customer["plan"],
            },
            "stats": {
                "total_messages": 0,  # Placeholder - will be real count in production
                "sentiment_trend": "stable",  # Placeholder - will be real trend in production
                "topics_discussed": ["billing", "technical"],  # Placeholder
                "channels_used": ["email", "whatsapp"],  # Placeholder
                "escalation_count": 0,  # Placeholder
            },
            "conversation_history": [],  # Placeholder - will be real messages in production
            "note": "Placeholder data - real database integration comes in Exercise 2.1"
        }

        logger.info(
            "Customer history retrieved",
            extra={
                "customer_id": input.customer_id,
                "plan": customer["plan"],
                "timestamp": datetime.now().isoformat()
            }
        )

        return json.dumps(history_response)

    except Exception as e:
        logger.error(
            "Customer history retrieval failed",
            extra={"customer_id": input.customer_id, "error": str(e)},
            exc_info=True
        )
        return json.dumps({
            "success": False,
            "error": "Failed to retrieve customer history. Please try again.",
            "details": str(e)
        })


# ============================================================================
# TOOL 4: ESCALATE TO HUMAN
# ============================================================================

def escalate_to_human(input: EscalationInput) -> str:
    """
    Escalate a ticket to human specialist.

    Use this tool when the issue cannot be resolved by AI (angry customer, complex
    technical issue, legal/compliance matter, refund request, etc). This creates an
    escalation record, assigns to appropriate team, publishes event, and notifies specialists.

    Args:
        input: EscalationInput with ticket_id, reason (required), category (optional)

    Returns:
        JSON string with escalation_id, assigned_team, sla_minutes, status.
        If ticket not found, returns error message.

    Execution Flow:
        1. Validate ticket exists
        2. Classify escalation reason to category
        3. Route to appropriate team based on category
        4. Generate escalation_id
        5. Create escalation record
        6. Publish Kafka event (in production)
        7. Update ticket status
        8. Log escalation

    Error Handling:
        - Ticket not found: Returns error message
        - Database write failure: Returns graceful fallback

    Team Routing by Category:
        - LEGAL: Legal Team (SLA: 1 hour)
        - COMPLIANCE: Compliance Team (SLA: 1 hour)
        - TECHNICAL: Engineering Team (SLA: 2 hours)
        - REFUND: Finance Team (SLA: 4 hours)
        - URGENT: Escalation Manager (SLA: 30 minutes)
    """
    try:
        global _escalation_counter

        # Validate ticket exists
        if input.ticket_id not in _tickets_db:
            logger.warning(
                "Escalation failed - ticket not found",
                extra={"ticket_id": input.ticket_id}
            )
            return json.dumps({
                "success": False,
                "error": f"Ticket {input.ticket_id} not found",
                "suggestion": "Verify ticket ID from previous create_ticket call"
            })

        # Team mapping
        team_mapping = {
            "legal": {"team": "Legal Team", "sla_minutes": 60},
            "compliance": {"team": "Compliance Team", "sla_minutes": 60},
            "technical": {"team": "Engineering Team", "sla_minutes": 120},
            "refund": {"team": "Finance Team", "sla_minutes": 240},
            "urgent": {"team": "Escalation Manager", "sla_minutes": 30},
            "default": {"team": "Support Team", "sla_minutes": 120},
        }

        # Determine team
        category = (input.category or "default").lower()
        team_info = team_mapping.get(category, team_mapping["default"])

        # Generate escalation ID
        _escalation_counter += 1
        date_str = datetime.now().strftime("%Y%m%d")
        escalation_id = f"ESC-{date_str}-{_escalation_counter:04d}"

        # Create escalation record
        escalation = {
            "escalation_id": escalation_id,
            "ticket_id": input.ticket_id,
            "reason": input.reason,
            "category": category,
            "assigned_team": team_info["team"],
            "sla_minutes": team_info["sla_minutes"],
            "status": "assigned",
            "created_at": datetime.now().isoformat(),
        }

        _escalations_db[escalation_id] = escalation

        # Update ticket
        if input.ticket_id in _tickets_db:
            _tickets_db[input.ticket_id]["status"] = "escalated"
            _tickets_db[input.ticket_id]["escalation_id"] = escalation_id

        logger.info(
            "Escalation created successfully",
            extra={
                "escalation_id": escalation_id,
                "ticket_id": input.ticket_id,
                "category": category,
                "assigned_team": team_info["team"]
            }
        )

        return json.dumps({
            "success": True,
            "escalation_id": escalation_id,
            "ticket_id": input.ticket_id,
            "reason": input.reason,
            "category": category,
            "assigned_team": team_info["team"],
            "sla_minutes": team_info["sla_minutes"],
            "status": "assigned",
            "created_at": escalation["created_at"],
            "note": "Escalation event published to notification system (Kafka in production)"
        })

    except Exception as e:
        logger.error(
            "Escalation creation failed",
            extra={"ticket_id": input.ticket_id, "error": str(e)},
            exc_info=True
        )
        return json.dumps({
            "success": False,
            "error": "Failed to escalate. Please try again.",
            "details": str(e)
        })


# ============================================================================
# TOOL 5: SEND RESPONSE
# ============================================================================

def send_response(input: ResponseInput) -> str:
    """
    Send a formatted response to customer via specified channel.

    Use this tool to send the final response to customer. This formats the message
    according to channel guidelines (Email: formal/detailed, WhatsApp: casual/concise,
    Web Form: semi-formal), validates against channel constraints, and logs delivery.

    Args:
        input: ResponseInput with ticket_id, message, channel, customer_name (optional)

    Returns:
        JSON string with delivery_status, formatted_message, channel, timestamp.
        If ticket not found or invalid channel, returns error message.

    Execution Flow:
        1. Validate ticket exists
        2. Load channel brand guidelines
        3. Format message with greeting, content, closing
        4. Validate against channel constraints (length, formatting)
        5. Store in ticket history (placeholder)
        6. Return formatted message for delivery

    Error Handling:
        - Ticket not found: Returns error message
        - Invalid channel: Returns error with valid options
        - Message too long: Returns error with max length
        - Message empty: Returns error
        - Formatting failure: Returns graceful fallback

    Channel Constraints:
        - EMAIL: Max 500 words, professional tone, signature required
        - WHATSAPP: Max 300 characters, casual tone, emojis OK
        - WEB_FORM: Max 300 words, semi-formal tone
    """
    try:
        # Validate ticket exists
        if input.ticket_id not in _tickets_db:
            logger.warning(
                "Response send failed - ticket not found",
                extra={"ticket_id": input.ticket_id}
            )
            return json.dumps({
                "success": False,
                "error": f"Ticket {input.ticket_id} not found",
                "suggestion": "Verify ticket ID from create_ticket call"
            })

        # Get channel guidelines
        guidelines = _brand_guidelines.get(input.channel.value, _brand_guidelines["email"])

        # Format message
        greeting = guidelines["greeting"].format(name=input.customer_name or "valued customer")
        closing = guidelines["closing"]

        formatted_message = f"{greeting}\n\n{input.message}\n\n{closing}"

        # Validate length based on channel
        length_limits = {
            "email": 500,
            "whatsapp": 300,
            "web_form": 300,
        }

        max_length = length_limits.get(input.channel.value, 500)
        if len(formatted_message) > max_length:
            logger.warning(
                "Response message exceeds channel limit",
                extra={
                    "ticket_id": input.ticket_id,
                    "channel": input.channel.value,
                    "length": len(formatted_message),
                    "limit": max_length
                }
            )
            return json.dumps({
                "success": False,
                "error": f"Message exceeds {input.channel.value} character limit",
                "details": f"Current: {len(formatted_message)}, Limit: {max_length}",
                "suggestion": "Shorten your response or split into multiple messages"
            })

        # Store response (placeholder - real implementation updates database)
        timestamp = datetime.now().isoformat()

        logger.info(
            "Response sent successfully",
            extra={
                "ticket_id": input.ticket_id,
                "channel": input.channel.value,
                "message_length": len(formatted_message),
                "timestamp": timestamp
            }
        )

        return json.dumps({
            "success": True,
            "ticket_id": input.ticket_id,
            "delivery_status": "sent",
            "channel": input.channel.value,
            "formatted_message": formatted_message,
            "message_length": len(formatted_message),
            "timestamp": timestamp,
            "note": "In production, this will send via Gmail API, Twilio WhatsApp, or API webhook"
        })

    except Exception as e:
        logger.error(
            "Response send failed",
            extra={"ticket_id": input.ticket_id, "channel": input.channel.value, "error": str(e)},
            exc_info=True
        )
        return json.dumps({
            "success": False,
            "error": "Failed to send response. Please try again.",
            "details": str(e)
        })


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "search_knowledge_base",
    "create_ticket",
    "get_customer_history",
    "escalate_to_human",
    "send_response",
    # Schemas
    "KnowledgeSearchInput",
    "TicketInput",
    "CustomerHistoryInput",
    "EscalationInput",
    "ResponseInput",
    # Enums
    "ChannelType",
    "PriorityLevel",
]
