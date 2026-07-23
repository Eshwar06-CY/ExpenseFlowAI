"""
Pydantic Schemas for AI Function Calling & Tool Execution - ExpenseFlowAI
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    FAILED = "FAILED"
    INVALID_TOOL = "INVALID_TOOL"


class AIToolActionRequest(BaseModel):
    message: Optional[str] = Field(None, description="User intent text e.g. 'Create a grocery budget of 7000'", examples=["Create a grocery budget of 7000"])
    tool_name: Optional[str] = Field(None, description="Direct tool name e.g. BudgetTool, GoalTool, ExpenseTool", examples=["BudgetTool"])
    action: Optional[str] = Field(None, description="Specific tool action e.g. create_budget, delete_subscription", examples=["create_budget"])
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action parameters dictionary")
    confirmed: Optional[bool] = Field(False, description="Flag explicitly confirming destructive action execution")


class AIToolExecutionResponse(BaseModel):
    tool: str = Field(..., description="Executed tool identifier name")
    status: ToolExecutionStatus = Field(..., description="Execution status: SUCCESS, REQUIRES_CONFIRMATION, FAILED, INVALID_TOOL")
    result: Dict[str, Any] = Field(default_factory=dict, description="Structured result metadata returned by backend tool service")
    assistant_response: str = Field(..., description="LLM assistant explanation of outcome")
    confirmation_prompt: Optional[str] = Field(None, description="User confirmation prompt if status is REQUIRES_CONFIRMATION")
