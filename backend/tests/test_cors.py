"""CORS regression tests — verify allow_credentials=False fix.

After changing CORSMiddleware(allow_credentials=False, allow_origins=["*"]), the
server must return `Access-Control-Allow-Origin: *` and MUST NOT return
`Access-Control-Allow-Credentials: true` (which is invalid combined with `*`
per the Fetch spec and blocks strict browsers like Brave or third-party
iframes).
"""
import os
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

# Origins we care about: the app.emergent.sh preview host, the current preview
# host (from env), and a random third party.
ORIGINS = [
    "https://app.emergent.sh",
    BASE_URL,
    "https://example.com",
]


def _hdrs_ci(resp):
    return {k.lower(): v for k, v in resp.headers.items()}


class TestCategoriesCORS:
    """GET /api/categories cross-origin — the exact request the mobile app makes."""

    def test_categories_get_cors_headers(self):
        for origin in ORIGINS:
            r = requests.get(f"{API}/categories", headers={"Origin": origin}, timeout=15)
            h = _hdrs_ci(r)
            assert r.status_code == 200, f"origin={origin} → {r.status_code}"
            aco = h.get("access-control-allow-origin")
            assert aco == "*", f"origin={origin} expected ACAO='*', got {aco!r}"
            acc = h.get("access-control-allow-credentials")
            assert acc is None or acc.lower() == "false", (
                f"origin={origin} INVALID combo: ACAO=* with ACAC={acc!r}"
            )

    def test_categories_preflight_options(self):
        # Mimic a browser CORS preflight from app.emergent.sh
        r = requests.options(
            f"{API}/categories",
            headers={
                "Origin": "https://app.emergent.sh",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=15,
        )
        h = _hdrs_ci(r)
        # Starlette CORS returns 200 for allowed preflight
        assert r.status_code in (200, 204), f"preflight → {r.status_code}"
        assert h.get("access-control-allow-origin") == "*"
        acc = h.get("access-control-allow-credentials")
        assert acc is None or acc.lower() == "false", f"INVALID: ACAC={acc!r}"
        methods = (h.get("access-control-allow-methods") or "").upper()
        assert "GET" in methods, f"GET missing from ACAM: {methods!r}"

    def test_body_shape_still_correct_under_cors(self):
        r = requests.get(
            f"{API}/categories",
            headers={"Origin": "https://app.emergent.sh"},
            timeout=15,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 13


class TestDiscoverNextCORS:
    def test_discover_next_cors(self):
        import uuid
        uid = f"TEST_{uuid.uuid4()}"
        r = requests.get(
            f"{API}/discover-next",
            params={"user_id": uid, "interests": "scienza"},
            headers={"Origin": "https://app.emergent.sh"},
            timeout=15,
        )
        h = _hdrs_ci(r)
        assert r.status_code == 200
        assert h.get("access-control-allow-origin") == "*"
        acc = h.get("access-control-allow-credentials")
        assert acc is None or acc.lower() == "false"
        body = r.json()
        assert body.get("category_id") == "scienza"
