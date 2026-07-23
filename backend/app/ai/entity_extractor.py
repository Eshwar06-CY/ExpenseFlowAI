"""
Entity Extractor Module - ExpenseFlowAI Multi-Stage Reasoning Pipeline

Extracts structured financial entities (goal name, target amount, timeline, income,
expenses, current savings, payment mode) from user prompts and conversation turns.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntities:
    goal_name: Optional[str] = None
    target_amount: Optional[float] = None
    timeline_months: Optional[int] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    current_savings: Optional[float] = None
    existing_loans: Optional[float] = None
    payment_mode: Optional[str] = None  # "cash", "emi"
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def has_goal_basics(self) -> bool:
        return self.target_amount is not None or self.goal_name is not None

    def is_fully_specified_for_plan() -> bool:
        """
        Returns True if income, expenses, savings, and timeline are specified or present.
        """
        return bool(
            self.target_amount and
            self.timeline_months and
            self.monthly_income and
            self.monthly_expenses
        )


class EntityExtractor:
    @classmethod
    def parse_amount(cls, text: str) -> Optional[float]:
        """
        Parses amounts like '2 lakh', '2 lakhs', '1.5 lakh', '50k', '₹200000', '$2,000'.
        """
        text_lower = text.lower()

        # Check Lakh / Lakhs
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakhs?|l\b)", text_lower)
        if lakh_match:
            val = float(lakh_match.group(1))
            return val * 100000.0

        # Check K (Thousands)
        k_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:k\b|thousand)", text_lower)
        if k_match:
            val = float(k_match.group(1))
            return val * 1000.0

        # Check Raw Currency
        num_match = re.search(r"(?:₹|\$|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)", text_lower)
        if num_match:
            raw = num_match.group(1).replace(",", "")
            try:
                val = float(raw)
                if val > 100:  # Ignore trivial numbers
                    return val
            except ValueError:
                pass

        return None

    @classmethod
    def parse_timeline(cls, text: str) -> Optional[int]:
        """
        Parses timeline into months (e.g. '2 years' -> 24, '6 months' -> 6).
        """
        text_lower = text.lower()

        # Check Years
        year_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", text_lower)
        if year_match:
            yrs = float(year_match.group(1))
            return int(yrs * 12)

        # Check Months
        month_match = re.search(r"(\d+)\s*(?:months?|mos?)", text_lower)
        if month_match:
            return int(month_match.group(1))

        return None

    @classmethod
    def extract(
        cls,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> ExtractedEntities:
        """
        Extracts entities across the user message and prior conversation turns.
        """
        combined_text = user_message or ""
        if chat_history:
            turns = [m.get("content", "") for m in chat_history[-6:]]
            combined_text = "\n".join(turns) + "\n" + combined_text

        entities = ExtractedEntities()
        text_lower = user_message.lower()

        # Goal & Category Detection
        comb_lower = combined_text.lower()
        if "bike" in comb_lower:
            entities.goal_name = "Buy Bike"
            entities.category = "Vehicle"
        elif "car" in comb_lower:
            entities.goal_name = "Buy Car"
            entities.category = "Vehicle"
        elif "house" in comb_lower or "home" in comb_lower:
            entities.goal_name = "Buy House"
            entities.category = "Real Estate"
        elif "phone" in comb_lower or "laptop" in comb_lower:
            entities.goal_name = "Buy Gadget"
            entities.category = "Electronics"

        # Amount & Timeline
        entities.target_amount = cls.parse_amount(combined_text)
        entities.timeline_months = cls.parse_timeline(combined_text)

        # Payment Mode
        if "emi" in text_lower or "loan" in text_lower:
            entities.payment_mode = "emi"
        elif "cash" in text_lower or "full" in text_lower:
            entities.payment_mode = "cash"

        # Monthly Income
        income_match = re.search(r"(?:income|salary|earn|earning)\s*(?:is|of|:)?\s*(\d+(?:\.\d+)?(?:\s*k|\s*lakh)?)", text_lower)
        if income_match:
            entities.monthly_income = cls.parse_amount(income_match.group(0))

        # Monthly Expenses
        expense_match = re.search(r"(?:expenses?|spend|spending)\s*(?:is|of|:)?\s*(\d+(?:\.\d+)?(?:\s*k|\s*lakh)?)", text_lower)
        if expense_match:
            entities.monthly_expenses = cls.parse_amount(expense_match.group(0))

        # Current Savings
        savings_match = re.search(r"(?:savings?|reserve)\s*(?:is|of|:)?\s*(\d+(?:\.\d+)?(?:\s*k|\s*lakh)?)", text_lower)
        if savings_match:
            entities.current_savings = cls.parse_amount(savings_match.group(0))

        logger.info("[EntityExtractor] Extracted: %s", entities.to_dict())
        return entities
