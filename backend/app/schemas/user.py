import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class UserBase(BaseModel):
    email: str
    full_name: str
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(EMAIL_REGEX, v):
            raise ValueError("Invalid email format.")
        return v.lower().strip()

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

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(EMAIL_REGEX, v):
                raise ValueError("Invalid email format.")
            return v.lower().strip()
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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
