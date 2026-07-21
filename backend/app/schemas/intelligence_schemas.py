from datetime import datetime, date
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict

class FinancialInsightResponse(BaseModel):
    id: int
    user_id: int
    type: str  # 'trend', 'health', 'pattern', 'forecast'
    title: str
    description: str
    data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FinancialEventResponse(BaseModel):
    id: int
    user_id: int
    event_type: str
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high'
    event_date: datetime
    is_dismissed: bool

    model_config = ConfigDict(from_attributes=True)

class DailyBriefingResponse(BaseModel):
    id: int
    user_id: int
    date: date
    content: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
