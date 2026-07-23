"""
Pydantic Schemas for Adaptive Financial Intelligence System - ExpenseFlowAI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class UserFeedbackRequest(BaseModel):
    event_type: Optional[str] = Field("RECOMMENDATION_RESPONSE", description="Event classification type e.g. RECOMMENDATION_RESPONSE, EARLY_BILL_PAYMENT", examples=["RECOMMENDATION_RESPONSE"])
    category: Optional[str] = Field(None, description="Financial category context e.g. Dining, Groceries, Savings", examples=["Dining"])
    recommendation_type: Optional[str] = Field(None, description="Specific recommendation type e.g. budget_cap, bill_reminder", examples=["budget_cap"])
    action: str = Field(..., description="Action taken: 'accepted', 'ignored', 'completed', 'dismissed'", examples=["accepted"])
    communication_style: Optional[str] = Field(None, description="Preferred AI tone: 'concise', 'detailed', 'direct'", examples=["concise"])
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata dictionary")


class PreferenceItem(BaseModel):
    key: str = Field(..., description="Preference key identifier")
    value: str = Field(..., description="Learned setting value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Personalization confidence score")


class AdaptiveIntelligenceResponse(BaseModel):
    discipline_score: int = Field(..., ge=0, le=100, description="Financial Discipline Score (0-100)", examples=[87])
    behavior_patterns: List[str] = Field(..., description="Identified behavioral habits & patterns", examples=["Consistently pays bills 5 days early", "Frequently ignores restaurant spending advice"])
    recommendation_effectiveness: float = Field(..., ge=0.0, le=1.0, description="Recommendation acceptance effectiveness rate (0.0 to 1.0)", examples=[0.82])
    personalization_confidence: float = Field(..., ge=0.0, le=1.0, description="Personalization confidence rating (0.0 to 1.0)", examples=[0.91])
    updated_preferences: List[PreferenceItem] = Field(default_factory=list, description="Application-level learned preferences and settings")
    explanation: str = Field(..., description="AI explanation of learned behavioral patterns and personalization adjustments")
