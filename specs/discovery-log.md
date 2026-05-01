# Discovery Log: Customer Success FTE - Incubation Phase

**Date:** 2025-03-31
**Status:** Complete Exploration of 20 Sample Tickets (8 Email, 7 WhatsApp, 6 Web Form)
**Next Phase:** Core Loop Prototype (Exercise 1.2)

---

## Executive Summary

Analyzed 20 real-world customer support tickets across three channels. Discovered **distinct communication patterns**, **critical escalation triggers**, and **hidden complexity** that will shape the AI agent design. The biggest finding: **channel is as important as content**—customers expect different response styles, urgency levels, and interaction models depending on how they contact us.

---

## Channel-Specific Behavioral Patterns

### 📧 EMAIL (Gmail) - 8 tickets (40% of sample)

#### Communication Characteristics
- **Length:** 150-400 words per message
- **Formality:** Semi-formal to formal
- **Tone:** Descriptive, context-heavy, patient
- **Time Pattern:** Mix of business hours + 2-3 off-hours (early morning or late evening international)
- **Structure:** Greeting + context + what they tried + what they need + closing

#### Examples from Sample Data
| Ticket | Pattern | Why It Matters |
|--------|---------|---|
| EMAIL-001 (Sarah) | Detailed context + clear requirements | She's documenting for a team of 50; needs step-by-step |
| EMAIL-003 (Aisha) | URGENT flag + error message + what tried | Already attempted fixes; wants rapid escalation |
| EMAIL-005 (Kevin) | Angry + accusatory + wants refund | High-escalation trigger; needs emotional handling |
| EMAIL-006 (Lisa) | Technical + developer-level question | API integration knowledge required |

#### AI Response Requirements
- ✅ Provide detailed explanations (200-300 words OK)
- ✅ Include step-by-step instructions with numbers/bullets
- ✅ Acknowledge their situation before solving
- ✅ Professional but warm tone
- ✅ Offer follow-up support
- ✅ Detect escalation triggers early (refunds, legal, data issues)

#### Hidden Requirements
1. **Context Preservation:** Email threads matter; need to track conversation history
2. **Urgency Detection:** "URGENT", "CRITICAL", "ASAP" flags should raise response priority
3. **Error Message Handling:** When customer includes error messages, we must search docs/FAQ for that specific error
4. **Decision Authority:** Some questions (refunds, SSO setup) need human approval
5. **Timezone Awareness:** Customers email at all hours; 2am EST email needs quicker response due to timezone gap

---

### 💬 WhatsApp - 7 tickets (35% of sample)

#### Communication Characteristics
- **Length:** 20-100 characters per message (SMS-style)
- **Formality:** Casual, conversational, emotionally expressive
- **Tone:** Immediate, sometimes panicked or frustrated
- **Time Pattern:** Often off-business-hours (22:45, 17:30, 20:30, 15:00)
- **Structure:** Rapid-fire, sometimes multi-message sequences, emoji use common
- **Urgency:** 5 of 7 (71%) had implied time pressure ("10 mins", "tomorrow", "ASAP")

#### Examples from Sample Data
| Ticket | Pattern | Why It Matters |
|--------|---------|---|
| WHATSAPP-001 | Multi-message + urgency + deadline | Client presentation tomorrow; needs 5-minute response |
| WHATSAPP-003 | Panicked + boss asking for report | Real-time pressure; emotional language |
| WHATSAPP-005 | Frustrated with bug (task reverting) | Repeated attempts to fix didn't work; needs troubleshooting |
| WHATSAPP-007 | Site down alert | System outage detection; needs immediate escalation |

#### AI Response Requirements
- ✅ SHORT responses (keep under 300 characters)
- ✅ Use multiple messages instead of walls of text
- ✅ Casual, friendly tone with occasional emoji
- ✅ Immediate acknowledgment (within seconds/minutes, not hours)
- ✅ Quick fix first, if no fix works → escalate fast
- ✅ Assume customer is context-switching; be very explicit
- ✅ Offer quick wins before escalating

