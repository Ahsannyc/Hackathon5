"""
CloudFlow Agent Skills Module
Exercise 1.5: Formalized agent skills for AI employee

This module contains 5 reusable agent skills that work together to process
customer inquiries intelligently. Skills are designed to be:
- Independent and testable
- Composable (work in sequence)
- Reusable across MCP tools, core loop, and custom implementations
- Auditable (clear input/output contracts)

Skills:
1. Knowledge Retrieval Skill - Search product documentation
2. Sentiment Analysis Skill - Analyze customer emotion
3. Escalation Decision Skill - Route to specialist teams
4. Channel Adaptation Skill - Format for specific channels
5. Customer Identification & History Skill - Cross-channel tracking
"""

import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


# ============================================================================
# SKILL 1: KNOWLEDGE RETRIEVAL
# ============================================================================

class KnowledgeRetrievalSkill:
    """Search product documentation and FAQ to find relevant information."""

    def __init__(self, knowledge_base: Dict):
        """Initialize with knowledge base dictionary."""
        self.knowledge_base = knowledge_base
        self.intent_patterns = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict:
        """Load intent detection patterns."""
        return {
            "troubleshooting": {
                "keywords": ["error", "not working", "broken", "issue", "problem", "fix", "help"],
                "phrases": ["workflow not sending", "not working", "can't access"],
                "confidence": 0.85
            },
            "billing": {
                "keywords": ["plan", "upgrade", "pricing", "cost", "subscription"],
                "phrases": ["upgrade my plan", "need more executions"],
                "confidence": 0.90
            },
            "compliance": {
                "keywords": ["gdpr", "dpa", "compliance", "security", "privacy", "hipaa"],
                "phrases": ["compliance documentation", "dpa required"],
                "confidence": 0.90
            },
            "technical": {
                "keywords": ["deleted", "lost", "corrupted", "recovery", "urgent", "critical"],
                "phrases": ["accidentally deleted", "production issue"],
                "confidence": 0.95
            },
            "feature_request": {
                "keywords": ["feature", "capability", "request", "integration"],
                "phrases": ["do you have", "would be great if"],
                "confidence": 0.85
            },
            "followup": {
                "keywords": ["following up", "regarding", "earlier", "last issue"],
                "phrases": ["as we discussed", "like i mentioned"],
                "confidence": 0.90
            }
        }

    def detect_intent(self, message: str) -> Tuple[str, float]:
        """Detect intent from message with confidence score."""
        if not message or not isinstance(message, str):
            return "troubleshooting", 0.5

        message_lower = message.lower()
        best_intent = "troubleshooting"
        best_confidence = 0.70

        for intent, patterns in self.intent_patterns.items():
            keyword_match = sum(1 for kw in patterns["keywords"] if kw in message_lower)
            phrase_match = any(phrase in message_lower for phrase in patterns["phrases"])

            if phrase_match:
                confidence = patterns["confidence"]
            elif keyword_match >= 2:
                confidence = patterns["confidence"] - 0.1
            elif keyword_match >= 1:
                confidence = patterns["confidence"] - 0.2
            else:
                confidence = 0.3

            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent

        return best_intent, round(best_confidence, 2)

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search knowledge base for relevant documentation.

        Args:
            query: Customer question/issue
            max_results: Maximum results to return

        Returns:
            Dict with results, intent, confidence
        """
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Query cannot be empty",
                "error_code": "EMPTY_QUERY"
            }

        if len(query) < 5:
            return {
                "success": False,
                "error": "Query must be at least 5 characters",
                "error_code": "QUERY_TOO_SHORT"
            }

        if len(query) > 500:
            return {
                "success": False,
                "error": "Query exceeds 500 character limit",
                "error_code": "QUERY_TOO_LONG"
            }

        intent, intent_confidence = self.detect_intent(query)
        query_lower = query.lower()
        results = []

        # Search knowledge base by intent category
        kb_category = intent if intent in self.knowledge_base else "troubleshooting"
        for article_key, article_data in self.knowledge_base.get(kb_category, {}).items():
            if any(word in query_lower for word in article_key.split("_")):
                relevance_score = intent_confidence
                results.append({
                    "rank": len(results) + 1,
                    "relevance_score": round(relevance_score, 2),
                    "category": kb_category,
                    "title": article_data.get("issue", article_key),
                    "content": str(article_data),
                    "article_id": f"kb_{kb_category}_{len(results):03d}"
                })

                if len(results) >= max_results:
                    break

        return {
            "success": True,
            "intent": intent,
            "intent_confidence": intent_confidence,
            "matches_found": len(results),
            "results": results,
            "metadata": {
                "search_time_ms": 45,
                "knowledge_base_size": len(self.knowledge_base),
                "intent_detected": intent,
                "confidence": intent_confidence
            }
        }


# ============================================================================
# SKILL 2: SENTIMENT ANALYSIS
# ============================================================================

@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    sentiment_score: float
    sentiment_label: str
    confidence: float
    emotion_detected: str
    confidence_level: str
    triggers_detected: List[Dict]
    recommendation: str


class SentimentAnalysisSkill:
    """Analyze customer emotion and detect frustration level."""

    SENTIMENT_RANGES = {
        "very_negative": (0.0, 0.15),
        "negative": (0.15, 0.4),
        "neutral": (0.4, 0.7),
        "positive": (0.7, 0.9),
        "very_positive": (0.9, 1.0)
    }

    def analyze(self, message: str, conversation_history: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze sentiment of customer message.

        Args:
            message: Customer message text
            conversation_history: Previous messages for trend analysis

        Returns:
            Dict with sentiment score (0-1), label, confidence, emotion
        """
        if not message or not message.strip():
            return {
                "success": False,
                "error": "Message cannot be empty",
                "error_code": "EMPTY_MESSAGE"
            }

        message_lower = message.lower()
        triggers = []

        # Check for all-caps (urgent signal)
        if message.isupper() and len(message) > 5:
            triggers.append({
                "trigger": "all_caps",
                "confidence": 0.90,
                "raw_signal": "ALL CAPS TEXT"
            })

        # Check for very negative words
        very_negative_words = ["unacceptable", "terrible", "broken", "ridiculous", "worst"]
        if any(word in message_lower for word in very_negative_words):
            triggers.append({
                "trigger": "very_negative_word",
                "confidence": 0.95,
                "raw_signal": next(w for w in very_negative_words if w in message_lower)
            })
            sentiment_score = 0.1
            emotion = "angry"
        # Check for negative words
        elif any(word in message_lower for word in ["frustrated", "angry", "upset", "problem"]):
            triggers.append({
                "trigger": "negative_word",
                "confidence": 0.85,
                "raw_signal": "negative word detected"
            })
            sentiment_score = 0.3
            emotion = "frustrated"
        # Check for urgent keywords
        elif any(word in message_lower for word in ["urgent", "critical", "asap", "emergency"]):
            triggers.append({
                "trigger": "urgent_keyword",
                "confidence": 0.80,
                "raw_signal": "urgent keyword"
            })
            sentiment_score = 0.25
            emotion = "urgent"
        # Check for positive words
        elif any(word in message_lower for word in ["thank", "appreciate", "great", "excellent"]):
            triggers.append({
                "trigger": "positive_word",
                "confidence": 0.85,
                "raw_signal": "positive word detected"
            })
            sentiment_score = 0.8
            emotion = "satisfied"
        else:
            sentiment_score = 0.5
            emotion = "neutral"

        # Determine label from score
        sentiment_label = self._score_to_label(sentiment_score)

        # Calculate confidence
        confidence = 0.5 + (len(triggers) * 0.15)  # Confidence increases with triggers
        confidence = min(confidence, 0.95)

        # Determine confidence level
        confidence_level = "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low"

        # Analyze trend if history provided
        trend = {"previous_sentiment": None, "sentiment_change": "stable", "messages_analyzed": 1}
        if conversation_history and len(conversation_history) > 0:
            trend["messages_analyzed"] = len(conversation_history) + 1
            trend["previous_sentiment"] = self._score_to_label(0.5)  # Placeholder
            if sentiment_score < 0.4:
                trend["sentiment_change"] = "decline"
            elif sentiment_score > 0.6:
                trend["sentiment_change"] = "improve"

        # Recommendation
        recommendation = "escalate" if sentiment_score < 0.3 else "monitor" if sentiment_score < 0.5 else "proceed"

        return {
            "success": True,
            "sentiment_score": round(sentiment_score, 2),
            "sentiment_label": sentiment_label,
            "confidence": round(confidence, 2),
            "emotion_detected": emotion,
            "confidence_level": confidence_level,
            "triggers_detected": triggers,
            "trend": trend,
            "recommendation": recommendation
        }

    def _score_to_label(self, score: float) -> str:
        """Convert score to sentiment label."""
        for label, (min_score, max_score) in self.SENTIMENT_RANGES.items():
            if min_score <= score < max_score:
                return label
        return "neutral"


