# Exercise 1.5: Agent Skills Definition

**Status:** ✅ COMPLETE  
**Date:** 2026-04-02  
**Exercise:** 1.5 - Define Agent Skills (Incubation Phase)

---

## Overview

Agent Skills are reusable, well-defined capabilities your Customer Success FTE can invoke. This document formalizes the 5 core skills discovered and tested during Exercises 1.1–1.4, providing the foundation for production implementation in Stage 2.

---

## Skill 1: Knowledge Retrieval Skill

**When to Use:** Customer asks product questions or needs guidance

### Purpose
Search product documentation and knowledge base to find answers for customer inquiries.

### Inputs
- `query` (string, 5–500 chars): Customer's question or issue description
- `category` (optional): Filter results by KB category (billing, technical, feature, general)
- `max_results` (int): Number of results to return (default 5, max 10)

### Outputs
```json
{
  "success": true,
  "intent": "billing",
  "intent_confidence": 0.92,
  "results_count": 3,
  "results": [
    {
      "title": "How to Upgrade Your Plan",
      "category": "billing",
      "relevance_score": 0.95,
      "snippet": "To upgrade your plan, navigate to Settings → Billing → Change Plan...",
      "full_url": "/docs/billing/upgrade-plan"
    }
  ],
  "fallback_suggestion": "If results aren't helpful, consider escalating to human support."
}
```

### Examples

**✅ Good:** "How do I upgrade my plan?" → Returns 5 billing articles, 0.92 intent confidence
**✅ Good:** "What's a webhook?" → Returns 3 technical articles, 0.87 intent confidence  
**⚠️ Edge Case:** "" (empty) → Returns error: "Query cannot be empty"
**⚠️ Edge Case:** "xyz123abc" → Returns empty results, suggests escalation

### Success Criteria
- Returns relevant documentation snippets within 2 seconds
- Intent detection accuracy >85% on test set
- Gracefully handles edge cases (empty, nonsensical, out-of-scope queries)
- Fallback suggestion provided when no results found

---

## Skill 2: Sentiment Analysis Skill

**When to Use:** Analyze every customer message to detect emotional tone and urgency

### Purpose
Detect customer sentiment and emotion to inform escalation decisions and response tone adjustment.

### Inputs
- `message_text` (string): Customer's message to analyze
- `context` (optional): Previous messages in conversation (for trend detection)

### Outputs
```json
{
  "primary_sentiment": "positive",
  "confidence": 0.87,
  "sentiment_levels": {
    "positive": 0.87,
    "neutral": 0.10,
    "negative": 0.03,
    "angry": 0.00,
    "frustrated": 0.00
  },
  "emotion_tags": ["satisfied", "helpful", "appreciative"],
  "urgency_level": 1,
  "should_escalate": false,
  "trend": "improving",
  "recommendation": "Respond with brief positive confirmation."
}
```

### Sentiment Scale (5 Levels)

| Level | Score | Definition | Action |
|-------|-------|-----------|--------|
| **Very Positive** | 4.0–5.0 | Delighted, praised, grateful | Reinforce positive experience |
| **Positive** | 3.0–3.99 | Satisfied, helped, pleased | Standard response |
| **Neutral** | 1.5–2.99 | Factual, matter-of-fact | Standard response |
| **Negative** | 0.5–1.49 | Concerned, unsatisfied, confused | Escalate if trend worsens |
| **Very Negative** | 0.0–0.49 | Angry, frustrated, demanding refund | **ESCALATE immediately** |

### Examples

**✅ Positive Message:**
```
"Wow, your new feature just saved me 2 hours! Thanks so much! 🎉"
→ Sentiment: Very Positive (0.95)
→ Emotion tags: [grateful, excited, satisfied]
→ Action: Affirm, thank for feedback, offer continued support
```

**⚠️ Negative Escalation Trigger:**
```
"I've been trying to fix this for 3 hours and nothing works. Your product is broken. I want my money back!"
→ Sentiment: Very Negative (0.12)
→ Emotion tags: [frustrated, angry, demanding]
→ Urgency: CRITICAL
→ Action: **ESCALATE to Finance + Product teams immediately**
```

