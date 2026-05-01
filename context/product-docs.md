# ProjectFlow - Product Documentation

## Core Features

### 1. Projects & Workspaces
Organize work into discrete projects with team collaboration

- Drag-and-drop project creation
- Unlimited projects (Pro) / 2 projects (Free)
- Role-based access: Admin, Manager, Member, Viewer
- Archive completed projects for historical reference
- Real-time collaboration updates

### 2. Tasks & Subtasks
Break down work into manageable units

- Create tasks and subtasks (unlimited depth)
- Set task dependencies (task A must finish before task B)
- Assign to team members with due dates
- Custom status workflow (Open, In Progress, Review, Done)
- Task priorities and labels for organization

### 3. Team Collaboration
Keep everyone in sync

- Comments on tasks and projects
- @Mentions to notify specific team members
- File attachments (images, docs, PDFs - max 500MB each)
- Real-time activity feed for project visibility
- Email notifications for updates (can be customized)

### 4. Automation & Workflows
Set it and forget it

- Simple workflow rules (If X, then Y)
- Recurring task creation on schedule
- Auto-assign based on conditions
- Status transition notifications
- Approval workflows for critical tasks

### 5. Reports & Insights
Measure progress and performance

- Project health dashboard (% complete, timeline status)
- Team performance metrics (velocity, burndown charts)
- Execution logs and audit trail
- Export reports as PDF/CSV
- Custom dashboards (Pro+ feature)

### 6. Integrations
Connect to your existing tools

- **Native:** Slack, Outlook, Gmail
- **OAuth:** Google Drive, OneDrive, Dropbox
- **Webhooks:** Custom integrations via REST API
- **Zapier:** Connect to 1000+ apps automatically

### 7. Access & Permissions
Fine-grained control

- Workspace-level roles (Admin, Manager, Member, Viewer)
- Project-level role overrides
- Guest access for external collaborators (read-only)
- SSO/SAML 2.0 (Enterprise only)

## Common User Actions

### Getting Started
1. Create account → Verify email
2. Complete onboarding wizard
3. Choose template or build from scratch
4. Create first project
5. Invite team members
6. Configure Slack/Gmail integrations (optional)
7. Activate project

### Managing Tasks
1. Create task with title and description
2. Assign to team member
3. Set due date and priority
4. Add subtasks for breakdown
5. Link dependencies (if workflow-dependent)
6. Update status as work progresses
7. Leave comments for collaboration

### Billing & Account
1. Upgrade/downgrade plans → Settings → Billing
2. View invoices → Billing → History
3. Update payment method → Billing → Payment Method
4. Add/remove team seats → Settings → Members
5. Cancel subscription (access retained until period end)

### Integration Setup
1. Go to Settings → Integrations
2. Click "Connect" on desired app
3. Authorize access (OAuth flow)
4. Configure notifications/rules
5. Test integration with sample data

## Troubleshooting Common Issues

### Task Not Updating or Syncing
- **Check:** Is the browser tab open? Refresh (Ctrl+R)
- **Check:** Does the task have dependencies blocking it? Review linked tasks
- **Check:** Do you have edit permissions? Ask workspace admin
- **Solution:** Clear browser cache, log out and back in
- **Escalate if:** Error persists after refresh + cache clear

### Can't See Projects or Permissions Denied
- **Check:** Are you in the right workspace?
- **Check:** What's your role? (Ask admin to verify)
- **Check:** Is the project archived? (Archived projects visible to admins only)
- **Solution:** Contact workspace admin for access
- **Escalate if:** Admin confirms you have role but still can't access

