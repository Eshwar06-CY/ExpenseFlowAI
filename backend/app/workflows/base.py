"""
Base Workflow Engine Core Architecture - ExpenseFlowAI

Provides Task Planner, Task Queueing, Agent Step Execution, Step Validation,
Retry mechanisms, and Rollback management for multi-step autonomous workflows.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


class WorkflowStep:
    def __init__(
        self,
        name: str,
        handler: Callable[[Session, int, Dict[str, Any]], Dict[str, Any]],
        rollback_handler: Optional[Callable[[Session, int, Dict[str, Any]], None]] = None,
        max_retries: int = 2
    ):
        self.name = name
        self.handler = handler
        self.rollback_handler = rollback_handler
        self.max_retries = max_retries


class BaseWorkflow(ABC):
    name: str = "BaseWorkflow"
    description: str = "Base Workflow Interface"

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()
        self.steps: List[WorkflowStep] = []
        self._setup_steps()

    @abstractmethod
    def _setup_steps(self):
        """Define steps sequence for the workflow."""
        pass

    def run(
        self,
        db: Session,
        user_id: int,
        parameters: Optional[Dict[str, Any]] = None,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Executes multi-step workflow pipeline:
        1. Iterates steps in sequence.
        2. Retries failed steps up to step.max_retries.
        3. If step permanently fails, executes rollbacks in reverse order.
        4. Returns structured progress report.
        """
        params = parameters or {}
        context: Dict[str, Any] = {"period": period, **params}
        actions_taken: List[Dict[str, Any]] = []
        recommendations: List[str] = []
        next_steps: List[str] = []
        completed_steps: List[WorkflowStep] = []

        for step in self.steps:
            retry_count = 0
            step_success = False
            last_error = None

            while retry_count <= step.max_retries and not step_success:
                try:
                    res = step.handler(db, user_id, context)
                    step_success = True
                    completed_steps.append(step)

                    if res.get("action"):
                        actions_taken.append(res["action"])
                    if res.get("recommendation"):
                        recommendations.append(res["recommendation"])
                    if res.get("next_step"):
                        next_steps.append(res["next_step"])
                    if res.get("context_update"):
                        context.update(res["context_update"])

                except Exception as exc:
                    retry_count += 1
                    last_error = exc
                    logger.warning("Workflow '%s' step '%s' failed (attempt %d/%d): %s",
                                   self.name, step.name, retry_count, step.max_retries + 1, str(exc))

            if not step_success:
                logger.error("Workflow '%s' failed at step '%s'. Triggering rollback sequence.", self.name, step.name)
                self._execute_rollbacks(db, user_id, completed_steps, context)
                return {
                    "workflow": self.name,
                    "status": "ROLLED_BACK",
                    "steps_completed": len(completed_steps),
                    "actions_taken": actions_taken,
                    "recommendations": recommendations,
                    "next_steps": [f"Fix failure in step '{step.name}': {str(last_error)}"]
                }

        return {
            "workflow": self.name,
            "status": "COMPLETED",
            "steps_completed": len(completed_steps),
            "actions_taken": actions_taken,
            "recommendations": recommendations,
            "next_steps": next_steps
        }

    def _execute_rollbacks(
        self,
        db: Session,
        user_id: int,
        completed_steps: List[WorkflowStep],
        context: Dict[str, Any]
    ):
        """Rolls back completed steps in reverse order."""
        for step in reversed(completed_steps):
            if step.rollback_handler:
                try:
                    step.rollback_handler(db, user_id, context)
                    logger.info("Successfully rolled back step '%s' in workflow '%s'.", step.name, self.name)
                except Exception as exc:
                    logger.error("Failed rollback for step '%s': %s", step.name, str(exc))
