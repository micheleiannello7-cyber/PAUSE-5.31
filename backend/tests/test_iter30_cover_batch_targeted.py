"""Targeted verification for current cover-batch scope (pilot3 + main20)."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from media_opt import encode_webp  # noqa: E402

REPORT_A = ROOT / "memory" / "cover_batches" / "5c7da1546ce245039d51fb4f8d4adbc2.json"
REPORT_B = ROOT / "memory" / "cover_batches" / "7dbe6ded62644d7e9ccf42931de7f6d0.json"
BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "").rstrip("/")


def _load_backend_env() -> None:
    env_path = ROOT / "backend" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key in {"MONGO_URL", "DB_NAME"} and not os.environ.get(key):
            os.environ[key] = val


def _base() -> str:
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL/EXPO_BACKEND_URL not set")
    return BASE_URL


def _mongo() -> MongoClient:
    _load_backend_env()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        pytest.skip("MONGO_URL/DB_NAME not set")
    return MongoClient(mongo_url)


def _reports() -> tuple[dict, dict]:
    return json.loads(REPORT_A.read_text()), json.loads(REPORT_B.read_text())


def _new_records() -> list[dict]:
    a, b = _reports()
    return list(a.get("generated", [])) + list(b.get("generated", []))


def _story_counts(db) -> dict[str, int]:
    rows = list(db.stories.find({}, {"_id": 0, "hero_image_generated": 1, "hero_image": 1}))
    generated = sum(1 for r in rows if r.get("hero_image_generated"))
    photo_only = sum(1 for r in rows if r.get("hero_image") and not r.get("hero_image_generated"))
    missing = sum(1 for r in rows if not r.get("hero_image_generated") and not r.get("hero_image"))
    return {"total": len(rows), "generated": generated, "photo_only": photo_only, "missing": missing}


# Module: report metadata + budget stop expectations
def test_reports_match_expected_scope_and_budget_stop() -> None:
    pilot, main = _reports()

    assert len(pilot.get("existing_covers", [])) == 373
    assert len(main.get("existing_covers", [])) == 376
    assert len(pilot.get("generated", [])) == 3
    assert len(main.get("generated", [])) == 20
    assert main.get("status") == "stopped"
    assert main.get("stop_reason") == "budget_or_quota"


# Module: 46 public media endpoints + digest path consistency
def test_new23_media_endpoints_are_webp_and_expected_dimensions() -> None:
    base = _base()
    session = requests.Session()

    records = _new_records()
    assert len(records) == 23

    for rec in records:
        sid = rec["id"]
        digest = rec.get("hero_source_digest")
        hero_path = rec.get("hero_image_generated")
        thumb_path = rec.get("hero_image_thumb")
        assert digest and hero_path and thumb_path
        assert f"-{digest}.webp" in hero_path
        assert f"-{digest}-thumb.webp" in thumb_path

        for size, expected, version in (
            ("hero", (896, 1200), hero_path),
            ("thumb", (448, 600), thumb_path),
        ):
            r = session.get(f"{base}/api/media/{sid}?size={size}&v={requests.utils.quote(version, safe='')}", timeout=60)
            assert r.status_code == 200, f"{sid} {size} returned {r.status_code}"
            assert "image/webp" in r.headers.get("content-type", "").lower()
            image = Image.open(BytesIO(r.content))
            image.load()
            assert image.size == expected, f"{sid} {size} wrong size: {image.size}"


# Module: preservation of pre-existing snapshot entries from pilot baseline
def test_existing_373_snapshot_fields_preserved_in_mongo() -> None:
    pilot, _ = _reports()
    existing = pilot.get("existing_covers", [])
    assert len(existing) == 373

    with _mongo() as client:
        db = client[os.environ["DB_NAME"]]
        ids = [row["id"] for row in existing]
        docs = {
            d["id"]: d
            for d in db.stories.find(
                {"id": {"$in": ids}},
                {"_id": 0, "id": 1, "hero_image": 1, "hero_image_generated": 1},
            )
        }

    assert len(docs) == 373
    for row in existing:
        now = docs[row["id"]]
        assert now.get("hero_image", "") == row.get("hero_image", "")
        if row.get("hero_image_generated"):
            assert now.get("hero_image_generated") == row.get("hero_image_generated")


# Module: catalog coverage counts after this batch
def test_catalog_counts_are_437_total_396_covered_41_missing() -> None:
    with _mongo() as client:
        db = client[os.environ["DB_NAME"]]
        counts = _story_counts(db)

    assert counts["total"] == 437
    assert counts["generated"] == 349
    assert counts["photo_only"] == 47
    assert counts["generated"] + counts["photo_only"] == 396
    assert counts["missing"] == 41


# Module: dry-run safety (count + no mutation)
def test_generate_covers_dry_run_reports_41_and_does_not_mutate_db() -> None:
    with _mongo() as client:
        db = client[os.environ["DB_NAME"]]
        before = _story_counts(db)

    proc = subprocess.run(
        [sys.executable, str(ROOT / "backend" / "generate_covers.py"), "--dry-run"],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert "missing covers: 41" in combined

    with _mongo() as client:
        db = client[os.environ["DB_NAME"]]
        after = _story_counts(db)

    assert before == after


# Module: lock safety for duplicate execution prevention
def test_generate_covers_lock_blocks_duplicate_execution() -> None:
    with (ROOT / "backend" / ".cover_generation.lock").open("a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "backend" / "generate_covers.py"), "--dry-run"],
            cwd=ROOT / "backend",
            capture_output=True,
            text=True,
            timeout=120,
        )
    out = (proc.stdout or "") + (proc.stderr or "")
    assert "A cover batch is already running; no duplicate generation." in out


# Module: source retention + media_opt pass-through, resize, EXIF orientation
def test_source_webp_retained_and_encode_webp_behaviour() -> None:
    records = _new_records()
    assert len(records) == 23
    for rec in records:
        source_file = rec.get("source_file")
        assert source_file
        p = ROOT / source_file
        assert p.exists(), f"Missing source: {source_file}"
        assert p.suffix.lower() == ".webp"

    sample_path = ROOT / records[0]["source_file"]
    raw = sample_path.read_bytes()
    # Same-size WebP should pass through byte-identical.
    assert encode_webp(raw, 1200) == raw

    thumb = encode_webp(raw, 600)
    t = Image.open(BytesIO(thumb))
    t.load()
    assert t.size == (448, 600)

    # JPEG EXIF orientation still respected (orientation=6 -> rotate to portrait).
    landscape = Image.new("RGB", (1200, 800), color=(30, 80, 120))
    exif = Image.Exif()
    exif[274] = 6
    buf = BytesIO()
    landscape.save(buf, format="JPEG", exif=exif.tobytes())
    oriented = encode_webp(buf.getvalue(), 600)
    oriented_img = Image.open(BytesIO(oriented))
    oriented_img.load()
    assert oriented_img.size == (400, 600)


# Module: two local-retouch stories are live on current versioned media
@pytest.mark.parametrize(
    "sid",
    [
        "v8-why-do-we-feel-embarrassed-for-other-people",
        "v8-why-do-we-drive-on-the-right-and-the-british-on-the-left",
    ],
)
def test_retouched_covers_load_via_current_version_query(sid: str) -> None:
    base = _base()
    session = requests.Session()

    story = session.get(f"{base}/api/stories/{sid}?lang=it", timeout=60)
    assert story.status_code == 200
    payload = story.json()
    hero_v = payload.get("hero_image_generated")
    thumb_v = payload.get("hero_image_thumb")
    assert hero_v and thumb_v

    hero = session.get(f"{base}/api/media/{sid}?size=hero&v={requests.utils.quote(hero_v, safe='')}", timeout=60)
    thumb = session.get(f"{base}/api/media/{sid}?size=thumb&v={requests.utils.quote(thumb_v, safe='')}", timeout=60)
    assert hero.status_code == 200
    assert thumb.status_code == 200
    assert "image/webp" in hero.headers.get("content-type", "").lower()
    assert "image/webp" in thumb.headers.get("content-type", "").lower()
