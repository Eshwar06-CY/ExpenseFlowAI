"""
Pydantic Schemas for AI Persistent Memory - ExpenseFlowAI
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AIMemoryCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=50, description="Memory category e.g. financial_goal, risk_preference, lifestyle_note", examples=["financial_goal"])
    key: str = Field(..., min_length=1, max_length=100, description="Unique key identifier e.g. macbook_goal, relocation_city", examples=["macbook_goal"])
    value: str = Field(..., min_length=1, description="Memory content value", examples=["MacBook Pro M4"])
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Confidence rating between 0.0 and 1.0")


class AIMemoryUpdate(BaseModel):
    value: Optional[str] = Field(None, min_length=1, description="Updated memory content value")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated confidence rating")
    is_active: Optional[bool] = Field(None, description="Active status flag")


class AIMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique memory ID")
    user_id: int = Field(..., description="Owner user ID")
    category: str = Field(..., description="Memory category")
    key: str = Field(..., description="Memory key identifier")
    value: str = Field(..., description="Memory content value")
    confidence: float = Field(..., description="Confidence score")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Timestamp of memory creation")
    updated_at: datetime = Field(..., description="Timestamp of memory update")


class AIMemoryExportResponse(BaseModel):
    user_id: int = Field(..., description="User ID exporting memories")
    exported_at: str = Field(..., description="Export timestamp")
    total_memories: int = Field(..., description="Count of exported memory records")
    memories: List[AIMemoryResponse] = Field(..., description="List of user memory objects")
