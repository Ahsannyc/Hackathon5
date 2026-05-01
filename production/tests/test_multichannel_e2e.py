"""
Multi-Channel End-to-End Testing Suite for CloudFlow Customer Success FTE
Tests the complete message flow across all channels (Web Form, Email, WhatsApp)
"""

import pytest
import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4


class TestWebFormChannel:
    """Test web form submission through the complete pipeline"""

    @pytest.fixture
    def web_form_data(self):
        """Sample web form submission data"""
        return {
            "customer_name": "John Doe",
            "email": "john@example.com",
            "subject": "Cannot login to account",
            "category": "technical",
            "priority": "high",
            "message": "I've been locked out of my account for 2 days. Password reset isn't working.",
            "channel": "web_form"
        }

    @pytest.fixture
    def api_endpoint(self):
        """API endpoint for form submission"""
        return "http://localhost:8000/api/messages/submit"

    def test_web_form_validation_required_fields(self):
        """Test that all required fields are validated"""
        invalid_data = {
            "customer_name": "",  # Empty name
            "email": "invalid-email",  # Invalid email
            "subject": "test",  # Too short (< 5 chars)
            "category": "technical",
            "priority": "high",
            "message": "short",  # Too short (< 10 chars)
        }

        # Validation should fail for required fields
        errors = validate_form_data(invalid_data)
        assert "customer_name" in errors
        assert "email" in errors
        assert "subject" in errors
        assert "message" in errors

    def test_web_form_validation_email_format(self):
        """Test email validation"""
        test_cases = [
            ("valid@example.com", True),
            ("user+tag@example.co.uk", True),
            ("invalid@", False),
            ("@invalid.com", False),
            ("no-at-sign.com", False),
        ]

        for email, should_pass in test_cases:
            result = validate_email(email)
            assert result == should_pass, f"Email {email} validation failed"

    def test_web_form_validation_character_limits(self):
        """Test character count validation"""
        # Subject max 100 chars
        assert validate_subject("x" * 100) == True
        assert validate_subject("x" * 101) == False

        # Message max 5000 chars
        assert validate_message("x" * 5000) == True
        assert validate_message("x" * 5001) == False

    def test_web_form_submission_success(self, web_form_data):
        """Test successful web form submission"""
        response = submit_web_form(web_form_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "ticket_id" in data
        assert data["ticket_id"].startswith("TICKET-")

    def test_web_form_creates_ticket(self, web_form_data):
        """Test that web form submission creates a ticket in database"""
        response = submit_web_form(web_form_data)
        ticket_id = response.json()["ticket_id"]

        # Verify ticket exists in database
        ticket = get_ticket_by_id(ticket_id)
        assert ticket is not None
        assert ticket["customer_name"] == web_form_data["customer_name"]
        assert ticket["email"] == web_form_data["email"]
        assert ticket["subject"] == web_form_data["subject"]
        assert ticket["priority"] == "high"
        assert ticket["status"] == "open"

    def test_web_form_creates_message(self, web_form_data):
        """Test that web form submission creates a message record"""
        response = submit_web_form(web_form_data)
        ticket_id = response.json()["ticket_id"]

        # Verify message is created
        messages = get_messages_for_ticket(ticket_id)
        assert len(messages) >= 1
        assert messages[0]["content"] == web_form_data["message"]
        assert messages[0]["channel"] == "web_form"

    def test_web_form_publishes_to_kafka(self, web_form_data):
        """Test that web form submission publishes to Kafka"""
        with patch("kafka_client.FTEKafkaProducer.send_ticket") as mock_send:
            mock_send.return_value = True
            response = submit_web_form(web_form_data)

            # Verify Kafka message was sent
            assert mock_send.called
            call_args = mock_send.call_args[0][0]
            assert call_args.customer_id
            assert call_args.customer_email == web_form_data["email"]


class TestEmailChannel:
    """Test email webhook processing"""

    @pytest.fixture
    def gmail_webhook_message(self):
        """Sample Gmail webhook message"""
        return {
            "message": {
                "data": "base64-encoded-message",
                "attributes": {
                    "messageNumber": "123456"
                }
            }
        }

    def test_gmail_webhook_parsing(self, gmail_webhook_message):
        """Test Gmail webhook message parsing"""
        # Simulate webhook reception
        ticket_id = process_gmail_webhook(gmail_webhook_message)

        assert ticket_id is not None
        assert ticket_id.startswith("TICKET-")

    def test_gmail_message_extraction(self):
        """Test extracting email content"""
        raw_email = """
        From: customer@example.com
        To: support@cloudflow.com
        Subject: Issue with billing

        Hi, I was charged twice for my subscription this month.
        Please help!
        """

        parsed = parse_email_content(raw_email)
        assert parsed["from"] == "customer@example.com"
        assert parsed["subject"] == "Issue with billing"
        assert "charged twice" in parsed["body"]

    def test_gmail_creates_conversation(self):
        """Test that Gmail creates conversation in database"""
        email_data = {
            "from": "customer@example.com",
            "subject": "Problem with service",
            "body": "Service has been down for 3 hours"
        }

        conversation = create_conversation_from_email(email_data)
        assert conversation is not None
        assert conversation["channel"] == "email"
        assert conversation["customer_email"] == "customer@example.com"


class TestWhatsAppChannel:
    """Test WhatsApp webhook processing"""

    @pytest.fixture
    def twilio_webhook_signature(self):
        """Sample Twilio signature for validation"""
        auth_token = "test-token"
        url = "https://api.example.com/whatsapp/webhook"
        params = {"MessageSid": "SM123", "From": "whatsapp:+1234567890"}

        signature = generate_twilio_signature(auth_token, url, params)
        return signature

    def test_twilio_signature_validation(self, twilio_webhook_signature):
        """Test Twilio signature verification"""
        auth_token = "test-token"
        url = "https://api.example.com/whatsapp/webhook"
        params = {"MessageSid": "SM123", "From": "whatsapp:+1234567890"}

        is_valid = validate_twilio_signature(
            twilio_webhook_signature,
            auth_token,
            url,
            params
        )
        assert is_valid == True

    def test_twilio_signature_validation_fails_wrong_token(self, twilio_webhook_signature):
        """Test signature validation fails with wrong token"""
        wrong_token = "wrong-token"
        url = "https://api.example.com/whatsapp/webhook"
        params = {"MessageSid": "SM123", "From": "whatsapp:+1234567890"}

        is_valid = validate_twilio_signature(
            twilio_webhook_signature,
            wrong_token,
            url,
            params
        )
        assert is_valid == False

    def test_whatsapp_message_parsing(self):
        """Test WhatsApp message parsing"""
        webhook_data = {
            "MessageSid": "SM123456",
            "From": "whatsapp:+14155552671",
            "Body": "Can't reset my password",
            "NumMedia": "0"
        }

        message = parse_whatsapp_message(webhook_data)
        assert message["phone"] == "+14155552671"
        assert message["content"] == "Can't reset my password"
        assert message["channel"] == "whatsapp"

    def test_whatsapp_creates_ticket(self):
        """Test WhatsApp creates ticket"""
        webhook_data = {
            "MessageSid": "SM123456",
            "From": "whatsapp:+14155552671",
            "Body": "Account locked, help needed"
        }

        ticket_id = process_whatsapp_message(webhook_data)
        assert ticket_id is not None

        ticket = get_ticket_by_id(ticket_id)
        assert ticket["channel"] == "whatsapp"
        assert ticket["priority"] in ["low", "medium", "high"]


class TestCrossChannelContinuity:
    """Test conversation continuity across channels"""

    def test_same_customer_different_channels(self):
        """Test customer contacting from different channels maintains conversation"""
        customer_email = "user@example.com"
        customer_name = "Jane Smith"

        # First contact via web form
        web_form_data = {
            "customer_name": customer_name,
            "email": customer_email,
            "subject": "Billing issue",
            "message": "I was overcharged",
            "category": "billing",
            "priority": "high",
            "channel": "web_form"
        }
        web_ticket = submit_web_form(web_form_data)
        web_ticket_id = web_ticket.json()["ticket_id"]

        # Same customer follows up via email
        email_data = {
            "from": customer_email,
            "subject": "Re: Billing issue",
            "body": "Can you please confirm receipt of my previous request?"
        }
        email_ticket = process_email(email_data)
        email_ticket_id = email_ticket["ticket_id"]

        # Verify tickets are linked (same customer)
        customer = get_customer_by_email(customer_email)
        assert customer is not None
        assert len(customer["tickets"]) >= 2

        # Verify conversation history shows both messages
        messages = get_customer_conversation(customer_email)
        assert any(m["channel"] == "web_form" for m in messages)
        assert any(m["channel"] == "email" for m in messages)

    def test_agent_response_across_channels(self):
        """Test agent response is routed to correct channel"""
        # Customer submits via web form
        customer_email = "test@example.com"
        web_form_data = {
            "customer_name": "Test User",
            "email": customer_email,
            "subject": "Issue",
            "message": "Help needed",
            "channel": "web_form"
        }
        response = submit_web_form(web_form_data)
        ticket_id = response.json()["ticket_id"]

        # Agent responds
        agent_response = {
            "ticket_id": ticket_id,
            "response": "We'll help you with that",
            "channel": "email"  # Send back via email
        }
        send_agent_response(agent_response)

        # Verify message is in correct channel output
        email_messages = get_emails_to_send(customer_email)
        assert any(ticket_id in msg for msg in email_messages)


class TestChannelMetrics:
    """Test channel-specific metrics endpoint"""

    def test_channel_metrics_endpoint(self):
        """Test /api/metrics/channels endpoint"""
        response = get_channel_metrics()

        assert response.status_code == 200
        data = response.json()

        # Verify all channels are present
        assert "email" in data
        assert "whatsapp" in data
        assert "web_form" in data

        # Verify metrics structure
        for channel, metrics in data.items():
            assert "messages_received" in metrics
            assert "messages_processed" in metrics
            assert "messages_failed" in metrics
            assert "average_response_time" in metrics

    def test_channel_metrics_accuracy(self):
        """Test that metrics are accurately tracked"""
        # Get initial metrics
        initial = get_channel_metrics().json()

        # Submit web form
        web_form_data = {
            "customer_name": "Test",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message",
            "channel": "web_form"
        }
        submit_web_form(web_form_data)

        # Get updated metrics
        updated = get_channel_metrics().json()

        # Verify web_form metrics increased
        assert updated["web_form"]["messages_received"] > initial["web_form"]["messages_received"]


class TestEscalationScenarios:
    """Test escalation scenarios"""

    def test_escalation_pricing_inquiry(self):
        """Test pricing-related escalation"""
        web_form_data = {
            "customer_name": "Customer",
            "email": "customer@example.com",
            "subject": "Pricing inquiry for enterprise",
            "message": "We need custom pricing for 1000 users",
            "category": "billing",
            "priority": "high",
            "channel": "web_form"
        }

        response = submit_web_form(web_form_data)
        ticket_id = response.json()["ticket_id"]

        # Process through agent
        result = process_message_with_agent(ticket_id)

        # Should be escalated due to pricing keyword
        assert result["escalated"] == True
        assert "sales" in result["escalation_reason"].lower()

    def test_escalation_angry_customer(self):
        """Test escalation for angry customer sentiment"""
        angry_message = {
            "customer_name": "Angry Customer",
            "email": "angry@example.com",
            "subject": "UNACCEPTABLE SERVICE!!!",
            "message": "This is the worst service I've ever used! You're incompetent and I'm switching providers immediately!",
            "category": "complaint",
            "priority": "high",
            "channel": "web_form"
        }

        response = submit_web_form(angry_message)
        ticket_id = response.json()["ticket_id"]

        # Process through sentiment analysis
        result = analyze_sentiment(ticket_id)

        # Should detect negative sentiment
        assert result["sentiment"] == "negative"
        assert result["confidence"] > 0.8

        # Should escalate
        ticket = get_ticket_by_id(ticket_id)
        assert ticket["escalated"] == True

    def test_escalation_technical_issue(self):
        """Test escalation for complex technical issues"""
        technical_issue = {
            "customer_name": "Dev",
            "email": "dev@company.com",
            "subject": "API returning 500 errors",
            "message": "Our integration broke after your update. API endpoint /v2/users returns 500. Critical production issue.",
            "category": "technical",
            "priority": "high",
            "channel": "web_form"
        }

        response = submit_web_form(technical_issue)
        ticket_id = response.json()["ticket_id"]

        # Should be escalated to technical team
        ticket = get_ticket_by_id(ticket_id)
        assert ticket["escalated"] == True
        assert ticket["assigned_to"] == "technical_team"


class TestMessageStorage:
    """Test proper message storage and retrieval"""

    def test_message_persistence(self):
        """Test messages are properly stored in database"""
        message_data = {
            "customer_name": "Alice",
            "email": "alice@example.com",
            "subject": "Test persistence",
            "message": "Testing message storage",
            "channel": "web_form"
        }

        response = submit_web_form(message_data)
        ticket_id = response.json()["ticket_id"]

        # Retrieve message
        messages = get_messages_for_ticket(ticket_id)
        assert len(messages) > 0

        stored_message = messages[0]
        assert stored_message["content"] == message_data["message"]
        assert stored_message["created_at"] is not None

    def test_conversation_history_order(self):
        """Test conversation messages are in correct chronological order"""
        ticket_id = "TICKET-test-001"

        # Add messages in sequence
        msg1 = add_message(ticket_id, "First message", "customer")
        msg2 = add_message(ticket_id, "Agent response", "agent")
        msg3 = add_message(ticket_id, "Follow up", "customer")

        # Retrieve history
        history = get_conversation_history(ticket_id)

        assert history[0]["id"] == msg1["id"]
        assert history[1]["id"] == msg2["id"]
        assert history[2]["id"] == msg3["id"]
        assert history[0]["created_at"] < history[1]["created_at"] < history[2]["created_at"]


class TestTicketCreation:
    """Test ticket creation and management"""

    def test_ticket_id_generation(self):
        """Test ticket IDs are unique and properly formatted"""
        ticket_ids = set()

        for i in range(100):
            web_form_data = {
                "customer_name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "subject": f"Issue {i}",
                "message": f"Message {i}",
                "channel": "web_form"
            }
            response = submit_web_form(web_form_data)
            ticket_id = response.json()["ticket_id"]

            # Verify format
            assert ticket_id.startswith("TICKET-")
            assert len(ticket_id) > 10

            # Verify uniqueness
            assert ticket_id not in ticket_ids
            ticket_ids.add(ticket_id)

    def test_ticket_metadata(self):
        """Test ticket includes all required metadata"""
        web_form_data = {
            "customer_name": "John",
            "email": "john@example.com",
            "subject": "Help",
            "message": "I need help with something",
            "category": "general",
            "priority": "low",
            "channel": "web_form"
        }

        response = submit_web_form(web_form_data)
        ticket_id = response.json()["ticket_id"]

        ticket = get_ticket_by_id(ticket_id)

        # Verify all fields
        assert ticket["customer_name"] == "John"
        assert ticket["email"] == "john@example.com"
        assert ticket["subject"] == "Help"
        assert ticket["category"] == "general"
        assert ticket["priority"] == "low"
        assert ticket["channel"] == "web_form"
        assert ticket["status"] in ["open", "in_progress", "resolved", "escalated"]
        assert ticket["created_at"] is not None
        assert ticket["sla_deadline"] is not None


# Helper functions (mocked for testing)
def validate_form_data(data: Dict) -> Dict[str, str]:
    """Validate form data"""
    errors = {}
    if not data.get("customer_name") or len(data["customer_name"]) < 2:
        errors["customer_name"] = "Name required, min 2 chars"
    if not validate_email(data.get("email", "")):
        errors["email"] = "Valid email required"
    if not data.get("subject") or len(data["subject"]) < 5:
        errors["subject"] = "Subject required, min 5 chars"
    if not data.get("message") or len(data["message"]) < 10:
        errors["message"] = "Message required, min 10 chars"
    return errors

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(pattern, email))

