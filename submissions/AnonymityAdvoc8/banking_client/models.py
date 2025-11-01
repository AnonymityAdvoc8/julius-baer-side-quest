"""
Data models for banking operations using Pydantic.

Provides type-safe, validated data structures for API requests and responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransferRequest(BaseModel):
    """Request model for fund transfers."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "fromAccount": "ACC1000",
                "toAccount": "ACC1001",
                "amount": 100.00,
            }
        },
    )

    from_account: str = Field(..., alias="fromAccount", min_length=7, max_length=7)
    to_account: str = Field(..., alias="toAccount", min_length=7, max_length=7)
    amount: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator("from_account", "to_account")
    @classmethod
    def validate_account_format(cls, v: str) -> str:
        """Validate account ID format (ACC1000-ACC9999)."""
        if not v.startswith("ACC"):
            raise ValueError("Account ID must start with 'ACC'")
        if not v[3:].isdigit():
            raise ValueError("Account ID must be in format ACC#### where # is a digit")
        return v


class TransferResponse(BaseModel):
    """Response model for fund transfers."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: str = Field(..., alias="transactionId")
    status: Literal["SUCCESS", "FAILED"]
    message: str
    from_account: str = Field(..., alias="fromAccount")
    to_account: str = Field(..., alias="toAccount")
    amount: Decimal
    timestamp: datetime | None = None


class Account(BaseModel):
    """Account information model."""

    model_config = ConfigDict(populate_by_name=True)

    account_id: str = Field(..., alias="accountId")
    account_holder: str = Field(default="Unknown", alias="accountHolder")
    balance: Decimal
    currency: str = "USD"
    status: str = "ACTIVE"


class AuthToken(BaseModel):
    """JWT authentication token model."""

    model_config = ConfigDict(populate_by_name=True)

    token: str
    expires_at: datetime | None = Field(None, alias="expiresAt")
    token_type: str = Field(default="Bearer", alias="tokenType")


class Transaction(BaseModel):
    """Individual transaction record."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: str = Field(..., alias="transactionId")
    from_account: str = Field(..., alias="fromAccount")
    to_account: str = Field(..., alias="toAccount")
    amount: Decimal
    timestamp: datetime
    status: str


class TransactionHistory(BaseModel):
    """Transaction history response."""

    model_config = ConfigDict(populate_by_name=True)

    transactions: list[Transaction]
    total_count: int = Field(..., alias="totalCount")


class ValidationResponse(BaseModel):
    """Account validation response."""

    model_config = ConfigDict(populate_by_name=True)

    account_id: str = Field(..., alias="accountId")
    valid: bool
    message: str | None = None
