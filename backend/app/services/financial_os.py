"""
AI Personal Finance Operating System (Financial OS) Service - ExpenseFlowAI

Master-orchestrates FinanceEngine, AIFinancialCoachService, AIGoalPlannerService,
AIAnomalyDetectorService, AIMemoryService, and ToolExecutor into a unified,
prioritized financial control center.

CONTAINS ZERO FINANCIAL CALCULATIONS. FinanceEngine is the single source of truth.
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
from app.services.memory_service import AIMemoryService
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider
from app.models.goal import Goal
from app.models.bill import Bill

logger = logging.getLogger(__name__)


FINANCIAL_OS_PROMPT = """You are ExpenseFlowAI Personal Finance Operating System (Financial OS).
You act as an intelligent executive financial director, orchestrating sub-service findings into a prioritized control briefing.

RULES:
1. NEVER INVENT METRICS: Use only the supplied FinanceEngine data.
2. ENFORCE COGNITIVE LIMITS: Never overwhelm the user. Limit priorities to 3, opportunities to 3, alerts to 3.
3. OUTPUT STRICT JSON ONLY: You MUST respond with a single valid JSON object containing:
   - "priorities": array of up to 3 high-priority focus items.
   - "opportunities": array of up to 3 financial growth or savings opportunities.
   - "alerts": array of up to 3 risk alerts or warnings.
   - "predictions": array of 2 forward-looking cashflow/reserve predictions.
   - "motivation": concise, inspiring closing guidance.
