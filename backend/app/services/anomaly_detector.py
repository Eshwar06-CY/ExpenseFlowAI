"""
AI Spending Anomaly Detection Service - ExpenseFlowAI

Detects financial anomalies, spending spikes, budget overruns, and cash flow risks
computed from FinanceEngine data, leveraging local LLM (Ollama) for structured
anomaly explanations and actionable guidance.

The AI DOES NOT perform mathematical deviation calculations. All numbers and threshold
checks are sourced directly from FinanceEngine.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.finance_engine import FinanceEngine
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider
from app.schemas.anomaly import AnomalySeverity, OverallRisk, AnomalyItem

logger = logging.getLogger(__name__)


ANOMALY_SYSTEM_PROMPT = """You are ExpenseFlowAI Anomaly Engine. You analyze pre-calculated financial deviations and return a JSON response listing detected anomalies.

RULES:
1. USE ONLY THE SUPPLIED DEVIATIONS & METRICS: Never invent balances or fake transactions.
2. OUTPUT STRICT JSON ONLY: You MUST respond with a single valid JSON object containing:
   - "anomalies": array of objects with keys ("severity", "category", "message", "possible_reason", "recommendation", "confidence").
     Allowed severities: "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL".
   - "overall_risk": "LOW", "MEDIUM", "HIGH", or "CRITICAL".
   - "summary": a brief 1-sentence summary of findings.
