"""
WorkflowEngine Registry & Dispatcher - ExpenseFlowAI Autonomous Workflow Engine

Manages registration and execution of multi-step autonomous workflows:
- GoalWorkflow
- BudgetOptimizerWorkflow
- ExpenseReductionWorkflow
- SubscriptionCleanupWorkflow
- FinancialReviewWorkflow
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workflows.base import BaseWorkflow
from app.workflows.goal_workflow import GoalWorkflow
from app.workflows.budget_optimizer import BudgetOptimizerWorkflow
from app.workflows.expense_reduction import ExpenseReductionWorkflow
from app.workflows.subscription_cleanup import SubscriptionCleanupWorkflow
from app.workflows.financial_review import FinancialReviewWorkflow
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()
        self._workflows: Dict[str, BaseWorkflow] = {
            "GoalWorkflow": GoalWorkflow(provider=self.provider),
            "BudgetOptimizerWorkflow": BudgetOptimizerWorkflow(provider=self.provider),
            "ExpenseReductionWorkflow": ExpenseReductionWorkflow(provider=self.provider),
            "SubscriptionCleanupWorkflow": SubscriptionCleanupWorkflow(provider=self.provider),
            "FinancialReviewWorkflow": FinancialReviewWorkflow(provider=self.provider),
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": wf.name,
                "description": wf.description,
                "step_count": len(wf.steps)
            }
            for wf in self._workflows.values()
        ]

    def execute_workflow(
        self,
        db: Session,
        user_id: int,
        workflow_name: str,
        period: str = "30d",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Looks up workflow by name and executes multi-step pipeline.
        """
        wf = self._workflows.get(workflow_name)
        if not wf:
            raise ValueError(f"Workflow '{workflow_name}' not found. Available: {list(self._workflows.keys())}")

        return wf.run(db=db, user_id=user_id, parameters=parameters, period=period)
