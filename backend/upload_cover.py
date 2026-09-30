"""
Upload an externally-made cover for a story (or category) into Object Storage
and link it in MongoDB.

Usage:
    cd /app/backend && python upload_cover.py <story-id> <file-or-url>
    cd /app/backend && python upload_cover.py --category <category-id> <file-or-url>
"""
import asyncio
import mimetypes
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from storage import put_object, APP_NAME  # noqa: E402


def read_source(src: str) -> tuple[bytes, str]:
    if src.startswith("http://") or src.startswith("https://"):
        r = requests.get(src, timeout=60)
        r.raise_for_status()
        return r.content, r.headers.get("Content-Type", "image/jpeg").split(";")[0]
    data = Path(src).read_bytes()
    return data, mimetypes.guess_type(src)[0] or "image/jpeg"


async def main():
    args = sys.argv[1:]
    is_cat = "--category" in args
    if is_cat:
        args.remove("--category")
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)
    target_id, src = args

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    coll, field, folder = ("categories", "illustration_generated", "category") if is_cat else ("stories", "hero_image_generated", "hero")

    if not await db[coll].find_one({"id": target_id}, {"_id": 1}):
        print(f"ERROR: {coll[:-1]} '{target_id}' not found")
        sys.exit(1)

    data, mime = read_source(src)
    if is_cat:
        ext = "jpg" if "jpeg" in mime else mime.split("/")[-1]
        path = f"{APP_NAME}/{folder}/{target_id}.{ext}"
        put_object(path, data, mime)
        await db[coll].update_one({"id": target_id}, {"$set": {field: path}})
        print(f"OK {target_id} -> {path} ({len(data)//1024} KB, {mime})")
    else:
        # Stories: WebP hero + thumb at content-addressed paths (see media_opt).
        from media_opt import upload_cover
        fields = upload_cover(target_id, data)
        await db[coll].update_one({"id": target_id}, {"$set": fields})
        b = fields["hero_bytes"]
        print(f"OK {target_id} -> {fields['hero_image_generated']} (source {b['source']//1024} KB → hero {b['hero']//1024} KB, thumb {b['thumb']//1024} KB)")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
