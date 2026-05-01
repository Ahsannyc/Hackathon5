"""
MULTI-CHANNEL API ROUTES
Handles Email (Gmail), WhatsApp, and Web Form channels
Exercise 2.5: Message processor endpoints for all channels

This module provides FastAPI route handlers for multi-channel integration
with support for both real APIs and simulation modes.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from production.channels.gmail_handler_enhanced import get_gmail_handler
from production.channels.whatsapp_handler_enhanced import get_whatsapp_handler
from production.api.agent_integration import process_message_unified

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTERS
# ============================================================================

email_router = APIRouter(prefix="/api/email", tags=["Email"])
whatsapp_router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class EmailIncomingRequest(BaseModel):
    """Incoming email message."""
    from_email: EmailStr
    from_name: str
    subject: str
    body: str


class EmailSimulationRequest(BaseModel):
    """Test email for simulation mode."""
    from_email: EmailStr
    from_name: str
    subject: str
    body: str


class WhatsAppIncomingRequest(BaseModel):
    """Incoming WhatsApp message."""
    from_number: str
    sender_name: str
    body: str


class WhatsAppSimulationRequest(BaseModel):
    """Test WhatsApp message for simulation mode."""
    from_number: str
    sender_name: str
    body: str


class ChannelStatusResponse(BaseModel):
    """Channel health and mode status."""
    channel: str
    status: str
    mode: str  # "REAL" or "SIMULATION"
    ready: bool


class MessageProcessingResponse(BaseModel):
    """Response from processing a message."""
    status: str
    ticket_id: str
    ai_response: str
    channel: str
    timestamp: str


# ============================================================================
# EMAIL ROUTES
# ============================================================================

@email_router.get("/health")
async def email_channel_health() -> ChannelStatusResponse:
    """
    Check Gmail channel health and operational mode.

    Returns:
    - status: "healthy" | "degraded" | "offline"
    - mode: "REAL" (using Gmail API) | "SIMULATION" (test mode)
    - ready: Whether channel can accept messages
    """
    handler = get_gmail_handler()

    return ChannelStatusResponse(
        channel="email",
        status="healthy",
        mode="REAL" if handler.is_real_mode() else "SIMULATION",
        ready=True
    )


@email_router.post("/process")
async def process_email(request: EmailIncomingRequest) -> MessageProcessingResponse:
    """
    Process an incoming email message.

    For testing without real Gmail credentials:
    1. Use /email/simulate endpoint instead
    2. Or provide credentials.json in production/config/

    Exercise 2.2: Email channel integration
    Exercise 2.5: Message processor endpoint
    """
    try:
        logger.info(f"📧 Processing email from {request.from_email}")

        # Use unified multi-channel processor
        result = await process_message_unified(
            message=request.body,
            customer_email=request.from_email,
            customer_name=request.from_name,
            channel="email",
            subject=request.subject
        )

        return MessageProcessingResponse(
            status=result.get("status", "success"),
            ticket_id=result.get("ticket_id", "EMAIL-UNKNOWN"),
            ai_response=result.get("ai_response", ""),
            channel="email",
            timestamp=result.get("timestamp", "")
        )

    except Exception as e:
        logger.error(f"Error processing email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email: {str(e)}"
        )


@email_router.post("/simulate")
async def simulate_email(request: EmailSimulationRequest) -> MessageProcessingResponse:
    """
    Simulate receiving an email (for testing without Gmail credentials).

    This endpoint adds a test email to the Gmail handler's simulation queue
    and processes it through the agent.

    Usage:
    POST /api/email/simulate
    {
        "from_email": "customer@example.com",
        "from_name": "Jane Doe",
        "subject": "API authentication help",
        "body": "How do I set up OAuth 2.0 for my app?"
    }

    Exercise 3.1: Testing multi-channel capability
    """
    try:
        logger.info(f"📧 Simulating email from {request.from_email}")

        # Add to Gmail handler's test queue
        handler = get_gmail_handler()
        handler.add_test_email(
            request.from_email,
            request.from_name,
            request.subject,
            request.body
        )

        # Process through unified multi-channel processor
        result = await process_message_unified(
            message=request.body,
            customer_email=request.from_email,
            customer_name=request.from_name,
            channel="email",
            subject=request.subject
        )

        return MessageProcessingResponse(
            status=result.get("status", "success"),
            ticket_id=result.get("ticket_id", "EMAIL-SIM"),
            ai_response=result.get("ai_response", ""),
            channel="email (simulated)",
            timestamp=result.get("timestamp", "")
        )

    except Exception as e:
        logger.error(f"Error simulating email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to simulate email: {str(e)}"
        )


# ============================================================================
# WHATSAPP ROUTES
# ============================================================================

@whatsapp_router.get("/health")
async def whatsapp_channel_health() -> ChannelStatusResponse:
    """
    Check WhatsApp channel health and operational mode.

    Returns:
    - status: "healthy" | "degraded" | "offline"
    - mode: "REAL" (using Twilio API) | "SIMULATION" (test mode)
    - ready: Whether channel can accept messages
    """
    handler = get_whatsapp_handler()

    return ChannelStatusResponse(
        channel="whatsapp",
        status="healthy",
        mode="REAL" if handler.is_real_mode() else "SIMULATION",
        ready=True
    )


@whatsapp_router.post("/process")
async def process_whatsapp(request: WhatsAppIncomingRequest) -> MessageProcessingResponse:
    """
    Process an incoming WhatsApp message from Twilio webhook.

    For testing without real Twilio credentials:
    1. Use /whatsapp/simulate endpoint instead
    2. Or provide TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env

    Exercise 2.2: WhatsApp channel integration
    Exercise 2.5: Message processor endpoint
    """
    try:
        logger.info(f"💬 Processing WhatsApp from {request.from_number}")

        # Use unified multi-channel processor
        result = await process_message_unified(
            message=request.body,
            customer_email=request.from_number,  # Use phone as unique identifier
            customer_name=request.sender_name,
            channel="whatsapp",
            phone=request.from_number
        )

        return MessageProcessingResponse(
            status=result.get("status", "success"),
            ticket_id=result.get("ticket_id", "WA-UNKNOWN"),
            ai_response=result.get("ai_response", ""),
            channel="whatsapp",
            timestamp=result.get("timestamp", "")
        )

    except Exception as e:
        logger.error(f"Error processing WhatsApp: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process WhatsApp: {str(e)}"
        )


@whatsapp_router.post("/simulate")
async def simulate_whatsapp(request: WhatsAppSimulationRequest) -> MessageProcessingResponse:
    """
    Simulate receiving a WhatsApp message (for testing without Twilio).

    This endpoint adds a test WhatsApp message to the handler's simulation queue
    and processes it through the agent.

    Usage:
    POST /api/whatsapp/simulate
    {
        "from_number": "+1-555-123-4567",
        "sender_name": "Marcus",
        "body": "My password reset link isn't working"
    }

    Exercise 3.1: Testing multi-channel capability
    """
    try:
        logger.info(f"💬 Simulating WhatsApp from {request.from_number}")

        # Add to WhatsApp handler's test queue
        handler = get_whatsapp_handler()
        handler.add_test_message(
            request.from_number,
            request.sender_name,
            request.body
        )

        # Process through unified multi-channel processor
        result = await process_message_unified(
            message=request.body,
            customer_email=request.from_number,  # Use phone as unique identifier
            customer_name=request.sender_name,
            channel="whatsapp",
            phone=request.from_number
        )

        return MessageProcessingResponse(
            status=result.get("status", "success"),
            ticket_id=result.get("ticket_id", "WA-SIM"),
            ai_response=result.get("ai_response", ""),
            channel="whatsapp (simulated)",
            timestamp=result.get("timestamp", "")
        )

    except Exception as e:
        logger.error(f"Error simulating WhatsApp: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to simulate WhatsApp: {str(e)}"
        )


# ============================================================================
# CHANNEL STATUS ENDPOINT
# ============================================================================

class MultiChannelStatusResponse(BaseModel):
    """Status of all channels."""
    web_form: ChannelStatusResponse
    email: ChannelStatusResponse
    whatsapp: ChannelStatusResponse


async def get_multi_channel_status() -> MultiChannelStatusResponse:
    """Get status of all channels (Web Form, Email, WhatsApp)."""
    email_handler = get_gmail_handler()
    whatsapp_handler = get_whatsapp_handler()

    return MultiChannelStatusResponse(
        web_form=ChannelStatusResponse(
            channel="web_form",
            status="healthy",
            mode="ACTIVE",
            ready=True
        ),
        email=ChannelStatusResponse(
            channel="email",
            status="healthy",
            mode="REAL" if email_handler.is_real_mode() else "SIMULATION",
            ready=True
        ),
        whatsapp=ChannelStatusResponse(
            channel="whatsapp",
            status="healthy",
            mode="REAL" if whatsapp_handler.is_real_mode() else "SIMULATION",
            ready=True
        )
    )
