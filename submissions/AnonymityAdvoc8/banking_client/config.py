"""
Configuration management for the banking client.

Supports environment variables and .env files for flexible configuration.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    api_base_url: str = "http://localhost:8123"
    api_timeout: int = 30
    api_max_retries: int = 3
    api_retry_backoff: float = 0.5

    # Authentication
    auth_username: str = "admin"
    auth_password: str = "password123"
    auth_cache_enabled: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str | None = None

    # Feature Flags
    enable_authentication: bool = False
    enable_request_logging: bool = True
    enable_response_caching: bool = False

    # Connection Pooling
    connection_pool_size: int = 10
    connection_pool_maxsize: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def transfer_url(self) -> str:
        """Get the full transfer endpoint URL."""
        return f"{self.api_base_url}/transfer"

    @property
    def auth_url(self) -> str:
        """Get the full authentication endpoint URL."""
        return f"{self.api_base_url}/authToken"

    @property
    def accounts_url(self) -> str:
        """Get the full accounts endpoint URL."""
        return f"{self.api_base_url}/accounts"

    def validate_url(self, account_id: str) -> str:
        """Get the account validation URL."""
        return f"{self.api_base_url}/accounts/validate/{account_id}"

    def balance_url(self, account_id: str) -> str:
        """Get the account balance URL."""
        return f"{self.api_base_url}/accounts/balance/{account_id}"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
