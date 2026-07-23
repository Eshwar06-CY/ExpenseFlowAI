"""
Insight Rules Engine - ExpenseFlowAI Hybrid AI Architecture

Deterministic Rule Engine that evaluates verified metrics produced by FinanceEngine
and extracts structured financial insights (facts, severity, thresholds).

CRITICAL RULE:
This component performs NO financial arithmetic or calculation recalculation.
All numerical values are provided directly by FinanceEngine.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class FinancialInsight:
    category: str       # "savings", "reserve", "budget", "bill", "health", "outflow"
    rule_id: str        # Unique identifier e.g., "SAVINGS_RATE_EXCELLENT"
    severity: str       # "positive", "info", "warning", "critical"
    title: str          # Factual title
    details: str        # Factual summary sentence
    metrics: Dict[str, Any] = field(default_factory=dict)


class InsightRuleEngine:
    @staticmethod
    def evaluate_rules(summary: Dict[str, Any]) -> List[FinancialInsight]:
        """
        Evaluates deterministic rules against FinanceEngine summary metrics.
        Returns a list of structured FinancialInsight objects.
        """
        insights: List[FinancialInsight] = []

        # Extract verified metrics directly from FinanceEngine output
        total_balance = float(summary.get("total_balance", 0.0))
        income = float(summary.get("period_income", 0.0))
        expenses = float(summary.get("period_expense", 0.0))
        net_savings = float(summary.get("period_savings", 0.0))
        savings_rate = float(summary.get("period_savings_rate", 0.0))

        health_score = int(summary.get("health_score", 0))
        health_status = str(summary.get("health_status", "N/A"))

        health_metrics = summary.get("health_metrics", {})
        reserve_months = float(health_metrics.get("reserve_months", 0.0))
        budget_adherence_pct = float(health_metrics.get("budget_adherence_pct", 100.0))
        bill_reliability_pct = float(health_metrics.get("bill_reliability_pct", 100.0))

        # -------------------------------------------------------------
        # 1. Savings Rate Rules
        # -------------------------------------------------------------
        if savings_rate >= 20.0:
            insights.append(FinancialInsight(
                category="savings",
                rule_id="SAVINGS_RATE_EXCELLENT",
                severity="positive",
                title="Strong Savings Rate",
                details=f"Your savings rate is {savings_rate:.1f}%, exceeding the benchmark target of 20.0%.",
                metrics={"savings_rate": savings_rate, "net_savings": net_savings}
            ))
        elif 10.0 <= savings_rate < 20.0:
            insights.append(FinancialInsight(
                category="savings",
                rule_id="SAVINGS_RATE_MODERATE",
                severity="info",
                title="Moderate Savings Velocity",
                details=f"Your current savings rate is {savings_rate:.1f}%. Increasing savings by 5% will accelerate your goal timeline.",
                metrics={"savings_rate": savings_rate, "net_savings": net_savings}
            ))
        elif 0.0 <= savings_rate < 10.0:
            insights.append(FinancialInsight(
                category="savings",
                rule_id="SAVINGS_RATE_LOW",
                severity="warning",
                title="Low Savings Margin",
                details=f"Your savings rate is {savings_rate:.1f}%, leaving little buffer for wealth building.",
                metrics={"savings_rate": savings_rate, "net_savings": net_savings}
            ))
        else: # Net deficit
            insights.append(FinancialInsight(
                category="savings",
                rule_id="SAVINGS_RATE_DEFICIT",
                severity="critical",
                title="Net Deficit Alert",
                details=f"Expenses exceed income for this period, resulting in a net outflow of ${abs(net_savings):,.2f}.",
                metrics={"savings_rate": savings_rate, "net_savings": net_savings, "income": income, "expenses": expenses}
            ))

        # -------------------------------------------------------------
        # 2. Emergency Cash Reserve Rules
        # -------------------------------------------------------------
        if reserve_months >= 6.0:
            insights.append(FinancialInsight(
                category="reserve",
                rule_id="RESERVE_ULTRA_SECURE",
                severity="positive",
                title="Ultra-Secure Emergency Reserve",
                details=f"Your liquid cash reserve covers {reserve_months:.1f} months of expenses, providing full safety.",
                metrics={"reserve_months": reserve_months, "total_balance": total_balance}
            ))
        elif 3.0 <= reserve_months < 6.0:
            insights.append(FinancialInsight(
                category="reserve",
                rule_id="RESERVE_HEALTHY",
                severity="positive",
                title="Healthy Emergency Fund",
                details=f"Your emergency reserve covers {reserve_months:.1f} months of expenses, meeting the recommended 3-6 month target.",
                metrics={"reserve_months": reserve_months, "total_balance": total_balance}
            ))
        elif 1.0 <= reserve_months < 3.0:
            insights.append(FinancialInsight(
                category="reserve",
                rule_id="RESERVE_VULNERABLE",
                severity="warning",
                title="Vulnerable Reserve Safety",
                details=f"Your cash reserve currently covers {reserve_months:.1f} months of outflows, below the 3-month safety benchmark.",
                metrics={"reserve_months": reserve_months, "total_balance": total_balance}
            ))
        else:
            insights.append(FinancialInsight(
                category="reserve",
                rule_id="RESERVE_CRITICAL",
                severity="critical",
                title="Critical Reserve Shortfall",
                details=f"Your emergency reserve is below 1 month ({reserve_months:.1f} months), leaving you exposed to unexpected shocks.",
                metrics={"reserve_months": reserve_months, "total_balance": total_balance}
            ))

        # -------------------------------------------------------------
        # 3. Budget Adherence Rules
        # -------------------------------------------------------------
        if budget_adherence_pct == 100.0:
            insights.append(FinancialInsight(
                category="budget",
                rule_id="BUDGET_PERFECT",
                severity="positive",
                title="Perfect Budget Adherence",
                details=f"All active spending budgets are within set limits ({budget_adherence_pct:.1f}% adherence).",
                metrics={"budget_adherence_pct": budget_adherence_pct}
            ))
        elif 80.0 <= budget_adherence_pct < 100.0:
            insights.append(FinancialInsight(
                category="budget",
                rule_id="BUDGET_WARNING",
                severity="warning",
                title="Minor Budget Overspends",
                details=f"Budget adherence is at {budget_adherence_pct:.1f}%. One or more category limits have been exceeded.",
                metrics={"budget_adherence_pct": budget_adherence_pct}
            ))
        else:
            insights.append(FinancialInsight(
                category="budget",
                rule_id="BUDGET_CRITICAL",
                severity="critical",
                title="Budget Slippage Alert",
                details=f"Budget adherence is at {budget_adherence_pct:.1f}%, indicating significant overspending in multiple categories.",
                metrics={"budget_adherence_pct": budget_adherence_pct}
            ))

        # -------------------------------------------------------------
        # 4. Bill Payment Reliability Rules
        # -------------------------------------------------------------
        if bill_reliability_pct >= 95.0:
            insights.append(FinancialInsight(
                category="bill",
                rule_id="BILL_PERFECT",
                severity="positive",
                title="Excellent Payment Reliability",
                details=f"Bill payment reliability stands at {bill_reliability_pct:.1f}%, protecting credit standing.",
                metrics={"bill_reliability_pct": bill_reliability_pct}
            ))
        else:
            insights.append(FinancialInsight(
                category="bill",
                rule_id="BILL_PENDING",
                severity="warning",
                title="Pending Bill Dues",
                details=f"Bill payment reliability is at {bill_reliability_pct:.1f}%. Ensure upcoming bills are scheduled.",
                metrics={"bill_reliability_pct": bill_reliability_pct}
            ))

        # -------------------------------------------------------------
        # 5. Overall Health Score Rule
        # -------------------------------------------------------------
        if health_score >= 80:
            insights.append(FinancialInsight(
                category="health",
                rule_id="HEALTH_EXCELLENT",
                severity="positive",
                title="Excellent Financial Standing",
                details=f"Overall workspace health score is {health_score}/100 ({health_status}).",
                metrics={"health_score": health_score, "health_status": health_status}
            ))
        elif 50 <= health_score < 80:
            insights.append(FinancialInsight(
                category="health",
                rule_id="HEALTH_GOOD",
                severity="info",
                title="Healthy Financial Base",
                details=f"Overall workspace health score is {health_score}/100 ({health_status}).",
                metrics={"health_score": health_score, "health_status": health_status}
            ))
        else:
            insights.append(FinancialInsight(
                category="health",
                rule_id="HEALTH_CRITICAL",
                severity="critical",
                title="Critical Financial Standing",
                details=f"Overall workspace health score is {health_score}/100 ({health_status}). Immediate optimization recommended.",
                metrics={"health_score": health_score, "health_status": health_status}
            ))

        # -------------------------------------------------------------
        # 6. Top Spending Outflows Rule
        # -------------------------------------------------------------
        category_spending = summary.get("category_spending", [])
        if category_spending:
            top_cat = category_spending[0]
            insights.append(FinancialInsight(
                category="outflow",
                rule_id="TOP_OUTFLOW_IDENTIFIED",
                severity="info",
                title="Primary Expense Category",
                details=f"Your highest spending category is '{top_cat['category']}' with ${top_cat['amount']:,.2f} ({top_cat['percentage']:.1f}% of outflows).",
                metrics={"top_category": top_cat['category'], "amount": top_cat['amount'], "percentage": top_cat['percentage']}
            ))

        return insights
