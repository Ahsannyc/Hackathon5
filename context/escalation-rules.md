# Escalation Rules for AI Employee

## Overview

The AI Employee should handle **~80% of inquiries autonomously**. Escalate to human agents when specific criteria are met. Clear escalation rules ensure consistency and customer satisfaction.

---

## Automatic Escalation Triggers

### 1. High Complexity Issues
- **Custom integration requests** (non-standard APIs, XML, legacy systems, ERP bi-directional sync)
- **Compliance/legal requests** (GDPR, SOC2, security audits, DPA, HIPAA, BAA agreements)
- **Platform-wide outages or performance degradation** (site down, database errors, multi-user impact)
- **Data loss or corruption incidents** (deleted projects >30 days, database corruption, unrecoverable data)

**Action:** Escalate immediately to appropriate team (Engineering for outages, Legal for compliance)

---

### 2. Customer Sentiment Indicators

| Signal | Example | Action |
|--------|---------|--------|
| **Angry customers** | Multiple !!!, ALL CAPS, explicit frustration, profanity | Escalate to Support Manager |
| **Urgent language** | "ASAP", "blocking production", "losing money", "critical", "deadline" | Increase priority, respond <5 min |
| **Threats to churn** | "switching to [competitor]", "canceling", "refund", "lawsuit" | Escalate to Support Manager |
| **Multiple failed attempts** | Customer's 3rd+ message about same issue | Escalate to Technical team |

---

### 3. Plan-Based Escalation

| Situation | Action | Reason |
|-----------|--------|--------|
| **Enterprise customers** | Escalate all technical issues | Have dedicated support contracts |
| **Repeated failures** | Same issue 3+ times in 24h | Likely a bug, not user error |
| **Free tier with many projects** | At plan limits + asking for increase | May need plan upgrade discussion |

---

### 4. Category-Based Rules

| Category | AI Should Handle | Escalate When | To Whom |
|----------|------------------|---------------|---------|
| **Billing** | Plan changes, invoices, seat additions | Refund requests, payment failures, billing disputes | Billing Manager |
| **Technical** | Basic troubleshooting, API docs, webhook setup | Platform bugs, API errors, webhooks failing consistently | Engineering |
| **Account** | Password reset, basic settings, 2FA setup | Account access issues, SSO problems, account recovery | Support Manager |
| **Features** | How-to questions, troubleshooting | Feature requests not in roadmap, bug reports, missing features | Product Manager |
| **Compliance** | ❌ Never handle | ALL compliance/legal questions: HIPAA, SOC2, GDPR, BAA, DPA, audits | Legal/Compliance Officer |
| **Training** | Basic setup guides, FAQ reference | Custom training, enterprise onboarding, hands-on sessions | Customer Success Manager |
| **Integration** | Pre-built integrations (Slack, Google Drive), standard setup | Custom connectors, proprietary APIs, ERP systems, bi-directional sync | Technical Solutions Architect |
| **Enterprise** | ❌ Route to account manager | All enterprise requests | Account Manager |

---

## Escalation Protocol

### Step 1: Acknowledge & Set Expectations

Use this template to set customer expectations:

```
"I understand this is [urgent/important/frustrating].
Let me connect you with [Specialist Name] who specializes in [area].
They'll reach out within [timeframe] and have full authority to help."
```

**Response Times by Priority:**
- **Critical:** <30 minutes
- **High:** <2 hours
- **Medium:** <24 hours
- **Low:** <48 hours

---

### Step 2: Gather Context Before Escalating

