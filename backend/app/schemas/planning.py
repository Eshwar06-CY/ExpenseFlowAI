from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.category import CategoryResponse
from app.schemas.account import AccountResponse

# --- Budget Schemas ---
class BudgetBase(BaseModel):
    category_id: int
    amount: float
    month: str  # YYYY-MM format

class BudgetCreate(BudgetBase):
    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Month must be in YYYY-MM format.")
        return v

class BudgetUpdate(BaseModel):
    amount: float

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    spent: float
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Goal Schemas ---
class GoalBase(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0.0
    target_date: Optional[datetime] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    target_date: Optional[datetime] = None

class GoalResponse(GoalBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Bill Schemas ---
class BillBase(BaseModel):
    name: str
    amount: float
    due_date: datetime
    is_paid: bool = False
    category_id: Optional[int] = None

class BillCreate(BaseModel):
    name: str
    amount: float
    due_date: datetime
    category_id: Optional[int] = None

class BillUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[datetime] = None
    is_paid: Optional[bool] = None
    category_id: Optional[int] = None

class BillResponse(BillBase):
    id: int
    user_id: int
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Recurring Transaction Schemas ---
class RecurringTransactionBase(BaseModel):
    type: str  # 'income', 'expense'
    amount: float
    description: str
    frequency: str  # 'daily', 'weekly', 'monthly', 'yearly'
    start_date: datetime
    category_id: Optional[int] = None
    account_id: int

class RecurringTransactionCreate(RecurringTransactionBase):
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid = {"income", "expense"}
        if v.lower() not in valid:
            raise ValueError(f"Type must be one of {valid}")
        return v.lower()

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid = {"daily", "weekly", "monthly", "yearly"}
        if v.lower() not in valid:
            raise ValueError(f"Frequency must be one of {valid}")
        return v.lower()

class RecurringTransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = {"income", "expense"}
            if v.lower() not in valid:
                raise ValueError(f"Type must be one of {valid}")
            return v.lower()
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = {"daily", "weekly", "monthly", "yearly"}
            if v.lower() not in valid:
                raise ValueError(f"Frequency must be one of {valid}")
            return v.lower()
        return v

class RecurringTransactionResponse(RecurringTransactionBase):
    id: int
    user_id: int
    last_run: Optional[datetime] = None
    next_run: datetime
    category: Optional[CategoryResponse] = None
    account: Optional[AccountResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Notification Schemas ---
class NotificationBase(BaseModel):
    title: str
    message: str
    is_read: bool

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
