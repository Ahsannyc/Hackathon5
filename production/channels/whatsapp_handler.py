"""
WhatsApp Channel Handler - Twilio WhatsApp Business API integration

Handles incoming WhatsApp messages via Twilio webhook, validates signatures,
converts to normalized message format, and sends responses.

Credentials:
- TWILIO_ACCOUNT_SID: From .env
- TWILIO_AUTH_TOKEN: From .env
- TWILIO_NUMBER: Twilio WhatsApp sandbox/number from .env
"""

import logging
import hashlib
import hmac
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from production.database.schema import (
    ChannelType, ConversationCreate, ConversationMessageSchema
)
from production.config.settings import Settings
from production.channels.base import ChannelHandler, AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessage:
    """Normalized WhatsApp message from Twilio."""
    message_id: str
    sender_number: str
    sender_name: Optional[str]
    body: str
    timestamp: datetime
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    channel: ChannelType = ChannelType.WHATSAPP


class WhatsAppHandler(ChannelHandler):
    """
    WhatsApp channel handler using Twilio Business API.

    Responsibilities:
    - Load Twilio credentials from environment
    - Validate incoming webhook signatures
    - Parse Twilio webhook payloads
    - Convert messages to normalized format
    - Send responses via Twilio API
    - Handle media messages (images, documents, etc.)
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize WhatsApp handler.

        Args:
            settings: Settings object with Twilio credentials
        """
        super().__init__(channel_type=ChannelType.WHATSAPP)
        self.settings = settings or Settings()
        self.client = None
        self.validator = None
        self.twilio_number = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Load and authenticate with Twilio API."""
        try:
            # Validate required credentials
            if not self.settings.twilio_account_sid:
                logger.error("TWILIO_ACCOUNT_SID not set in environment")
                return

            if not self.settings.twilio_auth_token:
                logger.error("TWILIO_AUTH_TOKEN not set in environment")
                return

            if not self.settings.twilio_number:
                logger.error("TWILIO_NUMBER not set in environment")
                return

            # Initialize Twilio client
            self.client = Client(
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token
            )

            # Initialize request validator for webhook signature verification
            self.validator = RequestValidator(self.settings.twilio_auth_token)
            self.twilio_number = self.settings.twilio_number

            logger.info(f"WhatsApp handler initialized with number: {self.twilio_number}")

        except Exception as e:
            logger.error(f"Error initializing WhatsApp handler: {e}")

    def validate_webhook_signature(
        self,
        url: str,
        post_params: Dict[str, str],
        signature: str
    ) -> bool:
        """
        Validate Twilio webhook signature.

        Args:
            url: Request URL (with query parameters)
            post_params: POST parameters from webhook
            signature: X-Twilio-Signature header value

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.validator:
            logger.error("Request validator not initialized")
            return False

        is_valid = self.validator.validate(url, post_params, signature)
        if not is_valid:
            logger.warning(f"Invalid webhook signature for URL: {url}")
        return is_valid

    def parse_webhook_payload(self, payload: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Parse Twilio webhook payload into WhatsAppMessage.

        Args:
            payload: Request form data from Twilio webhook

        Returns:
            WhatsAppMessage or None if parsing fails
        """
        try:
            message_id = payload.get("SmsMessageSid") or payload.get("MessageSid")
            from_number = payload.get("From", "").replace("whatsapp:", "")
            body = payload.get("Body", "")

            if not message_id or not from_number:
                logger.warning("Missing required fields in Twilio payload")
                return None

            # Parse media if present
            media_url = None
            media_type = None
            num_media = int(payload.get("NumMedia", 0))

            if num_media > 0:
                media_url = payload.get("MediaUrl0")
                media_type = payload.get("MediaContentType0")

            # Twilio uses Unix timestamp or we use current time
            timestamp = datetime.utcnow()

            # Extract sender name from contact name if available
            sender_name = payload.get("ProfileName")

            return WhatsAppMessage(
                message_id=message_id,
                sender_number=from_number,
                sender_name=sender_name,
                body=body,
                timestamp=timestamp,
                media_url=media_url,
                media_type=media_type,
                channel=ChannelType.WHATSAPP
            )

        except Exception as e:
            logger.error(f"Error parsing Twilio webhook payload: {e}")
            return None

    def _send_whatsapp_message(
        self,
        to_number: str,
        body: str,
        media_url: Optional[str] = None
    ) -> bool:
        """
        Send message via Twilio WhatsApp API (internal method).

        Args:
            to_number: Recipient phone number (without 'whatsapp:' prefix)
            body: Message content (max 1600 characters)
            media_url: Optional media URL to attach

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False

        if not self.twilio_number:
            logger.error("Twilio number not configured")
            return False

        try:
            # Ensure phone number has whatsapp: prefix
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            from_number = f"whatsapp:{self.twilio_number}"

            # Send message
            if media_url:
                message = self.client.messages.create(
                    from_=from_number,
                    to=to_number,
                    body=body,
                    media_url=media_url
                )
            else:
                message = self.client.messages.create(
                    from_=from_number,
                    to=to_number,
                    body=body
                )

            logger.info(
                f"WhatsApp message sent to {to_number} "
                f"(SID: {message.sid})"
            )
            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {to_number}: {e}")
            return False

    def send_template_message(
        self,
        to_number: str,
        template_name: str,
        template_variables: Optional[list] = None
    ) -> bool:
        """
        Send WhatsApp template message via Twilio.

        Args:
            to_number: Recipient phone number
            template_name: Pre-approved template name
            template_variables: List of variable values

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False

        if not self.twilio_number:
            logger.error("Twilio number not configured")
            return False

        try:
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            from_number = f"whatsapp:{self.twilio_number}"

            # Prepare template body
            template_body = {
                "name": template_name,
                "language": {"code": "en"}
            }

            if template_variables:
                template_body["parameters"] = {
                    "body": {"parameters": [{"text": v} for v in template_variables]}
                }

            message = self.client.messages.create(
                from_=from_number,
                to=to_number,
                content_sid=template_name
            )

            logger.info(
                f"Template message '{template_name}' sent to {to_number} "
                f"(SID: {message.sid})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending template message '{template_name}' "
                f"to {to_number}: {e}"
            )
            return False

    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[ConversationMessageSchema]:
        """Parse raw WhatsApp message to ConversationMessageSchema."""
        msg = self.parse_webhook_payload(raw_message)
        if msg:
            return self.to_message_schema(msg)
        return None

    def to_conversation_create(self, whatsapp_msg: WhatsAppMessage) -> ConversationCreate:
        """Convert WhatsAppMessage to ConversationCreate schema."""
        return ConversationCreate(
            customer_id=whatsapp_msg.sender_number,
            channel=ChannelType.WHATSAPP,
            subject=f"WhatsApp from {whatsapp_msg.sender_name or whatsapp_msg.sender_number}"
        )

    def to_message_schema(self, whatsapp_msg: WhatsAppMessage) -> ConversationMessageSchema:
        """Convert WhatsAppMessage to ConversationMessageSchema."""
        # Include media info in content if present
        content = whatsapp_msg.body
        if whatsapp_msg.media_url:
            content += f"\n[Media: {whatsapp_msg.media_type}]"

        return ConversationMessageSchema(
            id=whatsapp_msg.message_id,
            content=content,
            sender=whatsapp_msg.sender_number,
            channel=ChannelType.WHATSAPP,
            sentiment=None,  # Will be calculated by agent
            intent=None,  # Will be calculated by agent
            timestamp=whatsapp_msg.timestamp
        )

    # ========================================================================
    # Base Class Abstract Method Implementations
    # ========================================================================

    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from WhatsApp (via webhook polling)."""
        # Note: In production, messages arrive via webhook POST
        # This is for manual polling/testing
        return []

    def get_send_constraints(self) -> Dict[str, Any]:
        """Get WhatsApp-specific sending constraints."""
        return {
            "max_length": 4096,
            "supports_media": True,
            "supports_rich_text": False,
            "rate_limit": 80,
            "formats": ["text", "media"],
            "channel": ChannelType.WHATSAPP.value
        }

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send WhatsApp message via Twilio.

        Args:
            recipient_id: Phone number (with or without 'whatsapp:' prefix)
            content: Message body
            metadata: Optional metadata (media_url, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.validate_recipient_id(recipient_id):
            self.handle_error("VALIDATION", f"Invalid phone number: {recipient_id}")
            return False

        try:
            constraints = self.get_send_constraints()
            sanitized_content = self.sanitize_content(content, constraints["max_length"])

            media_url = metadata.get("media_url") if metadata else None

            success = self._send_whatsapp_message(
                to_number=recipient_id,
                body=sanitized_content,
                media_url=media_url
            )

            if success:
                self.log_message_sent(recipient_id, content)

            return success

        except Exception as e:
            self.handle_error("SEND", f"Failed to send WhatsApp message: {e}")
            return False
