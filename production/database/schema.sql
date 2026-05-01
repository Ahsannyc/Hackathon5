-- ============================================================================
-- CloudFlow Customer Success FTE - PostgreSQL Schema
-- ============================================================================
-- This is the complete CRM/Ticket Management System for the AI Employee.
-- All customer interactions, tickets, and knowledge are stored here.
-- ============================================================================

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CUSTOMERS TABLE
-- ============================================================================
-- Unified customer profile across all channels (Email, WhatsApp, Web Form)
-- Single source of truth for customer identity
-- ============================================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic customer information
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),

    -- Primary contact (for unified view)
    primary_email VARCHAR(255),
    primary_phone VARCHAR(20),

    -- Metadata
    customer_tier VARCHAR(50) DEFAULT 'standard' CHECK (customer_tier IN ('free', 'standard', 'premium', 'enterprise')),
    account_status VARCHAR(50) DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended', 'closed')),

    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_contact_at TIMESTAMP WITH TIME ZONE,

    -- Sentiment summary
    overall_sentiment VARCHAR(50) DEFAULT 'neutral' CHECK (overall_sentiment IN ('very_negative', 'negative', 'neutral', 'positive', 'very_positive')),
    satisfaction_score DECIMAL(3, 2) CHECK (satisfaction_score >= 0 AND satisfaction_score <= 5),

    CONSTRAINT customers_email_check CHECK (primary_email IS NOT NULL OR primary_phone IS NOT NULL)
);

CREATE INDEX idx_customers_email ON customers(primary_email) WHERE primary_email IS NOT NULL;
CREATE INDEX idx_customers_phone ON customers(primary_phone) WHERE primary_phone IS NOT NULL;
CREATE INDEX idx_customers_status ON customers(account_status);
CREATE INDEX idx_customers_created ON customers(created_at DESC);

-- ============================================================================
-- 2. CUSTOMER_IDENTIFIERS TABLE
-- ============================================================================
-- Maps multiple channel identifiers to a single customer
-- Enables cross-channel continuity (same person across Email, WhatsApp, Web)
-- ============================================================================
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- Channel information
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('email', 'whatsapp', 'web_form')),
    channel_identifier VARCHAR(255) NOT NULL,

    -- Metadata
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique mapping per channel
    CONSTRAINT unique_channel_identifier UNIQUE(channel, channel_identifier)
);

CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers(customer_id);
CREATE INDEX idx_customer_identifiers_channel ON customer_identifiers(channel);
CREATE INDEX idx_customer_identifiers_lookup ON customer_identifiers(channel, channel_identifier);

-- ============================================================================
-- 3. CONVERSATIONS TABLE
-- ============================================================================
-- Groups messages into logical conversation threads
-- Tracks conversation-level sentiment and resolution status
-- ============================================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- Conversation metadata
    title VARCHAR(500),
    initial_intent VARCHAR(255),
    primary_channel VARCHAR(50) NOT NULL CHECK (primary_channel IN ('email', 'whatsapp', 'web_form')),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'pending', 'resolved', 'escalated')),
    resolution_status VARCHAR(50) CHECK (resolution_status IN ('solved', 'unsolved', 'cancelled', NULL)),

    -- Sentiment and emotion tracking
    sentiment_trajectory VARCHAR(50),  -- improving, declining, stable
    customer_emotion_tags TEXT[],  -- e.g., {'frustrated', 'confused'}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Message count for quick stats
    message_count INTEGER DEFAULT 0,
    human_handoff_count INTEGER DEFAULT 0
);

CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_primary_channel ON conversations(primary_channel);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- ============================================================================
-- 4. MESSAGES TABLE
-- ============================================================================
-- Individual messages with AI analysis (sentiment, intent, emotion)
-- Tracks source channel and any channel switches
-- ============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- Message content
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'user' CHECK (message_type IN ('user', 'agent', 'system')),

    -- Channel information
    source_channel VARCHAR(50) NOT NULL CHECK (source_channel IN ('email', 'whatsapp', 'web_form')),
    channel_message_id VARCHAR(500),  -- ID from external channel (Gmail, Twilio, etc)

    -- AI Analysis
    sentiment VARCHAR(50) CHECK (sentiment IN ('very_negative', 'negative', 'neutral', 'positive', 'very_positive')),
    sentiment_confidence DECIMAL(3, 2) CHECK (sentiment_confidence >= 0 AND sentiment_confidence <= 1),
    detected_intent VARCHAR(255),
    intent_confidence DECIMAL(3, 2) CHECK (intent_confidence >= 0 AND intent_confidence <= 1),
    emotion_tags TEXT[],  -- e.g., {'frustrated', 'happy', 'confused'}

    -- Escalation signals
    escalation_triggered BOOLEAN DEFAULT false,
    escalation_reason VARCHAR(500),
    requires_human BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    word_count INTEGER,
    tokens_used INTEGER  -- for API usage tracking
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_customer ON messages(customer_id);
CREATE INDEX idx_messages_channel ON messages(source_channel);
CREATE INDEX idx_messages_sentiment ON messages(sentiment);
CREATE INDEX idx_messages_intent ON messages(detected_intent);
CREATE INDEX idx_messages_escalation ON messages(escalation_triggered, requires_human);
CREATE INDEX idx_messages_created ON messages(created_at DESC);

