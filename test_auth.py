import requests
import json

base_url = "http://localhost:8000"

def test_login():
    url = f"{base_url}/auth/login"
    payload = {
        "email": "agent_test_final@example.com",
        "password": "password123"
    }
    response = requests.post(url, json=payload)
    print(f"Login Status: {response.status_code}")
    print(f"Login Response: {response.text}")
    return response.json()

def test_dashboard(token):
    url = f"{base_url}/dashboard/stats"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print(f"Dashboard Status: {response.status_code}")
    print(f"Dashboard Response: {response.text}")

if __name__ == "__main__":
    log = test_login()
    if "access_token" in log:
        test_dashboard(log["access_token"])
