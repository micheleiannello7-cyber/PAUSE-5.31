from fastapi import FastAPI, APIRouter, HTTPException, Query, Request, Response, Depends
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import logging
import random
from collections import Counter
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from optional_services import check_optional_services

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="PAUSE API")
api_router = APIRouter(prefix="/api", dependencies=[Depends(check_optional_services)])

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Category(BaseModel):
    id: str
    name: str
    name_en: Optional[str] = None
    icon: str
    color: str
    emoji_key: str
    illustration_generated: Optional[str] = None
    story_count: int = 0
    lesson_count: int = 0

# ---------------------------------------------------------------------------
# i18n helpers — stories are authored in Italian; other languages live in
# doc["translations"][lang] with the same shape (title, hook, chapters, ...).
# ---------------------------------------------------------------------------

SUPPORTED_LANGS = ("it", "en")

# ---------------------------------------------------------------------------
# Audio duration estimator — the "3 min" badge must match the real narration.
# Italian OpenAI TTS reads ~14.5 chars/sec; each chapter title is announced
# with an extra ~1s pause; the intro (title + hook) adds ~1.2s of headroom.
# We CEIL to the next full minute so the badge is never shorter than the real
# playback (fixes: badge said "3 min" while the player lasted 4:50 → now 5).
# ---------------------------------------------------------------------------
import math
import re as _re

_TTS_CHARS_PER_SECOND = 12.5
_TTS_CHAPTER_PAUSE_S = 1.5
_TTS_INTRO_PAUSE_S = 1.5

def _clean_for_estimate(text: str) -> str:
    if not text:
        return ""
    t = _re.sub(r"https?://\S+", "", text)
    t = _re.sub(r"[*_#>~|`]", "", t)
    t = _re.sub(r"\s+", " ", t).strip()
    return t

def _estimated_audio_minutes(doc: dict) -> int:
    """Ceil(minutes) matching the OpenAI TTS narration used by /api/tts/story."""
    if not doc:
        return 1
    total_chars = 0
    total_chars += len(_clean_for_estimate(doc.get("title") or ""))
    total_chars += len(_clean_for_estimate(doc.get("hook") or ""))
    total_chars += len(_clean_for_estimate(doc.get("summary") or ""))
    chapters = doc.get("chapters") or []
    for ch in chapters:
        total_chars += len(_clean_for_estimate(ch.get("title") or ""))
        total_chars += len(_clean_for_estimate(ch.get("body") or ""))
    seconds = total_chars / _TTS_CHARS_PER_SECOND
    seconds += len(chapters) * _TTS_CHAPTER_PAUSE_S
    if doc.get("hook") or doc.get("title"):
        seconds += _TTS_INTRO_PAUSE_S
    return max(1, math.ceil(seconds / 60.0))


def _estimate_from_translation(doc: dict, lang: str) -> int:
    """Compute the ceil minutes using the translated payload when available."""
    tr = (doc.get("translations") or {}).get(lang)
    if not tr:
        return _estimated_audio_minutes(doc)
    merged = {
        "title": tr.get("title") or doc.get("title"),
        "hook": tr.get("hook") or doc.get("hook"),
        "summary": tr.get("summary") or doc.get("summary"),
    }
    base_ch = doc.get("chapters") or []
    tr_ch = tr.get("chapters") or []
    ch_merged = []
    for i, base in enumerate(base_ch):
        t = tr_ch[i] if i < len(tr_ch) else {}
        ch_merged.append({"title": t.get("title") or base.get("title"), "body": t.get("body") or base.get("body")})
    merged["chapters"] = ch_merged
    return _estimated_audio_minutes(merged)

# Mappa category_id -> nome inglese (per localizzare category_name nelle storie).
try:
    from seed_data import CATEGORY_NAMES_EN as _CAT_EN
except Exception:
    _CAT_EN = {}

def _localize(doc: dict, lang: str) -> dict:
    if not doc:
        return doc
    out = dict(doc)
    # Flag early-access window (Premium-exclusive for 7 days). Computed here
    # so every list/detail endpoint returns it without extra plumbing.
    out["is_new"] = _is_new(doc)
    # Sostituisce sempre reading_time_min e deep_dive_time_min con una stima
    # calcolata dal testo reale, arrotondata per eccesso ai minuti pieni. Così
    # il badge "N min" nell'app corrisponde alla durata effettiva del TTS
    # (bug: badge "3 min" mentre il player durava 4:50 → ora "5 min").
    # I capitoli non sono sempre nel doc (list endpoints usano projection senza
    # chapters), quindi ci basiamo sul valore precomputato `audio_minutes_est`
    # scritto al boot in `ensure_estimated_minutes`. Fallback: stima al volo.
    est_map = doc.get("audio_minutes_est") or {}
    est = est_map.get(lang) or est_map.get("it") or _estimated_audio_minutes(doc)
    out["reading_time_min"] = est
    out["deep_dive_time_min"] = est
    if lang == "it":
        return out
    # Nome categoria localizzato dal catalogo categorie (indipendente dalle translations della storia).
    if lang == "en" and doc.get("category_id") in _CAT_EN:
        out["category_name"] = _CAT_EN[doc["category_id"]]
    tr = (doc.get("translations") or {}).get(lang)
    if not tr:
        return out
    for key in ("title", "highlight_words", "hook", "summary", "category_name", "objective"):
        if tr.get(key):
            out[key] = tr[key]
    if tr.get("chapters") and doc.get("chapters"):
        merged = []
        for base, t in zip(doc["chapters"], tr["chapters"]):
            merged.append({**base, "title": t.get("title", base["title"]), "body": t.get("body", base["body"])})
        out["chapters"] = merged
    # Se abbiamo la stima nel doc, usa quella; altrimenti calcola al volo.
    est_lang = est_map.get(lang) or _estimated_audio_minutes(out)
    out["reading_time_min"] = est_lang
    out["deep_dive_time_min"] = est_lang
    return out

def _localize_category(doc: dict, lang: str) -> dict:
    if lang != "it" and doc.get("name_en"):
        return {**doc, "name": doc["name_en"]}
    return doc

def _lang(value: Optional[str]) -> str:
    return value if value in SUPPORTED_LANGS else "it"

class Chapter(BaseModel):
    number: int
    title: str
    body: str
    icon: str
    glow_color: str

class Story(BaseModel):
    id: str
    category_id: str
    category_name: str
    category_icon: str
    category_color: str
    title: str
    highlight_words: List[str] = Field(default_factory=list)
    hook: str
    hero_image: str = ""
    hero_image_generated: Optional[str] = None
    hero_image_thumb: Optional[str] = None
    reading_time_min: int
    deep_dive_time_min: int
    chapters: List[Chapter]
    summary: str
    kind: str = "story"
    objective: Optional[str] = None
    is_new: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StoryPreview(BaseModel):
    id: str
    category_id: str
    category_name: str
    category_icon: str
    category_color: str
    title: str
    highlight_words: List[str] = Field(default_factory=list)
    hook: str
    hero_image: str = ""
    hero_image_generated: Optional[str] = None
    hero_image_thumb: Optional[str] = None
    reading_time_min: int
    deep_dive_time_min: int
    kind: str = "story"
    objective: Optional[str] = None
    is_new: bool = False

class UserState(BaseModel):
    user_id: str
    interests: List[str] = Field(default_factory=list)
    completed_story_ids: List[str] = Field(default_factory=list)
    bookmarked_story_ids: List[str] = Field(default_factory=list)
    liked_story_ids: List[str] = Field(default_factory=list)
    session_start: Optional[datetime] = None
    session_count: int = 0
    blocked_until: Optional[datetime] = None
    total_minutes: int = 0
    streak_days: int = 0
    best_streak: int = 0
    last_active_date: Optional[str] = None
    limit_enabled: bool = True
    session_story_ids: List[str] = Field(default_factory=list)
    session_seconds: int = 0
    is_premium: bool = False
    # Story credits (token bucket): None = never initialised (full).
    credits: Optional[int] = None
    credits_at: Optional[str] = None
    listen_seconds: int = 0
    unlocked_categories: List[str] = Field(default_factory=list)
    # UI preferences persisted on the profile (travel across devices/reinstalls).
    # None = never set: the client keeps its local default.
    theme_mode: Optional[str] = None
    theme_accent: Optional[str] = None
    lang: Optional[str] = None
    # Which content kinds the user wants in the feed: "stories" (curiosità)
    # and/or "lessons" (mini lezioni). Both by default.
    content_modes: List[str] = Field(default_factory=lambda: ["stories", "lessons"])
    # Onboarding "Raccontaci qualcosa di te": optional, None = never provided.
    display_name: Optional[str] = None
    gender: Optional[str] = None  # "man" | "woman" | "other"
    age: Optional[int] = None

