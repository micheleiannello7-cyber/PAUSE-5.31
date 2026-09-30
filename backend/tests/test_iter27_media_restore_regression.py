"""Iteration 27: media restoration + cover sync regression tests for PAUSE."""

# Module coverage: category media CDN headers, generated/local covers integrity, idempotence scripts, and non-existent IDs.
import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from covers_sync import sync_local_covers  # noqa: E402
from generate_covers import budget_error  # noqa: E402


def _load_env_if_missing() -> None:
    backend_env = BACKEND_DIR / ".env"
    if backend_env.exists():
        for raw in backend_env.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ("MONGO_URL", "DB_NAME") and not os.environ.get(key):
                os.environ[key] = value


_load_env_if_missing()
BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL / EXPO_BACKEND_URL not configured", allow_module_level=True)
if not MONGO_URL or not DB_NAME:
    pytest.skip("MONGO_URL / DB_NAME not configured", allow_module_level=True)


def _parse_webp_size(payload: bytes) -> tuple[int, int]:
    if len(payload) < 30 or payload[0:4] != b"RIFF" or payload[8:12] != b"WEBP":
        raise AssertionError("Not a valid WEBP payload")
    idx = 12
    while idx + 8 <= len(payload):
        chunk = payload[idx:idx + 4]
        size = int.from_bytes(payload[idx + 4:idx + 8], "little")
        data_start = idx + 8
        data_end = data_start + size
        if data_end > len(payload):
            break
        if chunk == b"VP8X" and size >= 10:
            w = int.from_bytes(payload[data_start + 4:data_start + 7], "little") + 1
            h = int.from_bytes(payload[data_start + 7:data_start + 10], "little") + 1
            return w, h
        if chunk == b"VP8L" and size >= 5:
            b0, b1, b2, b3 = payload[data_start + 1:data_start + 5]
            w = ((b1 & 0x3F) << 8 | b0) + 1
            h = ((b3 & 0x0F) << 10 | (b2 << 2) | ((b1 & 0xC0) >> 6)) + 1
            return w, h
        if chunk == b"VP8 " and size >= 10:
            w = int.from_bytes(payload[data_start + 6:data_start + 8], "little") & 0x3FFF
            h = int.from_bytes(payload[data_start + 8:data_start + 10], "little") & 0x3FFF
            return w, h
        idx = data_end + (size % 2)
    raise AssertionError("Unable to parse WEBP dimensions")


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    return s


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


class TestCategoryMediaFromManifest:
    def test_all_13_manifest_category_media_webp_and_etag_304(self, session: requests.Session):
        manifest = ast.literal_eval((BACKEND_DIR / "category_art_manifest.json").read_text())
        ids = list(manifest["artworks"].keys())
        assert len(ids) == 13
        for category_id in ids:
            response = session.get(f"{BASE_URL}/api/category-media/{category_id}", timeout=30)
            assert response.status_code == 200, f"{category_id}: {response.status_code}"
            assert response.headers.get("content-type", "").startswith("image/webp")
            etag = response.headers.get("ETag")
            assert etag
            again = session.get(
                f"{BASE_URL}/api/category-media/{category_id}",
                headers={"If-None-Match": etag},
                timeout=30,
            )
            assert again.status_code == 304, f"{category_id}: expected 304"


