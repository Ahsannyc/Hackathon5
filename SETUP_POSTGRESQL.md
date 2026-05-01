# PostgreSQL Setup Guide for Hackathon5

This guide covers setting up PostgreSQL for the CloudFlow backend with the Hackathon5 database.

## Option A: Use Docker (Recommended - Simpler)

### Step 1: Install Docker Desktop

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Run the installer and follow the setup wizard
3. Restart your computer when prompted
4. Verify installation:
   ```powershell
   docker --version
   ```

### Step 2: Start PostgreSQL Container

After Docker is installed, run this command in PowerShell:

```powershell
docker run -d `
  --name hackathon5-postgres `
  -e POSTGRES_PASSWORD=1Funnylol! `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_DB=Hackhathon5 `
  -p 5432:5432 `
  postgres:17-alpine
```

### Step 3: Verify Connection

```powershell
# Wait 10 seconds for database to start
Start-Sleep -Seconds 10

# Test connection
docker exec hackathon5-postgres psql -U postgres -d Hackhathon5 -c "SELECT 1"
```

Expected output: `1` (shows database is ready)

---

## Option B: Native PostgreSQL Installation (More Complex)

### Step 1: Download PostgreSQL Installer

1. Go to https://www.postgresql.org/download/windows/
2. Download **PostgreSQL 17.x** (the latest version)
3. Run the installer

### Step 2: Run PostgreSQL Installer

During installation, when prompted:

- **Installation Directory**: Accept default (C:\Program Files\PostgreSQL\17)
- **Port**: Leave as 5432
- **Superuser Password**: Enter `1Funnylol!` (matches .env)
- **Service**: Check "Install as a service" (recommended)
- **Add to PATH**: Check this box

### Step 3: Create Database

After installation, open PowerShell and run:

```powershell
# Find psql location
$psqlPath = "C:\Program Files\PostgreSQL\17\bin\psql.exe"

# Create database
& $psqlPath -U postgres -c "CREATE DATABASE \"Hackhathon5\";"
```

When prompted for password, enter: `1Funnylol!`

### Step 4: Verify Connection

```powershell
& $psqlPath -U postgres -d Hackhathon5 -c "SELECT 1"
```

Expected output: `1` (shows database is ready)

---

## Step 4: Initialize Alembic Migrations (Both Options)

Once database is running (either Docker or native), proceed with this:

### 4A: Install Alembic

```powershell
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'
.\venv\Scripts\Activate.ps1
pip install alembic
```

### 4B: Initialize Alembic

```powershell
alembic init alembic
```

This creates `alembic/` directory with configuration files.

### 4C: Configure alembic/env.py

Edit `alembic/env.py` and make these changes:

**Around line 15-20, change from:**
```python
# import your models here for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None
```

**To:**
```python
# Import SQLAlchemy Base from production models
from production.database.models import Base
target_metadata = Base.metadata
```

**Around line 60, change from:**
```python
with connectable.connect() as connection:
```

**To:**
```python
import asyncio
from sqlalchemy import pool

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    from production.config.settings import settings
    
    # Replace postgresql:// with postgresql+asyncpg://
    database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    context.configure(
        url=database_url.replace("+asyncpg", ""),  # Use sync URL for migrations
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    from production.config.settings import settings
    from sqlalchemy import create_engine
    
    database_url = settings.database_url.replace("postgresql://", "postgresql://")
    connectable = create_engine(database_url, poolclass=pool.StaticPool)
    
    with connectable.connect() as connection:
        do_run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
```

### 4D: Create Initial Migration

```powershell
alembic revision --autogenerate -m "initial: create all tables"
```

Check `alembic/versions/` - should see a new file like `xxxxx_initial_create_all_tables.py`

### 4E: Run Migration

```powershell
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl()
INFO  [alembic.runtime.sqlalchemy.dialect] set isolation_level synchronous COMMIT
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, initial: create all tables
```

### Step 5: Verify Database Tables

```powershell
# Connect to database and list tables
$psqlPath = "C:\Program Files\PostgreSQL\17\bin\psql.exe"  # If native install
# OR use: docker exec hackathon5-postgres psql -U postgres -d Hackhathon5 (if Docker)

& $psqlPath -U postgres -d Hackhathon5 -c "\dt"
```

Expected tables:
```
customer
conversation
conversation_message
ticket
escalation
knowledge_base
sentiment_trend
response_template
audit_log
```

---

## Step 6: Update Web Form Handler (Optional - Better UX)

**File**: `production/channels/web_form_handler.py`

Find the `submit_form` function (around line 120) and after building the `WebFormMessage`, add database persistence:

```python
from production.database.db import AsyncSessionLocal
from production.database import queries

# ... existing code ...

async def submit_form(form_data: FormSubmissionRequest) -> FormSubmissionResponse:
    # ... existing code to build WebFormMessage ...
    
    # Save to database (NEW)
    try:
        async with AsyncSessionLocal() as session:
            # Get or create customer
            customer = await queries.get_or_create_customer(
                session,
                email=form_data.email,
                name=form_data.customer_name
            )
            
            # Create ticket
            ticket = await queries.create_ticket(
                session,
                customer_id=customer.id,
                subject=form_data.subject,
                description=form_data.message,
                priority=form_data.priority.value,
                channel="web_form",
                category=form_data.category
            )
            
            await session.commit()
            
            logger.info(f"Saved ticket {ticket.id} for customer {customer.id}")
            
            return FormSubmissionResponse(
                success=True,
                ticket_id=str(ticket.id),
                message="Thank you! Your request has been received."
            )
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        # Fallback to UUID if DB fails
        return FormSubmissionResponse(
            success=True,
            ticket_id=str(submission_id),
            message="Thank you! Your request has been received."
        )
```

---

## Troubleshooting

### Connection Refused Error
```
psql: error: could not translate host name "localhost" to address: No such host or server is known
```
**Fix**: 
- Docker: Check container is running: `docker ps`
- Native: Check PostgreSQL service is running: `services.msc`

### Authentication Failed
```
psql: error: FATAL: password authentication failed for user "postgres"
```
**Fix**: Verify password is `1Funnylol!` (matches .env DATABASE_URL)

### Port Already in Use
```
ERROR: bind() failed: Address already in use
```
**Fix**: 
- Docker: `docker rm -f hackathon5-postgres` then restart
- Native: Kill existing postgres: `taskkill /IM postgres.exe /F`

### Alembic Can't Find Models
```
ModuleNotFoundError: No module named 'production'
```
**Fix**: Ensure you're in project root and venv is activated:
```powershell
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'
.\venv\Scripts\Activate.ps1
```

---

## Quick Test After Setup

```powershell
# 1. Activate virtual environment
cd 'C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5'
.\venv\Scripts\Activate.ps1

# 2. Start backend
python -m uvicorn production.api.main:app --reload

# 3. Test health endpoint
curl http://localhost:8000/health

# 4. Check database status
# Should show: "database": "connected"
```

---

## Which Option Should You Choose?

**Use Docker if:**
- You want the easiest setup (one command)
- You plan to run multiple services (Kafka, PostgreSQL)
- You want isolation from your system
- You want to reset easily (`docker rm -f ...`)

**Use Native PostgreSQL if:**
- You prefer traditional database on your machine
- You want GUI tools (pgAdmin)
- You want better Windows integration

**Recommendation**: Start with Docker (simpler), then switch to native if needed.

---

**Status**: After completing these steps, you'll have:
✅ PostgreSQL database (Hackhathon5)
✅ Alembic migrations initialized
✅ 9 database tables created
✅ Web form handler integrated with database

Next: Start backend and test form submission → database persistence
