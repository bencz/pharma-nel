"""
Application Settings using pydantic-settings.

Environment variables are loaded from .env file and can be overridden.
"""

from functools import lru_cache
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Pharma NER/NEL API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENV")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON", description="Use JSON format for logs in production")

    # ArangoDB
    arango_host: str = Field(default="http://localhost:8529", alias="ARANGO_HOST")
    arango_database: str = Field(default="pharma_ner", alias="ARANGO_DATABASE")
    arango_user: str = Field(default="root", alias="ARANGO_USER")
    arango_password: str = Field(default="", alias="ARANGO_PASSWORD")

    # FDA API
    fda_api_key: str | None = Field(default=None, alias="FDA_API_KEY")
    fda_base_url: str = Field(default="https://api.fda.gov", alias="FDA_BASE_URL")
    fda_timeout: int = Field(default=30, alias="FDA_TIMEOUT")
    fda_max_retries: int = Field(default=3, alias="FDA_MAX_RETRIES")

    # RxNorm API
    rxnorm_base_url: str = Field(default="https://rxnav.nlm.nih.gov/REST", alias="RXNORM_BASE_URL")
    rxnorm_timeout: int = Field(default=30, alias="RXNORM_TIMEOUT")
    rxnorm_max_retries: int = Field(default=3, alias="RXNORM_MAX_RETRIES")

    # UNII API
    unii_base_url: str = Field(default="https://api.fda.gov/other/substance.json", alias="UNII_BASE_URL")
    unii_timeout: int = Field(default=30, alias="UNII_TIMEOUT")
    unii_max_retries: int = Field(default=3, alias="UNII_MAX_RETRIES")

    # OpenAI
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_timeout: int = Field(default=60, alias="OPENAI_TIMEOUT")

    # HTTP Client
    http_verify_ssl: bool = Field(default=True, alias="HTTP_VERIFY_SSL", description="Verify SSL certificates for HTTP clients")

    # CORS
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


API_V1_PREFIX: Final[str] = "/api/v1"
