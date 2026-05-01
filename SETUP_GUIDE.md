## Setup Guide: Complete Environment & Integration Setup

This guide explains exactly what you need to prepare for all integrations: Gmail API, WhatsApp (Twilio), Web Form, PostgreSQL Database, and OpenAI API.

### 📝 Environment Variables Template (`.env`)

Create a `.env` file in your project root with all these variables:

```bash
# ============================================================================
# DATABASE
# ============================================================================
DATABASE_URL=postgresql://username:password@localhost:5432/cloudflow_db
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=cloudflow_db

# ============================================================================
# OPENAI / AI
# ============================================================================
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

# ============================================================================
# GMAIL API
# ============================================================================
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.send

# ============================================================================
# TWILIO / WHATSAPP
# ============================================================================
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/webhooks/whatsapp

# ============================================================================
# WEB FORM
# ============================================================================
WEB_FORM_ENDPOINT=http://localhost:8000/webhooks/web-form
WEB_FORM_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# ============================================================================
# APPLICATION
# ============================================================================
APP_NAME=CloudFlow Customer Success FTE
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-for-sessions

# ============================================================================
# MONITORING & LOGGING
# ============================================================================
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id (optional)
LOG_FILE=logs/app.log
```

**Important:** 
- Add `.env` to `.gitignore` to prevent accidental commits
- Never commit real credentials to git
- Keep backups of your `.env` file safely

### 📧 Gmail API Setup (Step-by-Step)

To allow your AI Agent to read and send emails, follow these steps:

**1. Create a Google Cloud Project**

* Go to the **Google Cloud Console.**
* Create a new project (e.g., `Customer-Success-FTE`).

**2. Enable APIs**

* Navigate to **APIs & Services > Library.**
* Search for and enable **Gmail API.**
* Search for and enable **Cloud Pub/Sub API** (required for real-time notifications).

**3. Configure OAuth Consent Screen**

* Go to **APIs & Services > OAuth consent screen.**
* Select **External.**
* Add your email and app name.
* Add scopes: `https://www.googleapis.com/auth/gmail.readonly` and `https://www.googleapis.com/auth/gmail.send`.

**4. Create Credentials (Keys)**

* Go to **APIs & Services > Credentials.**
* Click **Create Credentials > OAuth client ID.**
* Select **Web application** (or Desktop app for local testing).
* **Authorized Redirect URIs:** Add `http://localhost:8000/auth/gmail/callback`.
* **Download the JSON file:** You will get a `client_id` and `client_secret`.

**5. Setup Pub/Sub (Push Notifications)**

* Go to the **Pub/Sub** section in the console.
* Create a **Topic** (e.g., `gmail-watch`).
* Grant `gmail-api-push@system.gserviceaccount.com` the **Pub/Sub Publisher** role on this topic.
* Create a **Subscription** (Push type) pointing to your FastAPI endpoint: `https://your-domain.com/webhooks/gmail`.

---

### 🗄️ Database Setup (CRM)

For this hackathon, PostgreSQL acts as your CRM.

**1. Connection Requirements**

You need a PostgreSQL URL in this format: `postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DATABASE_NAME>`

**2. Required Extensions**

Your database **MUST** have the `pgvector` extension installed for the Knowledge Base to work (semantic search). Run this query in your DB:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**3. Schema Preparation**

You will need to run the `schema.sql` (which we will create in Phase 2) to generate these tables:

* **customers** (Unified data)
* **conversations** (Thread history)
* **messages** (Individual messages)
* **tickets** (Support status)
* **knowledge_base** (Product docs + embeddings)

---

### 📱 WhatsApp Setup (Twilio)

While you didn't ask specifically, here is what you need for WhatsApp:

**1. Create/Access Your Twilio Account**
* Go to [Twilio Console](https://console.twilio.com)
* Sign up if you don't have an account
* Verify your email and phone number

**2. Get Your Account Credentials**
* Navigate to **Account Info** in the dashboard
* Copy your **Account SID** and **Auth Token**
* Store these securely in your `.env` file:
  ```
  TWILIO_ACCOUNT_SID=your_account_sid
  TWILIO_AUTH_TOKEN=your_auth_token
  ```

**3. Set Up WhatsApp Sandbox**
* Go to **Messaging > Try it out > Send a WhatsApp Message**
* Click on **Sandbox**
* You'll see a phone number and a join code (e.g., `join XXXXXX`)
* Send the join code to that number via WhatsApp to activate sandbox

**4. Get Your Twilio Phone Number**
* In the Sandbox section, you'll see your **Twilio Phone Number** (e.g., `+1234567890`)
* Store this in your `.env`:
  ```
  TWILIO_WHATSAPP_NUMBER=your_twilio_number
  ```

**5. Configure Webhook (For Receiving Messages)**
* Go to **Phone Numbers > Manage > Active Numbers**
* Select your Twilio number
* Scroll to **Messaging** section
* Set **Webhook URL** for incoming messages: `https://your-domain.com/webhooks/whatsapp`
* Set method to **POST**
* Save changes

**6. Add Test Users (Sandbox Only)**
* While in Sandbox mode, you can only message numbers that have joined
* Share the join code with team members who need to test
* Each tester sends the code to the Twilio number to activate

**7. Move to Production (Later)**
* When ready, apply for WhatsApp Business Account
* Get a production phone number
* Replace sandbox credentials with production ones

---

### 🌐 Web Form Setup

The Web Form is a standalone embeddable component for customer support submissions.

**1. Basic HTML Form**
Create your form with these required fields:
```html
<form id="support-form" action="http://localhost:8000/webhooks/web-form" method="POST">
  <input type="email" name="customer_email" placeholder="Your Email" required>
  <input type="text" name="subject" placeholder="Subject" required>
  <textarea name="message" placeholder="Describe your issue" required></textarea>
  <select name="priority">
    <option value="low">Low</option>
    <option value="medium" selected>Medium</option>
    <option value="high">High</option>
    <option value="critical">Critical</option>
  </select>
  <input type="hidden" name="channel" value="web_form">
  <button type="submit">Submit Support Request</button>
</form>
```

**2. Connect to Your FastAPI Backend**
* Form submits to: `POST /webhooks/web-form`
* Configure CORS in FastAPI to allow your domain:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "https://yourdomain.com"],
      allow_credentials=True,
      allow_methods=["POST", "GET"],
      allow_headers=["*"],
  )
  ```

**3. Store in `.env`**
```
WEB_FORM_ENDPOINT=http://localhost:8000/webhooks/web-form
```

**4. Response Handling**
The form will receive:
```json
{
  "status": "success",
  "ticket_id": "T-12345",
  "message": "We received your message. We'll respond within 2 hours."
}
```

**5. Database Storage**
Web form submissions automatically create tickets with:
- Channel: `web_form`
- Priority: Auto-detected from sentiment
- Status: `open`
- Created timestamp
- Customer email indexed for future lookups

---

## ✅ Verification Tests

Run these tests to confirm everything works:

```bash
# Test 1: Database connection
python -c "
from production.config.settings import settings
from sqlalchemy import text, create_engine
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connected!')
"

# Test 2: Check pgvector extension
python -c "
from production.config.settings import settings
from sqlalchemy import text, create_engine
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT extname FROM pg_extension WHERE extname = \'vector\''))
    if result.fetchone():
        print('✅ pgvector extension installed!')
    else:
        print('❌ pgvector NOT installed - semantic search won\'t work!')
"

# Test 3: Gmail credentials loaded
python -c "
from production.config.settings import settings
if settings.gmail_client_id:
    print(f'✅ Gmail Client ID loaded: {settings.gmail_client_id[:20]}...')
else:
    print('❌ GMAIL_CLIENT_ID not set in .env')
"

# Test 4: OpenAI key loaded
python -c "
from production.config.settings import settings
if settings.openai_api_key:
    print(f'✅ OpenAI API Key loaded: {settings.openai_api_key[:10]}...')
else:
    print('❌ OPENAI_API_KEY not set in .env')
"

# Test 5: Twilio credentials loaded
python -c "
from production.config.settings import settings
if settings.twilio_account_sid and settings.twilio_auth_token:
    print(f'✅ Twilio Account SID loaded: {settings.twilio_account_sid[:10]}...')
    print(f'✅ Twilio Auth Token loaded')
else:
    print('❌ TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set in .env')
"

# Test 6: Twilio WhatsApp number set
python -c "
from production.config.settings import settings
if settings.twilio_whatsapp_number:
    print(f'✅ Twilio WhatsApp Number loaded: {settings.twilio_whatsapp_number}')
else:
    print('❌ TWILIO_WHATSAPP_NUMBER not set in .env')
