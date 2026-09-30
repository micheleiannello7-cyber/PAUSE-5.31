"""Cover-batch + optional-services regression checks (public preview API)."""

from __future__ import annotations

import json
import fcntl
import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
BATCH_DIR = ROOT / "memory" / "cover_batches"
BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "").rstrip("/")


def _require_base_url() -> str:
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL/EXPO_BACKEND_URL not set")
    return BASE_URL


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _read_batch(path: Path) -> dict:
    return json.loads(path.read_text())


def _all_batches() -> list[dict]:
    files = sorted(BATCH_DIR.glob("*.json"))
    assert files, "No cover batch reports found in memory/cover_batches"
    return [_read_batch(p) for p in files]


def _all_completed_generated_ids() -> list[str]:
    ids: list[str] = []
    for report in _all_batches():
        for item in report.get("generated", []):
            sid = item.get("id")
            if sid:
                ids.append(sid)
    return sorted(set(ids))


def _all_generated_records() -> list[dict]:
    recs: list[dict] = []
    for report in _all_batches():
        recs.extend(report.get("generated", []))
    return recs


# Module: health + optional services guard
def test_health_tts_and_stripe_guardrails() -> None:
    base = _require_base_url()
    s = _session()

    health = s.get(f"{base}/api/health", timeout=30)
    assert health.status_code == 200
    body = health.json()
    assert body.get("status") == "ok"
    assert body.get("db") is True

    tts_urls = [
        f"{base}/api/tts/voices",
        f"{base}/api/tts/status/volcanoes-basics",
        f"{base}/api/tts/voice-sample?voice=nova&lang=it",
        f"{base}/api/tts/story/volcanoes-basics?lang=it",
    ]
    for url in tts_urls:
        r = s.get(url, timeout=30)
        assert r.status_code == 503, f"Expected 503 for {url}, got {r.status_code}"

    warmup = s.post(f"{base}/api/tts/warmup/volcanoes-basics?lang=it", timeout=30)
    assert warmup.status_code == 503

    purchase_payload = {
        "user_id": "TEST_anon_cover_guard",
        "category_id": "scienza",
        "return_url": base,
    }
    purchase = s.post(f"{base}/api/purchases", json=purchase_payload, timeout=30)
    assert purchase.status_code == 503


# Module: batch baseline + no-overwrite preservation
def test_existing_cover_baseline_preserved() -> None:
    base = _require_base_url()
    s = _session()

    # The three-image pilot is the original 179-cover baseline. The next batch
    # correctly starts with 182, because it preserves the successful pilot too.
    run = min(_all_batches(), key=lambda report: len(report.get("existing_covers", [])))
    existing = run.get("existing_covers", [])
    assert len(existing) == 179
    generated_count = sum(1 for d in existing if d.get("hero_image_generated"))
    photo_count = sum(1 for d in existing if d.get("hero_image") and not d.get("hero_image_generated"))
    assert generated_count == 132
    assert photo_count == 47

    stories = s.get(f"{base}/api/stories?limit=1000&lang=it", timeout=60)
    assert stories.status_code == 200
    current = {d["id"]: d for d in stories.json()}

    for row in existing:
        sid = row["id"]
        assert sid in current, f"Missing story from baseline: {sid}"
        now = current[sid]
        assert now.get("hero_image", "") == row.get("hero_image", ""), f"hero_image changed for {sid}"
        if row.get("hero_image_generated"):
            assert now.get("hero_image_generated") == row.get("hero_image_generated"), f"hero_image_generated changed for {sid}"

    # Also preserve images added by earlier batches, not just the original set.
    for report in _all_batches():
        for row in report.get("existing_covers", []):
            sid = row["id"]
            assert current[sid].get("hero_image", "") == row.get("hero_image", "")
            assert current[sid].get("hero_image_generated") == row.get("hero_image_generated")


# Module: generated-cover media integrity (hero+thumb) + content-addressed checks
def test_generated_media_endpoints_and_dimensions() -> None:
    base = _require_base_url()
    s = _session()
    generated_ids = _all_completed_generated_ids()
    assert generated_ids, "No completed generated covers found in reports"

    for sid in generated_ids:
        for size, max_side in (("hero", 1200), ("thumb", 600)):
            r = s.get(f"{base}/api/media/{sid}?size={size}", timeout=60)
            assert r.status_code == 200, f"{sid} size={size} returned {r.status_code}"
            ctype = r.headers.get("content-type", "")
            assert "image/webp" in ctype.lower(), f"{sid} size={size} is not webp: {ctype}"
            img = Image.open(BytesIO(r.content))
            img.load()
            w, h = img.size
            assert h >= w, f"{sid} size={size} not portrait ({w}x{h})"
            assert max(w, h) <= max_side, f"{sid} size={size} exceeds max side ({w}x{h})"

    records = _all_generated_records()
    assert records, "No generated records found"
    for rec in records:
        digest = rec.get("hero_source_digest")
        hero_path = rec.get("hero_image_generated")
        thumb_path = rec.get("hero_image_thumb")
        source_file = rec.get("source_file")
        if digest and hero_path:
            assert f"-{digest}.webp" in hero_path
        if digest and thumb_path:
            assert f"-{digest}-thumb.webp" in thumb_path
        if source_file:
            assert (ROOT / source_file).exists(), f"Missing local original: {source_file}"


# Module: dry-run safety while active batch + lock/no-overwrite protections
def test_dry_run_lock_message_when_batch_active() -> None:
    # Exercise a REAL OS lock even after generation finishes. No provider calls.
    with (ROOT / "backend" / ".cover_generation.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass  # A running batch already holds the lock for this test.
        proc = subprocess.run(
            [sys.executable, str(ROOT / "backend" / "generate_covers.py"), "--dry-run"],
            cwd=ROOT / "backend",
            capture_output=True,
            text=True,
            timeout=120,
        )
    out = (proc.stdout or "") + (proc.stderr or "")
    assert "A cover batch is already running; no duplicate generation." in out


def test_no_overwrite_query_and_checkpoint_present_in_generator_code() -> None:
    code = (ROOT / "backend" / "generate_covers.py").read_text()
    assert '"hero_image_generated": {"$in": [None, ""]}' in code
    assert '"hero_image": current.get("hero_image")' in code
    assert "temporary.replace(report_path)" in code
    assert "if originals:" in code
