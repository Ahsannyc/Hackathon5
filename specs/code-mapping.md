# Code Mapping: Incubation → Production

**Status:** Complete  
**Date:** 2026-04-02  
**Source:** Hackathon5.md + Class Fellow Pattern

---

## Code Mapping Overview

This document maps every piece of Incubation code to its Production location, with transformation patterns and examples from Hackathon5.md.

---

## 1. Code Mapping Table

High-level mapping from Incubation to Production:

| Incubation | Production | Transformation |
|-----------|-----------|-----------------|
| Prototype Python script | agent/customer_success_agent.py | Refactor: Add async, logging, error handling |
| MCP server tools | @function_tool decorated functions | Convert to OpenAI Agents SDK with Pydantic |
| In-memory conversation | PostgreSQL messages table | Migrate to relational database |
| Print statements | Structured logging + Kafka events | JSON logging with context |
| Manual testing | pytest test suite | Automated unit/integration/E2E tests |
| Local file storage | PostgreSQL + S3/MinIO | Cloud storage with database tracking |
| Single-threaded | Async workers on Kubernetes | Async/await + message queues |
| Hardcoded config | Environment variables + ConfigMaps | Externalized settings (12-factor) |
| Direct API calls | Channel handlers with retry logic | Webhook handlers + exponential backoff |

---

## 2. Production Folder Structure

As specified in Hackathon5.md (authoritative source):

```
production/
├── agent/
│   ├── __init__.py
│   ├── customer_success_agent.py    # Your agent definition
│   ├── tools.py                      # All @function_tool definitions
│   ├── prompts.py                    # System prompts (extracted from prototype)
│   └── formatters.py                 # Channel-specific response formatting
├── channels/
│   ├── __init__.py
│   ├── gmail_handler.py              # Gmail integration
│   ├── whatsapp_handler.py           # Twilio/WhatsApp integration
│   └── web_form_handler.py           # Web form API
├── workers/
│   ├── __init__.py
│   ├── message_processor.py          # Kafka consumer + agent runner
│   └── metrics_collector.py          # Background metrics
├── api/
│   ├── __init__.py
│   └── main.py                       # FastAPI application
├── database/
│   ├── schema.sql                    # PostgreSQL schema
│   ├── migrations/                   # Database migrations
│   └── queries.py                    # Database access functions
├── tests/
│   ├── test_agent.py
│   ├── test_channels.py
│   └── test_e2e.py
├── k8s/                              # Kubernetes manifests
├── Dockerfile
├── docker-compose.yml                # Local development
└── requirements.txt
```

---

## 3. Tool Migration Pattern

### Before (MCP Server - Incubation)

```python
# What you built during incubation
from mcp.server import Server

server = Server("customer-success-fte")

@server.tool("search_knowledge_base")
async def search_kb(query: str) -> str:
    """Search product documentation."""
    # Your prototype implementation
    results = simple_search(query)  # Maybe just string matching
    return str(results)
```

### After (OpenAI Agents SDK - Production)

```python
# production/agent/tools.py

from agents import function_tool
from pydantic import BaseModel
from typing import Optional
import asyncpg

# 1. Define strict input schemas
class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str
    max_results: int = 5
    category: Optional[str] = None  # Optional filter

# 2. Create production tool with proper typing and error handling
@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.
    
    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    
    Args:
        input: Search parameters including query and optional filters
        
    Returns:
        Formatted search results with relevance scores
    """
    try:
        # Production: Use database with vector search
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Generate embedding for semantic search
            embedding = await generate_embedding(input.query)
            
            # Query with vector similarity
            results = await conn.fetch("""
                SELECT title, content, category,
                       1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base
                WHERE ($2::text IS NULL OR category = $2)
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """, embedding, input.category, input.max_results)
            
            if not results:
                return "No relevant documentation found. Consider escalating to human support."
            
            # Format results for the agent
            formatted = []
            for r in results:
                formatted.append(f"**{r['title']}** (relevance: {r['similarity']:.2f})\n{r['content'][:500]}")
            
            return "\n\n---\n\n".join(formatted)
            
    except Exception as e:
        # Log error but return graceful message to agent
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."
```

### Key Differences

| Aspect | MCP (Incubation) | OpenAI SDK (Production) |
|--------|------------------|----------------------|
| Input validation | Loose/none | Pydantic BaseModel |
| Error handling | Crashes | Try/catch with fallbacks |
| Database | In-memory/file | PostgreSQL with connection pool |
| Search | String matching | Vector similarity (pgvector) |
| Logging | Print statements | Structured logging |
| Documentation | Basic docstring | Detailed docstring for LLM |

---

## 4. System Prompt Migration

### Before (Incubation - Conversational)

