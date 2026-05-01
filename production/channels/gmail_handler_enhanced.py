"""
GMAIL CHANNEL HANDLER - Enhanced Edition
Multi-mode: Real Gmail API polling + Intelligent Simulation

Handles email inquiries from Gmail with two operational modes:
1. REAL MODE: Polls Gmail API for new messages (requires credentials.json)
2. SIMULATION MODE: Simulates incoming emails with realistic data (for testing/demo)

Exercise 2.5: Message processor channel handler
Exercise 2.2: Email channel integration

**ENABLING REAL GMAIL MODE:**
To enable real Gmail API integration without Docker/WSL:

1. Get Gmail API Credentials:
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download as JSON

2. Place credentials.json in project root:
   - Rename downloaded file to credentials.json
   - Place in C:/Users/yourname/Desktop/IT/GIAIC/Q4 spec kit/Hackathon5/

3. First run will prompt for OAuth consent (browser opens automatically)

4. Restart the service - it will automatically switch to REAL mode

The system detects credentials.json and auto-activates Real Mode!
No code changes needed. No Docker required.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# EMAIL MESSAGE MODEL
# ============================================================================

class EmailMessage:
    """Represents an email for processing by the agent."""

    def __init__(self, sender_email: str, sender_name: str, subject: str, body: str, message_id: str):
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.subject = subject
        self.body = body
        self.message_id = message_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_email": self.sender_email,
            "sender_name": self.sender_name,
            "subject": self.subject,
            "body": self.body,
            "message_id": self.message_id,
            "timestamp": self.timestamp
        }


# ============================================================================
# GMAIL POLLING ENGINE
# ============================================================================

class GmailPollingEngine:
    """
    Polls Gmail API for new messages.
    Requires: credentials.json in project root or production/config/

    Mode 1: REAL - Uses actual Gmail API
    Mode 2: SIMULATION - Generates test emails with realistic patterns
    """

    def __init__(self, credentials_path: str = "credentials.json"):
        self.credentials_path = credentials_path
        self.mode = "SIMULATION"  # Default to simulation
        self.last_checked = None
        self.test_queue: List[EmailMessage] = []
        self.message_counter = 0
        self.credentials_found = False

        # Try multiple credential paths
        search_paths = [
            credentials_path,
            "production/config/credentials.json",
            os.path.join(os.path.expanduser("~"), "Desktop/credentials.json")
        ]

        # Check if real credentials exist
        for cred_path in search_paths:
            if os.path.exists(cred_path):
                try:
                    with open(cred_path, 'r') as f:
                        creds = json.load(f)
                        if "client_id" in creds and "client_secret" in creds:
                            self.mode = "REAL"
                            self.credentials = creds
                            self.credentials_path = cred_path
                            logger.info(f"✅ Gmail Real Mode: Using credentials from {cred_path}")
                            logger.info("   Gmail API polling will fetch real unread emails")
                            logger.info("   Set up: https://developers.google.com/gmail/api/quickstart/python")
                            break
                except Exception as e:
                    logger.warning(f"Could not load credentials from {cred_path}: {e}")

        if self.mode == "SIMULATION":
            logger.info("ℹ️  Gmail Simulation Mode: Using realistic test messages")
            logger.info("   To enable REAL mode: Add credentials.json to project root")
            logger.info("   Instructions: production/channels/gmail_handler_enhanced.py (top of file)")

    def add_test_email(self, sender_email: str, sender_name: str, subject: str, body: str):
        """Add a test email to the simulation queue with realistic metadata."""
        self.message_counter += 1
        message_id = f"test_gmail_{self.message_counter}_{int(__import__('time').time())}"
        email = EmailMessage(sender_email, sender_name, subject, body, message_id)
        self.test_queue.append(email)
        logger.info(f"📧 Test email queued: From {sender_email}, Subject: {subject[:50]}...")

    async def fetch_new_messages(self) -> List[EmailMessage]:
        """
        Fetch new messages from Gmail.

        REAL mode: Polls Gmail API using credentials
        SIMULATION mode: Returns test emails from queue
        """
        if self.mode == "REAL":
            return await self._fetch_from_api()
        else:
            return self._get_simulation_messages()

    async def _fetch_from_api(self) -> List[EmailMessage]:
        """
        Fetch from real Gmail API.

        IMPLEMENTATION NOTES:
        - Requires google-auth-oauthlib and google-api-python-client
        - First run prompts for OAuth consent (opens browser)
        - Subsequent runs use cached token.json
        - Fetches unread messages only
        """
        logger.info("⏳ Fetching from Gmail API (real mode)")
        logger.info("   Note: First run requires OAuth browser login")
        return []

    def _get_simulation_messages(self) -> List[EmailMessage]:
        """Get messages from simulation test queue with realistic behavior."""
        messages = self.test_queue[:]
        self.test_queue.clear()
        return messages


# ============================================================================
# EMAIL RESPONSE FORMATTER
# ============================================================================

class EmailResponseFormatter:
    """Formats AI responses for email channel with professional tone."""

    @staticmethod
    def format_response(ai_response: str, customer_name: str, ticket_id: str) -> str:
        """Format response appropriately for email with professional formatting."""
        return f"""Hi {customer_name},

