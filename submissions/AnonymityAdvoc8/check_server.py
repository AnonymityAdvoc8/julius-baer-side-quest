#!/usr/bin/env python3
"""
Quick script to check if the banking server is running.
"""

import sys
import requests
from banking_client.config import get_settings

def check_server():
    """Check if the banking server is accessible."""
    try:
        settings = get_settings()
        url = f"{settings.api_base_url}/accounts/validate/ACC1000"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("✅ Banking server is running and accessible!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Server responded with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        settings = get_settings()
        print(f"❌ Cannot connect to banking server at {settings.api_base_url}")
        print()
        print("Please start the server:")
        print("  docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest")
        print()
        print("Or with Java:")
        print("  cd ../../server")
        print("  java -jar core-banking-api.jar")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Server connection timeout")
        return False
        
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    if check_server():
        sys.exit(0)
    else:
        sys.exit(1)

