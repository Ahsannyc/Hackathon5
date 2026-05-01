"""
============================================================================
CloudFlow Customer Success FTE - Async Database Queries
============================================================================
High-performance async database operations using asyncpg.
All queries are parameterized to prevent SQL injection.
Connection pooling for optimal performance under load.
============================================================================
"""

import asyncpg
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION POOL MANAGEMENT
# ============================================================================

class DatabasePool:
    """Manages asyncpg connection pool for the application"""

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def initialize(
        cls,
        dsn: str,
        min_size: int = 5,
        max_size: int = 20,
        max_cached_statement_lifetime: int = 3600,
        max_cacheable_statement_size: int = 15000,
    ) -> None:
        """
        Initialize the connection pool.

        Args:
            dsn: PostgreSQL connection string
            min_size: Minimum pool connections
            max_size: Maximum pool connections
            max_cached_statement_lifetime: Prepared statement cache lifetime (seconds)
            max_cacheable_statement_size: Max size of cacheable statements (bytes)
        """
        try:
            cls._pool = await asyncpg.create_pool(
                dsn,
                min_size=min_size,
                max_size=max_size,
                max_cached_statement_lifetime=max_cached_statement_lifetime,
                max_cacheable_statement_size=max_cacheable_statement_size,
                command_timeout=60,
            )
            logger.info(f"✅ Database pool initialized (min: {min_size}, max: {max_size})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close the connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("✅ Database pool closed")

    @classmethod
    async def get_connection(cls) -> asyncpg.Connection:
        """Get a connection from the pool"""
        if not cls._pool:
            raise RuntimeError("Database pool not initialized")
        return await cls._pool.acquire()

    @classmethod
    async def execute_query(cls, query: str, *args) -> Any:
        """Execute a query and return results"""
        async with await cls.get_connection() as conn:
            return await conn.fetch(query, *args)


# ============================================================================
# CUSTOMER OPERATIONS
# ============================================================================

async def create_customer(
    first_name: str,
    last_name: str,
    primary_email: Optional[str] = None,
    primary_phone: Optional[str] = None,
    company_name: Optional[str] = None,
    customer_tier: str = "standard",
) -> UUID:
    """
    Create a new customer record.

    Args:
        first_name: Customer first name
        last_name: Customer last name
        primary_email: Customer email
        primary_phone: Customer phone
        company_name: Customer company
        customer_tier: Tier level (free, standard, premium, enterprise)

    Returns:
        UUID of created customer
    """
    query = """
        INSERT INTO customers (
            first_name, last_name, primary_email, primary_phone,
            company_name, customer_tier, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
        RETURNING id;
    """

    result = await DatabasePool.execute_query(
        query,
        first_name,
        last_name,
        primary_email,
        primary_phone,
        company_name,
        customer_tier,
    )

    customer_id = result[0]["id"]
    logger.info(f"✅ Created customer: {customer_id}")
    return customer_id


async def get_or_create_customer(
    channel: str,
    channel_identifier: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Tuple[UUID, bool]:
    """
    Get existing customer or create new one (for cross-channel matching).

    Args:
        channel: Channel type (email, whatsapp, web_form)
        channel_identifier: Channel-specific ID (email, phone, web ID)
        first_name: Name if creating new customer
        last_name: Name if creating new customer

    Returns:
        Tuple of (customer_id, is_new_customer)
    """
    # Try to find existing customer
    query = """
        SELECT c.id FROM customers c
        INNER JOIN customer_identifiers ci ON c.id = ci.customer_id
        WHERE ci.channel = $1 AND ci.channel_identifier = $2
        LIMIT 1;
    """

    result = await DatabasePool.execute_query(query, channel, channel_identifier)

    if result:
        customer_id = result[0]["id"]
        logger.info(f"✅ Found existing customer: {customer_id}")
        return customer_id, False

    # Create new customer if not found
    if not first_name or not last_name:
        first_name = first_name or "Unknown"
        last_name = last_name or "Customer"

    customer_id = await create_customer(first_name, last_name)

    # Add channel identifier
    await add_customer_identifier(customer_id, channel, channel_identifier)

    logger.info(f"✅ Created new customer: {customer_id}")
    return customer_id, True


async def add_customer_identifier(
    customer_id: UUID, channel: str, channel_identifier: str
) -> None:
    """
    Add a channel identifier to an existing customer.
    Enables cross-channel continuity.

    Args:
        customer_id: Customer UUID
        channel: Channel type (email, whatsapp, web_form)
        channel_identifier: Channel-specific ID
    """
    query = """
        INSERT INTO customer_identifiers (customer_id, channel, channel_identifier, created_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (channel, channel_identifier) DO NOTHING;
    """

    await DatabasePool.execute_query(query, customer_id, channel, channel_identifier)
    logger.info(f"✅ Added identifier {channel}:{channel_identifier} to customer {customer_id}")


async def update_customer_sentiment(
    customer_id: UUID, sentiment: str, satisfaction_score: Optional[float] = None
) -> None:
    """
    Update customer sentiment and satisfaction.

    Args:
        customer_id: Customer UUID
        sentiment: Sentiment level (very_negative, negative, neutral, positive, very_positive)
        satisfaction_score: Satisfaction score (0-5)
    """
    query = """
        UPDATE customers
        SET overall_sentiment = $1,
            satisfaction_score = COALESCE($2, satisfaction_score),
            updated_at = NOW(),
            last_contact_at = NOW()
        WHERE id = $3;
    """

    await DatabasePool.execute_query(query, sentiment, satisfaction_score, customer_id)
    logger.info(f"✅ Updated sentiment for customer {customer_id}: {sentiment}")


# ============================================================================
# CONVERSATION OPERATIONS
# ============================================================================

async def create_conversation(
    customer_id: UUID,
    primary_channel: str,
    title: Optional[str] = None,
    initial_intent: Optional[str] = None,
) -> UUID:
    """
    Create a new conversation thread.

    Args:
        customer_id: Customer UUID
        primary_channel: Channel type (email, whatsapp, web_form)
        title: Conversation title
        initial_intent: Detected intent

    Returns:
        UUID of created conversation
    """
    query = """
        INSERT INTO conversations (
            customer_id, primary_channel, title, initial_intent,
            status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, 'open', NOW(), NOW())
        RETURNING id;
    """

    result = await DatabasePool.execute_query(
        query, customer_id, primary_channel, title, initial_intent
    )

    conversation_id = result[0]["id"]
    logger.info(f"✅ Created conversation: {conversation_id}")
    return conversation_id


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================

async def store_message(
    conversation_id: UUID,
    customer_id: UUID,
    content: str,
    source_channel: str,
    message_type: str = "user",
    sentiment: Optional[str] = None,
    sentiment_confidence: Optional[float] = None,
    detected_intent: Optional[str] = None,
    intent_confidence: Optional[float] = None,
    emotion_tags: Optional[List[str]] = None,
    escalation_triggered: bool = False,
    escalation_reason: Optional[str] = None,
    requires_human: bool = False,
    channel_message_id: Optional[str] = None,
) -> UUID:
    """
    Store a message in the database with AI analysis.

    Args:
        conversation_id: Conversation UUID
        customer_id: Customer UUID
        content: Message text
        source_channel: Channel type (email, whatsapp, web_form)
        message_type: Type (user, agent, system)
        sentiment: Detected sentiment
        sentiment_confidence: Sentiment confidence (0-1)
        detected_intent: Detected intent
        intent_confidence: Intent confidence (0-1)
        emotion_tags: List of emotions detected
        escalation_triggered: Whether escalation was triggered
        escalation_reason: Reason for escalation
        requires_human: Whether human intervention needed
        channel_message_id: External channel ID

    Returns:
        UUID of created message
    """
    query = """
        INSERT INTO messages (
            conversation_id, customer_id, content, message_type,
            source_channel, sentiment, sentiment_confidence,
            detected_intent, intent_confidence, emotion_tags,
            escalation_triggered, escalation_reason, requires_human,
            channel_message_id, word_count, created_at, processed_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, NOW(), NOW()
        )
        RETURNING id;
    """

    word_count = len(content.split())

    result = await DatabasePool.execute_query(
        query,
        conversation_id,
        customer_id,
        content,
        message_type,
        source_channel,
        sentiment,
        sentiment_confidence,
        detected_intent,
        intent_confidence,
        emotion_tags or [],
        escalation_triggered,
        escalation_reason,
        requires_human,
        channel_message_id,
        word_count,
    )

    message_id = result[0]["id"]

    # Update conversation message count
    await DatabasePool.execute_query(
        "UPDATE conversations SET message_count = message_count + 1, updated_at = NOW() WHERE id = $1",
        conversation_id
    )

    logger.info(f"✅ Stored message: {message_id}")
    return message_id


# ============================================================================
# TICKET OPERATIONS
# ============================================================================

async def create_ticket(
    customer_id: UUID,
    conversation_id: UUID,
    title: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
    priority: str = "medium",
    sla_response_minutes: Optional[int] = None,
    sla_resolution_minutes: Optional[int] = None,
) -> str:
    """
    Create a support ticket.

    Args:
        customer_id: Customer UUID
        conversation_id: Conversation UUID
        title: Ticket title
        description: Ticket description
        category: Issue category (billing, technical, feature_request)
        priority: Priority level (critical, high, medium, low)
        sla_response_minutes: SLA response time target
        sla_resolution_minutes: SLA resolution time target

    Returns:
        Ticket number (string)
    """
    # Generate ticket number
    timestamp = int(datetime.now().timestamp() * 1000)
    ticket_number = f"TKT-{timestamp}"

    query = """
        INSERT INTO tickets (
            customer_id, conversation_id, ticket_number, title,
            description, category, priority,
            sla_response_minutes, sla_resolution_minutes,
            status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'open', NOW(), NOW())
        RETURNING ticket_number;
    """

    result = await DatabasePool.execute_query(
        query,
        customer_id,
        conversation_id,
        ticket_number,
        title,
        description,
        category,
        priority,
        sla_response_minutes,
        sla_resolution_minutes,
    )

    logger.info(f"✅ Created ticket: {ticket_number}")
    return result[0]["ticket_number"]


async def update_ticket_status(
    ticket_number: str,
    status: str,
    satisfaction_rating: Optional[float] = None,
) -> None:
    """
    Update ticket status.

    Args:
        ticket_number: Ticket number
        status: New status (open, in_progress, pending_customer, resolved, closed, reopened)
        satisfaction_rating: Customer satisfaction (0-5)
    """
    closed_at = "NOW()" if status in ["resolved", "closed"] else "NULL"

    query = f"""
        UPDATE tickets
        SET status = $1,
            satisfaction_rating = COALESCE($2, satisfaction_rating),
            closed_at = {closed_at},
            updated_at = NOW()
        WHERE ticket_number = $3;
    """

    await DatabasePool.execute_query(query, status, satisfaction_rating, ticket_number)
    logger.info(f"✅ Updated ticket {ticket_number} status: {status}")


async def escalate_ticket(
    ticket_number: str,
    escalated_to: str,
    escalation_reason: str,
) -> None:
    """
    Escalate a ticket to human team.

    Args:
        ticket_number: Ticket number
        escalated_to: Team or person name
        escalation_reason: Reason for escalation
    """
    query = """
        UPDATE tickets
        SET escalated = true,
            escalated_to = $1,
            escalation_reason = $2,
            escalated_at = NOW(),
            status = 'escalated',
            updated_at = NOW()
        WHERE ticket_number = $3;
    """

    await DatabasePool.execute_query(query, escalated_to, escalation_reason, ticket_number)
    logger.info(f"✅ Escalated ticket {ticket_number} to {escalated_to}")


# ============================================================================
# HISTORY & RETRIEVAL OPERATIONS
# ============================================================================

async def get_customer_history(
    customer_id: UUID,
    limit: int = 50,
    include_messages: bool = True,
) -> Dict[str, Any]:
    """
    Get complete customer history across all channels.
    Enables context awareness for multi-channel conversations.

    Args:
        customer_id: Customer UUID
        limit: Max conversations to retrieve
        include_messages: Whether to include message details

    Returns:
        Customer profile with conversation history
    """
    # Get customer info
    customer_query = """
        SELECT id, first_name, last_name, primary_email, primary_phone,
               company_name, customer_tier, overall_sentiment,
               satisfaction_score, last_contact_at
        FROM customers WHERE id = $1;
    """

    customer_result = await DatabasePool.execute_query(customer_query, customer_id)
    if not customer_result:
        logger.warning(f"⚠️ Customer not found: {customer_id}")
        return {}

    customer = dict(customer_result[0])

    # Get conversation history
    conv_query = """
        SELECT id, title, initial_intent, status, primary_channel,
               created_at, updated_at, message_count
        FROM conversations
        WHERE customer_id = $1
        ORDER BY created_at DESC
        LIMIT $2;
    """

    conversations = []
    conv_result = await DatabasePool.execute_query(conv_query, customer_id, limit)

    for conv in conv_result:
        conv_dict = dict(conv)

        # Get messages if requested
        if include_messages:
            msg_query = """
                SELECT id, content, message_type, source_channel,
                       sentiment, detected_intent, emotion_tags,
                       escalation_triggered, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT 10;
            """
            messages = await DatabasePool.execute_query(msg_query, conv["id"])
            conv_dict["messages"] = [dict(m) for m in messages]

        conversations.append(conv_dict)

    customer["conversations"] = conversations
    logger.info(f"✅ Retrieved history for customer {customer_id}: {len(conversations)} conversations")
    return customer


async def get_open_tickets(customer_id: UUID) -> List[Dict[str, Any]]:
    """
    Get all open tickets for a customer.

    Args:
        customer_id: Customer UUID

    Returns:
        List of open tickets
    """
    query = """
        SELECT id, ticket_number, title, priority, status,
               created_at, escalated, escalated_to
        FROM tickets
        WHERE customer_id = $1 AND status != 'closed'
        ORDER BY priority DESC, created_at DESC;
    """

    result = await DatabasePool.execute_query(query, customer_id)
    return [dict(row) for row in result]


# ============================================================================
# KNOWLEDGE BASE SEARCH (VECTOR SIMILARITY)
# ============================================================================

async def search_knowledge_base(
    query_embedding: List[float],
    limit: int = 5,
    similarity_threshold: float = 0.7,
) -> List[Dict[str, Any]]:
    """
    Search knowledge base using vector similarity (semantic search).
    Uses cosine similarity to find relevant documentation.

    Args:
        query_embedding: Query vector (1536 dims for OpenAI embeddings)
        limit: Max results to return
        similarity_threshold: Minimum similarity score (0-1)

    Returns:
        List of relevant knowledge base articles
    """
    # Convert to pgvector format
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    query = """
        SELECT id, title, content, category, section, url,
               1 - (embedding <=> $1::vector) as similarity_score,
               search_count, relevance_score
        FROM knowledge_base
        WHERE 1 - (embedding <=> $1::vector) > $2
        ORDER BY similarity_score DESC
        LIMIT $3;
    """

    result = await DatabasePool.execute_query(
        query,
        embedding_str,
        similarity_threshold,
        limit,
    )

    articles = [dict(row) for row in result]
    logger.info(f"✅ Found {len(articles)} relevant KB articles")
    return articles


async def add_knowledge_base_article(
    title: str,
    content: str,
    embedding: List[float],
    category: Optional[str] = None,
    section: Optional[str] = None,
    source: str = "product_docs",
    url: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> UUID:
    """
    Add a new knowledge base article with embedding.

    Args:
        title: Article title
        content: Article content
        embedding: Vector embedding (1536 dims)
        category: Article category
        section: Article section
        source: Source (product_docs, help_center, faq)
        url: Source URL
        tags: Search tags

    Returns:
        UUID of created article
    """
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    query = """
        INSERT INTO knowledge_base (
            title, content, embedding, category, section,
            source, url, tags, created_at, updated_at
        ) VALUES ($1, $2, $3::vector, $4, $5, $6, $7, $8, NOW(), NOW())
        RETURNING id;
    """

    result = await DatabasePool.execute_query(
        query,
        title,
        content,
        embedding_str,
        category,
        section,
        source,
        url,
        tags or [],
    )

    article_id = result[0]["id"]
    logger.info(f"✅ Added KB article: {article_id}")
    return article_id


async def increment_kb_search_count(kb_id: UUID) -> None:
    """Increment search count for a KB article (for ranking)"""
    query = """
        UPDATE knowledge_base
        SET search_count = search_count + 1,
            last_used_at = NOW()
        WHERE id = $1;
    """
    await DatabasePool.execute_query(query, kb_id)


# ============================================================================
# METRICS & REPORTING
# ============================================================================

async def record_agent_metrics(
    metric_hour: datetime,
    total_messages_processed: int,
    total_conversations: int,
    avg_response_time_ms: float,
    avg_sentiment_score: float,
    escalation_rate: float,
    email_messages: int = 0,
    whatsapp_messages: int = 0,
    web_form_messages: int = 0,
    api_errors: int = 0,
) -> None:
    """
    Record agent performance metrics for observability.

    Args:
        metric_hour: Hour bucket for metrics
        total_messages_processed: Total messages processed
        total_conversations: Total conversations handled
        avg_response_time_ms: Average response time
        avg_sentiment_score: Average sentiment score
        escalation_rate: Escalation rate percentage
        email_messages: Messages via email
        whatsapp_messages: Messages via WhatsApp
        web_form_messages: Messages via web form
        api_errors: API errors occurred
    """
    query = """
        INSERT INTO agent_metrics (
            metric_hour, total_messages_processed, total_conversations,
            avg_response_time_ms, avg_sentiment_score, escalation_rate,
            email_messages, whatsapp_messages, web_form_messages,
            api_errors, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW());
    """

    await DatabasePool.execute_query(
        query,
        metric_hour,
        total_messages_processed,
        total_conversations,
        avg_response_time_ms,
        avg_sentiment_score,
        escalation_rate,
        email_messages,
        whatsapp_messages,
        web_form_messages,
        api_errors,
    )
    logger.info(f"✅ Recorded metrics for {metric_hour}")


async def get_agent_metrics(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get agent metrics for the last N hours.

    Args:
        hours: Number of hours to retrieve

    Returns:
        List of hourly metrics
    """
    query = """
        SELECT * FROM agent_metrics
        WHERE metric_hour >= NOW() - INTERVAL '%d hours'
        ORDER BY metric_hour DESC;
    """ % hours

    result = await DatabasePool.execute_query(query)
    return [dict(row) for row in result]


# ============================================================================
# INITIALIZATION & HEALTH CHECK
# ============================================================================

async def health_check() -> bool:
    """
    Check database connectivity.

    Returns:
        True if database is healthy
    """
    try:
        result = await DatabasePool.execute_query("SELECT 1;")
        return bool(result)
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False


# ============================================================================
# END OF QUERIES
# ============================================================================
