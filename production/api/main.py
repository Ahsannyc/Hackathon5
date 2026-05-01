"""
CloudFlow Customer Success AI - Main FastAPI Application

Complete multi-channel integration service that:
1. Receives inquiries from Email (Gmail), WhatsApp (Twilio), and Web Forms
2. Normalizes and publishes to Kafka topic: fte.tickets.incoming
3. Consumes responses from Kafka: fte.responses, fte.escalations
4. Sends responses back via appropriate channels
5. Tracks metrics and provides monitoring endpoints

Architecture:
┌─────────────────────────────────────────┐
│      FastAPI Service (This File)        │
├─────────────────────────────────────────┤
│ • Health checks                         │
│ • Channel webhooks (Gmail, WhatsApp)    │
│ • Web form submission                   │
│ • Customer lookup                       │
│ • Metrics collection                    │
│ • Kafka producer (publish messages)     │
│ • Kafka consumer (background tasks)     │
│ • CORS middleware                       │
└─────────────────────────────────────────┘
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from collections import defaultdict

from fastapi import FastAPI, Header, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator

from production.config.settings import Settings
from production.channels.web_form_handler import (
    WebFormHandler, create_web_form_router, WebFormSubmissionResponse
)
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.gmail_handler import GmailHandler
from production.api.multi_channel_routes import email_router, whatsapp_router
from production.database.schema import ChannelType
from production.kafka_client import (
    FTEKafkaProducer, FTEKafkaConsumer,
    TicketMessage, FTETopics
)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ============================================================================
# SETTINGS & INITIALIZATION
# ============================================================================

settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="CloudFlow Customer Success AI",
    description="Multi-channel customer support AI with Kafka streaming",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ============================================================================
# GLOBAL STATE
# ============================================================================

# Kafka producer (initialized on startup)
kafka_producer: Optional[FTEKafkaProducer] = None

# Channel metrics tracking
channel_metrics = {
    "email": {"received": 0, "processed": 0, "failed": 0},
    "whatsapp": {"received": 0, "processed": 0, "failed": 0},
    "web_form": {"received": 0, "processed": 0, "failed": 0},
}

# Customer cache for lookup
customer_cache: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

allowed_origins = [
    origin.strip() for origin in settings.allowed_origins.split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods.split(","),
    allow_headers=settings.cors_allow_headers.split(",")
)

logger.info(f"CORS configured for origins: {allowed_origins}")

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SupportFormSubmission(BaseModel):
    """Web form submission with validation."""
    customer_name: str = Field(..., min_length=2, max_length=255)
    customer_email: EmailStr
    subject: str = Field(..., min_length=3, max_length=500)
    message: str = Field(..., min_length=5, max_length=5000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9\s\-()]{10,}$")
    company: Optional[str] = Field(None, max_length=255)

    @validator('message')
    def validate_message_content(cls, v):
        """Prevent XSS - remove script tags."""
        if '<script' in v.lower() or 'javascript:' in v.lower():
            raise ValueError("Message contains invalid content")
        return v

    class Config:
        example = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "subject": "Cannot reset password",
            "message": "I tried to reset my password but did not receive an email.",
            "priority": "high",
            "phone": "+1234567890",
            "company": "Acme Corp"
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    environment: str
    services: dict
    kafka_topics: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime


class CustomerLookupResponse(BaseModel):
    """Customer lookup response."""
    customer_id: str
    name: str
    email: str
    phone: Optional[str]
    total_tickets: int
    last_contacted: Optional[datetime]
    conversation_history: list


class ChannelMetricsResponse(BaseModel):
    """Channel metrics response."""
    timestamp: datetime
    email: dict
    whatsapp: dict
    web_form: dict
    total_received: int
    total_processed: int
    total_failed: int


class KafkaHealthResponse(BaseModel):
    """Kafka health check response."""
    status: str
    topics: dict
    timestamp: datetime


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Request Error",
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# KAFKA HELPER FUNCTIONS
# ============================================================================

async def publish_to_kafka(
    customer_id: str,
    customer_email: str,
    customer_name: str,
    channel: str,
    subject: str,
    message: str,
    priority: str = "medium",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish message to Kafka topic: fte.tickets.incoming

    Args:
        customer_id: Customer identifier
        customer_email: Customer email
        customer_name: Customer name
        channel: Channel type (email, whatsapp, web_form)
        subject: Message subject
        message: Message content
        priority: Priority level
        metadata: Additional metadata

    Returns:
        True if published successfully
    """
    try:
        if not kafka_producer:
            logger.warning("Kafka producer not initialized")
            return False

        ticket = TicketMessage(
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            channel=channel,
            subject=subject,
            message=message,
            priority=priority,
            metadata=metadata or {}
        )

        message_id = await kafka_producer.send_ticket(ticket)

        if message_id:
            logger.info(f"Message published to Kafka: {message_id}")
            return True
        else:
            logger.error("Failed to publish message to Kafka")
            return False

    except Exception as e:
        logger.error(f"Error publishing to Kafka: {e}")
        return False


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check overall application health"
)
async def health_check() -> HealthCheckResponse:
    """
    Check application health and service status.

    Returns:
        HealthCheckResponse with service status
    """
    kafka_topics_status = {}
    if kafka_producer:
        kafka_topics_status = {
            FTETopics.TICKETS_INCOMING.value: "ready",
            FTETopics.METRICS.value: "ready",
            FTETopics.ESCALATIONS.value: "ready",
            FTETopics.RESPONSES.value: "ready",
        }

    services_status = {
        "database": "configured",
        "gmail": "ready" if settings.gmail_enabled else "disabled",
        "whatsapp": "ready" if settings.whatsapp_enabled else "disabled",
        "web_form": "ready" if settings.webform_enabled else "disabled",
        "kafka": "connected" if kafka_producer else "disconnected",
        "redis": "configured",
    }

    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        services=services_status,
        kafka_topics=kafka_topics_status
    )


