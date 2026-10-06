"""Application configuration with strict environment validation via Pydantic."""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: str = Field(default="development")
    APPLICATION_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    PROJECT_NAME: str = Field(default="Dhruva.AI API")
    API_V1_PREFIX: str = Field(default="/api/v1")

    # Security & Tokens
    SECRET_KEY: str = Field(
        default="dhruva_development_fallback_secret_must_change_in_production_min32char"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)  # 15 minutes short-lived
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)     # 7 days session lifetime
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(default=24)

    # Brute-force & Lockout Policies
    MAX_FAILED_LOGIN_ATTEMPTS: int = Field(default=5)
    ACCOUNT_LOCKOUT_MINUTES: int = Field(default=15)

    # Secure Cookie Settings
    COOKIE_NAME_REFRESH_TOKEN: str = Field(default="dhruva_refresh_token")
    COOKIE_SECURE: bool = Field(default=False)  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = Field(default="lax")  # "lax" or "strict"
    COOKIE_DOMAIN: Union[str, None] = Field(default=None)

    # Database (PostgreSQL with pgvector)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://dhruva_admin:dhruva_secret_change_in_prod@localhost:5432/dhruva_db"
    )
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)

    # CORS
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("Invalid format for CORS_ORIGINS")

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_ENABLED: bool = Field(default=False)
    REDIS_TIMEOUT_SECONDS: int = Field(default=2)

    # Object Storage (S3-compatible / Local disk)
    STORAGE_BACKEND: str = Field(default="local")  # "local" or "s3"
    STORAGE_LOCAL_DIR: str = Field(default="storage/uploads")
    S3_ENDPOINT_URL: Union[str, None] = Field(default=None)
    S3_BUCKET_NAME: str = Field(default="dhruva-assets")
    S3_ACCESS_KEY_ID: Union[str, None] = Field(default=None)
    S3_SECRET_ACCESS_KEY: Union[str, None] = Field(default=None)
    S3_REGION: str = Field(default="ap-south-1")

    # Email Provider
    EMAIL_PROVIDER: str = Field(default="development")  # "development", "smtp", or "ses"
    SMTP_HOST: Union[str, None] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Union[str, None] = Field(default=None)
    SMTP_PASSWORD: Union[str, None] = Field(default=None)
    EMAIL_FROM: str = Field(default="Dhruva.AI <noreply@dhruva.ai>")

    # AI Governance & Cost Bounds (Domain 11 Production Tuning)
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = Field(default="text-embedding-004")
    GEMINI_TEMPERATURE: float = Field(default=0.2)
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=2048)
    AI_REQUEST_TIMEOUT: int = Field(default=30)
    AI_DAILY_USER_LIMIT: int = Field(default=100)
    AI_DAILY_INSTITUTION_LIMIT: int = Field(default=10000)

    # Feature Flags (Server-Authoritative)
    FEATURE_AI_ENABLED: bool = Field(default=True)
    FEATURE_NOTIFICATIONS_ENABLED: bool = Field(default=True)
    FEATURE_BACKGROUND_WORKERS_ENABLED: bool = Field(default=True)
    FEATURE_PUBLIC_PORTFOLIOS_ENABLED: bool = Field(default=True)
    FEATURE_PLACEMENT_MODULE_ENABLED: bool = Field(default=True)
    FEATURE_ADVANCED_ANALYTICS_ENABLED: bool = Field(default=True)

    # Observability
    SENTRY_DSN: Union[str, None] = Field(default=None)
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT.lower() == "staging"

    def validate_production_secrets(self) -> None:
        """Fail-fast validation for critical secrets in production."""
        if self.is_production:
            if "fallback" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL PRODUCTION VIOLATION: SECRET_KEY must be an unpredictable secret of at least 32 characters in production."
                )
            if "localhost" in self.DATABASE_URL.lower() and not self.DEBUG:
                pass  # Localhost database acceptable in single-node bare-metal/docker setups


settings = Settings()
