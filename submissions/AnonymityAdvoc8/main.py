#!/usr/bin/env python3
"""
Main CLI entry point for the Banking Client.

Provides a command-line interface for banking operations with comprehensive
argument parsing and user-friendly output.
"""

import argparse
import logging
import sys
from decimal import Decimal

from banking_client import BankingClient
from banking_client.exceptions import BankingClientError


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging based on verbosity level.

    Args:
        verbose: Enable debug-level logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from urllib3
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def handle_transfer(args: argparse.Namespace) -> int:
    """
    Handle transfer command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        with BankingClient() as client:
            response = client.transfer(
                from_account=args.from_account,
                to_account=args.to_account,
                amount=args.amount,
            )

            if response.status == "SUCCESS":
                print("✅ Transfer Successful!")
                print(f"Transaction ID: {response.transaction_id}")
                print(f"From: {response.from_account}")
                print(f"To: {response.to_account}")
                print(f"Amount: ${response.amount}")
                print(f"Message: {response.message}")
                return 0
            else:
                print(f"❌ Transfer Failed: {response.message}")
                return 1

    except BankingClientError as e:
        print(f"❌ Error: {e.message}")
        if args.verbose:
            logging.exception("Transfer failed with exception")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            logging.exception("Unexpected error during transfer")
        return 1


def handle_validate(args: argparse.Namespace) -> int:
    """
    Handle account validation command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        with BankingClient() as client:
            response = client.validate_account(args.account_id)

            if response.valid:
                print(f"✅ Account {args.account_id} is valid")
                if response.message:
                    print(f"Message: {response.message}")
                return 0
            else:
                print(f"❌ Account {args.account_id} is invalid")
                if response.message:
                    print(f"Message: {response.message}")
                return 1

    except BankingClientError as e:
        print(f"❌ Error: {e.message}")
        if args.verbose:
            logging.exception("Validation failed with exception")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            logging.exception("Unexpected error during validation")
        return 1


def handle_balance(args: argparse.Namespace) -> int:
    """
    Handle balance inquiry command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        with BankingClient() as client:
            balance = client.get_balance(args.account_id)
            print(f"Account: {args.account_id}")
            print(f"Balance: ${balance:,.2f}")
            return 0

    except BankingClientError as e:
        print(f"❌ Error: {e.message}")
        if args.verbose:
            logging.exception("Balance inquiry failed with exception")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            logging.exception("Unexpected error during balance inquiry")
        return 1


def handle_list_accounts(args: argparse.Namespace) -> int:
    """
    Handle list accounts command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        with BankingClient() as client:
            accounts = client.get_accounts()

            if not accounts:
                print("No accounts found")
                return 0

            print(f"Found {len(accounts)} account(s):\n")
            print(f"{'Account ID':<12} {'Holder':<25} {'Balance':>15} {'Status':<10}")
            print("-" * 70)

            for account in accounts:
                print(
                    f"{account.account_id:<12} "
                    f"{account.account_holder:<25} "
                    f"${account.balance:>14,.2f} "
                    f"{account.status:<10}"
                )

            return 0

    except BankingClientError as e:
        print(f"❌ Error: {e.message}")
        if args.verbose:
            logging.exception("List accounts failed with exception")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            logging.exception("Unexpected error listing accounts")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Enterprise Banking Client - Modernized Python 3.12 Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Transfer funds:
    %(prog)s transfer --from ACC1000 --to ACC1001 --amount 100.00

  Validate account:
    %(prog)s validate --account ACC1000

  Check balance:
    %(prog)s balance --account ACC1000

  List all accounts:
    %(prog)s list
        """,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available banking operations",
        dest="command",
        required=True,
    )

    # Transfer command
    transfer_parser = subparsers.add_parser(
        "transfer",
        help="Transfer funds between accounts",
        description="Transfer funds from one account to another",
    )
    transfer_parser.add_argument(
        "--from",
        "-f",
        dest="from_account",
        required=True,
        metavar="ACCOUNT",
        help="Source account ID (e.g., ACC1000)",
    )
    transfer_parser.add_argument(
        "--to",
        "-t",
        dest="to_account",
        required=True,
        metavar="ACCOUNT",
        help="Destination account ID (e.g., ACC1001)",
    )
    transfer_parser.add_argument(
        "--amount",
        "-a",
        type=Decimal,
        required=True,
        metavar="AMOUNT",
        help="Transfer amount (positive decimal)",
    )
    transfer_parser.set_defaults(func=handle_transfer)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an account",
        description="Check if an account exists and is valid",
    )
    validate_parser.add_argument(
        "--account",
        "-a",
        dest="account_id",
        required=True,
        metavar="ACCOUNT",
        help="Account ID to validate (e.g., ACC1000)",
    )
    validate_parser.set_defaults(func=handle_validate)

    # Balance command
    balance_parser = subparsers.add_parser(
        "balance",
        help="Check account balance",
        description="Get the current balance of an account",
    )
    balance_parser.add_argument(
        "--account",
        "-a",
        dest="account_id",
        required=True,
        metavar="ACCOUNT",
        help="Account ID to check (e.g., ACC1000)",
    )
    balance_parser.set_defaults(func=handle_balance)

    # List accounts command
    list_parser = subparsers.add_parser(
        "list",
        help="List all accounts",
        description="Display all available accounts",
    )
    list_parser.set_defaults(func=handle_list_accounts)

    return parser


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Execute the appropriate command handler
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
