#!/usr/bin/env python3
"""
Health check endpoint for monitoring and orchestration.

Can be used by Docker, Kubernetes, or monitoring systems.
Returns exit code 0 for healthy, 1 for unhealthy.
"""

import sys
import time
from datetime import datetime

try:
    from banking_client import BankingClient
    from banking_client.config import get_settings
except ImportError:
    print("❌ UNHEALTHY: Cannot import banking_client")
    sys.exit(1)


def check_health(verbose: bool = False) -> bool:
    """
    Perform comprehensive health check.
    
    Args:
        verbose: Print detailed status information
        
    Returns:
        True if healthy, False otherwise
    """
    checks = {
        "module_import": False,
        "settings_load": False,
        "client_init": False,
        "server_connection": False,
    }
    
    start_time = time.time()
    
    # Check 1: Module imports
    try:
        from banking_client import BankingClient
        checks["module_import"] = True
        if verbose:
            print("✅ Module imports: OK")
    except Exception as e:
        if verbose:
            print(f"❌ Module imports: FAILED - {e}")
        return False
    
    # Check 2: Settings configuration
    try:
        settings = get_settings()
        checks["settings_load"] = True
        if verbose:
            print(f"✅ Settings loaded: {settings.api_base_url}")
    except Exception as e:
        if verbose:
            print(f"❌ Settings load: FAILED - {e}")
        return False
    
    # Check 3: Client initialization
    try:
        client = BankingClient()
        checks["client_init"] = True
        if verbose:
            print("✅ Client initialization: OK")
    except Exception as e:
        if verbose:
            print(f"❌ Client init: FAILED - {e}")
        return False
    
    # Check 4: Server connectivity (optional - don't fail if server is down)
    try:
        with BankingClient() as client:
            result = client.validate_account("ACC1000")
            checks["server_connection"] = True
            if verbose:
                print(f"✅ Server connection: OK (Account valid: {result.valid})")
    except Exception as e:
        if verbose:
            print(f"⚠️  Server connection: UNAVAILABLE - {e}")
        # Don't fail health check if server is down
        # Client itself is healthy, server might be starting
        pass
    
    elapsed = time.time() - start_time
    
    # Health check passes if core components are working
    is_healthy = checks["module_import"] and checks["settings_load"] and checks["client_init"]
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Health Check: {'HEALTHY ✅' if is_healthy else 'UNHEALTHY ❌'}")
        print(f"Time: {elapsed:.3f}s")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Checks: {sum(checks.values())}/{len(checks)} passed")
        print(f"{'='*60}")
    
    return is_healthy


def main():
    """Main entry point for health check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Banking Client Health Check")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    args = parser.parse_args()
    
    if args.json:
        import json
        checks_result = {
            "healthy": check_health(verbose=False),
            "timestamp": datetime.now().isoformat(),
            "service": "banking-client",
            "version": "1.0.0"
        }
        print(json.dumps(checks_result))
        sys.exit(0 if checks_result["healthy"] else 1)
    else:
        is_healthy = check_health(verbose=args.verbose or True)
        sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    main()

