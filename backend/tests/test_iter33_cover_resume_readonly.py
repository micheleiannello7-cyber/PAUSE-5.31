"""Iteration 33 — read-only verification of cover resume/corrections rollout.

Modules covered:
- Catalog integrity (437 IDs, no missing/duplicate, covers present)
- Non-cover SHA256 parity against resume baseline
- Exact changed-cover ID set (27 IDs) + budget-stopped backlog unchanged
- Public API/media checks for updated stories (hero/thumb WebP constraints)
- Staged report publication metadata and filesystem artifacts
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "memory" / "cover_batches" / "resume_baseline.json"
A08_PATH = ROOT / "memory" / "cover_batches" / "a08de6ae79d149199e4b0a75fc7b3477.json"
R_LOCAL_01 = ROOT / "memory" / "cover_batches" / "corrections_local_01_staged" / "report.json"
R_EDITORIAL_01 = ROOT / "memory" / "cover_batches" / "corrections_editorial_01_staged" / "report.json"
R_LOCAL_02 = ROOT / "memory" / "cover_batches" / "corrections_local_02_staged" / "report.json"
R_ORBIT = ROOT / "memory" / "cover_batches" / "corrections_orbit_staged" / "report.json"
R_EDITORIAL_02 = ROOT / "memory" / "cover_batches" / "corrections_editorial_02_staged" / "report.json"
DEC_EDITORIAL_02 = ROOT / "memory" / "cover_batches" / "corrections_editorial_02.json"

EXCLUDED_NON_COVER_FIELDS = {
    "hero_image",
    "hero_image_generated",
    "hero_image_thumb",
    "hero_source_digest",
    "hero_bytes",
    "hero_generated_at",
    "hero_variants",
    "cover_review_reason",
}

COVER_FIELDS = [
    "hero_image",
    "hero_image_generated",
    "hero_image_thumb",
    "hero_source_digest",
    "hero_bytes",
    "hero_generated_at",
    "hero_variants",
    "cover_review_reason",
]


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
    base = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
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


def _read_json(path: Path):
    assert path.exists(), f"Missing file: {path}"
    return json.loads(path.read_text())


def _non_cover_sha(doc: dict) -> str:
    payload = {k: v for k, v in doc.items() if k not in EXCLUDED_NON_COVER_FIELDS and k != "_id"}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _cover_subset_from_doc(doc: dict) -> dict:
    return {k: doc.get(k) for k in COVER_FIELDS if k in doc}


def _cover_subset_from_baseline(entry: dict) -> dict:
    return dict(entry.get("cover") or {})


def _expected_27_ids() -> set[str]:
    a08 = _read_json(A08_PATH)
    r1 = _read_json(R_LOCAL_01)
    r2 = _read_json(R_EDITORIAL_01)
    r3 = _read_json(R_LOCAL_02)

    ids = set(x["id"] for x in a08.get("generated", []))
    ids.update((r1.get("candidates") or {}).keys())
    ids.update((r2.get("candidates") or {}).keys())
    ids.update((r3.get("candidates") or {}).keys())
    return ids


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


@pytest.fixture(scope="module")
def catalog_snapshot():
    baseline = _read_json(BASELINE_PATH)
    client, db = _mongo()
    try:
        docs = list(db.stories.find({}, {"_id": 0}))
    finally:
        client.close()
    return baseline, docs


# Module: process-guard and catalog inventory
def test_no_generation_process_running_and_catalog_complete(catalog_snapshot) -> None:
    baseline, docs = catalog_snapshot

    out = subprocess.run(
        "ps -ef | grep -E 'generate_covers|replace_reviewed_covers' | grep -v grep",
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.stdout.strip() == "", f"Unexpected active process:\n{out.stdout}"

    baseline_ids = [s["id"] for s in baseline["stories"]]
    current_ids = [d["id"] for d in docs]

    assert baseline.get("count") == 437
    assert len(baseline_ids) == 437
    assert len(current_ids) == 437
    assert len(set(current_ids)) == 437
    assert set(current_ids) == set(baseline_ids)

    missing_cover = [d["id"] for d in docs if not (d.get("hero_image_generated") or d.get("hero_image"))]
    assert not missing_cover, f"Stories without hero_image_generated/hero_image: {missing_cover[:10]}"


# Module: non-cover invariants and exact changed-cover IDs
def test_non_cover_sha_and_exact_27_changed_cover_ids(catalog_snapshot) -> None:
    baseline, docs = catalog_snapshot
    by_id = {d["id"]: d for d in docs}
    baseline_by_id = {s["id"]: s for s in baseline["stories"]}

    mismatched_sha = []
    changed_cover_ids = set()

    for sid, b in baseline_by_id.items():
        current = by_id[sid]
        current_sha = _non_cover_sha(current)
        if current_sha != b["content_sha256"]:
            mismatched_sha.append(sid)

        base_cover = _cover_subset_from_baseline(b)
        cur_cover = _cover_subset_from_doc(current)
        if cur_cover != base_cover:
            changed_cover_ids.add(sid)

    assert not mismatched_sha, f"Non-cover SHA mismatch on IDs: {mismatched_sha[:20]}"

    expected_27 = _expected_27_ids()
    assert len(expected_27) == 27
    assert changed_cover_ids == expected_27


# Module: budget-stopped editorial backlog must remain untouched
def test_editorial_02_stopped_and_9_ids_unchanged(catalog_snapshot) -> None:
    baseline, docs = catalog_snapshot
    report = _read_json(R_EDITORIAL_02)
    pending = _read_json(DEC_EDITORIAL_02)

    assert report.get("status") == "stopped"
    assert report.get("stop_reason") == "budget_or_quota"
    assert report.get("candidates") == {}

    pending_ids = [x["id"] for x in pending]
    assert len(pending_ids) == 9

    by_id = {d["id"]: d for d in docs}
    baseline_by_id = {s["id"]: s for s in baseline["stories"]}

    for sid in pending_ids:
        base_cover = _cover_subset_from_baseline(baseline_by_id[sid])
        cur_cover = _cover_subset_from_doc(by_id[sid])
        assert cur_cover == base_cover, f"Pending editorial_02 ID changed unexpectedly: {sid}"


# Module: staged reports publication metadata + artifact presence
@pytest.mark.parametrize(
    "report_path",
    [R_ORBIT, R_LOCAL_01, R_EDITORIAL_01, R_LOCAL_02],
)
def test_staged_reports_published_and_master_files_present(report_path: Path) -> None:
    report = _read_json(report_path)
    candidates = report.get("candidates") or {}
    assert candidates, f"No candidates in {report_path}"

    staged_dir = report_path.parent
    previous_originals = staged_dir / "previous_originals"

    for sid, rec in candidates.items():
        assert rec.get("status") == "published", f"{sid} not published in {report_path.name}"
        assert rec.get("before"), f"missing before for {sid}"
        assert rec.get("after"), f"missing after for {sid}"
        staged_file = Path(rec["file"])
        assert staged_file.exists(), f"missing staged file for {sid}: {staged_file}"

        if previous_originals.exists():
            matches = list(previous_originals.glob(f"{sid}.*"))
            if rec["before"].get("hero_image_generated"):
                assert matches, f"expected previous_originals backup for {sid}"


# Module: API detail + media endpoint checks for all 27 updated IDs
def test_api_detail_and_media_for_27_updated_ids(session: requests.Session, catalog_snapshot) -> None:
    base = _base_url()
    expected_27 = sorted(_expected_27_ids())

    _, docs = catalog_snapshot
    by_id = {d["id"]: d for d in docs}

    digest_re = re.compile(r"^[0-9a-f]{12}$")

    for sid in expected_27:
        # Public story detail
        story_r = session.get(f"{base}/api/stories/{sid}", timeout=60)
        assert story_r.status_code == 200, f"story detail failed: {sid}"
        story = story_r.json()
        assert story.get("id") == sid

        # DB metadata checks: storage paths + digest + no base64
        doc = by_id[sid]
        hero_path = doc.get("hero_image_generated")
        thumb_path = doc.get("hero_image_thumb")
        digest = doc.get("hero_source_digest")
        assert hero_path and thumb_path, f"Missing generated paths for {sid}"
        assert isinstance(hero_path, str) and hero_path.startswith("pause/") and "base64" not in hero_path.lower()
        assert isinstance(thumb_path, str) and thumb_path.startswith("pause/") and "base64" not in thumb_path.lower()
        assert isinstance(digest, str) and digest_re.fullmatch(digest), f"Invalid digest for {sid}: {digest}"

        # Public media endpoints
        for size, max_long in (("hero", 1200), ("thumb", 600)):
            media_r = session.get(
                f"{base}/api/media/{sid}",
                params={"size": size, "v": hero_path if size == "hero" else thumb_path},
                timeout=90,
            )
            assert media_r.status_code == 200, f"media {size} failed: {sid}"
            ctype = media_r.headers.get("content-type", "").lower()
            assert "image/webp" in ctype, f"non-webp {size} for {sid}: {ctype}"

            img = Image.open(BytesIO(media_r.content))
            img.load()
            w, h = img.size
            assert h > w, f"non-portrait {size} for {sid}: {(w, h)}"
            assert max(w, h) <= max_long, f"{size} too large for {sid}: {(w, h)}"
            if size == "hero":
                assert min(w, h) >= 768, f"hero short side <768 for {sid}: {(w, h)}"