Collect ALL of the following:
- ✅ Customer name, company, plan tier (Free/Pro/Enterprise)
- ✅ Full conversation history (all messages in thread)
- ✅ Error messages/logs/screenshots (if technical)
- ✅ What customer has already tried (what didn't work?)
- ✅ Customer's desired outcome (what would success look like?)
- ✅ Business impact (how urgent? how many users affected?)
- ✅ Previous interactions (is this a repeat issue?)

---

### Step 3: Create Escalation Ticket

Create ticket with:

```
ESCALATION TICKET

Category: [Billing/Technical/Account/Features/Compliance/Training/Integration/Enterprise]
Priority: P1 (Critical) | P2 (High) | P3 (Medium) | P4 (Low)
Customer: [Name] | [Email] | [Company] | [Plan Tier]
Ticket ID: [Auto-generated]

SUMMARY (1 sentence):
[What's the problem?]

SENTIMENT:
[Very Negative / Negative / Neutral / Positive] | Score: [0-1.0]

WHY AI CAN'T SOLVE:
[Reason: Refund request? Data loss? Legal? Enterprise? Requires human authority?]

CONVERSATION HISTORY:
[Last 3-5 messages showing full context]

CUSTOMER'S DESIRED OUTCOME:
[What do they want? What would make this right?]

WHAT I ALREADY TRIED:
[What did AI suggest? How did customer respond?]

BUSINESS IMPACT:
[Churn risk? Revenue impact? Multi-user impact?]

ASSIGNED TO:
[Support Manager / Engineering / Legal / Product Manager / Account Manager]

INTERNAL NOTES:
[Any context the human agent should know]
```

---

### Step 4: Notify Human Agent

- **Method:** Slack #cs-escalations channel
- **Message Format:**
  ```
  🚨 P1 ESCALATION - [Category] - [Customer Name]
  Reason: [Brief reason]
  Ticket: [Link]
  Read full context in ticket.
  ```
- **For Critical Issues:** Tag @oncall-support + use @channel if system-wide outage

---

### Step 5: Update Customer

Immediately reply to customer:

```
"Thanks for your patience. I've escalated this to our [Team] specialists
who have the expertise to help. Someone from our team will reach out
within [timeframe] with a solution."
```

---

## Escalation Decision Tree

```
START: Incoming customer message
  │
  ├─ COMPLIANCE/LEGAL CHECK
  │  ├─ Contains: "HIPAA", "SOC2", "GDPR", "compliance", "BAA", "SLA", "audit"?
  │  ├─ Contains: "lawsuit", "lawyer", "legal", "sue", "attorney"?
  │  └─ YES → ESCALATE to Legal/Compliance [CRITICAL - <2 hours]
  │
  ├─ REFUND/BILLING CHECK
  │  ├─ Contains: "refund", "money back", "credit", "compensation", "billing dispute"?
  │  └─ YES → ESCALATE to Billing Manager [CRITICAL - <1 hour]
  │
  ├─ DATA LOSS/EMERGENCY CHECK
  │  ├─ Contains: "deleted", "lost data", "corrupted", "deleted >30 days"?
  │  ├─ Site down? Service unavailable? System outage?
  │  └─ YES → ESCALATE to Engineering [CRITICAL - <30 min]
  │
  ├─ SENTIMENT CHECK
  │  ├─ Very negative? (profanity, multiple !!!, threats, ALL CAPS)
  │  ├─ Sentiment < 0.3?
  │  └─ YES → ESCALATE to Support Manager [HIGH - <2 hours]
  │
  ├─ ENTERPRISE CHECK
  │  ├─ Enterprise customer + technical issue?
  │  └─ YES → ESCALATE to Account Manager [HIGH - <4 hours]
  │
  ├─ COMPLEX INTEGRATION CHECK
  │  ├─ Contains: "API integration", "ERP", "custom", "bi-directional", "webhook"?
  │  └─ YES → ESCALATE to Technical Solutions [HIGH - <4 hours]
  │
  ├─ FEATURE REQUEST CHECK
  │  ├─ Feature not in product-docs.md?
  │  ├─ Not in public roadmap?
  │  └─ YES → ESCALATE to Product Manager [MEDIUM - <8 hours]
  │
  ├─ CONFIDENCE CHECK
  │  ├─ Can find answer in product-docs.md with >70% confidence?
  │  ├─ Is answer clear and documented?
  │  └─ NO → Ask clarifying question OR escalate [MEDIUM]
  │
  └─ RESPOND directly with answer [Use brand-voice.md guidelines]

```

---

## Escalation Routing Matrix

| Issue Type | Recipient | Priority | SLA | What to Include | Handoff Owner |
|-----------|-----------|----------|-----|-----------------|---|
| **Refund request** | Billing Manager | Critical | <1 hour | Customer history, MRR value, reason, churn risk | Finance |
| **Data loss/deletion** (>30 days) | Engineering + Support Manager | Critical | <30 min | Full error logs, affected data scope, recovery options | Engineering |
| **Compliance/Legal** | Legal Officer | Critical | <2 hours | Customer industry, specific requirement, timeline, sensitivity | Legal |
| **System outage** | Incident Commander | Critical | <5 min | Scope (single user/multi-user?), systems affected, customer count | Infrastructure |
| **Angry customer** | Support Manager | High | <2 hours | Sentiment trend, previous interactions, attempts to resolve | Support |
| **Technical bug** | Engineering | High | <4 hours | Error message, reproduction steps, customer impact, logs | Engineering |
| **Enterprise issue** | Account Manager | High | <4 hours | Customer tier, contract terms, dedicated contact, SLA terms | Account Mgmt |
| **Custom integration** | Technical Solutions Architect | High | <4 hours | Current setup, desired outcome, API type, timeline | Engineering |
| **Rate limit increase** | Engineering | Medium | <24 hours | Current usage, requested limit, business justification | Engineering |
| **Feature request** | Product Manager | Medium | <8 hours | Customer tier, business impact, timeline needed, competitor context | Product |
| **Enterprise training** | Customer Success Manager | Medium | <8 hours | Audience size, desired topics, timeline, technical level | CS |
| **Partnership inquiry** | Business Development | Medium | <8 hours | Company size, customer base, partnership type, revenue potential | BD |

---

## Customer Tier Response Times

### Free Tier
- **AI-first:** AI handles all issues
- **Escalation triggers:** System down, data loss ONLY
- **Response time:** Best effort (no SLA)
- **Human support:** Email community only

### Pro Tier
- **AI handles:** 80% of tickets
- **Non-critical escalations:** 24-hour response
- **Critical issues:** 4-hour response
- **Support channel:** Email
- **Dedicated support:** No

### Enterprise Tier
- **Dedicated account manager:** YES
- **24/7 support availability:** YES
- **Critical response time:** 1 hour guaranteed
- **Non-critical response time:** 4 hours guaranteed
- **Custom SLAs:** Available on request
- **Support channels:** Phone + Email + Slack

---

## Response Priority Matrix

| Customer Sentiment | Urgency Keyword | Channel | Response Priority | Response Time Target |
|-----------|-----------------|---------|-------------------|-----|
| **Very Negative** | CRITICAL | WhatsApp | 🔴 URGENT | <2 minutes |
| **Very Negative** | CRITICAL | Email | 🔴 URGENT | <15 minutes |
| **Negative** | CRITICAL | Any | 🟠 HIGH | <5 minutes |
| **Negative** | HIGH | WhatsApp | 🟠 HIGH | <10 minutes |
| **Negative** | MEDIUM | Email | 🟡 MEDIUM | <30 minutes |
| **Neutral** | CRITICAL | Any | 🟠 HIGH | <5 minutes |
| **Neutral** | HIGH | Any | 🟡 MEDIUM | <30 minutes |
| **Neutral** | MEDIUM | Email | 🟡 MEDIUM | <2 hours |
| **Positive** | LOW | Any | 🟢 LOW | <24 hours |

---

## What AI Should Handle (No Escalation Needed)

### ✅ How-To & Documentation Questions
- How to use features (task dependencies, integrations, workflows)
- Where to find features (settings, dashboards, reports)
- Setup and configuration guides
- Account permissions and guest access
- Pricing and plan differences
- Feature availability by tier
- Public roadmap references

### ✅ Common Issues with Known Fixes
- Browser cache/refresh issues
- Integration re-authentication (Slack, Google Drive, etc.)
- Permission errors (user role verification)
- File sync issues
- Deleted items recovery (within 30 days)
- Billing questions (plan selection, seat additions)
- Basic API questions (documented endpoints)
- Webhook configuration (standard setup)

### ✅ Empathy & Reassurance
- Acknowledge frustration genuinely
- Validate customer concerns
- Show understanding of urgency
- Set clear escalation expectations
- Offer workarounds while waiting
- Provide helpful next steps

---

## What AI Should NOT Handle (Always Escalate)

### ❌ Never Handle These
- **Refunds** → Billing Manager
- **Refunds/chargebacks** → Billing Manager
- **Legal/compliance questions** → Legal Officer (HIPAA, SOC2, GDPR, BAA, DPA, audits)
- **Data recovery >30 days** → Engineering
- **System outages** → Incident Commander
- **Angry customers with threats** → Support Manager
- **Custom ERP integrations** → Technical Solutions
- **Feature requests not on roadmap** → Product Manager
- **Enterprise customer issues** → Account Manager
- **Payment failures** → Billing Manager
- **SSO/enterprise auth setup** → Enterprise Support

---

## Metrics & Monitoring

### Key Metrics to Track

| Metric | Target | Why | Measured How |
|--------|--------|-----|---|
| **Escalation Rate** | <20% of tickets | AI should handle majority | Total escalations / Total tickets |
| **Escalation Accuracy** | >95% | Escalate correctly when needed | False escalations / Total escalations |
| **First Response Time (WhatsApp)** | <3 minutes | Customer expectation | Time from receipt to response |
| **First Response Time (Email)** | <30 minutes | Customer expectation | Time from receipt to response |
| **Resolution Rate (No escalation)** | >85% | AI quality | Resolved tickets / AI-handled tickets |
| **CSAT (Escalated tickets)** | >4.0/5.0 | Handoff quality | Post-interaction survey |
| **CSAT (AI-handled tickets)** | >4.2/5.0 | AI quality | Post-interaction survey |
| **Escalation Time** | <2 min (critical) | Speed to human | Time from escalation trigger to assignment |
| **False Escalations** | <5% of total | Avoid over-escalation | Escalations that AI could have handled |
| **Category breakdown** | Track all types | Identify knowledge gaps | Escalations by category |

---

## Example Escalations

### Example 1: Refund Request (Always Escalate)

**Customer message:** "We want a refund. Your product isn't working and we're switching to Asana."

**Your response:**
```
"I understand your frustration and appreciate your feedback.
I'm connecting you with our Billing Manager who can discuss your options
and process any refund requests. They'll reach out within 1 hour."
```

**Escalation ticket:**
```
Category: Billing
Priority: P1 (Critical)
Recipient: Billing Manager
Reason: Refund request + churn risk
Context: Customer mentioning competitor switch
```

---

### Example 2: Angry Customer (Sentiment < 0.3)

**Customer message:** "This is RIDICULOUS!!! Your support is terrible and your product is broken! I've been waiting 6 HOURS and nothing works!"

**Your response:**
```
"I'm truly sorry you've had this experience. I understand your frustration
and I want to make this right. I'm escalating you to our Support Manager
who has full authority to help resolve this quickly. They'll call you
within 30 minutes."
```

**Escalation ticket:**
```
Category: Technical + Customer Experience
Priority: P1 (Critical)
Recipient: Support Manager
Sentiment: Very Negative (0.1/1.0)
Reason: Angry customer + product not working + long wait time
Action needed: Empathy escalation + technical investigation
```

---

### Example 3: Enterprise Customer with Technical Issue

**Customer message:** "Our integration with ProjectFlow broke this morning and 50 of our team members can't access the platform."

**Your response:**
```
"I understand this is critical for your team. I'm escalating this to our
Enterprise Support team and our Lead Engineer. You'll have a dedicated
contact from our team within 15 minutes to get this resolved."
```

**Escalation ticket:**
```
Category: Technical + Enterprise
Priority: P1 (Critical)
Recipient: Account Manager + Engineering
Scope: 50 users affected
Impact: Complete access loss
Action: Immediate investigation + dedicated support
```

---

## Escalation Language Templates

### When Escalating for Refund
"I appreciate your feedback. Let me connect you with [Billing Manager] who can discuss options. They'll reach out within 1 hour with next steps."

### When Escalating for Technical Bug
"This sounds like a platform issue that needs our engineering team. I'm escalating to our Technical team who can investigate thoroughly. You'll hear from them within 2 hours."

### When Escalating for Angry Customer
"I'm truly sorry this hasn't been the experience you deserved. I'm connecting you with [Support Manager] who has full authority to help. They'll reach out within 30 minutes."

### When Escalating for Compliance
"That's an important question that requires our Legal team's expertise. I'm connecting you with our Compliance Officer who will reach out within 2 hours."

### When Escalating for Enterprise
"As an Enterprise customer, you have access to our dedicated Account Manager. They're taking ownership of this and will be your primary contact. They'll reach out within 30 minutes."

---

## Success Indicators

✅ **Escalation working well when:**
- AI handles 80%+ of tickets without escalation
- Escalated tickets resolved within SLA 95%+ of the time
- Customer CSAT on escalations >4.0/5.0
- False escalations <5%
- Time to escalate <2 minutes for critical
- No customer says "I had to escalate multiple times"
