# 📧 Complete Guide: Setting Up & Running Gmail Integration

**Last Updated:** 2026-04-26  
**Difficulty:** Intermediate 🟡  
**Time Required:** 30-45 minutes  
**Prerequisites:** Google Account, Backend API running

---

## 🎯 What You'll Learn

By the end of this guide, you'll be able to:
- ✅ Create a Google Cloud project
- ✅ Setup OAuth2 authentication
- ✅ Get Gmail API credentials
- ✅ Configure backend for Gmail
- ✅ Test email receiving
- ✅ Verify Kafka integration

---

## 📋 Prerequisites

Before starting, make sure you have:

### 1. Google Account
- If you don't have one: https://accounts.google.com/signup
- Can be personal or business account

### 2. Backend API running
```bash
cd production/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. PostgreSQL running
```bash
# Using Docker
docker run --name cloudflow-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=cloudflow_db \
  -p 5432:5432 \
  -d postgres:15
```

### 4. Kafka running
```bash
# Using Docker Compose
docker-compose -f production/docker-compose.yml up -d kafka zookeeper
```

---

## 🚀 Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com/

2. Click on the project dropdown (top left)
   ```
   [Project] ▼
   ```

3. Click "New Project"

4. Fill in project details:
   ```
   Project name: CloudFlow Customer Success
   Organization: (leave blank or select yours)
   Location: (default is fine)
   ```

5. Click "Create"

6. **Expected:** You see "Your project CloudFlow Customer Success is ready"

---

### Step 2: Enable Gmail API

1. In Google Cloud Console, go to "APIs & Services" → "Library"

2. Search for "Gmail API"

3. Click on "Gmail API"

4. Click "Enable" button

5. **Expected:** You see "Gmail API is now enabled"

---

### Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"

2. Click "Create Credentials" button (top)

3. Select "OAuth client ID"

4. If prompted, click "Configure OAuth Consent Screen" first

5. **On OAuth Consent Screen:**
   - User Type: Select "External"
   - Click "Create"
   
   **On Consent Screen Form:**
   - App name: "CloudFlow Customer Success"
   - User support email: your.email@gmail.com
   - Developer contact: your.email@gmail.com
   - Click "Save and Continue"
   
   - Scopes: Click "Add or Remove Scopes"
     - Search for: "gmail.readonly"
     - Check: "Gmail API - See all your Gmail messages and settings"
     - Click "Update"
   - Click "Save and Continue"
   
   - Test users: Click "Add Users"
     - Add your Google account email
     - Click "Add"
   - Click "Save and Continue"

6. Go back to "Credentials" page

7. Click "Create Credentials" → "OAuth client ID"

8. Application type: Select "Web application"

9. Name: "CloudFlow API"

10. Authorized redirect URIs: Click "Add URI"
    ```
    http://localhost:8000/api/gmail/callback
    ```

11. Click "Create"

12. **Copy the credentials:**
    - Client ID: Copy this
    - Client Secret: Copy this

13. Click "Download JSON" to save credentials file

---

### Step 4: Configure Backend Environment

1. Open `.env` file in project root:
   ```bash
   nano .env
   ```

2. Add Gmail credentials:
   ```
   GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=your_client_secret_here
   GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
   GMAIL_USER_EMAIL=your.email@gmail.com
   ```

3. Replace:
   - `your_client_id_here` with Client ID from Step 3
   - `your_client_secret_here` with Client Secret from Step 3
   - `your.email@gmail.com` with your Gmail email address

4. Save file (Ctrl+X → Y → Enter in nano)

5. Verify in `.env`:
   ```bash
   grep GMAIL .env
   ```

---

### Step 5: Get Initial OAuth2 Refresh Token

1. Open browser and go to:
   ```
   http://localhost:8000/api/gmail/callback?code=test
   ```

2. You should be redirected to Gmail login

3. Sign in with your Google account

4. Click "Allow" when asked for permissions

5. **Expected:** Browser shows: "Authorization successful!"

6. Copy the refresh token from the response

7. Add to `.env`:
   ```
   GMAIL_REFRESH_TOKEN=your_refresh_token_here
   ```

---

### Step 6: Verify Backend Configuration

1. Restart FastAPI backend:
   ```bash
   # Kill the old one: Ctrl+C
   # Start new one:
   cd production/api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Check Gmail endpoint:
   ```bash
   curl http://localhost:8000/api/gmail/callback
   ```

3. **Expected response:**
   ```json
   {
     "status": "success",
     "message": "Gmail integration active"
   }
   ```

