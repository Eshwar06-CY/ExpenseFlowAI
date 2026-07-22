import re
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_email_verified: bool = False

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format.")
        return v.lower().strip()

class ResendVerificationRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format.")
        return v.lower().strip()

class ResetPasswordRequest(BaseModel):
    token: str
    password: Optional[str] = None
    confirm_password: Optional[str] = None
    new_password: Optional[str] = None

    @model_validator(mode="after")
    def validate_password_payload(self) -> "ResetPasswordRequest":
        raw_pass = self.password or self.new_password
        if not raw_pass:
            raise ValueError("Password is required.")

        if self.confirm_password is not None and self.confirm_password != raw_pass:
            raise ValueError("Passwords do not match.")

        if len(raw_pass) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", raw_pass):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", raw_pass):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9\W]", raw_pass):
            raise ValueError("Password must contain at least one number or special character.")

        self.password = raw_pass
        return self