-- ============================================================================
-- 5. TICKETS TABLE
-- ============================================================================
-- Support tickets with SLA tracking and escalation information
-- One ticket per issue, can span multiple conversations
-- ============================================================================
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,

    -- Ticket identification
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Category and priority
    category VARCHAR(100),  -- e.g., 'billing', 'technical', 'feature_request'
    priority VARCHAR(50) NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'pending_customer', 'resolved', 'closed', 'reopened')),

    -- SLA tracking (in minutes)
    sla_response_minutes INTEGER,  -- Target response time based on priority
    sla_resolution_minutes INTEGER,  -- Target resolution time based on priority
    first_response_at TIMESTAMP WITH TIME ZONE,
    first_response_time_minutes INTEGER,  -- Actual response time
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_time_minutes INTEGER,  -- Actual resolution time

    -- Escalation info
    escalated BOOLEAN DEFAULT false,
    escalated_to VARCHAR(255),  -- Team or person
    escalation_reason VARCHAR(500),
    escalated_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE,

    -- Metrics
    resolution_attempts INTEGER DEFAULT 0,
    satisfaction_rating DECIMAL(3, 2) CHECK (satisfaction_rating >= 0 AND satisfaction_rating <= 5)
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_conversation ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_escalated ON tickets(escalated);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX idx_tickets_ticket_number ON tickets(ticket_number);

-- ============================================================================
-- 6. KNOWLEDGE_BASE TABLE
-- ============================================================================
-- Product documentation with vector embeddings for semantic search
-- Enables AI agent to find relevant docs even with different phrasing
-- ============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    section VARCHAR(255),  -- e.g., 'Getting Started', 'Troubleshooting'

    -- Vector embedding (1536 dimensions for OpenAI embeddings)
    embedding vector(1536),

    -- Metadata
    source VARCHAR(255),  -- e.g., 'product_docs', 'help_center', 'faq'
    url VARCHAR(500),
    version VARCHAR(50),

    -- Usage metrics
    search_count INTEGER DEFAULT 0,
    relevance_score DECIMAL(3, 2),  -- How often this doc was useful
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Tags for categorization
    tags TEXT[]
);

-- Vector search index (HNSW for fast similarity search)
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING hnsw (embedding vector_cosine_ops);
-- Standard indexes
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_source ON knowledge_base(source);
CREATE INDEX idx_knowledge_base_search_count ON knowledge_base(search_count DESC);

-- ============================================================================
-- 7. CHANNEL_CONFIGS TABLE
-- ============================================================================
-- Configuration for each communication channel
-- Enables channel-specific response formatting and rate limiting
-- ============================================================================
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Channel identification
    channel VARCHAR(50) NOT NULL UNIQUE CHECK (channel IN ('email', 'whatsapp', 'web_form')),

    -- Channel settings
    enabled BOOLEAN DEFAULT true,
    max_response_length INTEGER,  -- chars (e.g., 150 for WhatsApp, 500 for Email)
    response_style VARCHAR(50),  -- e.g., 'formal', 'casual', 'technical'

    -- API credentials (stored securely, referenced from .env)
    api_key_env_var VARCHAR(255),  -- e.g., 'GMAIL_CLIENT_ID'
    webhook_url VARCHAR(500),

    -- Rate limiting
    rate_limit_requests_per_minute INTEGER DEFAULT 60,
    rate_limit_burst INTEGER DEFAULT 10,

    -- Escalation thresholds
    escalation_on_sentiment_threshold DECIMAL(3, 2),  -- Escalate if sentiment < this
    escalation_on_response_time_minutes INTEGER,  -- Escalate if response takes longer

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_channel_configs_channel ON channel_configs(channel);
CREATE INDEX idx_channel_configs_enabled ON channel_configs(enabled);

-- ============================================================================
-- 8. AGENT_METRICS TABLE
-- ============================================================================
-- Tracks agent performance metrics for monitoring and improvement
-- Used for observability and SLA verification
-- ============================================================================
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Time bucket (hourly aggregation)
    metric_hour TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Request metrics
    total_messages_processed INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    total_tickets_created INTEGER DEFAULT 0,

    -- Performance metrics
    avg_response_time_ms DECIMAL(10, 2),
    p95_response_time_ms DECIMAL(10, 2),
    p99_response_time_ms DECIMAL(10, 2),

    -- Quality metrics
    avg_sentiment_score DECIMAL(3, 2),
    avg_intent_detection_confidence DECIMAL(3, 2),

    -- Escalation metrics
    escalation_rate DECIMAL(5, 2),  -- percentage
    human_escalations INTEGER DEFAULT 0,

    -- Channel breakdown
    email_messages INTEGER DEFAULT 0,
    whatsapp_messages INTEGER DEFAULT 0,
    web_form_messages INTEGER DEFAULT 0,

    -- Errors
    api_errors INTEGER DEFAULT 0,
    processing_errors INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_metrics_hour ON agent_metrics(metric_hour DESC);
CREATE INDEX idx_agent_metrics_created ON agent_metrics(created_at DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER channel_configs_updated_at BEFORE UPDATE ON channel_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER agent_metrics_updated_at BEFORE UPDATE ON agent_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE customers IS 'Unified customer profile across all channels (Email, WhatsApp, Web Form)';
COMMENT ON TABLE customer_identifiers IS 'Maps multiple channel identifiers to single customer - enables cross-channel continuity';
COMMENT ON TABLE conversations IS 'Conversation threads grouped by customer and primary channel';
COMMENT ON TABLE messages IS 'Individual messages with AI analysis (sentiment, intent, emotion)';
COMMENT ON TABLE tickets IS 'Support tickets with SLA tracking and escalation management';
COMMENT ON TABLE knowledge_base IS 'Product documentation with vector embeddings for semantic search';
COMMENT ON TABLE channel_configs IS 'Configuration for each communication channel (Email, WhatsApp, Web Form)';
COMMENT ON TABLE agent_metrics IS 'Agent performance metrics for monitoring and observability';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