# ============================================================================
# SKILL 3: ESCALATION DECISION
# ============================================================================

class EscalationDecisionSkill:
    """Determine whether customer issue requires human intervention."""

    ESCALATION_CATEGORIES = {
        "urgent": {
            "team": "Technical Support",
            "sla_minutes": 15,
            "triggers": ["critical", "urgent", "asap", "production"]
        },
        "compliance": {
            "team": "Legal/Compliance Team",
            "sla_minutes": 120,
            "triggers": ["gdpr", "dpa", "compliance", "hipaa"]
        },
        "billing": {
            "team": "Finance Team",
            "sla_minutes": 240,
            "triggers": ["refund", "money back", "credit", "compensation"]
        },
        "data_loss": {
            "team": "Technical Recovery Team",
            "sla_minutes": 30,
            "triggers": ["deleted", "lost data", "corrupted", "recovery"]
        },
        "angry_customer": {
            "team": "Priority Support",
            "sla_minutes": 30,
            "triggers": ["unacceptable", "terrible", "worst", "ridiculous"]
        },
        "followup_stalled": {
            "team": "General Support",
            "sla_minutes": 120,
            "triggers": []
        }
    }

    def decide(self, conversation_context: str, sentiment_score: float,
               sentiment_trend: List[str], customer_history: Dict[str, Any],
               detected_intent: str) -> Dict[str, Any]:
        """
        Determine if escalation is needed.

        Args:
            conversation_context: Full conversation history
            sentiment_score: Score 0.0-1.0
            sentiment_trend: List of previous sentiments
            customer_history: Customer state dict
            detected_intent: Intent type

        Returns:
            Dict with should_escalate, category, team, reason
        """
        if not isinstance(sentiment_score, (int, float)) or sentiment_score < 0 or sentiment_score > 1:
            return {
                "success": False,
                "error": "Invalid sentiment score (must be 0.0-1.0)",
                "error_code": "INVALID_SENTIMENT_SCORE"
            }

        escalation_triggers = []
        escalation_category = None
        confidence = 0.5

        # Check sentiment triggers
        if sentiment_score < 0.15:
            escalation_triggers.append({
                "trigger_type": "sentiment",
                "trigger_value": sentiment_score,
                "weight": "high",
                "reason": "Very negative sentiment detected"
            })
            escalation_category = "angry_customer"
            confidence = 0.95

        # Check intent triggers
        if detected_intent == "compliance":
            escalation_triggers.append({
                "trigger_type": "intent",
                "trigger_value": detected_intent,
                "weight": "high",
                "reason": "Compliance issues require legal review"
            })
            escalation_category = "compliance"
            confidence = 0.95

        elif detected_intent == "technical" and sentiment_score < 0.4:
            escalation_triggers.append({
                "trigger_type": "intent",
                "trigger_value": detected_intent,
                "weight": "high",
                "reason": "Technical issues with negative sentiment"
            })
            escalation_category = "urgent"
            confidence = 0.85

        # Check if no escalation needed
        should_escalate = len(escalation_triggers) > 0

        if not escalation_category:
            escalation_category = "urgent" if should_escalate else None

        if escalation_category:
            category_info = self.ESCALATION_CATEGORIES.get(escalation_category, {})
        else:
            category_info = {}

        return {
            "success": True,
            "should_escalate": should_escalate,
            "escalation_category": escalation_category,
            "confidence": round(confidence, 2),
            "reason": "Escalation required due to " + (escalation_category or "review"),
            "assigned_team": category_info.get("team", "General Support"),
            "estimated_response_time_minutes": category_info.get("sla_minutes", 120),
            "escalation_triggers": escalation_triggers,
            "customer_risk_level": "high" if sentiment_score < 0.3 else "medium" if sentiment_score < 0.5 else "low",
            "notes": f"Route to {category_info.get('team', 'General Support')} for review"
        }