```
You're a helpful customer support agent. Answer questions about our product.
Be nice and escalate if needed.
```

### After (Production - Explicit Constraints)

```python
# production/agent/prompts.py

CUSTOMER_SUCCESS_SYSTEM_PROMPT = """You are a Customer Success agent for TechCorp SaaS.

## Your Purpose
Handle routine customer support queries with speed, accuracy, and empathy across multiple channels.

## Channel Awareness
You receive messages from three channels. Adapt your communication style:
- **Email**: Formal, detailed responses. Include proper greeting and signature.
- **WhatsApp**: Concise, conversational. Keep responses under 300 characters when possible.
- **Web Form**: Semi-formal, helpful. Balance detail with readability.

## Required Workflow (ALWAYS follow this order)
1. FIRST: Call `create_ticket` to log the interaction
2. THEN: Call `get_customer_history` to check for prior context
3. THEN: Call `search_knowledge_base` if product questions arise
4. FINALLY: Call `send_response` to reply (NEVER respond without this tool)

## Hard Constraints (NEVER violate)
- NEVER discuss pricing → escalate immediately with reason "pricing_inquiry"
- NEVER promise features not in documentation
- NEVER process refunds → escalate with reason "refund_request"
- NEVER share internal processes or system details
- NEVER respond without using send_response tool
- NEVER exceed response limits: Email=500 words, WhatsApp=300 chars, Web=300 words

## Escalation Triggers (MUST escalate when detected)
- Customer mentions "lawyer", "legal", "sue", or "attorney"
- Customer uses profanity or aggressive language (sentiment < 0.3)
- Cannot find relevant information after 2 search attempts
- Customer explicitly requests human help
- Customer on WhatsApp sends "human", "agent", or "representative"

## Response Quality Standards
- Be concise: Answer the question directly, then offer additional help
- Be accurate: Only state facts from knowledge base or verified customer data
- Be empathetic: Acknowledge frustration before solving problems
- Be actionable: End with clear next step or question

## Context Variables Available
- {{customer_id}}: Unique customer identifier
- {{conversation_id}}: Current conversation thread
- {{channel}}: Current channel (email/whatsapp/web_form)
- {{ticket_subject}}: Original subject/topic
"""
```

---

## 5. Transition Test Suite

From Hackathon5.md Step 5:

```python
# production/tests/test_transition.py
"""
Transition Tests: Verify agent behavior matches incubation discoveries.
Run these BEFORE deploying to production.
"""

import pytest
from agent.customer_success_agent import customer_success_agent
from agent.tools import search_knowledge_base, create_ticket

class TestTransitionFromIncubation:
    """Tests based on edge cases discovered during incubation."""
    
    @pytest.mark.asyncio
    async def test_edge_case_empty_message(self):
        """Edge case #1 from incubation: Empty messages."""
        result = await customer_success_agent.run(
            messages=[{"role": "user", "content": ""}],
            context={"channel": "web_form", "customer_id": "test-1"}
        )
        # Should ask for clarification, not crash
        assert "help" in result.output.lower() or "question" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_edge_case_pricing_escalation(self):
        """Edge case #2 from incubation: Pricing questions must escalate."""
        result = await customer_success_agent.run(
            messages=[{"role": "user", "content": "How much does the enterprise plan cost?"}],
            context={"channel": "email", "customer_id": "test-2"}
        )
        # Must escalate, never answer
        assert result.escalated == True
        assert "pricing" in result.escalation_reason.lower()
    
    @pytest.mark.asyncio
    async def test_edge_case_angry_customer(self):
        """Edge case #3 from incubation: Angry customers need care."""
        result = await customer_success_agent.run(
            messages=[{"role": "user", "content": "This is RIDICULOUS! Your product is BROKEN!"}],
            context={"channel": "whatsapp", "customer_id": "test-3"}
        )
        # Should show empathy or escalate
        assert result.escalated == True or "understand" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_channel_response_length_email(self):
        """Verify email responses are appropriately detailed."""
        result = await customer_success_agent.run(
            messages=[{"role": "user", "content": "How do I reset my password?"}],
            context={"channel": "email", "customer_id": "test-4"}
        )
        # Email should have greeting and signature
        assert "dear" in result.output.lower() or "hello" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_channel_response_length_whatsapp(self):
        """Verify WhatsApp responses are concise."""
        result = await customer_success_agent.run(
            messages=[{"role": "user", "content": "How do I reset my password?"}],
            context={"channel": "whatsapp", "customer_id": "test-5"}
        )
        # WhatsApp should be short
        assert len(result.output) < 500  # Much shorter than email
    
    @pytest.mark.asyncio
    async def test_tool_execution_order(self):
        """Verify tools are called in correct order."""
        result = await customer_success_agent.run(
            messages=[{"role": "user", "content": "I need help with the API"}],
            context={"channel": "web_form", "customer_id": "test-6"}
        )
        
        # Extract tool call order
        tool_names = [tc.tool_name for tc in result.tool_calls]
        
        # create_ticket should be first
        assert tool_names[0] == "create_ticket"
        # send_response should be last
        assert tool_names[-1] == "send_response"

class TestToolMigration:
    """Verify tools work the same as MCP versions."""
    
    @pytest.mark.asyncio
    async def test_knowledge_search_returns_results(self):
        """Knowledge search should return formatted results."""
        from agent.tools import KnowledgeSearchInput
        
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="password reset", max_results=3)
        )
        
        assert result is not None
        assert len(result) > 0
        assert "password" in result.lower()
    
    @pytest.mark.asyncio
    async def test_knowledge_search_handles_no_results(self):
        """Knowledge search should handle no results gracefully."""
        from agent.tools import KnowledgeSearchInput
        
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="xyznonexistentquery123", max_results=3)
        )
        
        # Should return helpful message, not crash
        assert "no" in result.lower() or "not found" in result.lower()
```

