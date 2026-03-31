import requests
import json

BASE_URL = "http://localhost:5000"

def test_flow():
    # 1. We need a valid exchange ID. Let's try to find one from the DB or use a known one.
    # For testing, we'll assume there's an exchange with ID 1.
    # If not, this test will fail but we'll see the error message.
    
    # We'll use a user ID that we think exists. Let's try 1.
    
    test_data = {
        "requestId": 1,
        "userId": 1, # Numeric ID
        "partnerEmail": "test@gmail.com"
    }
    
    print("Testing initiate-completion with numeric userId...")
    try:
        response = requests.post(f"{BASE_URL}/exchange/initiate-completion", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with email userId
    test_data_email = {
        "requestId": 1,
        "userId": "owner@gmail.com", # Assuming this is the owner
        "partnerEmail": "test@gmail.com"
    }
    
    print("\nTesting initiate-completion with email userId...")
    try:
        response = requests.post(f"{BASE_URL}/exchange/initiate-completion", json=test_data_email)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_flow()
