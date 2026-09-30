"""
PAUSE — builder condiviso per i pacchetti di storie scritte a mano.
Stessa struttura di seed_data.STORIES (id, category_*, title, highlight_words,
hook, hero_image, reading_time_min, deep_dive_time_min, chapters[], summary).
Le icone dei capitoli vengono assegnate ciclicamente da un pool per categoria,
i glow_color ciclano come nel seed originale.
"""

GLOWS = ["#00E5FF", "#B200FF", "#FF6D00", "#FF006A", "#00E676"]

# (name, icon, color) — identico a CATEGORIES in seed_data.py
CAT_META = {
    "scienza":     ("Scienza",           "planet-outline",        "#00D2FF"),
    "spazio":      ("Spazio",            "rocket-outline",        "#B200FF"),
    "tecnologia":  ("Tecnologia",        "hardware-chip-outline", "#00E676"),
    "natura":      ("Natura",            "leaf-outline",          "#00E676"),
    "animali":     ("Animali",           "paw-outline",           "#FF9100"),
    "storia":      ("Storia",            "book-outline",          "#FF6D00"),
    "psicologia":  ("Psicologia",        "sparkles-outline",      "#FF006A"),
    "corpo-umano": ("Corpo umano",       "heart-outline",         "#FF006A"),
    "cultura":     ("Cultura",           "globe-outline",         "#00D2FF"),
    "curiosita":   ("Curiosità",         "help-circle-outline",   "#B200FF"),
    "economia":    ("Economia & Denaro", "cash-outline",          "#FFD600"),
    "arte":        ("Arte & Design",     "color-palette-outline", "#FF4FD8"),
    "geografia":   ("Geografia & Viaggi", "map-outline",          "#3FA9FF"),
}

# Pool di icone Ionicons coerenti col tema di ogni categoria.
ICON_POOL = {
    "scienza":     ["flask", "planet", "nuclear", "magnet", "bulb", "thermometer"],
    "spazio":      ["rocket", "planet", "telescope", "moon", "star", "earth"],
    "tecnologia":  ["hardware-chip", "wifi", "code-slash", "lock-closed", "key", "layers"],
    "natura":      ["leaf", "water", "flower", "sunny", "earth", "cloud"],
    "animali":     ["paw", "fish", "bug", "eye", "leaf", "water"],
    "storia":      ["book", "time", "hourglass", "people", "map", "trophy"],
    "psicologia":  ["sparkles", "bulb", "people", "heart", "eye", "happy"],
    "corpo-umano": ["heart", "body", "pulse", "medkit", "eye", "flash"],
    "cultura":     ["globe", "people", "language", "musical-notes", "book", "earth"],
    "curiosita":   ["help-circle", "bulb", "sparkles", "eye", "flash", "star"],
    "economia":    ["cash", "trending-up", "wallet", "pricetag", "card", "stats-chart"],
    "arte":        ["color-palette", "brush", "image", "eye", "construct", "musical-notes"],
    "geografia":   ["map", "earth", "airplane", "compass", "boat", "location"],
}


def en_entry(title, highlights, hook, summary, chapters):
    """Costruisce il blocco translations['en'] con la stessa forma del doc IT."""
    return {
        "title": title,
        "highlight_words": highlights,
        "hook": hook,
        "summary": summary,
        "chapters": [{"title": ct, "body": cb} for (ct, cb) in chapters],
    }


def mk(cat, sid, title, highlights, hook, summary, hero, chapters):
    name, icon, color = CAT_META[cat]
    pool = ICON_POOL[cat]
    built = []
    for i, (ct, cb) in enumerate(chapters):
        built.append({
            "number": i + 1,
            "title": ct,
            "body": cb,
            "icon": pool[i % len(pool)],
            "glow_color": GLOWS[i % len(GLOWS)],
        })
    return {
        "id": sid,
        "category_id": cat,
        "category_name": name,
        "category_icon": icon,
        "category_color": color,
        "title": title,
        "highlight_words": highlights,
        "hook": hook,
        "hero_image": hero,
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": built,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Lezioni — stessa forma delle storie + kind="lesson" e objective (cosa
# imparerai). I capitoli sono i passi della lezione.
# ---------------------------------------------------------------------------

def mk_lesson(cat, sid, title, highlights, hook, objective, summary, chapters, en=None, hero=None):
    doc = mk(cat, sid, title, highlights, hook, summary, hero, chapters)
    doc["kind"] = "lesson"
    doc["objective"] = objective
    doc["hero_image"] = hero or ""
    doc["reading_time_min"] = 3
    doc["deep_dive_time_min"] = 4
    if en:
        tr = en_entry(en["title"], en["highlight_words"], en["hook"], en["summary"], en["chapters"])
        tr["objective"] = en["objective"]
        doc["translations"] = {"en": tr}
    return doc
