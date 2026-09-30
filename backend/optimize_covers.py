"""One-off: converte le sorgenti in backend/covers/ (PNG/JPEG) in WebP 1200px
q84 — la stessa codifica che media_opt applica prima dell'upload — e rimuove
gli originali. Aggiorna hero_source_digest sulle storie già collegate così la
sync all'avvio non ricarica nulla.

python optimize_covers.py
"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
from media_opt import HERO_MAX, encode_webp, source_digest  # noqa: E402

COVERS = ROOT / "covers"


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    before = after = 0
    for src in sorted(COVERS.iterdir()):
        if src.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        raw = src.read_bytes()
        webp = encode_webp(raw, HERO_MAX)
        dst = src.with_suffix(".webp")
        dst.write_bytes(webp)
        await db.stories.update_one(
            {"id": src.stem, "hero_source_digest": source_digest(raw)},
            {"$set": {"hero_source_digest": source_digest(webp)}},
        )
        src.unlink()
        before += len(raw)
        after += len(webp)
        print(f"{src.name} -> {dst.name}: {len(raw)//1024} KB -> {len(webp)//1024} KB")
    print(f"TOTAL {before/1e6:.1f} MB -> {after/1e6:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())