"

# Test 7: Web Form endpoint configured
python -c "
from production.config.settings import settings
if settings.web_form_endpoint:
    print(f'✅ Web Form Endpoint: {settings.web_form_endpoint}')
else:
    print('⚠️  WEB_FORM_ENDPOINT not set (optional for local development)')
"

# Test 8: Send test WhatsApp message
python -c "
from twilio.rest import Client
from production.config.settings import settings

try:
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    message = client.messages.create(
        body='Test message from CloudFlow AI',
        from_=f'whatsapp:{settings.twilio_whatsapp_number}',
        to='whatsapp:+1234567890'  # Replace with your test number
    )
    print(f'✅ Test WhatsApp message sent: {message.sid}')
except Exception as e:
    print(f'❌ Failed to send test message: {str(e)}')
"
```

---

## ✅ Pre-Launch Checklist

Before running the agent, verify you have:

### Gmail Setup
- [ ] Google Cloud Project created
- [ ] Gmail API enabled
- [ ] Cloud Pub/Sub API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth credentials (client_id & client_secret) downloaded
- [ ] Redirect URI configured: `http://localhost:8000/auth/gmail/callback`
- [ ] Pub/Sub topic created: `gmail-watch`
- [ ] Push subscription configured

### Database Setup
- [ ] PostgreSQL installed and running
- [ ] Database created
- [ ] pgvector extension installed
- [ ] All tables created
- [ ] Tables verified in database

### WhatsApp Setup (Twilio)
- [ ] Twilio account created
- [ ] Account SID & Auth Token copied
- [ ] WhatsApp Sandbox activated
- [ ] Twilio phone number obtained
- [ ] Webhook URL configured (for receiving messages)
- [ ] Test user(s) added to sandbox
- [ ] TWILIO_ACCOUNT_SID in `.env`
- [ ] TWILIO_AUTH_TOKEN in `.env`
- [ ] TWILIO_WHATSAPP_NUMBER in `.env`

### Web Form Setup
- [ ] HTML form created with required fields
- [ ] CORS configured in FastAPI
- [ ] Form action points to correct endpoint
- [ ] Test submission works end-to-end
- [ ] Response displays correctly to user
- [ ] WEB_FORM_ENDPOINT in `.env` (optional)

### Environment Configuration
- [ ] `.env` file created with all required variables
- [ ] `.env` added to `.gitignore`
- [ ] All secrets filled in (no placeholder values)
- [ ] Database URL tested and working
- [ ] Gmail credentials tested and working
- [ ] OpenAI API key tested and working
- [ ] Twilio credentials tested and working
- [ ] WhatsApp sandbox joined and ready

### Verification Tests
- [ ] Database connection test passes ✅
- [ ] pgvector extension check passes ✅
- [ ] Gmail credentials check passes ✅
- [ ] OpenAI credentials check passes ✅
- [ ] Twilio credentials check passes ✅
- [ ] Twilio WhatsApp number check passes ✅
- [ ] Web Form endpoint check passes ✅
- [ ] Test WhatsApp message sends successfully ✅

---

## 🚀 Next Steps

Once setup is complete:

1. **Start the FastAPI server:**
   ```bash
   cd production
   python -m uvicorn api.main:app --reload
   ```

2. **Run tests:**
   ```bash
   pytest production/tests/ -v
   ```

3. **View API docs:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

## ❓ Troubleshooting

### Issue: `pgvector` not installed
**Solution:**
```bash
# Connect to database
psql -U postgres -d your_database_name

# Install extension
CREATE EXTENSION IF NOT EXISTS vector;

# Verify
\dx
```

### Issue: `GMAIL_CLIENT_ID` not found
**Solution:**
- Verify `.env` file exists at project root
- Check that all required environment variables are set
- Restart your IDE or terminal to reload `.env`

