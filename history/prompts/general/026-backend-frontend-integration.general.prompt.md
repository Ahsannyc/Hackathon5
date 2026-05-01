---
id: 026
title: Backend-Frontend Integration & Form Submission
stage: green
date: 2026-04-26
surface: agent
model: claude-haiku-4-5-20251001
feature: none
branch: 1-fastapi-backend
user: Ahsan Farooqui
command: Form submission integration and debugging
labels: ["fastapi", "next.js", "python3.14", "form-submission", "api-integration"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_modified:
  - requirements.txt (updated for Python 3.14 compatibility)
  - production/database/schema.py (regex -> pattern deprecation fix)
  - production/channels/web_form_handler.py (regex -> pattern fix)
  - production/api/main.py (regex -> pattern fix, error handling for handlers)
  - production/kafka_client.py (optional Kafka import with graceful degradation)
  - production/web-form/app/web-form/SupportForm.tsx (fixed endpoint URL and FormData format)
tests_run:
  - Health check endpoint: /health returns 200 with service status
  - Form submission endpoint: POST /api/form/submit accepts form data
  - Web form loads at http://localhost:3000/web-form
  - End-to-end form submission: success page with ticket ID generated
---

## Prompt

User wanted to get the FastAPI backend and Next.js web form running together with form submission working. Issues encountered:
1. Python 3.14 incompatibility with original package versions
2. Pydantic deprecation (regex -> pattern)
3. Kafka import errors (not critical, made optional)
4. Abstract handler classes failing to instantiate
5. Frontend posting to wrong endpoint with wrong format

User needed step-by-step PowerShell instructions to:
- Activate venv and start backend on port 8000
- Start Next.js dev server on port 3000
- Test form submission
- Debug endpoint mismatch

## Response

1. **Python 3.14 Compatibility Fix**
   - Updated requirements.txt to use pre-built wheel compatible versions
   - fastapi 0.115.6, uvicorn 0.32.1, pydantic 2.13.3, psycopg2-binary 2.9.12
   - Installed with --only-binary to avoid compilation issues

2. **Pydantic Deprecation Fixes**
   - Replaced `regex=` with `pattern=` in 4 locations:
     - production/database/schema.py line 365
     - production/channels/web_form_handler.py
     - production/api/main.py (2 instances)

3. **Kafka Graceful Degradation**
   - Made kafka import optional in production/kafka_client.py
   - App starts even if Kafka unavailable
   - Warnings logged but not fatal

4. **Handler Error Handling**
   - Added try/except around WhatsAppHandler instantiation
   - Added try/except around GmailHandler instantiation
   - Prevents abstract class errors from blocking startup

5. **Frontend Integration Fix**
   - Changed endpoint from `/api/messages/submit` to `http://localhost:8000/api/form/submit`
   - Changed from JSON to FormData format (required by backend)
   - Fixed field name: `email` → `customer_email`
   - Updated response handler to accept `submission_id` from backend

6. **PowerShell Instructions**
   - Provided clear terminal commands for Windows PowerShell
   - Separate terminals for backend, frontend, testing
   - Step-by-step form submission test

## Outcome

✅ **Success**: End-to-end form submission working
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000/web-form
- Form submission generates ticket ID: form_b231f66b6500
- Success page displays confirmation to user
- Data flows correctly from form → backend → response

**Key Files Modified**: 6 files
**Dependencies Updated**: 24 packages for Python 3.14
**Integration Status**: Fully working

## Next Steps

1. Set up database persistence for submissions
2. Implement email notifications
3. Set up Kafka for async message processing
4. Implement Gmail and WhatsApp integrations
