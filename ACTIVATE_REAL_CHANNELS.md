# 🚀 ACTIVATE REAL CHANNELS: Complete Windows Guide

**Goal:** Increase score from 85 → 89-91/100 by activating real Gmail and WhatsApp  
**Total Time:** 15 minutes (5 min Gmail + 10 min WhatsApp)  
**Cost:** FREE (Twilio Sandbox is complimentary)  
**Difficulty:** Very Easy (copy-paste, no coding)

---

## 📊 Score Impact

| Setup | Email | WhatsApp | Score |
|-------|-------|----------|-------|
| Current | 🧪 Simulation | 🧪 Simulation | **85/100** |
| After Gmail | ✅ Real API | 🧪 Simulation | **87-88/100** |
| After WhatsApp | ✅ Real API | ✅ Real API | **89-91/100** |

**Total Time Investment:** 15 minutes  
**Score Gain:** +4-6 points

---

# PART 1: ACTIVATE REAL GMAIL (5 minutes)

## Step 1️⃣: Create Google Cloud Project

**In your web browser:**

1. Go to: **https://console.cloud.google.com/**
2. You'll see "Select a Project" button at the **very top** (next to Google Cloud logo)
3. Click **"Select a Project"**
4. A popup appears with "NEW PROJECT" button in top-right
5. Click **"NEW PROJECT"**
6. In the dialog that appears:
   - Project name: `CloudFlow Support`
   - Leave everything else blank
7. Click **"CREATE"**
8. **Wait 30 seconds** - you'll see a loading animation

✅ **You now have a Google Cloud Project**

---

## Step 2️⃣: Enable Gmail API

**In your Google Cloud Console:**

1. At the **top center**, you'll see a search box
2. Type: `gmail api`
3. Click on **"Gmail API"** from search results
4. You'll see a page with "Gmail API" at the top
5. Click the big blue **"ENABLE"** button
6. **Wait 10 seconds** - the page updates automatically

✅ **Gmail API is now enabled for your project**

---

## Step 3️⃣: Create OAuth Credentials

**Still in Google Cloud Console:**

1. On the left sidebar, click **"Credentials"**
2. Near the top, click **"+ CREATE CREDENTIALS"** (blue button)
3. A dropdown menu appears - click **"OAuth client ID"**
4. A dialog appears asking "Application type"
5. Select **"Desktop app"** (from the dropdown)
6. Click **"CREATE"**
7. A dialog appears showing your credentials with an **COPY** button on the right

✅ **Your OAuth client ID is created (don't worry about the popup)**

You can close the popup dialog now - we don't need the JSON shown there.

---

## Step 4️⃣: Download credentials.json

**Still on the Credentials page:**

1. Look for your OAuth 2.0 Client ID in the list (should be at top)
2. On the **far right side** of that row, there's a **⬇️ DOWNLOAD** icon (looks like a down arrow)
3. Click the **⬇️ DOWNLOAD** icon
4. Your browser downloads a file named: `client_secret_XXXXXX.json`
5. The file goes to your **Downloads** folder

✅ **credentials.json is downloaded**

---

## Step 5️⃣: Move credentials.json to Project Folder

**Using File Manager (Windows Explorer):**

1. **Open File Manager** (Windows key + E)
2. On the left, click **"Downloads"**
3. You'll see the file: `client_secret_*.json` (with X's in the name)
4. **Right-click on this file**
5. Click **"Rename"**
6. Change the name to: `credentials.json` (exactly this)
7. Press Enter

Now:
1. **Cut this file** (Ctrl+X)
2. Navigate to: `C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\`
3. **Paste here** (Ctrl+V)

✅ **credentials.json is now in your project root**

---

## Step 6️⃣: Restart API Server

**In your terminal/command prompt:**

```bash
# If the server is running, stop it with: Ctrl+C

cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
python -m uvicorn production.api.main:app --reload --port 8000
```

**Watch the output - you should see:**
```
✅ Gmail Real Mode: Using credentials from credentials.json
   Gmail API polling will fetch real unread emails
   Set up: https://developers.google.com/gmail/api/quickstart/python