class ProfileUpdate(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None

class ContentModesUpdate(BaseModel):
    user_id: str
    modes: List[str]

class StoryRecap(StoryPreview):
    summary: str

class LimitSettingUpdate(BaseModel):
    user_id: str
    enabled: bool

class PremiumUpdate(BaseModel):
    user_id: str
    active: bool

class InterestsUpdate(BaseModel):
    user_id: str
    interests: List[str]

class ToggleRequest(BaseModel):
    user_id: str
    story_id: str

class CompleteRequest(BaseModel):
    user_id: str
    story_id: str
    minutes: int = 2
    seconds: int = 0

class ListenRequest(BaseModel):
    user_id: str
    story_id: str
    seconds: int = 0

class PreferencesUpdate(BaseModel):
    user_id: str
    theme_mode: Optional[str] = None
    theme_accent: Optional[str] = None
    lang: Optional[str] = None

# ---------------------------------------------------------------------------
# Seed (additive: only inserts missing docs; preserves generated URLs)
# ---------------------------------------------------------------------------

from seed_data import CATEGORIES, STORIES
try:
    from seed_lessons_a import LESSONS as LESSONS_A
except Exception:
    LESSONS_A = []
try:
    from seed_lessons_b import LESSONS_B
except Exception:
    LESSONS_B = []
# Former "mini lessons" are now regular stories: one single content format.
LESSONS = list(LESSONS_A) + list(LESSONS_B)
# Contenuti ritirati dal controllo qualità (doppioni / deboli): mai più seminati.
from retired_stories import RETIRED_IDS, retire_in_db
ALL_STORIES = [s for s in list(STORIES) + LESSONS if s["id"] not in RETIRED_IDS]
from category_taxonomy import apply_seed_taxonomy, migrate_curiosita, normalize_category_ids, REASSIGNMENTS
apply_seed_taxonomy(CATEGORIES, ALL_STORIES)

async def ensure_seed():
    """Insert/upsert seed. Preserves hero_image_generated and illustration_generated."""
    for c in CATEGORIES:
        existing = await db.categories.find_one({"id": c["id"]}, {"_id": 0, "illustration_generated": 1})
        payload = {k: v for k, v in c.items()}
        if existing and existing.get("illustration_generated"):
            payload["illustration_generated"] = existing["illustration_generated"]
        await db.categories.update_one({"id": c["id"]}, {"$set": payload}, upsert=True)

    for s in ALL_STORIES:
        existing = await db.stories.find_one(
            {"id": s["id"]},
            {"_id": 0, "hero_image": 1, "hero_image_generated": 1, "hero_image_thumb": 1, "chapters_v6": 1, "chapters": 1, "translations": 1,
             "reading_time_min": 1, "deep_dive_time_min": 1, "content_trimmed": 1, "hook": 1, "summary": 1},
        )
        payload = {k: v for k, v in s.items()}
        # Two content kinds share one shape: "story" (curiosità) and "lesson"
        # (mini lezione, guided steps + objective). The client shows a badge.
        payload["kind"] = s.get("kind", "story")
        if existing and existing.get("hero_image_generated"):
            payload["hero_image_generated"] = existing["hero_image_generated"]
            payload["hero_image_thumb"] = existing.get("hero_image_thumb")
            # Keep the reviewed fallback (including intentionally empty values).
            # Re-seeding must not revive an off-topic photo beneath a new cover.
            payload["hero_image"] = existing.get("hero_image", "")
        if existing and existing.get("content_trimmed"):
            # Editorial trim (trim_stories.py) is the current text: never let
            # the seed files put the long version back.
            for k in ("hook", "summary", "chapters", "translations"):
                if existing.get(k) is not None:
                    payload[k] = existing[k]
            payload["chapters_v6"] = True
        if existing and existing.get("chapters_v6"):
            # Chapters were normalized to 6 by normalize_chapters.py: keep them.
            payload["chapters"] = existing["chapters"]
            payload["chapters_v6"] = True
            for k in ("translations", "reading_time_min", "deep_dive_time_min"):
                if existing.get(k) is not None:
                    payload[k] = existing[k]
        await db.stories.update_one({"id": s["id"]}, {"$set": payload}, upsert=True)
    await db.stories.update_many({"kind": {"$exists": False}}, {"$set": {"kind": "story"}})
    # Il colore della categoria è unico e caratteristico: ogni storia (anche
    # quelle non nel seed) lo eredita sempre dalla propria categoria.
    for c in CATEGORIES:
        await db.stories.update_many(
            {"category_id": c["id"], "category_color": {"$ne": c["color"]}},
            {"$set": {"category_color": c["color"]}},
        )
    retired = await retire_in_db(db)
    if retired:
        logger.info("Retired %s stories into stories_retired", retired)

    # Early-access migration: backdate every story to > EARLY_ACCESS_DAYS ago
    # and re-flag the last 10 (by seed order) as "new" today. Idempotent —
    # only touches docs whose created_at is in the "wrong bucket" so subsequent
    # boots are no-ops. Also fills the field for legacy docs missing it.
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=EARLY_ACCESS_DAYS)
    all_ids = [s["id"] for s in ALL_STORIES]
    if all_ids:
        # I contenuti v9 (produce_v9.py) hanno la data reale di pubblicazione:
        # non vanno retrodatati, altrimenti perdono badge "Nuova" ed early access.
        older_ids = [i for i in all_ids[:-10] if not i.startswith("v9-")]
        fresh_ids = all_ids[-10:]
        old_dt = now - timedelta(days=EARLY_ACCESS_DAYS + 23)
        if older_ids:
            await db.stories.update_many(
                {"id": {"$in": older_ids}, "$or": [
                    {"created_at": {"$exists": False}},
                    {"created_at": {"$gt": threshold}},
                ]},
                {"$set": {"created_at": old_dt}},
            )
        if fresh_ids:
            await db.stories.update_many(
                {"id": {"$in": fresh_ids}, "$or": [
                    {"created_at": {"$exists": False}},
                    {"created_at": {"$lt": threshold}},
                ]},
                {"$set": {"created_at": now}},
            )

    logger.info("Seeded %s categories and %s stories", len(CATEGORIES), len(ALL_STORIES))
    try:
        from seed_chapters_v6 import apply_v6
        logger.info("6-chapter normalization: %s", await apply_v6(db))
    except Exception as e:  # noqa: BLE001
        logger.warning("6-chapter normalization failed: %s", e)
    # Precompute audio_minutes_est per ogni storia dopo la normalizzazione dei
    # capitoli, così i list endpoint (che escludono `chapters` dalla projection)
    # trovano il valore corretto senza dover ricaricare tutto il doc.
    try:
        await ensure_estimated_minutes()
    except Exception as e:  # noqa: BLE001
        logger.warning("audio_minutes_est precompute failed: %s", e)


async def ensure_estimated_minutes() -> None:
    """Precompute the ceil audio minutes for every story (IT + EN when
    available). Idempotent: skip docs where the value already matches."""
    changed = 0
    async for doc in db.stories.find({}, {"_id": 0, "id": 1, "title": 1, "hook": 1, "summary": 1,
                                          "chapters": 1, "translations": 1, "audio_minutes_est": 1}):
        est_it = _estimated_audio_minutes(doc)
        est_map = {"it": est_it}
        if (doc.get("translations") or {}).get("en"):
            est_map["en"] = _estimate_from_translation(doc, "en")
        current = doc.get("audio_minutes_est") or {}
        if current != est_map:
            await db.stories.update_one({"id": doc["id"]}, {"$set": {"audio_minutes_est": est_map}})
            changed += 1
    logger.info("audio_minutes_est precomputed: %s updated", changed)


async def _related_index():
    from related import INDEX
    count = await db.stories.count_documents({})
    if INDEX.size != count:
        docs = await db.stories.find(
            {}, {"_id": 0, "id": 1, "category_id": 1, "title": 1, "hook": 1, "summary": 1,
                 "highlight_words": 1, "translations.en.title": 1, "translations.en.hook": 1},
        ).to_list(5000)
        INDEX.build(docs)
    return INDEX


# --- Taste weighting -------------------------------------------------------
# Hearts are not a list the user browses: they are a signal. When picking the
# next "surprise" we sample a small pool and draw one story with odds that
# grow a little for categories/topics the user hearted (never exclusive, so
# the feed stays varied).
TASTE_POOL = 12
TASTE_CAT_BOOST = 0.6     # +60% at most for the most-hearted category
TASTE_TOPIC_BOOST = 1.2   # +120% at most for a near-identical topic (cosine 1.0)