#### Hidden Requirements
1. **Real-Time Response:** WhatsApp customers expect 2-5 minute response times, not hours
2. **Rapid Escalation:** If AI can't solve in 1-2 exchanges, must escalate immediately
3. **Emotion Detection:** 6 of 7 WhatsApp tickets had emotional language; AI must detect frustration
4. **Multi-Message Sequences:** Need to handle back-to-back messages as single conversation
5. **Off-Hours Support:** 70% came outside 9-5; AI enables true 24/7
6. **Action-Oriented:** Customers want "here's what to do NOW" not explanations

---

### 🌐 WEB FORM - 6 tickets (30% of sample)

#### Communication Characteristics
- **Length:** Structured form with 200-300 word narrative
- **Formality:** Semi-formal (balanced)
- **Tone:** Exploratory, business-focused, professional
- **Time Pattern:** Distributed through business day (08:45, 10:20, 12:00, 13:00, 14:15, 16:30)
- **Structure:** Form fields (name, email, subject, category, message) + narrative body
- **Urgency:** Mix of casual exploration and legitimate problems

#### Examples from Sample Data
| Ticket | Pattern | Why It Matters |
|--------|---------|---|
| WEB-FORM-001 (Marcus) | Pricing question | Prospect evaluation; sales opportunity |
| WEB-FORM-003 (Rachel) | Accidental deletion + panic | Data recovery needed; likely can't auto-solve |
| WEB-FORM-004 (Priya) | Feature exploration | Permission model questions; reference documentation |
| WEB-FORM-006 (James) | Billing change request | Account modification; needs transaction authority |

#### AI Response Requirements
- ✅ Semi-formal, helpful tone
- ✅ Clear, structured answers (200-300 words)
- ✅ Direct answer to their specific question first
- ✅ Offer next steps / follow-up options
- ✅ Link to relevant docs/dashboards when applicable
- ✅ Use form metadata (category, form fields) to route correctly

#### Hidden Requirements
1. **Form Structure Matters:** Category field guides response routing (billing → billing team, feature_request → product team)
2. **Web-to-Email Transition:** Web form customer might follow up via email/WhatsApp; need unified customer record
3. **Sales Opportunity:** Pricing questions are potential upsells; might need sales context
4. **Documentation References:** Web form customers often exploring; good opportunity to link docs and reduce future tickets

---

## Critical Findings: Issue Categories & Escalation Patterns

### 🎯 Issue Type Breakdown

| Issue Type | Count | Escalate? | AI Can Handle? | Example |
|-----------|-------|-----------|---|---------|
| **Feature "How-To"** | 5 | ❌ No | ✅ Yes | "How do I set up task dependencies?" |
| **Basic Troubleshooting** | 4 | ❌ No | ✅ Yes | "Files not showing up", "Task status reverting" |
| **Pricing/Billing Questions** | 3 | ⚠️ Sometimes | ⚠️ Partial | Simple answer OK, changes need human |
| **Permissions/Access** | 3 | ❌ No | ✅ Yes | "How to add guests", "Admin setup" |
| **Technical Bugs** | 2 | ✅ Yes | ❌ No | "Slack integration broken", "Sync issue" |
| **Refund/Account Issues** | 2 | ✅ ALWAYS | ❌ No | Refund request, data recovery |
| **Compliance/Legal** | 2 | ✅ ALWAYS | ❌ No | HIPAA questions, BAA agreements |
| **Enterprise/Integration** | 2 | ✅ ALWAYS | ❌ No | ERP integration, white-label |
| **Very Angry Customers** | 1 | ✅ ALWAYS | ❌ No | Multiple escalation flags |

### 🚨 Critical Escalation Triggers Found

**ALWAYS Escalate (6 triggers detected in sample):**

1. **Refund Requests** (EMAIL-005: "want a refund")
   - Financial authority required
   - Escalate to: Billing/Support Manager
   - Timeline: <1 hour response

2. **Data Loss/Deletion Recovery** (WEB-FORM-003: "accidentally deleted", EMAIL-005: "lost data")
   - Legal implications, recovery needed
   - Escalate to: Support Manager + Engineering
   - Timeline: Immediate

3. **Angry/Very Negative Sentiment** (EMAIL-005: profanity, accusations)
   - Requires empathy + authority
   - Escalate to: Support Manager
   - Timeline: <2 hours

