"""
Customer Success AI Agent - OpenAI Agents SDK with Cohere Integration

Exercise 2.3: Transforms the prototype into a production-grade Custom Agent
using the OpenAI Agents SDK with Cohere as the LLM provider.

This agent:
- Integrates the production system prompt from prompts.py
- Uses all 5 production tools from tools.py
- Handles multi-channel customer interactions (Email, WhatsApp, Web Form)
- Maintains conversation memory across channels
- Enforces strict workflow: create_ticket → get_history → search → send_response
- Properly escalates complex issues to human specialists
- Adapts responses per communication channel
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv

try:
    from agents import (
        Agent,
        AsyncOpenAI,
        OpenAIChatCompletionsModel,
        ModelSettings,
        enable_verbose_stdout_logging,
        function_tool,
    )
except ImportError:
    # Fallback if agents SDK not installed
    raise ImportError(
        "OpenAI Agents SDK required. Install with: pip install openai-agents"
    )

from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
)
from production.agent.memory import ConversationMemory, CustomerContextMemory
from production.database.schema import ChannelType

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Enable verbose logging for debugging (can be disabled in production)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
if DEBUG:
    enable_verbose_stdout_logging()

# Get Cohere API key from environment
COHERE_API_KEY = os.getenv("COHERE_KEY")
if not COHERE_API_KEY:
    raise ValueError(
        "COHERE_KEY is not set in .env. "
        "Please set COHERE_KEY with your Cohere API key."
    )

# Cohere API configuration
COHERE_BASE_URL = "https://api.cohere.com/v1"
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r-plus")  # Recommended models: command-r-plus, command-r

logger.info(f"Using Cohere model: {COHERE_MODEL}")

# ============================================================================
# COHERE CLIENT INITIALIZATION
# ============================================================================


def create_cohere_client() -> OpenAIChatCompletionsModel:
    """
    Initialize Cohere client using OpenAI-compatible API.

    Cohere provides an OpenAI-compatible API endpoint at https://api.cohere.com/v1
    This allows us to use the OpenAI Agents SDK with Cohere models.

    Returns:
        OpenAIChatCompletionsModel configured for Cohere
    """
    try:
        # Create AsyncOpenAI provider pointing to Cohere's OpenAI-compatible endpoint
        provider = AsyncOpenAI(
            api_key=COHERE_API_KEY,
            base_url=COHERE_BASE_URL,
        )

        # Create the model using Cohere's chat completions API
        model = OpenAIChatCompletionsModel(
            model=COHERE_MODEL,
            openai_client=provider,
        )

        logger.info(f"✅ Cohere client initialized with model: {COHERE_MODEL}")
        return model

    except Exception as e:
        logger.error(f"Failed to initialize Cohere client: {e}")
        raise


# ============================================================================
# CUSTOMER SUCCESS AGENT
# ============================================================================


class CustomerSuccessAgent:
    """
    Production-Grade Customer Success AI Employee

    Multi-channel support agent with:
    - Cohere language model backend
    - 5 integrated production tools
    - Strict workflow enforcement
    - Channel awareness
    - Dedicated memory management (ConversationMemory + CustomerContextMemory)
    - 10-iteration safety limit (prevents infinite loops)
    - Escalation handling
    """

    # Safety limit for agent iterations (prevents infinite tool-call loops)
    MAX_ITERATIONS = 10

    def __init__(self, enable_debug: bool = False):
        """
        Initialize the Customer Success Agent.

        Args:
            enable_debug: Enable verbose logging for debugging
        """
        self.debug = enable_debug
        self.model = create_cohere_client()
        self.agent = self._create_agent()

        # Memory management - replaces simple dict with dedicated classes
        self.conversation_memory: Dict[str, ConversationMemory] = {}
        self.customer_context_memory = CustomerContextMemory()

        # Iteration tracking for safety
        self.iteration_count: Dict[str, int] = {}

        logger.info("✅ Customer Success Agent initialized successfully")
        logger.debug(f"   - Max iterations (safety limit): {self.MAX_ITERATIONS}")

    def _create_agent(self) -> Agent:
        """
        Create the OpenAI Agent with Cohere backend.

        Configures:
        - Model: Cohere (command-r-plus or command-r)
        - System prompt: Production system prompt from prompts.py
        - Tools: All 5 production tools
        - ModelSettings: tool_choice="required" for guaranteed tool usage
        - Name: CustomerSuccessFTE

        Returns:
            Configured Agent instance
        """
        # Define agent with strict model settings
        agent = Agent(
            name="CustomerSuccessFTE",
            model=self.model,
            system_prompt=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
            tools=[
                search_knowledge_base,
                create_ticket,
                get_customer_history,
                escalate_to_human,
                send_response,
            ],
            model_settings=ModelSettings(
                tool_choice="required",  # Always require tool usage
                temperature=0.7,  # Balanced creativity vs consistency
                max_tokens=2048,  # Reasonable response length
            ),
        )

        logger.info("✅ Agent created with Cohere backend")
        logger.debug(f"   - Model: {COHERE_MODEL}")
        logger.debug(f"   - Tools: 5 production tools loaded")
        logger.debug(f"   - Mode: tool_choice='required'")

        return agent

    async def process_message(
        self,
        customer_message: str,
        customer_id: str,
        channel: ChannelType,
        conversation_id: Optional[str] = None,
        customer_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a customer message through the agent.

        Workflow (enforced by system prompt):
        1. CREATE_TICKET: Create or update support ticket
        2. GET_HISTORY: Retrieve customer conversation history
        3. SEARCH_KB: Search knowledge base for answers
        4. SEND_RESPONSE: Generate and send response via channel

        Includes 10-iteration safety limit to prevent infinite tool-call loops.

        Args:
            customer_message: The customer's message content
            customer_id: Unique customer identifier
            channel: Communication channel (email, whatsapp, web_form)
            conversation_id: Optional existing conversation ID
            customer_context: Optional customer context (name, email, phone, etc.)

        Returns:
            Dict with:
            {
                "status": "success" | "escalated" | "error",
                "response": str (agent response or escalation message),
                "ticket_id": str,
                "channel": str,
                "timestamp": datetime,
                "tools_used": List[str],
                "escalated": bool,
                "escalation_reason": Optional[str],
                "iterations": int
            }
        """
        try:
            logger.info(
                f"Processing message from {customer_id} via {channel.value}: "
                f"{customer_message[:50]}..."
            )

            # Generate conversation ID if not provided
            final_conversation_id = conversation_id or f"conv_{customer_id}_{datetime.utcnow().timestamp()}"

            # Initialize conversation memory if needed
            if final_conversation_id not in self.conversation_memory:
                self.conversation_memory[final_conversation_id] = ConversationMemory(final_conversation_id)
                self.iteration_count[final_conversation_id] = 0

            # Initialize/update customer context
            self.customer_context_memory.update_customer(
                customer_id=customer_id,
                **customer_context or {}
            )
            self.customer_context_memory.record_conversation(customer_id)

            # Increment iteration counter
            self.iteration_count[final_conversation_id] += 1
            current_iteration = self.iteration_count[final_conversation_id]

            # Check iteration safety limit
            if current_iteration > self.MAX_ITERATIONS:
                logger.warning(
                    f"⚠️ Iteration limit reached ({self.MAX_ITERATIONS}) for {final_conversation_id}. "
                    f"Escalating to human specialist."
                )

                # Store message in memory
                conv_memory = self.conversation_memory[final_conversation_id]
                conv_memory.add_message("user", customer_message)
                conv_memory.add_message(
                    "assistant",
                    "Escalating to human specialist due to conversation complexity.",
                    tools_used=["escalate_to_human"]
                )

                self.customer_context_memory.record_escalation(customer_id)

                return {
                    "status": "escalated",
                    "response": (
                        "I appreciate your patience. This issue requires specialist attention. "
                        "A human expert will be with you shortly."
                    ),
                    "channel": channel.value,
                    "conversation_id": final_conversation_id,
                    "timestamp": datetime.utcnow(),
                    "escalated": True,
                    "escalation_reason": "Iteration limit reached - complexity threshold exceeded",
                    "iterations": current_iteration,
                }

            # Prepare context for agent
            context = {
                "customer_id": customer_id,
                "channel": channel.value,
                "conversation_id": final_conversation_id,
                "customer_context": customer_context or {},
                "iteration": current_iteration,
            }

            # Format message for agent
            formatted_message = self._format_agent_input(
                customer_message, context
            )

            # Run agent
            logger.debug(f"Running agent iteration {current_iteration} with input: {formatted_message[:100]}...")
            agent_response = await self.agent.run(formatted_message)

            # Store in conversation memory
            conv_memory = self.conversation_memory[final_conversation_id]
            conv_memory.add_message("user", customer_message)

            tools_used = self._extract_tools_used(agent_response)
            conv_memory.add_message(
                "assistant",
                agent_response,
                tools_used=tools_used,
                metadata={"iteration": current_iteration}
            )

            # Parse agent response
            result = self._parse_agent_response(
                agent_response, channel, final_conversation_id
            )

            # Add iteration and memory info
            result["iterations"] = current_iteration
            result["conversation_memory_size"] = conv_memory.get_message_count()

            # Track escalations in customer context
            if result.get("escalated"):
                self.customer_context_memory.record_escalation(customer_id)

            logger.info(f"✅ Message processed successfully [iteration {current_iteration}]: {result['status']}")

            return result

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

            return {
                "status": "error",
                "response": (
                    f"I apologize, but I encountered an error processing your request. "
                    f"A human specialist has been notified and will assist you shortly."
                ),
                "channel": channel.value,
                "timestamp": datetime.utcnow(),
                "error": str(e),
                "escalated": True,
                "escalation_reason": f"System error: {str(e)}",
            }

    def _format_agent_input(
        self, customer_message: str, context: Dict[str, Any]
    ) -> str:
        """
        Format the customer message with context for the agent.

        Includes channel information, customer ID, and conversation context.
        """
        return f"""
Customer Message:
{customer_message}

Context:
- Customer ID: {context['customer_id']}
- Channel: {context['channel']}
- Conversation ID: {context['conversation_id']}
- Additional Context: {context['customer_context']}

Process this message following the STRICT WORKFLOW:
1. CREATE_TICKET first (always)
2. GET_HISTORY next
3. SEARCH knowledge base
4. SEND_RESPONSE

Channel Formatting Requirements:
- Email (200-500 chars, formal tone)
- WhatsApp (50-150 chars, casual tone)
- Web Form (150-300 chars, semi-formal tone)
"""

    def _parse_agent_response(
        self,
        agent_response: str,
        channel: ChannelType,
        conversation_id: str,
    ) -> Dict[str, Any]:
        """
        Parse the agent's response and extract key information.

        Returns structured result with status, response, and metadata.
        """
        # Extract escalation indicators
        escalated = any(
            keyword in agent_response.lower()
            for keyword in [
                "escalate",
                "escalated",
                "specialist",
                "human",
                "manager",
            ]
        )

        # Determine status
        if escalated:
            status = "escalated"
        else:
            status = "success"

        # Adapt response for channel
        formatted_response = self._adapt_for_channel(agent_response, channel)

        return {
            "status": status,
            "response": formatted_response,
            "channel": channel.value,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow(),
            "escalated": escalated,
            "tools_used": self._extract_tools_used(agent_response),
        }

    def _adapt_for_channel(self, response: str, channel: ChannelType) -> str:
        """
        Adapt response format based on communication channel.

        Email: 200-500 chars, formal
        WhatsApp: 50-150 chars, casual
        Web Form: 150-300 chars, semi-formal
        """
        if channel == ChannelType.EMAIL:
            # Keep full response (200-500 chars ideal)
            if len(response) > 500:
                response = response[:497] + "..."
            return response

        elif channel == ChannelType.WHATSAPP:
            # Shorten for WhatsApp (50-150 chars)
            if len(response) > 150:
                response = response[:147] + "..."
            return response

        elif channel == ChannelType.WEB_FORM:
            # Medium length for web form (150-300 chars)
            if len(response) > 300:
                response = response[:297] + "..."
            return response

        return response

    def _extract_tools_used(self, response: str) -> List[str]:
        """Extract which tools were used from agent response."""
        tools = []
        tool_names = [
            "search_knowledge_base",
            "create_ticket",
            "get_customer_history",
            "escalate_to_human",
            "send_response",
        ]

        for tool in tool_names:
            if tool in response.lower():
                tools.append(tool)

        return tools

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a conversation.

        Uses ConversationMemory for efficient history retrieval.
        """
        if conversation_id not in self.conversation_memory:
            return []
        return self.conversation_memory[conversation_id].get_messages()

    def get_conversation_context_window(self, conversation_id: str, window_size: int = 10) -> List[Dict[str, Any]]:
        """
        Get last N messages for context window.

        Useful for feeding recent context back into the agent.
        """
        if conversation_id not in self.conversation_memory:
            return []
        return self.conversation_memory[conversation_id].get_context_window(window_size)

    def get_customer_context(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get persistent customer context."""
        context = self.customer_context_memory.get_customer(customer_id)
        return context.to_dict() if context else None

    def clear_conversation_memory(self, conversation_id: str) -> None:
        """Clear conversation memory (useful for privacy/cleanup)."""
        if conversation_id in self.conversation_memory:
            self.conversation_memory[conversation_id].clear()
            del self.conversation_memory[conversation_id]
            if conversation_id in self.iteration_count:
                del self.iteration_count[conversation_id]
            logger.info(f"Cleared conversation memory: {conversation_id}")

    def clear_customer_memory(self, customer_id: str) -> None:
        """Clear all customer context."""
        self.customer_context_memory.clear_customer(customer_id)
        logger.info(f"Cleared customer context: {customer_id}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        total_conversations = len(self.conversation_memory)
        total_messages = sum(
            conv_mem.get_message_count() for conv_mem in self.conversation_memory.values()
        )
        total_customers = len(self.customer_context_memory.get_all_customers())

        return {
            "status": "ready",
            "model": COHERE_MODEL,
            "provider": "Cohere",
            "tools_loaded": 5,
            "max_iterations": self.MAX_ITERATIONS,
            "conversations_active": total_conversations,
            "total_messages": total_messages,
            "customers_tracked": total_customers,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


async def create_customer_success_agent(
    enable_debug: bool = False,
) -> CustomerSuccessAgent:
    """
    Factory function to create and initialize the Customer Success Agent.

    Args:
        enable_debug: Enable verbose logging

    Returns:
        Initialized CustomerSuccessAgent ready for message processing
    """
    agent = CustomerSuccessAgent(enable_debug=enable_debug)
    logger.info("✅ Customer Success Agent ready for operation")
    return agent


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        """Example usage of the Customer Success Agent."""
        # Create agent
        agent = await create_customer_success_agent(enable_debug=DEBUG)

        # Print status
        status = agent.get_agent_status()
        print("\n📊 Agent Status:")
        print(f"  Model: {status['model']}")
        print(f"  Provider: {status['provider']}")
        print(f"  Tools: {status['tools_loaded']}")
        print(f"  Status: {status['status']}")

        # Example message
        test_message = "I'm having trouble logging into my account. Can you help me reset my password?"

        print("\n📝 Processing example message:")
        print(f"  Customer: CUST-12345")
        print(f"  Channel: Email")
        print(f"  Message: {test_message}")

        try:
            result = await agent.process_message(
                customer_message=test_message,
                customer_id="CUST-12345",
                channel=ChannelType.EMAIL,
                customer_context={
                    "name": "John Doe",
                    "email": "john@example.com",
                },
            )

            print("\n✅ Agent Response:")
            print(f"  Status: {result['status']}")
            print(f"  Response: {result['response']}")
            print(f"  Escalated: {result['escalated']}")
            print(f"  Tools Used: {result.get('tools_used', [])}")

        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Run example
    asyncio.run(main())
