"""
Pydantic Schemas for Autonomous Workflow Engine - ExpenseFlowAI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WorkflowExecutionRequest(BaseModel):
    workflow_name: str = Field(..., description="Target workflow name e.g. ExpenseReductionWorkflow, GoalWorkflow", examples=["ExpenseReductionWorkflow"])
    period: Optional[str] = Field("30d", description="Analysis period e.g. 7d, 30d, 90d, 1y")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom parameters for the workflow e.g. target_amount, goal_name")


class WorkflowInfoResponse(BaseModel):
    name: str = Field(..., description="Workflow identifier name")
    description: str = Field(..., description="Workflow purpose and functionality")
    step_count: int = Field(..., description="Number of steps in the workflow pipeline")


class WorkflowExecutionResponse(BaseModel):
    workflow: str = Field(..., description="Executed workflow identifier")
    status: str = Field(..., description="Execution status: COMPLETED, FAILED, ROLLED_BACK")
    steps_completed: int = Field(..., description="Total number of workflow steps completed successfully")
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list, description="List of concrete actions executed during workflow")
    recommendations: List[str] = Field(default_factory=list, description="Generated recommendations from workflow execution")
    next_steps: List[str] = Field(default_factory=list, description="Follow-up action checklist items")
