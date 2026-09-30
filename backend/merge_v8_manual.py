"""Unisce i contenuti scritti a mano (v8_manual/*.py) in v8_content.json.
Uso: python merge_v8_manual.py  — poi riavvia il backend (ensure_seed fa l'upsert)."""
import importlib
import json
from pathlib import Path

OUT = Path(__file__).parent / "v8_content.json"
MODULES = ["corpo_umano", "cultura", "curiosita", "economia", "arte", "geografia"]


def validate(e: dict):
    for lang in ("it", "en"):
        d = e[lang]
        assert d["title"] and d["hook"] and d["summary"], f"{e['id']}: missing fields ({lang})"
        assert len(d["chapters"]) == 6, f"{e['id']}: need 6 chapters ({lang})"
        for i, ch in enumerate(d["chapters"]):
            n = len(ch["body"].split())
            assert ch["title"] and n >= 55, f"{e['id']} ch{i + 1} ({lang}) too short: {n} words"
        if e["kind"] == "lesson":
            assert d.get("objective"), f"{e['id']}: missing objective ({lang})"


def main():
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    added = 0
    for name in MODULES:
        try:
            mod = importlib.import_module(f"v8_manual.{name}")
        except ModuleNotFoundError:
            print(f"skip {name} (not written yet)")
            continue
        for e in mod.ENTRIES:
            validate(e)
            if e["id"] not in data:
                added += 1
            data[e["id"]] = e
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tmp.replace(OUT)
    print(f"merged: +{added} new, total {len(data)}")


if __name__ == "__main__":
    main()