async def _pick_by_taste(query: dict, state: Optional[dict]) -> Optional[dict]:
    liked: List[str] = [x for x in (state or {}).get("liked_story_ids", []) if x]
    size = TASTE_POOL if liked else 1
    docs = await db.stories.aggregate([
        {"$match": query},
        {"$sample": {"size": size}},
        {"$project": {"_id": 0, "chapters": 0}},
    ]).to_list(size)
    if not docs:
        return None
    if len(docs) == 1 or not liked:
        return docs[0]
    liked_docs = await db.stories.find({"id": {"$in": liked}}, {"_id": 0, "id": 1, "category_id": 1}).to_list(500)
    cat_counts = Counter(d.get("category_id") for d in liked_docs)
    top = max(cat_counts.values()) if cat_counts else 1
    index = await _related_index()
    weights = [
        1.0
        + TASTE_CAT_BOOST * cat_counts.get(d.get("category_id"), 0) / top
        + TASTE_TOPIC_BOOST * index.affinity(d["id"], liked)
        for d in docs
    ]
    return random.choices(docs, weights=weights, k=1)[0]

# ---------------------------------------------------------------------------
# Premium tiers — free vs premium session limits. The "intentional pause" is
# the core of PAUSE, so premium keeps a limit too: it's just a bit more generous
# (one extra story, half the cooldown). NOTE: premium status here is a
# pragmatic placeholder driven by the client; when RevenueCat is connected,
# gate on its entitlement instead.
# ---------------------------------------------------------------------------
# Story credits ("storie disponibili"): a token bucket. Every reader starts
# full (4 free / 5 premium); a NEW story consumes one credit once the reader
# dwells on chapter 1; credits come back one every recharge interval
# (2 h free / 1 h premium), computed on server time so device-clock changes
# can't mint credits. Recharge keeps running while the app is closed.
FREE_CAPACITY = 4
PREMIUM_CAPACITY = 5
FREE_RECHARGE_SECONDS = 2 * 3600
PREMIUM_RECHARGE_SECONDS = 3600
# Reading history: free readers browse the last N days only (records are kept).
HISTORY_FREE_DAYS = 10
# Free users can keep up to 20 bookmarks and 20 favourites; premium is unlimited.
FREE_SAVED_LIMIT = 20
# New stories are Premium-exclusive for this many days after their release
# (early access). Free users see them once the window closes.
EARLY_ACCESS_DAYS = 7
# The "Nuova" badge stays on for longer than early access, so free readers
# also discover a story as new once it opens up to them.
NEW_BADGE_DAYS = 21


def _early_filter(state: Optional[dict]) -> dict:
    """Mongo filter that hides stories still inside the early-access window
    from free users. Premium users get everything."""
    if state and state.get("is_premium"):
        return {}
    threshold = datetime.now(timezone.utc) - timedelta(days=EARLY_ACCESS_DAYS)
    return {"created_at": {"$lte": threshold}}


def _is_new(doc: dict) -> bool:
    created = doc.get("created_at")
    if not isinstance(created, datetime):
        return False
    # Normalize: Mongo stores naive UTC; make it aware for the delta.
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - created) < timedelta(days=NEW_BADGE_DAYS)


def _capacity_for(state: Optional[dict]) -> int:
    """Max story credits for this user's tier."""
    return PREMIUM_CAPACITY if state and state.get("is_premium") else FREE_CAPACITY


def _recharge_for(state: Optional[dict]) -> int:
    """Seconds per credit for this user's tier."""
    return PREMIUM_RECHARGE_SECONDS if state and state.get("is_premium") else FREE_RECHARGE_SECONDS


def _limit_enforced(state: dict) -> bool:
    return os.environ.get("ENFORCE_LIMIT", "false").lower() == "true" and state.get("limit_enabled", True)


def _credit_state(state: dict, now: datetime) -> tuple[int, datetime, bool]:
    """Token bucket read: (credits, anchor, changed). `anchor` is the instant the
    current recharge started counting from; meaningful only when credits < cap."""
    cap = _capacity_for(state)
    step = _recharge_for(state)
    raw = state.get("credits")
    anchor = _parse_dt(state.get("credits_at"))
    if raw is None or anchor is None:
        return cap, now, True
    credits = int(raw)
    changed = False
    if credits < cap:
        gained = int((now - anchor).total_seconds() // step)
        if gained > 0:
            credits = min(cap, credits + gained)
            anchor = anchor + timedelta(seconds=gained * step)
            changed = True
    if credits > cap:  # premium → free downgrade
        credits, changed = cap, True
    return credits, anchor, changed


def _next_credit_seconds(credits: int, anchor: datetime, cap: int, step: int, now: datetime) -> int:
    if credits >= cap:
        return 0
    return max(1, step - int((now - anchor).total_seconds()))


async def _refresh_credits(user_id: str, state: dict, now: datetime) -> tuple[int, datetime, int]:
    """Apply pending recharges and persist them. Returns (credits, anchor, cap)."""
    cap = _capacity_for(state)
    credits, anchor, changed = _credit_state(state, now)
    if changed:
        await db.user_state.update_one(
            {"user_id": user_id},
            {"$set": {"credits": credits, "credits_at": anchor.isoformat(), "session_count": cap - credits}},
        )
        state["credits"], state["credits_at"], state["session_count"] = credits, anchor.isoformat(), cap - credits
    return credits, anchor, cap


KIND_BY_MODE = {"stories": "story", "lessons": "lesson"}


def _kind_filter(state: Optional[dict]) -> dict:
    """Mongo filter for the content kinds a reader can see.

    Mini lessons ("lesson") are Premium-only: free readers always get
    curiosities ("story") regardless of their content_modes. Premium readers
    see the modes they picked (onboarding / profile toggles); an empty or
    missing selection defaults to everything."""
    if not (state or {}).get("is_premium"):
        return {"kind": "story"}
    modes = (state or {}).get("content_modes") or ["stories", "lessons"]
    kinds = [KIND_BY_MODE[m] for m in modes if m in KIND_BY_MODE]
    if not kinds or len(kinds) == len(KIND_BY_MODE):
        return {}
    return {"kind": {"$in": kinds}}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@api_router.get("/")
async def root():
    return {"app": "PAUSE", "status": "ok"}

@api_router.get("/health")
async def health():
    try:
        await db.command("ping")
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "time": datetime.now(timezone.utc).isoformat()}

@api_router.get("/categories", response_model=List[Category])
async def list_categories(lang: Optional[str] = Query("it")):
    docs = await db.categories.find({}, {"_id": 0}).to_list(200)
    # Count curiosità and mini lezioni separately: the grid says "N storie",
    # so mixing the two kinds inflated every counter.
    counts: dict = {}
    async for c in db.stories.aggregate([{"$group": {"_id": {"cat": "$category_id", "kind": "$kind"}, "n": {"$sum": 1}}}]):
        counts[(c["_id"]["cat"], c["_id"].get("kind") or "story")] = c["n"]
    return [
        Category(
            **_localize_category(d, _lang(lang)),
            story_count=counts.get((d["id"], "story"), 0),
            lesson_count=counts.get((d["id"], "lesson"), 0),
        )
        for d in docs
    ]

@api_router.get("/stories", response_model=List[StoryPreview])
async def list_stories(
    category_id: Optional[str] = Query(None),
    interests: Optional[str] = Query(None),
    limit: int = 50,
    lang: Optional[str] = Query("it"),
    user_id: Optional[str] = Query(None),
):
    query = {}
    if category_id and category_id != "all":
        if category_id == "curiosita":
            query["id"] = {"$in": list(REASSIGNMENTS)}
        else:
            query["category_id"] = category_id
    elif interests:
        ids = normalize_category_ids([i.strip() for i in interests.split(",") if i.strip()])
        if ids and "all" not in ids:
            query["category_id"] = {"$in": ids}
    # Early-access: free users don't see stories inside the 7-day window.
    state = await db.user_state.find_one({"user_id": user_id}, {"_id": 0}) if user_id else None
    query.update(_early_filter(state))
    query.update(_kind_filter(state))
    # Newest first so the early-access catalogue surfaces at the top for
    # Premium users (and stays hidden from Free via _early_filter).
    docs = await db.stories.find(query, {"_id": 0, "chapters": 0}).sort("created_at", -1).to_list(limit)
    return [StoryPreview(**_localize(d, _lang(lang))) for d in docs]

async def _discover_documents(user_id, interests, exclude, count, modes=None):
    """One state lookup per deck; keep taste, visibility and unread-first rules."""
    state = await db.user_state.find_one({"user_id": user_id}, {"_id": 0})
    completed = state.get("completed_story_ids", []) if state else []
    exclude_ids = list(completed)
    if exclude:
        exclude_ids.extend([e.strip() for e in exclude.split(",") if e.strip()])

    query: dict = {}
    if interests:
        ids = normalize_category_ids([i.strip() for i in interests.split(",") if i.strip()])
        if ids and "all" not in ids:
            query["category_id"] = {"$in": ids}
    if exclude_ids:
        query["id"] = {"$nin": exclude_ids}
    # Early-access: free users get "surprises" only from stories outside the
    # 7-day window; premium sees anything.
    query.update(_early_filter(state))
    mode_state = {**(state or {}), "content_modes": modes} if modes else state
    query.update(_kind_filter(mode_state))
    explicit = [e.strip() for e in (exclude or "").split(",") if e.strip()]
    picked = []
    for _ in range(count):
        chosen = [doc["id"] for doc in picked]
        unread = {**query, "id": {"$nin": exclude_ids + chosen}}
        doc = await _pick_by_taste(unread, state)
        if not doc:
            fallback = {**query, "id": {"$nin": explicit + chosen}}
            doc = await _pick_by_taste(fallback, state)
        if not doc:
            break
        picked.append(doc)
    return picked


