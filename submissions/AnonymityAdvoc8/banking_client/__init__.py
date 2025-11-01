"""
Enterprise Banking Client Package

A modern, enterprise-grade Python client for interacting with the Core Banking API.
Supports JWT authentication, comprehensive error handling, and full API coverage.
"""

from .client import BankingClient
from .exceptions import (
    AccountNotFoundError,
    AuthenticationError,
    BankingClientError,
    TransferError,
    ValidationError,
)
from .models import (
    Account,
    AuthToken,
    TransactionHistory,
    TransferRequest,
    TransferResponse,
)

__version__ = "1.0.0"
__all__ = [
    "BankingClient",
    "BankingClientError",
    "AuthenticationError",
    "TransferError",
    "ValidationError",
    "AccountNotFoundError",
    "TransferRequest",
    "TransferResponse",
    "Account",
    "AuthToken",
    "TransactionHistory",
]
