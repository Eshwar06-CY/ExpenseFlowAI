"""
GoalPlannerAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.goal_planner import AIGoalPlannerService


class GoalPlannerAgent(BaseAgent):
    name = "GoalPlannerAgent"
    description = "Specializes in timeline estimation, required monthly goal contributions, and achievement probabilities."
    capabilities = ["goal_feasibility", "timeline_projection", "contribution_calculation"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Goal Planner Agent. Provide precise goal timeline evaluations based on cashflow."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        goal_service = AIGoalPlannerService(provider=self.provider)
        report = goal_service.evaluate_goal(
            db=db,
            user_id=user_id,
            goal_name="Target Goal",
            target_amount=80000.0
        )
        return {
            "summary": report.get("summary", "Goal evaluation complete."),
            "confidence": report.get("completion_probability", 0.90),
            "data": report
        }
