"""Shared pytest setup for PAUSE backend tests.

Ensures EXPO_PUBLIC_BACKEND_URL is always available by loading it from the
frontend .env when the shell didn't export it. This prevents the aggregate
suite from constructing empty/stale API bases (the iter-17 harness failure).
"""
import os
from pathlib import Path

_FRONTEND_ENV = Path(__file__).resolve().parents[2] / "frontend" / ".env"


def _load_backend_url() -> None:
    if os.environ.get("EXPO_PUBLIC_BACKEND_URL"):
        return
    if not _FRONTEND_ENV.exists():
        return
    for line in _FRONTEND_ENV.read_text().splitlines():
        line = line.strip()
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            os.environ["EXPO_PUBLIC_BACKEND_URL"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return


_load_backend_url()
