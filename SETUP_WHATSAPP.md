# 💬 Complete Guide: Setting Up & Running WhatsApp Integration

**Last Updated:** 2026-04-26  
**Difficulty:** Intermediate 🟡  
**Time Required:** 45-60 minutes  
**Prerequisites:** Twilio Account, Phone Number, Backend API running

---

## 🎯 What You'll Learn

By the end of this guide, you'll be able to:
- ✅ Create Twilio account
- ✅ Setup WhatsApp Business account
- ✅ Get API credentials
- ✅ Configure webhook URLs
- ✅ Test WhatsApp messages
- ✅ Verify Kafka integration

---

## 📋 Prerequisites

Before starting, make sure you have:

### 1. Twilio Account
- Sign up: https://www.twilio.com/try-twilio
- Free trial gives $15 credit
- Can use test credentials initially

### 2. Phone Number (for testing)
- Any phone number that can receive SMS/WhatsApp
- Will receive test messages
- Can be personal phone

### 3. Backend API running
```bash
cd production/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Public URL for webhook (for production)
- For testing locally, you can use ngrok (comes later)
- For production, use your domain name

### 5. PostgreSQL and Kafka running
Same as Gmail setup (see SETUP_GMAIL.md)

---

## 🚀 Step-by-Step Setup

### Step 1: Create Twilio Account

1. Go to: https://www.twilio.com/try-twilio

2. Sign up with:
   - Email address
   - Password
   - Phone number

3. Verify email and phone

4. **Expected:** You see Twilio dashboard

5. Copy your Account SID:
   - Dashboard shows: "Account SID: AC..."
   - Copy this value

6. Copy your Auth Token:
   - Dashboard shows: "Auth Token: ..."
   - Click "Show" if hidden
   - Copy this value

---

### Step 2: Enable WhatsApp Sandbox

1. In Twilio Console, go to "Messaging" → "Try it out" → "Send a WhatsApp message"

2. Or navigate directly to WhatsApp Sandbox:
   - https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-sandbox

3. Click "Get Sandbox Number"

4. **Expected:** You get a WhatsApp number like:
   ```
   +1 (415) 523-8886
   or similar
   ```

5. Copy this number

6. Join sandbox:
   - You'll see: "Send this message to join sandbox:"
   - Open WhatsApp on your phone
   - Add contact: (or use existing): +1 (415) 523-8886
   - Send message: `join code-here` (it shows the code)
   - **Expected:** Sandbox confirms you joined

---

### Step 3: Get Twilio Credentials

1. Go to: https://console.twilio.com/account/keys-credentials

2. View credentials section:
   - **Account SID:** AC... (copy)
   - **Auth Token:** ... (copy, hidden by default)

3. Note your phone number to receive messages:
   - The phone you'll use to receive test messages
   - Example: +1 5551234567

---

### Step 4: Get Twilio WhatsApp Number

1. Go to: https://console.twilio.com/us1/develop/sms/messaging-services

2. Or click "Messaging" → "Services"

3. Click "Create Messaging Service"

4. Service name: "CloudFlow WhatsApp"

5. Use case: "WhatsApp Messages"

6. Click "Create"

7. In the service, click "Senders" → "Add Sender"

8. Select "WhatsApp"

9. Select the sandbox number you got earlier

10. Click "Add Sender"

11. **Expected:** You see the WhatsApp number in senders list

12. Copy this number (format: `whatsapp:+1xxxxxxxxxx`)

---

### Step 5: Setup Webhook URL

For local testing, you need a public URL pointing to your local machine:

**Option A: Using ngrok (Recommended for Testing)**

1. Download ngrok: https://ngrok.com/download

2. Extract and run:
   ```bash
   ./ngrok http 8000
   ```

3. **Expected output:**
   ```
   Forwarding: http://XXXXX.ngrok.io -> http://localhost:8000
   ```

4. Copy the URL: `http://XXXXX.ngrok.io`

