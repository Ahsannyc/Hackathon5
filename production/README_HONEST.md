# 🏭 Hackathon5: Honest Current Setup Guide

**Date:** 2026-04-30  
**Status:** Web Form channel working, other channels not yet configured  
**Environment:** Windows 11, Python 3.11, Node.js 20.x  
**Mode:** In-memory (PostgreSQL not running, Kafka gracefully degraded)

---

## ⚠️ REALITY CHECK: What's Actually Done

### ✅ WORKING RIGHT NOW

- **Web Form Submission:** Form fills out, submits to backend, returns ticket ID
- **Form Validation:** Email format, XSS prevention, required fields
- **Ticket ID Generation:** Unique IDs per submission
- **Health Checks:** `/health` and `/api/form/health` endpoints
- **API Documentation:** Swagger UI at `/api/docs`
- **Performance:** Submissions complete in <1s, health checks in <100ms

### ❌ NOT WORKING YET

- **PostgreSQL:** No data persistence (in-memory only, resets on restart)
- **Kafka:** Not running (graceful degradation works, but no queuing)
- **Gmail Integration:** No credentials configured
- **WhatsApp Integration:** No Twilio credentials
- **AI Agent Response:** Agent code exists but not called in form flow
- **Cross-Channel Continuity:** Only one channel works (Web Form)
- **Multi-Channel Testing:** Requires all 3 channels (have 1 of 3)

### 📊 PDF COMPLIANCE

| Exercise | Requirement | Status | Working |
|----------|-------------|--------|---------|
| 3.1 | Multi-channel E2E tests | 33% | Web form only |
| 3.2 | 24-hour load test (3 channels) | 25% | Can only test web form |

---

## 🚀 QUICK START (No Docker, No Database Needed)

### 1. Prerequisites (5 minutes)

```powershell
# Verify Python 3.11+
python --version

# Verify Node.js 20+
node --version

# Verify pip
pip --version
```

---

### 2. Activate Python Virtual Environment (2 minutes)

```powershell
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'

# Activate venv
.\venv\Scripts\Activate.ps1

# Verify activated (should show (venv) in prompt)
```

---

### 3. Start FastAPI Backend (Terminal 1)

```powershell
# Keep venv active from step 2

python -m uvicorn production.api.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Verify it's working:**
```powershell
# In another terminal/PowerShell window
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-30T10:30:00.000Z"
}
```

---

### 4. Start Next.js Frontend (Terminal 2)

```powershell
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\production\web-form'

npm run dev
```

**Expected output:**
```
> next-form@1.0.0 dev
> next dev

Local:        http://localhost:3000
```

---

### 5. Test the System (Terminal 3)

```powershell
# Test form submission
curl -X POST http://localhost:8000/api/form/submit `
  -F "customer_name=Test User" `
  -F "customer_email=test@example.com" `
  -F "subject=Testing the system" `
  -F "message=This is a test message for the form submission."

# Expected response (201 Created):
# {
#   "submission_id": "form_abc123xyz",
#   "status": "received",
#   "message": "Thank you for your submission. We'll respond shortly.",
#   "timestamp": "2026-04-30T10:30:00.000Z"
# }
```

---

## 📋 TESTING YOUR SYSTEM

### Option 1: Use the Web Form UI (Easiest)

```
1. Open browser: http://localhost:3000/web-form
2. Fill in all fields:
   - Name: Your Name
   - Email: your@email.com
   - Subject: Test subject (min 5 chars)
   - Message: Your message here (min 10 chars)
   - Priority: Select one (low/medium/high)
3. Click "Submit"
4. See "Thank you!" page with Ticket ID
```

**What happens:**
- ✅ Form validates on client side (email, required fields, XSS)
- ✅ Sends to `/api/form/submit` endpoint
- ✅ Backend validates again (secure)
- ✅ Ticket ID generated and returned
- ✅ Success page displays

**What does NOT happen:**
- ❌ No data saved to database (in-memory only)
- ❌ No message queued to Kafka
- ❌ No AI response generated
- ❌ No email sent

---

### Option 2: Automated Tests

```powershell
# Make sure you're in the project root
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'

# Activate venv if not already
.\venv\Scripts\Activate.ps1

# Install test dependencies
pip install pytest httpx

# Run the honest test suite (tests only what works)
pytest production/tests/test_current_setup.py -v

# Run specific category
pytest production/tests/test_current_setup.py::TestWebFormSubmission -v

# Run performance tests
pytest production/tests/test_current_setup.py::TestPerformance -v

# Run concurrent submission tests
pytest production/tests/test_current_setup.py::TestConcurrency -v
```

