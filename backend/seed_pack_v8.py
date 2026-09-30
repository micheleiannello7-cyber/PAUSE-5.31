"""PAUSE v8 — 5 curiosità + 5 mini lezioni in più per ogni categoria (13 × 10 = 130).
Argomenti curati in v8_topics.py, testi in v8_content.json (IT + EN, 6 capitoli ciascuno,
scritti con GPT-5.4 da generate_v8.py). Stessa gerarchia del resto del catalogo:
kind, objective (lezioni), translations.en, chapters_v6."""
import json
from pathlib import Path

from story_builder import mk, mk_lesson, en_entry, ICON_POOL

_JSON = Path(__file__).parent / "v8_content.json"
_CONTENT = json.loads(_JSON.read_text()) if _JSON.exists() else {}

# Copertina di ripiego per categoria (stesse foto curate del seed base), usata
# finché generate_images.py non produce la copertina AI del contenuto.
_U = "https://images.unsplash.com/{}?w=1200&q=80&auto=format&fit=crop"
FALLBACK_HERO = {
    "scienza": _U.format("photo-1470252649378-9c29740c9fa8"),
    "spazio": _U.format("photo-1543722530-d2c3201371e7"),
    "tecnologia": _U.format("photo-1587202372775-e229f172b9d7"),
    "natura": _U.format("photo-1531366936337-7c912a4589a7"),
    "animali": _U.format("photo-1550439062-609e1531270e"),
    "storia": _U.format("photo-1552832230-c0197dd311b5"),
    "psicologia": _U.format("photo-1620641788421-7a1c342ea42e"),
    "corpo-umano": _U.format("photo-1552057426-c4dbcae005b9"),
    "cultura": _U.format("photo-1610889556528-9a770e32642f"),
    "curiosita": _U.format("photo-1514888286974-6c03e2ca1dba"),
    "economia": _U.format("photo-1611974789855-9c2a0a7236a3"),
    "arte": _U.format("photo-1541961017774-22349e4a1262"),
    "geografia": _U.format("photo-1476514525535-07fb3b4ae5f1"),
}

def build_pack(content: dict):
    """Costruisce (STORIES, LESSONS) da un JSON {id: {it, en, kind, category_id, icons}}.
    Usato anche da seed_pack_v9.py (stessa gerarchia)."""
    stories, lessons = [], []
    for _sid, _e in content.items():
        _it, _en, _cat = _e["it"], _e["en"], _e["category_id"]
        _chapters = [(c["title"], c["body"]) for c in _it["chapters"]]
        if _e["kind"] == "lesson":
            _doc = mk_lesson(
                _cat, _sid, _it["title"], _it.get("highlight_words", [])[:3], _it["hook"],
                _it.get("objective", ""), _it["summary"], _chapters,
            )
        else:
            _doc = mk(_cat, _sid, _it["title"], _it.get("highlight_words", [])[:3], _it["hook"], _it["summary"],
                      FALLBACK_HERO[_cat], _chapters)
        # Icone scelte dal modello quando valide, altrimenti il pool di categoria.
        _pool = ICON_POOL[_cat]
        for _i, _ch in enumerate(_doc["chapters"]):
            _icon = (_e.get("icons") or [None] * 6)[_i] if _i < len(_e.get("icons") or []) else None
            _ch["icon"] = _icon or _pool[_i % len(_pool)]
        _tr = en_entry(_en["title"], _en.get("highlight_words", [])[:3], _en["hook"], _en["summary"],
                       [(c["title"], c["body"]) for c in _en["chapters"]])
        if _e["kind"] == "lesson":
            _tr["objective"] = _en.get("objective", "")
        _doc["translations"] = {"en": _tr}
        _doc["chapters_v6"] = True
        _doc["ai_generated"] = True
        (lessons if _e["kind"] == "lesson" else stories).append(_doc)
    return stories, lessons


STORIES, LESSONS = build_pack(_CONTENT)
