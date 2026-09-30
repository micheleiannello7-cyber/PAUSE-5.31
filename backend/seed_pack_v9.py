"""PAUSE v9 — contenuti per riportare in pari le categorie (argomenti in v9_topics.py, testi in
v9_content.json scritti da generate_v9.py). Stessa gerarchia del catalogo: kind, objective (lezioni),
translations.en, chapters_v6. Finché il JSON non esiste il pack è vuoto e il seed non cambia."""
import json
from pathlib import Path

from seed_pack_v8 import build_pack

_JSON = Path(__file__).parent / "v9_content.json"
_COVERS = Path(__file__).parent / "covers"
_ALL = json.loads(_JSON.read_text()) if _JSON.exists() else {}
# Regola v9: un contenuto entra nel catalogo solo insieme alla sua copertina (covers/<id>.*),
# prodotta da produce_v9.py subito dopo il testo. Mai storie senza immagine.
_CONTENT = {sid: e for sid, e in _ALL.items() if any(_COVERS.glob(f"{sid}.*"))}

STORIES, LESSONS = build_pack(_CONTENT)
