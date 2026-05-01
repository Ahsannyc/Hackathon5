"""
Pytest Configuration and Shared Fixtures

This module contains all shared pytest fixtures for the Transition Test Suite.
Fixtures are defined here so they can be used across all test files.

Fixtures Provided:
- mock_customers_db: Pre-populated customer database (5 customers from incubation)
- mock_tickets_db: Empty ticket database for testing
- mock_knowledge_base: Knowledge base with 4 categories (billing, technical, feature, general)
- mock_tools: Mock tool implementations
- event_loop: Async event loop for @pytest.mark.asyncio tests
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock


# ============================================================================
# MOCK CLASSES
# ============================================================================

class MockCustomer:
    """Mock customer object for testing."""
    def __init__(self, customer_id: str, name: str, email: str, plan: str = "starter"):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.plan = plan
        self.conversation_history = []
        self.sentiment_trend = []
        self.channels_used = []
        self.escalation_count = 0
        self.total_messages = 0
        self.last_contact = None


class MockTicket:
    """Mock ticket object for testing."""
    def __init__(self, ticket_id: str, customer_id: str, issue: str, priority: str, channel: str):
        self.ticket_id = ticket_id
        self.customer_id = customer_id
        self.issue = issue
        self.priority = priority
        self.channel = channel
        self.status = "open"
        self.created_at = datetime.now().isoformat()
        self.sla_minutes = {
            "critical": 15,
            "high": 30,
            "medium": 120,
            "low": 1440
        }.get(priority, 120)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_customers_db() -> Dict[str, MockCustomer]:
    """
    Fixture: Pre-populated customer database.

    Contains 5 customers from incubation phase discovery-log.md:
    - CUST-00001: Sarah (premium plan, from EMAIL-001)
    - CUST-00002: Aisha (starter plan, from EMAIL-003)
    - CUST-00003: Kevin (enterprise plan, from EMAIL-005 - angry customer)
    - CUST-00004: Lisa (starter plan, from EMAIL-006 - technical question)
    - CUST-00005: Marcus (starter plan, from WEB-FORM-001 - pricing question)

    Returns:
        Dict[str, MockCustomer]: Customer database with 5 test customers
    """
    return {
        "CUST-00001": MockCustomer("CUST-00001", "Sarah", "sarah@email.com", "premium"),
        "CUST-00002": MockCustomer("CUST-00002", "Aisha", "aisha@email.com", "starter"),
        "CUST-00003": MockCustomer("CUST-00003", "Kevin", "kevin@email.com", "enterprise"),
        "CUST-00004": MockCustomer("CUST-00004", "Lisa", "lisa@email.com", "starter"),
        "CUST-00005": MockCustomer("CUST-00005", "Marcus", "marcus@email.com", "starter"),
    }


@pytest.fixture
def mock_tickets_db() -> Dict[str, MockTicket]:
    """
    Fixture: Empty ticket database for testing.

    Used by TestToolMigration and other tests that create tickets.
    Returns an empty dict that tests can populate during execution.

    Returns:
        Dict[str, MockTicket]: Empty ticket database
    """
    return {}


@pytest.fixture
def mock_knowledge_base() -> Dict[str, List[Dict[str, str]]]:
    """
    Fixture: Knowledge base with 4 categories for search tests.

    Categories:
    1. billing: Pricing, refund policy, invoicing
    2. technical: API integration, Slack setup, sync troubleshooting
    3. feature: Task dependencies, permissions, guest access
    4. general: Getting started, account settings

    Each article has 'title' and 'content' fields.

    Returns:
        Dict[str, List[Dict[str, str]]]: KB organized by category
    """
    return {
        "billing": [
            {"title": "How to upgrade your plan", "content": "Click Settings → Billing → Upgrade Plan"},
            {"title": "Refund policy", "content": "30-day money-back guarantee on all plans"},
            {"title": "Invoice and billing", "content": "Access invoices in your dashboard"},
        ],
        "technical": [
            {"title": "API integration", "content": "Webhook setup guide for developers"},
            {"title": "Slack integration setup", "content": "Connect Slack to get notifications"},
            {"title": "Sync issues and troubleshooting", "content": "Clear cache and retry sync"},
        ],
        "feature": [
            {"title": "Task dependencies", "content": "Set dependencies in task details"},
            {"title": "Permissions and access", "content": "Invite team members with roles"},
            {"title": "Guest access setup", "content": "Create guest invites with limited permissions"},
        ],
        "general": [
            {"title": "Getting started", "content": "Create account and add first project"},
            {"title": "Account settings", "content": "Update profile and preferences"},
        ]
    }


@pytest.fixture
def mock_tools() -> Dict[str, AsyncMock]:
    """
    Fixture: Mock tool implementations for testing tool calls.

    Provides AsyncMock objects for all 5 production tools:
    - create_ticket: Creates a support ticket
    - get_customer_history: Retrieves customer conversation history
    - search_knowledge_base: Searches KB for answers
    - escalate_to_human: Escalates to human specialist
    - send_response: Sends formatted response via channel

    Returns:
        Dict[str, AsyncMock]: Mock implementations of all 5 tools
    """
    tools = {
        "create_ticket": AsyncMock(),
        "get_customer_history": AsyncMock(),
        "search_knowledge_base": AsyncMock(),
        "escalate_to_human": AsyncMock(),
        "send_response": AsyncMock(),
    }
    return tools


@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture: Provide event loop for async tests.

    Required for @pytest.mark.asyncio tests to work properly.
    Creates a single event loop for the entire test session.

    Yields:
        asyncio.AbstractEventLoop: Event loop for async operations
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """
    Pytest hook: Configure pytest behavior.

    Registers custom markers used in tests.
    """
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async (deselect with '-m \"not asyncio\"')"
    )


# ============================================================================
# PYTEST PLUGINS
# ============================================================================

# Enable pytest-asyncio plugin for @pytest.mark.asyncio support
pytest_plugins = ("pytest_asyncio",)
