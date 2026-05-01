"""
Web Form Channel Handler - FastAPI router for web form submissions

Handles incoming web form submissions, validates with Pydantic,
converts to normalized message format, and provides responses.

Configuration:
- WEBFORM_ENDPOINT: Route path (from .env)
- WEBFORM_MAX_FILE_SIZE: Max upload size (from .env)
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, validator

from production.database.schema import (
    ChannelType, ConversationCreate, ConversationMessageSchema
)
from production.config.settings import Settings
from production.channels.base import ChannelHandler

logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class WebFormSubmissionRequest(BaseModel):
    """Validated web form submission."""
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr
    subject: str = Field(..., min_length=5, max_length=500)
    message: str = Field(..., min_length=10, max_length=5000)
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    attachments_count: int = Field(default=0, ge=0, le=5)

    @validator("message")
    def message_no_scripts(cls, v):
        """Prevent XSS attacks in message field."""
        if "<script" in v.lower():
            raise ValueError("Script tags not allowed in message")
        return v

    @validator("subject")
    def subject_no_scripts(cls, v):
        """Prevent XSS attacks in subject field."""
        if "<script" in v.lower():
            raise ValueError("Script tags not allowed in subject")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "subject": "Help with account setup",
                "message": "I'm having trouble setting up my account. Can you help?",
                "priority": "medium",
                "phone": "+1234567890",
                "company": "Acme Corp"
            }
        }


class WebFormSubmissionResponse(BaseModel):
    """Response to web form submission - now with AI response."""
    submission_id: str
    status: str
    message: str
    timestamp: datetime
    ai_response: Optional[str] = None  # AI-generated response (if agent processed)
    ticket_id: Optional[str] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None
    estimated_response_time: str = "Immediate (AI processed)"

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "form_abc123xyz",
                "status": "responded",
                "message": "Your submission has been received and processed by our AI agent.",
                "ai_response": "Thank you for contacting us! Based on your issue about API integration, I recommend checking our REST API documentation at docs.example.com/api. Could you share more details about the specific error you're encountering?",
                "ticket_id": "TKT-001",
                "escalated": False,
                "timestamp": "2026-04-30T10:30:00Z",
                "estimated_response_time": "Immediate (AI processed)"
            }
        }


class FileUploadMetadata(BaseModel):
    """Metadata for uploaded file."""
    filename: str
    size_bytes: int
    mime_type: str
    upload_time: datetime


class WebFormMessage:
    """Normalized web form submission."""

    def __init__(
        self,
        submission_id: str,
        customer_name: str,
        customer_email: str,
        subject: str,
        body: str,
        priority: str = "medium",
        phone: Optional[str] = None,
        company: Optional[str] = None,
        attachments: Optional[List[FileUploadMetadata]] = None
    ):
        """Initialize web form message."""
        self.submission_id = submission_id
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.subject = subject
        self.body = body
        self.priority = priority
        self.phone = phone
        self.company = company
        self.attachments = attachments or []
        self.timestamp = datetime.utcnow()
        self.channel = ChannelType.WEB_FORM


class WebFormHandler(ChannelHandler):
    """
    Web form channel handler.

    Responsibilities:
    - Validate form submissions with Pydantic
    - Handle file uploads
    - Prevent XSS and injection attacks
    - Convert to normalized format
    - Provide API responses
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize web form handler."""
        super().__init__(channel_type=ChannelType.WEB_FORM)
        self.settings = settings or Settings()
        self.max_file_size = self.settings.webform_max_file_size
        self.is_authenticated = True  # Web forms don't need auth
        logger.info(f"Web form handler initialized (max file size: {self.max_file_size} bytes)")

    def validate_submission(self, data: dict) -> WebFormSubmissionRequest:
        """
        Validate form submission data.

        Args:
            data: Form data dictionary

        Returns:
            Validated WebFormSubmissionRequest

        Raises:
            ValueError: If validation fails
        """
        try:
            return WebFormSubmissionRequest(**data)
        except Exception as e:
            logger.error(f"Form validation error: {e}")
            raise ValueError(f"Invalid form submission: {str(e)}")

    def validate_file_upload(self, file: UploadFile) -> bool:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check file size (approximate)
            if file.size and file.size > self.max_file_size:
                logger.warning(
                    f"File {file.filename} exceeds max size: "
                    f"{file.size} > {self.max_file_size}"
                )
                return False

            # Whitelist safe MIME types
            safe_types = {
                "application/pdf",
                "text/plain",
                "text/csv",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "image/jpeg",
                "image/png",
                "image/gif",
            }

            if file.content_type not in safe_types:
                logger.warning(
                    f"Unsafe file type: {file.content_type} "
                    f"(file: {file.filename})"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating file {file.filename}: {e}")
            return False

    def generate_submission_id(self) -> str:
        """Generate unique submission ID."""
        return f"form_{uuid.uuid4().hex[:12]}"

    def to_conversation_create(self, form_msg: WebFormMessage) -> ConversationCreate:
        """Convert WebFormMessage to ConversationCreate schema."""
        return ConversationCreate(
            customer_id=form_msg.customer_email,
            channel=ChannelType.WEB_FORM,
            subject=form_msg.subject
        )

    def to_message_schema(self, form_msg: WebFormMessage) -> ConversationMessageSchema:
        """Convert WebFormMessage to ConversationMessageSchema."""
        # Include additional metadata in content
        content = form_msg.body
        if form_msg.phone:
            content += f"\n\nPhone: {form_msg.phone}"
        if form_msg.company:
            content += f"\nCompany: {form_msg.company}"
        if form_msg.attachments:
            content += f"\n\nAttachments: {len(form_msg.attachments)} file(s)"
            for att in form_msg.attachments:
                content += f"\n- {att.filename} ({att.size_bytes} bytes)"

        return ConversationMessageSchema(
            id=form_msg.submission_id,
            content=content,
            sender=form_msg.customer_email,
            channel=ChannelType.WEB_FORM,
            sentiment=None,  # Will be calculated by agent
            intent=None,  # Will be calculated by agent
            timestamp=form_msg.timestamp
        )

    # ========================================================================
    # Base Class Abstract Method Implementations
    # ========================================================================

    def _authenticate(self) -> None:
        """Web forms don't require authentication."""
        self.is_authenticated = True

    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Web forms use synchronous HTTP POST, not polling."""
        return []

    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[ConversationMessageSchema]:
        """Parse raw form data into schema."""
        try:
            form_data = WebFormSubmissionRequest(**raw_message)
            submission_id = self.generate_submission_id()
            form_msg = WebFormMessage(
                submission_id=submission_id,
                customer_name=form_data.customer_name,
                customer_email=form_data.customer_email,
                subject=form_data.subject,
                body=form_data.message,
                priority=form_data.priority,
                phone=form_data.phone,
                company=form_data.company
            )
            return self.to_message_schema(form_msg)
        except Exception as e:
            self.handle_error("PARSE", f"Failed to parse form data: {e}")
            return None

    def get_send_constraints(self) -> Dict[str, Any]:
        """Get web form-specific sending constraints."""
        return {
            "max_length": 5000,
            "supports_media": False,
            "supports_rich_text": False,
            "rate_limit": 1000,
            "formats": ["text"],
            "channel": ChannelType.WEB_FORM.value,
            "note": "Responses sent via email to form submitter"
        }

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send response via email (web form submitter's email).

        Args:
            recipient_id: Email address of form submitter
            content: Response message
            metadata: Optional metadata (subject, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.validate_recipient_id(recipient_id):
            self.handle_error("VALIDATION", f"Invalid email: {recipient_id}")
            return False

        try:
            constraints = self.get_send_constraints()
            sanitized_content = self.sanitize_content(content, constraints["max_length"])

            # TODO: Send email via Gmail handler or SMTP
            self.log_message_sent(recipient_id, content)
            return True

        except Exception as e:
            self.handle_error("SEND", f"Failed to send form response: {e}")
            return False


def create_web_form_router(handler: Optional[WebFormHandler] = None) -> APIRouter:
    """
    Create FastAPI router for web form submissions.

    Args:
        handler: WebFormHandler instance (created if not provided)

    Returns:
        APIRouter with form submission endpoints
    """
    router = APIRouter(prefix="/api/form", tags=["web-form"])
    handler = handler or WebFormHandler()

    # ========================================================================
    # POST /api/form/submit - Web form submission
    # ========================================================================
    @router.post(
        "/submit",
        response_model=WebFormSubmissionResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Submit web form",
        description="Submit a contact/support form with optional file attachments"
    )
    async def submit_form(
        customer_name: str = Form(..., min_length=1, max_length=255),
        customer_email: str = Form(...),
        subject: str = Form(..., min_length=5, max_length=500),
        message: str = Form(..., min_length=10, max_length=5000),
        priority: str = Form(default="medium", pattern="^(low|medium|high|critical)$"),
        phone: Optional[str] = Form(None, max_length=20),
        company: Optional[str] = Form(None, max_length=255),
        files: List[UploadFile] = File(default=[])
    ) -> WebFormSubmissionResponse:
        """
        Handle web form submission.

        Args:
            customer_name: Customer name
            customer_email: Customer email
            subject: Issue subject
            message: Issue description
            priority: Ticket priority
            phone: Optional phone number
            company: Optional company name
            files: Optional file attachments (max 5)

        Returns:
            WebFormSubmissionResponse

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Validate form data
            form_data = {
                "customer_name": customer_name,
                "customer_email": customer_email,
                "subject": subject,
                "message": message,
                "priority": priority,
                "phone": phone,
                "company": company,
                "attachments_count": len(files)
            }

            validated = handler.validate_submission(form_data)

            # Validate file uploads
            attachments = []
            if files:
                if len(files) > 5:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Maximum 5 attachments allowed"
                    )

                for file in files:
                    if not handler.validate_file_upload(file):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid or unsafe file: {file.filename}"
                        )

                    attachments.append(FileUploadMetadata(
                        filename=file.filename,
                        size_bytes=file.size or 0,
                        mime_type=file.content_type or "application/octet-stream",
                        upload_time=datetime.utcnow()
                    ))

            # Create normalized message
            submission_id = handler.generate_submission_id()
            form_msg = WebFormMessage(
                submission_id=submission_id,
                customer_name=validated.customer_name,
                customer_email=validated.customer_email,
                subject=validated.subject,
                body=validated.message,
                priority=validated.priority,
                phone=validated.phone,
                company=validated.company,
                attachments=attachments
            )

            logger.info(
                f"Form submitted: {submission_id} from {customer_email} "
                f"with {len(attachments)} attachment(s)"
            )

            # Process through AI Agent
            try:
                from production.api.agent_integration import process_form_submission_with_agent

                # Call agent asynchronously
                agent_result = await process_form_submission_with_agent(
                    submission_id=submission_id,
                    customer_name=validated.customer_name,
                    customer_email=validated.customer_email,
                    subject=validated.subject,
                    message=validated.message,
                    priority=validated.priority,
                    phone=validated.phone,
                    company=validated.company,
                )

                logger.info(f"✅ Agent processed submission {submission_id}")

                return WebFormSubmissionResponse(
                    submission_id=agent_result.get("submission_id"),
                    status=agent_result.get("status", "responded"),
                    message=agent_result.get("message", "Your submission has been received."),
                    ai_response=agent_result.get("ai_response"),
                    ticket_id=agent_result.get("ticket_id"),
                    escalated=agent_result.get("escalated", False),
                    escalation_reason=agent_result.get("escalation_reason"),
                    timestamp=form_msg.timestamp,
                    estimated_response_time="Immediate (AI processed)"
                )

            except Exception as agent_error:
                logger.warning(f"Agent processing failed: {agent_error}. Using fallback.")

                # Graceful fallback if agent fails
                return WebFormSubmissionResponse(
                    submission_id=submission_id,
                    status="received",
                    message="Thank you for your submission. We've received your message and our team will review it shortly.",
                    ai_response=None,
                    ticket_id=submission_id,
                    escalated=False,
                    timestamp=form_msg.timestamp,
                    estimated_response_time="2-4 hours"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing form submission: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing form submission"
            )

    # ========================================================================
    # GET /api/form/health - Health check
    # ========================================================================
    @router.get(
        "/health",
        summary="Health check",
        description="Check if web form handler is operational"
    )
    async def health_check():
        """Health check endpoint for web form handler."""
        return {
            "status": "healthy",
            "channel": "web_form",
            "timestamp": datetime.utcnow().isoformat()
        }

    return router
