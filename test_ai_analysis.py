#!/usr/bin/env python3
"""
Test script to verify AI analysis functionality
"""
import os
import sys
import django
import requests
from pathlib import Path

# Setup Django environment
sys.path.append('/mnt/c/Users/ZC/VSProject/homework')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_learning_platform.settings')
django.setup()

from exercises.vllm_service import VLLMService
from django.core.files.uploadedfile import SimpleUploadedFile

def test_vllm_service():
    """Test VL LLM Service"""
    print("Testing VL LLM Service...")

    try:
        service = VLLMService()
        print(f"✓ VLLM Service initialized successfully")
        print(f"  - API URL: {service.api_url}")
        print(f"  - Model: {service.model_name}")
        print(f"  - API Key: {'*' * 10}{service.api_key[-10:] if service.api_key else 'None'}")

        return True
    except Exception as e:
        print(f"✗ VLLM Service initialization failed: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity"""
    print("\nTesting API connectivity...")

    try:
        from django.conf import settings
        api_config = settings.VLLM_API_CONFIG

        headers = {
            "Authorization": f"Bearer {api_config['default_api_key']}",
            "Content-Type": "application/json"
        }

        # Simple ping test (send minimal payload)
        payload = {
            "model": api_config['default_model'],
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }

        response = requests.post(
            api_config['default_url'],
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print("✓ API connectivity successful")
            return True
        else:
            print(f"✗ API connectivity failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"✗ API connectivity test failed: {e}")
        return False

def test_frontend_upload_endpoint():
    """Test if upload endpoint is accessible"""
    print("\nTesting upload endpoint accessibility...")

    try:
        response = requests.get('http://localhost:8000/api/exercises/upload/', timeout=5)
        # This should return 405 Method Not Allowed for GET request, which means endpoint exists
        if response.status_code == 405:
            print("✓ Upload endpoint is accessible")
            return True
        else:
            print(f"✗ Unexpected response from upload endpoint: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Django server")
        return False
    except Exception as e:
        print(f"✗ Upload endpoint test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("AI Analysis Functionality Test")
    print("=" * 50)

    results = []

    # Test 1: VL LLM Service
    results.append(test_vllm_service())

    # Test 2: API Connectivity
    results.append(test_api_connectivity())

    # Test 3: Frontend Upload Endpoint
    results.append(test_frontend_upload_endpoint())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All tests passed! AI analysis functionality should work correctly.")
    else:
        print("❌ Some tests failed. AI analysis may not work properly.")

    print("=" * 50)

if __name__ == "__main__":
    main()