**Expected output:**
```
test_root_health_check PASSED
test_form_submission_basic PASSED
test_form_submission_with_all_fields PASSED
test_ticket_id_uniqueness PASSED
test_missing_required_field_name PASSED
...
test_gmail_integration_not_available SKIPPED
test_whatsapp_integration_not_available SKIPPED
test_database_persistence_not_available SKIPPED
...

====== 30 passed, 6 skipped ======
```

---

### Option 3: cURL Commands

**Test 1: Basic submission**
```powershell
curl -X POST http://localhost:8000/api/form/submit `
  -F "customer_name=Alice" `
  -F "customer_email=alice@example.com" `
  -F "subject=Help please" `
  -F "message=I need help with your product please."
```

**Test 2: With all fields**
```powershell
curl -X POST http://localhost:8000/api/form/submit `
  -F "customer_name=Bob Smith" `
  -F "customer_email=bob@company.com" `
  -F "subject=API integration question" `
  -F "message=How do I integrate your REST API with my Python backend?" `
  -F "priority=high" `
  -F "phone=+1-555-0123" `
  -F "company=Tech Corp"
```

**Test 3: Validation - missing email (should fail)**
```powershell
curl -X POST http://localhost:8000/api/form/submit `
  -F "customer_name=Charlie" `
  -F "subject=Missing email" `
  -F "message=This submission is missing the email field on purpose."
```
**Expected:** HTTP 422 (Validation Error)

**Test 4: XSS prevention (should fail)**
```powershell
curl -X POST http://localhost:8000/api/form/submit `
  -F "customer_name=David" `
  -F "customer_email=david@example.com" `
  -F "subject=Test <script>alert('xss')</script>" `
  -F "message=This subject has a script tag."
```
**Expected:** HTTP 422 (XSS detected)

---

## 📊 CURRENT SYSTEM STATUS

### Running Components

| Service | URL | Status | Notes |
|---------|-----|--------|-------|
| FastAPI Backend | http://localhost:8000 | ✅ Running | All 16+ endpoints available |
| Next.js Frontend | http://localhost:3000/web-form | ✅ Running | Form submission works |
| Health Check | http://localhost:8000/health | ✅ Running | Returns healthy |
| API Docs | http://localhost:8000/api/docs | ✅ Running | Interactive Swagger UI |

### Optional Components

| Service | Status | Notes |
|---------|--------|-------|
| PostgreSQL | ⏸️ Not Running | Data not persistent, resets on restart |
| Kafka | ⏸️ Not Running | Graceful degradation enabled |
| Gmail API | 🔴 Not Configured | Needs credentials.json |
| Twilio (WhatsApp) | 🔴 Not Configured | Needs account credentials |
| Cohere API | ✅ Configured | Key in .env, not called by form yet |

---

## 🔧 TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'production'"

**Fix:**
```powershell
# Make sure you're in the correct directory
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'

# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall if needed
pip install -e .
```

---

### Issue: "Port 8000 already in use"

**Fix:**
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID>)
taskkill /PID <PID> /F

# Or use a different port
python -m uvicorn production.api.main:app --reload --port 8001
```

---

### Issue: "Connection refused" when accessing localhost:3000

**Fix:**
```powershell
# Check if frontend is running
curl http://localhost:3000/web-form

# If not, start it:
cd production/web-form
npm run dev
```

---

### Issue: Form validation error (422) you didn't expect

**Possible causes:**
1. **Email invalid:** Must be valid format (user@domain.com)
2. **Subject too short:** Minimum 5 characters
3. **Message too short:** Minimum 10 characters
4. **XSS detected:** Script tags in subject or message
5. **Invalid priority:** Must be low, medium, high, or critical
6. **Missing required field:** Name, email, subject, message required

**Debug:**
```powershell
# Run validation tests to see what's expected
pytest production/tests/test_current_setup.py::TestFormValidation -v
```

---

### Issue: Cohere API key error

**Check:**
```powershell
# Verify key is set in .env
cat .env | findstr COHERE_KEY