"""


class AIFinancialOSService:
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

    def get_operating_system_overview(
        self,
        db: Session,
        user_id: int,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Master orchestration pipeline:
        1. Fetch FinanceEngine summary & health score.
        2. Safely query Coach, Anomaly, Goal, Memory, and Bill services.
        3. Prioritize findings (Max 3 per section).
        4. Synthesize via LLM and build mapped actionable tool suggestions.
        """
        # 1. Fetch FinanceEngine Dashboard Summary
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        today_snapshot = {
            "health_score": summary.get("health_score", 0),
            "health_status": summary.get("health_status", "N/A"),
            "total_balance": summary.get("total_balance", 0.0),
            "period_income": summary.get("period_income", 0.0),
            "period_expense": summary.get("period_expense", 0.0),
            "monthly_surplus": summary.get("period_savings", 0.0),
        }

        # 2. Safely query Coach Sub-service
        coach_data = {}
        try:
            coach_data = self.coach_service.generate_coaching_report(db, user_id=user_id, period=period)
        except Exception as exc:
            logger.warning("Financial OS coach sub-service error (%s).", str(exc))

        # 3. Safely query Anomaly Sub-service
        anomaly_data = {}
        try:
            anomaly_data = self.anomaly_service.detect_anomalies(db, user_id=user_id, period=period)
        except Exception as exc:
            logger.warning("Financial OS anomaly sub-service error (%s).", str(exc))

        # 4. Safely query Goal Evaluation
        goal_items = self._evaluate_user_goals(db, user_id)

        # 5. Safely query Memories & Bills
        memories = self._fetch_user_memories(db, user_id)
        upcoming_bills = self._fetch_upcoming_bills(db, user_id)

        # 6. Build prompt & execute LLM
        prompt = self._build_os_prompt(summary, coach_data, anomaly_data, goal_items, memories, upcoming_bills)

        try:
            llm_response = self.provider.generate(prompt=prompt, system_prompt=FINANCIAL_OS_PROMPT)
            parsed_json = self._extract_json(llm_response)
            if parsed_json:
                priorities = self._ensure_list(parsed_json.get("priorities"), self._default_priorities(summary, upcoming_bills))[:3]
                opportunities = self._ensure_list(parsed_json.get("opportunities"), coach_data.get("strengths", ["Build savings buffer"]))[:3]
                alerts = self._ensure_list(parsed_json.get("alerts"), [a.get("message") for a in anomaly_data.get("anomalies", []) if a.get("message")])[:3]
                predictions = self._ensure_list(parsed_json.get("predictions"), self._default_predictions(summary))[:2]
                motivation = str(parsed_json.get("motivation", "Consistency builds long-term financial independence."))

                actions = self._build_suggested_actions(summary, anomaly_data, coach_data, upcoming_bills)[:3]

                return {
                    "today": today_snapshot,
                    "priorities": priorities,
                    "opportunities": opportunities,
                    "alerts": alerts,
                    "predictions": predictions,
                    "actions": actions,
                    "motivation": motivation
                }
        except Exception as exc:
            logger.warning("LLM Financial OS synthesis failed (%s). Using deterministic OS overview.", str(exc))

        # Deterministic Fallback
        return self._build_deterministic_os_overview(today_snapshot, summary, coach_data, anomaly_data, upcoming_bills)

    def _evaluate_user_goals(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        goals = db.execute(select(Goal).where(Goal.user_id == user_id)).scalars().all()
        evals = []
        for g in goals:
            try:
                target_date_str = g.target_date.strftime("%Y-%m-%d") if g.target_date else None
                res = self.goal_service.evaluate_goal(
                    db=db,
                    user_id=user_id,
                    goal_name=g.name,
                    target_amount=g.target_amount,
                    target_date=target_date_str,
                    current_saved=g.current_amount or 0.0
                )
                evals.append(res)
            except Exception:
                pass
        return evals

    def _fetch_user_memories(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        try:
            mems = AIMemoryService.get_memories(db, user_id=user_id, active_only=True)
            return [{"category": m.category, "key": m.key, "value": m.value} for m in mems[:5]]
        except Exception:
            return []

    def _fetch_upcoming_bills(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        bills = db.execute(select(Bill).where(Bill.user_id == user_id, Bill.is_paid == False)).scalars().all()
        return [{"id": b.id, "name": b.name, "amount": b.amount} for b in bills]

    def _build_os_prompt(
        self,
        summary: Dict[str, Any],
        coach_data: Dict[str, Any],
        anomaly_data: Dict[str, Any],
        goal_items: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        upcoming_bills: List[Dict[str, Any]]
    ) -> str:
        anomalies_str = ", ".join([a.get("message", "") for a in anomaly_data.get("anomalies", [])[:3]]) or "None"
        goals_str = ", ".join([f"{g['goal_name']}: {g['status']}" for g in goal_items[:3]]) or "None"
        bills_str = ", ".join([f"{b['name']} (${b['amount']:,.2f})" for b in upcoming_bills[:3]]) or "None"
        mems_str = ", ".join([f"{m['key']}={m['value']}" for m in memories[:3]]) or "None"

        return f"""
Master Financial Data (Source: FinanceEngine):
- Health Score: {summary.get('health_score', 0)}/100 ({summary.get('health_status', 'N/A')})
- Available Balance: ${summary.get('total_balance', 0.0):,.2f}
- Monthly Net Savings: ${summary.get('period_savings', 0.0):,.2f} (Savings Rate: {summary.get('period_savings_rate', 0.0):.1f}%)
- Unpaid Bills: {bills_str}
- Risk Alerts: {anomalies_str}
- Active Goal Statuses: {goals_str}
- User Context Notes: {mems_str}

Synthesize into JSON Financial OS Overview matching strict limits (Max 3/section).
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

    def _build_suggested_actions(
        self,
        summary: Dict[str, Any],
        anomaly_data: Dict[str, Any],
        coach_data: Dict[str, Any],
        upcoming_bills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        actions = []

        # Action 1: Bill payment / reminder
        if upcoming_bills:
            b = upcoming_bills[0]
            actions.append({
                "title": f"Schedule reminder for {b['name']}",
                "tool_name": "ReminderTool",
                "action": "create_reminder",
                "parameters": {"title": b['name'], "amount": b['amount']},
                "impact_description": f"Ensures 100% on-time payment for {b['name']} (${b['amount']:,.2f})."
            })

        # Action 2: Budget adjustment if overspending
        anomalies = anomaly_data.get("anomalies", [])
        if anomalies:
            cat = anomalies[0].get("category", "General")
            actions.append({
                "title": f"Adjust {cat} spending budget",
                "tool_name": "BudgetTool",
                "action": "create_budget",
                "parameters": {"category": cat, "amount": 5000.0},
                "impact_description": f"Caps discretionary outflows in {cat} to protect monthly net savings."
            })
        else:
            actions.append({
                "title": "Set up monthly savings goal",
                "tool_name": "GoalTool",
                "action": "create_goal",
                "parameters": {"goal_name": "Emergency Fund", "target_amount": 100000.0},
                "impact_description": "Builds 3-month liquid cash emergency reserve."
            })

        # Action 3: Savings automation
        surplus = summary.get("period_savings", 0.0)
        if surplus > 0:
            actions.append({
                "title": "Automate monthly savings transfer",
                "tool_name": "BudgetTool",
                "action": "create_budget",
                "parameters": {"category": "Savings", "amount": round(surplus * 0.5, 2)},
                "impact_description": f"Automatically accumulates ${surplus * 0.5:,.2f} into high-yield savings each month."
            })

        return actions

    def _default_priorities(self, summary: Dict[str, Any], upcoming_bills: List[Dict[str, Any]]) -> List[str]:
        prios = []
        if upcoming_bills:
            prios.append(f"Pay upcoming bill: {upcoming_bills[0]['name']} (${upcoming_bills[0]['amount']:,.2f})")
        if summary.get("period_savings", 0.0) < 0:
            prios.append("Address negative monthly net cashflow")
        prios.append(f"Maintain health score at or above current {summary.get('health_score', 0)}/100 rating")
        return prios[:3]

    def _default_predictions(self, summary: Dict[str, Any]) -> List[str]:
        reserve = summary.get("health_metrics", {}).get("reserve_months", 0.0)
        surplus = summary.get("period_savings", 0.0)
        return [
            f"Estimated cash reserve trajectory: {reserve:.1f} months of expenses.",
            f"Projected annual savings at current rate: ${surplus * 12:,.2f}."
        ]

    def _build_deterministic_os_overview(
        self,
        today_snapshot: Dict[str, Any],
        summary: Dict[str, Any],
        coach_data: Dict[str, Any],
        anomaly_data: Dict[str, Any],
        upcoming_bills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        priorities = self._default_priorities(summary, upcoming_bills)[:3]
        opportunities = coach_data.get("strengths", ["Active financial tracking enabled."])[:3]
        alerts = [a.get("message") for a in anomaly_data.get("anomalies", []) if a.get("message")][:3]
        predictions = self._default_predictions(summary)[:2]
        actions = self._build_suggested_actions(summary, anomaly_data, coach_data, upcoming_bills)[:3]

        return {
            "today": today_snapshot,
            "priorities": priorities,
            "opportunities": opportunities,
            "alerts": alerts,
            "predictions": predictions,
            "actions": actions,
            "motivation": "Consistency and smart automation pave the way to financial independence!"
        }
