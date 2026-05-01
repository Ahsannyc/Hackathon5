"""
CloudFlow Customer Success AI - MCP Server
Exercise 1.4: Expose core_loop_with_memory as Model Context Protocol (MCP) server

MCP Server exposes 5 tools:
1. search_knowledge_base(query, max_results) - Search documentation
2. create_ticket(customer_id, issue, priority, channel) - Create support ticket
3. get_customer_history(customer_id) - Retrieve customer conversation history
4. escalate_to_human(ticket_id, reason) - Escalate to human specialist
5. send_response(ticket_id, message, channel) - Send formatted response

Install: pip install mcp
Run: python mcp_server.py
"""

import sys
import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add src/ to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core_loop_with_memory import CoreLoopWithMemory, ConversationMemory

# ============================================================================
# Channel Enum
# ============================================================================

class Channel(str, Enum):
    """Communication channels supported by CloudFlow."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


# ============================================================================
# Global State & MCP Server Initialization
# ============================================================================

# Initialize prototype once at startup
prototype = CoreLoopWithMemory("context")

# In-memory storage for tickets and escalations
tickets_db: Dict[str, Dict[str, Any]] = {}       # ticket_id -> ticket data
escalations_db: Dict[str, Dict[str, Any]] = {}   # escalation_id -> escalation data
escalation_counter = 0


# ============================================================================
# Tool Implementations
# ============================================================================

def search_knowledge_base(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the knowledge base for relevant documentation snippets.

    Args:
        query: Search query (customer question or issue description)
        max_results: Maximum number of results to return (default 5)

    Returns:
        Dict with 'success', 'results' (list of doc snippets), and 'count'

    When to use:
    - Customer asks a question: "How do I upgrade my plan?"
    - Need to find relevant documentation
    - Before responding to customer, search KB for matching content
    """

    if not query or not query.strip():
        return {
            "success": False,
            "error": "Query cannot be empty",
            "results": []
        }

    # Detect intent from query
    intent, confidence = prototype.detect_intent(query)

    # Search knowledge base using the prototype's method
    kb_match = prototype.search_knowledge_base(query, intent)

    results = []

    # Add primary KB match if found
    if kb_match:
        if isinstance(kb_match, dict):
            if "steps" in kb_match:
                results.append({
                    "type": "steps",
                    "issue": kb_match.get("issue", ""),
                    "steps": kb_match.get("steps", []),
                    "details": kb_match.get("details", "")
                })
            else:
                results.append({
                    "type": "documentation",
                    "content": kb_match
                })

    # Add secondary matches by searching knowledge_base dict directly
    kb = prototype.knowledge_base
    search_lower = query.lower()

    for category, entries in kb.items():
        if isinstance(entries, dict):
            for key, content in entries.items():
                if any(word in search_lower for word in key.split("_")):
                    if len(results) < max_results:
                        results.append({
                            "type": "category_match",
                            "category": category,
                            "key": key,
                            "content": content if isinstance(content, (str, dict)) else str(content)
                        })

    return {
        "success": True,
        "query": query,
        "detected_intent": intent,
        "intent_confidence": confidence,
        "results": results[:max_results],
        "count": len(results[:max_results])
    }


def create_ticket(customer_id: str, issue: str, priority: str,
                 channel: str) -> Dict[str, Any]:
    """
    Create a new support ticket for a customer.

    Args:
        customer_id: Unique customer identifier (CUST-NNNNN format)
        issue: Description of the issue/request
        priority: One of "low", "medium", "high", "critical"
        channel: Communication channel (email, whatsapp, web_form)

    Returns:
        Dict with ticket_id, status, estimated_response_time, created_at

    When to use:
    - Customer reports a new issue
    - Need to create a ticket for tracking
    - After determining priority, create ticket to track resolution
    """

    # Validate customer exists
    if customer_id not in prototype.memory.customers:
        return {
            "success": False,
            "error": f"Customer {customer_id} not found in system"
        }

    # Validate priority
    valid_priorities = ["low", "medium", "high", "critical"]
    if priority.lower() not in valid_priorities:
        return {
            "success": False,
            "error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        }

    # Validate channel
    try:
        Channel(channel.lower())
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid channel. Must be one of: {', '.join([c.value for c in Channel])}"
        }

    # Generate ticket ID
    ticket_id = prototype.generate_ticket_id()

    # Determine response time based on priority
    response_times = {
        "critical": "15 minutes",
        "high": "30 minutes",
        "medium": "2 hours",
        "low": "24 hours"
    }

    # Create ticket record
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority.lower(),
        "channel": channel.lower(),
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "responses": []
    }

    tickets_db[ticket_id] = ticket

    return {
        "success": True,
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "status": "open",
        "priority": priority.lower(),
        "channel": channel.lower(),
        "estimated_response_time": response_times[priority.lower()],
        "created_at": ticket["created_at"]
    }


