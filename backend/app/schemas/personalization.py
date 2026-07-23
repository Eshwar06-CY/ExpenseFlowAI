"""
Pydantic Schemas for Personalization & Privacy Center - ExpenseFlowAI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LearnedBehaviorItem(BaseModel):
    id: int = Field(..., description="Unique behavior observation ID", examples=[1])
    category: str = Field(..., description="Category context (e.g. Dining, Savings, Bills, Goals)", examples=["Dining"])
    observation: str = Field(..., description="Learned behavior observation text", examples=["Frequently exceeds budget."])
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score (0.0 to 1.0)", examples=[0.91])
    created_at: Optional[str] = Field(None, description="ISO timestamp of observation")


class PersonalizationPreferencesUpdate(BaseModel):
    enable_ai_personalization: Optional[bool] = Field(None, description="Toggle AI personalization")
    enable_ai_learning: Optional[bool] = Field(None, description="Toggle AI learning")
    coaching_style: Optional[str] = Field(None, description="Coaching style: friendly, professional, motivational", examples=["professional"])
    recommendation_frequency: Optional[str] = Field(None, description="Recommendation frequency: every_login, daily, weekly, important_only", examples=["daily"])
    response_detail: Optional[str] = Field(None, description="Response detail: brief, balanced, detailed", examples=["balanced"])
    
    enable_smart_suggestions: Optional[bool] = Field(None, description="Enable smart suggestions")
    enable_goal_recommendations: Optional[bool] = Field(None, description="Enable goal recommendations")
    enable_spending_insights: Optional[bool] = Field(None, description="Enable spending insights")
    
    enable_memory: Optional[bool] = Field(None, description="Enable persistent AI memory")
    enable_behavior_tracking: Optional[bool] = Field(None, description="Enable behavior tracking")
    enable_goal_tracking: Optional[bool] = Field(None, description="Enable goal tracking")
    enable_communication_preference_learning: Optional[bool] = Field(None, description="Enable communication preference learning")


class PersonalizationOverviewResponse(BaseModel):
    learning_enabled: bool = Field(..., description="Whether AI learning is enabled")
    memory_enabled: bool = Field(..., description="Whether AI memory is enabled")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall personalization confidence (0.0 to 1.0)", examples=[0.92])
    preferences: Dict[str, Any] = Field(..., description="Full user personalization settings dictionary")
    behaviors: List[LearnedBehaviorItem] = Field(default_factory=list, description="Active learned behavior items")


class BehaviorDeleteResponse(BaseModel):
    success: bool = Field(True, description="Deletion success status")
    message: str = Field(..., description="Human-readable result message")
    deleted_id: int = Field(..., description="ID of deleted behavior item")


class AIDataExportResponse(BaseModel):
    exported_at: str = Field(..., description="ISO timestamp of export")
    user_id: int = Field(..., description="User ID")
    preferences: Dict[str, Any] = Field(..., description="User preferences dictionary")
    behaviors: List[Dict[str, Any]] = Field(default_factory=list, description="Exported learned behavior observations")
    memories: List[Dict[str, Any]] = Field(default_factory=list, description="Exported persistent AI memory entries")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Exported AI interaction statistics")