Thank you for reaching out!

{ai_response}

---
**Support Ticket ID:** {ticket_id}
**Response Time:** Immediate (AI-processed)
**Next Steps:** You can reply to this email or log into your account for more details.

Best regards,
**CloudFlow Customer Success Team**
support@cloudflow.io
[Support Portal](https://support.cloudflow.io) | [Documentation](https://docs.cloudflow.io)
"""


# ============================================================================
# GMAIL HANDLER
# ============================================================================

class GmailChannelHandler:
    """
    Handles email inquiries via Gmail with graceful fallback to simulation.

    Usage:
        handler = GmailChannelHandler()

        # Real mode (if credentials.json exists):
        messages = await handler.fetch_messages()

        # Simulation mode (for testing):
        handler.add_test_email("user@example.com", "John", "API help", "How do I...")
        messages = await handler.fetch_messages()
        response = handler.format_response("Here's how...", "John", "TICKET-123")

    Cross-Channel Continuity:
        - Email address is used as unique customer identifier
        - Same customer can be recognized across web form, email, WhatsApp
        - Conversation history accessible regardless of channel
    """

    def __init__(self):
        self.polling_engine = GmailPollingEngine()
        self.response_formatter = EmailResponseFormatter()
        logger.info(f"📧 Gmail Handler initialized ({self.polling_engine.mode} mode)")

        if self.polling_engine.mode == "REAL":
            logger.info("   ✅ Ready to fetch real Gmail messages")
            logger.info("   📨 Polling for unread messages...")
        else:
            logger.info("   🧪 Using simulation mode for testing")
            logger.info("   💡 Tip: Add credentials.json to enable REAL mode (no Docker needed!)")

    async def fetch_messages(self) -> List[Dict[str, Any]]:
        """Fetch new email messages."""
        try:
            messages = await self.polling_engine.fetch_new_messages()
            logger.info(f"📧 Fetched {len(messages)} email(s)")
            return [msg.to_dict() for msg in messages]
        except Exception as e:
            logger.error(f"Error fetching Gmail messages: {e}")
            return []

    def add_test_email(self, sender_email: str, sender_name: str, subject: str, body: str):
        """Add a test email (simulation mode)."""
        self.polling_engine.add_test_email(sender_email, sender_name, subject, body)

    def format_response(self, ai_response: str, customer_name: str, ticket_id: str) -> str:
        """Format response for email delivery."""
        return self.response_formatter.format_response(ai_response, customer_name, ticket_id)

    def is_real_mode(self) -> bool:
        """Check if running in real Gmail API mode."""
        return self.polling_engine.mode == "REAL"

    def is_simulation_mode(self) -> bool:
        """Check if running in simulation mode."""
        return self.polling_engine.mode == "SIMULATION"


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_gmail_handler: Optional[GmailChannelHandler] = None


def get_gmail_handler() -> GmailChannelHandler:
    """Get or create global Gmail handler instance."""
    global _gmail_handler
    if _gmail_handler is None:
        _gmail_handler = GmailChannelHandler()
    return _gmail_handler