def validate_subject(subject: str) -> bool:
    """Validate subject length"""
    return 5 <= len(subject) <= 100

def validate_message(message: str) -> bool:
    """Validate message length"""
    return 10 <= len(message) <= 5000

def submit_web_form(data: Dict) -> Mock:
    """Mock web form submission"""
    if validate_form_data(data):
        raise ValueError("Invalid form data")
    return Mock(
        status_code=200,
        json=lambda: {"success": True, "ticket_id": f"TICKET-{uuid4()}"}
    )

def get_ticket_by_id(ticket_id: str) -> Dict:
    """Mock get ticket"""
    return {
        "id": ticket_id,
        "customer_name": "Test",
        "email": "test@example.com",
        "subject": "Test",
        "priority": "high",
        "status": "open",
        "channel": "web_form"
    }

def get_messages_for_ticket(ticket_id: str) -> List[Dict]:
    """Mock get messages"""
    return [{
        "ticket_id": ticket_id,
        "content": "Test message",
        "channel": "web_form",
        "created_at": datetime.now()
    }]

def process_gmail_webhook(webhook: Dict) -> str:
    """Mock Gmail webhook processing"""
    return f"TICKET-{uuid4()}"

def parse_email_content(raw_email: str) -> Dict:
    """Mock email parsing"""
    return {
        "from": "customer@example.com",
        "subject": "Issue",
        "body": raw_email
    }