class TestGeneratedAndLocalCovers:
    def test_assets_report_counts_68(self, session: requests.Session):
        response = session.get(f"{BASE_URL}/api/content/assets-report", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["covers"]["stories"] == 437
        assert data["covers"]["with_cover"] == 68
        assert data["covers"]["with_thumb"] == 68

    def test_generated_sources_have_60_ids(self):
        generated = ast.literal_eval((BACKEND_DIR / "generated_cover_sources.json").read_text())
        assert len(generated["sources"]) == 60

    def test_generated_cover_ids_have_media_variants_and_preserved_story_content(self, session: requests.Session):
        generated = ast.literal_eval((BACKEND_DIR / "generated_cover_sources.json").read_text())
        per_category = {}
        for sid in generated["sources"].keys():
            detail = session.get(f"{BASE_URL}/api/stories/{sid}", timeout=30)
            assert detail.status_code == 200, f"story missing: {sid}"
            story = detail.json()
            assert story.get("hero_image_generated"), f"missing hero generated: {sid}"
            assert story.get("hero_image_thumb"), f"missing thumb generated: {sid}"
            assert isinstance(story.get("hero_image"), str), f"hero_image not preserved as string: {sid}"
            assert len(story.get("chapters") or []) >= 1, f"chapters missing for {sid}"
            per_category[story["category_id"]] = per_category.get(story["category_id"], 0) + 1

            hero = session.get(f"{BASE_URL}/api/media/{sid}?size=hero", timeout=30)
            assert hero.status_code == 200
            assert hero.headers.get("content-type", "").startswith("image/webp")
            hero_w, hero_h = _parse_webp_size(hero.content)
            assert max(hero_w, hero_h) <= 1200

            thumb = session.get(f"{BASE_URL}/api/media/{sid}?size=thumb", timeout=30)
            assert thumb.status_code == 200
            assert thumb.headers.get("content-type", "").startswith("image/webp")
            thumb_w, thumb_h = _parse_webp_size(thumb.content)
            assert max(thumb_w, thumb_h) <= 600

        assert len(per_category) == 12
        assert set(per_category.values()) == {5}

    def test_local_8_covers_are_linked(self, session: requests.Session):
        local_ids = sorted(p.stem for p in (BACKEND_DIR / "covers").iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
        assert len(local_ids) == 8
        for sid in local_ids:
            detail = session.get(f"{BASE_URL}/api/stories/{sid}", timeout=30)
            assert detail.status_code == 200, f"local cover story missing: {sid}"
            story = detail.json()
            assert story.get("hero_image_generated"), f"local generated cover missing: {sid}"
            assert story.get("hero_image_thumb"), f"local thumb missing: {sid}"

    def test_missing_cover_urls_remain_210(self, mongo_db):
        count = mongo_db.stories.count_documents({
            "$and": [
                {"$or": [{"hero_image_generated": {"$exists": False}}, {"hero_image_generated": None}, {"hero_image_generated": ""}]},
                {"$or": [{"hero_image": {"$exists": False}}, {"hero_image": None}, {"hero_image": ""}]},
            ]
        })
        assert count == 210


class TestScriptIdempotenceAndSelection:
    def test_restore_generated_covers_rerun_skips_60(self):
        cmd = [sys.executable, str(BACKEND_DIR / "restore_generated_covers.py")]
        run = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True, timeout=180, check=True)
        out = [line.strip() for line in run.stdout.splitlines() if line.strip()]
        stats = ast.literal_eval(out[-1])
        assert stats["uploaded"] == 0
        assert stats["unknown"] == 0
        assert stats["skipped"] == 60

    def test_generate_covers_dry_run_only_reports_missing_and_no_generation(self):
        cmd = [sys.executable, str(BACKEND_DIR / "generate_covers.py"), "--dry-run"]
        run = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True, timeout=120, check=True)
        stdout = run.stdout
        assert "missing covers: 210" in stdout
        assert "GEN" not in stdout
        assert "FAIL" not in stdout

    def test_budget_error_detection(self):
        assert budget_error(RuntimeError("402 budget exhausted")) is True
        assert budget_error(RuntimeError("quota exceeded")) is True
        assert budget_error(RuntimeError("network timeout")) is False


class TestCoversSyncRegressionUnit:
    def test_sync_local_covers_handles_doc_with_missing_digest_not_unknown(self, monkeypatch):
        class FakeStories:
            def __init__(self):
                self.calls = []

            async def find_one(self, _query, _proj):
                return {"id": "test-story"}

            async def update_one(self, query, update):
                self.calls.append((query, update))

        class FakeDB:
            def __init__(self):
                self.stories = FakeStories()

        fake_db = FakeDB()

        monkeypatch.setattr("covers_sync.local_covers", lambda: {"test-story": Path("/tmp/test-story.png")})
        monkeypatch.setattr(Path, "read_bytes", lambda _self: b"fake-image")
        monkeypatch.setattr("covers_sync.source_digest", lambda _raw: "digest123")
        monkeypatch.setattr("covers_sync.upload_cover", lambda _sid, _raw: {"hero_image_generated": "pause/hero/test.webp", "hero_source_digest": "digest123", "hero_image_thumb": "pause/hero/test-thumb.webp"})

        import asyncio

        stats = asyncio.run(sync_local_covers(fake_db))
        assert stats["unknown"] == 0
        assert stats["uploaded"] == 1
        assert len(fake_db.stories.calls) == 1


class Test404AndNoObjectId:
    def test_nonexistent_category_and_media_return_404_not_500(self, session: requests.Session):
        bad_cat = session.get(f"{BASE_URL}/api/category-media/not-real-category", timeout=30)
        assert bad_cat.status_code == 404
        assert "ObjectId" not in bad_cat.text

        bad_media = session.get(f"{BASE_URL}/api/media/not-real-story", timeout=30)
        assert bad_media.status_code == 404
        assert "ObjectId" not in bad_media.text

    def test_stories_api_has_no_mongodb_object_id_field(self, session: requests.Session):
        response = session.get(f"{BASE_URL}/api/stories?limit=3", timeout=30)
        assert response.status_code == 200
        for item in response.json():
            assert "_id" not in item
