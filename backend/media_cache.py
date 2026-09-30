"""Bounded on-disk cache in front of Object Storage reads (images).

Storage reads are metered, so every static asset (category art, covers) is
fetched from storage once per backend instance and then served from disk.
Objects are content-addressed (their storage path embeds a digest), which is
why they can be cached forever and served with strong ETags.
"""
import hashlib
import json
import os
from pathlib import Path

from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException

from storage import get_object

CACHE_DIR = Path(__file__).parent / "media_cache"
CACHE_DIR.mkdir(exist_ok=True)
MAX_BYTES = int(os.environ.get("MEDIA_DISK_CACHE_MAX_MB", "200")) * 1024 * 1024
IMMUTABLE = "public, max-age=31536000, immutable"


def etag_for(storage_path: str) -> str:
    return '"' + hashlib.sha1(storage_path.encode()).hexdigest()[:20] + '"'


def _entry(storage_path: str) -> tuple[Path, Path]:
    stem = hashlib.sha1(storage_path.encode()).hexdigest()
    return CACHE_DIR / f"{stem}.bin", CACHE_DIR / f"{stem}.json"


def _trim() -> None:
    files = [(f.stat().st_atime, f.stat().st_size, f) for f in CACHE_DIR.glob("*.bin")]
    total = sum(s for _, s, _ in files)
    if total <= MAX_BYTES:
        return
    for _, size, f in sorted(files):
        try:
            f.unlink()
            f.with_suffix(".json").unlink(missing_ok=True)
            total -= size
        except OSError:
            continue
        if total <= MAX_BYTES:
            break


def _read_or_fetch(storage_path: str) -> tuple[bytes, str]:
    data_file, meta_file = _entry(storage_path)
    if data_file.exists() and meta_file.exists():
        return data_file.read_bytes(), json.loads(meta_file.read_text())["content_type"]
    content, ctype = get_object(storage_path)
    tmp = data_file.with_suffix(".tmp")
    tmp.write_bytes(content)
    tmp.replace(data_file)
    meta_file.write_text(json.dumps({"content_type": ctype, "path": storage_path}))
    _trim()
    return content, ctype


async def cached_object(storage_path: str) -> tuple[bytes, str]:
    try:
        return await run_in_threadpool(_read_or_fetch, storage_path)
    except HTTPException:
        raise
    except Exception:
        # The seed references Object Storage paths that may not exist in this
        # environment (e.g. after a migration to a fresh bucket). Surface a
        # clean 404 so the frontend uses its SVG fallback instead of a 500.
        raise HTTPException(404, "Asset not found in Object Storage")


def _read_or_make(key: str, make) -> tuple[bytes, str]:
    data_file, meta_file = _entry(key)
    if data_file.exists() and meta_file.exists():
        return data_file.read_bytes(), json.loads(meta_file.read_text())["content_type"]
    content, ctype = make()
    tmp = data_file.with_suffix(".tmp")
    tmp.write_bytes(content)
    tmp.replace(data_file)
    meta_file.write_text(json.dumps({"content_type": ctype, "path": key}))
    _trim()
    return content, ctype


async def cached_derived(key: str, make) -> tuple[bytes, str]:
    """Variante derivata di un asset (es. sfondo rimosso), calcolata una volta
    e servita da disco come gli oggetti dello storage."""
    return await run_in_threadpool(_read_or_make, key, make)


def stats() -> dict:
    sizes = [f.stat().st_size for f in CACHE_DIR.glob("*.bin")]
    return {"files": len(sizes), "bytes": sum(sizes), "budget_bytes": MAX_BYTES}