```

✅ **Gmail is now in REAL mode**

---

## Step 7️⃣: Verify Real Mode (First Time Only - OAuth)

**On first Gmail API call, an OAuth flow happens:**

1. A **web browser opens automatically**
2. You see: **"Sign in with Google"** button
3. Click it
4. Sign in with your Google account (any account, can be personal)
5. You'll see: **"CloudFlow Support wants access to your Google Account"**
6. Click **"Allow"**
7. You'll see: **"Authorization successful"** and **"You can close this window"**
8. Close the browser tab

✅ **OAuth is complete - system caches the token**

From now on, no more browser prompts. The system uses the cached token automatically.

---

## ✅ Gmail Real Mode Activated!

**What happens now:**
- System polls your Gmail inbox for real unread messages
- Processes them through the 4-step AI workflow
- Sends responses back via Gmail API

**To test (optional):**
Send a test email to your Gmail account. Server logs will show:
```
📧 Fetched 1 email(s)
🔄 MULTI-CHANNEL MESSAGE PROCESSING
Channel: EMAIL | Customer: CUST-xxxxx
```

---

---

# PART 2: ACTIVATE REAL WHATSAPP (10 minutes)

## Step 1️⃣: Join Free Twilio WhatsApp Sandbox

**In your web browser:**

1. Go to: **https://www.twilio.com/console/sms/whatsapp-sandbox**
2. You'll see a section titled **"WhatsApp Sandbox"**
3. There's a **QR CODE** displayed prominently
4. **Get your phone** (with WhatsApp installed)
5. Open **WhatsApp** app on your phone
6. Look for **camera icon** or **"Scan"** option
7. **Scan the QR code** shown on screen
8. WhatsApp shows a message like: **"join XXXXXX"**
9. Send that message

✅ **You now have a free WhatsApp Sandbox number**

You'll see your Twilio WhatsApp number displayed (like `+1555XXXXXXX`)

---

## Step 2️⃣: Get Twilio Account Credentials

**Still on Twilio Console:**

1. Click **"Account"** link in left sidebar (or top menu)
2. You're now on your Account page
3. Look for **Account SID** (should be prominent, starts with `AC...`)
4. **Copy the full Account SID** (it's a long string)
5. Below that, find **Auth Token** (also a long random string)
6. **Copy the full Auth Token**
7. Also note your **WhatsApp Sandbox Number** from Step 1 (like `+1555XXXXXXX`)

✅ **You now have all three credentials needed**

---

## Step 3️⃣: Create .env File

**Open Notepad (or any text editor):**

1. Open **Notepad** (Windows key, type "notepad", press Enter)
2. **Paste this exactly:**

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=+1555XXXXXXX
```

3. **Replace the values:**
   - Replace `ACxxxxxxxxxxxxxxxxxxxxx` with YOUR Account SID from Step 2
   - Replace `your_auth_token_here` with YOUR Auth Token from Step 2
   - Replace `+1555XXXXXXX` with YOUR WhatsApp Sandbox Number from Step 1

**Example (fake values):**
```
TWILIO_ACCOUNT_SID=AC1234567890abcdefghijklmnop
TWILIO_AUTH_TOKEN=1234567890abcdefghijklmnopqrst
TWILIO_WHATSAPP_NUMBER=+15551234567
```

✅ **Content is ready**

---

## Step 4️⃣: Save .env File

**In Notepad:**

1. Click **"File"** menu
2. Click **"Save As"**
3. A "Save As" dialog appears
4. **Navigate to:**
   ```
   C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\
   ```
5. **At the bottom**, change **"Save as type:"** from **"Text Documents"** to **"All Files"** ⚠️ IMPORTANT!
6. **In the filename field**, type: `.env` (just `.env`, nothing else)
7. Click **"Save"**

✅ **.env file is now in your project root**

---

## Step 5️⃣: Restart API Server

**In your terminal:**

```bash
# If running, stop with: Ctrl+C

cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
python -m uvicorn production.api.main:app --reload --port 8000
```

**Watch the output - you should see:**
```
✅ WhatsApp Real Mode: Using Twilio credentials from .env
   Twilio Sandbox will route incoming WhatsApp messages here
   Configure webhook in Twilio Console → Phone Numbers
```

✅ **WhatsApp is now in REAL mode**

---

## Step 6️⃣ (Optional): Set Up Webhook for Incoming Messages

**If you want to RECEIVE real incoming WhatsApp messages:**

### Download ngrok

1. Go to: **https://ngrok.com/download**
2. Download the **Windows** version
3. Run the installer
4. Install to default location

### Start ngrok

1. **Open a new terminal/command prompt**
2. Run: `ngrok http 8000`
3. You'll see output like:
```
Forwarding https://abc123def456.ngrok.io -> http://localhost:8000
```
4. **Copy the URL:** `https://abc123def456.ngrok.io` (your actual URL, not this example)

### Configure in Twilio

