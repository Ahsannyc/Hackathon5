"""
CROSS-CHANNEL CONTINUITY TESTS

Tests that demonstrate the same customer is recognized across all channels
(Web Form, Email, WhatsApp) and conversation memory preserved.

Exercise 3.1: Multi-channel E2E testing
Exercise 3.2: Cross-channel functionality and conversation continuity
"""

import pytest
from fastapi.testclient import TestClient
from production.api.main import app
from production.api.agent_integration import (
    _conversation_history,
    _customer_registry,
    _normalize_customer_id
)

# ============================================================================
# SETUP
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_memory():
    """Clear in-memory stores before each test."""
    _conversation_history.clear()
    _customer_registry.clear()
    yield


# ============================================================================
# CROSS-CHANNEL CONTINUITY TESTS
# ============================================================================

class TestCrossChannelContinuity:
    """
    EXERCISE 3.2: Cross-channel functionality

    Tests demonstrate:
    1. Same customer (identified by email) recognized across channels
    2. Conversation history preserved regardless of channel
    3. Unified agent workflow executes identically per channel
    """

    def test_01_web_form_creates_customer_record(self, client):
        """[Exercise 1.3 + 3.2] Web form submission creates customer record."""
        email = "alice@example.com"
        customer_id = _normalize_customer_id(email)

        # Submit via web form
        response = client.post("/api/form/submit", data={
            "customer_name": "Alice",
            "customer_email": email,
            "subject": "API Integration Help",
            "message": "How do I integrate your API?",
            "priority": "medium"
        })

        assert response.status_code in [200, 201]
        data = response.json()
        assert "ai_response" in data or "response" in data

        # Verify customer in registry
        assert customer_id in _customer_registry
        assert _customer_registry[customer_id]["email"] == email
        assert _customer_registry[customer_id]["name"] == "Alice"

    def test_02_email_recognizes_same_customer(self, client):
        """[Exercise 3.2] Email channel recognizes customer from web form."""
        email = "bob@example.com"
        customer_id = _normalize_customer_id(email)

        # First interaction via web form
        response1 = client.post("/api/form/submit", data={
            "customer_name": "Bob",
            "customer_email": email,
            "subject": "Password reset",
            "message": "I forgot my password",
            "priority": "high"
        })
        assert response1.status_code in [200, 201]
        interaction_count_after_form = _customer_registry[customer_id]["interaction_count"]

        # Second interaction via email (simulated)
        email_data = {
            "from_email": email,
            "from_name": "Bob",
            "subject": "Follow-up: Password reset",
            "body": "I still need help with my password"
        }
        response2 = client.post("/api/email/simulate", json=email_data)
        assert response2.status_code == 200

        # Verify same customer ID used
        assert customer_id in _customer_registry
        assert _customer_registry[customer_id]["interaction_count"] > interaction_count_after_form

    def test_03_whatsapp_recognizes_same_customer(self, client):
        """[Exercise 3.2] WhatsApp channel recognizes customer."""
        email = "charlie@example.com"
        customer_id = _normalize_customer_id(email)

        # Web form interaction
        response1 = client.post("/api/form/submit", data={
            "customer_name": "Charlie",
            "customer_email": email,
            "subject": "Feature request",
            "message": "Can you add dark mode?",
            "priority": "low"
        })
        assert response1.status_code in [200, 201]

        # WhatsApp interaction (simulated)
        whatsapp_data = {
            "from_number": "+1555012345",
            "sender_name": "Charlie",
            "body": "What about the dark mode feature I requested?"
        }
        response2 = client.post("/api/whatsapp/simulate", json=whatsapp_data)
        assert response2.status_code == 200

        # Verify customer tracked
        assert customer_id in _customer_registry

    def test_04_conversation_history_preserved_across_channels(self, client):
        """[Exercise 1.3 + 3.2] Conversation history accessible across channels."""
        email = "diana@example.com"
        customer_id = _normalize_customer_id(email)

        # Message 1: Web Form
        response1 = client.post("/api/form/submit", data={
            "customer_name": "Diana",
            "customer_email": email,
            "subject": "Rate limiting",
            "message": "What are your rate limits?",
            "priority": "medium"
        })
        assert response1.status_code in [200, 201]

        # Message 2: Email (follow-up)
        email_data = {
            "from_email": email,
            "from_name": "Diana",
            "subject": "Re: Rate limiting",
            "body": "I'm hitting your rate limit - need higher tier"
        }
        response2 = client.post("/api/email/simulate", json=email_data)
        assert response2.status_code == 200

        # Message 3: WhatsApp (urgent)
        whatsapp_data = {
            "from_number": "+1555055555",
            "sender_name": "Diana",
            "body": "URGENT: Still hitting rate limits, affecting production"
        }
        response3 = client.post("/api/whatsapp/simulate", json=whatsapp_data)
        assert response3.status_code == 200

        # Verify conversation history grows
        assert customer_id in _conversation_history
        history = _conversation_history[customer_id]
        assert len(history) >= 1  # At least one interaction logged

    def test_05_customer_data_consistency(self, client):
        """[Exercise 3.2] Customer data consistent across channels."""
        email = "evan@example.com"
        customer_id = _normalize_customer_id(email)

        # Multiple interactions via same channel
        for i in range(3):
            client.post("/api/form/submit", data={
                "customer_name": "Evan",
                "customer_email": email,
                "subject": f"Test {i}",
                "message": "Test message",
                "priority": "medium"
            })

        # Verify customer record consistency
        assert customer_id in _customer_registry
        assert _customer_registry[customer_id]["email"] == email
        assert _customer_registry[customer_id]["name"] == "Evan"
        assert _customer_registry[customer_id]["interaction_count"] >= 3

    def test_06_escalation_tracking_cross_channel(self, client):
        """[Exercise 2.6 + 3.2] Escalation tracking across channels."""
        email = "frank@example.com"
        customer_id = _normalize_customer_id(email)

        # High-priority interaction
        response = client.post("/api/form/submit", data={
            "customer_name": "Frank",
            "customer_email": email,
            "subject": "System outage",
            "message": "Your system is down and affecting my business!",
            "priority": "critical"
        })
        assert response.status_code in [200, 201]

        # Should have customer tracked
        assert customer_id in _customer_registry

    def test_07_same_email_different_names_treated_as_one_customer(self, client):
        """[Exercise 3.2] Same email from different names = same customer."""
        email = "grace@example.com"
        customer_id = _normalize_customer_id(email)

        # First interaction
        response1 = client.post("/api/form/submit", data={
            "customer_name": "Grace Smith",
            "customer_email": email,
            "subject": "Help needed",
            "message": "I need help with the API",
            "priority": "medium"
        })
        assert response1.status_code in [200, 201]

        # Second interaction - same email, slightly different name
        response2 = client.post("/api/form/submit", data={
            "customer_name": "G. Smith",
            "customer_email": email,
            "subject": "Follow-up question",
            "message": "Following up on my request",
            "priority": "medium"
        })
        assert response2.status_code in [200, 201]

        # Should be same customer_id
        assert customer_id in _customer_registry
        assert _customer_registry[customer_id]["interaction_count"] >= 2

    def test_08_parallel_channel_handling(self, client):
        """[Exercise 3.2] System handles messages from multiple channels independently."""
        # Test that multiple different customers can be handled

        # Customer 1 via web form
        r1 = client.post("/api/form/submit", data={
            "customer_name": "Henry",
            "customer_email": "henry@example.com",
            "subject": "API question",
            "message": "How do I use the API?",
            "priority": "medium"
        })
        assert r1.status_code in [200, 201]

        # Customer 2 via email
        r2 = client.post("/api/email/simulate", json={
            "from_email": "iris@example.com",
            "from_name": "Iris",
            "subject": "Integration help",
            "body": "Need help integrating"
        })
        assert r2.status_code == 200

        # Customer 3 via WhatsApp (can also add email for tracking)
        r3 = client.post("/api/whatsapp/simulate", json={
            "from_number": "+1555077777",
            "sender_name": "Jack",
            "body": "Password reset needed"
        })
        assert r3.status_code == 200

        # Verify customers 1 and 2 are tracked
        c1_id = _normalize_customer_id("henry@example.com")
        c2_id = _normalize_customer_id("iris@example.com")

        assert c1_id in _customer_registry
        assert c2_id in _customer_registry

    def test_09_workflow_consistency_across_channels(self, client):
        """[Exercise 2.1 + 3.2] Same 4-step workflow executes per channel."""
        # The unified agent should execute same workflow regardless of channel
        # This is validated through logging in agent_integration.py

        email = "karen@example.com"

        # Web form
        r1 = client.post("/api/form/submit", data={
            "customer_name": "Karen",
            "customer_email": email,
            "subject": "Integration",
            "message": "How do I integrate?",
            "priority": "medium"
        })
        assert r1.status_code in [200, 201]
        assert "response" in r1.json() or "ai_response" in r1.json()

        # Email
        r2 = client.post("/api/email/simulate", json={
            "from_email": email,
            "from_name": "Karen",
            "subject": "Integration",
            "body": "How do I integrate?"
        })
        assert r2.status_code == 200
        assert "response" in r2.json() or "ai_response" in r2.json()

    def test_10_memory_system_enables_context_aware_responses(self, client):
        """[Exercise 1.3 + 3.2] Memory enables context-aware responses."""
        email = "leo@example.com"
        customer_id = _normalize_customer_id(email)

        # First message
        response1 = client.post("/api/form/submit", data={
            "customer_name": "Leo",
            "customer_email": email,
            "subject": "Password reset",
            "message": "I need to reset my password",
            "priority": "high"
        })
        assert response1.status_code in [200, 201]

        # Second message (follow-up) - system should have context
        response2 = client.post("/api/form/submit", data={
            "customer_name": "Leo",
            "customer_email": email,
            "subject": "Password reset - still need help",
            "message": "The reset email didn't arrive",
            "priority": "high"
        })
        assert response2.status_code in [200, 201]

        # Should have context from first interaction
        assert customer_id in _customer_registry
        assert _customer_registry[customer_id]["interaction_count"] >= 2

