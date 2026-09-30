"""Progress statistics, badges and monthly recap for PAUSE.

Everything is derived from the user_state document:
- completed_story_ids            → lifetime stories (legacy, undated)
- completions [{story_id, category_id, at, minutes}] → dated history
- total_minutes                  → reading minutes
- listen_seconds / listen_by_month {"YYYY-MM": s} → listening time
- active_days ["YYYY-MM-DD"]     → streak history
- streak_days / best_streak
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

# (id, icon, metric, target, {lang: (title, description)})
BADGES = [
    ("first_story", "sparkles", "stories", 1, {
        "it": ("Prima scoperta", "La tua prima storia completata"),
        "en": ("First discovery", "Your first completed story")}),
    ("stories_10", "book", "stories", 10, {
        "it": ("Curioso", "10 storie completate"),
        "en": ("Curious", "10 stories completed")}),
    ("stories_50", "compass", "stories", 50, {
        "it": ("Esploratore", "50 storie completate"),
        "en": ("Explorer", "50 stories completed")}),
    ("stories_100", "trophy", "stories", 100, {
        "it": ("Centurione", "100 storie completate"),
        "en": ("Centurion", "100 stories completed")}),
    ("cats_5", "color-palette", "categories", 5, {
        "it": ("Onnivoro", "5 categorie esplorate"),
        "en": ("Omnivore", "5 categories explored")}),
    ("cats_10", "library", "categories", 10, {
        "it": ("Enciclopedico", "10 categorie esplorate"),
        "en": ("Encyclopedic", "10 categories explored")}),
    ("minutes_100", "hourglass", "minutes", 100, {
        "it": ("100 minuti", "100 minuti di lettura"),
        "en": ("100 minutes", "100 minutes of reading")}),
    ("minutes_500", "timer", "minutes", 500, {
        "it": ("Maratoneta", "500 minuti di lettura"),
        "en": ("Marathoner", "500 minutes of reading")}),
    ("minutes_1000", "medal", "minutes", 1000, {
        "it": ("Mille minuti", "1000 minuti di lettura"),
        "en": ("Thousand minutes", "1000 minutes of reading")}),
    ("listen_60", "headset", "listen_minutes", 60, {
        "it": ("Orecchio fino", "1 ora di ascolto"),
        "en": ("Keen ear", "1 hour of listening")}),
    ("listen_300", "musical-notes", "listen_minutes", 300, {
        "it": ("Audiofilo", "5 ore di ascolto"),
        "en": ("Audiophile", "5 hours of listening")}),
    ("streak_3", "flame", "best_streak", 3, {
        "it": ("Costante", "3 giorni di fila"),
        "en": ("Steady", "3-day streak")}),
    ("streak_7", "flame", "best_streak", 7, {
        "it": ("Settimana perfetta", "7 giorni di fila"),
        "en": ("Perfect week", "7-day streak")}),
    ("streak_30", "flame", "best_streak", 30, {
        "it": ("Un mese di fila", "30 giorni di fila"),
        "en": ("A month straight", "30-day streak")}),
]


def month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def build_stats(state: dict, categories: List[dict], story_cats: Dict[str, str],
                cat_totals: Dict[str, int], lang: str = "it") -> dict:
    now = datetime.now(timezone.utc)
    completed = list(state.get("completed_story_ids", []))
    # Re-reads live in the log for the history screen only.
    completions = [c for c in state.get("completions", []) if not c.get("reread")]
    total_minutes = int(state.get("total_minutes", 0))
    listen_seconds = int(state.get("listen_seconds", 0))
    listen_by_month: Dict[str, int] = dict(state.get("listen_by_month", {}) or {})
    active_days = set(state.get("active_days", []) or [])
    if state.get("last_active_date"):
        active_days.add(state["last_active_date"])
    streak = int(state.get("streak_days", 0))
    best_streak = max(int(state.get("best_streak", 0)), streak)

    # Categories explored (legacy ids resolved through story_cats).
    read_per_cat: Dict[str, int] = {}
    for sid in completed:
        cid = story_cats.get(sid)
        if cid:
            read_per_cat[cid] = read_per_cat.get(cid, 0) + 1
    cat_rows = []
    for c in categories:
        name = c.get("name_en") if lang == "en" and c.get("name_en") else c["name"]
        read = read_per_cat.get(c["id"], 0)
        total = cat_totals.get(c["id"], 0)
        cat_rows.append({
            "id": c["id"], "name": name, "icon": c["icon"], "color": c["color"],
            "read": read, "total": total,
            "ratio": round(read / total, 3) if total else 0.0,
        })
    cat_rows.sort(key=lambda r: (-r["read"], r["name"]))
    categories_explored = sum(1 for r in cat_rows if r["read"] > 0)

    # Last 14 days activity.
    history = []
    for i in range(13, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        history.append({"date": d, "active": d in active_days})

    # Current month recap.
    mk = month_key(now)
    month_completions = [c for c in completions if str(c.get("at", "")).startswith(mk)]
    month_cats: Dict[str, int] = {}
    for c in month_completions:
        cid = c.get("category_id") or story_cats.get(c.get("story_id", ""))
        if cid:
            month_cats[cid] = month_cats.get(cid, 0) + 1
    top_cat = None
    if month_cats:
        top_id = max(month_cats.items(), key=lambda kv: kv[1])[0]
        top_cat = next((r for r in cat_rows if r["id"] == top_id), None)
    month_active = sum(1 for d in active_days if d.startswith(mk))
    month = {
        "key": mk,
        "stories": len(month_completions),
        "minutes": int(sum(int(c.get("minutes", 0)) for c in month_completions)),
        "listen_minutes": int(listen_by_month.get(mk, 0) // 60),
        "active_days": month_active,
        "categories": len(month_cats),
        "top_category": top_cat,
    }

    metrics = {
        "stories": len(completed),
        "categories": categories_explored,
        "minutes": total_minutes,
        "listen_minutes": listen_seconds // 60,
        "best_streak": best_streak,
    }
    badges = []
    for bid, icon, metric, target, titles in BADGES:
        value = int(metrics.get(metric, 0))
        title, desc = titles.get(lang, titles["it"])
        badges.append({
            "id": bid, "icon": icon, "title": title, "description": desc,
            "target": target, "value": min(value, target), "unlocked": value >= target,
        })

    return {
        "stories": metrics["stories"],
        "minutes": total_minutes,
        "listen_minutes": metrics["listen_minutes"],
        "streak_days": streak,
        "best_streak": best_streak,
        "categories_explored": categories_explored,
        "categories_total": len(categories),
        "categories": cat_rows,
        "history": history,
        "badges": badges,
        "badges_unlocked": sum(1 for b in badges if b["unlocked"]),
        "month": month,
    }
