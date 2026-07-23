"""
AgentRouter - ExpenseFlowAI Multi-Agent System

Classifies user intent, selects 1 or more specialized domain agents, co-executes them,
and merges their structured outputs into a unified multi-agent synthesis response.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.financial_coach import FinancialCoachAgent
from app.agents.goal_planner import GoalPlannerAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.investment_agent import InvestmentAgent
from app.agents.subscription_agent import SubscriptionAgent
from app.agents.tax_agent import TaxAgent
from app.agents.debt_agent import DebtAgent
from app.agents.report_agent import ReportAgent
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


class AgentRouter:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()
        self._agents: Dict[str, BaseAgent] = {
            "FinancialCoachAgent": FinancialCoachAgent(provider=self.provider),
            "GoalPlannerAgent": GoalPlannerAgent(provider=self.provider),
            "BudgetAgent": BudgetAgent(provider=self.provider),
            "InvestmentAgent": InvestmentAgent(provider=self.provider),
            "SubscriptionAgent": SubscriptionAgent(provider=self.provider),
            "TaxAgent": TaxAgent(provider=self.provider),
            "DebtAgent": DebtAgent(provider=self.provider),
            "ReportAgent": ReportAgent(provider=self.provider),
        }

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities
            }
            for agent in self._agents.values()
        ]

    def route_and_execute(
        self,
        db: Session,
        user_id: int,
        message: str,
        period: str = "30d",
        forced_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Classifies intent, dispatches selected specialized agents, and merges findings.
        """
        # 1. Select Agents
        selected_names = forced_agents if forced_agents else self._select_agents(message)
        if not selected_names:
            selected_names = ["FinancialCoachAgent"]

        dispatched_agents = []
        agent_results = []
        summaries = []

        # 2. Co-execute Agents
        for name in selected_names:
            agent = self._agents.get(name)
            if not agent:
                continue

            try:
                res = agent.run(db=db, user_id=user_id, message=message, period=period)
                dispatched_agents.append(agent.name)
                agent_results.append({
                    "agent_name": agent.name,
                    "confidence": res.get("confidence", 0.90),
                    "summary": res.get("summary", ""),
                    "data": res.get("data", {})
                })
                summaries.append(f"**[{agent.name}]**: {res.get('summary', '')}")
            except Exception as exc:
                logger.error("Error executing agent %s: %s", name, str(exc))

        # 3. Merge Output
        if not agent_results:
            merged_response = "Unable to process query across dispatched agents."
        elif len(agent_results) == 1:
            merged_response = agent_results[0]["summary"]
        else:
            merged_response = "### Multi-Agent Synthesis:\n" + "\n\n".join(summaries)

        return {
            "query": message,
            "dispatched_agents": dispatched_agents,
            "agent_results": agent_results,
            "merged_response": merged_response
        }

    def _select_agents(self, text: str) -> List[str]:
        text_lower = text.lower()
        selected = []

        if any(k in text_lower for k in ["save", "goal", "target", "macbook", "trip", "buy"]):
            selected.append("GoalPlannerAgent")

        if any(k in text_lower for k in ["debt", "credit card", "pay off", "loan", "card"]):
            selected.append("DebtAgent")

        if any(k in text_lower for k in ["budget", "spent", "category", "grocery", "cap"]):
            selected.append("BudgetAgent")

        if any(k in text_lower for k in ["invest", "portfolio", "stock", "compound", "surplus"]):
            selected.append("InvestmentAgent")

        if any(k in text_lower for k in ["subscription", "netflix", "cancel", "recurring", "bill"]):
            selected.append("SubscriptionAgent")

        if any(k in text_lower for k in ["tax", "deduction", "write off"]):
            selected.append("TaxAgent")

        if any(k in text_lower for k in ["report", "audit", "summary"]):
            selected.append("ReportAgent")

        if not selected:
            selected.append("FinancialCoachAgent")

        return selected
