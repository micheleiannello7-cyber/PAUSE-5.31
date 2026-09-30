"""
PAUSE v9 — scrive i testi (IT + EN, 6 capitoli, 4–5 minuti di lettura) per gli argomenti di
v9_topics.py con GPT-5.4 via emergentintegrations e li salva in v9_content.json.

Stessa struttura di generate_v8.py (checkpoint per voce, riprende dai mancanti), con in più il
controllo di durata: il badge "N min" dell'app usa `_estimated_audio_minutes` (stima TTS), quindi
ogni lingua deve restare entro MAX_CHARS caratteri totali (≈ 5 minuti) — altrimenti si richiede
una versione più corta. seed_pack_v9.py legge il JSON e costruisce i documenti.

Usage:
    cd /app/backend && python generate_v9.py            # scrive i mancanti
    cd /app/backend && python generate_v9.py --only <id>
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from generate_fill import CHAPTER_ICONS, SYSTEM, parse_json, story_prompt, lesson_prompt  # noqa: E402
from generate_v8 import slugify  # noqa: E402
from server import _estimated_audio_minutes  # noqa: E402
from story_builder import CAT_META  # noqa: E402
from seed_data import CATEGORY_NAMES_EN  # noqa: E402
from v9_topics import all_topics  # noqa: E402

MODEL = ("openai", "gpt-5.4")
CONCURRENCY = 4
OUT = ROOT_DIR / "v9_content.json"
MAX_MINUTES = 5
# 5 min = 300 s a 12.5 caratteri/s meno le pause (~10.5 s) ≈ 3600 caratteri; margine di sicurezza.
MAX_CHARS = 3400
WORDS = "60-75 words"
MIN_WORDS = 50  # validate() di v8 esige 60 parole: qui i capitoli sono più brevi per restare ≤5 min.
LENGTH_RULE = (
    "\n\nLENGTH IS MANDATORY: the whole narration of each language (title + hook + 6 chapter titles + "
    f"6 bodies + summary) must stay under {MAX_CHARS} characters, so each chapter body is {WORDS}. "
    "Dense and precise beats long: no filler, no repetition, every sentence carries a fact or an image."
)


def topic_id(kind: str, title_en: str) -> str:
    return f"v9-{'lez-' if kind == 'lesson' else ''}{slugify(title_en)}"


def build_prompt(cat: dict, kind: str, title_it: str, title_en: str) -> str:
    base = story_prompt(cat, title_it, title_en) if kind == "story" else lesson_prompt(cat, title_it, title_en)
    return base.replace("90-130 words", WORDS) + LENGTH_RULE


def narration_chars(lang: dict) -> int:
    parts = [lang.get("title", ""), lang.get("hook", ""), lang.get("summary", "")]
    parts += [c.get("title", "") + c.get("body", "") for c in lang.get("chapters", [])]
    return sum(len(p) for p in parts)


def too_long(d: dict) -> str | None:
    for code in ("it", "en"):
        lang = d[code]
        mins = _estimated_audio_minutes(lang)
        if mins > MAX_MINUTES or narration_chars(lang) > MAX_CHARS:
            return f"{code}: {narration_chars(lang)} chars / {mins} min"
    return None


def load_out() -> dict:
    return json.loads(OUT.read_text()) if OUT.exists() else {}


def save_out(data: dict):
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tmp.replace(OUT)


def validate_v9(d: dict, kind: str):
    it, en = d["it"], d["en"]
    assert len(it["chapters"]) == 6 and len(en["chapters"]) == 6, "need 6 chapters"
    for lang in (it, en):
        assert lang["title"] and lang["hook"] and lang["summary"], "missing fields"
        for ch in lang["chapters"]:
            assert ch["title"] and len(ch["body"].split()) >= MIN_WORDS, "chapter too short"
        if kind == "lesson":
            assert lang.get("objective"), "missing objective"


async def ask(session_id: str, prompt: str, kind: str, retries: int = 3) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"{session_id}-{attempt}", system_message=SYSTEM)
            chat.with_model(*MODEL)
            d = parse_json(await chat.send_message(UserMessage(text=prompt)))
            validate_v9(d, kind)
            err = too_long(d)
            if err is None:
                return d
            last_err = f"too long ({err})"
            prompt += f"\n\nYour previous answer was too long ({err}). Cut every chapter body to about 60-65 words."
        except Exception as e:  # noqa: BLE001
            last_err = e
            msg = str(e).lower()
            if "budget" in msg or "insufficient" in msg or "402" in msg:
                raise
            await asyncio.sleep(2 + attempt * 3)
    raise RuntimeError(f"LLM failed for {session_id}: {last_err}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    parser.add_argument("--list", action="store_true", help="stampa gli id senza chiamare il modello")
    args = parser.parse_args()

    out = load_out()
    lock = asyncio.Lock()
    sem = asyncio.Semaphore(CONCURRENCY)
    todo = []
    for cat_id, kind, title_it, title_en in all_topics():
        sid = topic_id(kind, title_en)
        if args.list:
            print(f"{'done' if sid in out else 'todo'} {kind:6} {cat_id:12} {sid}")
            continue
        if args.only and sid != args.only:
            continue
        if sid in out and not args.only:
            continue
        todo.append((sid, cat_id, kind, title_it, title_en))
    if args.list:
        return
    print(f"done={len(out)} todo={len(todo)}")

    async def one(sid, cat_id, kind, title_it, title_en):
        name, icon, color = CAT_META[cat_id]
        cat = {"id": cat_id, "name": name, "name_en": CATEGORY_NAMES_EN[cat_id], "icon": icon, "color": color}
        async with sem:
            try:
                d = await ask(f"v9-{sid}", build_prompt(cat, kind, title_it, title_en), kind)
                icons = [i if i in CHAPTER_ICONS else None for i in (d.get("chapter_icons") or [])]
                entry = {"id": sid, "category_id": cat_id, "kind": kind, "it": d["it"], "en": d["en"], "icons": icons}
                async with lock:
                    out[sid] = entry
                    save_out(out)
                print(f"OK   {kind:6} {cat_id}/{sid} ({narration_chars(d['it'])} it / {narration_chars(d['en'])} en chars)", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {kind:6} {cat_id}/{sid}: {e}", flush=True)
                msg = str(e).lower()
                if "budget" in msg or "insufficient" in msg or "402" in msg:
                    raise

    try:
        await asyncio.gather(*(one(*t) for t in todo))
    except Exception as e:  # noqa: BLE001
        print(f"[stop] {e}")
    print(f"[done] total={len(out)}")


if __name__ == "__main__":
    asyncio.run(main())
