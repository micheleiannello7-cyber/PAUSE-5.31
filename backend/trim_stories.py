"""PAUSE — "limatura" pass: bring every story's narration under 4 minutes.

Long chapters are condensed (same facts, same tone, same chapter titles, same
language) so the estimated TTS duration used by the app (`_estimated_audio_minutes`)
never exceeds MAX_MINUTES. Titles, highlight words, categories and covers are
untouched. Nothing is deleted: the original document is copied once into
`stories_backup_pre_trim` before the first change, and `content_trimmed`
records what was done per language.

Usage (from backend/):
    python trim_stories.py --dry-run           # report only
    python trim_stories.py --limit 5            # try a few
    python trim_stories.py                      # all stories over budget
    python trim_stories.py --restore <story-id> # put the backup back
"""
import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from server import _estimated_audio_minutes, _localize, _clean_for_estimate  # noqa: E402

MODEL = ("openai", "gpt-5.4")  # same editor model used to generate the catalogue
# Regola editoriale: curiosità e mini lezioni tra 3 e 5 minuti (badge = stima TTS, ceil).
MAX_MINUTES = 5
# 5 min = 300 s at 12.5 chars/s minus chapter/intro pauses (~10.5 s) ≈ 3620 chars.
# Aim lower so the ceil() estimate lands safely at ≤ 5 min.
TARGET_CHARS = 3200
HARD_LIMIT_CHARS = 3550
CONCURRENCY = 4
BACKUP = "stories_backup_pre_trim"
# Sorgenti seed in JSON: il testo accorciato viene riscritto anche lì, così un
# nuovo ambiente (fork/deploy) riparte già con la versione corta.
SOURCE_JSONS = [ROOT / "v8_content.json", ROOT / "v9_content.json"]

SYSTEM = (
    "You are the senior editor of PAUSE, a premium micro-learning app. You tighten existing explainers "
    "so they read in under five minutes, without changing what they say. You never add facts, never "
    "remove a key idea, never change the language, tone or point of view, and you keep the prose vivid "
    "and precise. You answer with valid JSON only, no markdown fences, no commentary."
)

PROMPT = """Condense this {lang_name} story so the whole narration (hook + 6 chapters + summary) fits in
at most {budget} characters in total (currently {current} characters). Keep it {lang_name}.

Rules:
- Keep all 6 chapters, in order, with EXACTLY the same "title" values.
- Shorten each "body" by cutting repetition, filler, long asides and redundant examples. Keep the
  facts, numbers, names and the logical thread intact. Do not invent anything.
- Each body must stay a complete, fluent paragraph of at least 2 sentences (aim for {per_chapter} characters).
- "hook" and "summary" may be tightened slightly but must keep their meaning.
- Preserve the original register (second person, warm, curious).

Return JSON with this exact shape:
{{"hook": "...", "chapters": [{{"title": "...", "body": "..."}} x6], "summary": "..."}}

Story:
{payload}"""

LANG_NAME = {"it": "Italian", "en": "English"}


def total_chars(doc: dict) -> int:
    parts = [doc.get("title", ""), doc.get("hook", ""), doc.get("summary", "")]
    parts += [c.get("title", "") + c.get("body", "") for c in doc.get("chapters", [])]
    return sum(len(_clean_for_estimate(p)) for p in parts)


def parse_json(raw: str) -> dict:
    raw = re.sub(r"^```(?:json)?", "", raw.strip()).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])


def localized_view(doc: dict, lang: str) -> dict:
    """Narrated fields for one language (EN comes from translations.en)."""
    loc = _localize(doc, lang)
    return {
        "title": loc.get("title", ""), "hook": loc.get("hook", ""), "summary": loc.get("summary", ""),
        "chapters": [{"title": c.get("title", ""), "body": c.get("body", "")} for c in loc.get("chapters", [])],
    }


def has_own_translation(doc: dict, lang: str) -> bool:
    return lang == "it" or bool((doc.get("translations") or {}).get(lang, {}).get("chapters"))


def apply_trim(view: dict, result: dict) -> dict:
    out = dict(view)
    out["hook"] = result["hook"].strip()
    out["summary"] = result["summary"].strip()
    out["chapters"] = [
        {"title": v["title"], "body": r["body"].strip()} for v, r in zip(view["chapters"], result["chapters"])
    ]
    return out


def validate(view: dict, result: dict) -> str | None:
    chs = result.get("chapters")
    if not isinstance(chs, list) or len(chs) != len(view["chapters"]):
        return "chapter count changed"
    for v, r in zip(view["chapters"], chs):
        if not isinstance(r.get("body"), str) or len(r["body"].strip()) < 80:
            return "chapter body too short"
        if r.get("title", "").strip() != v["title"].strip():
            return "chapter title changed"
    if not result.get("hook") or not result.get("summary"):
        return "missing hook/summary"
    trimmed = apply_trim(view, result)
    if _estimated_audio_minutes(trimmed) > MAX_MINUTES or total_chars(trimmed) > HARD_LIMIT_CHARS:
        return f"still too long ({total_chars(trimmed)} chars, {_estimated_audio_minutes(trimmed)} min)"
    return None


