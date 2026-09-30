"""Iteration 25: Curiosita retirement migration + category artwork/API regression."""

# Module coverage: taxonomy migration, legacy interests normalization, media integrity, and backup consistency.
import os
import uuid
import sys
import asyncio
from copy import deepcopy
from pathlib import Path

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from category_taxonomy import MIGRATION_ID, REASSIGNMENTS, apply_seed_taxonomy, migrate_curiosita
from retired_stories import RETIRED_IDS

# Legacy ids still in the catalogue (4 were retired as duplicates/weak content, see retired_stories.py).
ACTIVE_REASSIGNED = {k: v for k, v in REASSIGNMENTS.items() if k not in RETIRED_IDS}


_BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"
if _BACKEND_ENV.exists():
    for raw in _BACKEND_ENV.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in ("MONGO_URL", "DB_NAME") and not os.environ.get(key):
            os.environ[key] = value

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not configured", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
if not MONGO_URL or not DB_NAME:
    pytest.skip("MONGO_URL/DB_NAME not configured", allow_module_level=True)

DESTINATIONS = tuple(dict.fromkeys(REASSIGNMENTS.values()))
EXPECTED_CATEGORY_IDS = {
    "scienza", "spazio", "tecnologia", "natura", "animali", "storia",
    "psicologia", "corpo-umano", "cultura", "economia", "arte", "geografia",
}


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


def _strip_category_metadata(doc: dict) -> dict:
    clean = deepcopy(doc)
    for key in ("category_id", "category_name", "category_icon", "category_color"):
        clean.pop(key, None)
    for tr in (clean.get("translations") or {}).values():
        if isinstance(tr, dict):
            for key in ("category_id", "category_name", "category_icon", "category_color"):
                tr.pop(key, None)
    return clean


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


class TestCuriositaPublicApi:
    def test_categories_exactly_12_no_curiosita_and_animali_path(self, session: requests.Session):
        response = session.get(f"{BASE_URL}/api/categories?lang=it", timeout=30)
        assert response.status_code == 200
        categories = response.json()
        ids = {c["id"] for c in categories}
        assert ids == EXPECTED_CATEGORY_IDS
        assert len(categories) == 12
        animali = next(c for c in categories if c["id"] == "animali")
        assert animali["illustration_generated"].endswith("animali-a5c17a2ed660.webp")

    def test_category_media_13_assets_webp_480(self, session: requests.Session):
        for category_id in sorted(EXPECTED_CATEGORY_IDS | {"all"}):
            response = session.get(f"{BASE_URL}/api/category-media/{category_id}?v=recognizable-2026-09-v2", timeout=30)
            assert response.status_code == 200
            assert response.headers.get("content-type", "").startswith("image/webp")
            assert _parse_webp_size(response.content) == (480, 480)

    def test_legacy_curiosita_filter_returns_old_ids_with_new_metadata(self, session: requests.Session):
        user_id = f"TEST_iter25_{uuid.uuid4()}"
        premium = session.post(
            f"{BASE_URL}/api/user/premium",
            json={"user_id": user_id, "active": True},
            timeout=30,
        )
        assert premium.status_code == 200

        response = session.get(f"{BASE_URL}/api/stories?category_id=curiosita&limit=100&user_id={user_id}", timeout=30)
        assert response.status_code == 200
        stories = response.json()
        ids = {s["id"] for s in stories}
        assert ids == set(ACTIVE_REASSIGNED.keys())
        assert all(s["category_id"] != "curiosita" for s in stories)

    def test_interests_curiosita_normalized_and_discover_works(self, session: requests.Session):
        user_id = f"TEST_iter25_{uuid.uuid4()}"
        post = session.post(
            f"{BASE_URL}/api/user/interests",
            json={"user_id": user_id, "interests": ["curiosita"]},
            timeout=30,
        )
        assert post.status_code == 200
        state = post.json()
        assert "curiosita" not in state["interests"]
        assert set(state["interests"]) == set(DESTINATIONS)

        nxt = session.get(f"{BASE_URL}/api/discover-next?user_id={user_id}&interests=curiosita", timeout=30)
        assert nxt.status_code == 200
        assert nxt.json()["category_id"] in set(DESTINATIONS)

    def test_moved_story_detail_related_bookmark_and_stats(self, session: requests.Session):
        user_id = f"TEST_iter25_{uuid.uuid4()}"
        story_id = "cur-why-mirrors-reverse"

        detail = session.get(f"{BASE_URL}/api/stories/{story_id}", timeout=30)
        assert detail.status_code == 200
        story = detail.json()
        assert story["category_id"] == "scienza"

        related = session.get(f"{BASE_URL}/api/stories/{story_id}/related?limit=3", timeout=30)
        assert related.status_code == 200

        toggle = session.post(
            f"{BASE_URL}/api/user/bookmark",
            json={"user_id": user_id, "story_id": story_id},
            timeout=30,
        )
        assert toggle.status_code == 200

        bookmarks = session.get(f"{BASE_URL}/api/user/{user_id}/bookmarks", timeout=30)
        assert bookmarks.status_code == 200
        assert any(item["id"] == story_id for item in bookmarks.json())

        stats = session.get(f"{BASE_URL}/api/user/{user_id}/stats", timeout=30)
        assert stats.status_code == 200
        body = stats.json()
        assert "stories" in body and "categories" in body