---

## 📧 Testing Gmail Integration

### Test 1: Manual Email Fetch

1. Send yourself a test email:
   ```
   To: your.email@gmail.com
   Subject: Test message for CloudFlow
   Message: This is a test to verify Gmail integration
   ```

2. Trigger fetch endpoint:
   ```bash
   curl http://localhost:8000/api/gmail/fetch
   ```

3. **Expected response:**
   ```json
   {
     "status": "success",
     "messages_fetched": 1,
     "latest_messages": [
       {
         "subject": "Test message for CloudFlow",
         "from": "your.email@gmail.com",
         "received_at": "2026-04-26T14:30:00"
       }
     ]
   }
   ```

4. Check backend logs:
   ```
   [INFO] Gmail: Fetched 1 new messages
   [INFO] Processing message: Test message for CloudFlow
   ```

---

### Test 2: Verify Kafka Publishing

1. Send another test email to yourself:
   ```
   Subject: Another test for Kafka
   Message: Verify this goes to Kafka
   ```

2. Monitor Kafka topic:
   ```bash
   kafka-console-consumer.sh --bootstrap-server localhost:9092 \
     --topic fte.tickets.incoming --from-beginning
   ```

3. Trigger fetch:
   ```bash
   curl http://localhost:8000/api/gmail/fetch
   ```

4. **Expected:** Message appears in Kafka topic showing:
   ```json
   {
     "customer_name": "Your Name",
     "email": "your.email@gmail.com",
     "subject": "Another test for Kafka",
     "message": "Verify this goes to Kafka",
     "channel": "email"
   }
   ```

---

### Test 3: Verify Database Storage

1. Check if message is stored in database:
   ```bash
   psql postgresql://postgres:password@localhost:5432/cloudflow_db
   ```

2. Query messages:
   ```sql
   SELECT * FROM messages WHERE channel = 'email' ORDER BY created_at DESC LIMIT 5;
   ```

3. **Expected:** You see your test emails in the database

---

### Test 4: End-to-End Flow

1. Send test email with subject and message

2. Verify Kafka receives it:
   ```bash
   kafka-console-consumer.sh --bootstrap-server localhost:9092 \
     --topic fte.tickets.incoming --max-messages=1
   ```

3. Verify database stores it:
   ```bash
   psql postgresql://postgres:password@localhost:5432/cloudflow_db \
     -c "SELECT subject, channel FROM messages ORDER BY created_at DESC LIMIT 1;"
   ```

4. Check backend logs for processing:
   ```
   [INFO] Processing email from your.email@gmail.com
   [INFO] Creating ticket for email
   [INFO] Ticket created: TICKET-2026-04-26-001
   ```

---

## 🔄 Continuous Email Polling

### Option 1: Manual Polling

Poll for new emails whenever needed:
```bash
curl http://localhost:8000/api/gmail/fetch
```

### Option 2: Automatic Polling (Advanced)

The backend automatically polls Gmail every 5 minutes. Check logs:

```bash
# Watch backend logs
tail -f logs/api.log | grep "Gmail"

# Expected output:
# [2026-04-26 14:30:00] [INFO] Gmail: Polling for new messages...
# [2026-04-26 14:30:05] [INFO] Gmail: Found 1 new message
```

---

## 🎨 Understanding the Integration

### Email Flow Diagram

```
Gmail Inbox
    ↓
OAuth2 Authentication
    ↓
Gmail API (Fetch Messages)
    ↓
Backend (API)
    ↓
Message Validation
    ↓
Kafka Topic (fte.tickets.incoming)
    ↓
Message Processor Worker
    ↓
CustomerSuccessAgent (AI Response)
    ↓
Response Published
    ↓
Email Reply Sent
```

### Data Transformation

When an email arrives:

```json
// From Gmail
{
  "from": "john@example.com",
  "subject": "Help with account",
  "body": "I need help..."
}

// Transforms to
{
  "customer_name": "John Doe",
  "email": "john@example.com",
  "subject": "Help with account",
  "message": "I need help...",
  "channel": "email"
}

// Stored as
{
  "ticket_id": "TICKET-2026-04-26-001",
  "customer_email": "john@example.com",
  "channel": "email",
  "created_at": "2026-04-26T14:30:00",
  "status": "open"
}
```

---

## ❌ Troubleshooting

### Issue: "Invalid Client ID"
**Solution:**
- Verify Client ID in `.env` matches Google Cloud Console
- No extra spaces or quotes
- Restart backend: Ctrl+C then restart