4. **Compliance/Legal Questions** (WEB-FORM-004: HIPAA, EMAIL-007: ERP regulations)
   - Legal liability
   - Escalate to: Legal/Compliance Officer
   - Timeline: <4 hours (high priority)

5. **Enterprise/Partnership Requests** (EMAIL-008: "white-label", "reseller")
   - Strategic business decision
   - Escalate to: Business Development
   - Timeline: <8 hours

6. **System Outages** (WHATSAPP-007: "website is down")
   - Multi-user impact
   - Escalate to: Engineering immediately
   - Timeline: Urgent

7. **Complex Technical Integration** (EMAIL-007: ERP bi-directional sync)
   - Requires engineering design
   - Escalate to: Technical Solutions
   - Timeline: <4 hours

---

## Hidden Requirements & Challenges

### 1. **Cross-Channel Customer Identity** ⚠️
**Challenge:** Same customer might contact via email, WhatsApp, and web form.

**Example from Sample:**
- Marcus (WEB-FORM-001) asks pricing → might follow up via WhatsApp asking "do you have mobile app?"
- Need to recognize it's the same customer and reference previous conversation

**Requirement:**
- Unified customer record keyed by email/phone
- Conversation history spans channels
- Context carried across channels
- Detection: Match email address, phone number, or name + company

### 2. **Emotion & Urgency Detection** ⚠️
**Challenge:** WhatsApp and some emails carry emotional language requiring different handling.

**Examples from Sample:**
- WHATSAPP-001: "😞" emoji + "urgent" + "client presentation tomorrow" = CRITICAL
- WHATSAPP-003: "HELP!!!" + "she wants it in 10 mins" = PANIC
- EMAIL-005: "unacceptable", "terrible", "posting reviews" = ANGRY, ESCALATE

**Requirement:**
- Sentiment analysis on incoming messages
- Urgency detection (keywords: "ASAP", "urgent", "deadline", "now")
- Emoji interpretation (😢 😤 😞 = negative)
- Response time calibration: WhatsApp CRITICAL = respond in minutes, not hours

### 3. **Channel-Appropriate Response Formatting** ⚠️
**Challenge:** Same answer needs different formats by channel.

**Example:** "How do I add a guest?"
- **Email:** Formal greeting, 5 numbered steps, screenshot links, professional closing
- **WhatsApp:** "Hey! Go to Settings > Members > Invite > select 'Guest'. They get read-only access 👍"
- **Web Form:** Semi-formal, 3-4 sentences with inline links

**Requirement:**
- Response template system parameterized by channel
- Character limits for WhatsApp (goal: <300 chars)
- Link handling (shortened URLs for SMS, full URLs for email)
- Emoji guidelines (WhatsApp: some OK, Email: none, Web: minimal)

### 4. **Knowledge Base Completeness Gaps** ⚠️
**Challenge:** Some questions from sample may NOT be answerable from product-docs.md

**From Sample:**
- EMAIL-004: "How to enable SSO?" → product-docs has no SSO section detail
- EMAIL-007: "ERP integration options?" → not documented
- WEB-FORM-004: "Guest permissions?" → needs more detail

**Requirement:**
- Robust "I don't know" handling → escalate or offer workaround
- Graceful degradation: "This is on our roadmap" vs "we can't do this"
- FAQ detection: Recognize when question is in docs but customer missed it
- Search confidence: If <70% match, escalate or ask clarifying question

### 5. **Escalation Context Preservation** ⚠️
**Challenge:** When escalating, human agent needs full conversation context.

**Example:** WHATSAPP-003 (panicked customer) needs:
- Full message thread (3 messages showing escalation of panic)
- Timestamp of messages (20:30 = evening, time-sensitive)
- Previous interactions (is this repeat issue or first time?)
- Attempted solutions (have they tried the FAQ already?)

**Requirement:**
- Escalation template with full context
- Message history attached to escalation
- Metadata: sentiment trend, urgency level, customer tier/history
- Clear "why this wasn't AI-solvable" explanation for human agent

### 6. **Tone & Personality Consistency** ⚠️
**Challenge:** AI must match brand voice but also channel expectations.

