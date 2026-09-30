"""
PAUSE — AI content pipeline (GPT-5.4 via emergentintegrations).

1. Translate every existing Italian story to English   -> doc["translations"]["en"]
2. Fill each category up to TARGET stories with new bilingual stories (IT + EN)
3. Store an `image_prompt` per story for generate_images.py

Idempotent: reruns only do the missing work. Progress is logged to stdout.

Usage:
    cd /app/backend && python generate_content.py                # everything
    cd /app/backend && python generate_content.py --step translate
    cd /app/backend && python generate_content.py --step create --target 20
"""
import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from seed_data import CATEGORIES, GLOWS  # noqa: E402

MODEL = ("openai", "gpt-5.4")
CONCURRENCY = 4
TARGET_DEFAULT = 20

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

# Fallback covers per category (used until the AI cover is generated).
FALLBACK_HERO = {
    "economia": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=80&auto=format&fit=crop",
    "arte": "https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1200&q=80&auto=format&fit=crop",
    "geografia": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1200&q=80&auto=format&fit=crop",
}

SYSTEM = (
    "You are the senior editor of PAUSE, a premium Italian micro-learning app that replaces doom-scrolling "
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
    last_err: Exception | None = None
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
# Step 1 — translate existing stories
# --------------------------------------------------------------------------

def translate_prompt(story: dict) -> str:
    payload = {
        "title": story["title"],
        "highlight_words": story.get("highlight_words", []),
        "hook": story["hook"],
        "category_name": story.get("category_name", ""),
        "chapters": [{"title": c["title"], "body": c["body"]} for c in story["chapters"]],
        "summary": story["summary"],
    }
    return (
        "Translate this Italian story into flawless, natural British/International English for an educated audience. "
        "Keep the same structure, the same number of chapters, the same meaning and tone (curious, precise, warm). "
        "highlight_words must be 1-3 words that literally appear in your English title. "
        "Return JSON with exactly the same keys and shapes.\n\n" + json.dumps(payload, ensure_ascii=False)
    )


async def translate_all(db, sem: asyncio.Semaphore):
    stories = await db.stories.find({"translations.en": {"$exists": False}}, {"_id": 0}).to_list(2000)
    print(f"[translate] {len(stories)} stories need English")

    async def one(story):
        async with sem:
            sid = story["id"]
            try:
                tr = await ask(f"tr-{sid}", translate_prompt(story))
                assert len(tr["chapters"]) == len(story["chapters"]), "chapter count mismatch"
                await db.stories.update_one({"id": sid}, {"$set": {"translations.en": tr}})
                print(f"[translate] OK   {sid}")
            except Exception as e:  # noqa: BLE001
                print(f"[translate] FAIL {sid}: {e}")

    await asyncio.gather(*(one(s) for s in stories))


# --------------------------------------------------------------------------
# Step 2 — create new bilingual stories
# --------------------------------------------------------------------------

def topics_prompt(cat: dict, existing_titles: list[str], n: int) -> str:
    return (
        f"Category: {cat['name']} ({cat['name_en']}). Propose {n} NEW story topics for this category, each a "
        "surprising 'why/how' question or a counter-intuitive fact that a curious adult would love to understand in 3 minutes. "
        "Avoid anything overlapping with these existing titles:\n- " + "\n- ".join(existing_titles or ["(none)"]) +
        "\n\nRules: varied sub-themes, concrete, verifiable science/history/culture, no clickbait, no duplicates. "
        "Return JSON: {\"topics\": [{\"title_it\": \"...\", \"title_en\": \"...\"}]}"
    )


def story_prompt(cat: dict, title_it: str, title_en: str) -> str:
    return (
        f"Write a complete bilingual PAUSE story for the category '{cat['name']}' / '{cat['name_en']}'.\n"
        f"Italian title: {title_it}\nEnglish title: {title_en}\n\n"
        "Structure (identical in both languages):\n"
        "- hook: 1-2 sentences (max 180 chars) that make the reader want to know more.\n"
        "- highlight_words: 1-3 words that literally appear in the title of that language.\n"
        "- chapters: exactly 6, ordered from the basics -> the core concept -> deeper details -> surprising extras. "
        "Each chapter: short title (max 45 chars) + body of 90-130 words, factual, accurate, engaging, no bullet points.\n"
        "- summary: one memorable sentence (max 170 chars) — the 'Da ricordare' takeaway.\n"
        f"- chapter_icons: 6 icon names, one per chapter, chosen ONLY from: {', '.join(CHAPTER_ICONS)}\n"
        "- image_prompt: an English prompt for a dark, cinematic, photorealistic editorial cover image that visually "
        "represents THIS topic (no text, no letters, no people faces close-up), vertical 3:4, moody premium lighting.\n\n"
        "Return JSON: {\"it\": {\"title\", \"highlight_words\", \"hook\", \"chapters\": [{\"title\", \"body\"}], \"summary\"}, "
        "\"en\": {same keys}, \"chapter_icons\": [...], \"image_prompt\": \"...\"}"
    )


async def create_for_category(db, cat: dict, target: int, sem: asyncio.Semaphore, fallback_hero: str, add: int = 0):
    existing = await db.stories.find({"category_id": cat["id"]}, {"_id": 0, "title": 1, "id": 1}).to_list(500)
    missing = add if add > 0 else target - len(existing)
    if missing <= 0:
        print(f"[create] {cat['id']}: already {len(existing)} stories")
        return
    print(f"[create] {cat['id']}: need {missing} new stories")
    async with sem:
        data = await ask(f"topics-{cat['id']}", topics_prompt(cat, [e["title"] for e in existing], missing))
    topics = data["topics"][:missing]
    existing_ids = {e["id"] for e in existing}

    async def one(topic):
        async with sem:
            sid = slugify(topic["title_en"])
            if not sid or sid in existing_ids:
                sid = slugify(topic["title_en"]) + "-" + cat["id"]
            try:
                d = await ask(f"story-{sid}", story_prompt(cat, topic["title_it"], topic["title_en"]))
                it, en = d["it"], d["en"]
                assert len(it["chapters"]) == 6 and len(en["chapters"]) == 6, "need 6 chapters"
                icons = d.get("chapter_icons") or []
                chapters = []
                for i, ch in enumerate(it["chapters"]):
                    icon = icons[i] if i < len(icons) and icons[i] in CHAPTER_ICONS else CHAPTER_ICONS[i % 7]
                    chapters.append({"number": i + 1, "title": ch["title"], "body": ch["body"], "icon": icon, "glow_color": GLOWS[i % len(GLOWS)]})
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
                    "reading_time_min": 2,
                    "deep_dive_time_min": 3,
                    "chapters": chapters,
                    "summary": it["summary"],
                    "image_prompt": d.get("image_prompt", ""),
                    "translations": {"en": {
                        "title": en["title"], "highlight_words": en.get("highlight_words", [])[:3], "hook": en["hook"],
                        "category_name": cat["name_en"],
                        "chapters": [{"title": c["title"], "body": c["body"]} for c in en["chapters"]],
                        "summary": en["summary"],
                    }},
                    "ai_generated": True,
                }
                await db.stories.update_one({"id": sid}, {"$setOnInsert": doc}, upsert=True)
                print(f"[create] OK   {cat['id']}/{sid}")
            except Exception as e:  # noqa: BLE001
                print(f"[create] FAIL {cat['id']}/{sid}: {e}")

    await asyncio.gather(*(one(t) for t in topics))


async def create_all(db, target: int, sem: asyncio.Semaphore, add: int = 0):
    cats = await db.categories.find({}, {"_id": 0}).to_list(100)
    for cat in cats:
        sample = await db.stories.find_one({"category_id": cat["id"]}, {"_id": 0, "hero_image": 1})
        fallback = FALLBACK_HERO.get(cat["id"]) or (sample or {}).get("hero_image") or FALLBACK_HERO["geografia"]
        try:
            await create_for_category(db, cat, target, sem, fallback, add=add)
        except Exception as e:  # noqa: BLE001
            print(f"[create] FAIL category {cat['id']}: {e}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["translate", "create", "all"], default="all")
    parser.add_argument("--target", type=int, default=TARGET_DEFAULT)
    parser.add_argument("--add", type=int, default=0, help="Add exactly N new stories to every category")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    # make sure new categories exist
    for c in CATEGORIES:
        await db.categories.update_one({"id": c["id"]}, {"$set": c}, upsert=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    if args.step in ("translate", "all"):
        await translate_all(db, sem)
    if args.step in ("create", "all"):
        await create_all(db, args.target, sem, add=args.add)
        # newly created stories already carry EN; nothing else to translate
    print("[done]")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
