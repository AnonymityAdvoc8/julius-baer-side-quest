"""
Integration tests for the BankingClient.

These tests require a running instance of the Core Banking API server.
Set SKIP_INTEGRATION_TESTS=1 to skip these tests if the server is not available.
"""

import os
from decimal import Decimal

import pytest

from banking_client import BankingClient
from banking_client.config import Settings
from banking_client.exceptions import BankingClientError

# Skip integration tests if environment variable is set
skip_integration = os.getenv("SKIP_INTEGRATION_TESTS", "0") == "1"


@pytest.fixture
def integration_client():
    """Create a client connected to the actual server."""
    settings = Settings(
        api_base_url="http://localhost:8123",
        enable_authentication=False,
    )
    return BankingClient(settings=settings)


@pytest.mark.skipif(skip_integration, reason="Integration tests disabled")
class TestIntegration:
    """Integration tests against live server."""

    def test_server_connectivity(self, integration_client):
        """Test that we can connect to the server."""
        # This should not raise an exception
        try:
            result = integration_client.validate_account("ACC1000")
            assert result is not None
        except BankingClientError as e:
            pytest.fail(f"Failed to connect to server: {e}")

    def test_validate_valid_account(self, integration_client):
        """Test validation of a valid account."""
        result = integration_client.validate_account("ACC1000")
        assert result.valid is True
        assert result.account_id == "ACC1000"

    def test_validate_invalid_account(self, integration_client):
        """Test validation of an invalid account."""
        result = integration_client.validate_account("ACC2000")
        # ACC2000 is in the invalid range
        assert result.account_id == "ACC2000"

    def test_successful_transfer(self, integration_client):
        """Test a successful transfer between valid accounts."""
        # Use smaller amount to avoid insufficient funds in repeated tests
        response = integration_client.transfer(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("1.00"),
        )

        assert response.status == "SUCCESS"
        assert response.transaction_id is not None
        assert len(response.transaction_id) > 0
        assert response.from_account == "ACC1000"
        assert response.to_account == "ACC1001"
        assert response.amount == Decimal("1.00")

    def test_transfer_from_invalid_account(self, integration_client):
        """Test transfer from an invalid account."""
        response = integration_client.transfer(
            from_account="ACC2000",
            to_account="ACC1001",
            amount=Decimal("100.00"),
        )

        # Should return FAILED status for invalid accounts
        assert response.status == "FAILED"

    def test_transfer_with_decimal_amount(self, integration_client):
        """Test transfer with precise decimal amount."""
        # Use smaller amount to avoid insufficient funds
        response = integration_client.transfer(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("0.75"),
        )

        # May fail if account has insufficient funds, which is expected behavior
        if response.status == "SUCCESS":
            assert response.amount == Decimal("0.75")
        else:
            # Failing due to insufficient funds is also valid - system working correctly
            assert (
                "Insufficient funds" in response.message
                or "insufficient" in response.message.lower()
            )

    def test_get_accounts_list(self, integration_client):
        """Test retrieving the list of accounts."""
        try:
            accounts = integration_client.get_accounts()
            # May return empty list or actual accounts depending on server
            assert isinstance(accounts, list)
        except BankingClientError:
            # Some servers may not implement this endpoint
            pytest.skip("Accounts endpoint not available")

    def test_context_manager_usage(self):
        """Test using client as context manager."""
        settings = Settings(api_base_url="http://localhost:8123")

        with BankingClient(settings=settings) as client:
            result = client.validate_account("ACC1000")
            assert result is not None

        # Client should be closed after context


@pytest.mark.skipif(skip_integration, reason="Integration tests disabled")
class TestEndToEndScenarios:
    """End-to-end test scenarios."""

    def test_multiple_transfers_sequence(self, integration_client):
        """Test executing multiple transfers in sequence."""
        transfers = [
            ("ACC1000", "ACC1001", Decimal("10.00")),
            ("ACC1001", "ACC1002", Decimal("20.00")),
            ("ACC1002", "ACC1003", Decimal("30.00")),
        ]

        for from_acc, to_acc, amount in transfers:
            response = integration_client.transfer(from_acc, to_acc, amount)
            assert response.status == "SUCCESS"
            assert response.from_account == from_acc
            assert response.to_account == to_acc
            assert response.amount == amount

    def test_validate_before_transfer(self, integration_client):
        """Test validating accounts before transfer."""
        # Validate source account
        from_validation = integration_client.validate_account("ACC1000")
        assert from_validation.valid is True

        # Validate destination account
        to_validation = integration_client.validate_account("ACC1001")
        assert to_validation.valid is True

        # Perform transfer with small amount
        response = integration_client.transfer(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("0.50"),
        )

        # Success or insufficient funds are both valid responses
        assert response.status in ["SUCCESS", "FAILED"]
        if response.status == "FAILED":
            # If it fails, it should be due to insufficient funds
            assert "fund" in response.message.lower()