5. This is your public URL for webhooks

**Option B: Using your domain (Production)**

If you have a domain:
```
https://yourdomain.com
```

---

### Step 6: Configure Backend Environment

1. Open `.env` file:
   ```bash
   nano .env
   ```

2. Add Twilio credentials:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=whatsapp:+1xxxxxxxxxx
   TWILIO_WEBHOOK_URL=http://XXXXX.ngrok.io/api/whatsapp/webhook
   TWILIO_SANDBOX_MODE=true
   ```

3. Replace:
   - `ACxxxxxxxxxxxxxxxxxxxxxxxxxx` - Your Account SID
   - `your_auth_token_here` - Your Auth Token
   - `whatsapp:+1xxxxxxxxxx` - Your WhatsApp number
   - `http://XXXXX.ngrok.io` - Your ngrok URL (or domain)

4. Save file (Ctrl+X → Y → Enter)

5. Verify:
   ```bash
   grep TWILIO .env
   ```

---

### Step 7: Setup Twilio Webhooks

1. Go to: https://console.twilio.com/us1/develop/sms/services

2. Click your WhatsApp Messaging Service

3. Go to "Integration" tab

4. Find "Webhook Configuration"

5. Set "Inbound URL":
   ```
   http://XXXXX.ngrok.io/api/whatsapp/webhook
   ```
   (Replace with your ngrok URL)

6. Set "Webhook Method": POST

7. Click "Save"

8. **Expected:** Webhook URL is saved

---

### Step 8: Restart Backend

1. Stop FastAPI backend (Ctrl+C in terminal)

2. Start it again:
   ```bash
   cd production/api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Verify it started:
   ```bash
   curl http://localhost:8000/api/health
   ```

---

## 💬 Testing WhatsApp Integration

### Test 1: Send Message to Twilio Sandbox

1. Open WhatsApp on your phone

2. Send message to Twilio WhatsApp number:
   ```
   To: (the sandbox number from Step 2)
   Message: "Hello, this is a test message"
   ```

3. Check backend logs:
   ```bash
   tail -f logs/api.log | grep -i whatsapp
   ```

4. **Expected logs:**
   ```
   [INFO] WhatsApp webhook received
   [INFO] From: +1 (your phone number)
   [INFO] Message: Hello, this is a test message
   ```

---

### Test 2: Verify Webhook is Working

1. Send another WhatsApp message:
   ```
   "Test message 2 for CloudFlow"
   ```

2. Watch ngrok terminal window:
   ```
   POST /api/whatsapp/webhook 200 OK
   ```

3. This confirms the webhook is being called

---

### Test 3: Verify Kafka Publishing

1. Send WhatsApp message:
   ```
   "Verify this goes to Kafka"
   ```

2. Monitor Kafka topic:
   ```bash
   kafka-console-consumer.sh --bootstrap-server localhost:9092 \
     --topic fte.tickets.incoming --from-beginning
   ```

3. **Expected:** Message appears in Kafka showing:
   ```json
   {
     "customer_phone": "+1 (your number)",
     "message": "Verify this goes to Kafka",
     "channel": "whatsapp"
   }
   ```

---

### Test 4: Verify Database Storage

1. Send WhatsApp message:
   ```
   "Test for database storage"
   ```

2. Check database:
   ```bash
   psql postgresql://postgres:password@localhost:5432/cloudflow_db
   ```

3. Query messages:
   ```sql
   SELECT * FROM messages WHERE channel = 'whatsapp' ORDER BY created_at DESC LIMIT 1;
   ```

4. **Expected:** Message is stored with:
   - Channel: "whatsapp"
   - Content: "Test for database storage"
   - Timestamp: current time

---

### Test 5: End-to-End Flow

Complete test from WhatsApp to system:

1. **Send message from your phone:**
   ```
   To: WhatsApp Sandbox Number
   Message: "Order status inquiry"
   ```

2. **Verify webhook received it:**
   ```bash
   tail -f logs/api.log | grep "WhatsApp"
   ```
   Expected: `WhatsApp webhook received from +1...`

3. **Verify Kafka got it:**
   ```bash
   kafka-console-consumer.sh --bootstrap-server localhost:9092 \
     --topic fte.tickets.incoming --max-messages=1
   ```
   Expected: Message in JSON format

4. **Verify database stored it:**
   ```bash
   psql postgresql://postgres:password@localhost:5432/cloudflow_db \
     -c "SELECT COUNT(*) FROM messages WHERE channel='whatsapp';"
   ```
   Expected: Count increased by 1

5. **Verify ticket was created:**
   ```bash
   psql postgresql://postgres:password@localhost:5432/cloudflow_db \
     -c "SELECT id, status FROM tickets ORDER BY created_at DESC LIMIT 1;"
   ```
   Expected: New ticket with status "open"

---

## 🔒 Understanding Twilio Signature Validation

The system validates that messages come from Twilio:

### How it Works

1. Twilio sends webhook with:
   - Message data
   - `X-Twilio-Signature` header

2. Backend calculates signature using:
   - Webhook URL
   - Request parameters
   - Auth Token (secret key)

3. Backend compares:
   - Received signature vs calculated signature
   - If they match: message is valid ✅
   - If they don't match: message is rejected ❌

### Verify in Code

File: `production/api/main.py`

Search for: `validate_twilio_signature`

You'll see:
```python
def validate_twilio_signature(request_signature, url, params, token):
    """Validate that request came from Twilio"""
    # Calculate signature
    # Compare with request_signature
    # Return True/False