# Should show something like:
# COHERE_KEY=U5kSpgfkUPzydnFLOC3W3Bw1...
```

---

## 📈 WHAT'S MISSING FOR PDF COMPLIANCE

### For Exercise 3.1 (Multi-Channel E2E Testing)

**Required:** All 3 channels must work and be tested
- ✅ Web Form: Working
- ❌ Gmail: Missing credentials
- ❌ WhatsApp: Missing Twilio account

**Current Progress:** 33% (1 of 3 channels)

**To Complete:**
1. Setup Gmail (see SETUP_GMAIL.md)
2. Setup WhatsApp (see SETUP_WHATSAPP.md)
3. Run comprehensive E2E tests with all channels

---

### For Exercise 3.2 (24-Hour Load Test)

**Required:** 24-hour test with all channels, 100+ web + 50+ email + 50+ WhatsApp + cross-channel

**Current Progress:** 25% (can only test web form)

**To Complete:**
1. Have all 3 channels working
2. Have database persistence
3. Run load test across all channels
4. Document cross-channel customer tracking

---

## 🎯 MINIMUM NEXT STEPS (No Docker)

### Step 1: Add Database (30 minutes)
```powershell
# Install PostgreSQL locally or use service
# Update .env: DATABASE_URL=postgresql://user:pass@localhost/cloudflow
# Restart backend
# Run migrations
```

**Impact:** Data now persists, enables cross-channel continuity

---

### Step 2: Wire AI Agent to Form (1-2 hours)

```powershell
# Edit production/api/main.py
# Add agent call to form submission endpoint
# Generate AI response for submission
# Return response in API
```

**Impact:** Form submission now gets AI response, not just "received"

---

### Step 3: Add Gmail Integration (1-2 hours)

```powershell
# Get credentials.json from Google Cloud
# Place in production/config/
# Restart backend
# Now email channel works
```

**Impact:** Email channel available (2 of 3 channels)

---

### Step 4: Add WhatsApp Integration (1-2 hours)

```powershell
# Get Twilio credentials
# Add to .env
# Restart backend
# Now WhatsApp channel works
```

**Impact:** SMS channel available (3 of 3 channels complete)

---

## 📊 REALISTIC TIMELINE

| Task | Effort | Impact | Blocking |
|------|--------|--------|----------|
| Database setup | 30 min | Medium | No (graceful degradation works) |
| AI agent wiring | 1-2 hrs | Medium | No (demo works without it) |
| Gmail setup | 1-2 hrs | High | Yes (needed for Exercise 3.1) |
| WhatsApp setup | 1-2 hrs | High | Yes (needed for Exercise 3.1) |
| Load test + 24hr plan | 3-4 hrs | High | Yes (needed for Exercise 3.2) |
| Documentation | 1-2 hrs | Low | No |

**Total Additional Effort for Full Compliance:** ~9-14 hours

---

## 📝 IMPORTANT: What to Submit

**For this current state:**
- ✅ Submit with `test_current_setup.py` (shows what works)
- ✅ Include `realistic-demo.md` (honest about limitations)
- ✅ Mention that 3 channels are coded but only 1 configured
- ✅ Document graceful degradation works perfectly
- ✅ Explain timeline to complete multi-channel

**What NOT to claim:**
- ❌ Don't claim multi-channel if only web form works
- ❌ Don't claim 24-hour test if you can't run it
- ❌ Don't claim data persistence if using in-memory
- ❌ Don't claim AI response integration if not wired

**Be honest about progress:** 30-40% complete with full functionality demonstrated in single channel.

---

## 🏁 QUICK REFERENCE

| What | Command | Port |
|------|---------|------|
| Start Backend | `python -m uvicorn production.api.main:app --reload --port 8000` | 8000 |
| Start Frontend | `npm run dev` (in `production/web-form`) | 3000 |
| Run Tests | `pytest production/tests/test_current_setup.py -v` | N/A |
| Health Check | `curl http://localhost:8000/health` | 8000 |
| API Docs | `http://localhost:8000/api/docs` | 8000 |
| Web Form | `http://localhost:3000/web-form` | 3000 |
| Stop Backend | `Ctrl+C` in terminal | N/A |
| Stop Frontend | `Ctrl+C` in terminal | N/A |

---

**Last Updated:** 2026-04-30  
**Status:** Realistic, honest, Windows-focused setup guide  
**Next:** Follow minimum steps to improve compliance score
