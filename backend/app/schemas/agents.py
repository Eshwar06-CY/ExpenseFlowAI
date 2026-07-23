"""
Pydantic Schemas for Multi-Agent AI System - ExpenseFlowAI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentDispatchRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User prompt or complex financial intent", examples=["I want to save $80,000 while paying off my credit card."])
    period: Optional[str] = Field("30d", description="Analysis period e.g. 7d, 30d, 90d, 1y")
    forced_agents: Optional[List[str]] = Field(None, description="Optional explicit list of agent names to dispatch e.g. ['GoalPlannerAgent', 'DebtAgent']")


class AgentInfoResponse(BaseModel):
    name: str = Field(..., description="Unique agent identifier name")
    description: str = Field(..., description="Agent domain expertise summary")
    capabilities: List[str] = Field(default_factory=list, description="Key domain capabilities")


class AgentResultItem(BaseModel):
    agent_name: str = Field(..., description="Name of the responding specialized agent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent response confidence score")
    summary: str = Field(..., description="Agent domain summary assessment")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured domain output data")


class AgentDispatchResponse(BaseModel):
    query: str = Field(..., description="Original user prompt query")
    dispatched_agents: List[str] = Field(..., description="List of specialized agents that executed")
    agent_results: List[AgentResultItem] = Field(..., description="Individual outputs returned by dispatched agents")
    merged_response: str = Field(..., description="Unified executive response combining all agent findings")
