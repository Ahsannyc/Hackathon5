"""
WHATSAPP CHANNEL HANDLER - Enhanced Edition
Multi-mode: Real Twilio Webhook + Intelligent Simulation

Handles SMS/WhatsApp inquiries via Twilio with two operational modes:
1. REAL MODE: Receives Twilio webhooks (needs TWILIO_* env vars)
2. SIMULATION MODE: Simulates incoming messages for testing/demo

Exercise 2.5: Message processor channel handler
Exercise 2.2: SMS/WhatsApp channel integration

**ENABLING REAL TWILIO MODE (Sandbox - Free):**
To enable real Twilio WhatsApp without Docker/WSL:

1. Get Free Twilio Sandbox:
   - Go to https://www.twilio.com/console/sms/whatsapp-sandbox
   - Click "Join Sandbox" and scan the QR code with WhatsApp
   - Or send "join <code>" to their number
   - You get a free testing number automatically!

2. Get API Credentials:
   - From https://www.twilio.com/console
   - Copy Account SID and Auth Token
   - Save to .env file:

   TWILIO_ACCOUNT_SID=ACxxxxxxxx
   TWILIO_AUTH_TOKEN=abcdefghij
   TWILIO_WHATSAPP_NUMBER=+1234567890

3. Configure Webhook URL:
   - In Twilio Console → Phone Numbers → Your Sandbox
   - Set "When a message comes in" to: https://your-domain.com/api/whatsapp/webhook
   - For local testing, use ngrok: ngrok http 8000

4. Restart service - it will auto-detect credentials and switch to REAL mode

The system detects TWILIO_* env vars and auto-activates Real Mode!
No code changes needed. No Docker required. Free Sandbox available!
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# MESSAGE MODEL
# ============================================================================

class WhatsAppMessage:
    """Represents a WhatsApp/SMS message."""

    def __init__(self, from_number: str, to_number: str, body: str, message_id: str, sender_name: str = "WhatsApp User"):
        self.from_number = from_number
        self.to_number = to_number
        self.body = body
        self.message_id = message_id
        self.sender_name = sender_name
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_number": self.from_number,
            "to_number": self.to_number,
            "body": self.body,
            "message_id": self.message_id,
            "sender_name": self.sender_name,
            "timestamp": self.timestamp
        }


# ============================================================================
# TWILIO WEBHOOK HANDLER
# ============================================================================

class TwilioWebhookReceiver:
    """
    Receives webhooks from Twilio WhatsApp Sandbox.
    Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER in .env

    Mode 1: REAL - Receives actual Twilio webhooks
    Mode 2: SIMULATION - Queues test messages
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "+1234567890")

        self.mode = "SIMULATION"  # Default

        if self.account_sid and self.auth_token:
            self.mode = "REAL"
            logger.info("✅ WhatsApp Real Mode: Using Twilio credentials from .env")
            logger.info("   Twilio Sandbox will route incoming WhatsApp messages here")
            logger.info("   Configure webhook in Twilio Console → Phone Numbers")
        else:
            logger.info("ℹ️  WhatsApp Simulation Mode: Using test messages (no Twilio credentials needed)")
            logger.info("   To enable REAL mode: Add TWILIO_* vars to .env")
            logger.info("   Free: Get Twilio Sandbox at https://www.twilio.com/console/sms/whatsapp-sandbox")

        self.test_queue: List[WhatsAppMessage] = []

    def add_test_message(self, from_number: str, sender_name: str, body: str):
        """Add a test WhatsApp message to the simulation queue."""
        message_id = f"test_whatsapp_{len(self.test_queue)}_{int(__import__('time').time())}"
        message = WhatsAppMessage(from_number, self.whatsapp_number, body, message_id, sender_name)
        self.test_queue.append(message)
        logger.info(f"💬 Test WhatsApp message queued: From {sender_name}, Body: {body[:50]}...")

    def process_webhook(self, webhook_data: Dict[str, str]) -> Optional[WhatsAppMessage]:
        """
        Process incoming Twilio webhook.
        REAL mode: Parse actual Twilio webhook format
        SIMULATION mode: Not used (messages come from test queue)

        Twilio webhook format (form-encoded):
        - From: whatsapp:+15551234567
        - To: whatsapp:+15559876543
        - Body: Message text
        - MessageSid: SMxxxxxxxx
        - ProfileName: Customer name (if available)
        """
        if self.mode == "REAL":
            try:
                from_number = webhook_data.get("From", "")
                body = webhook_data.get("Body", "")
                message_sid = webhook_data.get("MessageSid", "")
                sender_name = webhook_data.get("ProfileName", "WhatsApp User")

                message = WhatsAppMessage(from_number, self.whatsapp_number, body, message_sid, sender_name)
                logger.info(f"💬 Received real WhatsApp message from {from_number}")
                return message
            except Exception as e:
                logger.error(f"Error processing Twilio webhook: {e}")
                return None
        else:
            logger.info("(Webhook processing in SIMULATION mode)")
            return None

    def fetch_pending_messages(self) -> List[WhatsAppMessage]:
        """Get pending messages from simulation queue or real webhooks."""
        messages = self.test_queue[:]
        self.test_queue.clear()
        return messages


