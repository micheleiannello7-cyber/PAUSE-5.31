"""
PAUSE — copertine "locali": file in backend/covers/<story-id>.<png|jpg|jpeg|webp>
(fornite dall'utente) vengono caricate in Object Storage all'avvio e collegate
alla storia (hero_image_generated). Così le copertine viaggiano col progetto
(git/export) e sopravvivono a fork e nuovi ambienti. Idempotente: salta le
storie che hanno già una copertina nello storage.
"""
import asyncio
import logging
from pathlib import Path

from media_opt import source_digest, upload_cover

COVERS_DIR = Path(__file__).parent / "covers"
logger = logging.getLogger("covers")


def local_covers() -> dict[str, Path]:
    if not COVERS_DIR.exists():
        return {}
    out: dict[str, Path] = {}
    for p in sorted(COVERS_DIR.iterdir()):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            out[p.stem] = p
    return out


async def sync_local_covers(db) -> dict:
    """Idempotent: a cover is re-encoded/uploaded only when the source file
    changed (digest differs from the one recorded on the story)."""
    stats = {"uploaded": 0, "skipped": 0, "unknown": 0, "failed": 0}
    for sid, file in local_covers().items():
        doc = await db.stories.find_one({"id": sid}, {"_id": 0, "id": 1, "hero_source_digest": 1})
        if doc is None:
            stats["unknown"] += 1
            logger.warning("cover %s: nessuna storia con questo id", file.name)
            continue
        raw = file.read_bytes()
        if doc.get("hero_source_digest") == source_digest(raw):
            stats["skipped"] += 1
            continue
        # Object Storage occasionalmente risponde 500 sotto carico: ritenta il
        # singolo file senza abortire l'intera sync (nessuna generazione AI).
        fields = None
        for attempt in range(3):
            try:
                fields = await asyncio.to_thread(upload_cover, sid, raw)
                break
            except Exception:
                if attempt == 2:
                    stats["failed"] += 1
                    logger.exception("cover %s: upload fallito dopo 3 tentativi", file.name)
                else:
                    await asyncio.sleep(1.5 * (attempt + 1))
        if fields is None:
            continue
        await db.stories.update_one({"id": sid}, {"$set": fields})
        stats["uploaded"] += 1
    return stats
