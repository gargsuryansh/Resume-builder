"""Phase 4 — lightweight API contract checks (run with pytest)."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_public_config_routes():
    for path in ("/config/job_roles", "/config/courses", "/config/job_filters"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert isinstance(r.json(), (dict, list))


def test_protected_routes_require_auth():
    for path in (
        "/analyze/basic",
        "/analyze/ai",
        "/builder/generate",
        "/jobs/search",
        "/dashboard/metrics",
        "/admin/me",
        "/admin/feedback/stats",
        "/admin/export/resumes",
    ):
        if path == "/analyze/basic":
            r = client.post(path)
        elif path == "/analyze/ai":
            r = client.post(path)
        elif path == "/builder/generate":
            r = client.post(path, json={})
        elif path == "/jobs/search":
            r = client.get(path)
        elif path.startswith("/admin/export"):
            r = client.get(path)
        else:
            r = client.get(path)
        assert r.status_code == 403 or r.status_code == 401, (
            f"{path} expected 401/403 without auth, got {r.status_code}"
        )
