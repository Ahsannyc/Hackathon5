"""
Gmail Channel Handler - Email integration via Gmail API

Handles incoming emails from Gmail, converts to normalized message format,
and sends responses via email.

Credentials:
- credentials.json: OAuth2 credentials (stored in project root)
- Uses Google Calendar/Gmail API for Pub/Sub style notifications
"""

import json
import logging
import base64
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from email.mime.text import MIMEText
from dataclasses import dataclass

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth.exceptions

from production.database.schema import (
    ChannelType, ConversationCreate, ConversationMessageSchema,
    TicketCreate, PriorityLevel
)
from production.channels.base import ChannelHandler, AuthenticationError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


@dataclass
class EmailMessage:
    """Normalized email message from Gmail."""
    message_id: str
    thread_id: str
    sender_email: str
    sender_name: Optional[str]
    subject: str
    body: str
    timestamp: datetime
    channel: ChannelType = ChannelType.EMAIL


class GmailHandler(ChannelHandler):
    """
    Gmail channel handler for email integration.

    Responsibilities:
    - Load Gmail API credentials
    - Fetch and parse incoming emails
    - Convert emails to normalized format
    - Send responses via Gmail API
    - Handle errors and logging
    """

    def __init__(self, credentials_path: str = "credentials.json"):
        """
        Initialize Gmail handler.

        Args:
            credentials_path: Path to credentials.json file (default: project root)
        """
        super().__init__(channel_type=ChannelType.EMAIL)
        self.credentials_path = credentials_path
        self.service = None
        self.user_email = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Load and authenticate with Gmail API credentials."""
        try:
            # Check if credentials.json exists in project root
            if not os.path.exists(self.credentials_path):
                logger.warning(
                    f"Gmail credentials not found at {self.credentials_path}. "
                    "Gmail handler will not function. "
                    "Place credentials.json in project root or set GMAIL_CREDENTIALS_PATH."
                )
                return

            # Try to use existing token first
            token_path = ".gmail_token.json"
            creds = None

            if os.path.exists(token_path):
                with open(token_path, "r") as token_file:
                    token_data = json.load(token_file)
                    creds = UserCredentials.from_authorized_user_info(token_data, SCOPES)

            # If no valid token, get new one
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save token for future use
                with open(token_path, "w") as token_file:
                    json.dump(json.loads(creds.to_json()), token_file)

            # Import here to avoid circular dependency
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            self.service = build("gmail", "v1", credentials=creds)
            profile = self.service.users().getProfile(userId="me").execute()
            self.user_email = profile.get("emailAddress")
            logger.info(f"Gmail authenticated as {self.user_email}")

        except FileNotFoundError:
            logger.error(f"Credentials file not found: {self.credentials_path}")
        except google.auth.exceptions.DefaultCredentialsError as e:
            logger.error(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Gmail authentication: {e}")

    def fetch_unread_messages(self) -> list[EmailMessage]:
        """
        Fetch unread messages from Gmail inbox.

        Returns:
            List of EmailMessage objects
        """
        if not self.service:
            logger.warning("Gmail service not initialized")
            return []

        try:
            results = self.service.users().messages().list(
                userId="me",
                q="is:unread",
                maxResults=10
            ).execute()

            messages = []
            message_list = results.get("messages", [])

            for msg_summary in message_list:
                try:
                    msg = self.service.users().messages().get(
                        userId="me",
                        id=msg_summary["id"],
                        format="full"
                    ).execute()

                    email_msg = self._parse_message(msg)
                    if email_msg:
                        messages.append(email_msg)

                except Exception as e:
                    logger.error(f"Error parsing message {msg_summary['id']}: {e}")
                    continue

            logger.info(f"Fetched {len(messages)} unread messages from Gmail")
            return messages

        except Exception as e:
            logger.error(f"Error fetching messages from Gmail: {e}")
            return []

    def _parse_message(self, message: Dict[str, Any]) -> Optional[EmailMessage]:
        """
        Parse Gmail API message into EmailMessage object.

        Args:
            message: Gmail API message object

        Returns:
            EmailMessage or None if parsing fails
        """
        try:
            msg_id = message["id"]
            headers = message["payload"].get("headers", [])

            # Extract email headers
            header_dict = {h["name"]: h["value"] for h in headers}
            sender_email = header_dict.get("From", "").split("<")[-1].rstrip(">")
            sender_name = header_dict.get("From", "").split("<")[0].strip()
            subject = header_dict.get("Subject", "(No subject)")

            # Extract body
            body = self._get_message_body(message)

            # Parse timestamp
            timestamp = datetime.fromtimestamp(int(message["internalDate"]) / 1000)

            # Get thread ID
            thread_id = message.get("threadId", msg_id)

            return EmailMessage(
                message_id=msg_id,
                thread_id=thread_id,
                sender_email=sender_email,
                sender_name=sender_name if sender_name else None,
                subject=subject,
                body=body,
                timestamp=timestamp,
                channel=ChannelType.EMAIL
            )

        except Exception as e:
            logger.error(f"Error parsing message structure: {e}")
            return None

    def _get_message_body(self, message: Dict[str, Any]) -> str:
        """Extract message body from Gmail API response."""
        try:
            payload = message["payload"]

            # Handle multipart messages
            if "parts" in payload:
                return self._get_body_from_parts(payload["parts"])

            # Handle single part messages
            if "body" in payload and "data" in payload["body"]:
                data = payload["body"]["data"]
                return base64.urlsafe_b64decode(data).decode("utf-8")

            return ""

        except Exception as e:
            logger.error(f"Error extracting message body: {e}")
            return ""

    def _get_body_from_parts(self, parts: list) -> str:
        """Extract text body from multipart message."""
        for part in parts:
            mime_type = part.get("mimeType", "")

            if mime_type == "text/plain":
                if "data" in part.get("body", {}):
                    data = part["body"]["data"]
                    return base64.urlsafe_b64decode(data).decode("utf-8")

            # Recursively handle nested parts
            if "parts" in part:
                text = self._get_body_from_parts(part["parts"])
                if text:
                    return text

        return ""

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None
    ) -> bool:
        """
        Send email via Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            in_reply_to: Optional message ID to reply to

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Gmail service not initialized - cannot send email")
            return False

        try:
            message = MIMEText(body)
            message["to"] = to_email
            message["subject"] = subject

            if in_reply_to:
                message["In-Reply-To"] = in_reply_to
                message["References"] = in_reply_to

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode("utf-8")

            self.service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()

            logger.info(f"Email sent to {to_email} with subject: {subject}")
            return True

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read in Gmail."""
        if not self.service:
            return False

        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error marking message {message_id} as read: {e}")
            return False

    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[ConversationMessageSchema]:
        """Parse raw Gmail message to ConversationMessageSchema."""
        msg = self._parse_message(raw_message)
        if msg:
            return self.to_message_schema(msg)
        return None

    def to_conversation_create(self, email_msg: EmailMessage) -> ConversationCreate:
        """Convert EmailMessage to ConversationCreate schema."""
        return ConversationCreate(
            customer_id=email_msg.sender_email,
            channel=ChannelType.EMAIL,
            subject=email_msg.subject
        )

    def to_message_schema(self, email_msg: EmailMessage) -> ConversationMessageSchema:
        """Convert EmailMessage to ConversationMessageSchema."""
        return ConversationMessageSchema(
            id=email_msg.message_id,
            content=email_msg.body,
            sender=email_msg.sender_email,
            channel=ChannelType.EMAIL,
            sentiment=None,  # Will be calculated by agent
            intent=None,  # Will be calculated by agent
            timestamp=email_msg.timestamp
        )

    # ========================================================================
    # Base Class Abstract Method Implementations
    # ========================================================================

    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from Gmail (via polling)."""
        messages = self.fetch_unread_messages()
        return [
            {
                "message_id": msg.message_id,
                "thread_id": msg.thread_id,
                "sender_email": msg.sender_email,
                "sender_name": msg.sender_name,
                "subject": msg.subject,
                "body": msg.body,
                "timestamp": msg.timestamp.isoformat(),
                "channel": ChannelType.EMAIL.value
            }
            for msg in messages
        ]

    def get_send_constraints(self) -> Dict[str, Any]:
        """Get email-specific sending constraints."""
        return {
            "max_length": 5000,
            "supports_media": True,
            "supports_rich_text": True,
            "rate_limit": 100,
            "formats": ["text/plain", "text/html"],
            "channel": ChannelType.EMAIL.value
        }

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email via Gmail API.

        Args:
            recipient_id: Email address
            content: Message body
            metadata: Optional metadata (subject, in_reply_to, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.validate_recipient_id(recipient_id):
            self.handle_error("VALIDATION", f"Invalid email: {recipient_id}")
            return False

        try:
            subject = metadata.get("subject", "Response") if metadata else "Response"
            in_reply_to = metadata.get("in_reply_to") if metadata else None

            constraints = self.get_send_constraints()
            sanitized_content = self.sanitize_content(content, constraints["max_length"])

            success = self.send_email(
                to_email=recipient_id,
                subject=subject,
                body=sanitized_content,
                in_reply_to=in_reply_to
            )

            if success:
                self.log_message_sent(recipient_id, content)

            return success

        except Exception as e:
            self.handle_error("SEND", f"Failed to send email: {e}")
            return False
