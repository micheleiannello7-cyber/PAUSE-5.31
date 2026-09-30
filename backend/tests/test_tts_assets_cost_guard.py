"""Asset layer cost guard: an already generated narration must NEVER hit the
TTS provider again (same story + lang + voice + content version), while an
edited text (new content hash) is generated exactly once.

Runs fully offline: provider + Object Storage are monkeypatched, Mongo is a
throwaway database.
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tts  # noqa: E402

MONGO = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB = "pause_test_tts_assets"


def _story(body: str) -> dict:
    return {
        "id": "test-asset-story", "title": "Titolo di prova", "hook": "Un hook.",
        "chapters": [{"number": 1, "title": "Uno", "body": body}], "summary": "Fine.",
    }


@pytest.fixture()
def env(monkeypatch, tmp_path):
    calls = {"tts": 0, "put": 0, "get": 0}
    fake_storage: dict[str, bytes] = {}

    async def fake_synth(text, voice, lang, provider):
        calls["tts"] += 1
        return b"ID3" + text.encode()[:40]

    def fake_put(path, data, ctype):
        calls["put"] += 1
        fake_storage[path] = data
        return {"path": path}

    def fake_get_optional(path):
        calls["get"] += 1
        return fake_storage.get(path)

    monkeypatch.setattr(tts, "_synthesize", fake_synth)
    monkeypatch.setattr(tts, "put_object", fake_put)
    monkeypatch.setattr(tts, "get_object_optional", fake_get_optional)
    monkeypatch.setattr(tts, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(tts, "_locks", {})
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = AsyncIOMotorClient(MONGO, io_loop=loop)
    db = client[DB]
    loop.run_until_complete(client.drop_database(DB))
    loop.run_until_complete(tts.ensure_indexes(db))
    yield loop, db, calls, fake_storage, tmp_path
    loop.run_until_complete(client.drop_database(DB))
    client.close()
    loop.close()


def test_same_content_generates_once_and_is_reused(env):
    loop, db, calls, storage, disk = env
    story = _story("Corpo del capitolo, versione uno.")

    p1 = loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="nova"))
    assert calls["tts"] == 1 and calls["put"] == 1
    assert p1.exists()

    # Second play: metadata hit → disk hit → provider NOT called.
    p2 = loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="nova"))
    assert p2 == p1 and calls["tts"] == 1

    # Disk cache evicted (new pod): bytes re-hydrated from storage, still no provider call.
    p1.unlink()
    p3 = loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="nova"))
    assert p3.exists() and calls["tts"] == 1 and calls["get"] >= 1

    asset, chash, generating = loop.run_until_complete(tts.asset_status(db, story, "it", "nova", "full"))
    assert asset and asset["content_hash"] == chash and not generating
    assert asset["storage_path"] in storage
    assert loop.run_until_complete(db.tts_assets.count_documents({})) == 1


def test_other_voice_lang_or_edited_text_generate_exactly_once_each(env):
    loop, db, calls, storage, disk = env
    story = _story("Corpo del capitolo, versione uno.")
    loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="nova"))
    loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="onyx"))
    loop.run_until_complete(tts.generate_story_audio(story, "en", db=db, voice="nova"))
    loop.run_until_complete(tts.generate_story_audio(story, "it", preview=True, db=db, voice="nova"))
    assert calls["tts"] == 4

    edited = _story("Corpo del capitolo, versione due, più corta.")
    loop.run_until_complete(tts.generate_story_audio(edited, "it", db=db, voice="nova"))
    assert calls["tts"] == 5
    # Replaying both versions costs nothing more.
    loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="nova"))
    loop.run_until_complete(tts.generate_story_audio(edited, "it", db=db, voice="nova"))
    assert calls["tts"] == 5
    assert loop.run_until_complete(db.tts_assets.count_documents({})) == 5


def test_concurrent_requests_share_one_generation(env):
    loop, db, calls, storage, disk = env
    story = _story("Testo per la concorrenza.")

    async def burst():
        return await asyncio.gather(*[tts.generate_story_audio(story, "it", db=db, voice="nova") for _ in range(6)])

    paths = loop.run_until_complete(burst())
    assert len({p for p in paths}) == 1 and calls["tts"] == 1


def test_legacy_audio_is_adopted_not_regenerated(env):
    loop, db, calls, storage, disk = env
    story = _story("Testo con audio legacy.")
    legacy_key = tts._legacy_cache_key(story["id"], "it", "full", "nova", "openai")
    (disk / f"{legacy_key}.mp3").write_bytes(b"ID3legacy-bytes")

    path = loop.run_until_complete(tts.generate_story_audio(story, "it", db=db, voice="nova"))
    assert calls["tts"] == 0
    assert path.read_bytes() == b"ID3legacy-bytes"
    doc = loop.run_until_complete(db.tts_assets.find_one({}, {"_id": 0}))
    assert doc["legacy_key"] == legacy_key and doc["source"] == "adopted"
    assert doc["storage_path"] in storage  # uploaded once for persistence
