"""
P^USE — content top-up generator (bilingual IT+EN, GPT-5.4 via emergentintegrations).

Levels EVERY category to the same amount of content and then adds the extra
requested items, for BOTH kinds:
    - stories  (curiosità)     -> TARGET_STORY per category
    - lessons  (mini lezioni)  -> TARGET_LESSON per category

Idempotent: counts existing docs per (category, kind) and only creates the
missing ones. New docs are written straight to Mongo (upsert $setOnInsert) with
an old created_at so Free users see them immediately (past the early-access
window). Reruns only do the missing work.

Usage:
    cd /app/backend && python generate_fill.py                 # both kinds
    cd /app/backend && python generate_fill.py --kind story
    cd /app/backend && python generate_fill.py --kind lesson
"""
import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from seed_data import CATEGORIES, GLOWS  # noqa: E402

MODEL = ("openai", "gpt-5.4")
CONCURRENCY = 6
TARGET_STORY = 28   # 18 baseline (max) + 10 new
TARGET_LESSON = 20  # 10 baseline (max) + 10 new
OLD_DT = datetime.now(timezone.utc) - timedelta(days=40)  # past early-access

CHAPTER_ICONS = [
    "flash", "aperture", "sunny", "image", "bulb", "planet", "sparkles", "cloud", "water", "flame",
    "leaf", "rocket", "telescope", "book", "time", "heart", "eye", "ear", "body", "compass", "map",
    "cash", "trending-up", "color-palette", "brush", "musical-notes", "paw", "fish", "bug", "flask",
    "nuclear", "magnet", "thermometer", "medkit", "fitness", "nutrition", "restaurant", "earth",
    "globe", "airplane", "boat", "train", "car", "hammer", "construct", "hardware-chip", "wifi",
    "code-slash", "lock-closed", "key", "people", "person", "chatbubbles", "school", "library",
    "hourglass", "calendar", "star", "moon", "snow", "rainy", "thunderstorm", "pulse", "skull",
    "shield", "trophy", "game-controller", "camera", "film", "mic", "pricetag", "wallet", "layers",
]

FALLBACK_HERO = {
    "economia": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=80&auto=format&fit=crop",
    "arte": "https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1200&q=80&auto=format&fit=crop",
    "geografia": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1200&q=80&auto=format&fit=crop",
    "sport": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1200&q=80&auto=format&fit=crop",
}

SYSTEM = (
    "You are the senior editor of P^USE, a premium Italian micro-learning app that replaces doom-scrolling "
    "with short, accurate, fascinating explainers. You write clean, vivid, factual prose with zero errors, "
    "for curious adults. You always answer with valid JSON only, no markdown fences, no commentary."
)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60]


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start:end + 1])


async def ask(session_id: str, prompt: str, retries: int = 3) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"{session_id}-{attempt}", system_message=SYSTEM)
            chat.with_model(*MODEL)
            raw = await chat.send_message(UserMessage(text=prompt))
            return parse_json(raw)
        except Exception as e:  # noqa: BLE001
            last_err = e
            await asyncio.sleep(2 + attempt * 3)
    raise RuntimeError(f"LLM failed for {session_id}: {last_err}")


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------

def topics_prompt(cat, existing_titles, n, kind):
    what = (
        "surprising 'why/how' questions or counter-intuitive facts a curious adult would love to understand in 3 minutes"
        if kind == "story" else
        "practical mini-lessons that teach ONE clear, useful concept step by step in ~4 minutes"
    )
    return (
        f"Category: {cat['name']} ({cat['name_en']}). Propose {n} NEW {kind} topics for this category — {what}. "
        "Avoid anything overlapping with these existing titles:\n- " + "\n- ".join(existing_titles or ["(none)"]) +
        "\n\nRules: varied sub-themes, concrete, verifiable, no clickbait, no duplicates, titles that make people want to tap. "
        "Return JSON: {\"topics\": [{\"title_it\": \"...\", \"title_en\": \"...\"}]}"
    )


def story_prompt(cat, title_it, title_en):
    return (
        f"Write a complete bilingual P^USE curiosity for the category '{cat['name']}' / '{cat['name_en']}'.\n"
        f"Italian title: {title_it}\nEnglish title: {title_en}\n\n"
        "Structure (identical in both languages):\n"
        "- hook: 1-2 sentences (max 180 chars) that make the reader want to know more.\n"
        "- highlight_words: 1-3 words that literally appear in the title of that language.\n"
        "- chapters: EXACTLY 6 (no more, no less), from basics -> core idea -> deeper details -> surprising extras. "
        "Each chapter: short title (max 45 chars) + body of 90-130 words, factual, accurate, engaging, no bullet points.\n"
        "- summary: one memorable sentence (max 170 chars) — the takeaway.\n"
        f"- chapter_icons: 6 icon names, one per chapter, ONLY from: {', '.join(CHAPTER_ICONS)}\n"
        "Return JSON: {\"it\": {\"title\", \"highlight_words\", \"hook\", \"chapters\": [{\"title\", \"body\"}], \"summary\"}, "
        "\"en\": {same keys}, \"chapter_icons\": [...]}"
    )