def get_customer_history(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve complete conversation history for a customer across all channels.

    Args:
        customer_id: Unique customer identifier (CUST-NNNNN format)

    Returns:
        Dict with customer details, conversation history, and aggregated stats

    When to use:
    - Need context before responding to customer
    - Customer switches channels, retrieve full history
    - Determine if issue is recurring/related to previous interactions
    """

    # Get customer state from memory
    customer_state = prototype.memory.get_customer_state(customer_id)

    if not customer_state:
        return {
            "success": False,
            "error": f"Customer {customer_id} not found"
        }

    # Extract conversation history (last 10 messages)
    conversation_history = []
    for msg in customer_state.conversation_history[-10:]:
        conversation_history.append({
            "timestamp": msg.timestamp,
            "channel": msg.channel,
            "message": msg.message[:100] + "..." if len(msg.message) > 100 else msg.message,
            "sentiment": msg.sentiment,
            "intent": msg.intent,
            "escalation": msg.escalation,
            "escalation_reason": msg.escalation_reason
        })

    return {
        "success": True,
        "customer_id": customer_id,
        "customer_name": customer_state.customer_name,
        "customer_plan": customer_state.customer_plan,
        "email": customer_state.email,
        "phone": customer_state.phone,
        "stats": {
            "total_messages": customer_state.total_messages,
            "current_sentiment": customer_state.current_sentiment,
            "sentiment_trend": customer_state.sentiment_trend,
            "topics_discussed": customer_state.topics_discussed,
            "channels_used": customer_state.channels_used,
            "resolution_status": customer_state.resolution_status,
            "escalation_count": customer_state.escalation_count,
            "last_contact": customer_state.last_contact
        },
        "conversation_history": conversation_history,
        "context_summary": prototype.memory.get_conversation_context(customer_id)
    }


def escalate_to_human(ticket_id: str, reason: str) -> Dict[str, Any]:
    """
    Escalate a ticket to a human specialist.

    Args:
        ticket_id: The ticket ID to escalate (T20260401-NNNN format)
        reason: Reason for escalation (will classify to determine team)

    Returns:
        Dict with escalation_id, assigned_team, estimated_response, details

    When to use:
    - Angry customer that needs immediate attention
    - Technical issue beyond AI capability
    - Legal/compliance matters
    - Customer requests specific help
    """

    global escalation_counter

    # Validate ticket exists
    if ticket_id not in tickets_db:
        return {
            "success": False,
            "error": f"Ticket {ticket_id} not found"
        }

    # Detect escalation category from reason
    escalation_needed, escalation_category = prototype.detect_escalation_triggers(
        reason, 0.1, "general"
    )

    # Map escalation reason to team
    team_mapping = {
        "legal_triggers": "Legal Team",
        "compliance_triggers": "Compliance Team",
        "technical_triggers": "Technical Team",
        "angry_triggers": "Priority Support",
        "refund_triggers": "Finance Team",
        "data_loss_triggers": "Technical Recovery Team",
        "urgent_triggers": "Escalation Team"
    }

    assigned_team = team_mapping.get(escalation_category, "General Support")

    # Generate escalation ID
    escalation_counter += 1
    date_str = datetime.now().strftime("%Y%m%d")
    escalation_id = f"ESC-{date_str}-{escalation_counter:04d}"

    # Create escalation record
    escalation = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "category": escalation_category,
        "assigned_team": assigned_team,
        "created_at": datetime.now().isoformat(),
        "status": "assigned"
    }

    escalations_db[escalation_id] = escalation

    # Update ticket status
    if ticket_id in tickets_db:
        tickets_db[ticket_id]["status"] = "escalated"
        tickets_db[ticket_id]["escalation_id"] = escalation_id

    return {
        "success": True,
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "category": escalation_category,
        "assigned_team": assigned_team,
        "estimated_response": "15-30 minutes for priority customers, 1 hour for standard",
        "status": "assigned",
        "created_at": escalation["created_at"]
    }


def send_response(ticket_id: str, message: str, channel: str) -> Dict[str, Any]:
    """
    Send a formatted response to customer via specified channel.

    Args:
        ticket_id: Ticket ID to respond to (T20260401-NNNN format)
        message: Response message content
        channel: Channel to send via (email, whatsapp, web_form)

    Returns:
        Dict with delivery_status, channel, formatted_message, timestamp

    When to use:
    - Ready to send response to customer
    - Use brand guidelines to format message for channel
    - Track all responses in ticket history
    """

    # Validate ticket exists
    if ticket_id not in tickets_db:
        return {
            "success": False,
            "error": f"Ticket {ticket_id} not found"
        }

    # Validate channel
    try:
        channel_enum = Channel(channel.lower())
        channel_value = channel_enum.value
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid channel. Must be one of: {', '.join([c.value for c in Channel])}"
        }

    if not message or not message.strip():
        return {
            "success": False,
            "error": "Message cannot be empty"
        }

    # Get brand guidelines for this channel
    guidelines = prototype.brand_guidelines.get(channel_value, {})

    # Format message with brand voice
    greeting = guidelines.get("greeting", "Hi there!").format(name="Customer")
    closing = guidelines.get("closing", "Best regards,\nCloudFlow Team")

    formatted_message = f"{greeting}\n\n{message}\n\n{closing}"

    # Record response in ticket
    response_record = {
        "timestamp": datetime.now().isoformat(),
        "channel": channel_value,
        "message": message,
        "formatted_message": formatted_message
    }

    tickets_db[ticket_id]["responses"].append(response_record)
    tickets_db[ticket_id]["status"] = "responded"
    tickets_db[ticket_id]["last_response"] = response_record["timestamp"]

    return {
        "success": True,
        "ticket_id": ticket_id,
        "channel": channel_value,
        "delivery_status": "sent",
        "message_preview": message[:100] + "..." if len(message) > 100 else message,
        "formatted_message": formatted_message,
        "timestamp": response_record["timestamp"]
    }


# ============================================================================
# MCP Server Implementation
# ============================================================================

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent

    server = Server("cloudflow-customer-success")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available tools."""
        return [
            Tool(
                name="search_knowledge_base",
                description="Search the knowledge base for relevant documentation and troubleshooting steps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (customer question or issue description)"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="create_ticket",
                description="Create a new support ticket for a customer issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID in format CUST-NNNNN"
                        },
                        "issue": {
                            "type": "string",
                            "description": "Description of the issue or request"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Priority level of the ticket"
                        },
                        "channel": {
                            "type": "string",
                            "enum": ["email", "whatsapp", "web_form"],
                            "description": "Communication channel"
                        }
                    },
                    "required": ["customer_id", "issue", "priority", "channel"]
                }
            ),
            Tool(
                name="get_customer_history",
                description="Retrieve complete conversation history for a customer across all channels",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID in format CUST-NNNNN"
                        }
                    },
                    "required": ["customer_id"]
                }
            ),
            Tool(
                name="escalate_to_human",
                description="Escalate a ticket to a human specialist with appropriate team assignment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID in format T20260401-NNNN"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for escalation"
                        }
                    },
                    "required": ["ticket_id", "reason"]
                }
            ),
            Tool(
                name="send_response",
                description="Send a formatted response to customer via specified channel",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID in format T20260401-NNNN"
                        },
                        "message": {
                            "type": "string",
                            "description": "Response message content"
                        },
                        "channel": {
                            "type": "string",
                            "enum": ["email", "whatsapp", "web_form"],
                            "description": "Channel to send response via"
                        }
                    },
                    "required": ["ticket_id", "message", "channel"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Execute a tool and return results."""

        result = None

        try:
            if name == "search_knowledge_base":
                result = search_knowledge_base(
                    arguments.get("query", ""),
                    arguments.get("max_results", 5)
                )
            elif name == "create_ticket":
                result = create_ticket(
                    arguments.get("customer_id", ""),
                    arguments.get("issue", ""),
                    arguments.get("priority", ""),
                    arguments.get("channel", "")
                )
            elif name == "get_customer_history":
                result = get_customer_history(arguments.get("customer_id", ""))
            elif name == "escalate_to_human":
                result = escalate_to_human(
                    arguments.get("ticket_id", ""),
                    arguments.get("reason", "")
                )
            elif name == "send_response":
                result = send_response(
                    arguments.get("ticket_id", ""),
                    arguments.get("message", ""),
                    arguments.get("channel", "")
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

        except Exception as e:
            result = {"error": str(e)}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    MCP_AVAILABLE = True

except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  MCP package not found. Install with: pip install mcp")
    print("Running in test mode only.\n")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    if MCP_AVAILABLE:
        import sys
        from mcp.server.stdio import stdio_server
        from mcp.server import InitializationOptions

        print("🚀 CloudFlow Customer Success AI - MCP Server", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("Server starting...", file=sys.stderr)
        print("Available tools: 5 (search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response)", file=sys.stderr)
        print("\nWaiting for connections on stdio...\n", file=sys.stderr)

        async with stdio_server(server) as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name="cloudflow-customer-success",
                server_version="1.4.0",
                capabilities={}
            )
            await server.run(read_stream, write_stream, init_options)
    else:
        print("❌ MCP package not installed.")
        print("Install with: pip install mcp --quiet")
        print("\nTo test tools without MCP, run: python test_mcp_server.py")


if __name__ == "__main__":
    if MCP_AVAILABLE:
        asyncio.run(main())
    else:
        import sys
        print("MCP Server requires 'mcp' package.")
        print("Install: pip install mcp --quiet")
        print("Then run: python mcp_server.py")
        sys.exit(1)
