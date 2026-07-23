"""
Pydantic Schemas for AI Spending Anomaly Detection - ExpenseFlowAI
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AnomalySeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OverallRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyItem(BaseModel):
    severity: AnomalySeverity = Field(..., description="Severity level: INFO, LOW, MEDIUM, HIGH, CRITICAL")
    category: str = Field(..., description="Financial category or indicator affected (e.g. Food, Subscriptions, Emergency Fund)")
    message: str = Field(..., description="Clear explanation of the detected anomaly")
    possible_reason: str = Field(..., description="Probable underlying cause or financial driver")
    recommendation: str = Field(..., description="Actionable recommendation to address the anomaly")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score rating (0.0 - 1.0)")


class AIAnomalyDetectionResponse(BaseModel):
    anomalies: List[AnomalyItem] = Field(default_factory=list, description="List of detected spending and financial anomalies")
    overall_risk: OverallRisk = Field(OverallRisk.LOW, description="Aggregated risk assessment level")
    summary: str = Field(..., description="High-level summary of the anomaly detection evaluation")