@app.get(
    "/api/health",
    response_model=HealthCheckResponse,
    summary="API health check",
    description="Check API health"
)
async def api_health_check() -> HealthCheckResponse:
    """API health check endpoint."""
    return await health_check()


@app.get(
    "/api/health/kafka",
    response_model=KafkaHealthResponse,
    summary="Kafka health check",
    description="Check Kafka connectivity and topics"
)
async def kafka_health_check() -> KafkaHealthResponse:
    """
    Check Kafka health status.

    Returns:
        KafkaHealthResponse with topic status
    """
    topics_status = {
        FTETopics.TICKETS_INCOMING.value: "ready" if kafka_producer else "unavailable",
        FTETopics.METRICS.value: "ready" if kafka_producer else "unavailable",
        FTETopics.ESCALATIONS.value: "ready" if kafka_producer else "unavailable",
        FTETopics.RESPONSES.value: "ready" if kafka_producer else "unavailable",
    }

    return KafkaHealthResponse(
        status="connected" if kafka_producer else "disconnected",
        topics=topics_status,
        timestamp=datetime.utcnow()
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get(
    "/",
    summary="API root",
    description="CloudFlow Customer Success AI API"
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CloudFlow Customer Success AI",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health",
        "kafka": "integrated",
        "channels": ["email", "whatsapp", "web_form"]
    }


# ============================================================================
# WEB FORM HANDLER INTEGRATION
# ============================================================================

web_form_handler = WebFormHandler(settings=settings)
web_form_router = create_web_form_router(handler=web_form_handler)
app.include_router(web_form_router)

# Include multi-channel routers (email and WhatsApp)
app.include_router(email_router)
app.include_router(whatsapp_router)

logger.info("Web form handler integrated: POST /api/form/submit")
logger.info("Multi-channel handlers integrated: /api/email and /api/whatsapp")


# ============================================================================
# CUSTOM WEB FORM ENDPOINT WITH KAFKA
# ============================================================================

@app.post(
    "/api/messages/submit",
    response_model=dict,
    summary="Submit customer message",
    description="Submit message via web form to Kafka"
)
async def submit_customer_message(
    form: SupportFormSubmission,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Submit customer message and publish to Kafka.

    Args:
        form: Form submission data
        background_tasks: Background task executor

    Returns:
        Submission status and ID
    """
    try:
        # Generate customer ID if not exists
        customer_id = f"CUST-{form.customer_email.split('@')[0]}-{hash(form.customer_email) % 10000}"

        # Update metrics
        channel_metrics["web_form"]["received"] += 1

        # Publish to Kafka
        success = await publish_to_kafka(
            customer_id=customer_id,
            customer_email=form.customer_email,
            customer_name=form.customer_name,
            channel="web_form",
            subject=form.subject,
            message=form.message,
            priority=form.priority,
            metadata={
                "phone": form.phone,
                "company": form.company,
            }
        )

        if success:
            channel_metrics["web_form"]["processed"] += 1
            logger.info(f"Message submitted: {customer_id} via web_form")

            return {
                "status": "submitted",
                "customer_id": customer_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Your message has been received. We will respond shortly."
            }
        else:
            channel_metrics["web_form"]["failed"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process message"
            )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        channel_metrics["web_form"]["failed"] += 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting message: {e}")
        channel_metrics["web_form"]["failed"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing submission"
        )


# ============================================================================
# WHATSAPP WEBHOOK INTEGRATION
# ============================================================================

if settings.whatsapp_enabled:
    try:
        whatsapp_handler = WhatsAppHandler(settings=settings)
    except Exception as e:
        logger.warning(f"WhatsApp handler disabled: {e}")

    @app.get(
        "/api/whatsapp/webhook",
        summary="WhatsApp webhook verification",
        description="Verify WhatsApp webhook (GET request from Twilio)"
    )
    async def whatsapp_webhook_verify(
        hub_mode: str = None,
        hub_challenge: str = None,
        hub_verify_token: str = None
    ) -> dict:
        """
        Verify WhatsApp webhook subscription.

        This endpoint is called by Twilio to verify the webhook URL.

        Args:
            hub_mode: Subscription mode (should be "subscribe")
            hub_challenge: Challenge token to echo back
            hub_verify_token: Token to verify webhook owner

        Returns:
            Challenge token or error

        Raises:
            HTTPException: If verification fails
        """
        try:
            if hub_verify_token != settings.whatsapp_webhook_verify_token:
                logger.warning("Invalid WhatsApp webhook verify token")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid verify token"
                )

            if hub_mode == "subscribe" and hub_challenge:
                logger.info("WhatsApp webhook verified successfully")
                return {"challenge": hub_challenge}

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook verification parameters"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying WhatsApp webhook: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook verification failed"
            )

    @app.post(
        "/api/whatsapp/webhook",
        summary="WhatsApp message webhook",
        description="Receive incoming WhatsApp messages from Twilio"
    )
    async def whatsapp_webhook_receive(
        request: Request,
        x_twilio_signature: str = Header(None),
        background_tasks: BackgroundTasks = None
    ) -> dict:
        """
        Receive incoming WhatsApp messages and publish to Kafka.

        Args:
            request: FastAPI request object
            x_twilio_signature: Twilio signature header
            background_tasks: Background task executor

        Returns:
            Acknowledgment response

        Raises:
            HTTPException: If signature validation fails
        """
        try:
            body = await request.body()
            form_data = await request.form()

            # Validate Twilio signature
            url = str(request.url)
            post_params = dict(form_data)

            if not whatsapp_handler.validate_webhook_signature(
                url, post_params, x_twilio_signature
            ):
                logger.warning("Invalid WhatsApp webhook signature")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid webhook signature"
                )

            # Parse message
            whatsapp_msg = whatsapp_handler.parse_webhook_payload(post_params)

            if not whatsapp_msg:
                logger.warning("Failed to parse WhatsApp message")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to parse message"
                )

            # Update metrics
            channel_metrics["whatsapp"]["received"] += 1

            # Publish to Kafka
            customer_id = f"CUST-WA-{whatsapp_msg.sender_number[-10:]}"

            success = await publish_to_kafka(
                customer_id=customer_id,
                customer_email=f"{whatsapp_msg.sender_number}@whatsapp.local",
                customer_name=whatsapp_msg.sender_name or whatsapp_msg.sender_number,
                channel="whatsapp",
                subject="WhatsApp message",
                message=whatsapp_msg.body,
                metadata={
                    "phone": whatsapp_msg.sender_number,
                    "message_id": whatsapp_msg.message_id,
                }
            )

            if success:
                channel_metrics["whatsapp"]["processed"] += 1

            logger.info(
                f"WhatsApp message received from {whatsapp_msg.sender_number}: "
                f"{whatsapp_msg.body[:50]}..."
            )

            return {"status": "received"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {e}")
            channel_metrics["whatsapp"]["failed"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing webhook"
            )

    @app.post(
        "/api/whatsapp/status",
        summary="WhatsApp message status callback",
        description="Receive WhatsApp message delivery status updates"
    )
    async def whatsapp_status_callback(
        request: Request,
        x_twilio_signature: str = Header(None)
    ) -> dict:
        """
        Handle WhatsApp message status updates.

        Called by Twilio to report message delivery status.

        Args:
            request: FastAPI request object
            x_twilio_signature: Twilio signature header

        Returns:
            Acknowledgment response
        """
        try:
            form_data = await request.form()
            post_params = dict(form_data)

            # Validate signature
            url = str(request.url)
            if not whatsapp_handler.validate_webhook_signature(
                url, post_params, x_twilio_signature
            ):
                logger.warning("Invalid WhatsApp status callback signature")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid signature"
                )

            # Log status
            message_sid = post_params.get("MessageSid", "unknown")
            message_status = post_params.get("MessageStatus", "unknown")
            phone_number = post_params.get("To", "unknown")

            logger.info(
                f"WhatsApp message status: sid={message_sid}, "
                f"status={message_status}, to={phone_number}"
            )

            return {"status": "acknowledged"}

        except Exception as e:
            logger.error(f"Error processing WhatsApp status callback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing status"
            )

    logger.info("WhatsApp handler integrated: /api/whatsapp/webhook, /api/whatsapp/status")


# ============================================================================
# GMAIL WEBHOOK INTEGRATION
# ============================================================================

if settings.gmail_enabled:
    try:
        gmail_handler = GmailHandler(credentials_path="credentials.json")
    except Exception as e:
        logger.warning(f"Gmail handler disabled: {e}")

    @app.get(
        "/api/gmail/callback",
        summary="Gmail OAuth callback",
        description="OAuth2 callback endpoint for Gmail authentication"
    )
    async def gmail_oauth_callback(code: str = None, state: str = None) -> dict:
        """
        Handle Gmail OAuth callback.

        Args:
            code: OAuth authorization code
            state: State parameter for security

        Returns:
            Authentication status
        """
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code"
            )

        logger.info("Gmail OAuth callback received")
        return {"status": "authenticated", "code": code[:10] + "..."}

    @app.post(
        "/api/gmail/webhook",
        summary="Gmail Pub/Sub webhook",
        description="Receive notifications from Gmail Pub/Sub"
    )
    async def gmail_webhook_receive(request: Request) -> dict:
        """
        Receive Gmail Pub/Sub notifications.

        Note: This is a placeholder for Pub/Sub integration.
        Polling is used as fallback.

        Args:
            request: FastAPI request

        Returns:
            Acknowledgment
        """
        try:
            body = await request.json()
            logger.info(f"Gmail webhook notification: {body}")
            return {"status": "acknowledged"}
        except Exception as e:
            logger.error(f"Error processing Gmail webhook: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing notification"
            )

    @app.get(
        "/api/gmail/fetch",
        summary="Fetch unread emails",
        description="Manually trigger email fetch (for testing/polling)"
    )
    async def fetch_gmail_messages(background_tasks: BackgroundTasks = None) -> dict:
        """
        Manually fetch unread emails from Gmail and publish to Kafka.

        This is useful for testing and as a fallback to webhook/Pub/Sub.

        Returns:
            List of fetched messages
        """
        try:
            messages = gmail_handler.fetch_unread_messages()
            logger.info(f"Fetched {len(messages)} emails from Gmail")

            # Update metrics
            channel_metrics["email"]["received"] += len(messages)

            # Publish each message to Kafka
            for msg in messages:
                customer_id = f"CUST-{msg.sender_email.split('@')[0]}-{hash(msg.sender_email) % 10000}"

                success = await publish_to_kafka(
                    customer_id=customer_id,
                    customer_email=msg.sender_email,
                    customer_name=msg.sender_name or msg.sender_email,
                    channel="email",
                    subject=msg.subject,
                    message=msg.body,
                    metadata={
                        "email_id": msg.message_id,
                        "gmail_message_id": msg.message_id,
                    }
                )

                if success:
                    channel_metrics["email"]["processed"] += 1
                else:
                    channel_metrics["email"]["failed"] += 1

            return {
                "status": "fetched",
                "count": len(messages),
                "messages": [
                    {
                        "id": msg.message_id,
                        "from": msg.sender_email,
                        "subject": msg.subject,
                        "preview": msg.body[:100]
                    }
                    for msg in messages
                ]
            }

        except Exception as e:
            logger.error(f"Error fetching Gmail messages: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching messages"
            )

    logger.info("Gmail handler integrated: /api/gmail/webhook, /api/gmail/fetch")


# ============================================================================
# CUSTOMER LOOKUP ENDPOINT
# ============================================================================

@app.get(
    "/api/customers/lookup",
    response_model=CustomerLookupResponse,
    summary="Customer lookup",
    description="Lookup customer information by email or ID"
)
async def lookup_customer(
    email: Optional[str] = None,
    customer_id: Optional[str] = None
) -> CustomerLookupResponse:
    """
    Lookup customer information.

    Args:
        email: Customer email (optional)
        customer_id: Customer ID (optional)

    Returns:
        Customer information and history

    Raises:
        HTTPException: If customer not found
    """
    try:
        if not email and not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide email or customer_id"
            )

        # Check cache first
        lookup_key = customer_id or email
        if lookup_key in customer_cache:
            logger.debug(f"Customer found in cache: {lookup_key}")
            return CustomerLookupResponse(**customer_cache[lookup_key])

        # For now, return placeholder data
        # In production, this would query the database
        customer_id = customer_id or f"CUST-{email.split('@')[0]}"
        customer_data = {
            "customer_id": customer_id,
            "name": "Valued Customer",
            "email": email or "unknown@example.com",
            "phone": None,
            "total_tickets": 0,
            "last_contacted": None,
            "conversation_history": []
        }

        # Cache the result
        customer_cache[lookup_key] = customer_data

        logger.info(f"Customer lookup: {lookup_key}")
        return CustomerLookupResponse(**customer_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error looking up customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error looking up customer"
        )


# ============================================================================
# CHANNEL METRICS ENDPOINT
# ============================================================================

@app.get(
    "/api/metrics/channels",
    response_model=ChannelMetricsResponse,
    summary="Channel metrics",
    description="Get metrics for all channels"
)
async def get_channel_metrics() -> ChannelMetricsResponse:
    """
    Get current channel metrics.

    Returns:
        ChannelMetricsResponse with metrics for all channels
    """
    total_received = sum(m["received"] for m in channel_metrics.values())
    total_processed = sum(m["processed"] for m in channel_metrics.values())
    total_failed = sum(m["failed"] for m in channel_metrics.values())

    return ChannelMetricsResponse(
        timestamp=datetime.utcnow(),
        email=channel_metrics["email"],
        whatsapp=channel_metrics["whatsapp"],
        web_form=channel_metrics["web_form"],
        total_received=total_received,
        total_processed=total_processed,
        total_failed=total_failed
    )


# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    global kafka_producer

    logger.info("=" * 80)
    logger.info("CloudFlow Customer Success AI - Starting up")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug: {settings.debug}")
    logger.info(f"API Port: {settings.api_port}")
    logger.info(f"Kafka Bootstrap: {settings.kafka_bootstrap_servers}")
    logger.info(f"Gmail: {'enabled' if settings.gmail_enabled else 'disabled'}")
    logger.info(f"WhatsApp: {'enabled' if settings.whatsapp_enabled else 'disabled'}")
    logger.info(f"Web Form: {'enabled' if settings.webform_enabled else 'disabled'}")

    try:
        # Initialize and start Kafka producer
        kafka_producer = FTEKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
        await kafka_producer.start()
        logger.info("Kafka producer started successfully")
        logger.info(f"Topics: {[t.value for t in FTETopics]}")

    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")
        logger.warning("Service starting without Kafka (messages will not be published)")

    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    global kafka_producer

    logger.info("CloudFlow Customer Success AI - Shutting down")

    # Close Kafka producer
    if kafka_producer:
        try:
            await kafka_producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "production.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
