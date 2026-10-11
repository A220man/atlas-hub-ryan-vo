from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "atlas-hub-ryan-vo"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")
    APP_SECRET_KEY: str = Field(default="atlas-hub-dev-insecure-secret-key-32b")
    DATABASE_URL: str = Field(default="sqlite:///./atlas_hub.db")
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)

    # Local Demo Mode: Refused in production
    DEMO_MODE: bool = Field(default=False)

    # Keycloak / OIDC configuration
    OIDC_ISSUER: Optional[str] = Field(default=None)
    OIDC_CLIENT_ID: str = Field(default="atlas-hub-app")
    OIDC_CLIENT_SECRET: Optional[str] = Field(default=None)
    OIDC_AUDIENCE: str = Field(default="atlas-hub-app")
    OIDC_DISCOVERY_URL: Optional[str] = Field(default=None)
    OIDC_ALGORITHMS: List[str] = Field(default_factory=lambda: ["RS256", "HS256"])

    # Optional server-side LLM Advisory provider settings
    LLM_PROVIDER: str = Field(default="openai-compatible")
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    LLM_API_KEY: Optional[str] = Field(default=None)
    LLM_BASE_URL: Optional[str] = Field(default=None)

    @field_validator("DEMO_MODE")
    @classmethod
    def validate_demo_mode(cls, v: bool, info) -> bool:
        env = info.data.get("APP_ENV", "development").lower()
        if env == "production" and v:
            raise ValueError("DEMO_MODE is strictly forbidden in production mode.")
        return v

    def validate_runtime_guards(self) -> None:
        """Enforce strict production startup rules."""
        if self.APP_ENV.lower() == "production":
            if self.DEMO_MODE:
                raise RuntimeError("Refusing to start: DEMO_MODE must be False in production.")
            if not self.OIDC_ISSUER:
                raise RuntimeError("Refusing to start: OIDC_ISSUER is required in production.")


settings = Settings()
