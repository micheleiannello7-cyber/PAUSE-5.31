# Iteration 2 — PAUSE: flusso autenticato (Bearer token) + regression API pubbliche.
# Copre: /api/auth/me con/senza token, bookmark del test user, core API, no-5xx sweep.
import os
import uuid

import pytest
import requests


def _base_url() -> str:
    url = os.environ.get("EXPO_BACKEND_URL") or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    if not url:
        env_path = "/app/frontend/.env"
        if os.path.exists(env_path):
            for line in open(env_path):
                if line.startswith("EXPO_PUBLIC_BACKEND_URL=") or line.startswith("EXPO_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip().strip('"')
                    break
    assert url, "EXPO_BACKEND_URL / EXPO_PUBLIC_BACKEND_URL non configurato"
    return url.rstrip("/")


BASE_URL = _base_url()
TOKEN = "testtoken_8ad64e048af641939d01b2e1e73731c6"
TEST_USER_ID = "user_testpause001"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------------------------------------------------------------------------
# Auth (Bearer session token)
# ---------------------------------------------------------------------------
class TestAuth:
    def test_auth_me_with_bearer_returns_test_user(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/auth/me", headers=AUTH)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["user_id"] == TEST_USER_ID
        assert data["email"] == "pause.test@example.com"
        assert data["name"] == "Pause Tester"
        assert "_id" not in data

    def test_auth_me_without_token_is_401(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_auth_me_with_invalid_token_is_401(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/auth/me",
                           headers={"Authorization": "Bearer TEST_invalid_token_xyz"})
        assert r.status_code == 401

    def test_auth_session_invalid_session_id_is_401(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/session", json={"session_id": "TEST_bogus"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Core public API (seed atteso: 12 categorie, 441 storie in DB)
# ---------------------------------------------------------------------------
class TestCoreApi:
    def test_health(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["db"] is True

    def test_categories_returns_12(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/categories")
        assert r.status_code == 200
        cats = r.json()
        assert len(cats) == 12
        for c in cats:
            assert c["id"] and c["name"]

    def test_stories_seed_441_in_db(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/content/report")
        assert r.status_code == 200
        assert r.json()["stories"] == 441

    def test_stories_list_visible_for_anonymous(self, api_client):
        # Early-access filter nasconde le storie nella finestra 7 giorni ai free:
        # visibili < 441 ma comunque un catalogo ampio, senza errori.
        r = api_client.get(f"{BASE_URL}/api/stories", params={"limit": 500})
        assert r.status_code == 200
        stories = r.json()
        assert 400 <= len(stories) <= 441
        s = stories[0]
        for key in ("id", "title", "category_id", "reading_time_min"):
            assert key in s

    def test_story_detail_has_chapters(self, api_client):
        stories = api_client.get(f"{BASE_URL}/api/stories", params={"limit": 5}).json()
        sid = stories[0]["id"]
        r = api_client.get(f"{BASE_URL}/api/stories/{sid}")
        assert r.status_code == 200
        story = r.json()
        assert story["id"] == sid
        assert isinstance(story["chapters"], list) and len(story["chapters"]) >= 1

    def test_story_detail_unknown_id_404(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/stories/TEST_nonexistent_story_id")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Flusso autenticato a livello dati: stato utente + bookmark persistito
# ---------------------------------------------------------------------------
class TestAuthenticatedUserFlows:
    def test_user_state_for_test_user(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/user/{TEST_USER_ID}")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == TEST_USER_ID
        assert "_id" not in data

    def test_bookmark_toggle_persists_and_reverts(self, api_client):
        stories = api_client.get(f"{BASE_URL}/api/stories", params={"limit": 3}).json()
        sid = stories[-1]["id"]

        before = api_client.get(f"{BASE_URL}/api/user/{TEST_USER_ID}/bookmarks").json()
        before_ids = [b["id"] for b in before]

        # Salva (bookmark on)
        r = api_client.post(f"{BASE_URL}/api/user/bookmark",
                            json={"user_id": TEST_USER_ID, "story_id": sid}, headers=AUTH)
        assert r.status_code == 200, r.text
        assert sid in r.json().get("bookmarked_story_ids", [])

        # GET verifica persistenza
        after = api_client.get(f"{BASE_URL}/api/user/{TEST_USER_ID}/bookmarks").json()
        after_ids = [b["id"] for b in after]
        assert sid in after_ids

        # Cleanup: toggle off per ripristinare lo stato iniziale
        r2 = api_client.post(f"{BASE_URL}/api/user/bookmark",
                             json={"user_id": TEST_USER_ID, "story_id": sid}, headers=AUTH)
        assert r2.status_code == 200
        final = api_client.get(f"{BASE_URL}/api/user/{TEST_USER_ID}/bookmarks").json()
        final_ids = [b["id"] for b in final]
        if sid not in before_ids:
            assert sid not in final_ids

    def test_discover_batch_for_test_user(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/discover-batch",
                           params={"user_id": TEST_USER_ID, "count": 5}, headers=AUTH)
        assert r.status_code == 200
        deck = r.json()
        assert 1 <= len(deck) <= 5
        ids = [s["id"] for s in deck]
        assert len(ids) == len(set(ids)), "deck con duplicati"


# ---------------------------------------------------------------------------
# Regression sweep: nessun 5xx sulle API pubbliche
# ---------------------------------------------------------------------------
class TestNoServerErrors:
    def test_public_endpoints_no_5xx(self, api_client):
        sid = api_client.get(f"{BASE_URL}/api/stories", params={"limit": 1}).json()[0]["id"]
        guest = f"TEST_sweep_{uuid.uuid4().hex[:8]}"
        endpoints = [
            ("GET", "/api/health", {}),
            ("GET", "/api/", {}),
            ("GET", "/api/categories", {}),
            ("GET", "/api/categories", {"lang": "en"}),
            ("GET", "/api/stories", {"limit": 10}),
            ("GET", f"/api/stories/{sid}", {}),
            ("GET", f"/api/stories/{sid}/related", {}),
            ("GET", f"/api/stories/{sid}/next", {}),
            ("GET", "/api/discover-batch", {"user_id": guest, "count": 3}),
            ("GET", "/api/playlist", {"user_id": guest}),
            ("GET", f"/api/user/{guest}", {}),
            ("GET", f"/api/user/{guest}/bookmarks", {}),
            ("GET", f"/api/user/{guest}/liked", {}),
            ("GET", f"/api/user/{guest}/stats", {}),
            ("GET", f"/api/user/{guest}/limit-check", {}),
            ("GET", f"/api/user/{guest}/session-stories", {}),
            ("GET", "/api/content/report", {}),
            ("GET", "/api/category-clips", {}),
            ("GET", "/api/category-media/scienza", {}),
            ("GET", "/api/content-mode-media/storie", {}),
        ]
        failures = []
        for method, path, params in endpoints:
            r = api_client.request(method, f"{BASE_URL}{path}", params=params, timeout=30)
            if r.status_code >= 500:
                failures.append(f"{method} {path} -> {r.status_code}: {r.text[:200]}")
        assert not failures, "5xx rilevati: " + "; ".join(failures)
