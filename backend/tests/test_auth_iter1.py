"""PAUSE — iteration test: auth endpoints (Google via Emergent Auth, Apple, session/me/logout).

Requires seeded doc: user_test00000001 + session token test_session_token_pause_0001.
See /app/memory/test_credentials.md.
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
SEEDED_TOKEN = "test_session_token_pause_0001"
SEEDED_USER_ID = "user_test00000001"
SEEDED_EMAIL = "test.pause@example.com"


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ----------------------------- /api/auth/me -----------------------------
class TestAuthMe:
    def test_me_without_header_401(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_me_with_seeded_bearer_returns_user(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {SEEDED_TOKEN}"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["user_id"] == SEEDED_USER_ID
        assert data["email"] == SEEDED_EMAIL
        assert data.get("name") == "Test Pause"

    def test_me_with_bogus_bearer_401(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": "Bearer totally_bogus_token"})
        assert r.status_code == 401


# ----------------------------- /api/auth/session -----------------------------
class TestAuthSession:
    def test_session_with_bogus_id_returns_401(self, api):
        r = api.post(f"{BASE_URL}/api/auth/session", json={"session_id": "bogus"})
        assert r.status_code == 401

    def test_session_wrong_field_returns_422(self, api):
        r = api.post(f"{BASE_URL}/api/auth/session", json={"session_token": "bogus"})
        assert r.status_code == 422


# ----------------------------- /api/auth/apple -----------------------------
class TestAuthApple:
    def test_apple_with_bogus_token_returns_401(self, api):
        r = api.post(f"{BASE_URL}/api/auth/apple", json={"identity_token": "not.a.real.jwt"})
        assert r.status_code == 401

    def test_apple_missing_body_returns_422(self, api):
        r = api.post(f"{BASE_URL}/api/auth/apple", json={})
        assert r.status_code == 422


# ----------------------------- /api/auth/logout -----------------------------
def test_logout_invalidates_throwaway_session(api):
    """Create a throwaway session in Mongo directly, POST /logout, verify /me returns 401."""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")

    async def _run():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        throwaway = "TEST_throwaway_" + uuid.uuid4().hex
        try:
            now = datetime.now(timezone.utc)
            await db.user_sessions.insert_one({
                "session_token": throwaway,
                "user_id": SEEDED_USER_ID,
                "created_at": now,
                "expires_at": now + timedelta(days=1),
            })
            return throwaway
        finally:
            client.close()

    async def _cleanup(token):
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        try:
            await db.user_sessions.delete_one({"session_token": token})
        finally:
            client.close()

    throwaway = asyncio.run(_run())
    try:
        # Sanity: /me works with new token
        r = api.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {throwaway}"})
        assert r.status_code == 200, r.text

        # Logout
        r = api.post(f"{BASE_URL}/api/auth/logout", headers={"Authorization": f"Bearer {throwaway}"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}

        # /me now 401
        r = api.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {throwaway}"})
        assert r.status_code == 401

        # Ensure seeded token still works
        r = api.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {SEEDED_TOKEN}"})
        assert r.status_code == 200
    finally:
        asyncio.run(_cleanup(throwaway))


# ----------------------------- Mongo indexes -----------------------------
def test_indexes_exist():
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")

    async def _run():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        try:
            return await db.users.index_information(), await db.user_sessions.index_information()
        finally:
            client.close()

    users_idx, sessions_idx = asyncio.run(_run())
    # users.user_id unique
    assert any(
        v.get("key") == [("user_id", 1)] and v.get("unique")
        for v in users_idx.values()
    ), users_idx
    # users.email sparse unique
    assert any(
        v.get("key") == [("email", 1)] and v.get("unique") and v.get("sparse")
        for v in users_idx.values()
    ), users_idx
    # users.apple_sub sparse unique
    assert any(
        v.get("key") == [("apple_sub", 1)] and v.get("unique") and v.get("sparse")
        for v in users_idx.values()
    ), users_idx
    # sessions.session_token unique
    assert any(
        v.get("key") == [("session_token", 1)] and v.get("unique")
        for v in sessions_idx.values()
    ), sessions_idx
    # sessions.expires_at TTL
    assert any(
        v.get("key") == [("expires_at", 1)] and v.get("expireAfterSeconds") == 0
        for v in sessions_idx.values()
    ), sessions_idx


# ----------------------------- Regression -----------------------------
class TestRegression:
    def test_health_ok(self, api):
        r = api.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_categories_returns_12(self, api):
        r = api.get(f"{BASE_URL}/api/categories")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 12, f"expected 12 categories, got {len(data)}"

    def test_user_anonymous_uuid_still_works(self, api):
        anon_id = f"anon_{uuid.uuid4().hex[:8]}"
        r = api.get(f"{BASE_URL}/api/user/{anon_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == anon_id
