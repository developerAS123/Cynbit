from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cynbit Backend Services"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: Union[bool, str] = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug")
        return bool(v)
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./cynbit_local.db",
        description="Async database connection string"
    )
    
    # Cryptographic & Session Configuration
    JWT_SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="High-entropy HMAC secret for signing JWT tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    COOKIE_NAME: str = "cynbit_session"
    
    # Cashfree Payment Gateway Credentials
    CASHFREE_APP_ID: str = Field(default="TEST_APP_ID", description="Cashfree Merchant App ID")
    CASHFREE_SECRET_KEY: str = Field(default="TEST_SECRET_KEY", description="Cashfree Merchant Secret Key")
    CASHFREE_ENVIRONMENT: str = Field(default="sandbox", description="'sandbox' or 'production'")
    CASHFREE_API_VERSION: str = "2023-08-01"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "https://www.cynbit.in",
        "https://cynbit.in",
        "https://bitelevate.cynbit.in",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Rate Limiting Defaults
    RATE_LIMIT_DEFAULT_LIMIT: int = 60
    RATE_LIMIT_DEFAULT_WINDOW: int = 60
    RATE_LIMIT_INQUIRY_LIMIT: int = 5
    RATE_LIMIT_APPLICATION_LIMIT: int = 3
    RATE_LIMIT_AUTH_LIMIT: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