### Issue: Database connection refused
**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS
# Windows: Check Services app for PostgreSQL
```

### Issue: Tables already exist
**Solution:**
```bash
# Drop and recreate
python -c "
from production.database.models import Base, engine
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print('✅ Database reset!')
"
```

### Issue: WhatsApp messages not received
**Solution:**
1. Verify webhook URL is publicly accessible (not localhost)
2. Check webhook is set to POST method in Twilio console
3. Verify .env has correct credentials:
   ```bash
   python -c "from production.config.settings import settings; print(settings.twilio_account_sid)"
   ```
4. Test with curl:
   ```bash
   curl -X POST http://localhost:8000/webhooks/whatsapp \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "From=whatsapp:%2B1234567890&Body=test"
   ```

### Issue: WhatsApp sandbox timeout after 72 hours
**Solution:**
- Twilio sandbox tokens expire after 72 hours of inactivity
- Re-join the sandbox by sending the join code again
- Check Twilio console for the current join code
- Keep the integration active by sending test messages every 48 hours

### Issue: Web Form returns 403 Forbidden
**Solution:**
- CORS is likely blocking the request
- Check your FastAPI CORS configuration includes your domain
- Verify `WEB_FORM_CORS_ORIGINS` in `.env`
- Test with a simple curl request:
  ```bash
  curl -X POST http://localhost:8000/webhooks/web-form \
    -H "Content-Type: application/json" \
    -d '{"customer_email":"test@example.com","subject":"Test","message":"Test message"}'
  ```

### Issue: Web Form submissions not appearing in database
**Solution:**
1. Check database tables exist:
   ```bash
   python -c "from production.database.models import Base; print(Base.metadata.tables.keys())"
   ```
2. Verify database connection in production logs
3. Check if form submission actually reaches the API:
   ```bash
   # Enable debug logging
   export LOG_LEVEL=DEBUG
   ```
4. Manually create a test ticket:
   ```bash
   python -c "
   from production.database.models import Ticket, engine
   from sqlalchemy.orm import Session
   session = Session(engine)
   ticket = Ticket(
       customer_email='test@example.com',
       subject='Test',
       message='Test message',
       channel='web_form',
       status='open'
   )
   session.add(ticket)
   session.commit()
   print(f'✅ Test ticket created: {ticket.id}')
   "
   ```

---

## 🔌 API Endpoints Reference

Your FastAPI application will expose these endpoints:

### Webhook Endpoints (Incoming Messages)
```
POST /webhooks/gmail         - Receive emails from Gmail
POST /webhooks/whatsapp      - Receive messages from WhatsApp
POST /webhooks/web-form      - Receive form submissions
```

### Health & Status
```
GET  /health                 - Application health check
GET  /status                 - System status
```

### Ticket Management
```
GET  /tickets                - List all tickets
GET  /tickets/{ticket_id}    - Get specific ticket
POST /tickets                - Create new ticket
PUT  /tickets/{ticket_id}    - Update ticket
```

### Customer Management
```
GET  /customers              - List all customers
GET  /customers/{customer_id} - Get customer details
GET  /customers/{customer_id}/history - Get conversation history
```

### Knowledge Base
```
GET  /knowledge-base         - Search knowledge articles
GET  /knowledge-base/{id}    - Get specific article
```

### Admin/Monitoring
```
GET  /docs                   - Swagger UI documentation
GET  /redoc                  - ReDoc documentation
GET  /metrics                - Prometheus metrics (for monitoring)
```

---

## 📚 Additional Resources

### Gmail Integration
- [Gmail API Docs](https://developers.google.com/gmail/api/guides)
- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
- [Google Cloud Console](https://console.cloud.google.com)
- [OAuth 2.0 Setup Guide](https://developers.google.com/identity/protocols/oauth2)

### WhatsApp & Twilio
- [Twilio WhatsApp API](https://www.twilio.com/whatsapp)
- [Twilio Console](https://console.twilio.com)
- [Twilio Python SDK](https://www.twilio.com/docs/python/install)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Twilio Webhooks Documentation](https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python)

### Database & ORM
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Web Development
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [HTML Forms Reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/form)

### AI & Embeddings
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Models](https://platform.openai.com/docs/models)
- [Embeddings API](https://platform.openai.com/docs/guides/embeddings)

### DevOps & Deployment
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)

---

## 🎯 Quick Start Checklist

After completing all setup steps:

1. ✅ `.env` file created with all credentials
2. ✅ PostgreSQL running with pgvector extension
3. ✅ Gmail API credentials obtained and stored
4. ✅ Twilio account created with WhatsApp sandbox
5. ✅ Web form HTML created and CORS configured
6. ✅ All verification tests passing
7. ✅ FastAPI server starting without errors
8. ✅ Can access Swagger docs at `http://localhost:8000/docs`

**Then you're ready to begin Exercise 2.1: Database Schema Implementation!**
