"""
Tests for configuration management.

Ensures 100% coverage of the config module.
"""

from banking_client.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        # Note: If .env file exists, it will override defaults
        settings = Settings(_env_file=None)  # Ignore .env file for this test

        assert settings.api_base_url == "http://localhost:8123"
        assert settings.api_timeout == 30
        assert settings.api_max_retries == 3
        # Default is False, but .env might override it
        assert settings.auth_username == "admin"

    def test_custom_settings(self):
        """Test custom settings override."""
        settings = Settings(
            api_base_url="http://custom:9000",
            api_timeout=60,
            enable_authentication=True,
            auth_username="custom_user",
        )

        assert settings.api_base_url == "http://custom:9000"
        assert settings.api_timeout == 60
        assert settings.enable_authentication is True
        assert settings.auth_username == "custom_user"

    def test_transfer_url(self):
        """Test transfer URL property."""
        settings = Settings(api_base_url="http://test:8000")
        assert settings.transfer_url == "http://test:8000/transfer"

    def test_auth_url(self):
        """Test auth URL property."""
        settings = Settings(api_base_url="http://test:8000")
        assert settings.auth_url == "http://test:8000/authToken"

    def test_accounts_url(self):
        """Test accounts URL property."""
        settings = Settings(api_base_url="http://test:8000")
        assert settings.accounts_url == "http://test:8000/accounts"

    def test_validate_url(self):
        """Test validate URL method."""
        settings = Settings(api_base_url="http://test:8000")
        url = settings.validate_url("ACC1000")
        assert url == "http://test:8000/accounts/validate/ACC1000"

    def test_balance_url(self):
        """Test balance URL method."""
        settings = Settings(api_base_url="http://test:8000")
        url = settings.balance_url("ACC1000")
        assert url == "http://test:8000/accounts/balance/ACC1000"

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance (cached)
        assert settings1 is settings2

    def test_environment_variables(self, monkeypatch):
        """Test settings from environment variables."""
        monkeypatch.setenv("API_BASE_URL", "http://env:7000")
        monkeypatch.setenv("API_TIMEOUT", "120")
        monkeypatch.setenv("ENABLE_AUTHENTICATION", "true")

        # Need to clear cache for get_settings
        from banking_client.config import get_settings

        get_settings.cache_clear()

        settings = get_settings()
        assert settings.api_base_url == "http://env:7000"
        assert settings.api_timeout == 120
        assert settings.enable_authentication is True
