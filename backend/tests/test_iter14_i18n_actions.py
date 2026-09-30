"""
Iteration 14 backend contract tests:
- health, content/report (en_done=130, en_missing=[])
- story EN/IT content for `quantum-basics`
- discover-next EN preview
- bookmark + like flows and lang=en listings
- categories lang=en names
"""
import os
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"]
BASE_URL = BASE_URL.rstrip("/")

USER_ID = "TEST_iter14_user"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------------- health / content report ----------------
def test_health(api):
    r = api.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["db"] is True


def test_content_report_en_complete(api):
    r = api.get(f"{BASE_URL}/api/content/report")
    assert r.status_code == 200
    j = r.json()
    assert j["stories"] == 222, f"expected 222 stories, got {j['stories']}"
    assert j["en_done"] == 156, f"en_done={j['en_done']}"
    # v4 pack (66 docs) is Italian-only for now: EN translations still pending
    assert j["en_missing"] and all(str(i).startswith("v4-") for i in j["en_missing"]), \
        f"en_missing should only contain v4 ids: {j['en_missing'][:5]}"


# ---------------- stories: quantum-basics EN + IT ----------------
ITALIAN_STOPWORDS = {"che", "della", "quando", "perché", "gli", "delle", "sono", "come", "questo", "questa"}


def _english_text_check(text: str) -> bool:
    """Naive heuristic: text likely english if it contains no strong italian stopwords among top hits."""
    if not text:
        return False
    lower = " " + text.lower() + " "
    hits = sum(1 for w in ITALIAN_STOPWORDS if f" {w} " in lower)
    return hits <= 1  # allow at most 1 accidental hit


def test_story_quantum_basics_en(api):
    r = api.get(f"{BASE_URL}/api/stories/quantum-basics", params={"lang": "en"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["id"] == "quantum-basics"
    assert d["category_name"] == "Science", d["category_name"]
    assert _english_text_check(d["title"]), f"non-english title: {d['title']}"
    assert _english_text_check(d["hook"]), f"non-english hook: {d['hook']}"
    assert _english_text_check(d["summary"]), f"non-english summary: {d['summary'][:120]}"
    assert d["chapters"] and len(d["chapters"]) >= 5
    for ch in d["chapters"]:
        assert _english_text_check(ch["title"]), f"non-english chapter title: {ch['title']}"
        assert _english_text_check(ch["body"][:400]), f"non-english chapter body: {ch['body'][:120]}"


def test_story_quantum_basics_it(api):
    r = api.get(f"{BASE_URL}/api/stories/quantum-basics", params={"lang": "it"})
    assert r.status_code == 200
    d = r.json()
    assert d["id"] == "quantum-basics"
    # italian source: category_name should not be "Science"
    assert d["category_name"] != "Science"
    assert d["chapters"] and len(d["chapters"]) >= 5


# ---------------- discover-next EN ----------------
def test_discover_next_en(api):
    r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": "TEST_discover_en", "lang": "en"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("title"), d
    assert d.get("hook"), d
    assert _english_text_check(d["hook"]), f"non-english discover preview: {d['hook'][:150]}"


# ---------------- categories EN ----------------
def test_categories_en_names(api):
    r = api.get(f"{BASE_URL}/api/categories", params={"lang": "en"})
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) >= 13
    by_id = {c["id"]: c for c in cats}
    expected = {
        "scienza": "Science",
        "spazio": "Space",
        "tecnologia": "Technology",
        "corpo-umano": "Human Body",
        "psicologia": "Psychology",
    }
    for cid, en_name in expected.items():
        assert by_id[cid]["name"] == en_name, f"{cid}: got {by_id[cid]['name']}"


# ---------------- bookmark + liked flow ----------------
def test_bookmark_then_get_en(api):
    payload = {"user_id": USER_ID, "story_id": "quantum-basics"}
    r = api.post(f"{BASE_URL}/api/user/bookmark", json=payload)
    assert r.status_code == 200
    state = r.json()
    assert "quantum-basics" in state["bookmarked_story_ids"]

    r = api.get(f"{BASE_URL}/api/user/{USER_ID}/bookmarks", params={"lang": "en"})
    assert r.status_code == 200
    items = r.json()
    assert any(it["id"] == "quantum-basics" for it in items)
    q = next(it for it in items if it["id"] == "quantum-basics")
    assert q["category_name"] == "Science", q["category_name"]
    assert _english_text_check(q["title"]), q["title"]


def test_like_then_get_en(api):
    payload = {"user_id": USER_ID, "story_id": "quantum-basics"}
    r = api.post(f"{BASE_URL}/api/user/like", json=payload)
    assert r.status_code == 200
    state = r.json()
    assert "quantum-basics" in state["liked_story_ids"]

    r = api.get(f"{BASE_URL}/api/user/{USER_ID}/liked", params={"lang": "en"})
    assert r.status_code == 200
    items = r.json()
    assert any(it["id"] == "quantum-basics" for it in items)
    q = next(it for it in items if it["id"] == "quantum-basics")
    assert q["category_name"] == "Science"
    assert _english_text_check(q["title"])


# ---------------- cleanup: unbookmark + unlike ----------------
def test_cleanup(api):
    # toggle off
    api.post(f"{BASE_URL}/api/user/bookmark", json={"user_id": USER_ID, "story_id": "quantum-basics"})
    api.post(f"{BASE_URL}/api/user/like", json={"user_id": USER_ID, "story_id": "quantum-basics"})
    r = api.get(f"{BASE_URL}/api/user/{USER_ID}")
    st = r.json()
    assert "quantum-basics" not in st["bookmarked_story_ids"]
    assert "quantum-basics" not in st["liked_story_ids"]
