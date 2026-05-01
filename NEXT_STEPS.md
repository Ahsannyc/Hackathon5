# Next Steps - PostgreSQL + External Services Setup

**Status**: All code integrations complete ✅  
**Missing**: PostgreSQL database + external service credentials

---

## What's Complete

✅ **Kafka**: aiokafka installed and configured (Python 3.14 compatible)  
✅ **WhatsApp**: Handler fixed, ready for credentials  
✅ **Gmail**: Handler implemented, ready for OAuth2 credentials  
✅ **Database**: SQLAlchemy async engine ready (waiting for PostgreSQL)  
✅ **asyncpg**: Installed (async PostgreSQL driver)  
✅ **requirements.txt**: Updated with all dependencies  

---

## What You Need to Do (Choose One Path)

### Path A: Docker PostgreSQL (Easiest - 5 minutes)

**Prerequisite**: Install Docker Desktop from https://www.docker.com/products/docker-desktop

Then run this PowerShell command:

```powershell
docker run -d `
  --name hackathon5-postgres `
  -e POSTGRES_PASSWORD=1Funnylol! `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_DB=Hackhathon5 `
  -p 5432:5432 `
  postgres:17-alpine
```

Then skip to **Step: Initialize Alembic** below.

---

### Path B: Native PostgreSQL (More Complex - 15 minutes)

See detailed instructions in: `SETUP_POSTGRESQL.md`

---

## Initialize Alembic (After PostgreSQL is Running)

Once your database is up (Docker or native), run:

```powershell
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'
.\venv\Scripts\Activate.ps1

# Initialize Alembic
alembic init alembic
```

### Edit alembic/env.py

Around **line 18**, change:
```python
target_metadata = None
```

To:
```python
from production.database.models import Base
target_metadata = Base.metadata
```

### Create and Run Migration

```powershell
alembic revision --autogenerate -m "initial: create all tables"
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, initial: create all tables
```

---

## Test Database Connection

```powershell
# While in project directory with venv activated
python -c "from production.database.db import AsyncSessionLocal; print('Database connected')"
```

---

## Optional: Wire Database to Form Submission

To save web form submissions to the database, edit:  
`production/channels/web_form_handler.py`

Find the `submit_form()` function and add database save logic (see SETUP_POSTGRESQL.md for code example).

---

## Next External Services (Optional)

Once database is working:

### WhatsApp (with Twilio credentials you have)
Add to `.env`:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_NUMBER=+1415xxxxxxx
WHATSAPP_WEBHOOK_VERIFY_TOKEN=cloudflow-secret
WHATSAPP_ENABLED=true
```

Then expose local server with ngrok:
```powershell
# In new PowerShell window
ngrok http 8000
# Copy the URL and set it in Twilio Console webhook
```

### Gmail (requires Google Cloud setup)
1. Go to https://console.cloud.google.com
2. Create project → Enable Gmail API
3. Create OAuth2 credentials (Desktop app) → Download as JSON
4. Place `credentials.json` in project root
5. Add to `.env`:
```
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=credentials.json
```

### Kafka (optional - for async processing)
```powershell
docker run -d --name kafka -p 9092:9092 apache/kafka:latest
```

---

## Test Everything Together

```powershell
# Terminal 1: Backend
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'
.\venv\Scripts\Activate.ps1
python -m uvicorn production.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\production\web-form'
npm run dev
```

Then:
1. Open http://localhost:3000/web-form
2. Submit form
3. Check terminal 1 for success message
4. (If using database) Query database to verify record was saved

---

## Recommendation

**Start with Docker PostgreSQL** - it's the fastest path to a working system.

1. Install Docker Desktop (one-time setup)
2. Run the docker command above
3. Run Alembic migrations
4. Test form submission with database
5. Add credentials for WhatsApp/Gmail as needed

Total time: ~20 minutes

See `SETUP_POSTGRESQL.md` for detailed troubleshooting if you hit issues.
