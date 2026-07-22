import re
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, field_validator, computed_field

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class UserBase(BaseModel):
    email: str
    full_name: str
    profile_picture: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Invalid email format.")
        normalized = v.strip().lower()
        if not re.match(EMAIL_REGEX, normalized):
            raise ValueError("Invalid email format.")
        return normalized

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9\W]", v):
            raise ValueError("Password must contain at least one number or special character.")
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    profile_picture: Optional[str] = None
    password: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: Any) -> Optional[str]:
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Invalid email format.")
            normalized = v.strip().lower()
            if not re.match(EMAIL_REGEX, normalized):
                raise ValueError("Invalid email format.")
            return normalized
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long.")
            if not re.search(r"[A-Z]", v):
                raise ValueError("Password must contain at least one uppercase letter.")
            if not re.search(r"[a-z]", v):
                raise ValueError("Password must contain at least one lowercase letter.")
            if not re.search(r"[0-9\W]", v):
                raise ValueError("Password must contain at least one number or special character.")
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    email_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_email_verified(self) -> bool:
        return self.is_verified

    @computed_field
    @property
    def name(self) -> str:
        return self.full_name

    model_config = ConfigDict(from_attributes=True)