# ============================================================================
# SKILL 4: CHANNEL ADAPTATION
# ============================================================================

class ChannelAdaptationSkill:
    """Format and tone-adjust responses based on communication channel."""

    CHANNEL_GUIDELINES = {
        "email": {
            "greeting": "Hi {name}!",
            "opening": "Great question.",
            "closing": "Best regards,\nCloudFlow Support Team\nsupport@cloudflow.io",
            "tone": "professional, helpful",
            "min_chars": 300,
            "max_chars": 500
        },
        "whatsapp": {
            "greeting": "Hi {name}!",
            "opening": "Great question.",
            "closing": "- CloudFlow Team",
            "tone": "casual, friendly",
            "min_chars": 150,
            "max_chars": 300
        },
        "web_form": {
            "greeting": "Hi {name}!",
            "opening": "Great question.",
            "closing": "Best regards,\nCloudFlow Team",
            "tone": "semi-formal",
            "min_chars": 250,
            "max_chars": 400
        }
    }

    def adapt(self, raw_response: str, target_channel: str,
              customer_name: str, sentiment_score: float = 0.5) -> Dict[str, Any]:
        """
        Adapt response for specific channel.

        Args:
            raw_response: Unformatted response text
            target_channel: email, whatsapp, or web_form
            customer_name: Customer name for personalization
            sentiment_score: For empathy adjustment

        Returns:
            Dict with formatted_response, tone, character_count, adaptations
        """
        if target_channel not in self.CHANNEL_GUIDELINES:
            return {
                "success": False,
                "error": f"Invalid channel. Must be one of: email, whatsapp, web_form",
                "error_code": "INVALID_CHANNEL",
                "valid_channels": ["email", "whatsapp", "web_form"]
            }

        if not raw_response or not raw_response.strip():
            return {
                "success": False,
                "error": "Response cannot be empty",
                "error_code": "EMPTY_RESPONSE"
            }

        guidelines = self.CHANNEL_GUIDELINES[target_channel]
        adaptations = []

        # Personalization
        first_name = customer_name.split()[0] if customer_name else "there"
        greeting = guidelines["greeting"].format(name=first_name)
        adaptations.append({
            "type": "personalization",
            "detail": f"Added customer name ({first_name}) in greeting"
        })

        # Empathy adjustment
        if sentiment_score < 0.2:
            opening = "I sincerely apologize for your frustration. "
            adaptations.append({
                "type": "empathy",
                "detail": "Added apology for very negative sentiment"
            })
        elif sentiment_score < 0.4:
            opening = "I understand your frustration. "
            adaptations.append({
                "type": "empathy",
                "detail": "Added empathy for negative sentiment"
            })
        else:
            opening = guidelines["opening"]

        # Format response
        formatted_response = f"{greeting}\n\n{opening} {raw_response}\n\n{guidelines['closing']}"

        # Character count
        char_count = len(formatted_response)

        adaptations.append({
            "type": "formality",
            "detail": f"{guidelines['tone']} tone applied"
        })

        adaptations.append({
            "type": "signature",
            "detail": f"Added {target_channel} signature"
        })

        return {
            "success": True,
            "channel": target_channel,
            "formatted_response": formatted_response,
            "tone": guidelines["tone"],
            "character_count": char_count,
            "estimated_read_time_seconds": max(15, char_count // 20),
            "brand_guidelines_applied": guidelines,
            "adaptations": adaptations
        }


# ============================================================================
# SKILL 5: CUSTOMER IDENTIFICATION & HISTORY
# ============================================================================

class CustomerIdentificationSkill:
    """Identify customers uniquely across channels and retrieve conversation history."""

    def __init__(self, memory):
        """Initialize with conversation memory."""
        self.memory = memory

    def identify_and_fetch_history(self, identifier: str, identifier_type: str,
                                   customer_name: Optional[str] = None,
                                   customer_plan: Optional[str] = None) -> Dict[str, Any]:
        """
        Identify customer and retrieve their history.

        Args:
            identifier: Email or phone number
            identifier_type: 'email' or 'phone'
            customer_name: Name if new customer
            customer_plan: Plan type if new customer

        Returns:
            Dict with customer_id, history, stats
        """
        if not identifier or not identifier.strip():
            return {
                "success": False,
                "error": "Identifier cannot be empty",
                "error_code": "EMPTY_IDENTIFIER"
            }

        if identifier_type not in ["email", "phone"]:
            return {
                "success": False,
                "error": f"Invalid identifier type. Must be 'email' or 'phone'",
                "error_code": "INVALID_IDENTIFIER_TYPE"
            }

        # Try to find existing customer
        customer_id = None
        if identifier_type == "email":
            customer_id = self.memory.email_to_id.get(identifier)
        elif identifier_type == "phone":
            customer_id = self.memory.phone_to_id.get(identifier)

        # If found, return with history
        if customer_id:
            customer_state = self.memory.get_customer_state(customer_id)
            if customer_state:
                return {
                    "success": True,
                    "customer_found": True,
                    "customer_id": customer_id,
                    "customer_name": customer_state.customer_name,
                    "customer_plan": customer_state.customer_plan,
                    "email": customer_state.email,
                    "phone": customer_state.phone,
                    "channels_used": customer_state.channels_used,
                    "original_channel": customer_state.original_channel,
                    "conversation_stats": {
                        "total_messages": customer_state.total_messages,
                        "first_contact": customer_state.conversation_history[0].timestamp if customer_state.conversation_history else None,
                        "last_contact": customer_state.last_contact,
                        "sentiment_trend": customer_state.sentiment_trend,
                        "current_sentiment": customer_state.current_sentiment,
                        "topics_discussed": customer_state.topics_discussed,
                        "resolution_status": customer_state.resolution_status,
                        "escalation_count": customer_state.escalation_count
                    },
                    "conversation_history": [
                        asdict(msg) for msg in customer_state.conversation_history[-10:]
                    ],
                    "context_summary": f"{customer_state.customer_name} ({customer_state.customer_plan}) - {customer_state.total_messages} messages, current sentiment: {customer_state.current_sentiment}"
                }

        # Create new customer if not found
        if not customer_name or not customer_plan:
            return {
                "success": False,
                "error": "New customer requires name and plan",
                "error_code": "MISSING_NEW_CUSTOMER_DATA"
            }

        email = identifier if identifier_type == "email" else None
        phone = identifier if identifier_type == "phone" else None

        new_customer_id = self.memory.find_or_create_customer(
            customer_name=customer_name,
            customer_plan=customer_plan,
            email=email,
            phone=phone
        )

        return {
            "success": True,
            "customer_found": False,
            "customer_created": True,
            "customer_id": new_customer_id,
            "customer_name": customer_name,
            "customer_plan": customer_plan,
            "email": email,
            "phone": phone,
            "channels_used": [],
            "original_channel": None,
            "conversation_stats": {
                "total_messages": 0,
                "first_contact": None,
                "last_contact": None,
                "sentiment_trend": [],
                "current_sentiment": "neutral",
                "topics_discussed": [],
                "resolution_status": "pending",
                "escalation_count": 0
            },
            "conversation_history": [],
            "context_summary": f"New customer: {customer_name} ({customer_plan})"
        }


# ============================================================================
# SKILL REGISTRY (For easy access to all skills)
# ============================================================================

class AgentSkillsRegistry:
    """Registry providing access to all agent skills."""

    def __init__(self, knowledge_base: Dict, memory):
        """Initialize skill registry with dependencies."""
        self.knowledge_retrieval = KnowledgeRetrievalSkill(knowledge_base)
        self.sentiment_analysis = SentimentAnalysisSkill()
        self.escalation_decision = EscalationDecisionSkill()
        self.channel_adaptation = ChannelAdaptationSkill()
        self.customer_identification = CustomerIdentificationSkill(memory)

    def get_skill(self, skill_name: str):
        """Get skill by name."""
        skills = {
            "knowledge_retrieval": self.knowledge_retrieval,
            "sentiment_analysis": self.sentiment_analysis,
            "escalation_decision": self.escalation_decision,
            "channel_adaptation": self.channel_adaptation,
            "customer_identification": self.customer_identification
        }
        return skills.get(skill_name)

    def list_skills(self) -> List[str]:
        """List all available skills."""
        return [
            "knowledge_retrieval",
            "sentiment_analysis",
            "escalation_decision",
            "channel_adaptation",
            "customer_identification"
        ]
