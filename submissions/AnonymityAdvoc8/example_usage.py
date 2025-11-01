#!/usr/bin/env python3
"""
Example usage of the Banking Client.

This script demonstrates various features of the modernized banking client.
Run this after starting the Core Banking API server.
"""

import sys
from decimal import Decimal
import requests
from banking_client import BankingClient
from banking_client.config import get_settings
from banking_client.exceptions import BankingClientError


def check_server() -> bool:
    """Check if the banking server is running."""
    try:
        settings = get_settings()
        url = f"{settings.api_base_url}/accounts/validate/ACC1000"
        response = requests.get(url, timeout=3)
        return response.status_code == 200
    except:
        return False


def main():
    """Demonstrate banking client features."""

    print("🏦 Banking Client Demo - Python 3.12 Modernized\n")
    print("=" * 60)

    # Check if server is running
    print("\n🔍 Checking server connection...")
    settings = get_settings()
    if not check_server():
        print(f"❌ Banking server is not running at {settings.api_base_url}")
        print()
        print("Please start the server first:")
        print("  docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest")
        print()
        print("Or with Java:")
        print("  cd ../../server && java -jar core-banking-api.jar")
        print()
        sys.exit(1)
    else:
        print(f"✅ Server is running and accessible at {settings.api_base_url}")

    # Use context manager for automatic resource cleanup
    with BankingClient() as client:
        # Example 1: Validate accounts
        print("\n📋 Example 1: Account Validation")
        print("-" * 60)

        accounts_to_validate = ["ACC1000", "ACC1001", "ACC2000", "ACC9999"]
        for account_id in accounts_to_validate:
            try:
                result = client.validate_account(account_id)
                status = "✅ Valid" if result.valid else "❌ Invalid"
                print(f"{account_id}: {status}")
                if result.message:
                    print(f"  Message: {result.message}")
            except BankingClientError as e:
                print(f"{account_id}: ❌ Error - {e.message}")

        # Example 2: Simple transfer
        print("\n💸 Example 2: Simple Transfer")
        print("-" * 60)

        try:
            response = client.transfer(
                from_account="ACC1000", to_account="ACC1001", amount=Decimal("100.00")
            )

            print(f"Status: {response.status}")
            print(f"Transaction ID: {response.transaction_id}")
            print(f"From: {response.from_account} → To: {response.to_account}")
            print(f"Amount: ${response.amount}")
            print(f"Message: {response.message}")

        except BankingClientError as e:
            print(f"❌ Transfer failed: {e.message}")

        # Example 3: Transfer with validation
        print("\n🔍 Example 3: Transfer with Pre-validation")
        print("-" * 60)

        from_acc = "ACC1002"
        to_acc = "ACC1003"
        amount = Decimal("50.75")

        # Validate accounts first
        from_valid = client.validate_account(from_acc)
        to_valid = client.validate_account(to_acc)

        if from_valid.valid and to_valid.valid:
            print(f"✅ Both accounts validated")
            try:
                response = client.transfer(from_acc, to_acc, amount)
                print(f"✅ Transfer {response.status}: {response.transaction_id}")
            except BankingClientError as e:
                print(f"❌ Transfer failed: {e.message}")
        else:
            print(f"❌ Account validation failed")
            if not from_valid.valid:
                print(f"  - {from_acc}: {from_valid.message}")
            if not to_valid.valid:
                print(f"  - {to_acc}: {to_valid.message}")

        # Example 4: Multiple transfers
        print("\n🔄 Example 4: Multiple Transfers")
        print("-" * 60)

        transfers = [
            ("ACC1000", "ACC1001", Decimal("10.00")),
            ("ACC1001", "ACC1002", Decimal("20.00")),
            ("ACC1002", "ACC1003", Decimal("30.00")),
        ]

        successful = 0
        failed = 0

        for from_acc, to_acc, amount in transfers:
            try:
                response = client.transfer(from_acc, to_acc, amount)
                if response.status == "SUCCESS":
                    print(f"✅ {from_acc} → {to_acc}: ${amount}")
                    successful += 1
                else:
                    print(f"❌ {from_acc} → {to_acc}: {response.message}")
                    failed += 1
            except BankingClientError as e:
                print(f"❌ {from_acc} → {to_acc}: {e.message}")
                failed += 1

        print(f"\nResults: {successful} successful, {failed} failed")

        # Example 5: List accounts (if available)
        print("\n📊 Example 5: List Accounts")
        print("-" * 60)

        try:
            accounts = client.get_accounts()
            if accounts:
                print(f"Found {len(accounts)} account(s):")
                for account in accounts:
                    print(
                        f"  {account.account_id}: {account.account_holder} - ${account.balance}"
                    )
            else:
                print("No accounts available or endpoint not implemented")
        except BankingClientError as e:
            print(f"Could not fetch accounts: {e.message}")

        # Example 6: Error handling demo
        print("\n⚠️  Example 6: Error Handling")
        print("-" * 60)

        # Try invalid account format
        try:
            client.transfer("INVALID", "ACC1001", Decimal("100.00"))
        except BankingClientError as e:
            print(f"✅ Caught validation error: {e.message}")

        # Try transfer from invalid account range
        try:
            response = client.transfer("ACC2000", "ACC1001", Decimal("100.00"))
            if response.status == "FAILED":
                print(f"✅ Transfer failed as expected: {response.message}")
        except BankingClientError as e:
            print(f"✅ Caught transfer error: {e.message}")

    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\nModernization highlights:")
    print("  • Python 3.12 with type hints")
    print("  • Pydantic models for validation")
    print("  • Modern requests library")
    print("  • Context managers for cleanup")
    print("  • Comprehensive error handling")
    print("  • Structured logging")
    print("  • Decimal for precise amounts")


if __name__ == "__main__":
    main()
