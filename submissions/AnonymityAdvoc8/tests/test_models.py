"""
Comprehensive tests for data models.

Ensures 100% coverage of the models module.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from banking_client.models import (
    Account,
    AuthToken,
    Transaction,
    TransactionHistory,
    TransferRequest,
    TransferResponse,
    ValidationResponse,
)


class TestTransferRequest:
    """Test suite for TransferRequest model."""

    def test_valid_transfer_request(self):
        """Test valid transfer request creation."""
        request = TransferRequest(
            fromAccount="ACC1000", toAccount="ACC1001", amount=Decimal("100.00")
        )

        assert request.from_account == "ACC1000"
        assert request.to_account == "ACC1001"
        assert request.amount == Decimal("100.00")

    def test_transfer_request_alias(self):
        """Test that aliases work correctly."""
        request = TransferRequest(
            from_account="ACC1000",  # Using Python-style name
            to_account="ACC1001",
            amount=Decimal("50.00"),
        )

        # Should serialize with aliases
        data = request.model_dump(by_alias=True)
        assert "fromAccount" in data
        assert "toAccount" in data

    def test_invalid_account_no_acc_prefix(self):
        """Test validation fails for account without ACC prefix."""
        with pytest.raises(ValidationError) as exc_info:
            TransferRequest(
                fromAccount="INVALID", toAccount="ACC1001", amount=Decimal("100.00")
            )

        assert "must start with 'ACC'" in str(exc_info.value)

    def test_invalid_account_wrong_format(self):
        """Test validation fails for account with wrong format."""
        with pytest.raises(ValidationError) as exc_info:
            TransferRequest(
                fromAccount="ACCABCD",  # Not digits after ACC
                toAccount="ACC1001",
                amount=Decimal("100.00"),
            )

        assert "must be in format ACC####" in str(exc_info.value)

    def test_invalid_account_length(self):
        """Test validation fails for wrong account length."""
        with pytest.raises(ValidationError) as exc_info:
            TransferRequest(
                fromAccount="ACC100",  # Too short
                toAccount="ACC1001",
                amount=Decimal("100.00"),
            )

        # Should fail min_length validation
        assert "validation error" in str(exc_info.value).lower()

    def test_negative_amount(self):
        """Test validation fails for negative amount."""
        with pytest.raises(ValidationError) as exc_info:
            TransferRequest(
                fromAccount="ACC1000", toAccount="ACC1001", amount=Decimal("-100.00")
            )

        # Should fail gt=0 validation
        assert "validation error" in str(exc_info.value).lower()

    def test_zero_amount(self):
        """Test validation fails for zero amount."""
        with pytest.raises(ValidationError) as exc_info:
            TransferRequest(
                fromAccount="ACC1000", toAccount="ACC1001", amount=Decimal("0.00")
            )

        # Should fail gt=0 validation
        assert "validation error" in str(exc_info.value).lower()


class TestTransferResponse:
    """Test suite for TransferResponse model."""

    def test_success_response(self):
        """Test successful transfer response."""
        response = TransferResponse(
            transactionId="txn-123",
            status="SUCCESS",
            message="Transfer completed",
            fromAccount="ACC1000",
            toAccount="ACC1001",
            amount=Decimal("100.00"),
        )

        assert response.transaction_id == "txn-123"
        assert response.status == "SUCCESS"
        assert response.from_account == "ACC1000"

    def test_failed_response(self):
        """Test failed transfer response."""
        response = TransferResponse(
            transactionId="txn-456",
            status="FAILED",
            message="Insufficient funds",
            fromAccount="ACC1000",
            toAccount="ACC1001",
            amount=Decimal("100.00"),
        )

        assert response.status == "FAILED"
        assert "Insufficient" in response.message

    def test_response_with_timestamp(self):
        """Test response with timestamp."""
        now = datetime.now()
        response = TransferResponse(
            transactionId="txn-789",
            status="SUCCESS",
            message="Done",
            fromAccount="ACC1000",
            toAccount="ACC1001",
            amount=Decimal("50.00"),
            timestamp=now,
        )

        assert response.timestamp == now


class TestAccount:
    """Test suite for Account model."""

    def test_account_with_all_fields(self):
        """Test account with all fields."""
        account = Account(
            accountId="ACC1000",
            accountHolder="John Doe",
            balance=Decimal("1000.00"),
            currency="USD",
            status="ACTIVE",
        )

        assert account.account_id == "ACC1000"
        assert account.account_holder == "John Doe"
        assert account.balance == Decimal("1000.00")

    def test_account_default_holder(self):
        """Test account with default holder."""
        account = Account(accountId="ACC1001", balance=Decimal("500.00"))

        # Should use default "Unknown"
        assert account.account_holder == "Unknown"
        assert account.currency == "USD"
        assert account.status == "ACTIVE"


class TestAuthToken:
    """Test suite for AuthToken model."""

    def test_token_minimal(self):
        """Test token with minimal fields."""
        token = AuthToken(token="jwt-token-123")

        assert token.token == "jwt-token-123"
        assert token.expires_at is None
        assert token.token_type == "Bearer"

    def test_token_with_expiration(self):
        """Test token with expiration."""
        expires = datetime.now()
        token = AuthToken(token="jwt-token-456", expiresAt=expires, tokenType="Custom")

        assert token.expires_at == expires
        assert token.token_type == "Custom"


class TestTransaction:
    """Test suite for Transaction model."""

    def test_transaction_creation(self):
        """Test transaction model."""
        now = datetime.now()
        transaction = Transaction(
            transactionId="txn-111",
            fromAccount="ACC1000",
            toAccount="ACC1001",
            amount=Decimal("25.00"),
            timestamp=now,
            status="SUCCESS",
        )

        assert transaction.transaction_id == "txn-111"
        assert transaction.from_account == "ACC1000"
        assert transaction.amount == Decimal("25.00")


class TestTransactionHistory:
    """Test suite for TransactionHistory model."""

    def test_transaction_history(self):
        """Test transaction history model."""
        now = datetime.now()
        transactions = [
            Transaction(
                transactionId="txn-1",
                fromAccount="ACC1000",
                toAccount="ACC1001",
                amount=Decimal("10.00"),
                timestamp=now,
                status="SUCCESS",
            ),
            Transaction(
                transactionId="txn-2",
                fromAccount="ACC1001",
                toAccount="ACC1002",
                amount=Decimal("20.00"),
                timestamp=now,
                status="SUCCESS",
            ),
        ]

        history = TransactionHistory(transactions=transactions, totalCount=2)

        assert len(history.transactions) == 2
        assert history.total_count == 2


class TestValidationResponse:
    """Test suite for ValidationResponse model."""

    def test_valid_account_response(self):
        """Test validation response for valid account."""
        response = ValidationResponse(
            accountId="ACC1000", valid=True, message="Account is active"
        )

        assert response.account_id == "ACC1000"
        assert response.valid is True
        assert response.message == "Account is active"

    def test_invalid_account_response(self):
        """Test validation response for invalid account."""
        response = ValidationResponse(accountId="ACC9999", valid=False)

        assert response.valid is False
        assert response.message is None

    def test_json_serialization(self):
        """Test JSON serialization with mode='json'."""
        request = TransferRequest(
            fromAccount="ACC1000", toAccount="ACC1001", amount=Decimal("123.45")
        )

        # Test mode='json' for Decimal serialization
        json_data = request.model_dump(by_alias=True, mode="json")

        assert json_data["fromAccount"] == "ACC1000"
        assert (
            json_data["amount"] == "123.45"
        )  # Decimal serialized as string in json mode
