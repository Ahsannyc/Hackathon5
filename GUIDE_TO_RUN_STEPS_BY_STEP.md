# 🚀 GUIDE TO RUN STEPS BY STEP
**Hackathon5 Customer Success AI Project**

**Last Updated:** 2026-05-01  
**Status:** Ready to Run  
**Difficulty:** Beginner-Friendly ✅

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Step 1: Navigate to Project](#step-1-navigate-to-project)
3. [Step 2: Open PowerShell/Terminal](#step-2-open-powershellterminal)
4. [Step 3: Check Python Installation](#step-3-check-python-installation)
5. [Step 4: Install Dependencies](#step-4-install-dependencies)
6. [Step 5: Start the Server](#step-5-start-the-server)
7. [Step 6: Test the API](#step-6-test-the-api)
8. [Step 7: Run All Tests](#step-7-run-all-tests)
9. [Optional: Add PostgreSQL](#optional-add-postgresql)
10. [Optional: Add Real Gmail](#optional-add-real-gmail)
11. [Optional: Add Real WhatsApp](#optional-add-real-whatsapp)
12. [Troubleshooting](#troubleshooting)

---

## ✅ PREREQUISITES

Before starting, make sure you have:

- ✅ **Python 3.11+** installed
- ✅ **Git** installed (to clone/pull the project)
- ✅ **Project folder** at `C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5`
- ✅ **pip** (Python package manager - comes with Python)

**Check if you have Python:**
```bash
python --version
```

You should see: `Python 3.11.x` or higher

---

# 🎯 STEP-BY-STEP INSTRUCTIONS

## STEP 1: Navigate to Project

**What this does:** Changes your current folder to the Hackathon5 project directory

**Windows PowerShell:**
```bash
cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
```

**What you'll see:**
```
PS C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5>
```

✅ **Success:** The folder path shows `Hackathon5` at the end

---

## STEP 2: Open PowerShell/Terminal

**What this does:** Opens a command-line interface where you can run Python commands

**Windows:**
- Press: `Windows Key + X`
- Click: "Terminal" or "PowerShell"

Or:

- Right-click in the folder
- Select: "Open in Terminal" or "Open PowerShell here"

**You should see:**
```
PS C:\Users\...>
```

---

## STEP 3: Check Python Installation

**What this does:** Verifies Python is installed and working

**Run this command:**
```bash
python --version
```

**Expected output:**
```
Python 3.11.x (or 3.12.x or 3.13.x or 3.14.x)
```

**If you see an error:**
- Install Python from: https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Restart PowerShell after installation

✅ **Success:** Python version displays correctly

---

## STEP 4: Install Dependencies

**What this does:** Downloads and installs all required Python packages

**Run this command:**
```bash
pip install -r requirements.txt
```

**What you'll see:**
```
Collecting fastapi==0.115.6
Collecting uvicorn[standard]==0.32.1
...
Successfully installed fastapi-0.115.6 uvicorn-0.32.1 ...
```

**This will take 2-5 minutes** (first time only)

⚠️ **Note:** You might see warnings. **This is normal.** As long as you see "Successfully installed", you're good.

**After installation, verify:**
```bash
pip list | grep fastapi
```

**Expected output:**
```
fastapi                      0.115.6
```

✅ **Success:** Dependencies installed without errors

---

## STEP 5: Start the Server

**What this does:** Starts the Hackathon5 API server

**Run this command:**
```bash
python -m uvicorn production.api.main:app --port 8000
```

**What you'll see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**This means the server is RUNNING!** 🎉

✅ **Success:** Server started and waiting for requests

**To stop the server later:** Press `CTRL+C`

---

## STEP 6: Test the API

**What this does:** Sends a test request to the Web Form endpoint

**Open a NEW PowerShell window** (keep the server running in the first one)

**Navigate to the project again:**
```bash
cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
```

**Run this test command:**
```bash
curl -X POST http://localhost:8000/api/form/submit `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "customer_name=Alice&customer_email=alice@example.com&subject=Help&message=How do I integrate the API?"
```

**Expected response:**
```json
{
  "status": "responded",
  "ticket_id": "FORM-CUST-XXXXX",
  "customer_id": "CUST-XXXXX",
  "ai_response": "I understand you're asking about API integration...",
  "workflow_steps_completed": ["create_ticket", "get_history", "search_kb", "send_response"]
}
```

✅ **Success:** API responded with ticket ID and AI response

---

### ALTERNATIVE: Use Browser Instead of curl

**If curl doesn't work, use the interactive API docs:**

1. Open your browser
2. Go to: `http://127.0.0.1:8000/api/docs`
3. Find "POST /api/form/submit"
4. Click "Try it out"
5. Fill in the form:
   - customer_name: `Alice`
   - customer_email: `alice@example.com`
   - subject: `Help`
   - message: `How do I integrate the API?`
6. Click "Execute"
7. See the response below

✅ **Success:** API responded in browser

---

## STEP 7: Run All Tests

**What this does:** Runs the 24 automated tests to verify everything works

**In the NEW PowerShell window (where you tested the API):**

```bash
python -m pytest production/tests/test_multi_channel.py -v
```

**Wait for completion...**

**Expected output:**
```
======================== 14 passed in X.XXs ========================
```

**Then run the second test suite:**
```bash
python -m pytest production/tests/test_cross_channel_continuity.py -v
```

**Expected output:**
```
======================== 10 passed in X.XXs ========================
```

✅ **Success:** All 24 tests passing

---

## STEP 8: Verify Everything Works

**Check all 3 channels are working:**

**In the server window (Step 5), you should see:**
```
✓ Web form handler initialized
✓ Gmail handler integrated
✓ WhatsApp handler integrated
✓ All channels ready
```

**Channel statuses:**
- ✅ **Web Form:** Ready (no credentials needed)
- ✅ **Gmail:** Ready (simulation mode)
- ✅ **WhatsApp:** Ready (simulation mode)

---

# 🎉 YOU'RE DONE!

**The Hackathon5 project is now RUNNING!**

| What | Status | URL |
|------|--------|-----|
| **API Server** | ✅ Running | http://127.0.0.1:8000 |
| **API Docs** | ✅ Available | http://127.0.0.1:8000/api/docs |
| **Web Form** | ✅ Working | POST to /api/form/submit |
| **Tests** | ✅ Passing | 24/24 tests pass |
| **All Channels** | ✅ Ready | Web, Email, WhatsApp |

---

# 📚 OPTIONAL ADVANCED SETUPS

## OPTIONAL: Add PostgreSQL (5 minutes)

**For data persistence**

### Step 1: Install PostgreSQL

**Windows:**
```bash
winget install PostgreSQL.PostgreSQL
```

Or download from: https://www.postgresql.org/download/windows/

### Step 2: Create Database

**Open PostgreSQL command prompt or use PowerShell:**
```bash
psql -U postgres -c "CREATE DATABASE \"Hackhathon5\";"
```

**You'll be prompted for the PostgreSQL password** (set during installation)

### Step 3: Run Database Migrations

**In your Hackathon5 PowerShell window:**
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### Step 4: Restart Server

**Press CTRL+C to stop the server, then restart:**
```bash
python -m uvicorn production.api.main:app --port 8000
```

**Now the server will save data to PostgreSQL!**

✅ **Success:** Database persistence enabled

---

## OPTIONAL: Add Real Gmail (5 minutes)

**For real Gmail integration instead of simulation**

### Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com
2. Click "Create Project"
3. Name it: "Hackathon5"
4. Click "Create"

### Step 2: Enable Gmail API

1. In the search bar, type: "Gmail API"
2. Click on "Gmail API"
3. Click "ENABLE"

### Step 3: Create OAuth2 Credentials

1. Click "Create Credentials"
2. Choose: "OAuth client ID"
3. Choose: "Desktop application"
4. Click "Create"
5. Click "Download" (saves as `.json` file)

### Step 4: Place Credentials in Project

1. Rename the downloaded file to: `credentials.json`
2. Move it to: `C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\credentials.json`

### Step 5: Update .env File

**Open file:** `production/.env`

**Find this line:**
```
GMAIL_ENABLED=true
```

**Add below it:**
```
GMAIL_CREDENTIALS_PATH=credentials.json
```

**Save the file**

### Step 6: Restart Server

**Press CTRL+C to stop, then restart:**
```bash
python -m uvicorn production.api.main:app --port 8000
```

**First run:** Browser will open asking for permission
- Click "Allow"
- Gmail token will be cached automatically

✅ **Success:** Real Gmail integration active

---

## OPTIONAL: Add Real WhatsApp (10 minutes)

**For real WhatsApp integration via Twilio**

### Step 1: Get Twilio Account

1. Go to: https://www.twilio.com/
2. Sign up or log in
3. Create a project
4. Get your:
   - Account SID
   - Auth Token
   - WhatsApp Sandbox phone ID

### Step 2: Update .env File

**Open:** `production/.env`

**Add these lines:**
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_NUMBER=+1415xxxxxxx
WHATSAPP_BUSINESS_TOKEN=your_whatsapp_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=cloudflow-secret
WHATSAPP_ENABLED=true
```

**Replace with your actual credentials from Twilio**

### Step 3: Restart Server

```bash
# Press CTRL+C to stop
# Then restart:
python -m uvicorn production.api.main:app --port 8000
```

✅ **Success:** Real WhatsApp integration active

---

# 🆘 TROUBLESHOOTING

## Problem: "Command not found: python"

**Solution:**
```bash
# Try:
python3 --version

# Or reinstall Python from:
https://www.python.org/downloads/
# Check "Add Python to PATH"
```

---

## Problem: "Module not found: fastapi"

**Solution:**
```bash
# Reinstall dependencies:
pip install -r requirements.txt

# Or try:
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Problem: "Address already in use: 8000"

**Solution:**
```bash
# Kill the process using port 8000:
# Windows:
netstat -ano | findstr :8000

# Then stop that process and try again
```

---

## Problem: Server starts but API returns error

**Solution:**
1. Check all dependencies installed: `pip list`
2. Check the error message in the server window
3. Restart the server
4. If issue persists, check PostgreSQL is running (if you set it up)

---

## Problem: Tests fail

**Solution:**
```bash
# Reinstall dependencies:
pip install -r requirements.txt

# Run tests again:
python -m pytest production/tests/test_multi_channel.py -v
```

---

## Problem: "CORS error" or "Connection refused"

**Solution:**
1. Check server is running (you should see "Uvicorn running on...")
2. Check you're using correct URL: `http://127.0.0.1:8000` (not `localhost`)
3. Check no firewall is blocking port 8000

---

# 📞 QUICK REFERENCE

## Server Commands

**Start server:**
```bash
python -m uvicorn production.api.main:app --port 8000
```

**Stop server:**
```
Press CTRL+C
```

**Restart server:**
```
Press CTRL+C, then run start command again
```

---

## Test Commands

**Run multi-channel tests:**
```bash
python -m pytest production/tests/test_multi_channel.py -v
```

**Run continuity tests:**
```bash
python -m pytest production/tests/test_cross_channel_continuity.py -v
```

**Run all tests:**
```bash
python -m pytest production/tests/ -v
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/form/submit` | POST | Web form submission |
| `/api/gmail/webhook` | POST | Gmail webhook |
| `/api/whatsapp/webhook` | POST | WhatsApp webhook |
| `/api/docs` | GET | Interactive API documentation |

---

## Important Files

| File | Purpose |
|------|---------|
| `production/api/main.py` | Main API server |
| `production/.env` | Configuration (secrets) |
| `requirements.txt` | Python dependencies |
| `GUIDE_TO_RUN_STEPS_BY_STEP.md` | This guide |

---

# 🎓 LEARNING TIPS

1. **First run:** Just follow Steps 1-7 (about 15 minutes)
2. **After it works:** Try the optional setups if interested
3. **Read the logs:** The server output tells you what's happening
4. **Use the API docs:** Go to `http://127.0.0.1:8000/api/docs` to explore endpoints
5. **Check tests:** Tests show what the system can do

---

# ✅ FINAL CHECKLIST

After following all steps, you should have:

- ✅ Python installed
- ✅ Dependencies installed
- ✅ Server running on port 8000
- ✅ API responding to requests
- ✅ All 24 tests passing
- ✅ 3 channels working (Web Form, Gmail, WhatsApp)
- ✅ Access to API documentation at `/api/docs`

---

## 🚀 NEXT STEPS

After everything works:

1. **Explore the API:** Visit `http://127.0.0.1:8000/api/docs`
2. **Test more endpoints:** Try different form submissions
3. **Read the code:** Check `production/agent/` to see how it works
4. **Add real integrations:** Follow optional setup guides for Gmail/WhatsApp
5. **Run load tests:** When ready, execute the load test suite

---

## 📝 NOTES

- **Simulation mode:** All 3 channels work without any external credentials
- **Real mode:** Add credentials to use actual Gmail/WhatsApp
- **No database required:** Everything works without PostgreSQL (data in memory)
- **Graceful degradation:** Missing optional services don't break the system
- **24/7 ready:** The system can run continuously without issues

---

## 📞 SUPPORT

If you encounter issues:

1. **Check the logs:** Read what the server is printing
2. **Try restarting:** Many issues resolve with a restart
3. **Check dependencies:** Ensure all are installed: `pip list`
4. **Check ports:** Ensure port 8000 is available
5. **Check Python version:** Should be 3.11+

---

**Created:** 2026-05-01  
**Status:** Tested and Working ✅  
**Last Verified:** Server running, all tests passing

**Happy Hacking! 🚀**