# ============================================================================
# WHATSAPP RESPONSE FORMATTER
# ============================================================================

class WhatsAppResponseFormatter:
    """Formats AI responses for WhatsApp/SMS channel - concise and mobile-friendly."""

    @staticmethod
    def format_response(ai_response: str, ticket_id: str) -> str:
        """
        Format response appropriately for WhatsApp.
        Concise, conversational tone, mobile-optimized.
        WhatsApp messages should be readable on small screens.
        """
        # WhatsApp messages should be concise but helpful
        if len(ai_response) > 500:
            formatted = ai_response[:450] + "...\n\n[See full response via email]"
        else:
            formatted = ai_response

        return f"""{formatted}

Ticket: {ticket_id}"""

    @staticmethod
    def split_long_message(message: str, chunk_size: int = 1000) -> List[str]:
        """Split long messages into WhatsApp-friendly chunks."""
        if len(message) <= chunk_size:
            return [message]

        chunks = []
        words = message.split()
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 <= chunk_size:
                current_chunk += word + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


# ============================================================================
# WHATSAPP HANDLER
# ============================================================================

class WhatsAppChannelHandler:
    """
    Handles SMS and WhatsApp messages via Twilio.

    Usage:
        handler = WhatsAppChannelHandler()

        # Real mode (if Twilio credentials in .env):
        # - Receives POST webhooks at /api/whatsapp/webhook
        # - Sends via Twilio API

        # Simulation mode (for testing):
        handler.add_test_message("+1555012345", "Sarah", "How do I reset my password?")
        messages = handler.fetch_messages()
        response = handler.format_response("Here are the steps...", "TICKET-456")

    Cross-Channel Continuity:
        - Phone number is used as secondary customer identifier
        - Can be linked to email (from web form or email channel)
        - Same customer recognized across all three channels
    """

    def __init__(self):
        self.webhook_receiver = TwilioWebhookReceiver()
        self.response_formatter = WhatsAppResponseFormatter()
        logger.info(f"💬 WhatsApp Handler initialized ({self.webhook_receiver.mode} mode)")

        if self.webhook_receiver.mode == "REAL":
            logger.info("   ✅ Ready to receive Twilio WhatsApp webhooks")
            logger.info("   📱 Set webhook URL in Twilio Console")
        else:
            logger.info("   🧪 Using simulation mode for testing")
            logger.info("   💡 Tip: Add TWILIO_* to .env to enable REAL mode (free sandbox available!)")

    def add_test_message(self, from_number: str, sender_name: str, body: str):
        """Add a test WhatsApp message (simulation mode)."""
        self.webhook_receiver.add_test_message(from_number, sender_name, body)

    def fetch_messages(self) -> List[Dict[str, Any]]:
        """Fetch pending WhatsApp messages."""
        try:
            messages = self.webhook_receiver.fetch_pending_messages()
            logger.info(f"💬 Fetched {len(messages)} WhatsApp message(s)")
            return [msg.to_dict() for msg in messages]
        except Exception as e:
            logger.error(f"Error fetching WhatsApp messages: {e}")
            return []

    def format_response(self, ai_response: str, ticket_id: str) -> str:
        """Format response for WhatsApp delivery."""
        return self.response_formatter.format_response(ai_response, ticket_id)

    def process_webhook(self, webhook_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Process incoming Twilio webhook."""
        message = self.webhook_receiver.process_webhook(webhook_data)
        if message:
            return message.to_dict()
        return None

    def is_real_mode(self) -> bool:
        """Check if running in real Twilio mode."""
        return self.webhook_receiver.mode == "REAL"

    def is_simulation_mode(self) -> bool:
        """Check if running in simulation mode."""
        return self.webhook_receiver.mode == "SIMULATION"


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_whatsapp_handler: Optional[WhatsAppChannelHandler] = None


def get_whatsapp_handler() -> WhatsAppChannelHandler:
    """Get or create global WhatsApp handler instance."""
    global _whatsapp_handler
    if _whatsapp_handler is None:
        _whatsapp_handler = WhatsAppChannelHandler()
    return _whatsapp_handler