def lesson_prompt(cat, title_it, title_en):
    return (
        f"Write a complete bilingual P^USE MINI-LESSON for the category '{cat['name']}' / '{cat['name_en']}'.\n"
        f"Italian title: {title_it}\nEnglish title: {title_en}\n\n"
        "A mini-lesson teaches ONE useful concept in clear, guided steps. Structure (identical in both languages):\n"
        "- hook: 1-2 sentences (max 180 chars) that promise what the reader will be able to do.\n"
        "- objective: one sentence stating the concrete skill/understanding gained ('Capirai...', 'You'll understand...').\n"
        "- highlight_words: 1-3 words that literally appear in the title of that language.\n"
        "- chapters: EXACTLY 6 ordered STEPS (no more, no less). Each step: short title (max 45 chars) + body of 90-130 words, "
        "concrete, with a small example, building on the previous step, no bullet lists.\n"
        "- summary: one memorable sentence (max 170 chars) — the key takeaway.\n"
        f"- chapter_icons: 6 icon names, one per step, ONLY from: {', '.join(CHAPTER_ICONS)}\n"
        "Return JSON: {\"it\": {\"title\", \"highlight_words\", \"hook\", \"objective\", \"chapters\": [{\"title\", \"body\"}], \"summary\"}, "
        "\"en\": {same keys}, \"chapter_icons\": [...]}"
    )


# --------------------------------------------------------------------------
# Creation
# --------------------------------------------------------------------------

async def create_for_category(db, cat, kind, target, sem, fallback_hero, results):
    n_chapters = 6
    existing = await db.stories.find(
        {"category_id": cat["id"], "kind": kind}, {"_id": 0, "title": 1, "id": 1}
    ).to_list(500)
    missing = target - len(existing)
    if missing <= 0:
        print(f"[{kind}] {cat['id']}: already {len(existing)} (target {target})")
        return
    print(f"[{kind}] {cat['id']}: need {missing} (have {len(existing)})")
    async with sem:
        data = await ask(f"topics-{kind}-{cat['id']}", topics_prompt(cat, [e["title"] for e in existing], missing, kind))
    topics = data["topics"][:missing]
    existing_ids = {e["id"] for e in existing}

    async def one(topic):
        async with sem:
            sid = slugify(topic["title_en"]) or slugify(topic["title_it"])
            sid = f"gen-{kind}-{sid}"
            if sid in existing_ids:
                sid = f"{sid}-{cat['id']}"
            try:
                prompt = story_prompt(cat, topic["title_it"], topic["title_en"]) if kind == "story" \
                    else lesson_prompt(cat, topic["title_it"], topic["title_en"])
                d = await ask(f"{kind}-{sid}", prompt)
                it, en = d["it"], d["en"]
                assert len(it["chapters"]) == n_chapters and len(en["chapters"]) == n_chapters, \
                    f"need {n_chapters} chapters"
                icons = d.get("chapter_icons") or []
                chapters = []
                for i, ch in enumerate(it["chapters"]):
                    icon = icons[i] if i < len(icons) and icons[i] in CHAPTER_ICONS else CHAPTER_ICONS[i % len(CHAPTER_ICONS)]
                    chapters.append({"number": i + 1, "title": ch["title"], "body": ch["body"], "icon": icon, "glow_color": GLOWS[i % len(GLOWS)]})
                en_tr = {
                    "title": en["title"], "highlight_words": en.get("highlight_words", [])[:3], "hook": en["hook"],
                    "category_name": cat["name_en"],
                    "chapters": [{"title": c["title"], "body": c["body"]} for c in en["chapters"]],
                    "summary": en["summary"],
                }
                doc = {
                    "id": sid,
                    "category_id": cat["id"],
                    "category_name": cat["name"],
                    "category_icon": cat["icon"],
                    "category_color": cat["color"],
                    "title": it["title"],
                    "highlight_words": it.get("highlight_words", [])[:3],
                    "hook": it["hook"],
                    "hero_image": fallback_hero,
                    "reading_time_min": 2 if kind == "story" else 3,
                    "deep_dive_time_min": 3 if kind == "story" else 4,
                    "chapters": chapters,
                    "summary": it["summary"],
                    "kind": kind,
                    "created_at": OLD_DT,
                    "translations": {"en": en_tr},
                    "ai_generated": True,
                    "chapters_v6": True,
                }
                if kind == "lesson":
                    doc["objective"] = it.get("objective", "")
                    en_tr["objective"] = en.get("objective", "")
                await db.stories.update_one({"id": sid}, {"$setOnInsert": doc}, upsert=True)
                results["ok"] += 1
                print(f"[{kind}] OK   {cat['id']}/{sid}")
            except Exception as e:  # noqa: BLE001
                results["fail"] += 1
                print(f"[{kind}] FAIL {cat['id']}/{sid}: {e}")

    await asyncio.gather(*(one(t) for t in topics))


async def run(db, kind, target, sem):
    results = {"ok": 0, "fail": 0}
    cats = await db.categories.find({}, {"_id": 0}).to_list(100)
    for cat in cats:
        sample = await db.stories.find_one({"category_id": cat["id"]}, {"_id": 0, "hero_image": 1})
        fallback = FALLBACK_HERO.get(cat["id"]) or (sample or {}).get("hero_image") or FALLBACK_HERO["geografia"]
        try:
            await create_for_category(db, cat, kind, target, sem, fallback, results)
        except Exception as e:  # noqa: BLE001
            print(f"[{kind}] FAIL category {cat['id']}: {e}")
    print(f"[{kind}] DONE ok={results['ok']} fail={results['fail']}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["story", "lesson", "both"], default="both")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    sem = asyncio.Semaphore(CONCURRENCY)
    if args.kind in ("story", "both"):
        await run(db, "story", TARGET_STORY, sem)
    if args.kind in ("lesson", "both"):
        await run(db, "lesson", TARGET_LESSON, sem)
    print("[all done]")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