**⚠️ Trend Detection:**
```
Message 1: "Your product is okay, but..." → Neutral (2.1)
Message 2: "I found it confusing..." → Negative (1.3)
Message 3: "I'm going to cancel..." → Very Negative (0.2)
→ Trend: Declining
→ Action: **ESCALATE before customer leaves**
```

### Success Criteria
- Sentiment detection accuracy >80% on test set
- Emotion tag identification >75% accuracy
- Escalation trigger detection 100% (no missed "very negative" messages)
- Processing time <500ms per message

---

## Skill 3: Escalation Decision Skill

**When to Use:** After analyzing sentiment and attempting to resolve, decide if human escalation is needed

### Purpose
Determine when a ticket should be escalated to a human specialist based on issue type, sentiment, complexity, and business rules.

### Inputs
- `ticket_id` (string): Ticket identifier
- `reason` (string): Why escalation is being considered
- `issue_category` (string): Billing, Technical, Feature, Compliance, Other
- `sentiment_score` (float): Current sentiment (0.0–5.0)
- `sentiment_trend` (string): improving, stable, declining
- `conversation_length` (int): Number of messages exchanged
- `resolution_attempts` (int): How many solutions have been tried

### Outputs
```json
{
  "should_escalate": true,
  "escalation_category": "refund_request",
  "priority": "high",
  "assigned_team": "finance",
  "sla_minutes": 240,
  "confidence": 0.96,
  "reason": "Customer requested refund; sentiment declining over 4 messages",
  "rules_triggered": [
    "very_negative_sentiment",
    "refund_request",
    "declining_trend"
  ],
  "agent_notes": "Customer frustrated after 3 failed attempts to fix. Started conversation positive, now escalating negativity."
}
```

### Escalation Rules (Decision Matrix)

| Trigger | Category | Team | Priority | SLA | Auto-Escalate? |
|---------|----------|------|----------|-----|---|
| Sentiment < 0.5 | Any | Specialist | Critical | 1 hr | ✅ YES |
| Refund request | Billing | Finance | High | 4 hrs | ✅ YES |
| Legal/compliance question | Compliance | Legal | Critical | 1 hr | ✅ YES |
| Technical issue + 3 attempts failed | Technical | Engineering | High | 2 hrs | ✅ YES |
| Feature request | Feature | Product | Medium | 24 hrs | ❌ NO (collect for product) |
| Angry tone + unresolved | Any | Manager | High | 2 hrs | ✅ YES |
| >5 messages with no resolution | Any | Specialist | Medium | 4 hrs | ✅ YES |
| Declining sentiment trend | Any | Manager | High | 2 hrs | ✅ YES |
| VIP customer (premium plan) | Any | Account Manager | High | 1 hr | ✅ YES |
| Zero KB matches found | Any | Specialist | Medium | 4 hrs | ✅ YES |

### Examples

**✅ Auto-Escalate (Refund):**
```
Reason: "Customer wants refund, lost faith in product"
Sentiment: 0.15 (very negative)
Triggered rules: [refund_request, very_negative_sentiment, declining_trend]
→ Escalate: YES
→ Team: Finance
→ Priority: High
→ SLA: 4 hours
```

**❌ Do NOT Escalate (Feature Request):**
```
Reason: "Customer asking if we can add dark mode"
Sentiment: 3.2 (positive)
Issue: Feature request
→ Escalate: NO
→ Action: Log as feature request, thank customer, move to product backlog
```

**⚠️ Escalate (Technical + Multiple Attempts):**
```
Reason: "Customer tried 3 different solutions, still getting error code X"
Sentiment: 2.1 (neutral but frustrated)
Attempts: 3
→ Escalate: YES
→ Team: Engineering
→ Priority: High
→ SLA: 2 hours
```

