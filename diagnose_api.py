import requests
import json

base_url = "http://127.0.0.1:8000/api/v1"
headers = {"Authorization": "Bearer manager-demo"}

def check_endpoint(path):
    url = f"{base_url}{path}"
    print(f"Checking {url}...")
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_endpoint("/health")
    check_endpoint("/kho/titles")
    check_endpoint("/kho/items")
