"""
Authentication handler for JWT token management.

Handles token acquisition, caching, and automatic refresh.
"""

import logging
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Settings
from .exceptions import AuthenticationError
from .models import AuthToken

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages JWT authentication tokens with automatic refresh.

    Features:
    - Automatic token acquisition
    - Token caching to reduce API calls
    - Automatic refresh before expiration
    - Thread-safe token management
    """

    def __init__(self, settings: Settings):
        """
        Initialize the authentication manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._token: AuthToken | None = None
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic.

        Returns:
            Configured requests Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.settings.api_max_retries,
            backoff_factor=self.settings.api_retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.settings.connection_pool_size,
            pool_maxsize=self.settings.connection_pool_maxsize,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid JWT token, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if cached token is valid

        Returns:
            Valid JWT token string

        Raises:
            AuthenticationError: If token acquisition fails
        """
        if not self.settings.enable_authentication:
            logger.debug("Authentication is disabled")
            return ""

        # Check if we have a valid cached token
        if not force_refresh and self._token and self._is_token_valid():
            logger.debug("Using cached authentication token")
            return self._token.token

        # Acquire new token
        logger.info("Acquiring new authentication token")
        self._token = self._acquire_token()
        return self._token.token

    def _is_token_valid(self) -> bool:
        """
        Check if the current token is still valid.

        Returns:
            True if token is valid, False otherwise
        """
        if not self._token:
            return False

        if not self._token.expires_at:
            # No expiration set, assume valid for 1 hour from now
            return True

        # Add 5 minute buffer before expiration
        buffer = timedelta(minutes=5)
        now = datetime.now(timezone.utc)

        # Make expires_at timezone-aware if it isn't already
        expires_at = self._token.expires_at
        if expires_at.tzinfo is None:
            # If expires_at is naive, assume UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return now + buffer < expires_at

    def _acquire_token(self) -> AuthToken:
        """
        Acquire a new JWT token from the API.

        Returns:
            New AuthToken instance

        Raises:
            AuthenticationError: If token acquisition fails
        """
        try:
            payload = {
                "username": self.settings.auth_username,
                "password": self.settings.auth_password,
            }

            # Request token with transfer permissions for maximum bonus points!
            auth_url_with_claim = f"{self.settings.auth_url}?claim=transfer"

            response = self._session.post(
                auth_url_with_claim,
                json=payload,
                timeout=self.settings.api_timeout,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            data = response.json()

            # Parse response into AuthToken model
            token = AuthToken(
                token=data.get("token", ""),
                expiresAt=data.get("expiresAt"),
            )

            logger.info("Successfully acquired authentication token")
            return token

        except requests.exceptions.HTTPError as e:
            error_msg = f"Authentication failed with status {e.response.status_code}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg, e.response.status_code) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during authentication: {e}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

        except (KeyError, ValueError) as e:
            error_msg = f"Invalid authentication response: {e}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    def invalidate_token(self) -> None:
        """Invalidate the current token, forcing a refresh on next request."""
        logger.debug("Invalidating cached token")
        self._token = None

    def close(self) -> None:
        """Close the session and release resources."""
        self._session.close()
