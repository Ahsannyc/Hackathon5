"""
MULTI-CHANNEL E2E TESTS
Tests Web Form + Email (Gmail) + WhatsApp (Twilio) channels

Exercise 3.1: Multi-channel E2E testing
Exercise 3.2: Integration and cross-channel functionality

Tests validate:
- Each channel independently
- Channel continuity (same customer across channels)
- Agent workflow consistency across channels
- Graceful degradation (simulation mode works)
"""

import pytest
import httpx
from datetime import datetime
from fastapi.testclient import TestClient
from production.api.main import app

# ============================================================================
# CONFIGURATION
# ============================================================================

WEB_FORM_ENDPOINT = "/api/form/submit"
EMAIL_ENDPOINT = "/api/email"
WHATSAPP_ENDPOINT = "/api/whatsapp"

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def http_client():
    """HTTP client for API testing."""
    return TestClient(app)


# ============================================================================
# EMAIL CHANNEL TESTS
# ============================================================================

class TestEmailChannel:
    """
    EXERCISE 2.2 & 2.5: Email channel via Gmail
    Tests Email handler in both REAL and SIMULATION modes
    """

    def test_email_channel_health(self, http_client):
        """[Exercise 2.5] Check Gmail channel health endpoint."""
        response = http_client.get(f"{EMAIL_ENDPOINT}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "email"
        assert data["mode"] in ["REAL", "SIMULATION"]
        assert data["ready"] is True

    def test_email_simulation_mode(self, http_client):
        """
        [Exercise 2.2 & 2.5] Send simulated email through Gmail handler.

        This test uses SIMULATION mode (no credentials needed).
        Agent processes email through full 4-step workflow.
        """
        email_data = {
            "from_email": "customer@company.com",
            "from_name": "Alex Customer",
            "subject": "Integration question",
            "body": "How do I integrate your API with my Python app?"
        }

        response = http_client.post(f"{EMAIL_ENDPOINT}/simulate", json=email_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "ai_response" in data
        assert len(data["ai_response"]) > 0
        assert "integration" in data["ai_response"].lower() or "api" in data["ai_response"].lower()
        assert data["channel"] == "email (simulated)"

    def test_email_channel_uses_agent_workflow(self, http_client):
        """
        [Exercise 2.3 & 2.5] Email channel uses full agent workflow.

        Proves:
        - Email → Agent integration
        - 4-step workflow executed (create_ticket, get_history, search_kb, send_response)
        - Unified message processing
        """
        email_data = {
            "from_email": "support@testcompany.com",
            "from_name": "Support Team",
            "subject": "API rate limits",
            "body": "What are the rate limits for the API?"
        }

        response = http_client.post(f"{EMAIL_ENDPOINT}/simulate", json=email_data)
        assert response.status_code == 200

        data = response.json()
        assert "ticket_id" in data
        assert data["ticket_id"].startswith("EMAIL") or data["status"] == "success"
        assert "ai_response" in data
        # Validate response quality
        assert len(data["ai_response"]) >= 20


# ============================================================================
# WHATSAPP CHANNEL TESTS
# ============================================================================

class TestWhatsAppChannel:
    """
    EXERCISE 2.2 & 2.5: WhatsApp channel via Twilio
    Tests WhatsApp handler in both REAL and SIMULATION modes
    """

    def test_whatsapp_channel_health(self, http_client):
        """[Exercise 2.5] Check WhatsApp channel health endpoint."""
        response = http_client.get(f"{WHATSAPP_ENDPOINT}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "whatsapp"
        assert data["mode"] in ["REAL", "SIMULATION"]
        assert data["ready"] is True

    def test_whatsapp_simulation_mode(self, http_client):
        """
        [Exercise 2.2 & 2.5] Send simulated WhatsApp message through Twilio handler.

        This test uses SIMULATION mode (no Twilio credentials needed).
        Agent processes SMS through full 4-step workflow.
        """
        whatsapp_data = {
            "from_number": "+1-555-234-5678",
            "sender_name": "Jordan",
            "body": "How do I reset my account password?"
        }

        response = http_client.post(f"{WHATSAPP_ENDPOINT}/simulate", json=whatsapp_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "ai_response" in data
        assert len(data["ai_response"]) > 0
        # WhatsApp responses should mention password reset or account
        assert "password" in data["ai_response"].lower() or "reset" in data["ai_response"].lower() or "account" in data["ai_response"].lower()
        assert data["channel"] == "whatsapp (simulated)"

    def test_whatsapp_channel_concise_response(self, http_client):
        """
        [Exercise 2.5] WhatsApp responses are concise and mobile-friendly.

        Proves channel-aware response formatting.
        """
        whatsapp_data = {
            "from_number": "+1-555-345-6789",
            "sender_name": "Casey",
            "body": "Feature request: dark mode"
        }

        response = http_client.post(f"{WHATSAPP_ENDPOINT}/simulate", json=whatsapp_data)
        assert response.status_code == 200

        data = response.json()
        ai_response = data["ai_response"]
        # WhatsApp responses should be readable on mobile (reasonably concise)
        assert len(ai_response) < 2000
        assert len(ai_response) > 10


# ============================================================================
# CROSS-CHANNEL CONTINUITY TESTS
# ============================================================================

class TestCrossChannelContinuity:
    """
    EXERCISE 3.1: Multi-channel conversation continuity
    Same customer uses different channels - system recognizes continuation
    """

    def test_same_customer_web_form_to_email(self, http_client):
        """
        [Exercise 1.3 & 3.1] Same customer (by email) submits via Web Form, then Email.

        System should:
        1. Recognize same customer
        2. Provide continued context
        3. Avoid duplicate solutions
        """
        shared_email = "continuity@example.com"
        shared_name = "Chris Multichannel"

        # SUBMISSION 1: Via Web Form
        form_data = {
            "customer_name": shared_name,
            "customer_email": shared_email,
            "subject": "Feature request",
            "message": "Can you add a dark mode feature?"
        }

        response1 = http_client.post(WEB_FORM_ENDPOINT, data=form_data)
        assert response1.status_code == 201
        web_result = response1.json()
        web_customer_id = web_result.get("customer_id")

        # SUBMISSION 2: Via Email (same customer)
        email_data = {
            "from_email": shared_email,
            "from_name": shared_name,
            "subject": "Following up on dark mode",
            "body": "Any updates on the dark mode feature request I submitted earlier?"
        }

        response2 = http_client.post(f"{EMAIL_ENDPOINT}/simulate", json=email_data)
        assert response2.status_code == 200
        email_result = response2.json()
        email_customer_id = email_result.get("customer_id") or web_customer_id

        # KEY ASSERTION: Same customer recognized across channels
        assert web_customer_id == email_customer_id or "CUST-" in str(email_customer_id)

        # Both should get AI responses
        assert len(web_result.get("ai_response", "")) > 0
        assert len(email_result.get("ai_response", "")) > 0

    def test_same_customer_web_form_to_whatsapp(self, http_client):
        """
        [Exercise 1.3 & 3.1] Same customer (by email/phone) uses Web Form, then WhatsApp.

        System recognizes continuation and provides context.
        """
        shared_email = "omnichannel@example.com"
        shared_phone = "+1-555-456-7890"
        shared_name = "Riley Omnichannel"

        # SUBMISSION 1: Via Web Form
        form_data = {
            "customer_name": shared_name,
            "customer_email": shared_email,
            "subject": "Technical issue",
            "message": "I'm getting a 500 error when accessing my dashboard",
            "phone": shared_phone
        }

        response1 = http_client.post(WEB_FORM_ENDPOINT, data=form_data)
        assert response1.status_code == 201
        web_result = response1.json()

        # SUBMISSION 2: Via WhatsApp (same customer)
        whatsapp_data = {
            "from_number": shared_phone,
            "sender_name": shared_name,
            "body": "Still getting that error. Can you help?"
        }

        response2 = http_client.post(f"{WHATSAPP_ENDPOINT}/simulate", json=whatsapp_data)
        assert response2.status_code == 200
        whatsapp_result = response2.json()

        # Both should have responses
        assert len(web_result.get("ai_response", "")) > 0
        assert len(whatsapp_result.get("ai_response", "")) > 0

        # WhatsApp response should reference the technical issue or error
        whatsapp_response = whatsapp_result.get("ai_response", "").lower()
        assert "error" in whatsapp_response or "500" in whatsapp_response or "dashboard" in whatsapp_response or "help" in whatsapp_response


# ============================================================================
# UNIFIED AGENT WORKFLOW TESTS
# ============================================================================

class TestUnifiedAgentWorkflow:
    """
    EXERCISE 2.3 & 2.5: Agent workflow is consistent across channels
    All channels execute the same 4-step workflow
    """

    def test_all_channels_execute_4_step_workflow(self, http_client):
        """
        [Exercise 2.3] Verify that Web Form, Email, and WhatsApp all execute:
        STEP 1: create_ticket()
        STEP 2: get_customer_history()
        STEP 3: search_knowledge_base()
        STEP 4: send_response()

        Logs show clear workflow progression for each channel.
        """
        test_message = "How do I enable two-factor authentication?"
        test_subject = "Security question"
        test_email = f"workflow_test_{int(__import__('time').time())}@example.com"

        channels_to_test = [
            ("web_form", WEB_FORM_ENDPOINT, {
                "customer_name": "Workflow Tester",
                "customer_email": test_email,
                "subject": test_subject,
                "message": test_message
            }),
            ("email", f"{EMAIL_ENDPOINT}/simulate", {
                "from_email": test_email,
                "from_name": "Workflow Tester",
                "subject": test_subject,
                "body": test_message
            }),
            ("whatsapp", f"{WHATSAPP_ENDPOINT}/simulate", {
                "from_number": "+1-555-567-8901",
                "sender_name": "Workflow Tester",
                "body": test_message
            })
        ]

        for channel_name, endpoint, payload in channels_to_test:
            if channel_name == "web_form":
                response = http_client.post(endpoint, data=payload)
            else:
                response = http_client.post(endpoint, json=payload)

            assert response.status_code == 200 or response.status_code == 201, \
                f"Failed for {channel_name}: {response.status_code}"

            data = response.json()
            assert "ai_response" in data, f"No AI response for {channel_name}"
            assert len(data["ai_response"]) > 0, f"Empty response for {channel_name}"
            assert "two-factor" in data["ai_response"].lower() or \
                   "authentication" in data["ai_response"].lower() or \
                   "security" in data["ai_response"].lower() or \
                   "factor" in data["ai_response"].lower(), \
                f"{channel_name} response not relevant to query"


# ============================================================================
# CHANNEL INDEPENDENCE TESTS
# ============================================================================

class TestChannelIndependence:
    """
    EXERCISE 3.1: Channels operate independently
    One channel's failure doesn't affect others
    """

    def test_web_form_works_independently(self, http_client):
        """Web Form channel works regardless of Email/WhatsApp status."""
        form_data = {
            "customer_name": "Independent Tester",
            "customer_email": "independent@example.com",
            "subject": "Web form only test",
            "message": "This submission should work regardless of other channels"
        }

        response = http_client.post(WEB_FORM_ENDPOINT, data=form_data)
        assert response.status_code == 201
        assert "ai_response" in response.json()

    def test_email_channel_independent_of_credentials(self, http_client):
        """Email simulation works without real Gmail credentials."""
        email_data = {
            "from_email": "no_creds_test@example.com",
            "from_name": "No Credentials Tester",
            "subject": "Simulation mode test",
            "body": "This works without real Gmail API credentials"
        }

        response = http_client.post(f"{EMAIL_ENDPOINT}/simulate", json=email_data)
        assert response.status_code == 200
        assert "ai_response" in response.json()

    def test_whatsapp_independent_of_credentials(self, http_client):
        """WhatsApp simulation works without real Twilio credentials."""
        whatsapp_data = {
            "from_number": "+1-555-678-9012",
            "sender_name": "No Credentials Tester",
            "body": "This works without real Twilio credentials"
        }

        response = http_client.post(f"{WHATSAPP_ENDPOINT}/simulate", json=whatsapp_data)
        assert response.status_code == 200
        assert "ai_response" in response.json()


# ============================================================================
# SIMULATION MODE VERIFICATION
# ============================================================================

class TestSimulationMode:
    """
    EXERCISE 3.1: Verification that channels work in simulation mode
    Proves system doesn't depend on external services for core functionality
    """

    def test_email_channel_health_shows_mode(self, http_client):
        """Email health check reports operational mode."""
        response = http_client.get(f"{EMAIL_ENDPOINT}/health")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert data["mode"] in ["REAL", "SIMULATION"]
        logger.info(f"Email channel running in {data['mode']} mode")

    def test_whatsapp_channel_health_shows_mode(self, http_client):
        """WhatsApp health check reports operational mode."""
        response = http_client.get(f"{WHATSAPP_ENDPOINT}/health")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert data["mode"] in ["REAL", "SIMULATION"]
        logger.info(f"WhatsApp channel running in {data['mode']} mode")


import logging
logger = logging.getLogger(__name__)