class TestCuriositaBackupAndDataIntegrity:
    def test_total_docs_and_reassignment_distribution(self, mongo_db):
        assert mongo_db.categories.count_documents({}) == 12
        assert mongo_db.categories.count_documents({"id": "curiosita"}) == 0
        assert mongo_db.stories.count_documents({}) == 419  # 437 - 18 retired

        moved_docs = list(mongo_db.stories.find({"id": {"$in": list(ACTIVE_REASSIGNED.keys())}}, {"_id": 0}))
        assert len(moved_docs) == 24
        by_kind = {"story": 0, "lesson": 0}
        for doc in moved_docs:
            by_kind[doc.get("kind", "story")] = by_kind.get(doc.get("kind", "story"), 0) + 1
            assert doc["category_id"] == REASSIGNMENTS[doc["id"]]
        assert by_kind["story"] == 14
        assert by_kind["lesson"] == 10

    def test_taxonomy_backup_story_docs_preserve_core_fields(self, mongo_db):
        backups = list(mongo_db.taxonomy_backups.find({"migration": MIGRATION_ID, "kind": "story"}, {"_id": 0}))
        assert len(backups) == 28
        for row in backups:
            before = row["document"]
            after = mongo_db.stories.find_one({"id": row["entity_id"]}, {"_id": 0})
            assert after is not None
            assert _strip_category_metadata(after) == _strip_category_metadata(before)

    def test_user_state_protected_fields_untouched_for_backed_up_users(self, mongo_db):
        backups = list(mongo_db.taxonomy_backups.find({"migration": MIGRATION_ID, "kind": "user_state"}, {"_id": 0}))
        protected = [
            "bookmarked_story_ids", "completed_story_ids", "liked_story_ids", "session_start",
            "session_count", "session_seconds", "session_story_ids", "total_minutes", "listen_seconds",
        ]
        for row in backups:
            before = row["document"]
            after = mongo_db.user_state.find_one({"user_id": row["entity_id"]}, {"_id": 0})
            if not after:
                continue
            for key in protected:
                assert after.get(key) == before.get(key)
            assert "curiosita" not in (after.get("interests") or [])
            assert "curiosita" not in (after.get("unlocked_categories") or [])

    def test_category_backup_exists_and_curiosita_removed(self, mongo_db):
        backup = mongo_db.taxonomy_backups.find_one(
            {"migration": MIGRATION_ID, "kind": "category", "entity_id": "curiosita"},
            {"_id": 0},
        )
        assert backup is not None
        assert mongo_db.categories.find_one({"id": "curiosita"}) is None


