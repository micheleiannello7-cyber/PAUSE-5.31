"""Audit contenuti: per categoria conta storie/lezioni, capitoli, copertine."""
import os, asyncio
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "pause")]
    cats = await db.categories.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(None)
    print(f"{'cat':<14}{'tot':>4}{'stories':>8}{'lessons':>8}  chapters  heroes  langs")
    for c in cats:
        st = await db.stories.find({"category_id": c["id"]}, {"_id": 0, "kind": 1, "chapters": 1, "hero_image_generated": 1, "lang": 1, "id": 1}).to_list(None)
        kinds = Counter(s.get("kind", "story") for s in st)
        ch = Counter(len(s.get("chapters", [])) for s in st)
        heroes = sum(1 for s in st if s.get("hero_image_generated"))
        langs = Counter(s.get("lang", "?") for s in st)
        print(f"{c['id']:<14}{len(st):>4}{kinds.get('story',0):>8}{kinds.get('lesson',0):>8}  {dict(sorted(ch.items()))}  {heroes}  {dict(langs)}")
    s = await db.stories.find_one({}, {"_id": 0})
    print("\nFIELDS:", {k: (v if isinstance(v, (int, float, bool)) or (isinstance(v, str) and len(v) < 40) else type(v).__name__) for k, v in s.items()})
    print("CHAPTER KEYS:", list(s["chapters"][0].keys()))
    print("N stories total:", await db.stories.count_documents({}))


asyncio.run(main())