@api_router.get("/discover-next", response_model=StoryPreview)
async def discover_next(
    user_id: str = Query(...), interests: Optional[str] = Query(None),
    exclude: Optional[str] = Query(None), lang: Optional[str] = Query("it"),
):
    docs = await _discover_documents(user_id, interests, exclude, 1)
    if not docs:
        raise HTTPException(404, "No stories match")
    return StoryPreview(**_localize(docs[0], _lang(lang)))


@api_router.get("/discover-batch", response_model=List[StoryPreview])
async def discover_batch(
    user_id: str = Query(...), interests: Optional[str] = Query(None),
    exclude: Optional[str] = Query(None), count: int = Query(7, ge=1, le=14),
    modes: Optional[str] = Query(None), lang: Optional[str] = Query("it"),
):
    """A stable, unique deck in one request, also used to prewarm onboarding.

    Optional modes only preview format selection; never change premium visibility.
    """
    selected_modes = [mode.strip() for mode in modes.split(",")] if modes else None
    if selected_modes and any(mode not in KIND_BY_MODE for mode in selected_modes):
        raise HTTPException(422, "Invalid content mode")
    docs = await _discover_documents(user_id, interests, exclude, count, selected_modes)
    return [StoryPreview(**_localize(doc, _lang(lang))) for doc in docs]

@api_router.get("/stories/{story_id}", response_model=Story)
async def get_story(story_id: str, lang: Optional[str] = Query("it")):
    doc = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Story not found")
    return Story(**_localize(doc, _lang(lang)))

@api_router.get("/stories/{story_id}/related", response_model=List[StoryPreview])
async def related_stories(story_id: str, limit: int = Query(3, ge=1, le=6), lang: Optional[str] = Query("it")):
    """Thematic path: the stories this one 'connects to' (keyword similarity,
    at most two from the same category so the path crosses topics)."""
    if not await db.stories.find_one({"id": story_id}, {"_id": 1}):
        raise HTTPException(404, "Story not found")
    index = await _related_index()
    ids = index.related(story_id, limit=limit)
    if not ids:
        return []
    docs = await db.stories.find({"id": {"$in": ids}}, {"_id": 0, "chapters": 0}).to_list(len(ids))
    by_id = {d["id"]: d for d in docs}
    return [StoryPreview(**_localize(by_id[i], _lang(lang))) for i in ids if i in by_id]

@api_router.get("/stories/{story_id}/next", response_model=StoryPreview)
async def next_story(story_id: str, user_id: Optional[str] = None, lang: Optional[str] = Query("it")):
    current = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not current:
        raise HTTPException(404, "Story not found")
    completed: List[str] = []
    interests: List[str] = []
    if user_id:
        state = await db.user_state.find_one({"user_id": user_id}, {"_id": 0})
        if state:
            completed = state.get("completed_story_ids", [])
            interests = [i for i in state.get("interests", []) if i and i != "all"]

    exclude = [story_id] + completed
    # Prefer the thematic path: the first related story not yet read.
    index = await _related_index()
    for rid in index.related(story_id, limit=3, exclude=completed):
        doc = await db.stories.find_one({"id": rid}, {"_id": 0, "chapters": 0, "summary": 0})
        if doc:
            return StoryPreview(**_localize(doc, _lang(lang)))
    query: dict = {"id": {"$nin": exclude}, "category_id": current["category_id"]}
    doc = await db.stories.find_one(query, {"_id": 0, "chapters": 0, "summary": 0})
    if not doc and interests:
        doc = await db.stories.find_one(
            {"id": {"$nin": exclude}, "category_id": {"$in": interests}},
            {"_id": 0, "chapters": 0, "summary": 0},
        )
    if not doc:
        doc = await db.stories.find_one({"id": {"$nin": exclude}}, {"_id": 0, "chapters": 0, "summary": 0})
    if not doc:
        doc = await db.stories.find_one({"id": {"$ne": story_id}}, {"_id": 0, "chapters": 0, "summary": 0})
    if not doc:
        raise HTTPException(404, "No more stories")
    return StoryPreview(**_localize(doc, _lang(lang)))

@api_router.get("/playlist")
async def build_playlist(
    user_id: str = Query(...),
    minutes: int = Query(10, ge=3, le=30),
    lang: Optional[str] = Query("it"),
):
    """'Pausa da 10 minuti': 2-3 unread stories matching the user's interests
    whose narration fits in ~`minutes`. Never exceeds the stories left in the
    current session so the intentional pause still applies."""
    state = await _get_or_create_state(user_id)
    completed = state.get("completed_story_ids", [])
    interests = [i for i in state.get("interests", []) if i and i != "all"]
    credits, _, _ = await _refresh_credits(user_id, state, datetime.now(timezone.utc))
    slots = max(1, credits)
    max_items = min(3, slots)

    # Same visibility rules as the catalog: early-access window for free
    # users and Premium-only lessons (honouring the user's content modes).
    # Newest content first, then a random shuffle inside that pool so the
    # queue feels fresh while still surfacing the latest releases.
    visibility: dict = {**_early_filter(state), **_kind_filter(state)}
    query: dict = {"id": {"$nin": completed}, **visibility}
    if interests:
        query["category_id"] = {"$in": interests}

    async def _pool(q: dict) -> List[dict]:
        return await db.stories.aggregate([
            {"$match": q},
            {"$sort": {"created_at": -1}},
            {"$limit": 24},
            {"$sample": {"size": 12}},
            {"$project": {"_id": 0, "chapters": 0}},
        ]).to_list(12)

    docs = await _pool(query)
    if len(docs) < 2:
        docs = await _pool({"id": {"$nin": completed}, **visibility})

    picked: List[dict] = []
    total = 0
    for d in docs:
        dur = int(d.get("deep_dive_time_min") or 3)
        if picked and total + dur > minutes:
            continue
        picked.append(d)
        total += dur
        if len(picked) >= max_items:
            break
    return {
        "minutes": minutes,
        "total_min": total,
        "stories": [StoryPreview(**_localize(d, _lang(lang))) for d in picked],
    }

# --------------------------- user state ---------------------------

async def _get_or_create_state(user_id: str) -> dict:
    doc = await db.user_state.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        state = UserState(user_id=user_id).dict()
        await db.user_state.insert_one(state.copy())
        return state
    return doc

@api_router.get("/user/{user_id}", response_model=UserState)
async def get_user(user_id: str):
    return UserState(**await _get_or_create_state(user_id))

@api_router.get("/user/{user_id}/bookmarks", response_model=List[StoryPreview])
async def user_bookmarks(user_id: str, lang: Optional[str] = Query("it")):
    state = await _get_or_create_state(user_id)
    ids = state.get("bookmarked_story_ids", [])
    if not ids:
        return []
    docs = await db.stories.find({"id": {"$in": ids}}, {"_id": 0, "chapters": 0}).to_list(500)
    return [StoryPreview(**_localize(d, _lang(lang))) for d in docs]

@api_router.get("/user/{user_id}/liked", response_model=List[StoryPreview])
async def user_liked(user_id: str, lang: Optional[str] = Query("it")):
    state = await _get_or_create_state(user_id)
    ids = state.get("liked_story_ids", [])
    if not ids:
        return []
    docs = await db.stories.find({"id": {"$in": ids}}, {"_id": 0, "chapters": 0}).to_list(500)
    return [StoryPreview(**_localize(d, _lang(lang))) for d in docs]

@api_router.get("/user/{user_id}/session-stories", response_model=List[StoryRecap])
async def user_session_stories(user_id: str, lang: Optional[str] = Query("it")):
    """Stories read in the current session (ordered), with their 'Da ricordare' summary."""
    state = await _get_or_create_state(user_id)
    ids = state.get("session_story_ids", [])
    if not ids:
        return []
    docs = await db.stories.find({"id": {"$in": ids}}, {"_id": 0, "chapters": 0}).to_list(50)
    by_id = {d["id"]: _localize(d, _lang(lang)) for d in docs}
    return [StoryRecap(**by_id[i]) for i in ids if i in by_id]

