"""
Test script for VideoNote Python Sidecar API
Tests the download functionality without requiring a video download.
"""

import sys
import time
import requests
from pathlib import Path

# Test configuration
BASE_URL = "http://127.0.0.1"  # Will be updated with actual port
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Sample YouTube URL
SAVE_PATH = str(Path.home() / "Downloads" / "videonote_test")


def test_health_check(port: int) -> bool:
    """Test the health check endpoint."""
    url = f"{BASE_URL}:{port}/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['message']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


def test_download_endpoint(port: int) -> bool:
    """Test the download endpoint (without actually downloading)."""
    url = f"{BASE_URL}:{port}/api/download"

    # Test with invalid data first
    print("\nTesting validation...")
    try:
        response = requests.post(url, json={}, timeout=5)
        if response.status_code == 422:  # Validation error expected
            print("✓ Validation working correctly")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"✗ Validation test error: {e}")

    # Test with valid data structure (but won't complete download without permission)
    print("\nTesting download endpoint structure...")
    try:
        response = requests.post(
            url,
            json={
                "url": TEST_URL,
                "save_path": SAVE_PATH,
                "format_preference": "best"
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("task_id"):
                print(f"✓ Download endpoint working: Task ID = {data['task_id']}")

                # Test status endpoint
                task_id = data["task_id"]
                status_url = f"{BASE_URL}:{port}/api/download/{task_id}"

                time.sleep(1)  # Wait a moment for background task to start

                status_response = requests.get(status_url, timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✓ Status endpoint working: {status_data.get('message', 'No message')}")
                    return True
                else:
                    print(f"✗ Status check failed: {status_response.status_code}")
                    return False
            else:
                print(f"✗ Invalid response structure: {data}")
                return False
        else:
            print(f"✗ Download endpoint failed: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Download test error: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("VideoNote Python Sidecar API Test")
    print("=" * 60)

    # Check if port is provided
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Error: Invalid port number")
            sys.exit(1)
    else:
        print("\nUsage: python test_api.py <port>")
        print("Example: python test_api.py 8000")
        sys.exit(1)

    print(f"\nTesting server at {BASE_URL}:{port}")
    print("-" * 60)

    # Run tests
    all_passed = True

    print("\n1. Testing Health Check Endpoint")
    print("-" * 60)
    if not test_health_check(port):
        all_passed = False

    print("\n2. Testing Download API Endpoints")
    print("-" * 60)
    if not test_download_endpoint(port):
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
