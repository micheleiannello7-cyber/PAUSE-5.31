"""Persist reviewed cover exclusions without changing story text or valid replacements."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


async def apply_cover_exclusions(db):
    exclusions = json.loads((ROOT / "cover_exclusions.json").read_text())
    audit = ROOT.parent / "cover_audit"
    if (audit / "decisions.json").exists():
        decisions = json.loads((audit / "decisions.json").read_text())
        catalog = json.loads((audit / "catalog.json").read_text())
        for group in catalog["groups"]:
            decision = decisions.get(str(group["group"]))
            if not decision:
                continue
            for doc in group["stories"]:
                if doc["id"] in decision["keep"]:
                    continue
                field = "hero_image_generated" if doc.get("hero_image_generated") else "hero_image"
                exclusions[doc["id"]] = {field: doc[field], "reason": decision["reason"]}
    removed = 0
    for sid, review in exclusions.items():
        for field in ("hero_image", "hero_image_generated"):
            if not review.get(field):
                continue
            values = {field: "", "cover_review_reason": review["reason"]}
            if field == "hero_image_generated":
                values.update({"hero_variants": {}, "hero_bytes": {}, "hero_image_thumb": None})
            result = await db.stories.update_one({"id": sid, field: review[field]}, {"$set": values})
            removed += result.modified_count
    return removed


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        print("Removed:", await apply_cover_exclusions(client[os.environ["DB_NAME"]]))
    finally:
        client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())