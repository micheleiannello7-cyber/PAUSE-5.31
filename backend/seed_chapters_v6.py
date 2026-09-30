"""
P^USE — capitoli aggiuntivi scritti a mano per portare OGNI contenuto a 6 capitoli.

I moduli `v6_*.py` espongono un dict EXTRA = {story_id: {"it": [(title, body), ...],
"en": [(title, body), ...]}}. `apply_v6(db)` appende i capitoli mancanti (IT e, se il
doc ha una traduzione, EN), assegna icona/glow e marca il doc con `chapters_v6: True`
così `ensure_seed` non lo sovrascrive più. Idempotente: tocca solo i doc con < 6 capitoli.
"""
import importlib
import pkgutil
from pathlib import Path

from story_builder import GLOWS, ICON_POOL

N = 6
_GENERIC_ICONS = ["bulb", "sparkles", "flash", "star", "eye", "compass"]
ICON_POOL = {**ICON_POOL, "sport": ["fitness", "flame", "trophy", "heart", "pulse", "body"]}


def load_extra() -> dict:
    extra: dict = {}
    for mod in pkgutil.iter_modules([str(Path(__file__).parent)]):
        if mod.name.startswith("v6_"):
            m = importlib.import_module(mod.name)
            extra.update(getattr(m, "EXTRA", {}))
    return extra


async def apply_v6(db) -> dict:
    extra = load_extra()
    stats = {"fixed": 0, "skipped": 0, "mismatch": 0}
    for sid, add in extra.items():
        doc = await db.stories.find_one({"id": sid}, {"_id": 0, "chapters": 1, "translations": 1, "category_id": 1, "kind": 1})
        if not doc:
            stats["skipped"] += 1
            continue
        chapters = list(doc.get("chapters") or [])
        en = (doc.get("translations") or {}).get("en")
        update = {}
        need_it = N - len(chapters)
        if need_it > 0:
            it_add = add.get("it", [])
            if len(it_add) != need_it:
                print(f"[v6] IT mismatch {sid}: need {need_it}, have {len(it_add)}")
                stats["mismatch"] += 1
                continue
            pool = ICON_POOL.get(doc.get("category_id"), _GENERIC_ICONS)
            for i, (ct, cb) in enumerate(it_add):
                idx = len(chapters)
                chapters.append({"number": idx + 1, "title": ct, "body": cb,
                                 "icon": pool[idx % len(pool)], "glow_color": GLOWS[idx % len(GLOWS)]})
            update["chapters"] = chapters
        if en:
            en_ch = list(en.get("chapters") or [])
            need_en = N - len(en_ch)
            if need_en > 0:
                en_add = add.get("en", [])
                if len(en_add) != need_en:
                    print(f"[v6] EN mismatch {sid}: need {need_en}, have {len(en_add)}")
                    stats["mismatch"] += 1
                    continue
                en_ch.extend({"title": ct, "body": cb} for ct, cb in en_add)
                update["translations.en.chapters"] = en_ch
        if not update:
            stats["skipped"] += 1
            continue
        update["chapters_v6"] = True
        update["reading_time_min"] = 2 if doc.get("kind", "story") == "story" else 3
        update["deep_dive_time_min"] = 3 if doc.get("kind", "story") == "story" else 4
        await db.stories.update_one({"id": sid}, {"$set": update})
        stats["fixed"] += 1
    return stats


if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient

    load_dotenv(Path(__file__).parent / ".env")

    async def _main():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ["DB_NAME"]]
        print(await apply_v6(db))
        client.close()

    asyncio.run(_main())