**Examples from Sample:**
- EMAIL-001: "Thanks for the great question!" (Sarah = knowledgeable, friendly)
- EMAIL-005: "I'm really sorry to hear this..." (Kevin = angry, needs empathy FIRST)
- WHATSAPP-001: "😢" emoji + urgent → respond casual but FAST
- WHATSAPP-004: "hi! quick question" → friendly, no stress

**Requirement:**
- System prompt must include brand voice guidelines
- Sentiment-aware responses (adjust tone to customer's tone)
- Channel-aware tone (casual for WhatsApp, formal for email)
- Emoji rules (when to use, when not to)

### 7. **Billing & Account Modification Authority** ⚠️
**Challenge:** Some customer requests touch financial/account state.

**From Sample:**
- WEB-FORM-006: "Can we change billing to annual? Add 10 seats?" → AI can INFORM but not ACT
- WEB-FORM-001: "Do you offer annual discounts?" → AI can answer, but usage may vary

**Requirement:**
- Clear distinction: Answer vs. Action
- AI can tell them HOW, but humans must EXECUTE
- For billing changes, escalate to Billing team with request summary
- Track which questions became account actions (feedback loop)

### 8. **FAQ Recognition & Optimization** ⚠️
**Challenge:** 60% of support should be FAQ-level, but FAQ structure isn't in current docs.

**From Sample Solvable as FAQ:**
- "How do I set task dependencies?" → Should be in FAQ
- "Where are reports?" → Should be in FAQ
- "How do I add guests?" → Should be in FAQ
- "Is there a mobile app?" → Should be in FAQ

**Requirement:**
- Create explicit FAQ section in knowledge base
- Tag questions as "FAQ-solvable" in training data
- Measure: % of tickets that could be FAQ-redirected
- Iteration: Use AI Q&A logs to improve FAQ

### 9. **Error Message Handling** ⚠️
**Challenge:** Some customers report errors; AI needs ability to search error DB.

**From Sample:**
- EMAIL-002: "Cannot delete workspace with archived projects"
- EMAIL-003: "Unauthorized: Invalid API token"

**Requirement:**
- Error code lookup function
- Stack trace search capability
- Link to troubleshooting guides for specific errors
- If unknown error: escalate to Engineering

### 10. **Time Zone Awareness** ⚠️
**Challenge:** ProjectFlow has customers in 20+ countries; 24/7 AI matters.

**Example Timeline:**
- WHATSAPP-001: 22:45 UTC (customer evening) = immediate response advantage
- EMAIL-006: 03:30 UTC (middle of night) = AI responds when humans can't

**Requirement:**
- No response time SLAs for off-hours (AI is 24/7, humans aren't)
- Escalations generated at any time; humans triage in business hours
- Set customer expectations: "AI will respond immediately, human team within [X] hours"

---

## High-Level System Architecture (Discovered)

```
┌────────────────────────────────────────────────────────────────┐
│                    CUSTOMER SUCCESS FTE SYSTEM                 │
└────────────────────────────────────────────────────────────────┘

1. INTAKE LAYER (Multi-Channel)
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ Gmail API    │  │ Twilio       │  │ Web Form     │
   │ (Webhook)    │  │ WhatsApp API │  │ HTTP POST    │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                  ┌──────────────────┐
                  │  Unified Queue   │
                  │ (Channel-aware)  │
                  └────────┬─────────┘
                           │
2. PROCESSING LAYER        ▼
   ┌────────────────────────────────────────┐
   │  Customer Success Agent (Claude)       │
   │  ├─ Identify Customer (Cross-channel)  │
   │  ├─ Fetch Conversation History         │
   │  ├─ Search Knowledge Base              │
   │  ├─ Analyze Sentiment & Urgency        │
   │  ├─ Determine: Answer or Escalate?     │
   │  └─ Format Response (Channel-aware)    │
   └────────────────────────────────────────┘
          │                      │
    Answer (80%)          Escalate (20%)
      │                      │
      ▼                      ▼
3. RESPONSE LAYER      ESCALATION LAYER
   ┌──────────────┐  ┌──────────────────┐
   │ Send Response│  │ Create Handoff   │
   │ via Channel  │  │ Assign to Team   │
   └──────────────┘  └──────────────────┘
          │
          ▼
4. STATE & MEMORY
   ┌───────────────────────────────────────┐
   │  PostgreSQL Database (CRM)            │
   │  ├─ Customers (unified identity)      │
   │  ├─ Conversations (channel-aware)     │
   │  ├─ Messages (full history)           │
   │  ├─ Tickets (unified tracking)        │
   │  └─ Escalations (handoff records)     │
   └───────────────────────────────────────┘

5. LEARNING & ITERATION
   ├─ Daily sentiment reports
   ├─ Escalation reasons analysis
   ├─ FAQ gap analysis
   └─ Channel-specific metrics
```

---

## Key Clarifying Questions for Next Phase

Before building the prototype, I need your input on:

1. **Knowledge Base Source:** Where will the agent search for answers?
   - Will you use product-docs.md as the knowledge base?
   - Should we add vector embeddings for semantic search?
   - Do you have FAQ data or should we build from sample tickets?

2. **Sentiment Analysis Approach:** How should the agent detect emotion?
   - Rule-based (keywords: "URGENT", "angry") or LLM-based?
   - Should we flag escalations automatically or let human validate?
   - What's our sentiment threshold for escalation? (<0.3? <0.4?)

3. **Response Time SLAs:** What's acceptable?
   - WhatsApp: <5 min? <2 min? <30 sec?
   - Email: <1 hour? <2 hours?
   - Web Form: <15 min? <30 min?

4. **Escalation Decision Authority:** When AI is unsure, should it:
   - Always escalate (conservative, safer)?
   - Attempt one solution attempt then escalate (balanced)?
   - Try multiple approaches before giving up (aggressive)?

5. **Channel Priority:** If customer uses all 3 channels, which takes priority?
   - WhatsApp (most urgent)?
   - Latest message regardless of channel?
   - Customer preference setting?

---

## Discovered Metrics to Track

Once prototype is running:

| Metric | Target | Why Important |
|--------|--------|---|
| % Handled by AI (no escalation) | 80%+ | Measure AI competence |
| Average response time (WhatsApp) | <3 min | WhatsApp expectation |
| Average response time (Email) | <2 hours | Email expectation |
| Customer satisfaction (post-response) | 4.0/5.0+ | Quality of answers |
| Escalation rate by reason | <20% total | Identify knowledge gaps |
| Cross-channel identification rate | 95%+ | CRM accuracy |
| Sentiment trend accuracy | 90%+ | Emotion detection quality |

---

## Next Steps: Exercise 1.2

You're now ready to build the **Core Loop Prototype**. Use this discovery log to inform:

1. System prompt (leverage findings on brand voice, tone, escalation rules)
2. Tool definitions (search knowledge base, create ticket, escalate)
3. Channel awareness (format responses by channel)
4. Edge case handling (see "What AI Should Handle" section above)

**Ready to continue? Move to Exercise 1.2 prompt below.** ↓

---

## 📋 Incubation Phase - Exercise 1.2 Prompt Template

When you're ready to start building the prototype, use this prompt:

```
Based on the discovery log we just created, I'm ready to build the core loop prototype.

Here's what I want you to build:

**Core Interaction Loop:**
1. Take a customer message as input with channel metadata
2. Normalize the message regardless of source channel
3. Search the knowledge base (context/product-docs.md) for relevant information
4. Generate a helpful response
5. Format response appropriately for the channel (email vs chat style)
6. Decide if escalation is needed (using escalation-rules.md)

**Requirements:**
- Use Python (simple, readable, testable)
- Implement for all 3 channels (channel awareness)
- Use the brand voice guidelines from brand-voice.md
- Detect sentiment and urgency from escalation-rules.md
- Gracefully handle edge cases
- Test with at least 5 diverse tickets from sample-tickets.json

**Deliverables:**
1. Working prototype script (src/core_loop.py)
2. Test results showing it handles at least 5 sample tickets
3. Notes on what's working, what's hard, what needs iteration

Let's start!
```

---

## Discovery Log Status

✅ **Exploration Complete**
- [x] Analyzed 20 sample tickets across 3 channels
- [x] Identified 10 hidden requirements
- [x] Mapped escalation triggers and patterns
- [x] Defined channel-specific behaviors
- [x] Created high-level system architecture
- [x] Generated clarifying questions
- [x] Documented metrics to track

**Ready to move to Exercise 1.2: Prototype the Core Loop** 🚀
