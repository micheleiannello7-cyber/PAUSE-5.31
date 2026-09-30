"""
P^USE — normalizza OGNI contenuto (curiosità e mini lezioni) a ESATTAMENTE 6 capitoli.

Per ogni documento con meno di 6 capitoli (IT o EN) chiede a GPT-5.4 di riscrivere
il corpo in 6 capitoli, conservando tutti i fatti esistenti e approfondendo dove
serve. Titolo, hook, summary e obiettivo restano invariati.

I documenti aggiornati ricevono il flag `chapters_v6: True`, che `ensure_seed`
usa per NON sovrascrivere i capitoli con quelli dei file seed al riavvio.

Idempotente: i documenti già a 6 capitoli vengono saltati.

Usage:
    cd /app/backend && python normalize_chapters.py            # tutto
    cd /app/backend && python normalize_chapters.py --only <id>
    cd /app/backend && python normalize_chapters.py --category sport
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from generate_fill import CHAPTER_ICONS, ask  # noqa: E402
from seed_data import GLOWS  # noqa: E402

N = 6
CONCURRENCY = 6


def prompt_for(doc: dict) -> str:
    kind = doc.get("kind", "story")
    en = (doc.get("translations") or {}).get("en")
    unit = "STEPS of a mini-lesson (each step builds on the previous one, with a small concrete example)" \
        if kind == "lesson" else "chapters of a curiosity (basics -> core idea -> deeper details -> surprising extras)"
    payload = {
        "it": {"title": doc["title"], "hook": doc.get("hook", ""), "summary": doc.get("summary", ""),
               "chapters": [{"title": c["title"], "body": c["body"]} for c in doc["chapters"]]},
    }
    if en:
        payload["en"] = {"title": en.get("title", ""), "hook": en.get("hook", ""), "summary": en.get("summary", ""),
                         "chapters": [{"title": c.get("title", ""), "body": c.get("body", "")} for c in en.get("chapters", [])]}
    langs = "Italian AND English (the English version must be a faithful translation of the Italian one, same 6 chapters)" \
        if en else "Italian only"
    import json
    return (
        f"Below is an existing P^USE {kind} for the category '{doc.get('category_name', '')}' with only "
        f"{len(doc['chapters'])} chapters. Rewrite its body so it has EXACTLY {N} {unit}, in {langs}.\n\n"
        "Rules:\n"
        "- Keep EVERY fact already present; redistribute and deepen the content, add accurate, verifiable detail where needed.\n"
        "- Each chapter: short title (max 45 chars) + body of 90-130 words, vivid, factual, no bullet points.\n"
        "- Do NOT change title, hook or summary — return them unchanged.\n"
        f"- chapter_icons: exactly {N} icon names, one per chapter, ONLY from: {', '.join(CHAPTER_ICONS)}\n"
        f"- The chapters array MUST contain exactly {N} items in every language. No more, no less.\n\n"
        f"CURRENT CONTENT:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Return JSON: {\"it\": {\"chapters\": [{\"title\", \"body\"}]}"
        + (", \"en\": {\"chapters\": [{\"title\", \"body\"}]}" if en else "")
        + ", \"chapter_icons\": [...]}"
    )


def needs_fix(doc: dict) -> bool:
    if len(doc.get("chapters") or []) != N:
        return True
    en = (doc.get("translations") or {}).get("en")
    return bool(en) and len(en.get("chapters") or []) != N


async def fix_one(db, doc, sem, results):
    sid = doc["id"]
    async with sem:
        try:
            d = await ask(f"norm6-{sid}", prompt_for(doc))
            it_ch = d["it"]["chapters"]
            assert len(it_ch) == N, f"IT has {len(it_ch)} chapters"
            icons = d.get("chapter_icons") or []
            old_icons = [c.get("icon") for c in doc["chapters"]]
            chapters = []
            for i, ch in enumerate(it_ch):
                icon = icons[i] if i < len(icons) and icons[i] in CHAPTER_ICONS else (
                    old_icons[i] if i < len(old_icons) and old_icons[i] else CHAPTER_ICONS[i % len(CHAPTER_ICONS)])
                chapters.append({"number": i + 1, "title": ch["title"], "body": ch["body"],
                                 "icon": icon, "glow_color": GLOWS[i % len(GLOWS)]})
            update = {"chapters": chapters, "chapters_v6": True,
                      "reading_time_min": 2 if doc.get("kind", "story") == "story" else 3,
                      "deep_dive_time_min": 3 if doc.get("kind", "story") == "story" else 4}
            if (doc.get("translations") or {}).get("en"):
                en_ch = d["en"]["chapters"]
                assert len(en_ch) == N, f"EN has {len(en_ch)} chapters"
                update["translations.en.chapters"] = [{"title": c["title"], "body": c["body"]} for c in en_ch]
            await db.stories.update_one({"id": sid}, {"$set": update})
            results["ok"] += 1
            print(f"OK   {doc.get('category_id')}/{sid}: {len(doc['chapters'])} -> {N}")
        except Exception as e:  # noqa: BLE001
            results["fail"] += 1
            print(f"FAIL {doc.get('category_id')}/{sid}: {e}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    parser.add_argument("--category")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    query = {}
    if args.only:
        query["id"] = args.only
    if args.category:
        query["category_id"] = args.category
    docs = await db.stories.find(query, {"_id": 0}).to_list(5000)
    todo = [d for d in docs if needs_fix(d)]
    print(f"{len(todo)} / {len(docs)} contents need normalization to {N} chapters")
    sem = asyncio.Semaphore(CONCURRENCY)
    results = {"ok": 0, "fail": 0}
    await asyncio.gather(*(fix_one(db, d, sem, results) for d in todo))
    print(f"DONE ok={results['ok']} fail={results['fail']}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
