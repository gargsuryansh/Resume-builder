#!/usr/bin/env python3
"""
Phase 4 — backend verification (no Streamlit).

Checks:
  - GET /health
  - OpenAPI reachable
  - Public /config/* routes (no auth)
  - Optional: admin JWT round-trip if ADMIN_EMAIL / ADMIN_PASSWORD env vars are set

Persistence: with Docker Compose, set DATA_DIR=/app/data and mount a volume so
resume_data.db and feedback.db stay under the same directory tree.

Usage:
  python scripts/verify_phase4_backend.py
  set API_BASE=http://localhost:8000 && python scripts/verify_phase4_backend.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read()


def _post_json(url: str, body: dict[str, Any]) -> tuple[int, bytes]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.read()


def status_report(completed: list[str], pending: list[str], notes: str) -> None:
    print("\n--- Phase 4 status report ---")
    print("Completed checks:", ", ".join(completed) or "(none)")
    print("Pending / manual:", ", ".join(pending) or "(none)")
    if notes:
        print("Notes:", notes)
    print("Say 'Continue' in your agent chat to resume from pending items.\n")


def main() -> int:
    base = os.environ.get("API_BASE", "http://127.0.0.1:8000").rstrip("/")
    completed: list[str] = []
    pending: list[str] = []

    # 1) Health
    try:
        code, raw = _get(f"{base}/health")
        if code != 200:
            raise RuntimeError(f"HTTP {code}")
        doc = json.loads(raw.decode())
        if doc.get("status") != "ok":
            raise RuntimeError(doc)
        completed.append("/health")
    except Exception as e:
        print("FAIL /health:", e)
        status_report(
            completed,
            ["Fix API process or API_BASE", "Full OpenAPI + config checks"],
            "Stop here until the server responds on /health.",
        )
        return 1

    # 2) OpenAPI
    try:
        code, _ = _get(f"{base}/openapi.json")
        if code != 200:
            raise RuntimeError(f"HTTP {code}")
        completed.append("/openapi.json")
    except Exception as e:
        print("WARN openapi:", e)
        pending.append("openapi.json unreachable")

    # 3) Public config
    for path in ("/config/job_roles", "/config/courses", "/config/job_filters"):
        try:
            code, raw = _get(f"{base}{path}")
            if code != 200:
                raise RuntimeError(f"{path} HTTP {code}")
            json.loads(raw.decode())
            completed.append(path)
        except Exception as e:
            print(f"FAIL {path}:", e)
            pending.append(path)

    # 4) Admin login (optional)
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    token: str | None = None
    if email and password:
        try:
            code, raw = _post_json(
                f"{base}/admin/login",
                {"email": email, "password": password},
            )
            if code != 200:
                raise RuntimeError(f"HTTP {code} {raw[:200]!r}")
            body = json.loads(raw.decode())
            token = body.get("access_token")
            if not token:
                raise RuntimeError("no access_token")
            completed.append("POST /admin/login")
        except Exception as e:
            print("WARN admin login:", e)
            pending.append("admin login (check credentials / verify_admin)")
    else:
        pending.append(
            "admin JWT checks (set ADMIN_EMAIL + ADMIN_PASSWORD to verify protected routes)"
        )

    if token:
        auth = {"Authorization": f"Bearer {token}"}
        for path in ("/admin/me", "/dashboard/metrics", "/admin/feedback/stats"):
            try:
                code, _ = _get(f"{base}{path}", headers=auth)
                if code != 200:
                    raise RuntimeError(f"{path} HTTP {code}")
                completed.append(path)
            except Exception as e:
                print(f"WARN {path}:", e)
                pending.append(path)

    print("Phase 4 backend verification:", "OK" if not pending else "PARTIAL")
    for c in completed:
        print("  [ok]", c)
    if pending:
        status_report(completed, pending, "")
        return 2
    print("All automated checks passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as e:
        print("HTTP error:", e.code, e.read()[:500])
        sys.exit(1)
