"""
Main banking client implementation.

Provides a high-level interface for all banking operations with comprehensive
error handling, logging, and validation.
"""

import logging
from decimal import Decimal

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import AuthManager
from .config import Settings, get_settings
from .exceptions import (
    AccountNotFoundError,
    NetworkError,
    TransferError,
    ValidationError,
)
from .models import (
    Account,
    TransferRequest,
    TransferResponse,
    ValidationResponse,
)

logger = logging.getLogger(__name__)


class BankingClient:
    """
    Enterprise-grade banking client for the Core Banking API.

    Features:
    - Modern Python 3.12+ with type hints
    - JWT authentication support
    - Comprehensive error handling
    - Request/response validation with Pydantic
    - Connection pooling and retry logic
    - Structured logging
    - Context manager support

    Example:
        >>> with BankingClient() as client:
        ...     response = client.transfer(
        ...         from_account="ACC1000",
        ...         to_account="ACC1001",
        ...         amount=100.00
        ...     )
        ...     print(f"Transfer ID: {response.transaction_id}")
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize the banking client.

        Args:
            settings: Optional settings override. If None, uses default settings.
        """
        self.settings = settings or get_settings()
        self._session = self._create_session()
        self._auth_manager = AuthManager(self.settings)

        logger.info(
            "Initialized BankingClient",
            extra={
                "base_url": self.settings.api_base_url,
                "auth_enabled": self.settings.enable_authentication,
            },
        )

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic and connection pooling.

        Returns:
            Configured requests Session
        """
        session = requests.Session()

        # Configure retry strategy for resilience
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

    def _get_headers(self) -> dict[str, str]:
        """
        Get request headers with optional authentication.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BankingClient/1.0.0",
        }

        if self.settings.enable_authentication:
            token = self._auth_manager.get_token()
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def transfer(
        self,
        from_account: str,
        to_account: str,
        amount: float | Decimal,
    ) -> TransferResponse:
        """
        Transfer funds between accounts.

        Args:
            from_account: Source account ID (e.g., "ACC1000")
            to_account: Destination account ID (e.g., "ACC1001")
            amount: Transfer amount (positive decimal)

        Returns:
            TransferResponse with transaction details

        Raises:
            ValidationError: If input validation fails
            TransferError: If the transfer fails
            NetworkError: If network communication fails

        Example:
            >>> client = BankingClient()
            >>> response = client.transfer("ACC1000", "ACC1001", 100.00)
            >>> print(response.transaction_id)
        """
        # Validate and create request
        try:
            request = TransferRequest(
                fromAccount=from_account,
                toAccount=to_account,
                amount=Decimal(str(amount)),
            )
        except ValueError as e:
            error_msg = f"Invalid transfer request: {e}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e

        logger.info(
            f"Initiating transfer: {from_account} -> {to_account}, amount: {amount}"
        )

        try:
            response = self._session.post(
                self.settings.transfer_url,
                json=request.model_dump(by_alias=True, mode="json"),
                headers=self._get_headers(),
                timeout=self.settings.api_timeout,
            )

            # Log request/response if enabled
            if self.settings.enable_request_logging:
                logger.debug(
                    f"Transfer request: {request.model_dump(by_alias=True, mode='json')}"
                )
                logger.debug(
                    f"Transfer response: {response.status_code} {response.text}"
                )

            response.raise_for_status()

            # Parse and validate response
            transfer_response = TransferResponse(**response.json())

            if transfer_response.status == "SUCCESS":
                logger.info(f"Transfer successful: {transfer_response.transaction_id}")
            else:
                logger.warning(f"Transfer failed: {transfer_response.message}")

            return transfer_response

        except requests.exceptions.HTTPError as e:
            error_msg = f"Transfer failed with status {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise TransferError(error_msg, e.response.status_code) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during transfer: {e}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e

        except (KeyError, ValueError) as e:
            error_msg = f"Invalid transfer response: {e}"
            logger.error(error_msg)
            raise TransferError(error_msg) from e

    def validate_account(self, account_id: str) -> ValidationResponse:
        """
        Validate if an account exists and is active.

        Args:
            account_id: Account ID to validate

        Returns:
            ValidationResponse with validation result

        Raises:
            NetworkError: If network communication fails

        Example:
            >>> client = BankingClient()
            >>> result = client.validate_account("ACC1000")
            >>> print(result.valid)
        """
        logger.debug(f"Validating account: {account_id}")

        try:
            response = self._session.get(
                self.settings.validate_url(account_id),
                headers=self._get_headers(),
                timeout=self.settings.api_timeout,
            )

            response.raise_for_status()
            data = response.json()

            # Handle both 'valid' and 'isValid' field names
            is_valid = data.get("valid", data.get("isValid", False))
            message = data.get("message") or data.get("status")

            validation_response = ValidationResponse(
                accountId=account_id,
                valid=is_valid,
                message=message,
            )

            logger.info(f"Account {account_id} validation: {validation_response.valid}")
            return validation_response

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Account not found: {account_id}")
                return ValidationResponse(
                    accountId=account_id,
                    valid=False,
                    message="Account not found",
                )
            raise NetworkError(
                f"Validation failed: {e.response.status_code}", e.response.status_code
            ) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during validation: {e}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e

    def get_accounts(self) -> list[Account]:
        """
        Get list of all accounts.

        Returns:
            List of Account objects

        Raises:
            NetworkError: If network communication fails

        Example:
            >>> client = BankingClient()
            >>> accounts = client.get_accounts()
            >>> for account in accounts:
            ...     print(f"{account.account_id}: {account.balance}")
        """
        logger.debug("Fetching account list")

        try:
            response = self._session.get(
                self.settings.accounts_url,
                headers=self._get_headers(),
                timeout=self.settings.api_timeout,
            )

            response.raise_for_status()
            data = response.json()

            # Handle both list and dict responses
            accounts = []
            if isinstance(data, list):
                account_list = data
            elif isinstance(data, dict) and "accounts" in data:
                account_list = data["accounts"]
            else:
                account_list = []

            # Parse accounts with flexible field mapping
            for account_data in account_list:
                try:
                    # Map API fields to our model fields
                    account = Account(
                        accountId=account_data.get("accountId")
                        or account_data.get("id"),
                        accountHolder=account_data.get("accountHolder", "Unknown"),
                        balance=account_data.get("balance", 0),
                        currency=account_data.get("currency", "USD"),
                        status=account_data.get("status", "ACTIVE"),
                    )
                    accounts.append(account)
                except (KeyError, ValueError) as e:
                    # Skip invalid account data
                    logger.warning(f"Skipping invalid account data: {e}")
                    continue

            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch accounts: {e}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e

    def get_balance(self, account_id: str) -> Decimal:
        """
        Get account balance.

        Args:
            account_id: Account ID

        Returns:
            Account balance as Decimal

        Raises:
            AccountNotFoundError: If account doesn't exist
            NetworkError: If network communication fails

        Example:
            >>> client = BankingClient()
            >>> balance = client.get_balance("ACC1000")
            >>> print(f"Balance: ${balance}")
        """
        logger.debug(f"Fetching balance for account: {account_id}")

        try:
            response = self._session.get(
                self.settings.balance_url(account_id),
                headers=self._get_headers(),
                timeout=self.settings.api_timeout,
            )

            response.raise_for_status()
            data = response.json()

            balance = Decimal(str(data.get("balance", 0)))
            logger.info(f"Account {account_id} balance: {balance}")
            return balance

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise AccountNotFoundError(
                    f"Account {account_id} not found", 404
                ) from e
            raise NetworkError(
                f"Balance fetch failed: {e.response.status_code}",
                e.response.status_code,
            ) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error fetching balance: {e}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        return False

    def close(self) -> None:
        """Close sessions and release resources."""
        logger.debug("Closing BankingClient")
        self._session.close()
        self._auth_manager.close()
