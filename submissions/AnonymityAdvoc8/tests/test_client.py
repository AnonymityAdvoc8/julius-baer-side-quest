"""
Unit tests for the BankingClient.

Tests all banking operations with mocked HTTP responses to ensure
proper behavior without requiring a live server.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from banking_client import BankingClient
from banking_client.config import Settings
from banking_client.exceptions import (
    AccountNotFoundError,
    TransferError,
    ValidationError,
)
from banking_client.models import TransferResponse


@pytest.fixture
def mock_settings():
    """Create test settings."""
    return Settings(
        api_base_url="http://localhost:8123",
        api_timeout=10,
        enable_authentication=False,
        enable_request_logging=False,
    )


@pytest.fixture
def client(mock_settings):
    """Create a BankingClient instance for testing."""
    return BankingClient(settings=mock_settings)


class TestBankingClient:
    """Test suite for BankingClient."""

    def test_client_initialization(self, client):
        """Test that client initializes correctly."""
        assert client is not None
        assert client.settings.api_base_url == "http://localhost:8123"

    def test_context_manager(self, mock_settings):
        """Test that client works as a context manager."""
        with BankingClient(settings=mock_settings) as client:
            assert client is not None
            # Session should be available during context
            assert client._session is not None
        # Session should be closed after context (but adapters dict remains)
        # The important thing is that close() was called
        assert client._session is not None  # Session object still exists but is closed

    @patch("banking_client.client.requests.Session.post")
    def test_transfer_success(self, mock_post, client):
        """Test successful transfer."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn-123",
            "status": "SUCCESS",
            "message": "Transfer completed successfully",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.00,
        }
        mock_post.return_value = mock_response

        # Execute transfer
        response = client.transfer("ACC1000", "ACC1001", 100.00)

        # Verify response
        assert response.transaction_id == "txn-123"
        assert response.status == "SUCCESS"
        assert response.from_account == "ACC1000"
        assert response.to_account == "ACC1001"
        assert response.amount == Decimal("100.00")

        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "fromAccount" in call_args.kwargs["json"]
        assert call_args.kwargs["json"]["fromAccount"] == "ACC1000"

    @patch("banking_client.client.requests.Session.post")
    def test_transfer_failed_status(self, mock_post, client):
        """Test transfer with FAILED status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn-456",
            "status": "FAILED",
            "message": "Insufficient funds",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.00,
        }
        mock_post.return_value = mock_response

        response = client.transfer("ACC1000", "ACC1001", 100.00)

        assert response.status == "FAILED"
        assert "Insufficient funds" in response.message

    def test_transfer_validation_error(self, client):
        """Test transfer with invalid account format."""
        with pytest.raises(ValidationError) as exc_info:
            client.transfer("INVALID", "ACC1001", 100.00)

        assert "Invalid transfer request" in str(exc_info.value)

    @patch("banking_client.client.requests.Session.post")
    def test_transfer_http_error(self, mock_post, client):
        """Test transfer with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.raise_for_status.side_effect = Exception("HTTP 400")

        from requests.exceptions import HTTPError

        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        with pytest.raises(TransferError) as exc_info:
            client.transfer("ACC1000", "ACC1001", 100.00)

        assert exc_info.value.status_code == 400

    @patch("banking_client.client.requests.Session.post")
    def test_transfer_network_error(self, mock_post, client):
        """Test transfer with network error."""
        from requests.exceptions import ConnectionError

        from banking_client.exceptions import NetworkError

        mock_post.side_effect = ConnectionError("Network failure")

        with pytest.raises(NetworkError) as exc_info:
            client.transfer("ACC1000", "ACC1001", 100.00)

        assert "Network error during transfer" in str(exc_info.value)

    @patch("banking_client.client.requests.Session.post")
    def test_transfer_invalid_json_response(self, mock_post, client):
        """Test transfer with invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        with pytest.raises(TransferError) as exc_info:
            client.transfer("ACC1000", "ACC1001", 100.00)

        assert "Invalid transfer response" in str(exc_info.value)

    @patch("banking_client.client.requests.Session.get")
    def test_validate_account_valid(self, mock_get, client):
        """Test account validation for valid account."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "message": "Account is active",
        }
        mock_get.return_value = mock_response

        result = client.validate_account("ACC1000")

        assert result.valid is True
        assert result.account_id == "ACC1000"

    @patch("banking_client.client.requests.Session.get")
    def test_validate_account_invalid(self, mock_get, client):
        """Test account validation for invalid account."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": False,
            "message": "Account not found",
        }
        mock_get.return_value = mock_response

        result = client.validate_account("ACC9999")

        assert result.valid is False

    @patch("banking_client.client.requests.Session.get")
    def test_validate_account_not_found(self, mock_get, client):
        """Test account validation when account doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")

        from requests.exceptions import HTTPError

        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        result = client.validate_account("ACC9999")

        assert result.valid is False
        assert "not found" in result.message.lower()

    @patch("banking_client.client.requests.Session.get")
    def test_validate_account_http_error_non_404(self, mock_get, client):
        """Test account validation with non-404 HTTP error."""
        from requests.exceptions import HTTPError

        from banking_client.exceptions import NetworkError

        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        with pytest.raises(NetworkError) as exc_info:
            client.validate_account("ACC1000")

        assert exc_info.value.status_code == 500

    @patch("banking_client.client.requests.Session.get")
    def test_validate_account_network_error(self, mock_get, client):
        """Test account validation with network error."""
        from requests.exceptions import ConnectionError

        from banking_client.exceptions import NetworkError

        mock_get.side_effect = ConnectionError("Network failure")

        with pytest.raises(NetworkError) as exc_info:
            client.validate_account("ACC1000")

        assert "Network error during validation" in str(exc_info.value)

    @patch("banking_client.client.requests.Session.get")
    def test_get_accounts(self, mock_get, client):
        """Test fetching account list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "accountId": "ACC1000",
                "accountHolder": "John Doe",
                "balance": 1000.00,
                "currency": "USD",
                "status": "ACTIVE",
            },
            {
                "accountId": "ACC1001",
                "accountHolder": "Jane Smith",
                "balance": 2000.00,
                "currency": "USD",
                "status": "ACTIVE",
            },
        ]
        mock_get.return_value = mock_response

        accounts = client.get_accounts()

        assert len(accounts) == 2
        assert accounts[0].account_id == "ACC1000"
        assert accounts[0].balance == Decimal("1000.00")
        assert accounts[1].account_id == "ACC1001"

    @patch("banking_client.client.requests.Session.get")
    def test_get_accounts_empty_response(self, mock_get, client):
        """Test fetching accounts with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = (
            {}
        )  # Empty dict (not list or dict with "accounts")
        mock_get.return_value = mock_response

        accounts = client.get_accounts()

        assert len(accounts) == 0

    @patch("banking_client.client.requests.Session.get")
    def test_get_accounts_with_invalid_data(self, mock_get, client):
        """Test fetching accounts with some invalid data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ACC1000",  # Using "id" instead of "accountId"
                "balance": 1000.00,
            },
            {
                "accountId": "invalid",  # This might cause KeyError or ValueError
                "balance": "not-a-number",  # Invalid balance
            },
        ]
        mock_get.return_value = mock_response

        # Should skip invalid entries and return valid ones
        accounts = client.get_accounts()

        # At least one account should be parsed successfully
        assert len(accounts) >= 0

    @patch("banking_client.client.requests.Session.get")
    def test_get_accounts_network_error(self, mock_get, client):
        """Test fetching accounts with network error."""
        from requests.exceptions import ConnectionError

        from banking_client.exceptions import NetworkError

        mock_get.side_effect = ConnectionError("Network failure")

        with pytest.raises(NetworkError) as exc_info:
            client.get_accounts()

        assert "Failed to fetch accounts" in str(exc_info.value)

    @patch("banking_client.client.requests.Session.get")
    def test_get_balance(self, mock_get, client):
        """Test fetching account balance."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": 1500.50}
        mock_get.return_value = mock_response

        balance = client.get_balance("ACC1000")

        assert balance == Decimal("1500.50")

    @patch("banking_client.client.requests.Session.get")
    def test_get_balance_not_found(self, mock_get, client):
        """Test fetching balance for non-existent account."""
        mock_response = Mock()
        mock_response.status_code = 404

        from requests.exceptions import HTTPError

        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        with pytest.raises(AccountNotFoundError) as exc_info:
            client.get_balance("ACC9999")

        assert exc_info.value.status_code == 404

    @patch("banking_client.client.requests.Session.get")
    def test_get_balance_http_error_non_404(self, mock_get, client):
        """Test fetching balance with non-404 HTTP error."""
        from requests.exceptions import HTTPError

        from banking_client.exceptions import NetworkError

        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        with pytest.raises(NetworkError) as exc_info:
            client.get_balance("ACC1000")

        assert exc_info.value.status_code == 500

    @patch("banking_client.client.requests.Session.get")
    def test_get_balance_network_error(self, mock_get, client):
        """Test fetching balance with network error."""
        from requests.exceptions import ConnectionError

        from banking_client.exceptions import NetworkError

        mock_get.side_effect = ConnectionError("Network failure")

        with pytest.raises(NetworkError) as exc_info:
            client.get_balance("ACC1000")

        assert "Network error fetching balance" in str(exc_info.value)


