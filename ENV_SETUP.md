# Environment Configuration Guide

## Overview

This guide explains how to set up environment variables for CloudFlow Customer Success AI Employee.

## Quick Start

### 1. Create .env file from template

```bash
cp production/.env.example production/.env
```

### 2. Edit production/.env

Open the file and fill in your actual values:

```bash
nano production/.env  # or your preferred editor
```

## Configuration Sections

### Application Settings

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | development | app environment (development/staging/production) |
| `DEBUG` | true | enable debug mode (NEVER true in production) |
| `SECRET_KEY` | generated | flask/fastapi secret key |
| `LOG_LEVEL` | INFO | logging level (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FORMAT` | json | log format (json/text) |

### Database

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | postgresql://cloudflow:password@localhost:5432/cloudflow_db | PostgreSQL connection string |
| `DB_POOL_SIZE` | 20 | connection pool size |
| `DB_MAX_OVERFLOW` | 40 | max overflow connections |

**PostgreSQL Connection String Format:**
```
postgresql://username:password@host:port/database_name
```

### Redis Cache

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection URL |
| `CACHE_TTL` | 3600 | cache time-to-live (seconds) |

### Kafka Event Streaming

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | localhost:9092 | kafka broker addresses |
| `KAFKA_CONSUMER_GROUP` | cloudflow-agents | consumer group name |
| `KAFKA_TOPIC_MESSAGES` | customer-messages | messages topic |
| `KAFKA_TOPIC_ESCALATIONS` | escalations | escalations topic |

### Gmail Integration

| Variable | Required | Purpose |
|----------|----------|---------|
| `GMAIL_ENABLED` | ✅ | enable gmail channel |
| `GMAIL_CLIENT_ID` | ✅ | from Google Cloud Console |
| `GMAIL_CLIENT_SECRET` | ✅ | from Google Cloud Console |
| `GMAIL_REDIRECT_URI` | ✅ | oauth2 redirect URI |

**Setup Steps:**
1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Web application)
5. Copy Client ID and Client Secret

### WhatsApp Business API

| Variable | Required | Purpose |
|----------|----------|---------|
| `WHATSAPP_ENABLED` | ✅ | enable whatsapp channel |
| `WHATSAPP_BUSINESS_TOKEN` | ✅ | from Meta Business Dashboard |
| `WHATSAPP_BUSINESS_PHONE_ID` | ✅ | your whatsapp phone number id |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | ✅ | custom webhook verification token |

**Setup Steps:**
1. Go to https://business.facebook.com
2. Create WhatsApp Business App
3. Get access token
4. Get phone number ID
5. Set webhook URL: `{your-domain}/api/whatsapp/webhook`

### Monitoring & Observability

| Variable | Default | Purpose |
|----------|---------|---------|
| `SENTRY_DSN` | optional | sentry error tracking |
| `SENTRY_ENABLED` | true | enable sentry |
| `PROMETHEUS_ENABLED` | true | enable prometheus metrics |
| `PROMETHEUS_PORT` | 9090 | prometheus port |
| `GRAFANA_PORT` | 3000 | grafana dashboard port |

### Rate Limiting

| Variable | Default | Purpose |
|----------|---------|---------|
| `RATE_LIMIT_PER_MINUTE` | 100 | requests per minute per ip |
| `RATE_LIMIT_PER_HOUR` | 1000 | requests per hour per ip |

### Celery Task Queue

| Variable | Default | Purpose |
|----------|---------|---------|
| `CELERY_BROKER_URL` | redis://localhost:6379/1 | celery broker (redis) |
| `CELERY_RESULT_BACKEND` | redis://localhost:6379/2 | celery results backend |

## Security Guidelines

### ⚠️ NEVER

- ❌ Commit .env to version control
- ❌ Use the same SECRET_KEY in production as development
- ❌ Share API keys in chat/email
- ❌ Log sensitive information
- ❌ Set DEBUG=true in production

### ✅ DO

- ✅ Use strong, random SECRET_KEY
- ✅ Rotate API keys regularly
- ✅ Use environment-specific .env files
- ✅ Store secrets in secure vault (AWS Secrets Manager, etc.) in production
- ✅ Use HTTPS for all external API calls

## Local Development Setup

### Prerequisites

```bash
# Install PostgreSQL
brew install postgresql  # macOS
apt-get install postgresql  # Ubuntu
choco install postgresql  # Windows

# Install Redis
brew install redis  # macOS
apt-get install redis-server  # Ubuntu
choco install redis  # Windows

# Install Kafka (optional for local dev)
brew install kafka  # macOS
```

### Start Local Services

```bash
# Terminal 1: PostgreSQL
pg_ctl start
# or
sudo systemctl start postgresql

# Terminal 2: Redis
redis-server

# Terminal 3: Kafka (optional)
zookeeper-server-start.sh config/zookeeper.properties
kafka-server-start.sh config/server.properties
```

### Create Database

```bash
createdb cloudflow_db
psql cloudflow_db < production/database/schema.sql
```

### Run Application

```bash
cd production
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

## Docker Development

If using Docker Compose:

```bash
cd production
docker-compose up -d
```

This starts:
- PostgreSQL
- Redis
- Kafka
- Prometheus
- Grafana

## Environment-Specific Configurations

### Development (.env)

```
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
SENTRY_ENABLED=false
```

### Staging

```
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
SENTRY_ENABLED=true
```

### Production

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SENTRY_ENABLED=true
SECRET_KEY={strong-random-key}
DATABASE_URL={production-db-url}
```

## Troubleshooting

### Database Connection Failed
```
Error: could not translate host name "localhost" to address
```
**Solution:** Ensure PostgreSQL is running
```bash
pg_isready  # check postgresql status
```

### Redis Connection Error
```
Error: ConnectionError to redis://localhost:6379/0
```
**Solution:** Ensure Redis is running
```bash
redis-cli ping  # should return PONG
```

### Gmail API Not Working
```
Error: Invalid OAuth client
```
**Solution:**
1. Verify CLIENT_ID and CLIENT_SECRET
2. Check redirect URI matches in Google Cloud Console
3. Ensure Gmail API is enabled

### WhatsApp Webhook Not Receiving Messages
**Solution:**
1. Verify WHATSAPP_WEBHOOK_VERIFY_TOKEN matches Meta Business config
2. Check webhook URL is publicly accessible
3. Verify webhook is set to POST (not GET)

## Reference

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Google Gmail API](https://developers.google.com/gmail/api)
- [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Sentry Documentation](https://docs.sentry.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)

---

**Last Updated:** 2026-04-02  
**Status:** Complete
