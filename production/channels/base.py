"""
Base Channel Handler - Abstract Base Class for all channel implementations

Defines the interface that all channel handlers (Email, WhatsApp, Web Form) must implement.
Ensures consistent message handling, normalization, and response routing across channels.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from production.database.schema import (
    ChannelType, ConversationCreate, ConversationMessageSchema
)

logger = logging.getLogger(__name__)


class ChannelHandler(ABC):
    """
    Abstract base class for all channel handlers.

    Defines the interface that all channel implementations must follow:
    - Email (Gmail)
    - Messaging (WhatsApp via Twilio)
    - Web (Form submissions)

    Each handler is responsible for:
    1. Authenticating with external service
    2. Receiving/polling for incoming messages
    3. Parsing and normalizing messages
    4. Converting to ConversationMessageSchema
    5. Sending responses back via the channel
    6. Handling errors and logging
    """

    def __init__(self, channel_type: ChannelType):
        """
        Initialize channel handler.

        Args:
            channel_type: Type of channel (EMAIL, WHATSAPP, WEB_FORM)
        """
        self.channel_type = channel_type
        self.is_authenticated = False
        self.logger = logging.getLogger(self.__class__.__name__)

    # ========================================================================
    # AUTHENTICATION - Abstract Methods
    # ========================================================================

    @abstractmethod
    def _authenticate(self) -> None:
        """
        Authenticate with external service.

        Must be called during initialization to set up credentials and
        validate connection with external service.

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    # ========================================================================
    # MESSAGE RECEPTION - Abstract Methods
    # ========================================================================

    @abstractmethod
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """
        Receive/fetch incoming messages from the channel.

        This is the main entry point for polling or webhook-based message intake.

        Returns:
            List of message dictionaries (channel-specific format)

        Raises:
            ChannelError: If message retrieval fails
        """
        pass

    @abstractmethod
    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[ConversationMessageSchema]:
        """
        Parse raw channel message into normalized schema.

        Converts channel-specific message format to ConversationMessageSchema
        for consistent processing by the agent.

        Args:
            raw_message: Channel-specific message (dict or dataclass)

        Returns:
            ConversationMessageSchema or None if parsing fails

        Raises:
            ParseError: If message cannot be parsed
        """
        pass

    # ========================================================================
    # MESSAGE SENDING - Abstract Methods
    # ========================================================================

    @abstractmethod
    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send message via this channel.

        Args:
            recipient_id: Channel-specific recipient ID (email, phone, etc.)
            content: Message content (channel-appropriate length)
            metadata: Channel-specific metadata (optional)

        Returns:
            True if successful, False otherwise

        Raises:
            SendError: If send fails critically
        """
        pass

    @abstractmethod
    def get_send_constraints(self) -> Dict[str, Any]:
        """
        Get channel-specific constraints for message sending.

        Returns dict with:
        {
            "max_length": int,          # Max message length
            "supports_media": bool,     # Can attach media
            "supports_rich_text": bool, # HTML/Markdown
            "rate_limit": int,          # Messages per minute
            "formats": ["text", ...]    # Supported formats
        }

        Returns:
            Dictionary of constraints
        """
        pass

    # ========================================================================
    # SCHEMA CONVERSION - Abstract Methods
    # ========================================================================

    @abstractmethod
    def to_conversation_create(self, message: Any) -> ConversationCreate:
        """
        Convert channel message to ConversationCreate schema.

        Used when creating a new conversation from incoming message.

        Args:
            message: Channel-specific message object

        Returns:
            ConversationCreate schema
        """
        pass

    @abstractmethod
    def to_message_schema(self, message: Any) -> ConversationMessageSchema:
        """
        Convert channel message to ConversationMessageSchema.

        Used when adding message to existing conversation.

        Args:
            message: Channel-specific message object

        Returns:
            ConversationMessageSchema
        """
        pass

    # ========================================================================
    # CONCRETE HELPER METHODS
    # ========================================================================

    def get_channel_type(self) -> ChannelType:
        """Get this handler's channel type."""
        return self.channel_type

    def is_enabled(self) -> bool:
        """Check if handler is authenticated and ready."""
        return self.is_authenticated

    def log_message_received(
        self,
        message_id: str,
        sender: str,
        content_preview: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Log received message (standard format across all channels).

        Args:
            message_id: Unique message ID
            sender: Sender identifier
            content_preview: First 100 chars of message
            metadata: Optional metadata dict
        """
        self.logger.info(
            f"Message received: {message_id} from {sender} "
            f"({self.channel_type.value}): {content_preview[:50]}..."
        )
        if metadata:
            self.logger.debug(f"Metadata: {metadata}")

    def log_message_sent(
        self,
        recipient: str,
        content_preview: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Log sent message (standard format across all channels).

        Args:
            recipient: Recipient identifier
            content_preview: First 100 chars of message
            success: Whether send was successful
            error: Error message if failed
        """
        if success:
            self.logger.info(
                f"Message sent to {recipient} ({self.channel_type.value}): "
                f"{content_preview[:50]}..."
            )
        else:
            self.logger.error(
                f"Failed to send to {recipient} ({self.channel_type.value}): "
                f"{error}"
            )

    def validate_recipient_id(self, recipient_id: str) -> bool:
        """
        Validate recipient ID format (override in subclass).

        Args:
            recipient_id: Recipient identifier

        Returns:
            True if valid, False otherwise
        """
        if not recipient_id or not isinstance(recipient_id, str):
            return False
        if len(recipient_id.strip()) < 3:
            return False
        return True

    def sanitize_content(self, content: str, max_length: int) -> str:
        """
        Sanitize message content.

        - Remove extra whitespace
        - Truncate to max length
        - Remove null characters

        Args:
            content: Raw message content
            max_length: Maximum allowed length

        Returns:
            Sanitized content
        """
        if not content:
            return ""

        # Remove null characters
        content = content.replace('\x00', '')

        # Collapse whitespace
        content = ' '.join(content.split())

        # Truncate
        if len(content) > max_length:
            content = content[:max_length - 3] + "..."

        return content

    # ========================================================================
    # ERROR HANDLING
    # ========================================================================

    def handle_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        critical: bool = False
    ) -> None:
        """
        Handle errors consistently across all channels.

        Args:
            error_type: Type of error (AUTH, SEND, RECEIVE, PARSE)
            error_message: Error message
            context: Optional context dict
            critical: Whether error is critical
        """
        log_func = self.logger.error if critical else self.logger.warning

        log_func(
            f"[{error_type}] {error_message}",
            extra={"context": context, "critical": critical}
        )

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check handler health and readiness.

        Returns dict with:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "channel": "email" | "whatsapp" | "web_form",
            "authenticated": bool,
            "last_check": timestamp,
            "details": {...}
        }

        Returns:
            Health check result
        """
        return {
            "status": "healthy" if self.is_authenticated else "unhealthy",
            "channel": self.channel_type.value,
            "authenticated": self.is_authenticated,
            "last_check": datetime.utcnow().isoformat(),
            "details": {}
        }

    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(channel={self.channel_type.value}, authenticated={self.is_authenticated})"

    def __repr__(self) -> str:
        """Developer representation."""
        return self.__str__()


# ============================================================================
# CHANNEL-SPECIFIC EXCEPTIONS
# ============================================================================

class ChannelError(Exception):
    """Base exception for all channel errors."""
    pass


class AuthenticationError(ChannelError):
    """Authentication with external service failed."""
    pass


class SendError(ChannelError):
    """Failed to send message."""
    pass


class ReceiveError(ChannelError):
    """Failed to receive/fetch messages."""
    pass


class ParseError(ChannelError):
    """Failed to parse message."""
    pass


class ValidationError(ChannelError):
    """Message or request validation failed."""
    pass
