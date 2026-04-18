import requests
import json

base_url = "http://localhost:8000"

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZ2VudF90ZXN0X2ZpbmFsQGV4YW1wbGUuY29tIiwicm9sZSI6ImhyIiwiZXhwIjoxNzc2NTIyMjg1fQ.eAGRlYFGOfUasMZWfDwVBCQBu1eRF-Jngdzaab2pmv8"
headers = {"Authorization": f"Bearer {TOKEN}"}

def check(name, status):
    result = "SUCCESS" if status < 400 else "FAILED"
    print(f"[{result}] {name}: {status}")

print("\n--- Starting API Verification ---")

r = requests.get(f"{base_url}/health")
check("GET /health", r.status_code)

fb_payload = {
    "full_name": "Test User",
    "email": "test@example.com",
    "rating": 5,
    "message": "Excellent API!",
    "category": "General"
}
r = requests.post(f"{base_url}/feedback/", json=fb_payload)
check("POST /feedback/", r.status_code)

r = requests.get(f"{base_url}/feedback/all")
check("GET /feedback/all", r.status_code)

r = requests.get(f"{base_url}/candidates/search?job_role=Developer", headers=headers)
check("GET /candidates/search", r.status_code)

r = requests.get(f"{base_url}/dashboard/stats", headers=headers)
check("GET /dashboard/stats", r.status_code)

r = requests.get(f"{base_url}/dashboard/export/csv", headers=headers)
check("GET /dashboard/export/csv", r.status_code)

builder_payload = {
    "template": "Modern",
    "personal_info": {
        "full_name": "API Tester",
        "email": "tester@api.com",
        "title": "Software Engineer"
    },
    "summary": "Testing the builder API.",
    "experience": [],
    "education": [],
    "skills": {"technical": ["API Testing"]}
}
r = requests.post(f"{base_url}/builder/generate", json=builder_payload, headers=headers)
check("POST /builder/generate", r.status_code)

print("--- Verification Complete ---\n")