@api_router.post("/user/interests", response_model=UserState)
async def set_interests(payload: InterestsUpdate):
    await _get_or_create_state(payload.user_id)
    interests = normalize_category_ids(payload.interests)
    # Nessun limite di argomenti: ogni lettore (base o Premium) sceglie liberamente.
    await db.user_state.update_one(
        {"user_id": payload.user_id},
        {"$set": {"interests": interests}},
    )
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.post("/user/limit-setting", response_model=UserState)
async def set_limit_setting(payload: LimitSettingUpdate):
    await _get_or_create_state(payload.user_id)
    await db.user_state.update_one(
        {"user_id": payload.user_id},
        {"$set": {"limit_enabled": payload.enabled}},
    )
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.post("/user/premium", response_model=UserState)
async def set_premium(payload: PremiumUpdate):
    """Set the user's premium flag. Placeholder unlock driven by the client;
    when RevenueCat is connected, this is set from a verified 'pro' entitlement."""
    await _get_or_create_state(payload.user_id)
    update: dict = {"is_premium": payload.active}
    await db.user_state.update_one({"user_id": payload.user_id}, {"$set": update})
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)


@api_router.post("/user/content-modes", response_model=UserState)
async def set_content_modes(payload: ContentModesUpdate):
    """Choose which content kinds appear in the feed (curiosità / mini lezioni).
    Both kinds are free. An empty or invalid selection falls back to stories."""
    modes = [m for m in payload.modes if m in KIND_BY_MODE]
    await _get_or_create_state(payload.user_id)
    if not modes:
        modes = ["stories"]
    await db.user_state.update_one({"user_id": payload.user_id}, {"$set": {"content_modes": modes}})
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)


# --------------------------- consumable: Stripe Checkout ---------------------------
# Pay once (€1,99) to browse a single category. Flow:
#   1. POST /purchases            -> pending doc + Stripe Checkout Session (hosted page)
#   2. Stripe redirects to /purchases/{id}/return|cancel -> 302 back into the app
#   3. GET /purchases/{id}        -> verifies payment_status with Stripe, grants category
#   4. POST /webhook/stripe       -> same grant, server-to-server (needs STRIPE_WEBHOOK_SECRET)
# Price is server-side only; the client never sends amount/currency.

import stripe
from fastapi.responses import RedirectResponse

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
# Emergent's shared test key is proxied through the integrations gateway.
if "sk_test_emergent" in stripe.api_key:
    stripe.api_base = "https://integrations.emergentagent.com/stripe"
CATEGORY_PRICE_CENTS = 199


class CreatePurchaseRequest(BaseModel):
    user_id: str
    category_id: str
    # Deep link back into the app (https://.../unlock on web, exp://... in Expo Go).
    return_url: str = Field(min_length=1, max_length=500)


def _allowed_return_url(url: str) -> bool:
    return url.startswith(("exp://", "exps://", "frontend://", "https://", "http://localhost"))


def _public_base(request: Request) -> str:
    """Public https origin of this API as seen by the browser (behind the ingress)."""
    env = os.environ.get("PUBLIC_API_URL")
    if env:
        return env.rstrip("/")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}"


def _append_query(url: str, **params) -> str:
    from urllib.parse import urlencode
    return f"{url}{'&' if '?' in url else '?'}{urlencode(params)}"


async def _grant_category(user_id: str, category_id: str) -> None:
    await _get_or_create_state(user_id)
    await db.user_state.update_one(
        {"user_id": user_id}, {"$addToSet": {"unlocked_categories": category_id}},
    )