```

---

## 📱 Testing Different Message Types

### Test 1: Text Message

```
Send to sandbox: "Simple text message"
```

### Test 2: Message with Special Characters

```
Send to sandbox: "Special chars: @#$%^&*()"
```

### Test 3: Long Message

```
Send to sandbox: "This is a very long message that contains
multiple lines and tests the character limit
to make sure the system handles it correctly."
```

### Test 4: Emoji Support

```
Send to sandbox: "Testing emojis 😊 🎉 ✅"
```

---

## ⚠️ Important Notes

### ngrok URL Changes
- ngrok URL changes every time you restart
- Update `.env` with new URL
- Restart backend
- Update Twilio webhook URL

### Sandbox vs Production
- Sandbox: Free, for testing
- Production: Requires WhatsApp Business account approval
- For production, see Twilio documentation

### Message Limits
- Sandbox: Can only receive 1 message per joining
- Must rejoin to receive another
- Production: No limits

### Testing Best Practices
- Keep ngrok running while testing
- Monitor logs continuously
- Test with various message types
- Verify Kafka receives messages
- Check database for storage

---

## ❌ Troubleshooting

### Issue: "Webhook not receiving messages"
**Solution:**
1. Verify ngrok is running: `./ngrok http 8000`
2. Check ngrok URL in `.env` matches: `grep TWILIO_WEBHOOK .env`
3. Verify Twilio webhook URL is correct:
   - Go to Twilio Console → Messaging → Services
   - Check inbound URL matches ngrok
4. Restart backend: Ctrl+C then restart

### Issue: "Invalid signature" error
**Solution:**
1. Verify Auth Token in `.env` is correct
2. Verify Auth Token matches Twilio Console
3. No extra spaces in `.env`
4. Restart backend
5. Send message again

### Issue: "Webhook URL timeout"
**Solution:**
1. Ensure backend is running: `curl http://localhost:8000/api/health`
2. Ensure ngrok is running: check ngrok terminal
3. Check port 8000 is not blocked
4. Check firewall settings

### Issue: "Phone number not authorized"
**Solution:**
1. Go to Twilio Console → Messaging → Sandbox
2. Rejoin sandbox with same phone
3. Send "join [code]" again
4. Try sending message again

