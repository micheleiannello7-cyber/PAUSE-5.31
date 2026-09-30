"""PAUSE — contenuti ritirati dal catalogo dopo il controllo qualità editoriale.

Ogni voce è un doppione (stesso argomento già trattato meglio da un'altra storia)
o un contenuto giudicato debole. I documenti NON vengono cancellati: al boot
`retire_in_db` li sposta nella collection `stories_retired` (con motivo e data)
e li rimuove da `stories`, così spariscono dall'app ma restano recuperabili.
I file seed originali restano in archivio; `server.py` li filtra tramite RETIRED.
"""
from datetime import datetime, timezone

# id -> (motivo, id della storia che resta in catalogo o None)
RETIRED = {
    "time-zones": ("doppione: fusi orari", "geo-why-timezones"),
    "why-oceans-salty": ("doppione: mare salato", "geo-why-oceans-salty"),
    "why-we-yawn": ("doppione: sbadiglio (versione meno rigorosa)", "v4-sbadiglio"),
    "why-mirror-flip": ("doppione: specchio", "cur-why-mirrors-reverse"),
    "cur-why-popcorn-pops": ("doppione: popcorn (versione meno precisa)", "v4-pop-corn"),
    "v4-polpo-cervelli": ("doppione: cervelli del polpo (titolo semplificato)", "octopus-brains"),
    "ani-bee-dance": ("doppione: comunicazione delle api", "bees-communicate"),
    "v4-foglie-autunno": ("doppione: foglie d'autunno", "nat-why-leaves-fall"),
    "nat-lightning": ("doppione: fulmine (versione meno ricca)", "v4-fulmini"),
    "nat-mushrooms-network": ("doppione: rete dei funghi", "v4-funghi-rete"),
    "moon-tides": ("doppione: maree (versione più semplice)", "nat-tides"),
    "procrastination": ("doppione: procrastinazione", "psi-why-procrastinate"),
    "why-we-dream": ("doppione: sogni", "cor-why-dreams"),
    "sto-printing-press": ("doppione: stampa a caratteri mobili", "printing-press"),
    "espresso-italian": ("doppione: espresso (premessa poco verificabile)", "v4-caffe-espresso"),
    "eco-why-money-value": ("doppione: valore della banconota", "v4-banconote-valore"),
    "cur-why-yawn-contagious-fun": ("contenuto debole: zucchero filato", None),
    "v7-lez-viaggiare-leggeri": ("contenuto debole: fare la valigia", None),
}

RETIRED_IDS = frozenset(RETIRED)


async def retire_in_db(db) -> int:
    """Archivia in `stories_retired` e rimuove da `stories`. Idempotente."""
    moved = 0
    async for doc in db.stories.find({"id": {"$in": list(RETIRED_IDS)}}, {"_id": 0}):
        reason, kept = RETIRED[doc["id"]]
        await db.stories_retired.update_one(
            {"id": doc["id"]},
            {"$set": {**doc, "retired_at": datetime.now(timezone.utc), "retired_reason": reason, "kept_id": kept}},
            upsert=True,
        )
        await db.stories.delete_one({"id": doc["id"]})
        moved += 1
    return moved