async def _settle_purchase(doc: dict) -> dict:
    """Ask Stripe for the session's payment_status and, if paid, grant the
    category. Idempotent: the conditional update only flips pending -> paid."""
    if doc.get("status") == "paid" or not doc.get("checkout_session_id"):
        return doc
    session = await run_in_threadpool(stripe.checkout.Session.retrieve, doc["checkout_session_id"])
    if session.payment_status != "paid":
        return doc
    res = await db.purchases.update_one(
        {"purchase_id": doc["purchase_id"], "status": {"$ne": "paid"}},
        {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.modified_count:
        await _grant_category(doc["user_id"], doc["category_id"])
        logger.info("Purchase %s paid: user=%s category=%s", doc["purchase_id"], doc["user_id"], doc["category_id"])
    return {**doc, "status": "paid"}


@api_router.post("/purchases")
async def create_purchase(payload: CreatePurchaseRequest, request: Request):
    if not stripe.api_key:
        raise HTTPException(503, "Payments not configured")
    if not _allowed_return_url(payload.return_url):
        raise HTTPException(400, "Unsupported return URL")
    cat = await db.categories.find_one({"id": payload.category_id}, {"_id": 0, "name": 1, "name_en": 1})
    if not cat:
        raise HTTPException(404, "Category not found")
    state = await _get_or_create_state(payload.user_id)
    if state.get("is_premium") or payload.category_id in state.get("unlocked_categories", []):
        raise HTTPException(409, "Category already unlocked")

    purchase_id = uuid.uuid4().hex
    await db.purchases.insert_one({
        "purchase_id": purchase_id,
        "user_id": payload.user_id,
        "category_id": payload.category_id,
        "amount_cents": CATEGORY_PRICE_CENTS,
        "currency": "eur",
        "status": "pending",
        "return_url": payload.return_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    base = _public_base(request)
    try:
        session = await run_in_threadpool(
            stripe.checkout.Session.create,
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": CATEGORY_PRICE_CENTS,
                    "product_data": {"name": f"PAUSE — {cat['name']}", "description": "Sblocco singola categoria (una tantum)"},
                },
                "quantity": 1,
            }],
            success_url=f"{base}/api/purchases/{purchase_id}/return?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/api/purchases/{purchase_id}/cancel",
            client_reference_id=purchase_id,
            metadata={"purchase_id": purchase_id, "user_id": payload.user_id, "category_id": payload.category_id},
        )
    except stripe.StripeError as exc:
        logger.exception("Stripe session creation failed: %s", exc)
        await db.purchases.update_one({"purchase_id": purchase_id}, {"$set": {"status": "error"}})
        raise HTTPException(502, "Could not create checkout session")
    await db.purchases.update_one({"purchase_id": purchase_id}, {"$set": {"checkout_session_id": session.id}})
    return {"purchase_id": purchase_id, "checkout_url": session.url}


@api_router.get("/purchases/{purchase_id}")
async def purchase_status(purchase_id: str):
    doc = await db.purchases.find_one({"purchase_id": purchase_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Purchase not found")
    if doc.get("status") == "pending":
        try:
            doc = await _settle_purchase(doc)
        except stripe.StripeError as exc:
            logger.warning("Stripe status check failed for %s: %s", purchase_id, exc)
    return {k: doc.get(k) for k in ("purchase_id", "user_id", "category_id", "status")}


@api_router.get("/purchases/{purchase_id}/return")
async def purchase_return(purchase_id: str, session_id: str = Query(...)):
    doc = await db.purchases.find_one({"purchase_id": purchase_id}, {"_id": 0})
    if not doc or doc.get("checkout_session_id") != session_id:
        raise HTTPException(400, "Invalid checkout session")
    # Settle eagerly so the app usually sees "paid" on its first poll.
    try:
        await _settle_purchase(doc)
    except stripe.StripeError:
        pass
    return RedirectResponse(_append_query(doc["return_url"], purchase_id=purchase_id))


@api_router.get("/purchases/{purchase_id}/cancel")
async def purchase_cancel(purchase_id: str):
    doc = await db.purchases.find_one({"purchase_id": purchase_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Purchase not found")
    await db.purchases.update_one({"purchase_id": purchase_id, "status": "pending"}, {"$set": {"status": "cancelled"}})
    return RedirectResponse(_append_query(doc["return_url"], purchase_id=purchase_id, cancelled="1"))


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(503, "Webhook not configured")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, request.headers.get("stripe-signature", ""), secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook")
    if event["type"] in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        session_id = event["data"]["object"]["id"]
        doc = await db.purchases.find_one({"checkout_session_id": session_id}, {"_id": 0})
        if doc:
            await _settle_purchase(doc)
    return {"received": True}


async def _toggle_saved(payload: ToggleRequest, field: str, limit_code: str) -> UserState:
    state = await _get_or_create_state(payload.user_id)
    ids = set(state.get(field, []))
    if payload.story_id in ids:
        ids.remove(payload.story_id)
    else:
        if not state.get("is_premium") and len(ids) >= FREE_SAVED_LIMIT:
            # 402 Payment Required: the client shows the paywall prompt.
            raise HTTPException(402, {"code": limit_code, "limit": FREE_SAVED_LIMIT})
        ids.add(payload.story_id)
    await db.user_state.update_one({"user_id": payload.user_id}, {"$set": {field: list(ids)}})
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.post("/user/preferences", response_model=UserState)
async def set_preferences(payload: PreferencesUpdate):
    """Persist UI preferences (theme, accent, language) on the profile so they
    survive reinstalls and travel across devices. Only known values are stored;
    omitted fields are left untouched."""
    update: dict = {}
    if payload.theme_mode in ("light", "dark", "system"):
        update["theme_mode"] = payload.theme_mode
    if payload.theme_accent in ("aurora", "tramonto", "foresta", "oceano", "orchidea"):
        update["theme_accent"] = payload.theme_accent
    if payload.lang in ("it", "en"):
        update["lang"] = payload.lang
    await _get_or_create_state(payload.user_id)
    if update:
        await db.user_state.update_one({"user_id": payload.user_id}, {"$set": update})
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.post("/user/profile", response_model=UserState)
async def set_profile(payload: ProfileUpdate):
    """Persist the onboarding profile (name/nickname, gender, age). Additive:
    only valid, provided fields are written; nothing else on the state changes."""
    update: dict = {}
    if payload.display_name is not None:
        name = payload.display_name.strip()
        if not (1 <= len(name) <= 40):
            raise HTTPException(422, "display_name must be 1-40 characters")
        update["display_name"] = name
    if payload.gender is not None:
        if payload.gender not in ("man", "woman", "other"):
            raise HTTPException(422, "invalid gender")
        update["gender"] = payload.gender
    if payload.age is not None:
        if not (13 <= payload.age <= 120):
            raise HTTPException(422, "age must be between 13 and 120")
        update["age"] = payload.age
    await _get_or_create_state(payload.user_id)
    if update:
        await db.user_state.update_one({"user_id": payload.user_id}, {"$set": update})
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.post("/user/bookmark", response_model=UserState)
async def toggle_bookmark(payload: ToggleRequest):
    return await _toggle_saved(payload, "bookmarked_story_ids", "saved_limit")

@api_router.post("/user/like", response_model=UserState)
async def toggle_like(payload: ToggleRequest):
    return await _toggle_saved(payload, "liked_story_ids", "liked_limit")

@api_router.post("/user/complete", response_model=UserState)
async def complete_story(payload: CompleteRequest):
    state = await _get_or_create_state(payload.user_id)
    completed = set(state.get("completed_story_ids", []))
    was_new = payload.story_id not in completed
    completed.add(payload.story_id)
    total_minutes = state.get("total_minutes", 0) + (payload.minutes if was_new else 0)

    # Credits: a NEW story consumes one credit (token bucket, +1 every hour).
    now = datetime.now(timezone.utc)
    credits, anchor, cap = await _refresh_credits(payload.user_id, state, now)
    session_story_ids = list(state.get("session_story_ids", []))
    session_seconds = state.get("session_seconds", 0)
    if was_new:
        if credits >= cap:
            # Fully recharged → this reading opens a new "session" (recap list).
            session_story_ids = []
            session_seconds = 0
            anchor = now
        if credits > 0:
            credits -= 1
        session_story_ids.append(payload.story_id)
        session_seconds += max(0, min(payload.seconds, 1800))

    today = now.strftime("%Y-%m-%d")
    last_active = state.get("last_active_date")
    streak = state.get("streak_days", 0)
    if last_active != today:
        if last_active:
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            streak = streak + 1 if last_active == yesterday else 1
        else:
            streak = 1
    best_streak = max(int(state.get("best_streak", 0)), streak)

    # Dated history for statistics / monthly recap.
    active_days = list(state.get("active_days", []))
    if today not in active_days:
        active_days.append(today)
    active_days = active_days[-400:]
    completions = list(state.get("completions", []))
    story_doc = await db.stories.find_one({"id": payload.story_id}, {"_id": 0, "category_id": 1})
    entry = {
        "story_id": payload.story_id,
        "category_id": story_doc.get("category_id") if story_doc else None,
        "at": now.isoformat(),
        "minutes": payload.minutes,
    }
    if not was_new:
        # Re-reads are kept for the reading history but don't count as new
        # discoveries (stats ignore them).
        entry["reread"] = True
    completions.append(entry)

    await db.user_state.update_one(
        {"user_id": payload.user_id},
        {
            "$set": {
                "completed_story_ids": list(completed),
                "total_minutes": total_minutes,
                "credits": credits,
                "credits_at": anchor.isoformat(),
                "session_count": cap - credits,
                "session_story_ids": session_story_ids[-cap:],
                "session_seconds": session_seconds,
                "blocked_until": None,
                "streak_days": streak,
                "best_streak": best_streak,
                "last_active_date": today,
                "active_days": active_days,
                "completions": completions,
            }
        },
    )
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.post("/user/listen", response_model=UserState)
async def log_listen(payload: ListenRequest):
    """Accumulate listening time (flushed by the player every ~30s)."""
    state = await _get_or_create_state(payload.user_id)
    secs = max(0, min(int(payload.seconds), 600))
    now = datetime.now(timezone.utc)
    mk = now.strftime("%Y-%m")
    by_month = dict(state.get("listen_by_month", {}) or {})
    by_month[mk] = int(by_month.get(mk, 0)) + secs
    await db.user_state.update_one(
        {"user_id": payload.user_id},
        {"$set": {"listen_seconds": int(state.get("listen_seconds", 0)) + secs, "listen_by_month": by_month}},
    )
    doc = await db.user_state.find_one({"user_id": payload.user_id}, {"_id": 0})
    return UserState(**doc)

@api_router.get("/user/{user_id}/stats")
async def user_stats(user_id: str, lang: Optional[str] = Query("it")):
    """Progress dashboard: totals, categories map, 14-day history, badges, month recap."""
    from stats import build_stats
    state = await _get_or_create_state(user_id)
    cats = await db.categories.find({}, {"_id": 0}).to_list(200)
    totals = {c["_id"]: c["n"] async for c in db.stories.aggregate([{"$group": {"_id": "$category_id", "n": {"$sum": 1}}}])}
    ids = state.get("completed_story_ids", [])
    story_cats: dict = {}
    if ids:
        async for d in db.stories.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "category_id": 1}):
            story_cats[d["id"]] = d["category_id"]
    return build_stats(state, cats, story_cats, totals, _lang(lang))


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        s = value.replace("Z", "+00:00") if isinstance(value, str) else value
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


@api_router.get("/user/{user_id}/limit-check")
async def limit_check(user_id: str):
    state = await _get_or_create_state(user_id)
    enforce = _limit_enforced(state)
    now = datetime.now(timezone.utc)
    credits, anchor, cap = await _refresh_credits(user_id, state, now)
    step = _recharge_for(state)
    next_in = _next_credit_seconds(credits, anchor, cap, step, now)
    next_at = (now + timedelta(seconds=next_in)) if next_in else None
    blocked = bool(enforce and credits <= 0)
    return {
        "enforce": enforce,
        "credits": credits,
        "capacity": cap,
        "recharge_seconds": step,
        "next_credit_in": next_in,
        "next_credit_at": next_at.isoformat() if next_at else None,
        # Legacy fields kept for existing UI: "used" count and the reopen time.
        "session_count": cap - credits,
        "session_seconds": state.get("session_seconds", 0),
        "limit": cap,
        "is_premium": bool(state.get("is_premium")),
        "reached": bool(enforce and credits <= 0),
        "blocked": blocked,
        "blocked_until": next_at.isoformat() if blocked and next_at else None,
        "remaining_seconds": next_in if blocked else 0,
    }


class HistoryItem(BaseModel):
    story: StoryPreview
    read_at: str
    reread: bool = False


@api_router.get("/user/{user_id}/history")
async def user_history(
    user_id: str,
    lang: Optional[str] = Query("it"),
    q: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
):
    """Reading history (latest read per story, newest first) built from the
    existing `completions` log. Free readers only see the last
    HISTORY_FREE_DAYS days and cannot search/filter; nothing is deleted."""
    state = await _get_or_create_state(user_id)
    premium = bool(state.get("is_premium"))
    now = datetime.now(timezone.utc)
    latest: dict = {}
    for c in state.get("completions", []):
        at = _parse_dt(c.get("at"))
        sid = c.get("story_id")
        if not at or not sid:
            continue
        prev = latest.get(sid)
        if not prev or at > prev["at"]:
            latest[sid] = {"at": at, "reread": bool(c.get("reread"))}
    entries = sorted(latest.items(), key=lambda kv: kv[1]["at"], reverse=True)
    hidden = 0
    if not premium:
        threshold = now - timedelta(days=HISTORY_FREE_DAYS)
        visible = [(sid, e) for sid, e in entries if e["at"] >= threshold]
        hidden = len(entries) - len(visible)
        entries = visible
    else:
        since_dt = _parse_dt(since)
        if since_dt:
            entries = [(sid, e) for sid, e in entries if e["at"] >= since_dt]
    ids = [sid for sid, _ in entries]
    docs = await db.stories.find({"id": {"$in": ids}}, {"_id": 0, "chapters": 0}).to_list(len(ids) or 1)
    by_id = {d["id"]: _localize(d, _lang(lang)) for d in docs}
    items: List[HistoryItem] = []
    needle = (q or "").strip().lower() if premium else ""
    cat = category_id if premium else None
    for sid, e in entries:
        doc = by_id.get(sid)
        if not doc:
            continue
        if cat and doc.get("category_id") != cat:
            continue
        if needle and needle not in str(doc.get("title", "")).lower():
            continue
        items.append(HistoryItem(story=StoryPreview(**doc), read_at=e["at"].isoformat(), reread=e["reread"]))
    return {
        "items": items,
        "is_premium": premium,
        "window_days": None if premium else HISTORY_FREE_DAYS,
        "hidden_count": hidden,
        "total": len(latest),
    }

@api_router.get("/content/report")
async def content_report():
    """Progress of AI content: stories per category, translations and cover images done/missing."""
    stories = await db.stories.find({}, {"_id": 0, "id": 1, "category_id": 1, "hero_image_generated": 1, "translations": 1}).to_list(2000)
    per_cat: dict = {}
    for st in stories:
        per_cat[st["category_id"]] = per_cat.get(st["category_id"], 0) + 1
    missing_images = [st["id"] for st in stories if not st.get("hero_image_generated")]
    missing_en = [st["id"] for st in stories if not (st.get("translations") or {}).get("en")]
    return {
        "stories": len(stories),
        "per_category": per_cat,
        "images_done": len(stories) - len(missing_images),
        "images_missing": missing_images,
        "en_done": len(stories) - len(missing_en),
        "en_missing": missing_en,
    }

# --------------------------- media proxy ---------------------------
# Object Storage has no public/CDN URLs, so the backend fronts every image
# read with a bounded disk cache (media_cache.py). Storage paths are
# content-addressed → strong ETag + immutable caching are safe; a changed
# asset gets a new path (and the client a new `?v=`), never a stale hit.

def _image_response(request: Request, storage_path: str, content: bytes, ctype: str) -> Response:
    from media_cache import etag_for, IMMUTABLE
    etag = etag_for(storage_path)
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": IMMUTABLE})
    return Response(content=content, media_type=ctype, headers={"Cache-Control": IMMUTABLE, "ETag": etag})


@api_router.get("/media/{story_id}")
async def media_for_story(request: Request, story_id: str, size: str = Query("hero")):
    """Serve a story cover (WebP) from Object Storage. `size=thumb` returns the
    ≤600px variant for lists when available."""
    doc = await db.stories.find_one({"id": story_id}, {"_id": 0, "hero_image_generated": 1, "hero_image_thumb": 1})
    if not doc or not doc.get("hero_image_generated"):
        raise HTTPException(404, "No generated image")
    path = (doc.get("hero_image_thumb") if size == "thumb" else None) or doc["hero_image_generated"]
    from media_cache import cached_object
    content, ctype = await cached_object(path)
    return _image_response(request, path, content, ctype)


@api_router.get("/category-media-candidate/{category_id}")
async def media_candidate_for_category(category_id: str):
    """Anteprima (revisione) di una nuova famiglia di icone: PNG RGBA locali in
    category_art/candidates, non ancora pubblicati nell'Object Storage."""
    safe = "".join(ch for ch in category_id if ch.isalnum() or ch == "-")
    path = Path(__file__).parent / "category_art" / "candidates" / f"{safe}.png"
    if not path.is_file():
        raise HTTPException(404, "No candidate")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-cache"})


@api_router.get("/category-media/{category_id}")
async def media_for_category(request: Request, category_id: str, cutout: bool = False, tight: bool = False):
    """Serve the illustration for a category. `cutout=true` returns the object
    alone (black studio background keyed out, PNG RGBA), for tinted surfaces."""
    collection = db.design_assets if category_id == "all" else db.categories
    asset_id = "category-all" if category_id == "all" else category_id
    doc = await collection.find_one({"id": asset_id}, {"_id": 0, "illustration_generated": 1})
    if not doc or not doc.get("illustration_generated"):
        raise HTTPException(404, "No generated image")
    path = doc["illustration_generated"]
    from media_cache import cached_object, cached_derived
    content, ctype = await cached_object(path)
    if cutout:
        from media_opt import cutout_png
        path = f"{path}#cutout-tight-v1" if tight else f"{path}#cutout-v2"
        content, ctype = await cached_derived(path, lambda: (cutout_png(content, tight=tight), "image/png"))
    return _image_response(request, path, content, ctype)


@api_router.get("/category-clips")
async def category_clips():
    """Map category id → URL of its ~3s hero clip (only the ones generated)."""
    out = {}
    async for doc in db.design_assets.find({"id": {"$regex": "^clip-"}, "clip_path": {"$nin": [None, ""]}}, {"_id": 0, "id": 1, "clip_revision": 1}):
        cid = doc["id"][len("clip-"):]
        out[cid] = f"/api/category-clip/{cid}?v={doc.get('clip_revision', '1')}"
    return out


@api_router.get("/category-clip/{category_id}")
async def clip_for_category(request: Request, category_id: str):
    """Serve the MP4 hero clip of a category from Object Storage."""
    doc = await db.design_assets.find_one({"id": f"clip-{category_id}"}, {"_id": 0, "clip_path": 1})
    if not doc or not doc.get("clip_path"):
        raise HTTPException(404, "No clip")
    from media_cache import cached_object
    content, _ = await cached_object(doc["clip_path"])
    return _image_response(request, doc["clip_path"], content, "video/mp4")


@api_router.get("/content-mode-media/{mode}")
async def media_for_content_mode(request: Request, mode: str):
    """Serve the 3D icon for a content mode (stories / lessons)."""
    doc = await db.design_assets.find_one({"id": f"mode-{mode}"}, {"_id": 0, "illustration_generated": 1})
    if not doc or not doc.get("illustration_generated"):
        raise HTTPException(404, "No generated image")
    path = doc["illustration_generated"]
    from media_cache import cached_object
    content, ctype = await cached_object(path)
    return _image_response(request, path, content, ctype)


@api_router.get("/content/assets-report")
async def content_assets_report():
    """Metadata-only overview of generated media (no bytes touched)."""
    from tts import assets_report
    import media_cache
    covers = await db.stories.count_documents({"hero_image_generated": {"$nin": [None, ""]}})
    thumbs = await db.stories.count_documents({"hero_image_thumb": {"$nin": [None, ""]}})
    total = await db.stories.count_documents({})
    return {
        "tts": await assets_report(db),
        "covers": {"stories": total, "with_cover": covers, "with_thumb": thumbs},
        "image_disk_cache": media_cache.stats(),
    }

# --------------------------- tts (nova / tts-1-hd) ---------------------------

def _tts_url(story_id: str, lang: str, voice: str, preview: bool, chash: str) -> str:
    from urllib.parse import urlencode
    from tts import VOICE
    q = {"lang": lang}
    if voice != VOICE:
        q["voice"] = voice
    if preview:
        q["preview"] = "true"
    q["v"] = chash
    return f"/api/tts/story/{story_id}?{urlencode(q)}"


@api_router.get("/tts/status/{story_id}")
async def tts_status_for_story(
    story_id: str, lang: Optional[str] = Query("it"), voice: Optional[str] = Query(None), preview: bool = Query(False),
):
    """Is the narration for this story+lang+voice+content already generated?
    Never triggers generation — the player uses it to decide whether to load
    the persistent URL right away or ask for a warm-up first."""
    doc = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Story not found")
    from tts import asset_status, last_failure, resolve_voice
    resolved_lang = _lang(lang)
    v = resolve_voice(voice)
    kind = "preview" if preview else "full"
    asset, chash, generating = await asset_status(db, _localize(doc, resolved_lang), resolved_lang, v, kind)
    return {
        "story_id": story_id, "lang": resolved_lang, "voice": v, "content_hash": chash,
        "ready": asset is not None, "generating": generating,
        "error": None if asset else last_failure(story_id, resolved_lang, v, kind, chash),
        "key": asset["key"] if asset else None, "size": asset.get("size") if asset else None,
        "provider": asset.get("provider") if asset else None,
        "url": _tts_url(story_id, resolved_lang, v, preview, chash),
    }


@api_router.post("/tts/warmup/{story_id}")
async def tts_warmup(story_id: str, lang: Optional[str] = Query("it"), voice: Optional[str] = Query(None)):
    """Kick off TTS generation for a story. Returns immediately; the file is
    written in the background. Idempotent: if the audio already exists (for
    this exact content version) nothing is generated."""
    doc = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Story not found")
    from tts import asset_status, generate_story_audio, resolve_voice
    resolved_lang = _lang(lang)
    v = resolve_voice(voice)
    localized = _localize(doc, resolved_lang)
    asset, chash, generating = await asset_status(db, localized, resolved_lang, v, "full")
    if asset:
        return {"story_id": story_id, "status": "cached", "voice": v, "url": _tts_url(story_id, resolved_lang, v, False, chash)}
    if not generating:
        # Fire and forget: the coroutine registers the asset when it finishes.
        asyncio.create_task(generate_story_audio(localized, resolved_lang, preview=False, db=db, voice=v))
    return {"story_id": story_id, "status": "generating", "voice": v, "url": _tts_url(story_id, resolved_lang, v, False, chash)}


@api_router.get("/tts/voices")
async def tts_voices():
    from tts import VOICES, VOICE, tts_status
    return {"voices": list(VOICES), "default": VOICE, **tts_status()}


@api_router.get("/tts/voice-sample")
async def tts_voice_sample(request: Request, voice: str = Query("nova"), lang: Optional[str] = Query("it")):
    """Short greeting in the requested voice for the voice picker."""
    from tts import generate_voice_sample
    try:
        path = await generate_voice_sample(voice, _lang(lang), db=db)
    except Exception as exc:
        logger.exception("Voice sample failed for %s: %s", voice, exc)
        raise HTTPException(502, f"TTS generation failed: {exc}")
    return _range_response(path, request)


def _range_response(path: Path, request: Request, etag: Optional[str] = None, immutable: bool = True) -> Response:
    """Serve a file with HTTP Range support so expo-audio can scrub.

    Starlette 0.37 FileResponse ignores the Range header and always returns
    the full body — that makes seeking near-impossible on the web preview
    (the browser can only jump to already-buffered bytes). We handle 206
    partial-content ourselves; without a Range header we fall back to the
    plain FileResponse.

    `etag` is the asset key (content-addressed) → conditional requests get a
    304 and the body is only cacheable "forever" when the URL is versioned.
    """
    file_size = path.stat().st_size
    range_header = request.headers.get("range") or request.headers.get("Range")
    common_headers = {
        "Cache-Control": "public, max-age=31536000, immutable" if immutable else "public, max-age=3600",
        "Accept-Ranges": "bytes",
    }
    if etag:
        common_headers["ETag"] = f'"{etag}"'
        if request.headers.get("if-none-match") == f'"{etag}"':
            return Response(status_code=304, headers=common_headers)
    if not range_header or not range_header.startswith("bytes="):
        return FileResponse(str(path), media_type="audio/mpeg", headers=common_headers)

    try:
        raw = range_header.removeprefix("bytes=")
        start_s, _, end_s = raw.partition("-")
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else file_size - 1
    except ValueError:
        raise HTTPException(status_code=416, detail="Invalid Range header")
    if start >= file_size or start < 0 or end < start:
        return Response(status_code=416, headers={**common_headers,
                                                  "Content-Range": f"bytes */{file_size}"})
    end = min(end, file_size - 1)
    length = end - start + 1

    def _iter():
        with path.open("rb") as f:
            f.seek(start)
            remaining = length
            chunk = 64 * 1024
            while remaining > 0:
                buf = f.read(min(chunk, remaining))
                if not buf:
                    break
                remaining -= len(buf)
                yield buf

    from fastapi.responses import StreamingResponse
    headers = {
        **common_headers,
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(length),
    }
    return StreamingResponse(_iter(), status_code=206, media_type="audio/mpeg", headers=headers)


@api_router.get("/tts/story/{story_id}")
async def tts_story(
    request: Request,
    story_id: str,
    lang: Optional[str] = Query("it"),
    preview: bool = Query(False),
    voice: Optional[str] = Query(None),
    v: Optional[str] = Query(None),
):
    """Serve the narrated audio for a story (voice=nova by default,
    onyx/echo/shimmer for Premium listeners).

    `v` is the content hash returned by /tts/status — it only versions the URL
    (safe long-lived caching); the asset itself is resolved from the current
    story text, so the same content is never generated twice.
    """
    doc = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Story not found")
    localized = _localize(doc, _lang(lang))
    from tts import asset_status, generate_story_audio, resolve_voice
    resolved_lang = _lang(lang)
    rv = resolve_voice(voice)
    kind = "preview" if preview else "full"
    asset, chash, _ = await asset_status(db, localized, resolved_lang, rv, kind)
    etag = asset["key"] if asset else None
    if etag and request.headers.get("if-none-match") == f'"{etag}"':
        return Response(status_code=304, headers={"ETag": f'"{etag}"', "Accept-Ranges": "bytes"})
    try:
        path = await generate_story_audio(localized, resolved_lang, preview=preview, db=db, voice=rv)
    except Exception as exc:
        logger.exception("TTS generation failed for %s: %s", story_id, exc)
        raise HTTPException(502, f"TTS generation failed: {exc}")
    if etag is None:
        fresh, _, _ = await asset_status(db, localized, resolved_lang, rv, kind)
        etag = fresh["key"] if fresh else None
    return _range_response(path, request, etag=etag, immutable=v == chash)


@api_router.get("/tts/random-preview")
async def tts_random_preview(lang: Optional[str] = Query("it")):
    """Return metadata + audio URL of a random story preview (~5s of narration).

    The client can hit this once from Profile to sample the Italian nova voice
    before enabling audio playback in every deep-dive.
    """
    cursor = db.stories.aggregate([{"$sample": {"size": 1}}, {"$project": {"_id": 0}}])
    docs = await cursor.to_list(1)
    if not docs:
        raise HTTPException(404, "No stories to preview")
    story = docs[0]
    return {
        "story_id": story["id"],
        "title": _localize(story, _lang(lang)).get("title"),
        "audio_path": f"/api/tts/story/{story['id']}?preview=true&lang={_lang(lang)}",
    }


# ---------------------------------------------------------------------------
from auth import create_auth_router, ensure_auth_indexes

app.include_router(api_router)
app.include_router(create_auth_router(db))

app.add_middleware(
    CORSMiddleware,
    # The app is anonymous (no cookies / auth headers), so credentials are not
    # needed. Keeping allow_credentials=False lets us safely return
    # `Access-Control-Allow-Origin: *`; combining `*` with credentials=true is
    # invalid per the Fetch spec and strict browsers (e.g. Brave, or when the
    # web preview runs inside a third-party iframe) block the response.
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.on_event("startup")
async def startup_event():
    await ensure_auth_indexes(db)
    logger.info("Reclassified legacy Curiosità records: %s", await migrate_curiosita(db, CATEGORIES))
    await ensure_seed()
    # Asset sync (copertine, artwork, audio) può richiedere minuti in un ambiente
    # nuovo: gira in background così l'API risponde subito. Le storie senza
    # copertina usano il fallback grafico finché la sync non le collega.
    app.state.asset_sync = asyncio.create_task(sync_assets_in_background())


async def sync_assets_in_background():
    from category_artwork import ensure_category_artwork
    await ensure_category_artwork(db)
    from content_mode_artwork import ensure_content_mode_artwork
    await ensure_content_mode_artwork(db)
    # Copertine fornite dall'utente in backend/covers/<id>.<ext>: ottimizzate in
    # WebP, caricate nello storage e collegate alla storia (idempotente).
    try:
        from covers_sync import sync_local_covers
        logger.info("Local covers sync: %s", await sync_local_covers(db))
    except Exception:
        logger.exception("Local covers sync failed")
    from cover_curation import apply_cover_exclusions
    logger.info("Applied cover exclusions: %s", await apply_cover_exclusions(db))
    # Copertine importate (manifest 4.96/4.971) + esclusioni editoriali per
    # sorgente: solo asset già approvati, nessuna generazione a pagamento.
    try:
        from restore_imported_covers import restore_imported_covers
        from cover_editorial import apply_cover_exclusions as apply_editorial_exclusions
        imported = await restore_imported_covers(db)
        logger.info("Imported covers restore: %s", {k: len(v) for k, v in imported.items()})
        logger.info("Off-topic covers excluded: %s", len(await apply_editorial_exclusions(db)))
    except Exception:
        logger.exception("Reviewed cover restore failed")
    # Cache disco delle copertine e delle icone categoria riscaldata subito:
    # la prima apertura della Home non aspetta l'Object Storage.
    try:
        logger.info("Media cache warm-up: %s files", await warm_media_cache())
    except Exception:
        logger.exception("Media cache warm-up failed")
    # Audio assets: metadata indexes, then adopt every legacy mp3 (disk or
    # storage) into `tts_assets` so it is reused instead of regenerated.
    try:
        from tts import ensure_indexes, ingest_disk_cache_into_storage, adopt_legacy_assets
        await ensure_indexes(db)
        logger.info("TTS disk→storage ingest: %s", await ingest_disk_cache_into_storage(db))
        docs = await db.stories.find({}, {"_id": 0}).to_list(5000)
        localized = [(lang, _localize(d, lang)) for d in docs for lang in SUPPORTED_LANGS]
        logger.info("TTS legacy adoption: %s", await adopt_legacy_assets(db, localized))
    except Exception:
        logger.exception("TTS asset migration failed")

async def warm_media_cache() -> int:
    from media_cache import cached_object
    paths = []
    async for doc in db.categories.find({"illustration_generated": {"$ne": None}}, {"_id": 0, "illustration_generated": 1}):
        paths.append(doc["illustration_generated"])
    async for doc in db.stories.find({"hero_image_generated": {"$ne": None}}, {"_id": 0, "hero_image_generated": 1, "hero_image_thumb": 1}):
        paths.extend(p for p in (doc.get("hero_image_generated"), doc.get("hero_image_thumb")) if p)
    warmed = 0
    for path in paths:
        try:
            await cached_object(path)
            warmed += 1
        except HTTPException:
            continue
    return warmed


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
