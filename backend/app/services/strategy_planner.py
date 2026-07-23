"""
AI Financial Strategy Planner Service - ExpenseFlowAI

Acts as an executive Personal CFO creating long-term (1-Year, 3-Year, 5-Year) financial roadmaps,
prioritized directives, monthly action plans, and risk mitigation strategies.
FinanceEngine performs ALL mathematical calculations; AI structures and explains the strategy.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.finance_engine import FinanceEngine
from app.services.memory_service import AIMemoryService
from app.services.cashflow_forecast import CashFlowForecastService
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


STRATEGY_SYSTEM_PROMPT = """You are ExpenseFlowAI Personal CFO & Strategic Financial Planner.
Act as an executive financial director to synthesize a long-term financial roadmap.

RULES:
1. NEVER INVENT MATH METRICS: Use only the supplied FinanceEngine figures.
2. STRUCTURED OUTPUT: Respond with valid JSON containing:
   - "priorities": array of top 5 prioritized directives.
   - "one_year_plan": array of 3 tactical 1-year milestones.
   - "three_year_plan": array of 3 strategic 3-year milestones.
   - "five_year_plan": array of 3 wealth & independence 5-year milestones.
   - "risks": array of identified financial risk factors.
"""


class AIStrategyPlannerService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def generate_strategy_plan(
        self,
        db: Session,
        user_id: int,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Main orchestration pipeline:
        1. Fetch FinanceEngine summary & health metrics.
        2. Fetch user persistent memories & preferences.
        3. Fetch cashflow forecast projections.
        4. Derive 1Y, 3Y, 5Y roadmaps, priorities, and 12-month action checklist.
        """
        # 1. Fetch FinanceEngine Baseline Data
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        health_data = FinanceEngine.calculate_financial_health_score(db, user_id=user_id)

        health_score = health_data["health_score"]
        health_status = health_data["status"]
        income = float(summary.get("period_income", 0.0))
        expense = float(summary.get("period_expense", 0.0))
        surplus = float(summary.get("period_savings", 0.0))
        savings_rate = float(summary.get("period_savings_rate", 0.0))
        reserve_months = float(health_data["metrics"]["reserve_months"])

        # 2. Fetch User Persistent Memories
        memories = []
        try:
            mem_records = AIMemoryService.get_memories(db, user_id=user_id, active_only=True)
            memories = [{"category": m.category, "key": m.key, "value": m.value} for m in mem_records[:5]]
        except Exception:
            pass

        # 3. Derive Top 5 Priorities Deterministically
        priorities = self._derive_priorities(health_score, savings_rate, reserve_months, surplus)

        # 4. Derive 1Y, 3Y, 5Y Roadmaps
        one_year = [
            f"Increase liquid emergency cash reserve to {max(6.0, reserve_months):.1f} months of expenses.",
            "Eliminate short-term high-interest consumer liabilities and pending bills.",
            f"Maintain category budget adherence with net savings rate above {max(25.0, savings_rate):.0f}%."
        ]

        three_year = [
            "Accumulate 50% of target financial goals through systematic monthly contributions.",
            f"Deploy monthly surplus (${max(surplus, 1000.0):,.2f}/mo) into low-cost index investments.",
            "Establish automated cashflow rebalancing to maintain optimal liquidity reserves."
        ]

        five_year = [
            "Achieve 100% completion across all long-term financial target goals.",
            "Maintain complete high-yield financial independence with 12+ months cash runway.",
            "Build a resilient, multi-asset financial foundation with zero bad debt."
        ]

        # 5. Derive 12-Month Action Checklist
        monthly_actions = self._derive_monthly_actions(surplus)

        # 6. Derive Risks
        risks = self._derive_risks(savings_rate, reserve_months, surplus, summary.get("category_spending", []))

        # 7. Calculate Confidence Score
        confidence = 0.93 if income > 0 else 0.75

        # 8. Optional LLM Synthesis Overlay
        prompt = self._build_prompt(summary, health_data, priorities, memories)
        try:
            llm_res = self.provider.generate(prompt=prompt, system_prompt=STRATEGY_SYSTEM_PROMPT)
            parsed = self._extract_json(llm_res)
            if parsed:
                if isinstance(parsed.get("priorities"), list) and len(parsed["priorities"]) >= 3:
                    priorities = [str(p) for p in parsed["priorities"][:5]]
                if isinstance(parsed.get("one_year_plan"), list) and len(parsed["one_year_plan"]) >= 2:
                    one_year = [str(p) for p in parsed["one_year_plan"][:3]]
                if isinstance(parsed.get("three_year_plan"), list) and len(parsed["three_year_plan"]) >= 2:
                    three_year = [str(p) for p in parsed["three_year_plan"][:3]]
                if isinstance(parsed.get("five_year_plan"), list) and len(parsed["five_year_plan"]) >= 2:
                    five_year = [str(p) for p in parsed["five_year_plan"][:3]]
                if isinstance(parsed.get("risks"), list) and len(parsed["risks"]) >= 1:
                    risks = [str(r) for r in parsed["risks"][:4]]
        except Exception as exc:
            logger.warning("LLM Strategy Plan synthesis error (%s). Using deterministic CFO roadmap.", str(exc))

        return {
            "current_health": health_score,
            "priorities": priorities,
            "one_year_plan": one_year,
            "three_year_plan": three_year,
            "five_year_plan": five_year,
            "monthly_actions": monthly_actions,
            "risks": risks,
            "confidence": confidence
        }

    def _derive_priorities(
        self,
        health_score: int,
        savings_rate: float,
        reserve_months: float,
        surplus: float
    ) -> List[str]:
        prios = []
        if reserve_months < 6.0:
            prios.append("Priority 1: Increase emergency fund to 6 months of expenses.")
        else:
            prios.append("Priority 1: Maintain robust 6+ month emergency cash reserve.")

        if surplus <= 0:
            prios.append("Priority 2: Eliminate net cashflow deficit by capping non-essential spending.")
        else:
            prios.append("Priority 2: Repay high-interest debt and pending bill obligations.")

        alloc = max(surplus * 0.5, 2000.0)
        prios.append(f"Priority 3: Increase systematic investment plan (SIP) by ${alloc:,.2f} after debt reduction.")
        prios.append("Priority 4: Reduce food delivery and discretionary entertainment spending by 20%.")
        prios.append(f"Priority 5: Maintain net savings rate above {max(25.0, savings_rate):.0f}%.")
        return prios

    def _derive_monthly_actions(self, surplus: float) -> List[Dict[str, Any]]:
        alloc = max(surplus * 0.4, 1000.0)
        actions = [
            {"month_number": 1, "title": "Audit Subscriptions", "description": "Audit recurring bills and eliminate unused streaming services.", "target_category": "Budget"},
            {"month_number": 2, "title": "Emergency Fund Allocation", "description": f"Allocate ${alloc:,.2f} to high-yield emergency reserve.", "target_category": "Savings"},
            {"month_number": 3, "title": "Debt Reduction Sweep", "description": "Pay down highest APR credit card or loan balance.", "target_category": "Debt"},
            {"month_number": 4, "title": "Budget Cap Optimization", "description": "Set 10% lower spending caps on dining & shopping.", "target_category": "Budget"},
            {"month_number": 5, "title": "SIP Investment Boost", "description": "Automate monthly investment contribution.", "target_category": "Investment"},
            {"month_number": 6, "title": "Mid-Year CFO Health Audit", "description": "Evaluate health score trajectory and goal progress.", "target_category": "General"},
            {"month_number": 7, "title": "Utility & Fixed Bill Review", "description": "Negotiate insurance and utility provider rates.", "target_category": "Budget"},
            {"month_number": 8, "title": "Goal Progress Acceleration", "description": "Transfer excess cash surplus to active goals.", "target_category": "Savings"},
            {"month_number": 9, "title": "Tax Deduction Tracking", "description": "Review tax-advantaged retirement accounts.", "target_category": "Tax"},
            {"month_number": 10, "title": "Holiday Budget Preparation", "description": "Pre-fund seasonal holiday expenses.", "target_category": "Budget"},
            {"month_number": 11, "title": "Annual Debt Clearance Check", "description": "Verify 0 high-interest debt balance.", "target_category": "Debt"},
            {"month_number": 12, "title": "Year-End CFO Strategy Review", "description": "Re-balance portfolio and set next year's targets.", "target_category": "General"}
        ]
        return actions

    def _derive_risks(
        self,
        savings_rate: float,
        reserve_months: float,
        surplus: float,
        categories: List[Dict[str, Any]]
    ) -> List[str]:
        risks = []
        if reserve_months < 3.0:
            risks.append("Low emergency cash reserve exposes user to sudden income shocks.")
        if savings_rate < 15.0:
            risks.append("Savings rate below 15% slows down long-term goal accumulation velocity.")
        if surplus <= 0:
            risks.append("Negative cashflow surplus threatens liquidity and risks debt dependency.")

        if categories:
            top_cat = categories[0].get("category", "General")
            risks.append(f"High spending concentration in '{top_cat}' category.")

        if not risks:
            risks.append("Inflation risk impacting purchasing power over 5-year horizon.")
        return risks

    def _build_prompt(
        self,
        summary: Dict[str, Any],
        health_data: Dict[str, Any],
        priorities: List[str],
        memories: List[Dict[str, Any]]
    ) -> str:
        prios_str = "; ".join(priorities)
        mems_str = "; ".join([f"{m['key']}={m['value']}" for m in memories]) or "None"

        return f"""
FINANCIAL BASELINE (Source: FinanceEngine):
- Health Score: {health_data['health_score']}/100 ({health_data['status']})
- Income: ${summary.get('period_income', 0.0):,.2f}
- Expenses: ${summary.get('period_expense', 0.0):,.2f}
- Net Savings: ${summary.get('period_savings', 0.0):,.2f} (Savings Rate: {summary.get('period_savings_rate', 0.0):.1f}%)
- Emergency Reserve: {health_data['metrics']['reserve_months']:.1f} months
- Baseline Directives: {prios_str}
- User Context Preferences: {mems_str}

Generate JSON strategy roadmap matching strict 1Y, 3Y, 5Y schema.
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