class TestMigrationIsolatedFixture:
    def test_unknown_story_fails_closed(self):
        async def _run():
            db_name = f"test_taxonomy_iter25_{uuid.uuid4().hex[:8]}"
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[db_name]
            try:
                categories = [{"id": cid, "name": cid, "icon": "i", "color": "#000"} for cid in EXPECTED_CATEGORY_IDS]
                await db.stories.insert_one({
                    "id": "TEST_unknown_legacy", "category_id": "curiosita", "category_name": "Curiosità", "kind": "story",
                    "title": "t", "hook": "h", "summary": "s", "chapters": [],
                })
                with pytest.raises(ValueError, match="Migration needs editorial decisions"):
                    await migrate_curiosita(db, categories)
                assert await db.stories.count_documents({"category_id": "curiosita"}) == 1
            finally:
                await client.drop_database(db_name)
                client.close()
        asyncio.run(_run())

    def test_idempotent_double_call_and_user_interest_expansion(self):
        async def _run():
            db_name = f"test_taxonomy_iter25_{uuid.uuid4().hex[:8]}"
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[db_name]
            try:
                categories = [{"id": cid, "name": cid, "icon": "i", "color": "#111"} for cid in EXPECTED_CATEGORY_IDS]
                await db.categories.insert_many(categories + [{"id": "curiosita", "name": "Curiosità", "icon": "q", "color": "#999"}])
                await db.stories.insert_one({
                    "id": "cur-why-yawn-contagious-fun",
                    "category_id": "curiosita",
                    "category_name": "Curiosità",
                    "category_icon": "spark",
                    "category_color": "#999",
                    "kind": "story",
                    "title": "Cotton candy",
                    "hook": "h",
                    "summary": "s",
                    "chapters": [{"number": 1, "title": "t", "body": "b", "icon": "i", "glow_color": "#fff"}],
                    "hero_image": "cover",
                    "translations": {"it": {"title": "it"}, "en": {"title": "en"}},
                })
                await db.user_state.insert_one({
                    "user_id": "u1",
                    "interests": ["curiosita", "scienza"],
                    "unlocked_categories": ["curiosita"],
                    "bookmarked_story_ids": ["x"],
                    "completed_story_ids": ["y"],
                    "liked_story_ids": ["z"],
                    "session_count": 3,
                    "total_minutes": 21,
                })

                first = await migrate_curiosita(db, categories)
                second = await migrate_curiosita(db, categories)
                assert first == 1
                assert second == 0

                migrated = await db.stories.find_one({"id": "cur-why-yawn-contagious-fun"}, {"_id": 0})
                assert migrated["category_id"] == "scienza"

                user = await db.user_state.find_one({"user_id": "u1"}, {"_id": 0})
                assert "curiosita" not in user["interests"]
                assert "curiosita" not in user["unlocked_categories"]
                assert user["bookmarked_story_ids"] == ["x"]
                assert user["completed_story_ids"] == ["y"]
                assert user["liked_story_ids"] == ["z"]
            finally:
                await client.drop_database(db_name)
                client.close()
        asyncio.run(_run())

    def test_apply_seed_taxonomy_removes_curiosita_and_reclassifies(self):
        categories = [
            {"id": "curiosita", "name": "Curiosità", "icon": "spark", "color": "#000"},
            {"id": "scienza", "name": "Scienza", "icon": "flask", "color": "#0af"},
        ]
        stories = [{
            "id": "cur-why-yawn-contagious-fun",
            "category_id": "curiosita",
            "category_name": "Curiosità",
            "category_icon": "spark",
            "category_color": "#000",
            "title": "Cotton candy",
            "hook": "h",
            "summary": "s",
            "chapters": [],
        }]
        apply_seed_taxonomy(categories, stories)
        assert [c["id"] for c in categories] == ["scienza"]
        assert stories[0]["category_id"] == "scienza"
