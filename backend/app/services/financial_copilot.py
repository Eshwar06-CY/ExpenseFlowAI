"""
AI Financial Copilot Service - ExpenseFlowAI

Orchestrates FinanceEngine, AIFinancialCoachService, AIAnomalyDetectorService,
and goal tracking to produce a unified, proactive Daily Financial Briefing.

The AI DOES NOT perform mathematical calculations itself. All numbers, scores,
bill due dates, and goal percentages are computed directly from FinanceEngine.
"""

from datetime import datetime, timezone
import json
import logging
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.services.finance_engine import FinanceEngine
from app.services.ai_financial_coach import AIFinancialCoachService
from app.services.anomaly_detector import AIAnomalyDetectorService
from app.services.goal_planner import AIGoalPlannerService
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.user import User

logger = logging.getLogger(__name__)


COPILOT_SYSTEM_PROMPT = """You are ExpenseFlowAI Financial Copilot. You produce proactive, encouraging daily financial briefings based on pre-calculated user metrics.

RULES:
1. USE ONLY SUPPLIED METRICS: Never invent balances or fake scores.
2. OUTPUT STRICT JSON ONLY: You MUST respond with a single valid JSON object containing:
   - "greeting": A warm, personalized greeting (e.g. "Good Morning 👋").
   - "highlights": A list of 2-3 key positive financial achievements.
   - "alerts": A list of 1-3 urgent alerts or warnings.
   - "recommendations": A list of 3 prioritized daily actionable recommendations.
   - "encouragement": A motivational closing sentence.
"""