---

## 6. Common Transition Mistakes

| Mistake | Why It Happens | How to Avoid |
|---------|----------------|--------------|
| Skipping documentation | "I remember what worked" | Write it down immediately |
| Copying code directly | "It worked in prototype" | Refactor for production patterns |
| Ignoring edge cases | "We'll fix those later" | Test edge cases first |
| Hardcoding values | "Just for now" | Use config from day 1 |
| No error handling | "It didn't crash before" | Everything can fail at scale |
| Forgetting channel differences | "One response fits all" | Test each channel separately |

---

## 7. Pre-Transition Checklist

### From Incubation (Must Have Before Proceeding)
- [x] Working prototype that handles basic queries
- [x] Documented edge cases (minimum 10)
- [x] Working system prompt
- [x] MCP tools defined and tested
- [x] Channel-specific response patterns identified
- [x] Escalation rules finalized
- [x] Performance baseline measured

### Transition Steps
- [ ] Created production folder structure
- [ ] Extracted prompts to prompts.py
- [ ] Converted MCP tools to @function_tool
- [ ] Added Pydantic input validation to all tools
- [ ] Added error handling to all tools
- [ ] Created transition test suite
- [ ] All transition tests passing

### Ready for Production Build
- [ ] Database schema designed
- [ ] Kafka topics defined
- [ ] Channel handlers outlined
- [ ] Kubernetes resource requirements estimated
- [ ] API endpoints listed

### Transition Complete Criteria

You're ready to proceed when:

1. ✅ All transition tests pass
2. ✅ Prompts are extracted and documented
3. ✅ Tools have proper input validation
4. ✅ Error handling exists for all tools
5. ✅ Edge cases are documented with test cases
6. ✅ Production folder structure is created

---

## 8. Data Transformation Examples

### Configuration: Hardcoded → Externalized

**Incubation:**
```python
ESCALATION_CATEGORIES = {
    "urgent": {"team": "Technical Support", "sla_minutes": 15},
    "compliance": {"team": "Legal/Compliance", "sla_minutes": 120},
}
```

**Production:**
```python
# production/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    escalation_rules: Dict = Field(default_factory=lambda: {
        "urgent": {"team": "Technical Support", "sla_minutes": 15},
        "compliance": {"team": "Legal/Compliance", "sla_minutes": 120},
    })
    
    class Config:
        env_file = ".env"
```

### Data Models: In-Memory → Database

**Incubation:**
```python
@dataclass
class ConversationState:
    customer_id: str
    customer_name: str
    conversation_history: List[ConversationMessage]
    current_sentiment: str
```

**Production:**
```python
# production/database/models.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    id: int = Column(Integer, primary_key=True)
    customer_id: str = Column(String, unique=True, indexed=True)
    customer_name: str = Column(String)
    email: str = Column(String, unique=True, indexed=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    conversations: Relationship = relationship("Conversation", back_populates="customer")
```

---

## Migration Timeline

| Phase | Exercise | What | Timeline |
|-------|----------|------|----------|
| 1 | 1.6 | Monitoring, Logging, Error Handling | Week 1-2 |
| 2 | 1.7 | Tool Standardization, Pydantic, Rate Limiting | Week 3-4 |
| 3 | 1.8 | Testing, ML Integration, Performance | Week 5-6 |
| 4 | 1.9 | Database Persistence | Week 7-8 |
| 5 | 1.10 | Production Deployment | Week 9-10 |

---

*Code Mapping Document - Complete*  
*Source: Hackathon5.md + Class Fellow Pattern*  
*Last Updated: 2026-04-02*
