"""
Template Engine - ExpenseFlowAI Hybrid AI Architecture

Deterministic Template Engine that converts evaluated FinancialInsight objects
and FinanceEngine summary metrics into high-quality text and structured JSON responses
WITHOUT calling any external LLM or AI provider API.
"""

import json
from typing import Dict, Any, List, Optional
from app.ai.insight_rules import FinancialInsight


class TemplateEngine:
    @staticmethod
    def render_text_report(
        insights: List[FinancialInsight],
        summary: Dict[str, Any],
        user_message: Optional[str] = None
    ) -> str:
        """
        Renders a comprehensive, intent-aware report or conversational response.
        """
        query_text = (user_message or "").strip()
        query_lower = query_text.lower()

        # Handle Conversational Intents directly without raw financial report
        if "joke" in query_lower:
            return "😂 Why don't accountants read novels?\n\nBecause the ending is always *balanced*! 📊"

        if query_lower in ["hi", "hello", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening"]:
            return "Hi 👋\n\nI'm ExpenseFlow AI, your Personal CFO.\n\nHow can I help with your financial goals, spending, or budgets today?"

        if any(term in query_lower for term in ["thanks", "thank you", "thx", "cool", "awesome", "great", "nice", "how are you"]):
            return "You're welcome 😊\n\nAlways happy to help!"

        if any(term in query_lower for term in ["who are you", "what is your name", "who created you", "tell me about yourself"]):
            return "I'm your AI Financial Assistant.\n\nI can analyze spending, create financial plans, compare scenarios, explain budgets, and help you make better financial decisions using verified metrics from your ExpenseFlow workspace."

        if any(term in query_lower for term in ["what can you do", "help", "capabilities", "features"]):
            return "I can help you:\n\n• **Analyze spending** & review category outflows\n• **Explain budgets** & track adherence limits\n• **Review expenses** & identify anomalies\n• **Calculate 90-day cashflow forecasts**\n• **Compare financial scenarios** (e.g. buying a bike vs. saving)\n• **Plan financial goals** with custom roadmaps"

        total_balance = float(summary.get("total_balance", 0.0))
        income = float(summary.get("period_income", 0.0))
        expenses = float(summary.get("period_expense", 0.0))
        net_savings = float(summary.get("period_savings", 0.0))
        savings_rate = float(summary.get("period_savings_rate", 0.0))
        health_score = int(summary.get("health_score", 0))
        health_status = str(summary.get("health_status", "N/A"))

        positives = [i for i in insights if i.severity == "positive"]
        warnings = [i for i in insights if i.severity in ("warning", "critical")]

        lines = []

        if query_text:
            lines.append(f"### Financial Advisory & Analysis\n")
            lines.append(f"Regarding your query *\"{query_text}\"*, here is your verified assessment based on ExpenseFlowAI workspace metrics:\n")

            if "forecast" in query_lower or "cashflow" in query_lower:
                lines.append(f"**90-Day Cashflow Velocity Projection:**")
                projected_90d_savings = net_savings * 3
                lines.append(f"- **Current Monthly Net Savings:** ${net_savings:,.2f}")
                lines.append(f"- **Projected 90-Day Net Cash Accumulation:** ${projected_90d_savings:,.2f}")
                lines.append(f"- **Projected 90-Day Liquid Balance:** ${total_balance + projected_90d_savings:,.2f}\n")
            elif "bike" in query_lower or "buy" in query_lower or "purchase" in query_lower:
                lines.append(f"**Discretionary Purchase Feasibility Assessment:**")
                lines.append(f"- **Current Liquid Balance:** ${total_balance:,.2f}")
                lines.append(f"- **Emergency Reserve Buffer:** {summary.get('health_metrics', {}).get('reserve_months', 0.0):.1f} months of expenses")
                if total_balance < 2000:
                    lines.append(f"- **Advisory Recommendation:** Postpone non-essential large purchases until liquid reserves cover at least 3 months of operating expenses.\n")
                else:
                    lines.append(f"- **Advisory Recommendation:** Ensure purchase leaves minimum 3 months emergency reserve intact.\n")
            elif "optimize" in query_lower or "expense" in query_lower:
                lines.append(f"**Monthly Outflow Optimization Analysis:**")
                lines.append(f"- **Total Monthly Expenses:** ${expenses:,.2f}")
                lines.append(f"- **Savings Rate Target:** Raise current {savings_rate:.1f}% savings rate by 5% through category spending caps.\n")
        else:
            lines.append(f"### Executive Financial Assessment\n")

        lines.append(f"**Financial Health Overview:**")
        lines.append(f"- **Composite Score:** {health_score}/100 ({health_status})")
        lines.append(f"- **Liquid Balance:** ${total_balance:,.2f}")
        lines.append(f"- **Period Cash Flow:** Income ${income:,.2f} | Expenses ${expenses:,.2f} | Net Savings ${net_savings:,.2f}")
        lines.append(f"- **Savings Rate:** {savings_rate:.1f}%\n")

        lines.append("#### Key Financial Observations:")
        for ins in insights:
            icon = "✅" if ins.severity == "positive" else ("⚠️" if ins.severity == "warning" else ("🚨" if ins.severity == "critical" else "ℹ️"))
            lines.append(f"- {icon} **{ins.title}:** {ins.details}")

        lines.append("\n#### Recommended Next Steps:")
        if warnings:
            for w in warnings:
                lines.append(f"- Address **{w.title}**: {w.details}")
        else:
            lines.append("- Maintain your current healthy savings habit and consider transferring surplus funds to high-yield reserves.")

        lines.append("- Continue monitoring discretionary category outflows in ExpenseFlowAI to protect cash reserves.")
        lines.append("\n*Note: This report was generated deterministically by ExpenseFlowAI Financial Engine.*")

        return "\n".join(lines)

    @staticmethod
    def render_structured_coach(
        insights: List[FinancialInsight],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Renders a structured JSON coaching report matching the exact schema expected
        by AIFinancialCoachService.
        """
        health_score = int(summary.get("health_score", 0))
        health_status = str(summary.get("health_status", "N/A"))
        period = str(summary.get("period", "30d"))

        health_metrics = summary.get("health_metrics", {})
        reserve_months = float(health_metrics.get("reserve_months", 0.0))
        budget_adherence_pct = float(health_metrics.get("budget_adherence_pct", 100.0))
        bill_reliability_pct = float(health_metrics.get("bill_reliability_pct", 100.0))

        snapshot = {
            "income": float(summary.get("period_income", 0.0)),
            "expenses": float(summary.get("period_expense", 0.0)),
            "savings": float(summary.get("period_savings", 0.0)),
            "savings_rate": float(summary.get("period_savings_rate", 0.0)),
            "health_score": health_score,
            "health_status": health_status,
            "reserve_months": reserve_months,
            "budget_adherence_pct": budget_adherence_pct,
            "bill_reliability_pct": bill_reliability_pct,
        }

        # Build Strengths
        strengths = [ins.details for ins in insights if ins.severity == "positive"]
        if not strengths:
            strengths.append("Active financial tracking established on ExpenseFlowAI workspace.")

        # Build Risks
        risks = [ins.details for ins in insights if ins.severity in ("warning", "critical")]
        if not risks:
            risks.append("Keep monitoring discretionary category outflows to sustain positive cash flow velocity.")

        # Build Recommendations
        recommendations = []
        if reserve_months < 3.0:
            recommendations.append(f"Build emergency reserves to 3.0 months (currently {reserve_months:.1f} months).")
        if snapshot["savings_rate"] < 20.0:
            recommendations.append(f"Automate a 5% monthly savings transfer to raise current savings rate ({snapshot['savings_rate']:.1f}%).")
        if budget_adherence_pct < 100.0:
            recommendations.append("Review exceeded budget categories and adjust discretionary spending limits.")
        if not recommendations:
            recommendations.append("Maintain current budget adherence and evaluate long-term investment options.")

        # Build Next Month Focus
        focus = [
            "Maintain 100% on-time bill payments to protect credit standing.",
            "Enforce category spending caps to optimize monthly net savings."
        ]

        summary_text = f"Your overall financial health is rated as {health_status} with a composite score of {health_score}/100 over the {period} period."
        encouragement_text = "Consistency is the foundation of wealth building. You are taking proactive control of your financial future!"

        return {
            "summary": summary_text,
            "financial_snapshot": snapshot,
            "strengths": strengths,
            "risks": risks,
            "recommendations": recommendations[:3],
            "next_month_focus": focus,
            "encouragement": encouragement_text,
            "confidence": 0.90,
        }

    @staticmethod
    def render_stream_chunks(text: str, words_per_chunk: int = 4) -> List[str]:
        """
        Splits rendered text into small token chunks for real-time SSE streaming.
        """
        words = text.split(" ")
        chunks = []
        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i:i + words_per_chunk])
            if i + words_per_chunk < len(words):
                chunk += " "
            chunks.append(chunk)
        return chunks
