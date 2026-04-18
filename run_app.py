#!/usr/bin/env python3
"""
Launch the FastAPI backend (Smart AI Resume Analyzer API).

Usage:
  python run_app.py
  # or: uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import subprocess


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    setup_script = os.path.join(root, "setup_chromedriver.py")
    if os.path.exists(setup_script):
        try:
            with open(os.devnull, "w", encoding="utf-8") as devnull:
                subprocess.run(
                    [sys.executable, setup_script],
                    stdout=devnull,
                    stderr=devnull,
                    check=False,
                )
        except Exception:
            pass

    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
