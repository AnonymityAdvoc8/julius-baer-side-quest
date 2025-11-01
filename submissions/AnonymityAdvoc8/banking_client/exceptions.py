"""
Custom exceptions for the banking client.

Provides a hierarchy of exceptions for different error scenarios.
"""


class BankingClientError(Exception):
    """Base exception for all banking client errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(BankingClientError):
    """Raised when authentication fails."""

    pass


class TransferError(BankingClientError):
    """Raised when a transfer operation fails."""

    pass


class ValidationError(BankingClientError):
    """Raised when input validation fails."""

    pass


class AccountNotFoundError(BankingClientError):
    """Raised when an account is not found."""

    pass


class NetworkError(BankingClientError):
    """Raised when network communication fails."""

    pass


class ConfigurationError(BankingClientError):
    """Raised when configuration is invalid."""

    pass