async def condense(story_id: str, lang: str, view: dict) -> dict:
    current = total_chars(view)
    budget = TARGET_CHARS
    last = "no attempt"
    for attempt in range(4):
        per_chapter = max(220, (budget - len(view["hook"]) - len(view["summary"]) - len(view["title"])) // 6 - 10)
        payload = json.dumps({k: view[k] for k in ("hook", "chapters", "summary")}, ensure_ascii=False, indent=1)
        prompt = PROMPT.format(lang_name=LANG_NAME[lang], budget=budget, current=current, per_chapter=per_chapter, payload=payload)
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"trim-{story_id}-{lang}-{attempt}", system_message=SYSTEM)
        chat.with_model(*MODEL)
        try:
            result = parse_json(await chat.send_message(UserMessage(text=prompt)))
        except Exception as exc:  # network / JSON
            last = f"llm error: {exc}"
            continue
        err = validate(view, result)
        if err is None:
            return result
        last = err
        budget -= 200  # ask for a tighter cut next time
    raise RuntimeError(f"{story_id}/{lang}: {last}")


def set_fields(lang: str, trimmed: dict, original_chapters: list[dict]) -> dict:
    """Mongo $set for one language. Chapter icons/glow/number are kept."""
    if lang == "it":
        chapters = [{**orig, "body": t["body"]} for orig, t in zip(original_chapters, trimmed["chapters"])]
        return {"hook": trimmed["hook"], "summary": trimmed["summary"], "chapters": chapters}
    return {
        f"translations.{lang}.hook": trimmed["hook"],
        f"translations.{lang}.summary": trimmed["summary"],
        f"translations.{lang}.chapters": [
            {**orig, "body": t["body"]} for orig, t in zip(original_chapters, trimmed["chapters"])
        ],
    }


async def process(db, doc: dict, lang: str, dry_run: bool, sem: asyncio.Semaphore) -> tuple[str, str, str]:
    sid = doc["id"]
    view = localized_view(doc, lang)
    before_min, before_chars = _estimated_audio_minutes(view), total_chars(view)
    if before_min <= MAX_MINUTES:
        return sid, lang, "ok"
    if dry_run:
        return sid, lang, f"would trim ({before_min} min, {before_chars} chars)"
    async with sem:
        try:
            result = await condense(sid, lang, view)
        except Exception as exc:
            return sid, lang, f"FAILED {exc}"
    trimmed = apply_trim(view, result)
    after_min, after_chars = _estimated_audio_minutes(trimmed), total_chars(trimmed)

    # Backup once per story, before the first modification of any language.
    if not await db[BACKUP].find_one({"id": sid}, {"_id": 1}):
        original = await db.stories.find_one({"id": sid}, {"_id": 0})
        await db[BACKUP].insert_one({**original, "backed_up_at": datetime.now(timezone.utc)})

    original_chapters = doc["chapters"] if lang == "it" else doc["translations"][lang]["chapters"]
    fields = set_fields(lang, trimmed, original_chapters)
    fields[f"content_trimmed.{lang}"] = {
        "at": datetime.now(timezone.utc), "model": "/".join(MODEL),
        "from_chars": before_chars, "to_chars": after_chars, "from_min": before_min, "to_min": after_min,
    }
    fields["chapters_v6"] = True
    await db.stories.update_one({"id": sid}, {"$set": fields})
    sync_source_json(sid, lang, trimmed)
    return sid, lang, f"trimmed {before_min}→{after_min} min ({before_chars}→{after_chars} chars)"


def sync_source_json(sid: str, lang: str, trimmed: dict) -> None:
    """Riscrive hook/summary/body accorciati nel JSON seed che contiene la storia (se esiste)."""
    for path in SOURCE_JSONS:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        entry = data.get(sid)
        if not entry or lang not in entry:
            continue
        block = entry[lang]
        block["hook"], block["summary"] = trimmed["hook"], trimmed["summary"]
        for ch, t in zip(block["chapters"], trimmed["chapters"]):
            ch["body"] = t["body"]
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        tmp.replace(path)
        return


async def restore(db, story_id: str) -> None:
    backup = await db[BACKUP].find_one({"id": story_id}, {"_id": 0, "backed_up_at": 0})
    if not backup:
        print(f"no backup for {story_id}")
        return
    await db.stories.replace_one({"id": story_id}, backup)
    print(f"restored {story_id} from backup")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only", help="comma-separated story ids")
    parser.add_argument("--restore", help="story id to restore from backup")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    if args.restore:
        await restore(db, args.restore)
        return

    query = {"id": {"$in": args.only.split(",")}} if args.only else {}
    docs = await db.stories.find(query, {"_id": 0}).to_list(5000)
    jobs = [(d, lang) for d in docs for lang in ("it", "en") if has_own_translation(d, lang)]
    jobs = [(d, lang) for d, lang in jobs if _estimated_audio_minutes(localized_view(d, lang)) > MAX_MINUTES]
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"{len(docs)} stories, {len(jobs)} narrations over {MAX_MINUTES} min", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*[process(db, d, lang, args.dry_run, sem) for d, lang in jobs])
    failed = 0
    for sid, lang, status in results:
        print(f"{sid} [{lang}] {status}", flush=True)
        failed += status.startswith("FAILED")
    print(f"done: {len(results) - failed} ok, {failed} failed", flush=True)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
