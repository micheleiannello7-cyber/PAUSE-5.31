"""Dump compatto dei contenuti con < 6 capitoli per una categoria (per scrivere i v6)."""
import os, sys, asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


async def main(cat):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    st = await db.stories.find({"category_id": cat}, {"_id": 0, "id": 1, "kind": 1, "title": 1, "hook": 1, "chapters": 1, "translations.en": 1, "summary": 1}).to_list(None)
    for s in st:
        n = len(s["chapters"])
        if n >= 6:
            continue
        en = (s.get("translations") or {}).get("en")
        print(f"\n### {s['id']} [{s['kind']}] n={n} en={'Y' if en else 'N'} (en_ch={len(en['chapters']) if en else 0})")
        print("T:", s["title"])
        print("H:", s["hook"])
        for c in s["chapters"]:
            print(f"  {c['number']}. {c['title']} :: {c['body'][:110]}...")
        print("S:", s["summary"][:160])


asyncio.run(main(sys.argv[1]))
