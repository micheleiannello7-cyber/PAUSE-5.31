"""TTS module for PAUSE.

Generates HD audio narration for stories (OpenAI tts-1-hd via the Emergent key,
optionally ElevenLabs for Italian).

Asset model (generate once, reuse forever):
  • An audio asset is identified by story + lang + voice + kind (full/preview)
    + content_hash (SHA-256 of the exact narrated text) + provider.
  • MongoDB `tts_assets` stores URL + metadata only (never audio bytes) and is
    the source of truth for "does this audio already exist?".
  • Bytes live in Object Storage; tts_cache/ on disk is a bounded LRU serving
    cache (HTTP Range playback) that is re-hydrated from storage on demand.
  • Editing a story changes the content_hash → new asset generated once; the
    unchanged combinations keep reusing the existing file.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Iterable

import emoji
from emergentintegrations.llm.openai import OpenAITextToSpeech
from litellm import speech as _litellm_speech

from storage import put_object, get_object_optional

CACHE_DIR = Path(__file__).parent / "tts_cache"
CACHE_DIR.mkdir(exist_ok=True)
# Disk is only a hot serving cache: keep it bounded (LRU by last access).
DISK_CACHE_MAX_BYTES = int(os.environ.get("TTS_DISK_CACHE_MAX_MB", "400")) * 1024 * 1024

# Object Storage is the persistent home for narration audio (cheap, survives
# redeploys, keeps the project/git light). The local tts_cache/ is only a fast
# serving cache for HTTP Range playback and is rebuilt on demand from storage.
TTS_STORAGE_PREFIX = "pause/tts"


def _storage_object_path(key: str) -> str:
    """Legacy (pre content-hash) storage path — still valid for adopted assets."""
    return f"{TTS_STORAGE_PREFIX}/{key}.mp3"


def _write_disk(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(".mp3.tmp")
    with tmp.open("wb") as f:
        f.write(data)
    tmp.replace(path)
    _trim_disk_cache()


def _trim_disk_cache() -> None:
    """Evict least-recently-used mp3s once the disk cache exceeds its budget."""
    try:
        files = [(f.stat().st_atime, f.stat().st_size, f) for f in CACHE_DIR.glob("*.mp3")]
    except OSError:
        return
    total = sum(s for _, s, _ in files)
    if total <= DISK_CACHE_MAX_BYTES:
        return
    for _, size, f in sorted(files):
        try:
            f.unlink()
            total -= size
        except OSError:
            continue
        if total <= DISK_CACHE_MAX_BYTES:
            break

# Both languages use tts-1-hd (high-definition). The proxy only exposes
# tts-1 / tts-1-hd; gpt-4o-mini-tts (which supported style `instructions`) is
# no longer available, so we drop the instructions and rely on the input text.
# NOTE: all OpenAI TTS voices are English-optimised, so Italian narration keeps
# a slight English accent — that's a provider ceiling, not a bug.
MODEL_IT = "tts-1-hd"
MODEL_EN = "tts-1-hd"
MODEL = MODEL_EN  # legacy default; per-request pick below picks the right one

# Style instructions passed to gpt-4o-mini-tts to lock the accent in place —
# without this the same voice slips back into an English cadence on longer
# Italian passages.
IT_STYLE = (
    "Parla in italiano perfetto, con accento italiano nativo di Roma o di Milano, "
    "calmo, caldo e chiaro. Non usare mai accento inglese o americano. "
    "Pronuncia correttamente le parole italiane, gli accenti tonici e le doppie consonanti. "
    "Ritmo naturale e riflessivo, come una lettura per adulti curiosi in una PAUSA serale."
)
EN_STYLE = (
    "Speak in clear, warm, native English with a calm and thoughtful pace, "
    "as if reading a bedtime curiosity to a curious adult listener."
)

VOICE = "nova"
# Voices offered in the app: Nova is the free default, the others are Premium.
VOICES = ("nova", "onyx", "echo", "shimmer")
# OpenAI TTS accepts up to 4096 chars per request; leave a small margin.
CHUNK_CHARS = 3800

# --- ElevenLabs (native Italian narration) --------------------------------
# When a real ELEVENLABS_API_KEY is configured, Italian audio is generated with
# eleven_multilingual_v2 (no English accent). English keeps OpenAI. Any
# ElevenLabs failure (placeholder key, quota, network) falls back to OpenAI so
# playback never breaks. The four app voices map to ElevenLabs premade voices;
# override with ELEVENLABS_VOICE_MAP="nova:<id>,onyx:<id>,..." if desired.
ELEVEN_MODEL = "eleven_multilingual_v2"
ELEVEN_OUTPUT = "mp3_44100_128"
_ELEVEN_DEFAULT_VOICES = {
    "nova": "EXAVITQu4vr4xnSDxMaL",     # Sarah — warm, calm female
    "shimmer": "Xb7hH8MSUJpSbSDYk0k2",  # Alice — clear, bright female
    "onyx": "JBFqnCBsd6RMkjVDRZzb",     # George — deep, warm male
    "echo": "onwK4e9ZLuTAKqWW03F9",     # Daniel — steady male narrator
}
_PLACEHOLDER_KEYS = {"", "placeholder", "your_key_here", "changeme", "todo"}
# After a failed ElevenLabs call we stop trying for a while (monotonic secs)
# so a bad key doesn't add a failing round-trip to every playback.
ELEVEN_BACKOFF_SECONDS = 600
_eleven_disabled_until = 0.0


def eleven_key() -> Optional[str]:
    key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    return None if key.lower() in _PLACEHOLDER_KEYS else key


def _eleven_voice_id(voice: str) -> str:
    overrides = {}
    for pair in (os.environ.get("ELEVENLABS_VOICE_MAP") or "").split(","):
        name, _, vid = pair.strip().partition(":")
        if name and vid:
            overrides[name.strip()] = vid.strip()
    return overrides.get(voice) or _ELEVEN_DEFAULT_VOICES.get(voice) or _ELEVEN_DEFAULT_VOICES[VOICE]


def provider_for(lang: str) -> str:
    """'eleven' for Italian when a real key is set (and not backing off), else 'openai'."""
    import time
    if lang == "it" and eleven_key() and time.monotonic() >= _eleven_disabled_until:
        return "eleven"
    return "openai"


def tts_status() -> dict:
    return {
        "elevenlabs_configured": bool(eleven_key()),
        "provider_it": provider_for("it"),
        "provider_en": provider_for("en"),
    }


def _model_for(lang: str) -> str:
    return MODEL_IT if lang == "it" else MODEL_EN


def _style_for(lang: str) -> str:
    return IT_STYLE if lang == "it" else EN_STYLE


def resolve_voice(value: Optional[str]) -> str:
    return value if value in VOICES else VOICE

_tts: Optional[OpenAITextToSpeech] = None
_locks: dict[str, asyncio.Lock] = {}


def _client() -> OpenAITextToSpeech:
    global _tts
    if _tts is None:
        key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("EMERGENT_LLM_KEY not configured")
        _tts = OpenAITextToSpeech(api_key=key)
    return _tts


def clean_for_tts(text: str) -> str:
    """Strip emoji, urls, markdown and other symbols the narrator would read aloud."""
    text = emoji.replace_emoji(text, replace="")
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"[*_#>~|`]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_into_chunks(text: str, max_chars: int = CHUNK_CHARS) -> List[str]:
    """Split at sentence boundaries so each chunk fits in one TTS request."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    # Split on sentence-ending punctuation while keeping the punctuation.
    parts = re.split(r"(?<=[.!?…])\s+", text)
    chunks: List[str] = []
    buf = ""
    for p in parts:
        if not p:
            continue
        if len(buf) + len(p) + 1 <= max_chars:
            buf = f"{buf} {p}".strip()
        else:
            if buf:
                chunks.append(buf)
            # A single sentence may still exceed the limit — hard-slice it.
            while len(p) > max_chars:
                chunks.append(p[:max_chars])
                p = p[max_chars:]
            buf = p
    if buf:
        chunks.append(buf)
    return chunks


