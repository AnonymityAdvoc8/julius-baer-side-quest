"""
Comprehensive tests for the JWT authentication module.

Tests all authentication scenarios to achieve 100% coverage.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from banking_client.auth import AuthManager
from banking_client.config import Settings
from banking_client.exceptions import AuthenticationError
from banking_client.models import AuthToken


@pytest.fixture
def auth_settings():
    """Create test settings with auth enabled."""
    return Settings(
        api_base_url="http://localhost:8123",
        enable_authentication=True,
        auth_username="testuser",
        auth_password="testpass",
        api_timeout=10,
    )


@pytest.fixture
def auth_manager(auth_settings):
    """Create an AuthManager instance for testing."""
    return AuthManager(auth_settings)


class TestAuthManager:
    """Test suite for AuthManager."""

    def test_initialization(self, auth_manager):
        """Test that AuthManager initializes correctly."""
        assert auth_manager is not None
        assert auth_manager.settings.enable_authentication is True
        assert auth_manager._token is None

    @patch("banking_client.auth.requests.Session.post")
    def test_acquire_token_success(self, mock_post, auth_manager):
        """Test successful token acquisition."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "test-jwt-token-12345",
            "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "tokenType": "Bearer",
        }
        mock_post.return_value = mock_response

        # Get token
        token = auth_manager.get_token()

        # Verify
        assert token == "test-jwt-token-12345"
        assert auth_manager._token is not None
        assert auth_manager._token.token == "test-jwt-token-12345"

        # Verify correct URL was called with claim parameter
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "claim=transfer" in call_args[0][0]

    @patch("banking_client.auth.requests.Session.post")
    def test_token_caching(self, mock_post, auth_manager):
        """Test that tokens are cached and reused."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "cached-token",
            "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        mock_post.return_value = mock_response

        # First call should acquire token
        token1 = auth_manager.get_token()
        assert mock_post.call_count == 1

        # Second call should use cached token
        token2 = auth_manager.get_token()
        assert mock_post.call_count == 1  # Still 1, not called again

        # Tokens should be the same
        assert token1 == token2 == "cached-token"

    @patch("banking_client.auth.requests.Session.post")
    def test_force_refresh(self, mock_post, auth_manager):
        """Test forcing token refresh."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "refreshed-token",
        }
        mock_post.return_value = mock_response

        # Get initial token
        auth_manager.get_token()
        assert mock_post.call_count == 1

        # Force refresh
        token = auth_manager.get_token(force_refresh=True)
        assert mock_post.call_count == 2  # Called again
        assert token == "refreshed-token"

    def test_token_validation_no_token(self, auth_manager):
        """Test token validation when no token exists."""
        assert auth_manager._is_token_valid() is False

    def test_token_validation_no_expiration(self, auth_manager):
        """Test token validation with no expiration time."""
        # Create token without expiration
        auth_manager._token = AuthToken(token="test-token")
        assert auth_manager._is_token_valid() is True

    def test_token_validation_expired(self, auth_manager):
        """Test token validation with expired token."""
        # Create expired token
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        auth_manager._token = AuthToken(token="expired-token", expiresAt=expired_time)
        assert auth_manager._is_token_valid() is False

    def test_token_validation_valid(self, auth_manager):
        """Test token validation with valid token."""
        # Create valid token (expires in 1 hour)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        auth_manager._token = AuthToken(token="valid-token", expiresAt=future_time)
        assert auth_manager._is_token_valid() is True

    def test_token_validation_near_expiration(self, auth_manager):
        """Test token validation near expiration (within buffer)."""
        # Create token expiring in 3 minutes (within 5 minute buffer)
        near_expiry = datetime.now(timezone.utc) + timedelta(minutes=3)
        auth_manager._token = AuthToken(token="expiring-soon", expiresAt=near_expiry)
        # Should be invalid due to 5-minute buffer
        assert auth_manager._is_token_valid() is False

    def test_token_validation_naive_datetime(self, auth_manager):
        """Test token validation with timezone-naive datetime."""
        # Create token with naive datetime (far in the future to be safe)
        naive_time = datetime.now() + timedelta(hours=24)
        auth_manager._token = AuthToken(token="naive-token", expiresAt=naive_time)
        # Should still work (gets converted to timezone-aware)
        # Note: comparison happens in UTC, so using a large buffer
        assert auth_manager._is_token_valid() is True

    @patch("banking_client.auth.requests.Session.post")
    def test_acquire_token_http_error(self, mock_post, auth_manager):
        """Test token acquisition with HTTP error."""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 401

        from requests.exceptions import HTTPError

        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        # Should raise AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.get_token()

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in str(exc_info.value)

    @patch("banking_client.auth.requests.Session.post")
    def test_acquire_token_network_error(self, mock_post, auth_manager):
        """Test token acquisition with network error."""
        from requests.exceptions import ConnectionError

        # Mock network error
        mock_post.side_effect = ConnectionError("Network error")

        # Should raise AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.get_token()

        assert "Network error" in str(exc_info.value)

    @patch("banking_client.auth.requests.Session.post")
    def test_acquire_token_invalid_response(self, mock_post, auth_manager):
        """Test token acquisition with malformed JSON."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        # Should raise AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.get_token()

        assert "Invalid authentication response" in str(exc_info.value)

    @patch("banking_client.auth.requests.Session.post")
    def test_empty_token_response(self, mock_post, auth_manager):
        """Test handling of empty token in response."""
        # Mock response with empty string token
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": ""}
        mock_post.return_value = mock_response

        # Should create token with empty string (not raise error)
        token = auth_manager.get_token()
        assert token == ""
        assert auth_manager._token.token == ""

    def test_invalidate_token(self, auth_manager):
        """Test token invalidation."""
        # Set a token
        auth_manager._token = AuthToken(token="test-token")
        assert auth_manager._token is not None

        # Invalidate
        auth_manager.invalidate_token()
        assert auth_manager._token is None

    def test_close_session(self, auth_manager):
        """Test session cleanup."""
        # Should not raise any errors
        auth_manager.close()

    def test_auth_disabled(self):
        """Test behavior when authentication is disabled."""
        settings = Settings(enable_authentication=False)
        auth_manager = AuthManager(settings)

        # Should return empty string without making API call
        token = auth_manager.get_token()
        assert token == ""

    @patch("banking_client.auth.requests.Session.post")
    def test_token_refresh_on_expiration(self, mock_post, auth_manager):
        """Test automatic token refresh when expired."""
        # Mock two different tokens
        mock_response = Mock()
        mock_response.status_code = 200

        # First call: expired token
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        auth_manager._token = AuthToken(token="old-token", expiresAt=expired_time)

        # Second call: new token
        mock_response.json.return_value = {
            "token": "new-token",
            "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        mock_post.return_value = mock_response

        # Get token should refresh because old one is expired
        token = auth_manager.get_token()

        assert token == "new-token"
        assert mock_post.call_count == 1

    @patch("banking_client.auth.requests.Session.post")
    def test_acquire_token_timeout(self, mock_post, auth_manager):
        """Test token acquisition with timeout."""
        from requests.exceptions import Timeout

        # Mock timeout error
        mock_post.side_effect = Timeout("Request timeout")

        # Should raise AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.get_token()

        assert "timeout" in str(exc_info.value).lower()


class TestAuthManagerIntegration:
    """Integration tests for AuthManager with real API."""

    @pytest.mark.skipif(
        True, reason="Requires live server"  # Skip by default unless server is running
    )
    def test_real_token_acquisition(self):
        """Test real token acquisition from API."""
        settings = Settings(
            api_base_url="http://localhost:8123",
            enable_authentication=True,
            auth_username="admin",
            auth_password="password123",
        )

        auth_manager = AuthManager(settings)
        token = auth_manager.get_token()

        assert token is not None
        assert len(token) > 0
        assert auth_manager._token is not None