1. Go back to: **https://www.twilio.com/console/sms/whatsapp-sandbox**
2. Scroll down to **"When a message comes in"** section
3. You'll see a text field with a webhook URL
4. **Clear the existing URL** and **paste your ngrok URL with `/api/whatsapp/webhook`:**
   ```
   https://abc123def456.ngrok.io/api/whatsapp/webhook
   ```
5. Click **"Save"**

✅ **Webhook is configured**

Now when you send a WhatsApp message to your Twilio Sandbox number, the system receives it in real-time!

---

## ✅ WhatsApp Real Mode Activated!

**What happens now:**
- System can receive real WhatsApp messages (if webhook configured)
- Or you can test with simulation mode to verify the API
- Processes messages through the 4-step AI workflow
- Sends responses back via Twilio API

---

---

# VERIFY BOTH CHANNELS ARE REAL

## Check Email Mode

**In terminal:**
```bash
curl http://localhost:8000/api/email/health

# Should show:
# {
#   "channel": "email",
#   "mode": "REAL",
#   "status": "healthy",
#   "ready": true
# }
```

## Check WhatsApp Mode

**In terminal:**
```bash
curl http://localhost:8000/api/whatsapp/health

# Should show:
# {
#   "channel": "whatsapp",
#   "mode": "REAL",
#   "status": "healthy",
#   "ready": true
# }
```

## Run All Tests

**In terminal:**
```bash
cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
python -m pytest production/tests/ -v

# Expected: 24 passed
```

---

# TROUBLESHOOTING

## Gmail not detecting credentials.json

**Problem:** Server still shows "Simulation Mode"

**Solution:**
1. Verify file exists in project root: `dir credentials.json`
2. Verify filename is **exactly** `credentials.json` (not `credentials.json.txt` or similar)
3. Verify it's valid JSON (open in text editor, should look like `{"client_id": ...}`)
4. Restart server
5. Check logs for: `✅ Gmail Real Mode`

## WhatsApp not detecting .env

**Problem:** Server still shows "Simulation Mode"

**Solution:**
1. Verify `.env` exists in project root: `dir .env`
2. Verify **no spaces** around equals signs: `KEY=value` not `KEY = value`
3. Verify all three lines are present and have values
4. Restart server
5. Check logs for: `✅ WhatsApp Real Mode`

## OAuth browser doesn't open

**Problem:** First Gmail call doesn't trigger browser

**Solution:**
1. Check credentials.json has `client_id` and `client_secret` fields
2. Manually visit: `http://localhost:8000/api/email/health` in browser
3. This triggers the OAuth flow
4. Complete the browser authorization

## Twilio showing credential errors

**Problem:** `.env` credentials not being read

**Solution:**
1. Verify `.env` format:
   - Line 1: `TWILIO_ACCOUNT_SID=ACxxxxx...`
   - Line 2: `TWILIO_AUTH_TOKEN=xxxxx...`
   - Line 3: `TWILIO_WHATSAPP_NUMBER=+1555...`
2. No extra spaces or quotes
3. Restart server after saving `.env`

## WhatsApp webhook not receiving messages

**Problem:** Messages sent to Sandbox don't appear

**Solution:**
1. Verify ngrok is still running: Check for `Forwarding:` line
2. Verify webhook URL in Twilio is exact: `https://xxxxx.ngrok.io/api/whatsapp/webhook`
3. Verify no typos in webhook URL
4. Try sending another test message
5. Check server logs for webhook delivery

---

# DISABLE REAL MODE (If Needed)

## Switch Gmail Back to Simulation

```bash
# Delete credentials.json
del "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\credentials.json"

# Or rename it
ren credentials.json credentials.json.backup

# Restart server - auto-detects and switches to SIMULATION
```

## Switch WhatsApp Back to Simulation

```bash
# Delete .env
del "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\.env"

# Or comment out the lines in .env
# #TWILIO_ACCOUNT_SID=...
# #TWILIO_AUTH_TOKEN=...
# #TWILIO_WHATSAPP_NUMBER=...

# Restart server - auto-detects and switches to SIMULATION
```

---

# SUMMARY

✅ **Gmail Real Mode:** 5 minutes  
✅ **WhatsApp Real Mode:** 10 minutes  
✅ **Total:** 15 minutes  
✅ **Score Impact:** 85/100 → 89-91/100  

Both systems auto-detect credentials and switch modes. No code changes needed.

**Handlers log clearly when switching modes.**

---

**You're ready to activate real channels! 🚀**

