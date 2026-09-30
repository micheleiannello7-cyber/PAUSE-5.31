"""Live checks for iter18 review (not part of pytest suite)."""
import os, time, requests, pathlib

def _load_env():
    if os.environ.get("EXPO_PUBLIC_BACKEND_URL"):
        return
    p = pathlib.Path(__file__).resolve().parents[2] / "frontend" / ".env"
    for line in p.read_text().splitlines():
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            os.environ["EXPO_PUBLIC_BACKEND_URL"] = line.split("=",1)[1].strip().strip('"')

_load_env()
BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
UID = "test-iter18"

def check(name, cond, extra=""):
    print(("PASS" if cond else "FAIL"), name, extra)
    return cond

def main():
    # Categories IT/EN
    r_it = requests.get(f"{BASE}/api/categories", params={"lang":"it"}, timeout=30)
    r_en = requests.get(f"{BASE}/api/categories", params={"lang":"en"}, timeout=30)
    check("GET /api/categories?lang=it 200", r_it.status_code == 200)
    check("GET /api/categories?lang=en 200", r_en.status_code == 200)
    cats_it = r_it.json()
    cats_en = r_en.json()
    check("categories it non-empty list", isinstance(cats_it, list) and len(cats_it) > 0)
    check("categories no _id leak (it)", all("_id" not in c for c in cats_it))
    check("categories no _id leak (en)", all("_id" not in c for c in cats_en))
    print("  categories count it:", len(cats_it), "en:", len(cats_en))

    # discover-next
    r = requests.get(f"{BASE}/api/discover-next", params={"user_id": UID}, timeout=60)
    check("GET /api/discover-next 200", r.status_code == 200, str(r.status_code))
    story = r.json()
    sid = story.get("id") or story.get("story_id")
    print("  story id:", sid, "title:", story.get("title"))
    check("discover-next has id", bool(sid))
    check("discover-next no _id", "_id" not in story)

    # user state
    r = requests.get(f"{BASE}/api/user/{UID}", timeout=30)
    check("GET /api/user/{uid} 200", r.status_code == 200)
    r = requests.get(f"{BASE}/api/user/{UID}/limit-check", timeout=30)
    check("GET /api/user/{uid}/limit-check 200", r.status_code == 200)
    print("  limit-check:", r.json())

    # complete
    r = requests.post(f"{BASE}/api/user/complete", json={"user_id": UID, "story_id": sid}, timeout=30)
    check("POST /api/user/complete 2xx", 200 <= r.status_code < 300, str(r.status_code))

    # session stories
    r = requests.get(f"{BASE}/api/user/{UID}/session-stories", timeout=30)
    check("GET /api/user/{uid}/session-stories 200", r.status_code == 200)
    print("  session-stories:", r.json() if r.status_code==200 else r.text[:120])

    # TTS: pick a story id from discover-next different from cached list
    # Warmup
    r = requests.post(f"{BASE}/api/tts/warmup/{sid}", timeout=90)
    check("POST /api/tts/warmup 2xx", 200 <= r.status_code < 300, f"{r.status_code} {r.text[:120]}")
    t0 = time.time()
    r = requests.get(f"{BASE}/api/tts/story/{sid}", timeout=120)
    dt1 = time.time() - t0
    check("GET /api/tts/story 200", r.status_code == 200, f"{r.status_code} ct={r.headers.get('content-type')} bytes={len(r.content)} t={dt1:.2f}s")
    body = r.content
    check("audio/mpeg content-type", "audio/mpeg" in (r.headers.get("content-type","")))
    check("mp3 body > 10KB", len(body) > 10 * 1024)
    check("mp3 magic (ID3 or 0xFFFB)", body[:3] == b"ID3" or body[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"))

    # Second request from cache -> should be quick
    t0 = time.time()
    r2 = requests.get(f"{BASE}/api/tts/story/{sid}", timeout=30)
    dt2 = time.time() - t0
    check("GET /api/tts/story cached 200", r2.status_code == 200, f"t={dt2:.2f}s")
    check("cache faster than first", dt2 < max(1.0, dt1))

    # Range request
    r3 = requests.get(f"{BASE}/api/tts/story/{sid}", headers={"Range": "bytes=0-1023"}, timeout=30)
    check("GET /api/tts/story Range 206", r3.status_code == 206, f"{r3.status_code} len={len(r3.content)} cr={r3.headers.get('content-range')}")

    # random preview
    r = requests.get(f"{BASE}/api/tts/random-preview", timeout=90)
    check("GET /api/tts/random-preview 200", r.status_code == 200, f"{r.status_code} ct={r.headers.get('content-type')} bytes={len(r.content)}")

    # media
    r = requests.get(f"{BASE}/api/media/sky-blue-sunset-orange", timeout=30)
    check("GET /api/media/sky-blue-sunset-orange 200", r.status_code == 200, f"{r.status_code} ct={r.headers.get('content-type')}")
    r = requests.get(f"{BASE}/api/media/why-we-yawn", timeout=30)
    check("GET /api/media/why-we-yawn 404 expected", r.status_code == 404, str(r.status_code))

if __name__ == "__main__":
    main()
