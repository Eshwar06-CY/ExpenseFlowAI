import os
from typing import Optional, Any
from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ExpenseFlow AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # "development", "production", "testing"
    LOG_LEVEL: str = "INFO"
    DB_ECHO: bool = False

    # MySQL connection parameters (optional if DATABASE_URL is set)
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_HOST: Optional[str] = None
    MYSQL_PORT: Optional[str] = None
    MYSQL_DB: Optional[str] = None

    # Database connection URL
    DATABASE_URL: str = "sqlite:///./dev.db"

    # JWT configuration
    JWT_SECRET: str = "super_secret_key_change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Password reset
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP & Brevo email configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: str = "ExpenseFlow AI"

    # Brevo-specific aliases
    BREVO_SMTP_SERVER: Optional[str] = None
    BREVO_SMTP_PORT: Optional[int] = None
    BREVO_SMTP_USERNAME: Optional[str] = None
    BREVO_SMTP_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None

    # AI Financial Advisor & Local LLM (Ollama)
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: float = 60.0

    @property
    def effective_smtp_server(self) -> Optional[str]:
        return self.BREVO_SMTP_SERVER or self.SMTP_HOST

    @property
    def effective_smtp_port(self) -> int:
        return self.BREVO_SMTP_PORT or self.SMTP_PORT or 587

    @property
    def effective_smtp_username(self) -> Optional[str]:
        return self.BREVO_SMTP_USERNAME or self.SMTP_USER

    @property
    def effective_smtp_password(self) -> Optional[str]:
        return self.BREVO_SMTP_PASSWORD or self.SMTP_PASSWORD

    @property
    def effective_mail_from(self) -> Optional[str]:
        return self.MAIL_FROM or self.EMAILS_FROM_EMAIL or self.effective_smtp_username

    @property
    def is_smtp_configured(self) -> bool:
        return bool(
            self.effective_smtp_server and
            self.effective_smtp_username and
            self.effective_smtp_password
        )

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower not in {"development", "production", "testing"}:
            raise ValueError("ENVIRONMENT must be development, production, or testing")
        return v_lower

    @model_validator(mode="before")
    @classmethod
    def assemble_db_connection(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check environment
            env = data.get("ENVIRONMENT", os.environ.get("ENVIRONMENT", "development")).lower().strip()
            
            # Apply sensible environmental defaults
            if env == "testing":
                data.setdefault("DATABASE_URL", "sqlite:///./test.db")
                data.setdefault("LOG_LEVEL", "WARNING")
                data.setdefault("DB_ECHO", False)
            elif env == "production":
                data.setdefault("LOG_LEVEL", "INFO")
                data.setdefault("DB_ECHO", False)
            else:
                data.setdefault("DATABASE_URL", "sqlite:///./dev.db")
                data.setdefault("LOG_LEVEL", "INFO")
                data.setdefault("DB_ECHO", False)  # Can be overridden in env

            # Build database connection if MySQL components are provided
            user = data.get("MYSQL_USER")
            password = data.get("MYSQL_PASSWORD")
            host = data.get("MYSQL_HOST")
            port = data.get("MYSQL_PORT", "3306")
            db = data.get("MYSQL_DB")
            
            if user and password and host and db:
                data["DATABASE_URL"] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
                
        return data

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET == "super_secret_key_change_me_in_production":
                raise ValueError("INSECURE DEFAULT JWT_SECRET CANNOT BE USED IN PRODUCTION!")
            if len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production for cryptographic strength!")
        return self

settings = Settings()