### Slack Integration Not Sending Notifications
- **Check:** Did you authorize Slack? (Settings → Integrations → Slack)
- **Check:** Is the notification rule configured? (Settings → Notifications)
- **Check:** Did you select a Slack channel? (Some tasks don't trigger by default)
- **Solution:** Re-authenticate Slack (disconnect, then reconnect)
- **Solution:** Verify Slack workspace permissions allow ProjectFlow
- **Escalate if:** Error persists after re-authentication

### Files Not Appearing in Task
- **Check:** Was file upload successful? (Check for upload progress indicator)
- **Check:** Is file size under 500MB limit?
- **Check:** Do you have attachment permissions? (Ask admin)
- **Solution:** Try again with smaller file or different format
- **Solution:** Clear browser cache and retry
- **Escalate if:** Consistently fails on multiple files

### Accidentally Deleted Task or Project
- **Recovery window:** 30 days in Trash (go to project → Trash tab)
- **Restore:** Click task/project → Restore
- **Permanent deletion:** Older than 30 days? Contact support
- **Escalate if:** Need recovery beyond 30 days

### Rate Limiting or API Errors
- **Check:** API rate limit is 1,000 requests/hour
- **Check:** Webhook response time (must be <30s)
- **Solution:** Implement exponential backoff in your code
- **Solution:** Batch requests instead of individual calls
- **Escalate if:** Need higher rate limit (enterprise option)

## Billing & Plans

### Free Plan
- Up to 2 projects
- 5 team members
- Basic task management
- Email/Slack integration
- Community support

### Pro Plan ($50/month per workspace)
- Unlimited projects
- 50+ team members
- Advanced automations
- Custom workflows
- Priority email support
- Zapier integration

### Enterprise (Custom pricing)
- Unlimited everything
- SSO/SAML authentication
- Dedicated account manager
- 24/7 phone support
- Custom integrations
- SLA guarantees

## API Reference (Key Endpoints)

### Authentication
```
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh-token
```

### Projects
```
GET    /api/v1/projects              # List projects
POST   /api/v1/projects              # Create project
GET    /api/v1/projects/{id}         # Get project details
PUT    /api/v1/projects/{id}         # Update project
DELETE /api/v1/projects/{id}         # Archive project
```

### Tasks
```
GET    /api/v1/projects/{id}/tasks              # List tasks
POST   /api/v1/projects/{id}/tasks              # Create task
GET    /api/v1/tasks/{id}                       # Get task details
PUT    /api/v1/tasks/{id}                       # Update task
DELETE /api/v1/tasks/{id}                       # Delete task
POST   /api/v1/tasks/{id}/comments              # Add comment
```

### Webhooks
```
POST /api/v1/webhooks                # Register webhook
GET  /api/v1/webhooks/{id}          # Get webhook details
DELETE /api/v1/webhooks/{id}        # Delete webhook

Supported events:
- task.created
- task.updated
- task.completed
- project.created
- comment.added
```

### Rate Limits
- **Default:** 1,000 requests/hour per API key
- **Headers:** X-RateLimit-Remaining, X-RateLimit-Reset
- **Exceeded:** Returns 429 Too Many Requests
- **Contact support for Enterprise limit increases**

## Limits & Constraints

| Limit | Free | Pro | Enterprise |
|-------|------|-----|-----------|
| Projects | 2 | Unlimited | Unlimited |
| Team Members | 5 | 50+ | Unlimited |
| File Size | 50MB | 500MB | 1GB |
| Workspace Storage | 1GB | 100GB | Unlimited |
| API Rate Limit | 100/hr | 1,000/hr | Custom |
| Webhook Retries | 24 hours | 72 hours | Unlimited |
| Data Retention | 90 days | 2 years | Unlimited |

## Feature Roadmap

- **Q2 2025:** Mobile app (iOS/Android)
- **Q3 2025:** Advanced portfolio management & resource planning
- **Q4 2025:** AI-powered task prioritization
- **2026:** Custom fields, advanced reporting, machine learning insights

## Support & SLAs

| Channel | Free | Pro | Enterprise |
|---------|------|-----|-----------|
| Email | Community | 24 hours | 4 hours |
| Chat | N/A | Business hours | 24/7 |
| Phone | N/A | N/A | 24/7 |
| Uptime SLA | Best effort | 99.5% | 99.99% |

## FAQ - Quick Answers

### Getting Started
**Q: How long does setup take?**
A: 5-10 minutes. Create account → verify email → invite team members → create first project. Optional: connect integrations.

**Q: Can I import existing projects/tasks?**
A: Yes, via CSV/spreadsheet import (Pro+). Contact support for bulk migrations from other tools.

**Q: Is there a trial?**
A: Free plan includes all core features. Upgrade to Pro anytime.

### Features & Functionality
**Q: Can I use ProjectFlow for personal tasks?**
A: Yes! Free plan works for individuals. Add team members when ready.

**Q: What's the difference between Projects, Tasks, and Subtasks?**
A: Project = container (e.g., "Q2 Campaign"). Task = work item. Subtask = breakdown of task. Can nest infinitely.

**Q: Can I automate task creation?**
A: Yes, via scheduled rules or webhook triggers. See API reference or contact support for advanced workflows.

**Q: What happens when I archive a project?**
A: Archived projects hidden from normal view but still accessible to admins. All data preserved forever. Can unarchive anytime.

### Integration & API
**Q: Which apps integrate with ProjectFlow?**
A: Native: Slack, Outlook, Gmail. OAuth: Google Drive, OneDrive, Dropbox. Custom: any via REST API/webhooks.

**Q: Can I export my data?**
A: Yes, full export available in Settings → Data Export (CSV/JSON). Available on Pro+.

**Q: What's the API rate limit?**
A: 1,000 requests/hour (Pro), 100/hour (Free), custom (Enterprise). Contact sales to increase.

### Billing & Accounts
**Q: Can I have multiple workspaces?**
A: Yes. Each workspace billed separately. Useful for different teams/projects.

**Q: Do you offer annual discounts?**
A: Yes, 20% off annual billing. Upgrade in Settings → Billing.

**Q: How do I add/remove team members?**
A: Settings → Members → Add/Remove. Pro plan: $50/month covers unlimited members. Free: 5 members max.

**Q: Can I cancel anytime?**
A: Yes, zero lock-in. Cancel in Settings → Billing. You keep access until period end.

### Troubleshooting
**Q: Task not showing up in Slack?**
A: Check notification rules (Settings → Notifications). Verify Slack app authorized. Try re-authenticating.

**Q: Rate limited on API?**
A: Implement exponential backoff (2s → 4s → 8s retries). Batch requests when possible. Contact for limit increase.

**Q: Lost access to shared project?**
A: Contact workspace admin. You may have been removed or had permissions changed.

## Common Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Unauthorized: Invalid API token" | Slack/API token expired | Re-authenticate in Integrations → disconnect/reconnect |
| "Rate limit exceeded" | Too many API calls | Implement backoff strategy, batch requests |
| "Permission denied" | Insufficient role | Ask workspace admin to grant access |
| "Task with dependencies can't be marked done" | Blocking task exists | Complete/remove dependencies first |
| "Webhook not responding" | Endpoint timeout (>30s) | Optimize endpoint, move processing async |
| "File upload failed" | File too large | Keep files under 500MB (Free), 1GB (Pro) |
| "Cannot delete workspace" | Has active members/data | Archive projects, remove members first |
| "SSO not available" | Not on Enterprise | Upgrade to Enterprise plan or contact sales |

## Security & Privacy

**Data Encryption**
- All data in transit: TLS 1.3
- Data at rest: AES-256
- Backups: Encrypted, geographically redundant

**Compliance**
- SOC 2 Type II certified
- GDPR compliant (EU data residency available)
- HIPAA: Not certified (Enterprise can inquire about BAA)

**Authentication**
- Passwords: bcrypt hashing, minimum 12 characters
- Session: Secure HTTP-only cookies
- 2FA: Optional for all users

**Data Retention**
- Active accounts: Indefinite
- Deleted accounts: 90-day grace period, then purged
- Audit logs: 2 years retention

## Performance & Limits Reference

| Limit | Value | Notes |
|-------|-------|-------|
| Max projects/workspace | Unlimited (Pro), 2 (Free) | Enterprise: unlimited |
| Max tasks/project | Unlimited | Practical limit ~50k for performance |
| Max team members | 50+ (Pro), 5 (Free), Unlimited (Enterprise) | Each takes 1 workspace seat |
| Max file size | 500MB (Pro), 50MB (Free), 1GB (Enterprise) | Larger files on request |
| Max API calls/hour | 1,000 (Pro), 100 (Free), Custom (Enterprise) | Burst limit: 10 per second |
| Webhook timeout | 30 seconds max | Must respond or retry triggers |
| Task comment limit | Unlimited | Search may slow with 10k+ comments |
| Concurrent connections | Unlimited | Per workspace |