### Success Criteria
- Escalation rules applied correctly 100% of the time (no false negatives on refunds, legal issues, etc.)
- False positive escalations <5% (don't escalate simple feature requests)
- SLA accuracy: match team assignment to issue category
- Decision time <1 second

---

## Skill 4: Channel Adaptation Skill

**When to Use:** Before sending any response to customer, adapt message tone and format for channel

### Purpose
Format AI responses to match each communication channel's conventions, length constraints, and tone expectations.

### Inputs
- `message_text` (string): Raw response from AI
- `target_channel` (enum): email, whatsapp, web_form
- `customer_sentiment` (float): Current sentiment (for tone adjustment)
- `ticket_priority` (string): low, medium, high, critical

### Outputs
```json
{
  "success": true,
  "channel": "whatsapp",
  "original_length": 245,
  "formatted_length": 158,
  "formatted_message": "Hey! 👋 Thanks for reaching out.\n\nHere's how to fix it:\n1. Go to Settings\n2. Click 'Reset Cache'\n3. Refresh\n\nLet me know if it works! 🚀",
  "character_count": 158,
  "emoji_count": 2,
  "tone": "casual_friendly",
  "formatting_applied": ["emoji_spacing", "line_breaks", "bullet_points"],
  "within_constraints": true
}
```

### Channel Guidelines

#### Email (Gmail)
- **Tone:** Professional, thorough, solution-focused
- **Length:** 300–500 words
- **Structure:**
  - Greeting (formal: "Dear [Name],")
  - Acknowledgment of issue
  - Step-by-step solution (numbered list)
  - Next steps / call to action
  - Professional signature
- **Emojis:** None (or very minimal for special cases)
- **Formatting:** Headers, bold for important terms, numbered/bulleted lists

**Example:**
```
Dear John,

Thank you for reaching out about your upgrade issue.

I understand you're having difficulty navigating to the Billing section. Here's how to resolve this:

1. Log in to your CloudFlow account
2. Navigate to Settings (top-right corner)
3. Click "Billing" in the left sidebar
4. Select "Change Plan"
5. Choose your desired tier and confirm

If you encounter any additional issues, please let me know.

Best regards,
CloudFlow Customer Success Team
support@cloudflow.io
```

#### WhatsApp (Twilio)
- **Tone:** Casual, friendly, encouraging, emoji-friendly
- **Length:** 150–300 characters (SMS-optimized)
- **Structure:**
  - Greeting emoji + name (optional)
  - Direct, concise answer
  - Numbered steps or tips
  - Closing question or encouragement
  - Casual sign-off
- **Emojis:** 1–3 per message (enhance readability)
- **Formatting:** Line breaks for scannability, avoid long paragraphs

**Example:**
```
Hey there! 👋

Great question! To upgrade:
1️⃣ Settings
2️⃣ Billing
3️⃣ Change Plan

Done! Let us know if you need anything else 🎉

- CloudFlow Team
```

#### Web Form (API Response)
- **Tone:** Professional yet warm, clear, actionable
- **Length:** 200–400 words
- **Structure:**
  - Greeting
  - Quick summary of issue/action taken
  - Detailed steps (if applicable)
  - Link to relevant docs
  - Offer for follow-up
- **Formatting:** HTML-safe, no emojis (or minimal), clear sections

**Example:**
```
<h3>Thanks for submitting your form!</h3>

<p>We've received your request about upgrading your plan. Here's what to do next:</p>

<ol>
  <li>Log in to your account</li>
  <li>Go to Settings → Billing</li>
  <li>Click "Change Plan"</li>
  <li>Select your new tier and confirm</li>
</ol>

<p><strong>Need more help?</strong> <a href="/docs/billing">View our billing guide</a> or <a href="mailto:support@cloudflow.io">contact us</a>.</p>
```

### Examples

**Email Adaptation (Professional):**
```
Input: "click settings then billing then change plan done"
Channel: email
→ Formatted:
"Thank you for your inquiry about upgrading your plan. Here's the straightforward process:

1. Log in to your CloudFlow account
2. Click Settings (top-right corner)
3. Select Billing from the menu
4. Click Change Plan and choose your desired tier

If you have any questions, please let us know.

Best regards,
CloudFlow Support"
```

**WhatsApp Adaptation (Casual):**
```
Input: "click settings then billing then change plan done"
Channel: whatsapp
→ Formatted:
"Hey! 👋

Easy peasy:
1️⃣ Settings
2️⃣ Billing
3️⃣ Change Plan ✅

Done! Any other Qs? 🎉"
```

### Success Criteria
- All responses adhere to channel length constraints 100% of the time
- Tone detection (formal vs. casual) correct 95%+ of the time
- Formatting (emoji, line breaks, structure) appropriate for channel 100%
- No HTML/markdown leakage between channels

---

## Skill 5: Customer Identification Skill

**When to Use:** On every incoming message from any channel, identify or create customer record

### Purpose
Unified customer identification across all channels so the FTE remembers customers even if they switch from Email → WhatsApp → Web Form.

### Inputs
- `message_metadata` (object):
  - `from_email` (optional): Sender's email
  - `from_phone` (optional): Sender's phone number
  - `from_channel` (enum): email, whatsapp, web_form
  - `customer_name` (optional): Name provided in message or form
  - `message_text` (string): Message content (may contain identity clues)

### Outputs
```json
{
  "success": true,
  "customer_id": "CUST-A7F2E9",
  "action": "matched",
  "confidence": 0.98,
  "customer_record": {
    "customer_id": "CUST-A7F2E9",
    "name": "John Smith",
    "email": "john.smith@company.com",
    "phone": "+1-555-123-4567",
    "plan": "pro",
    "signup_date": "2024-06-15",
    "total_messages": 7,
    "channels_used": ["email", "whatsapp"],
    "last_contact": "2026-04-02T14:32:00Z",
    "sentiment_trend": [3.2, 3.5, 3.8, 4.1, 3.9, 4.2, 4.0],
    "topics": ["billing", "features", "technical"],
    "escalation_count": 0,
    "merged_history_summary": "Positive customer, used email then WhatsApp, mostly feature questions"
  },
  "merged_conversations": 7,
  "notes": "Customer switched from email to WhatsApp on 2026-04-01 but previously engaged with product."
}
```

### Identification Scenarios

#### Scenario 1: Email → WhatsApp (Same Customer)
```
Email: "john.smith@company.com"
WhatsApp: "+1-555-123-4567"
→ Lookup: Email found in DB as CUST-A7F2E9
→ Phone number matches existing record
→ Action: MERGE (update phone in existing customer)
→ Result: Unified history across 2 channels
```

#### Scenario 2: Brand New Customer (Web Form)
```
Form submission:
  name: "Sarah Johnson"
  email: "sarah.johnson@startup.io"
  message: "How do I get started?"
→ Lookup: No match in DB
→ Action: CREATE new customer record
→ Result: CUST-K3M9L2 assigned
```

#### Scenario 3: Same Customer, Multiple Email Addresses
```
Message 1: "john.work@company.com"
Message 2: "john.personal@gmail.com"
Same phone: "+1-555-123-4567"
→ Lookup: Phone number matches CUST-A7F2E9
→ Action: MERGE (add secondary email)
→ Result: Both emails linked to single customer ID
```

#### Scenario 4: Ambiguous (Merge Multiple?)
```
Email: "support@bigcompany.com"
Name: "John"
Phone: None
→ Lookup: Multiple John records exist in CUST-JOHN-*
→ Confidence: 0.45 (too low for auto-match)
→ Action: Request clarification (ask for account email or plan info)
→ Result: Do not merge until confident
```

### Identification Rules

| Input | Priority | Matching Logic | Confidence |
|-------|----------|---|---|
| Email address | High | Exact match in DB | 0.98+ |
| Phone number | High | Exact match in DB | 0.97+ |
| Email + Phone | Very High | Both must match same customer | 0.99 |
| Email + Name | Medium | Email is primary, name validates | 0.85–0.90 |
| Phone + Name | Medium | Phone is primary, name validates | 0.85–0.90 |
| Name only | Low | Skip if >1 match, ask for clarification | <0.70 |

### Examples

**✅ Perfect Match (Email):**
```
Incoming: Email from "alice.jones@company.com"
Lookup: Found CUST-B5K7P9 with email "alice.jones@company.com"
→ Match: YES (0.98 confidence)
→ Action: Load customer history (14 previous messages, 2 channels)
→ Result: Respond with context, remember sentiment trend
```

**✅ Cross-Channel Merge (Phone + Email):**
```
Incoming: WhatsApp from "+1-555-999-8888"
Lookup: CUST-M2N8Q1 has phone "+1-555-999-8888"
→ Match: YES (0.97 confidence)
→ Action: Check if email in record; if different, merge contact info
→ Result: Unified history shows: Email 3 months ago (positive), WhatsApp today
```

**⚠️ Ambiguous (Request Clarification):**
```
Incoming: Web form, name "John", no email/phone
Lookup: Multiple Johns in DB (CUST-JOHN-1, CUST-JOHN-2, CUST-JOHN-3)
→ Match: AMBIGUOUS (0.30 confidence, too low)
→ Action: Ask "Hi John! Could you provide your email or account name so I can pull up your history?"
→ Result: Wait for response before proceeding
```

### Success Criteria
- Exact email/phone matches: 100% accuracy
- Cross-channel merges: >95% accuracy (test with known customers)
- New customer creation: Proper CUST-ID generation, no duplicates
- Ambiguous cases: Always request clarification (never auto-merge questionable matches)
- Processing time <500ms

---

## Skill Integration & Workflow

### How Skills Work Together

```
1. INCOMING MESSAGE
   ↓
2. Customer Identification Skill
   (Who is this? Load history)
   ↓
3. Knowledge Retrieval Skill
   (What do they want? Search KB)
   ↓
4. Sentiment Analysis Skill
   (How are they feeling? Detect emotion)
   ↓
5. Escalation Decision Skill
   (Should we escalate? Check rules)
   ↓
6. Channel Adaptation Skill
   (Format response for this channel)
   ↓
7. SEND RESPONSE (or escalate to human)
```

### Real-World Example

**Incoming Message:**
```
WhatsApp from "+1-555-123-4567":
"I've been trying to fix this for hours and it's still broken. I just want my money back!"
```

**Skill Execution:**

1. **Customer Identification:** ✅ Found CUST-A7F2E9 (existing customer, known from email)
2. **Knowledge Retrieval:** 🔍 Searched KB for "broken", found 0 matches → KB gap
3. **Sentiment Analysis:** 🔴 Sentiment 0.10 (very negative), emotion tags: [frustrated, angry, demanding_refund]
4. **Escalation Decision:** ✅ Rule triggered: "Refund request + very negative sentiment" → **ESCALATE YES**
   - Team: Finance
   - Priority: High
   - SLA: 4 hours
5. **Channel Adaptation:** (Not needed—escalating)
6. **Result:** Create ESC-20260402-0001, assign to Finance team, respond with empathy message

---

## Skill Accuracy Targets (Test Set)

| Skill | Metric | Target | Tolerance |
|-------|--------|--------|-----------|
| Knowledge Retrieval | Intent detection accuracy | >85% | ±5% |
| Knowledge Retrieval | Response time | <2s | ±500ms |
| Sentiment Analysis | Sentiment detection accuracy | >80% | ±8% |
| Sentiment Analysis | "Very negative" escalation recall | 100% | 0% tolerance |
| Escalation Decision | Rule application accuracy | 100% | 0% tolerance |
| Escalation Decision | False positive rate | <5% | ±2% |
| Channel Adaptation | Length constraint compliance | 100% | 0% tolerance |
| Channel Adaptation | Tone appropriateness | >95% | ±3% |
| Customer Identification | Email/phone exact match | 100% | 0% tolerance |
| Customer Identification | Cross-channel merge accuracy | >95% | ±3% |
| Customer Identification | No false merges | 100% | 0% tolerance |

---

## Testing & Validation

### Unit Tests Per Skill

#### Test: Knowledge Retrieval
```python
# Test 1: Valid query with results
input: query="How do I upgrade?", max_results=5
expected: intent="billing", results_count=3–5

# Test 2: Empty query
input: query="", max_results=5
expected: error message, no crash

# Test 3: Out-of-scope query
input: query="xyz123abc", max_results=5
expected: intent="general", results_count=0, fallback suggestion provided
```

#### Test: Sentiment Analysis
```python
# Test 1: Very positive message
input: message="Wow, you saved me so much time! Thanks! 🎉"
expected: sentiment=4.5, should_escalate=False

# Test 2: Very negative message
input: message="I'm furious. This doesn't work at all. I want a refund."
expected: sentiment=0.2, should_escalate=True

# Test 3: Trending negative
input: [msg1_score=3.5, msg2_score=2.0, msg3_score=0.8]
expected: trend="declining", escalate_recommendation=True
```

#### Test: Escalation Decision
```python
# Test 1: Refund request
input: reason="Refund request", issue="billing", sentiment=0.15
expected: should_escalate=True, team="finance", priority="high"

# Test 2: Feature request
input: reason="Feature request for dark mode", issue="feature", sentiment=3.2
expected: should_escalate=False, action="log_feature_request"

# Test 3: Technical + 3 attempts
input: attempts=3, issue="technical", sentiment=2.1
expected: should_escalate=True, team="engineering", priority="high"
```

#### Test: Channel Adaptation
```python
# Test 1: Long message → WhatsApp
input: message=500-char text, channel="whatsapp"
expected: output length <300 chars, emojis included

# Test 2: Short message → Email
input: message="click settings", channel="email"
expected: formatted as professional email with steps

# Test 3: Character limit compliance
input: channel="whatsapp"
expected: formatted_length <= 320 (2 SMS)
```

#### Test: Customer Identification
```python
# Test 1: Email exact match
input: email="john@company.com"
expected: customer_id="CUST-ABC", confidence=0.98

# Test 2: Cross-channel merge
input: phone="+1-555-123-4567"
lookup: existing customer with same phone
expected: merge=True, unified_history=True

# Test 3: Ambiguous (multiple matches)
input: name="John" (only identifier)
expected: confidence<0.70, request_clarification=True
```

---

## Implementation Notes

### Production Requirements

1. **Performance:** All skills must execute in <2 seconds total per message
2. **Reliability:** Skills must degrade gracefully (return empty results rather than crash)
3. **Logging:** All skill decisions logged for audit and improvement
4. **Monitoring:** Metrics tracked: execution time, accuracy, error rates per skill
5. **Versioning:** Skills versioned for easy updates without breaking production

### Handoff to Stage 2

These skills definitions will be implemented as:
- **OpenAI Agents SDK @function_tool decorators** (production tools)
- **PostgreSQL schemas** (customer, message, ticket, escalation tables)
- **Integration with FastAPI** (endpoints for channel webhooks)
- **Kubernetes deployment** (async workers processing Kafka messages)

---

## Sign-Off Checklist

- [x] Knowledge Retrieval Skill defined (intent detection, KB search)
- [x] Sentiment Analysis Skill defined (5-level scale, emotion tags, escalation triggers)
- [x] Escalation Decision Skill defined (decision matrix, 10+ rules)
- [x] Channel Adaptation Skill defined (email/whatsapp/web formatting rules)
- [x] Customer Identification Skill defined (unified IDs, cross-channel merging)
- [x] Skills integration workflow documented
- [x] Test cases defined for all 5 skills
- [x] Accuracy targets specified
- [x] Handoff notes for Stage 2 production implementation

**Exercise 1.5 Complete.** Ready to transition to Stage 2 (Exercises 1.6–1.10).

---

*Last Updated: 2026-04-02*  
*Exercise Status: ✅ COMPLETE*  
*Next: Exercise 1.6 - Monitoring & Logging Infrastructure*