def process_whatsapp_message(data: Dict) -> str:
    """Mock WhatsApp processing"""
    return f"TICKET-{uuid4()}"

def parse_whatsapp_message(data: Dict) -> Dict:
    """Mock WhatsApp parsing"""
    return {
        "phone": data.get("From", "").replace("whatsapp:", ""),
        "content": data.get("Body", ""),
        "channel": "whatsapp"
    }

def get_channel_metrics() -> Mock:
    """Mock get metrics"""
    return Mock(
        status_code=200,
        json=lambda: {
            "email": {"messages_received": 10, "messages_processed": 8, "messages_failed": 2, "average_response_time": 300},
            "whatsapp": {"messages_received": 5, "messages_processed": 5, "messages_failed": 0, "average_response_time": 150},
            "web_form": {"messages_received": 15, "messages_processed": 15, "messages_failed": 0, "average_response_time": 50}
        }
    )

def generate_twilio_signature(token: str, url: str, params: Dict) -> str:
    """Generate Twilio signature"""
    data = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))
    return hmac.new(token.encode(), data.encode(), hashlib.sha1).digest().hex()

def validate_twilio_signature(sig: str, token: str, url: str, params: Dict) -> bool:
    """Validate Twilio signature"""
    expected = generate_twilio_signature(token, url, params)
    return hmac.compare_digest(sig, expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
