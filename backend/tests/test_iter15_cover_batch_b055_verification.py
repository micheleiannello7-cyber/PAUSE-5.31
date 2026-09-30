"""Iteration 15 — cover batch b055 verification (read-only, no paid calls).

Modules covered:
- batch/report integrity + stop reason guards
- DB/API/media consistency for generated/rejected/current covers
- safety guards that must refuse replacements while 10 covers are still missing
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "memory" / "cover_batches" / "b05599495e734316a8fa89c707c13a43.json"
TARGET_REJECTED_ID = "lez-orbite-gravita"
TARGET_GOOD_ID = "v8-lez-saying-no-without-guilt-the-6-step-method"
EXPECTED_MISSING = {
    "lez-orbite-gravita",
    "lez-teoria-colore",
    "lez-leggere-mappa",
    "lez-fusi-orari",
    "lez-etimologia",
    "lez-calendario",
    "lez-respirazione",
    "lez-febbre",
    "lez-ghiaccio-galleggia",
    "lez-eco",
}


def _load_env() -> None:
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
    base = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
    if not base:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL not set")
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
    assert REPORT_PATH.exists(), f"Missing report file: {REPORT_PATH}"
    return json.loads(REPORT_PATH.read_text())


def _norm(value):
    return value or ""


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


def test_report_metadata_and_status_guardrails() -> None:
    report = _report()
    assert report["id"] == "b05599495e734316a8fa89c707c13a43"
    assert report["status"] == "stopped"
    assert report.get("stop_reason") == "budget_or_quota"
    assert report["total"] == 25
    assert report.get("ok") == 16
    assert report.get("fail") == 1
    assert report.get("published") == 15
    assert len(report.get("generated", [])) == 15
    assert len(report.get("rejected", [])) == 1
    assert len(report.get("existing_covers", [])) == 412
    assert report.get("encoding", {}).get("format") == "webp"
    assert report.get("encoding", {}).get("quality") == 84


def test_generated_and_rejected_lists_are_expected() -> None:
    report = _report()
    generated_ids = {row["id"] for row in report.get("generated", [])}
    rejected_ids = {row["id"] for row in report.get("rejected", [])}
    assert TARGET_REJECTED_ID in rejected_ids
    assert TARGET_REJECTED_ID not in generated_ids
    assert TARGET_GOOD_ID in generated_ids


def test_generated_story_api_links_digest_and_fields(session: requests.Session) -> None:
    base = _base_url()
    report = _report()

    for rec in report["generated"]:
        sid = rec["id"]
        digest = rec["hero_source_digest"]
        hero_path = rec["hero_image_generated"]
        thumb_path = rec["hero_image_thumb"]

        response = session.get(f"{base}/api/stories/{sid}", timeout=45)
        assert response.status_code == 200, f"/stories/{sid} => {response.status_code}"
        data = response.json()

        assert data["hero_image_generated"] == hero_path
        assert data["hero_image_thumb"] == thumb_path
        assert digest in data["hero_image_generated"]
        assert digest in data["hero_image_thumb"]


def test_generated_media_endpoints_decode_webp_and_no_duplicate_hero_bytes(session: requests.Session) -> None:
    base = _base_url()
    report = _report()

    seen_hero_hashes: set[str] = set()
    for rec in report["generated"]:
        sid = rec["id"]
        for size, max_side in (("hero", 1200), ("thumb", 600)):
            r = session.get(f"{base}/api/media/{sid}", params={"size": size}, timeout=75)
            assert r.status_code == 200, f"{sid} {size} -> {r.status_code}"
            assert "image/webp" in r.headers.get("content-type", "").lower()

            img = Image.open(BytesIO(r.content))
            img.load()
            w, h = img.size
            assert h > w, f"{sid} {size} not portrait: {(w, h)}"
            assert max(w, h) <= max_side, f"{sid} {size} max side too large: {(w, h)}"

            if size == "hero":
                payload_hash = hashlib.sha256(r.content).hexdigest()
                assert payload_hash not in seen_hero_hashes, f"Duplicate hero bytes found for {sid}"
                seen_hero_hashes.add(payload_hash)


def test_generated_original_files_persisted_in_backend_covers() -> None:
    report = _report()
    for rec in report["generated"]:
        sid = rec["id"]
        path = ROOT / "backend" / "covers" / f"{sid}.webp"
        assert path.exists(), f"Missing original backend/covers file for {sid}"
        assert path.stat().st_size > 0


def test_existing_412_unchanged_against_db_and_story_api(session: requests.Session) -> None:
    base = _base_url()
    report = _report()
    existing = report["existing_covers"]
    ids = [row["id"] for row in existing]

    # DB check in bulk
    client, db = _mongo()
    try:
        docs = list(db.stories.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "hero_image": 1, "hero_image_generated": 1}))
    finally:
        client.close()
    by_id = {doc["id"]: doc for doc in docs}
    assert len(by_id) == len(ids)

    # Story API check in bulk
    list_resp = session.get(f"{base}/api/stories", params={"limit": 600}, timeout=90)
    assert list_resp.status_code == 200
    story_rows = {row["id"]: row for row in list_resp.json()}

    for row in existing:
        sid = row["id"]
        db_doc = by_id[sid]
        api_doc = story_rows.get(sid)
        assert api_doc is not None, f"{sid} missing from /api/stories"

        expected_generated = _norm(row.get("hero_image_generated"))
        expected_photo = _norm(row.get("hero_image"))

        assert _norm(db_doc.get("hero_image_generated")) == expected_generated, f"DB generated changed for {sid}"
        assert _norm(db_doc.get("hero_image")) == expected_photo, f"DB hero_image changed for {sid}"
        assert _norm(api_doc.get("hero_image_generated")) == expected_generated, f"API generated changed for {sid}"
        assert _norm(api_doc.get("hero_image")) == expected_photo, f"API hero_image changed for {sid}"


def test_orbit_quarantine_and_absence_from_live_media(session: requests.Session) -> None:
    base = _base_url()
    report = _report()
    rejected = report["rejected"][0]
    assert rejected["id"] == TARGET_REJECTED_ID

    quarantined_path = ROOT / rejected["source_file"]
    assert quarantined_path.exists(), f"Missing quarantined original: {quarantined_path}"
    assert quarantined_path.stat().st_size > 0

    backend_cover = ROOT / "backend" / "covers" / f"{TARGET_REJECTED_ID}.webp"
    assert not backend_cover.exists(), "Rejected cover should not persist in backend/covers"

    story_resp = session.get(f"{base}/api/stories/{TARGET_REJECTED_ID}", timeout=45)
    assert story_resp.status_code == 200
    story = story_resp.json()
    assert not story.get("hero_image_generated")
    assert not story.get("hero_image_thumb")

    media_resp = session.get(f"{base}/api/media/{TARGET_REJECTED_ID}", timeout=45)
    assert media_resp.status_code == 404


def test_previous_rejected_portrait_now_valid_and_not_quarantined(session: requests.Session) -> None:
    base = _base_url()
    report = _report()
    generated_map = {row["id"]: row for row in report["generated"]}
    assert TARGET_GOOD_ID in generated_map

    # It must not be in this run's quarantined list.
    assert all(row["id"] != TARGET_GOOD_ID for row in report.get("rejected", []))

    media_resp = session.get(f"{base}/api/media/{TARGET_GOOD_ID}", timeout=45)
    assert media_resp.status_code == 200
    assert "image/webp" in media_resp.headers.get("content-type", "").lower()


def test_current_coverage_count_and_remaining_missing_ids() -> None:
    client, db = _mongo()
    try:
        docs = list(db.stories.find({}, {"_id": 0, "id": 1, "hero_image": 1, "hero_image_generated": 1}))
    finally:
        client.close()

    covered = [d["id"] for d in docs if d.get("hero_image_generated") or d.get("hero_image")]
    missing = {d["id"] for d in docs if not (d.get("hero_image_generated") or d.get("hero_image"))}
    assert len(docs) == 437
    assert len(covered) == 427
    assert missing == EXPECTED_MISSING


def test_guard_scripts_refuse_operations_before_full_coverage() -> None:
    # catalog snapshot must refuse while missing covers remain.
    catalog = subprocess.run(
        ["python", "catalog_cover_sheets.py"],
        cwd=str(ROOT / "backend"),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert catalog.returncode != 0
    assert "Finish missing covers BEFORE catalog review" in (catalog.stdout + catalog.stderr)

    # replacement script must refuse while empty covers still exist.
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write("[]")
        decisions = handle.name
    try:
        replace = subprocess.run(
            ["python", "replace_reviewed_covers.py", decisions],
            cwd=str(ROOT / "backend"),
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        Path(decisions).unlink(missing_ok=True)

    assert replace.returncode != 0
    assert "Complete empty covers before replacing existing covers" in (replace.stdout + replace.stderr)
