from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

class AccountBase(BaseModel):
    name: str
    type: str
    balance: float = 0.0
    currency: str = "USD"

class AccountCreate(AccountBase):
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"bank", "cash", "credit"}
        if v.lower() not in valid_types:
            raise ValueError(f"Account type must be one of {valid_types}")
        return v.lower()

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = {"bank", "cash", "credit"}
            if v.lower() not in valid_types:
                raise ValueError(f"Account type must be one of {valid_types}")
            return v.lower()
        return v

class AccountResponse(AccountBase):
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)