def _legacy_cache_key(story_id: str, lang: str, kind: str, voice: str = VOICE, provider: str = "openai") -> str:
    """Key formula used before content-hashed assets. Kept only so audio that
    was already generated can be adopted (never regenerated)."""
    if provider == "eleven":
        version, model = "v4-eleven", ELEVEN_MODEL
    else:
        version, model = ("v3-native" if lang == "it" else "v2"), _model_for(lang)
    payload = f"{story_id}|{lang}|{voice}|{model}|{kind}|{version}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def content_hash(text: str) -> str:
    """Version of the narrated text: same text → same hash → same asset."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def asset_key(story_id: str, lang: str, voice: str, kind: str, chash: str, provider: str) -> str:
    model = ELEVEN_MODEL if provider == "eleven" else _model_for(lang)
    payload = f"{story_id}|{lang}|{voice}|{kind}|{chash}|{provider}|{model}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def _asset_storage_path(story_id: str, lang: str, voice: str, kind: str, chash: str, provider: str) -> str:
    return f"{TTS_STORAGE_PREFIX}/v2/{story_id}/{lang}-{voice}-{kind}-{chash}-{provider}.mp3"


def disk_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.mp3"


def _has_file(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _asset_filter(story_id: str, lang: str, voice: str, kind: str, chash: str) -> dict:
    return {"story_id": story_id, "lang": lang, "voice": voice, "kind": kind, "content_hash": chash}


async def find_asset(db, story_id: str, lang: str, voice: str, kind: str, chash: str, provider: str) -> Optional[dict]:
    """Existing asset for this exact combination. For the OpenAI path an
    ElevenLabs asset (better native accent) is accepted too; the ElevenLabs
    path only accepts ElevenLabs audio (so enabling the key upgrades once)."""
    if db is None:
        return None
    docs = await db.tts_assets.find(_asset_filter(story_id, lang, voice, kind, chash), {"_id": 0}).to_list(4)
    by_provider = {d.get("provider"): d for d in docs}
    if provider == "eleven":
        return by_provider.get("eleven")
    return by_provider.get("eleven") or by_provider.get("openai")


async def ensure_indexes(db) -> None:
    await db.tts_assets.create_index("key", unique=True)
    await db.tts_assets.create_index([("story_id", 1), ("lang", 1), ("voice", 1), ("kind", 1), ("content_hash", 1)])


CHAPTER_LABEL = {"it": "Capitolo", "en": "Chapter"}


def _compose_full(story: dict, lang: str = "it") -> str:
    label = CHAPTER_LABEL.get(lang, CHAPTER_LABEL["it"])
    parts: List[str] = []
    if story.get("title"):
        parts.append(story["title"].rstrip(".") + ".")
    if story.get("hook"):
        parts.append(story["hook"])
    for ch in story.get("chapters", []) or []:
        # Announce the chapter number before the title so the listener always
        # knows where they are — e.g. "Capitolo 1. Un impero enorme."
        num = ch.get("number")
        title = (ch.get("title") or "").rstrip(".")
        if num is not None and title:
            parts.append(f"{label} {num}. {title}.")
        elif title:
            parts.append(title + ".")
        if ch.get("body"):
            parts.append(ch["body"])
    if story.get("summary"):
        parts.append(story["summary"])
    return clean_for_tts(" ".join(parts))


def _compose_preview(story: dict) -> str:
    # ~5 seconds of speech: title + first sentence of hook.
    title = (story.get("title") or "").rstrip(".") + "."
    hook = story.get("hook") or ""
    first = re.split(r"(?<=[.!?…])\s+", hook.strip())[0] if hook else ""
    return clean_for_tts(f"{title} {first}").strip()


async def _generate_bytes(text: str, voice: str = VOICE, lang: str = "it") -> bytes:
    """Call OpenAI TTS in a thread. Uses `litellm.speech` directly so we can:
      • target `gpt-4o-mini-tts` for Italian (native-accent, multilingual)
      • pass a style `instructions` prompt (unsupported by tts-1-hd, ignored
        there by the API — so it's a no-op for the English path)
      • route through the Emergent proxy when the key is sk-emergent-*.
    """
    model = _model_for(lang)
    style = _style_for(lang)
    api_key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("EMERGENT_LLM_KEY not configured")

    params: dict = {
        "model": f"openai/{model}",
        "input": text,
        "voice": voice,
        "api_key": api_key,
    }
    if api_key.startswith("sk-emergent-"):
        proxy = os.getenv("INTEGRATION_PROXY_URL", "https://integrations.emergentagent.com")
        params["api_base"] = proxy + "/llm"
        params["custom_llm_provider"] = "openai"

    def _run() -> bytes:
        resp = _litellm_speech(**params)
        if hasattr(resp, "content"):
            return resp.content
        if hasattr(resp, "read"):
            return resp.read()
        return bytes(resp)
    return await asyncio.to_thread(_run)


async def _generate_bytes_eleven(text: str, voice: str = VOICE, lang: str = "it") -> bytes:
    """Native-accent narration via ElevenLabs eleven_multilingual_v2 (mp3)."""
    from elevenlabs import ElevenLabs, VoiceSettings

    key = eleven_key()
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY not configured")
    voice_id = _eleven_voice_id(voice)

    def _run() -> bytes:
        client = ElevenLabs(api_key=key, timeout=120)
        stream = client.text_to_speech.convert(
            voice_id,
            text=text,
            model_id=ELEVEN_MODEL,
            output_format=ELEVEN_OUTPUT,
            language_code=lang,
            voice_settings=VoiceSettings(stability=0.55, similarity_boost=0.8, style=0.15, use_speaker_boost=True),
        )
        return b"".join(chunk for chunk in stream if chunk)
    data = await asyncio.to_thread(_run)
    if not data:
        raise RuntimeError("ElevenLabs returned empty audio")
    return data


async def _synthesize(text: str, voice: str, lang: str, provider: str) -> bytes:
    """Chunk the text and concatenate the mp3 blobs for the given provider.
    Concatenating well-formed MP3 streams byte-wise plays back seamlessly in
    expo-audio; a single request stays a single file."""
    gen = _generate_bytes_eleven if provider == "eleven" else _generate_bytes
    blobs: List[bytes] = []
    for c in _split_into_chunks(text):
        blobs.append(await gen(c, voice, lang))
    return b"".join(blobs)


VOICE_SAMPLE_TEXT = {
    "it": "Ciao, sono {name}. Sarò la tua voce su PAUSE: una storia alla volta, con calma.",
    "en": "Hi, I'm {name}. I'll be your voice on PAUSE: one story at a time, at your pace.",
}


async def generate_voice_sample(voice: str, lang: str, db=None) -> Path:
    """Short greeting used by the voice picker. Cached like any story audio."""
    voice = resolve_voice(voice)
    text = VOICE_SAMPLE_TEXT.get(lang, VOICE_SAMPLE_TEXT["it"]).format(name=voice.capitalize())
    story = {"id": f"voice-sample-{voice}", "title": "", "hook": text, "chapters": [], "summary": ""}
    return await generate_story_audio(story, lang, preview=False, db=db, voice=voice)


def narration_text(story: dict, lang: str, kind: str) -> str:
    return _compose_preview(story) if kind == "preview" else _compose_full(story, lang)


def _log() -> logging.Logger:
    return logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lock_for(name: str) -> asyncio.Lock:
    return _locks.setdefault(name, asyncio.Lock())


def is_generating(story_id: str, lang: str, voice: str, kind: str, chash: str) -> bool:
    lock = _locks.get(f"{story_id}|{lang}|{voice}|{kind}|{chash}")
    return bool(lock and lock.locked())


# Last failed generation per combination (monotonic time, message), so the
# status endpoint can tell the client to stop waiting instead of polling.
_failures: dict[str, tuple[float, str]] = {}
FAILURE_TTL_SECONDS = 120


def last_failure(story_id: str, lang: str, voice: str, kind: str, chash: str) -> Optional[str]:
    entry = _failures.get(f"{story_id}|{lang}|{voice}|{kind}|{chash}")
    if entry and time.monotonic() - entry[0] < FAILURE_TTL_SECONDS:
        return entry[1]
    return None


async def asset_status(db, story: dict, lang: str, voice: str, kind: str) -> tuple[Optional[dict], str, bool]:
    """(existing asset or None, content_hash, generating?) — never generates."""
    voice = resolve_voice(voice)
    chash = content_hash(narration_text(story, lang, kind))
    asset = await find_asset(db, story["id"], lang, voice, kind, chash, provider_for(lang))
    if asset is None:
        # Legacy audio may exist without a metadata record yet (first request
        # after the migration to content-hashed assets): adopt it, no API call.
        asset = await _adopt_legacy(db, story["id"], lang, voice, kind, chash, provider_for(lang))
    return asset, chash, is_generating(story["id"], lang, voice, kind, chash)


async def generate_story_audio(story: dict, lang: str, preview: bool = False, db=None, voice: str = VOICE) -> Path:
    """Ensure the mp3 for a story is on disk and return its path.

    Provider: ElevenLabs for Italian when configured (native accent), OpenAI
    otherwise; ElevenLabs failures fall back to OpenAI with a backoff.

    Lookup order (each hit avoids the next, more expensive layer):
      1. `tts_assets` metadata (Mongo) → disk cache or Object Storage bytes
      2. Legacy files (pre content-hash keys) on disk / in storage → adopted
      3. The TTS provider — the only step that costs credits
    """
    global _eleven_disabled_until
    kind = "preview" if preview else "full"
    voice = resolve_voice(voice)
    provider = provider_for(lang)
    try:
        try:
            return await _ensure_audio(story, lang, kind, voice, provider, db)
        except Exception as exc:
            if provider != "eleven":
                raise
            _eleven_disabled_until = time.monotonic() + ELEVEN_BACKOFF_SECONDS
            _log().warning("ElevenLabs failed for %s (%s); falling back to OpenAI for %ss", story["id"], exc, ELEVEN_BACKOFF_SECONDS)
            return await _ensure_audio(story, lang, kind, voice, "openai", db)
    except Exception as exc:
        chash = content_hash(narration_text(story, lang, kind))
        _failures[f"{story['id']}|{lang}|{voice}|{kind}|{chash}"] = (time.monotonic(), str(exc)[:300])
        raise


async def _materialise(db, asset: dict) -> Optional[Path]:
    """Make the asset's bytes available on disk (hydrating from storage)."""
    path = disk_path(asset["key"])
    if _has_file(path):
        return path
    if not asset.get("storage_path"):
        return None
    try:
        data = await asyncio.to_thread(get_object_optional, asset["storage_path"])
    except Exception as exc:
        _log().warning("Storage read failed for %s: %s", asset["storage_path"], exc)
        return None
    if not data:
        return None
    _write_disk(path, data)
    return path


async def _ensure_audio(story: dict, lang: str, kind: str, voice: str, provider: str, db) -> Path:
    text = narration_text(story, lang, kind)
    if not text:
        raise ValueError("Empty text after cleanup")
    chash = content_hash(text)
    story_id = story["id"]

    asset = await find_asset(db, story_id, lang, voice, kind, chash, provider)
    if asset:
        path = await _materialise(db, asset)
        if path:
            return path

    # Serialize per combination so two clients never trigger duplicate work.
    async with _lock_for(f"{story_id}|{lang}|{voice}|{kind}|{chash}"):
        asset = await find_asset(db, story_id, lang, voice, kind, chash, provider)
        if asset:
            path = await _materialise(db, asset)
            if path:
                return path
            # Metadata without retrievable bytes: drop it and regenerate once.
            _log().warning("Asset %s unreachable; regenerating", asset["key"])
            if db is not None:
                await db.tts_assets.delete_one({"key": asset["key"]})

        asset = await _adopt_legacy(db, story_id, lang, voice, kind, chash, provider)
        if asset:
            path = await _materialise(db, asset)
            if path:
                return path

        # Layer 3 — the provider call (this is what costs credits).
        payload = await _synthesize(text, voice, lang, provider)
        key = asset_key(story_id, lang, voice, kind, chash, provider)
        path = disk_path(key)
        _write_disk(path, payload)
        spath = _asset_storage_path(story_id, lang, voice, kind, chash, provider)
        stored = True
        try:
            await asyncio.to_thread(put_object, spath, payload, "audio/mpeg")
        except Exception as exc:
            stored = False
            _log().warning("TTS upload to Object Storage failed for %s: %s", key, exc)
        await _register_asset(db, {
            "key": key, "story_id": story_id, "lang": lang, "voice": voice, "kind": kind,
            "content_hash": chash, "provider": provider,
            "model": ELEVEN_MODEL if provider == "eleven" else _model_for(lang),
            "storage_path": spath if stored else None, "size": len(payload),
            "chars": len(text), "created_at": _now(), "source": "generated",
        })
        return path


async def _register_asset(db, doc: dict) -> None:
    if db is None:
        return
    try:
        await db.tts_assets.update_one({"key": doc["key"]}, {"$set": doc}, upsert=True)
    except Exception as exc:
        _log().warning("tts_assets upsert failed for %s: %s", doc["key"], exc)


# --------------------------------------------------------------------------
# Legacy adoption — audio generated before content-hashed assets is reused
# as-is (never regenerated) and simply gets a metadata record.
# --------------------------------------------------------------------------

async def _legacy_in_storage(db, legacy_key: str) -> bool:
    if db is not None and await db.tts_uploaded.find_one({"key": legacy_key}, {"_id": 1}):
        return True
    try:
        return bool(await asyncio.to_thread(get_object_optional, _storage_object_path(legacy_key)))
    except Exception:
        return False


async def _adopt_legacy(db, story_id: str, lang: str, voice: str, kind: str, chash: str, provider: str) -> Optional[dict]:
    providers = ("eleven",) if provider == "eleven" else ("eleven", "openai")
    for p in providers:
        lk = _legacy_cache_key(story_id, lang, kind, voice, p)
        lpath = disk_path(lk)
        on_disk = _has_file(lpath)
        if not on_disk and not await _legacy_in_storage(db, lk):
            continue
        if on_disk and not await _legacy_in_storage(db, lk):
            try:
                await asyncio.to_thread(put_object, _storage_object_path(lk), lpath.read_bytes(), "audio/mpeg")
                if db is not None:
                    await db.tts_uploaded.update_one({"key": lk}, {"$set": {"key": lk, "size": lpath.stat().st_size}}, upsert=True)
            except Exception as exc:
                _log().warning("Legacy upload failed for %s: %s", lk, exc)
        key = asset_key(story_id, lang, voice, kind, chash, p)
        if on_disk and not _has_file(disk_path(key)):
            try:
                os.link(lpath, disk_path(key))  # same bytes, no extra disk usage
            except OSError:
                shutil.copyfile(lpath, disk_path(key))
        doc = {
            "key": key, "story_id": story_id, "lang": lang, "voice": voice, "kind": kind,
            "content_hash": chash, "provider": p,
            "model": ELEVEN_MODEL if p == "eleven" else _model_for(lang),
            "storage_path": _storage_object_path(lk), "legacy_key": lk,
            "size": lpath.stat().st_size if on_disk else None,
            "created_at": _now(), "source": "adopted",
        }
        await _register_asset(db, doc)
        _log().info("Adopted legacy audio %s for %s/%s/%s/%s", lk, story_id, lang, voice, kind)
        return doc
    return None


def _voice_sample_story(voice: str, lang: str) -> dict:
    text = VOICE_SAMPLE_TEXT.get(lang, VOICE_SAMPLE_TEXT["it"]).format(name=voice.capitalize())
    return {"id": f"voice-sample-{voice}", "title": "", "hook": text, "chapters": [], "summary": ""}


async def adopt_legacy_assets(db, localized_stories: Iterable[tuple[str, dict]]) -> dict:
    """Startup migration: give every legacy mp3 (disk or storage) a
    `tts_assets` record keyed by the current content hash, so playback finds
    it without touching the provider. Idempotent; nothing is re-generated.

    `localized_stories` yields (lang, localized story dict) pairs.
    """
    known: set[str] = set()
    async for d in db.tts_uploaded.find({}, {"_id": 0, "key": 1}):
        known.add(d["key"])
    known.update(f.stem for f in CACHE_DIR.glob("*.mp3"))
    adopted_legacy: set[str] = set()
    async for d in db.tts_assets.find({}, {"_id": 0, "key": 1, "legacy_key": 1}):
        known.discard(d["key"])  # content-hashed asset files are not legacy
        if d.get("legacy_key"):
            adopted_legacy.add(d["legacy_key"])
    pending = known - adopted_legacy
    stats = {"legacy_files": len(known), "already": len(adopted_legacy), "adopted": 0, "unmatched": 0}
    if not pending:
        return stats

    candidates: list[tuple[str, dict]] = list(localized_stories)
    for lang in ("it", "en"):
        for v in VOICES:
            candidates.append((lang, _voice_sample_story(v, lang)))

    for lang, story in candidates:
        for voice in VOICES:
            for kind in ("full", "preview"):
                for p in ("eleven", "openai"):
                    lk = _legacy_cache_key(story["id"], lang, kind, voice, p)
                    if lk not in pending:
                        continue
                    chash = content_hash(narration_text(story, lang, kind))
                    if await _adopt_legacy(db, story["id"], lang, voice, kind, chash, p):
                        stats["adopted"] += 1
                        pending.discard(lk)
    stats["unmatched"] = len(pending)
    return stats


async def ingest_disk_cache_into_storage(db=None) -> dict:
    """Upload every legacy mp3 on disk into Object Storage (idempotent via
    `tts_uploaded`). Keeps a zip-imported project cross-deploy persistent."""
    uploaded = 0
    seen = 0
    done_keys: set[str] = set()
    if db is not None:
        async for d in db.tts_uploaded.find({}, {"_id": 0, "key": 1}):
            done_keys.add(d["key"])
        async for d in db.tts_assets.find({"storage_path": {"$ne": None}}, {"_id": 0, "key": 1}):
            done_keys.add(d["key"])
    for f in CACHE_DIR.glob("*.mp3"):
        seen += 1
        key = f.stem
        if key in done_keys:
            continue
        try:
            data = f.read_bytes()
            await asyncio.to_thread(put_object, _storage_object_path(key), data, "audio/mpeg")
            if db is not None:
                await db.tts_uploaded.update_one({"key": key}, {"$set": {"key": key, "size": len(data)}}, upsert=True)
            uploaded += 1
        except Exception:
            continue
    return {"seen": seen, "uploaded": uploaded}


async def assets_report(db) -> dict:
    """Metadata-only summary for /api/content/assets-report."""
    pipeline = [{"$group": {
        "_id": {"lang": "$lang", "voice": "$voice", "kind": "$kind", "provider": "$provider"},
        "count": {"$sum": 1}, "bytes": {"$sum": {"$ifNull": ["$size", 0]}},
    }}]
    groups = [
        {**g["_id"], "count": g["count"], "bytes": g["bytes"]}
        async for g in db.tts_assets.aggregate(pipeline)
    ]
    disk = [f.stat().st_size for f in CACHE_DIR.glob("*.mp3")]
    return {
        "assets": sum(g["count"] for g in groups),
        "bytes_in_storage": sum(g["bytes"] for g in groups),
        "by_combination": sorted(groups, key=lambda g: (g["lang"], g["voice"], g["kind"], g["provider"])),
        "disk_cache": {"files": len(disk), "bytes": sum(disk), "budget_bytes": DISK_CACHE_MAX_BYTES},
        "providers": tts_status(),
    }