### Issue: "Refresh token expired"
**Solution:**
1. Delete old token from `.env`
2. Re-authenticate:
   ```bash
   curl http://localhost:8000/api/gmail/callback?code=new_code
   ```
3. Copy new refresh token to `.env`

### Issue: "Gmail API not enabled"
**Solution:**
1. Go to Google Cloud Console
2. APIs & Services → Library
3. Search "Gmail API"
4. Click "Enable"
5. Wait 5 minutes for changes to propagate
6. Restart backend

### Issue: "CORS error" in browser
**Solution:**
Check `.env` has:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Issue: No emails appearing
**Solution:**
1. Verify email was sent to correct address
2. Check spam/trash folder
3. Manually trigger fetch:
   ```bash
   curl http://localhost:8000/api/gmail/fetch
   ```
4. Check logs:
   ```bash
   tail -f logs/api.log | grep "Gmail"
   ```

### Issue: "redirect_uri_mismatch"
**Solution:**
1. Go to Google Cloud Console
2. Credentials → OAuth 2.0 Client IDs
3. Edit "CloudFlow API"
4. Verify Authorized redirect URIs includes:
   ```
   http://localhost:8000/api/gmail/callback
   ```
5. Save and restart backend

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth2 credentials created
- [ ] Client ID in `.env`
- [ ] Client Secret in `.env`
- [ ] Refresh token in `.env`
- [ ] Backend running and connected to Gmail
- [ ] Manual email fetch works
- [ ] Message appears in Kafka topic
- [ ] Message stored in database
- [ ] Backend logs show processing

---

## 📱 Multi-Channel Testing

Once Gmail is working:

1. **Test with Web Form**
   - See SETUP_WEBFORM.md
   - Submit form AND send email
   - Verify both appear in system

2. **Test with WhatsApp**
   - See SETUP_WHATSAPP.md
   - Try all 3 channels together

3. **Test Cross-Channel**
   - Send email
   - Also fill web form
   - Also send WhatsApp
   - All should have same ticket ID

---

## 📊 Monitoring

### View Emails Received

```bash
# Check Kafka topic for emails
kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic fte.tickets.incoming \
  --property print.key=true \
  --from-beginning | grep email

# Check database
psql postgresql://postgres:password@localhost:5432/cloudflow_db \
  -c "SELECT COUNT(*) FROM messages WHERE channel='email';"
```

### View Processing Logs

```bash
# Watch for Gmail processing
tail -f logs/api.log | grep -E "Gmail|email"

# Expected logs:
# [INFO] Gmail: Fetching new messages
# [INFO] Processing email: subject
# [INFO] Email stored: ticket_id
```

---

## 🔒 Security Notes

**Important:**
- Never share your Client Secret
- Never commit `.env` file to git
- Refresh tokens are sensitive - keep secure
- Use environment variables in production
- Rotate tokens periodically

**In Production:**
- Use production Gmail OAuth credentials
- Enable "Less secure app access" warning awareness
- Implement token refresh logic
- Monitor for unauthorized access
- Log all email processing

---

## 📚 File Locations

**Backend Gmail Integration:**
- Config: `production/config/settings.py`
- Handler: `production/channels/email_handler.py`
- API: `production/api/main.py` (search for `/api/gmail/`)

**Environment:**
- `.env` - Gmail credentials
- `.env.example` - Template with placeholders

---

## 💡 Tips

- **Test multiple emails:** Send from different senders
- **Test special characters:** Verify special chars work
- **Test long messages:** Verify character limits
- **Monitor logs:** `tail -f logs/api.log` in separate terminal
- **Test offline:** System works without Kafka briefly
- **Check rate limits:** Gmail API has rate limits (see docs)

---

## 📞 Getting Help

**If stuck:**

1. Check backend logs:
   ```bash
   tail -f logs/api.log
   ```

2. Verify credentials:
   ```bash
   grep GMAIL .env
   ```

3. Test API directly:
   ```bash
   curl http://localhost:8000/api/gmail/fetch -v
   ```

4. Check Google Cloud Console for errors

---

## 🎉 Success!

You've successfully:
- ✅ Created Google Cloud project
- ✅ Enabled Gmail API
- ✅ Setup OAuth2 authentication
- ✅ Configured backend
- ✅ Tested email receiving
- ✅ Verified Kafka integration

**Next:** Setup WhatsApp integration using SETUP_WHATSAPP.md!

---

**Questions?** Check troubleshooting section or see `production/README.md` for more help.

*Gmail Setup Complete!* 📧🚀
