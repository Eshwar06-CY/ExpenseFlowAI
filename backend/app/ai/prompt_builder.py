"""
Prompt Builder for ExpenseFlowAI AI Financial Advisor

Formats verified financial metrics from FinanceEngine into a clean, structured
context block for LLM consumption, stripping away internal database IDs or raw sensitive fields.
"""

from typing import Dict, Any, List, Optional
from app.ai.system_prompt import SYSTEM_PROMPT


class PromptBuilder:
    @staticmethod
    def build_financial_context(financial_summary: Dict[str, Any]) -> str:
        """
        Formats financial metrics into structured markdown text.
        """
        total_balance = financial_summary.get("total_balance", 0.0)
        period = financial_summary.get("period", "30d")
        period_income = financial_summary.get("period_income", 0.0)
        period_expense = financial_summary.get("period_expense", 0.0)
        period_savings = financial_summary.get("period_savings", 0.0)
        savings_rate = financial_summary.get("period_savings_rate", 0.0)
        health_score = financial_summary.get("health_score", 0)
        health_status = financial_summary.get("health_status", "N/A")

        category_spending: List[Dict[str, Any]] = financial_summary.get("category_spending", [])
        health_metrics: Dict[str, Any] = financial_summary.get("health_metrics", {})

        top_categories_str = "None recorded"
        if category_spending:
            cat_lines = [
                f"  - {c.get('category', 'General')}: ${c.get('amount', 0.0):,.2f} ({c.get('percentage', 0.0):.1f}%)"
                for c in category_spending[:5]
            ]
            top_categories_str = "\n".join(cat_lines)

        reserve_months = health_metrics.get("reserve_months", 0.0)
        budget_adherence = health_metrics.get("budget_adherence_pct", 100.0)
        bill_reliability = health_metrics.get("bill_reliability_pct", 100.0)

        context = f"""
VERIFIED FINANCIAL CONTEXT (Source: ExpenseFlowAI FinanceEngine):
-------------------------------------------------------------
- Total Available Balance: ${total_balance:,.2f}
- Active Analysis Window: {period}
- Total Income ({period}): ${period_income:,.2f}
- Total Expenses ({period}): ${period_expense:,.2f}
- Net Savings ({period}): ${period_savings:,.2f}
- Savings Rate: {savings_rate:.1f}%
- Financial Health Score: {health_score}/100 ({health_status})
- Emergency Cash Reserve: {reserve_months:.1f} months of expenses
- Budget Adherence Rate: {budget_adherence:.1f}%
- Bill Payment Reliability: {bill_reliability:.1f}%

Top Spending Categories ({period}):
{top_categories_str}
-------------------------------------------------------------
"""
        return context.strip()

    @classmethod
    def build_prompt(
        cls,
        financial_summary: Dict[str, Any],
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Combines formatted financial context, conversation history (if provided),
        and the user's question into a single final prompt.
        """
        context_block = cls.build_financial_context(financial_summary)

        history_block = ""
        if chat_history:
            lines = []
            for msg in chat_history[-4:]:  # Include last 4 turns for context
                role = "User" if msg.get("role") == "user" else "Advisor"
                lines.append(f"{role}: {msg.get('content', '')}")
            if lines:
                history_block = "PREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(lines) + "\n\n"

        prompt = f"{context_block}\n\n{history_block}USER QUESTION:\n{user_message}\n\nADVISOR RESPONSE:"
        return prompt

    @staticmethod
    def get_system_prompt() -> str:
        return SYSTEM_PROMPT