class AIFinancialCopilotService:
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        coach_service: Optional[AIFinancialCoachService] = None,
        anomaly_service: Optional[AIAnomalyDetectorService] = None,
        goal_service: Optional[AIGoalPlannerService] = None
    ):
        self.provider = provider or get_llm_provider()
        self.coach_service = coach_service or AIFinancialCoachService(provider=self.provider)
        self.anomaly_service = anomaly_service or AIAnomalyDetectorService(provider=self.provider)
        self.goal_service = goal_service or AIGoalPlannerService(provider=self.provider)

    def generate_daily_briefing(
        self,
        db: Session,
        user_id: int,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Orchestrates metrics from FinanceEngine, Coach, Anomaly Detector, and Goals
        to compile a comprehensive Daily Financial Briefing.
        """
        # 1. Fetch FinanceEngine Dashboard Summary
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        health_score = summary.get("health_score", 0)
        health_status = summary.get("health_status", "N/A")

        # 2. Safely call Coaching Service
        coach_data = {}
        try:
            coach_data = self.coach_service.generate_coaching_report(db, user_id=user_id, period=period)
        except Exception as exc:
            logger.warning("Copilot coaching sub-service error (%s).", str(exc))

        # 3. Safely call Anomaly Detector Service
        anomaly_data = {}
        try:
            anomaly_data = self.anomaly_service.detect_anomalies(db, user_id=user_id, period=period)
        except Exception as exc:
            logger.warning("Copilot anomaly sub-service error (%s).", str(exc))

        # 4. Fetch Goal Updates
        goal_updates = self._fetch_goal_updates(db, user_id)

        # 5. Fetch Upcoming Events & Bills
        upcoming_events = self._fetch_upcoming_events(db, user_id)

        # 6. Build LLM prompt
        prompt = self._build_copilot_prompt(summary, coach_data, anomaly_data, goal_updates, upcoming_events)

        try:
            llm_response = self.provider.generate(prompt=prompt, system_prompt=COPILOT_SYSTEM_PROMPT)
            parsed_json = self._extract_json(llm_response)
            if parsed_json:
                return {
                    "greeting": str(parsed_json.get("greeting", "Good Morning 👋")),
                    "health_score": health_score,
                    "health_status": health_status,
                    "highlights": self._ensure_list(parsed_json.get("highlights"), coach_data.get("strengths", ["Active financial tracking established."])),
                    "alerts": self._ensure_list(parsed_json.get("alerts"), [a.get("message") for a in anomaly_data.get("anomalies", []) if a.get("message")]),
                    "recommendations": self._ensure_list(parsed_json.get("recommendations"), coach_data.get("recommendations", ["Review spending limits."])),
                    "goal_updates": goal_updates,
                    "upcoming_events": upcoming_events,
                    "encouragement": str(parsed_json.get("encouragement", "You are making steady progress towards your financial targets!")),
                }
        except Exception as exc:
            logger.warning("LLM copilot briefing generation failed (%s). Using deterministic copilot.", str(exc))

        # Deterministic Fallback
        return self._build_deterministic_briefing(health_score, health_status, coach_data, anomaly_data, goal_updates, upcoming_events)

    def _fetch_goal_updates(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        goals = db.execute(select(Goal).where(Goal.user_id == user_id)).scalars().all()
        updates = []
        for g in goals:
            target = max(g.target_amount, 1.0)
            current = max(g.current_amount or 0.0, 0.0)
            pct = round(min((current / target) * 100.0, 100.0), 1)
            status_str = "ON_TRACK" if pct >= 50.0 else "IN_PROGRESS"
            if pct >= 100.0:
                status_str = "ALREADY_ACHIEVED"
            updates.append({
                "goal_name": g.name,
                "target_amount": g.target_amount,
                "current_saved": current,
                "progress_pct": pct,
                "status": status_str
            })
        return updates

    def _fetch_upcoming_events(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        bills = db.execute(select(Bill).where(Bill.user_id == user_id, Bill.is_paid == False)).scalars().all()
        events = []
        now = datetime.now(timezone.utc)
        for b in bills:
            due_str = b.due_date.strftime("%Y-%m-%d") if b.due_date else "N/A"
            days = (b.due_date.replace(tzinfo=timezone.utc) - now).days if b.due_date else 0
            events.append({
                "title": f"{b.name} due",
                "type": "BILL",
                "amount": b.amount,
                "due_date": due_str,
                "days_remaining": max(days, 0)
            })
        return events

    def _build_copilot_prompt(
        self,
        summary: Dict[str, Any],
        coach_data: Dict[str, Any],
        anomaly_data: Dict[str, Any],
        goal_updates: List[Dict[str, Any]],
        upcoming_events: List[Dict[str, Any]]
    ) -> str:
        anomalies_summary = ", ".join([a.get("message", "") for a in anomaly_data.get("anomalies", [])[:2]]) or "None"
        goals_summary = ", ".join([f"{g['goal_name']}: {g['progress_pct']}%" for g in goal_updates[:3]]) or "None"
        bills_summary = ", ".join([f"{b['title']} (${b['amount']:,.2f})" for b in upcoming_events[:2]]) or "None"

        return f"""
Aggregated Financial Context:
- Composite Health Score: {summary.get('health_score', 0)}/100 ({summary.get('health_status', 'N/A')})
- Available Balance: ${summary.get('total_balance', 0.0):,.2f}
- Monthly Net Savings: ${summary.get('period_savings', 0.0):,.2f} (Savings Rate: {summary.get('period_savings_rate', 0.0):.1f}%)
- Identified Strengths: {", ".join(coach_data.get('strengths', []))}
- Active Risk Alerts: {anomalies_summary}
- Financial Goals Progress: {goals_summary}
- Upcoming Unpaid Bills: {bills_summary}

Generate JSON Daily Briefing object.
"""

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return None

    def _ensure_list(self, val: Any, default_list: List[str]) -> List[str]:
        if isinstance(val, list) and len(val) > 0:
            return [str(item) for item in val]
        return default_list

    def _build_deterministic_briefing(
        self,
        health_score: int,
        health_status: str,
        coach_data: Dict[str, Any],
        anomaly_data: Dict[str, Any],
        goal_updates: List[Dict[str, Any]],
        upcoming_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        highlights = coach_data.get("strengths", ["Active financial tracking enabled on ExpenseFlowAI."])
        alerts = [a.get("message") for a in anomaly_data.get("anomalies", []) if a.get("message")]
        recs = coach_data.get("recommendations", ["Keep monitoring category spending limits."])

        return {
            "greeting": "Good Morning 👋",
            "health_score": health_score,
            "health_status": health_status,
            "highlights": highlights,
            "alerts": alerts,
            "recommendations": recs,
            "goal_updates": goal_updates,
            "upcoming_events": upcoming_events,
            "encouragement": "You are making steady progress towards taking total control of your money!"
        }
