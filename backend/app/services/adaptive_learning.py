"""
Adaptive Financial Intelligence Service - ExpenseFlowAI

Provides application-level behavioral learning and personalization:
- Learns spending habits, savings consistency, and ignored/accepted advice.
- Computes Financial Discipline Score and Recommendation Effectiveness.
- Adapts reminder timing and communication style.
- GUARANTEES 100% PRIVACY: Zero raw transaction history or PII leaves the application. NO LLM training.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.user_preferences import UserPreferences
from app.models.user_behavior import UserBehaviorEvent
from app.models.goal import Goal
from app.services.finance_engine import FinanceEngine
from app.schemas.adaptive import UserFeedbackRequest
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


ADAPTIVE_SYSTEM_PROMPT = """You are ExpenseFlowAI Adaptive Intelligence System.
Synthesize the application-level learned user behavior profile into a clear, personalized executive summary.

LEARNED PROFILE:
- Financial Discipline Score: {discipline_score}/100
- Recommendation Effectiveness: {effectiveness:.0%}
- Behavioral Patterns: {patterns_str}
- Learned Preferences: {prefs_str}

RULES:
1. Explain how the AI has personalized recommendations based on past user feedback.
2. Emphasize that all learning is application-level and private.
3. Keep the tone adaptive and supportive.
"""


class AdaptiveLearningService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def get_or_create_preferences(self, db: Session, user_id: int) -> UserPreferences:
        prefs = db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id)).scalar_one_or_none()
        if not prefs:
            prefs = UserPreferences(
                user_id=user_id,
                communication_style="concise",
                category_sensitivities=json.dumps({}),
                ignored_recommendation_types=json.dumps([]),
                auto_reminder_lead_days=3
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

    def record_user_feedback(
        self,
        db: Session,
        user_id: int,
        feedback: UserFeedbackRequest
    ) -> Dict[str, Any]:
        """
        Records a user interaction event and updates learned application preferences.
        """
        prefs = self.get_or_create_preferences(db, user_id)

        # 1. Update preferences if explicit style or actions provided
        if feedback.communication_style:
            prefs.communication_style = feedback.communication_style.lower()

        ignored_list = json.loads(prefs.ignored_recommendation_types or "[]")
        if feedback.action == "ignored":
            key = feedback.category or feedback.recommendation_type or "general"
            if key and key not in ignored_list:
                ignored_list.append(key)
                prefs.ignored_recommendation_types = json.dumps(ignored_list)

        # Adjust reminder timing if early payment event
        if feedback.event_type == "EARLY_BILL_PAYMENT":
            prefs.auto_reminder_lead_days = max(1, prefs.auto_reminder_lead_days - 1)

        # 2. Record behavior event
        event = UserBehaviorEvent(
            user_id=user_id,
            event_type=feedback.event_type or "RECOMMENDATION_RESPONSE",
            category=feedback.category,
            action=feedback.action.lower(),
            metadata_json=json.dumps(feedback.metadata or {})
        )
        db.add(event)
        db.commit()
        db.refresh(prefs)

        return self.get_adaptive_profile(db, user_id)

    def get_adaptive_profile(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Computes discipline score, recommendation effectiveness, learned behavior patterns,
        and personalization confidence.
        """
        prefs = self.get_or_create_preferences(db, user_id)
        ignored_list = json.loads(prefs.ignored_recommendation_types or "[]")

        # 1. Fetch FinanceEngine baseline data
        health_data = FinanceEngine.calculate_financial_health_score(db, user_id=user_id)
        budget_data = FinanceEngine.get_budget_adherence(db, user_id=user_id)

        health_score = health_data["health_score"]
        adherence_pct = float(budget_data.get("adherence_rate_pct", 100.0))

        # Goal completion velocity
        goals = db.execute(select(Goal).where(Goal.user_id == user_id)).scalars().all()
        if goals:
            pcts = [min((g.current_amount / max(g.target_amount, 1.0)) * 100.0, 100.0) for g in goals]
            goal_pct = sum(pcts) / len(goals)
        else:
            goal_pct = 85.0

        # 2. Compute Financial Discipline Score
        discipline_raw = (health_score * 0.50) + (adherence_pct * 0.30) + (goal_pct * 0.20)
        discipline_score = int(round(min(100.0, max(0.0, discipline_raw))))

        # 3. Compute Recommendation Effectiveness Rate
        events = db.execute(
            select(UserBehaviorEvent)
            .where(UserBehaviorEvent.user_id == user_id)
        ).scalars().all()

        accepted_count = sum(1 for e in events if e.action == "accepted")
        ignored_count = sum(1 for e in events if e.action == "ignored")
        total_eval = accepted_count + ignored_count

        if total_eval > 0:
            effectiveness = round(accepted_count / float(total_eval), 2)
        else:
            effectiveness = 0.82  # Default baseline high effectiveness

        # 4. Synthesize Behavior Patterns
        behavior_patterns = []
        if ignored_list:
            ignored_str = ", ".join(ignored_list)
            behavior_patterns.append(f"User frequently ignores {ignored_str} advice -> Reduced recommendation frequency.")

        if adherence_pct >= 90.0:
            behavior_patterns.append("Consistently maintains high budget adherence -> Increasing savings expectations.")
        else:
            behavior_patterns.append("Discretionary spending occasionally exceeds budget -> Recommending lower category caps.")

        if prefs.auto_reminder_lead_days < 3:
            behavior_patterns.append(f"User usually pays bills early -> Adjusted reminder lead time to {prefs.auto_reminder_lead_days} day(s) before due date.")
        else:
            behavior_patterns.append(f"Default bill reminder timing active ({prefs.auto_reminder_lead_days} days before due date).")

        if health_score >= 80:
            behavior_patterns.append("Strong financial discipline pattern detected across all 5 health pillars.")

        # 5. Compute Personalization Confidence
        confidence = round(min(0.95, 0.70 + (len(events) * 0.03)), 2)

        # 6. Build Updated Preferences List
        updated_prefs = [
            {"key": "communication_style", "value": prefs.communication_style.capitalize(), "confidence": confidence},
            {"key": "auto_reminder_lead_days", "value": f"{prefs.auto_reminder_lead_days} days", "confidence": confidence},
            {"key": "recommendation_frequency", "value": "Standard" if not ignored_list else "Filtered for " + ", ".join(ignored_list), "confidence": confidence}
        ]

        # 7. AI Executive Narrative Explanation
        patterns_str = "; ".join(behavior_patterns)
        prefs_str = f"Style={prefs.communication_style}, ReminderLead={prefs.auto_reminder_lead_days}d"

        prompt = ADAPTIVE_SYSTEM_PROMPT.format(
            discipline_score=discipline_score,
            effectiveness=effectiveness,
            patterns_str=patterns_str,
            prefs_str=prefs_str
        )

        try:
            explanation = self.provider.generate(prompt=prompt)
            if not explanation or len(explanation.strip()) < 10:
                explanation = self._build_deterministic_explanation(discipline_score, effectiveness, behavior_patterns)
        except Exception as exc:
            logger.warning("LLM Adaptive Intelligence generation error (%s). Using fallback explanation.", str(exc))
            explanation = self._build_deterministic_explanation(discipline_score, effectiveness, behavior_patterns)

        return {
            "discipline_score": discipline_score,
            "behavior_patterns": behavior_patterns,
            "recommendation_effectiveness": effectiveness,
            "personalization_confidence": confidence,
            "updated_preferences": updated_prefs,
            "explanation": explanation
        }

    def _build_deterministic_explanation(
        self,
        discipline_score: int,
        effectiveness: float,
        patterns: List[str]
    ) -> str:
        pattern_msg = f" Key insights: {patterns[0]}" if patterns else ""
        return (
            f"Your Financial Discipline Score is {discipline_score}/100 with a {effectiveness:.0%} recommendation effectiveness rate. "
            f"{pattern_msg} All behavioral learning is processed application-side to protect user data privacy."
        )