"""


class AIAnomalyDetectorService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def detect_anomalies(
        self,
        db: Session,
        user_id: int,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Gathers verified metrics from FinanceEngine, identifies rule-based deviations,
        passes context to LLM for rich explanations, and falls back safely to deterministic
        anomaly structures if LLM parsing fails.
        """
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        budget_data = FinanceEngine.get_budget_adherence(db, user_id=user_id)
        bill_data = FinanceEngine.get_bill_reliability(db, user_id=user_id)
        reserve_data = FinanceEngine.get_cash_reserve_metrics(db, user_id=user_id)

        # 1. Identify rule-based financial deviations computed from FinanceEngine
        raw_deviations = self._extract_financial_deviations(summary, budget_data, bill_data, reserve_data)

        # 2. If no deviations detected, return clean clean bill of health
        if not raw_deviations:
            return {
                "anomalies": [],
                "overall_risk": OverallRisk.LOW.value,
                "summary": "No unusual spending anomalies or financial risks detected."
            }

        # 3. Build prompt for LLM enrichment
        prompt = self._build_anomaly_prompt(summary, raw_deviations)

        try:
            llm_response = self.provider.generate(prompt=prompt, system_prompt=ANOMALY_SYSTEM_PROMPT)
            parsed_json = self._extract_json(llm_response)
            if parsed_json and "anomalies" in parsed_json:
                anomalies_list = self._sanitize_anomalies(parsed_json.get("anomalies", []))
                overall_risk = str(parsed_json.get("overall_risk", self._determine_overall_risk(anomalies_list)))
                summary_text = str(parsed_json.get("summary", f"{len(anomalies_list)} anomaly detected."))
                return {
                    "anomalies": anomalies_list,
                    "overall_risk": overall_risk,
                    "summary": summary_text
                }
        except Exception as exc:
            logger.warning("LLM anomaly explanation failed (%s). Using deterministic anomaly report.", str(exc))

        # 4. Deterministic Fallback if LLM fails
        return self._build_deterministic_anomalies(raw_deviations)

    def _extract_financial_deviations(
        self,
        summary: Dict[str, Any],
        budget_data: Dict[str, Any],
        bill_data: Dict[str, Any],
        reserve_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        deviations = []

        # Check 1: Budget Overspending
        budgets_list = budget_data.get("budgets", [])
        if isinstance(budgets_list, list):
            for b in budgets_list:
                if b.get("is_exceeded"):
                    cat_name = b.get("category_name", b.get("category", "General"))
                    spent = b.get("spent", 0.0)
                    amount = b.get("amount", 1.0)
                    over_pct = ((spent - amount) / max(amount, 1.0)) * 100.0
                    deviations.append({
                        "type": "BUDGET_OVERRUN",
                        "severity": AnomalySeverity.HIGH.value if over_pct > 25.0 else AnomalySeverity.MEDIUM.value,
                        "category": cat_name,
                        "detail": f"Category '{cat_name}' spent ${spent:,.2f} exceeding limit ${amount:,.2f} (+{over_pct:.1f}% over budget)."
                    })

        # Check 2: Cash Reserve Depletion
        total_bal = summary.get("total_balance", 0.0)
        monthly_exp = reserve_data.get("monthly_expense_30d", 0.0)
        reserve_months = reserve_data.get("reserve_months", 0.0)
        if monthly_exp > 0 or total_bal > 0:
            if reserve_months < 1.0:
                deviations.append({
                    "type": "RESERVE_CRITICAL",
                    "severity": AnomalySeverity.CRITICAL.value,
                    "category": "Emergency Reserve",
                    "detail": f"Emergency fund cash reserve ({reserve_months:.1f} months) is dangerously below 1-month safety floor."
                })
            elif reserve_months < 3.0:
                deviations.append({
                    "type": "RESERVE_LOW",
                    "severity": AnomalySeverity.MEDIUM.value,
                    "category": "Emergency Reserve",
                    "detail": f"Cash reserve of {reserve_months:.1f} months is below 3-month recommended benchmark."
                })

        # Check 3: Savings Rate Drop / Negative Net
        savings_rate = summary.get("period_savings_rate", 0.0)
        net_savings = summary.get("period_savings", 0.0)
        period_income = summary.get("period_income", 0.0)
        period_expense = summary.get("period_expense", 0.0)
        if net_savings < 0:
            deviations.append({
                "type": "NEGATIVE_NET_SAVINGS",
                "severity": AnomalySeverity.HIGH.value,
                "category": "Cash Flow",
                "detail": f"Expenses (${period_expense:,.2f}) exceeded income (${period_income:,.2f}), causing negative net savings (${net_savings:,.2f})."
            })
        elif (period_income > 0 or period_expense > 0) and savings_rate < 10.0:
            deviations.append({
                "type": "LOW_SAVINGS_RATE",
                "severity": AnomalySeverity.LOW.value,
                "category": "Savings",
                "detail": f"Savings rate ({savings_rate:.1f}%) is low for the selected period."
            })

        # Check 4: Dominant Category Spending Spike
        cat_spending = summary.get("category_spending", [])
        for c in cat_spending:
            pct = c.get("percentage", 0.0)
            amt = c.get("amount", 0.0)
            cat_name = c.get("category", "General")
            if pct >= 40.0:
                deviations.append({
                    "type": "CATEGORY_SPIKE",
                    "severity": AnomalySeverity.MEDIUM.value,
                    "category": cat_name,
                    "detail": f"{cat_name} accounts for {pct:.1f}% (${amt:,.2f}) of total monthly expenses."
                })

        # Check 5: Overdue Unpaid Bills
        unpaid_count = bill_data.get("unpaid_bills", 0)
        if unpaid_count > 0:
            deviations.append({
                "type": "UNPAID_BILLS",
                "severity": AnomalySeverity.HIGH.value,
                "category": "Bills & Utilities",
                "detail": f"There are {unpaid_count} upcoming/unpaid bills total value ${bill_data.get('unpaid_amount', 0.0):,.2f}."
            })

        return deviations

    def _build_anomaly_prompt(self, summary: Dict[str, Any], raw_deviations: List[Dict[str, Any]]) -> str:
        dev_lines = [f"- [{d['severity']}] {d['category']}: {d['detail']}" for d in raw_deviations]
        dev_text = "\n".join(dev_lines)

        return f"""
Calculated Financial Deviations (Source: FinanceEngine):
{dev_text}

Transform these pre-calculated deviations into structured JSON:
{{
  "anomalies": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "category": "...",
      "message": "...",
      "possible_reason": "...",
      "recommendation": "...",
      "confidence": 0.95
    }}
  ],
  "overall_risk": "CRITICAL|HIGH|MEDIUM|LOW",
  "summary": "..."
}}
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

    def _sanitize_anomalies(self, raw_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sanitized = []
        valid_severities = {s.value for s in AnomalySeverity}
        for item in raw_list:
            sev = str(item.get("severity", "MEDIUM")).upper()
            if sev not in valid_severities:
                sev = "MEDIUM"
            sanitized.append({
                "severity": sev,
                "category": str(item.get("category", "Financial Metric")),
                "message": str(item.get("message", "Anomalous financial trend detected.")),
                "possible_reason": str(item.get("possible_reason", "Increased spending or shift in baseline outflow.")),
                "recommendation": str(item.get("recommendation", "Review category transactions and budget limits.")),
                "confidence": min(1.0, max(0.0, float(item.get("confidence", 0.90)))),
            })
        return sanitized

    def _determine_overall_risk(self, anomalies: List[Dict[str, Any]]) -> str:
        severities = {a.get("severity") for a in anomalies}
        if AnomalySeverity.CRITICAL.value in severities:
            return OverallRisk.CRITICAL.value
        if AnomalySeverity.HIGH.value in severities:
            return OverallRisk.HIGH.value
        if AnomalySeverity.MEDIUM.value in severities:
            return OverallRisk.MEDIUM.value
        return OverallRisk.LOW.value

    def _build_deterministic_anomalies(self, raw_deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        anomalies = []
        for d in raw_deviations:
            anomalies.append({
                "severity": d["severity"],
                "category": d["category"],
                "message": d["detail"],
                "possible_reason": f"Significant deviation in {d['category']} relative to expected parameters.",
                "recommendation": f"Inspect recent {d['category']} entries and adjust allocation.",
                "confidence": 0.92,
            })

        overall_risk = self._determine_overall_risk(anomalies)
        summary = f"Detected {len(anomalies)} spending anomaly/risk factors."

        return {
            "anomalies": anomalies,
            "overall_risk": overall_risk,
            "summary": summary
        }
