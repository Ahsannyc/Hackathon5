"""
Channels Module - Multi-channel input/output handling

Provides handlers for Email (Gmail), WhatsApp (Twilio), and Web Forms.
Each handler normalizes incoming messages to ConversationMessageSchema.
"""

from .base import (
    ChannelHandler, ChannelError, AuthenticationError, SendError,
    ReceiveError, ParseError, ValidationError
)
from .gmail_handler import GmailHandler, EmailMessage
from .whatsapp_handler import WhatsAppHandler, WhatsAppMessage
from .web_form_handler import WebFormHandler, WebFormMessage, create_web_form_router

__all__ = [
    "ChannelHandler",
    "ChannelError",
    "AuthenticationError",
    "SendError",
    "ReceiveError",
    "ParseError",
    "ValidationError",
    "GmailHandler",
    "EmailMessage",
    "WhatsAppHandler",
    "WhatsAppMessage",
    "WebFormHandler",
    "WebFormMessage",
    "create_web_form_router",
]