### Issue: "No messages in Kafka"
**Solution:**
1. Verify message was received (check backend logs)
2. Verify Kafka is running:
   ```bash
   kafka-broker-api-versions.sh --bootstrap-server localhost:9092
   ```
3. Verify backend can connect to Kafka:
   ```bash
   curl http://localhost:8000/api/health/kafka
   ```

### Issue: "ngrok connection refused"
**Solution:**
1. Verify backend is running on port 8000
2. Start ngrok: `./ngrok http 8000`
3. Wait for ngrok to show "Forwarding" URL
4. Copy URL to `.env`
5. Restart backend

### Issue: "CORS error"
**Solution:**
Check `.env` has:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8001
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Twilio account created
- [ ] WhatsApp sandbox joined
- [ ] Account SID in `.env`
- [ ] Auth Token in `.env`
- [ ] WhatsApp number in `.env`
- [ ] ngrok running and URL in `.env`
- [ ] Backend running and connected
- [ ] WhatsApp message received
- [ ] Backend logs show message
- [ ] Kafka topic has message
- [ ] Database has message stored

---

## 📊 Multi-Channel Testing

Once WhatsApp is working:

1. **Test with Web Form**
   - See SETUP_WEBFORM.md
   - Submit form while WhatsApp running
   - Both should work independently

2. **Test with Gmail**
   - See SETUP_GMAIL.md
   - Send email + WhatsApp message
   - Both should be in system

3. **Test Cross-Channel**
   - Send all 3 channels:
     - Web form
     - Email
     - WhatsApp
   - All should have same ticket ID
   - Verify cross-channel continuity

---

## 🎯 Production Deployment

For production (beyond sandbox):

1. **WhatsApp Business Account**
   - Apply through: https://www.whatsapp.com/business/
   - Get approved by WhatsApp
   - Setup official business phone

2. **Update Credentials**
   - Get production Account SID
   - Get production Auth Token
   - Use your approved WhatsApp number

3. **Update Webhook**
   - Use your production domain
   - Update all URLs to use HTTPS
   - Test thoroughly before going live

4. **Remove Sandbox Mode**
   - Set `TWILIO_SANDBOX_MODE=false` in `.env`

---

## 📚 File Locations

**Backend WhatsApp Integration:**
- Config: `production/config/settings.py`
- Handler: `production/channels/whatsapp_handler.py`
- API: `production/api/main.py` (search for `/api/whatsapp/`)
- Signature validation: `production/api/main.py` (validate_twilio_signature)

**Environment:**
- `.env` - Twilio credentials
- `.env.example` - Template with placeholders

---

## 💡 Tips

- **Keep logs visible:** `tail -f logs/api.log` in separate terminal
- **Watch Kafka:** `kafka-console-consumer.sh` in separate terminal
- **Monitor ngrok:** Keep ngrok terminal visible
- **Test frequently:** Send test messages often
- **Check all three:** Logs, Kafka, Database
- **Document URL changes:** Note ngrok URL each time
- **Verify signature:** Turn off temporarily to test (for debugging only)

---

## 📞 Getting Help

**If stuck:**

1. Check backend logs:
   ```bash
   tail -f logs/api.log | grep -i whatsapp
   ```

2. Verify credentials:
   ```bash
   grep TWILIO .env
   ```

3. Test webhook:
   ```bash
   curl -X POST http://localhost:8000/api/whatsapp/webhook \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "From=whatsapp:%2B1234567890&Body=test"
   ```

4. Check Twilio Console for errors

5. Monitor ngrok for connection issues

---

## 🎉 Success!

You've successfully:
- ✅ Created Twilio account
- ✅ Joined WhatsApp sandbox
- ✅ Got API credentials
- ✅ Setup webhook
- ✅ Tested messages
- ✅ Verified Kafka integration

**Next:** Test all 3 channels together and run the complete system!

---

**Questions?** Check troubleshooting section or see `production/README.md` for more help.

*WhatsApp Setup Complete!* 💬🚀
