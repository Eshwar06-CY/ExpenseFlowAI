"""
Intent Classifier Module - ExpenseFlowAI Multi-Stage Reasoning Pipeline

Classifies user messages into granular intent types with confidence scores.
Determines whether financial data from FinanceEngine is required.
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    IDENTITY = "identity"
    HELP = "help"
    CAPABILITIES = "help"
    GENERAL_QA = "general_qa"
    FINANCIAL_ANALYSIS = "financial_analysis"
    SPENDING_ANALYSIS = "spending_analysis"
    FINANCIAL_QUERY = "spending_analysis"
    INCOME_ANALYSIS = "income_analysis"
    BUDGET_ANALYSIS = "budget_analysis"
    PURCHASE_DECISION = "purchase_decision"
    FINANCIAL_ADVICE = "purchase_decision"
    GOAL_PLANNING = "goal_planning"
    FINANCIAL_FORECAST = "financial_forecast"
    INVESTMENT = "investment"
    LOAN = "loan"
    EMI = "emi"
    INSURANCE = "insurance"
    TAX = "tax"
    SAVINGS_PLAN = "savings_plan"
    SIMULATION = "simulation"
    WHAT_IF_ANALYSIS = "what_if_analysis"
    FOLLOW_UP = "follow_up"
    MEMORY_REFERENCE = "memory_reference"
    GOODBYE = "goodbye"
    JOKE = "joke"
    UNKNOWN = "unknown"

    @property
    def requires_financial_data(self) -> bool:
        """
        FinanceEngine calculations and DB metrics are injected ONLY when required.
        """
        return self in (
            IntentType.FINANCIAL_ANALYSIS,
            IntentType.SPENDING_ANALYSIS,
            IntentType.INCOME_ANALYSIS,
            IntentType.BUDGET_ANALYSIS,
            IntentType.PURCHASE_DECISION,
            IntentType.GOAL_PLANNING,
            IntentType.FINANCIAL_FORECAST,
            IntentType.INVESTMENT,
            IntentType.LOAN,
            IntentType.EMI,
            IntentType.SAVINGS_PLAN,
            IntentType.SIMULATION,
            IntentType.WHAT_IF_ANALYSIS,
        )


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    requires_financial_data: bool
    description: str = ""

    def __iter__(self):
        return iter((self.intent, self.requires_financial_data))


class IntentClassifier:
    PATTERNS: List[Tuple[IntentType, float, List[str]]] = [
        # Greeting
        (IntentType.GREETING, 0.95, [
            r"^\b(hi|hello|hey|heyy|heya|yo|greetings|namaste|hola)\b",
            r"^\b(good\s+(morning|afternoon|evening|day|night))\b",
            r"^\b(what'?s\s+up|sup)\b"
        ]),

        # Small Talk
        (IntentType.SMALL_TALK, 0.90, [
            r"^\b(how\s+are\s+you|how\s+do\s+you\s+do|how'?s\s+it\s+going|how\s+are\s+things)\b",
            r"^\b(thank\s+you|thanks|thx|thank\s+you\s+so\s+much|many\s+thanks)\b",
            r"^\b(cool|awesome|great|nice|perfect|got\t?it|understoo?d|okay?|ok|sweet)\b",
            r"^\b(good\s+job|well\s+done|nice\s+work)\b"
        ]),

        # Joke
        (IntentType.JOKE, 0.95, [
            r"\b(tell\s+me\s+a\s+joke|make\s+me\s+laugh|funny\s+story|joke)\b"
        ]),

        # Goodbye
        (IntentType.GOODBYE, 0.95, [
            r"\b(bye|goodbye|see\s+you|talk\s+to\s+you\s+later|cya|exit|quit)\b"
        ]),

        # Identity
        (IntentType.IDENTITY, 0.95, [
            r"\b(who\s+are\s+you|what\s+is\s+your\s+name|your\s+identity|who\s+made\s+you|who\s+created\s+you)\b",
            r"\b(tell\s+me\s+about\s+yourself|describe\s+yourself|what\s+are\s+you)\b"
        ]),

        # Help / Capabilities
        (IntentType.HELP, 0.95, [
            r"\b(what\s+can\s+you\s+do|how\s+can\s+you\s+help|what\s+are\s+your\s+features|what\s+services)\b",
            r"^\b(help|help\s+me|options|capabilities|commands|menu)\b"
        ]),

        # Goal Planning
        (IntentType.GOAL_PLANNING, 0.92, [
            r"\b(financial\s*plan|create\s+a\s+plan|build\s+a\s+roadmap|goal\s+planning|save\s+for|target\s+savings)\b",
            r"\b(saving\s+goal|target\s+amount|timeline|buying\s+in\s+\d+\s*(years?|months?))\b"
        ]),

        # Purchase Decision
        (IntentType.PURCHASE_DECISION, 0.92, [
            r"\b(can\s+i\s+(buy|afford|purchase)|should\s+i\s+(buy|afford|purchase))\b",
            r"\b(want\s+to\s+buy|planning\s+to\s+buy|thinking\s+of\s+buying)\b",
            r"\b(bike|car|house|phone|laptop|vacation|trip|gadget|watch|home)\b"
        ]),

        # Spending Analysis
        (IntentType.SPENDING_ANALYSIS, 0.90, [
            r"\b(spend|spent|spending|expense|expenses|cost|outflow|cashflow|top\s+spending|highest\s+expense)\b",
            r"\b(category\s+spending|discretionary\s+outflow|spending\s+breakdown|expense\s+summary)\b"
        ]),

        # Financial Advice & Optimization
        (IntentType.FINANCIAL_ADVICE, 0.90, [
            r"\b(can\s+i\s+(buy|afford|purchase)|should\s+i\s+(buy|afford|purchase))\b",
            r"\b(how\s+(can|do)\s+i\s+(save|optimize|reduce|cut|improve)|advice|recommendation|strategy|coaching)\b",
            r"\b(financial\s*goal|investment|plan|planning|retire|emergency\s*fund)\b"
        ]),

        # Budget Analysis
        (IntentType.BUDGET_ANALYSIS, 0.90, [
            r"\b(budget\s+adherence|am\s+i\s+over\s+budget|budget\s+status|budget\s+limit|category\s+budgets)\b"
        ]),

        # Financial Forecast
        (IntentType.FINANCIAL_FORECAST, 0.90, [
            r"\b(forecast|projection|90-day|cashflow\s+forecast|liquid\s+balance\s+in\s+3\s+months)\b"
        ]),

        # Financial Analysis
        (IntentType.FINANCIAL_ANALYSIS, 0.85, [
            r"\b(financial\s*health|health\s*score|reserve\s*months|emergency\s*fund|overall\s*finances)\b"
        ])
    ]

    @classmethod
    def classify(
        cls,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResult:
        """
        Classifies incoming user message into structured IntentResult.
        """
        text = (user_message or "").strip()
        text_lower = text.lower()

        if not text_lower:
            return IntentResult(
                intent=IntentType.GREETING,
                confidence=1.0,
                requires_financial_data=False,
                description="Empty prompt defaulted to greeting"
            )

        # Match regex patterns
        for intent_type, confidence, patterns in cls.PATTERNS:
            for pat in patterns:
                if re.search(pat, text_lower):
                    logger.info("[IntentClassifier] Matched %s (conf: %.2f) for '%s'", intent_type.value, confidence, text)
                    return IntentResult(
                        intent=intent_type,
                        confidence=confidence,
                        requires_financial_data=intent_type.requires_financial_data,
                        description=f"Matched pattern: {pat}"
                    )

        # Check multi-turn context
        if chat_history and len(chat_history) > 0:
            last_msg = chat_history[-1].get("content", "").lower()
            if any(k in text_lower for k in ["explain", "why", "how", "what about", "more", "next"]):
                if any(k in last_msg for k in ["spend", "budget", "savings", "income", "bike", "plan"]):
                    return IntentResult(
                        intent=IntentType.FOLLOW_UP,
                        confidence=0.80,
                        requires_financial_data=True,
                        description="Follow-up to previous financial topic"
                    )

        # General QA / Conversational Chatter
        return IntentResult(
            intent=IntentType.GENERAL_QA,
            confidence=0.70,
            requires_financial_data=False,
            description="General conversational query"
        )
