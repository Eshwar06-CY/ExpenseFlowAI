from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.schemas.account import AccountResponse
from app.schemas.category import CategoryResponse

class TransactionBase(BaseModel):
    type: str
    amount: float
    description: Optional[str] = None
    date: datetime
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    to_account_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"income", "expense", "transfer"}
        if v.lower() not in valid_types:
            raise ValueError(f"Transaction type must be one of {valid_types}")
        return v.lower()

    @model_validator(mode="after")
    def validate_transaction_details(self) -> "TransactionCreate":
        if self.type == "transfer":
            if not self.account_id or not self.to_account_id:
                raise ValueError("Both account_id and to_account_id are required for transfers.")
            if self.account_id == self.to_account_id:
                raise ValueError("Source and destination accounts must be different for transfers.")
        else:
            if not self.account_id:
                raise ValueError(f"account_id is required for {self.type} transactions.")
        return self

class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    to_account_id: Optional[int] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = {"income", "expense", "transfer"}
            if v.lower() not in valid_types:
                raise ValueError(f"Transaction type must be one of {valid_types}")
            return v.lower()
        return v

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    category: Optional[CategoryResponse] = None
    account: Optional[AccountResponse] = None
    to_account: Optional[AccountResponse] = None

    model_config = ConfigDict(from_attributes=True)