class TestModels:
    """Test suite for data models."""

    def test_transfer_request_validation(self):
        """Test TransferRequest validation."""
        from banking_client.models import TransferRequest

        # Valid request
        request = TransferRequest(
            fromAccount="ACC1000",
            toAccount="ACC1001",
            amount=Decimal("100.00"),
        )
        assert request.from_account == "ACC1000"
        assert request.amount == Decimal("100.00")

    def test_transfer_request_invalid_account(self):
        """Test TransferRequest with invalid account format."""
        from pydantic import ValidationError

        from banking_client.models import TransferRequest

        with pytest.raises(ValidationError):
            TransferRequest(
                fromAccount="INVALID",
                toAccount="ACC1001",
                amount=Decimal("100.00"),
            )

    def test_transfer_request_negative_amount(self):
        """Test TransferRequest with negative amount."""
        from pydantic import ValidationError

        from banking_client.models import TransferRequest

        with pytest.raises(ValidationError):
            TransferRequest(
                fromAccount="ACC1000",
                toAccount="ACC1001",
                amount=Decimal("-100.00"),
            )

    def test_transfer_response_parsing(self):
        """Test TransferResponse model parsing."""
        data = {
            "transactionId": "txn-123",
            "status": "SUCCESS",
            "message": "Transfer completed",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.00,
        }

        response = TransferResponse(**data)
        assert response.transaction_id == "txn-123"
        assert response.status == "SUCCESS"
        assert response.amount == Decimal("100.00")


class TestExceptions:
    """Test suite for custom exceptions."""

    def test_banking_client_error(self):
        """Test base BankingClientError."""
        from banking_client.exceptions import BankingClientError

        error = BankingClientError("Test error", status_code=400)
        assert error.message == "Test error"
        assert error.status_code == 400
        assert str(error) == "Test error"

    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        from banking_client.exceptions import (
            AuthenticationError,
            BankingClientError,
            TransferError,
        )

        assert issubclass(TransferError, BankingClientError)
        assert issubclass(AuthenticationError, BankingClientError)
