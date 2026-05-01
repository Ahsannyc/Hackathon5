"""
Agent Module - Core AI Employee implementation

Exercise 2.3+: OpenAI Agents SDK with Cohere Integration + Enhanced Memory Management
Provides production-grade agent with:
- CustomerSuccessAgent: Multi-channel AI employee with memory management
- Memory: Dedicated memory classes (ConversationMemory, CustomerContextMemory)
- Tools: 5 production tools for customer support
- System Prompt: Production-grade multi-channel prompt
- Safety: 10-iteration limit to prevent infinite loops
"""

# Lazy imports to prevent circular dependencies
def __getattr__(name):
    """Lazy loading to prevent circular imports."""
    if name == "CustomerSuccessAgent":
        from .customer_success_agent import CustomerSuccessAgent
        return CustomerSuccessAgent
    elif name == "create_customer_success_agent":
        from .customer_success_agent import create_customer_success_agent
        return create_customer_success_agent
    elif name == "ConversationMemory":
        from .memory import ConversationMemory
        return ConversationMemory
    elif name == "CustomerContextMemory":
        from .memory import CustomerContextMemory
        return CustomerContextMemory
    elif name == "Message":
        from .memory import Message
        return Message
    elif name == "CustomerContext":
        from .memory import CustomerContext
        return CustomerContext
    elif name == "search_knowledge_base":
        from .tools import search_knowledge_base
        return search_knowledge_base
    elif name == "create_ticket":
        from .tools import create_ticket
        return create_ticket
    elif name == "get_customer_history":
        from .tools import get_customer_history
        return get_customer_history
    elif name == "escalate_to_human":
        from .tools import escalate_to_human
        return escalate_to_human
    elif name == "send_response":
        from .tools import send_response
        return send_response
    elif name == "KnowledgeSearchInput":
        from .tools import KnowledgeSearchInput
        return KnowledgeSearchInput
    elif name == "TicketInput":
        from .tools import TicketInput
        return TicketInput
    elif name == "CustomerHistoryInput":
        from .tools import CustomerHistoryInput
        return CustomerHistoryInput
    elif name == "EscalationInput":
        from .tools import EscalationInput
        return EscalationInput
    elif name == "ResponseInput":
        from .tools import ResponseInput
        return ResponseInput
    elif name == "CUSTOMER_SUCCESS_SYSTEM_PROMPT":
        from .prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        return CUSTOMER_SUCCESS_SYSTEM_PROMPT
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Explicit exports for static analysis
__all__ = [
    # Agent
    "CustomerSuccessAgent",
    "create_customer_success_agent",

    # Memory
    "ConversationMemory",
    "CustomerContextMemory",
    "Message",
    "CustomerContext",

    # Tools
    "search_knowledge_base",
    "create_ticket",
    "get_customer_history",
    "escalate_to_human",
    "send_response",

    # Tool Schemas
    "KnowledgeSearchInput",
    "TicketInput",
    "CustomerHistoryInput",
    "EscalationInput",
    "ResponseInput",

    # System Prompt
    "CUSTOMER_SUCCESS_SYSTEM_PROMPT",
]
