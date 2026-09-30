"""Iteration 31 — read-only validation for active cover batch + deck/guards.

Scope:
- active cover-batch report consistency (id 56ba...)
- generated media endpoints decode correctly (hero/thumb WebP portrait)
- discover-batch uniqueness/exclude contract remains intact
- optional paid flows remain disabled (TTS + Stripe)
"""

from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "memory" / "cover_batches" / "56ba5742cf674cb7a8acbbc14cf85680.json"


def _load_env() -> None:
    """Load only required vars from frontend/backend env files if missing."""
    front_env = ROOT / "frontend" / ".env"
    if front_env.exists() and not os.environ.get("EXPO_PUBLIC_BACKEND_URL"):
        for raw in front_env.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "EXPO_PUBLIC_BACKEND_URL":
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

    back_env = ROOT / "backend" / ".env"
    if back_env.exists() and (not os.environ.get("MONGO_URL") or not os.environ.get("DB_NAME")):
        for raw in back_env.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            key = k.strip()
            if key in {"MONGO_URL", "DB_NAME"} and not os.environ.get(key):
                os.environ[key] = v.strip().strip('"').strip("'")


def _base_url() -> str:
    _load_env()
    base = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "").rstrip("/")
    if not base:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL / EXPO_BACKEND_URL not set")
    return base


def _mongo():
    _load_env()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        pytest.skip("MONGO_URL / DB_NAME not set")
    client = MongoClient(mongo_url)
    return client, client[db_name]


def _report() -> dict:
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"
    return json.loads(REPORT_PATH.read_text())


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


# Module: backend health and optional-service guards
def test_health_tts_and_stripe_guards(session: requests.Session) -> None:
    base = _base_url()

    health = session.get(f"{base}/api/health", timeout=30)
    assert health.status_code == 200
    payload = health.json()
    assert payload.get("status") == "ok"

    tts = session.get(f"{base}/api/tts/status/black-holes-basics", timeout=30)
    assert tts.status_code == 503
    assert "disabled" in tts.text.lower()

    purchase = session.post(
        f"{base}/api/purchases",
        json={
            "user_id": "TEST_iter31_user",
            "category_id": "spazio",
            "return_url": base,
        },
        timeout=30,
    )
    assert purchase.status_code == 503
    assert "not configured" in purchase.text.lower()


# Module: cover-batch metadata and progress snapshot
def test_cover_report_baseline_and_progress_snapshot() -> None:
    report = _report()
    assert report["id"] == "56ba5742cf674cb7a8acbbc14cf85680"
    assert report["total"] == 41
    assert len(report.get("existing_covers", [])) == 396
    assert report.get("status") in {"running", "stopped", "completed"}
    assert len(report.get("generated", [])) >= 3


# Module: DB coverage counts and generated-id persistence
def test_db_total_and_generated_ids_applied() -> None:
    report = _report()
    generated = report.get("generated", [])
    generated_ids = [r["id"] for r in generated]

    client, db = _mongo()
    try:
        total = db.stories.count_documents({})
        assert total == 437

        if generated_ids:
            docs = list(db.stories.find({"id": {"$in": generated_ids}}, {"_id": 0, "id": 1, "hero_image_generated": 1, "hero_image_thumb": 1}))
            assert len(docs) == len(generated_ids)
            for doc in docs:
                assert doc.get("hero_image_generated")
                assert doc.get("hero_image_thumb")
    finally:
        client.close()


# Module: active-run generated media validity (public endpoints)
def test_generated_media_endpoints_webp_portrait_and_limits(session: requests.Session) -> None:
    base = _base_url()
    report = _report()
    generated = report.get("generated", [])
    assert generated, "No generated entries yet to validate"

    for rec in generated:
        sid = rec["id"]
        hero_v = rec.get("hero_image_generated")
        thumb_v = rec.get("hero_image_thumb")
        assert hero_v and thumb_v

        for size, version, max_side in (("hero", hero_v, 1200), ("thumb", thumb_v, 600)):
            r = session.get(
                f"{base}/api/media/{sid}",
                params={"size": size, "v": version},
                timeout=60,
            )
            assert r.status_code == 200, f"{sid} {size} -> {r.status_code}"
            assert "image/webp" in r.headers.get("content-type", "").lower()
            img = Image.open(BytesIO(r.content))
            img.load()
            assert img.height > img.width, f"{sid} {size} not portrait: {img.size}"
            assert max(img.size) <= max_side, f"{sid} {size} exceeds limit: {img.size}"


# Module: discover-batch uniqueness/exclude regression
def test_discover_batch_uniqueness_and_exclude(session: requests.Session) -> None:
    base = _base_url()
    first = session.get(
        f"{base}/api/discover-batch",
        params={"user_id": "TEST_iter31_deck", "count": 7, "lang": "it"},
        timeout=30,
    )
    assert first.status_code == 200
    a = first.json()
    assert len(a) == 7
    a_ids = [row["id"] for row in a]
    assert len(set(a_ids)) == 7

    second = session.get(
        f"{base}/api/discover-batch",
        params={"user_id": "TEST_iter31_deck", "count": 7, "lang": "it", "exclude": ",".join(a_ids)},
        timeout=30,
    )
    assert second.status_code == 200
    b = second.json()
    assert len(b) == 7
    b_ids = {row["id"] for row in b}
    assert not (set(a_ids) & b_ids)
