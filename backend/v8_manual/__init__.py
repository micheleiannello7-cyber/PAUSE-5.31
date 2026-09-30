"""PAUSE v8 — contenuti scritti a mano (IT + EN) per completare il pacchetto v8.
Ogni modulo di categoria espone ENTRIES, nello stesso formato di v8_content.json,
così seed_pack_v8.py li carica senza modifiche. merge_v8_manual.py li unisce al JSON."""
import re
import unicodedata


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:56]


def _entry(cat, kind, title_it, title_en, hl_it, hl_en, hook_it, hook_en, summary_it, summary_en,
           chapters, icons, objective_it=None, objective_en=None):
    """chapters: 6 tuple (title_it, body_it, title_en, body_en)."""
    assert len(chapters) == 6, f"{title_it}: need 6 chapters"
    assert len(icons) == 6, f"{title_it}: need 6 icons"
    it = {
        "title": title_it, "highlight_words": hl_it, "hook": hook_it,
        "chapters": [{"title": c[0], "body": c[1]} for c in chapters], "summary": summary_it,
    }
    en = {
        "title": title_en, "highlight_words": hl_en, "hook": hook_en,
        "chapters": [{"title": c[2], "body": c[3]} for c in chapters], "summary": summary_en,
    }
    if kind == "lesson":
        it["objective"] = objective_it
        en["objective"] = objective_en
    return {
        "id": f"v8-{'lez-' if kind == 'lesson' else ''}{_slug(title_en)}",
        "category_id": cat, "kind": kind, "it": it, "en": en, "icons": icons, "manual": True,
    }


def story(cat, title_it, title_en, hl_it, hl_en, hook_it, hook_en, summary_it, summary_en, chapters, icons):
    return _entry(cat, "story", title_it, title_en, hl_it, hl_en, hook_it, hook_en, summary_it, summary_en, chapters, icons)


def lesson(cat, title_it, title_en, hl_it, hl_en, hook_it, hook_en, objective_it, objective_en,
           summary_it, summary_en, chapters, icons):
    return _entry(cat, "lesson", title_it, title_en, hl_it, hl_en, hook_it, hook_en, summary_it, summary_en,
                  chapters, icons, objective_it, objective_en)
