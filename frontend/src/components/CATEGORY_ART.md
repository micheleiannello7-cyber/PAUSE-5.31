# PAUSE — due serie conservate

## Serie attiva — reference-3d-v6 (richiesta esplicita 25/09/2026)
Rigenerata fedelmente alla foto fornita dall'utente: beuta, Saturno, chip, germoglio,
zampa, busto, loto/Psicologia, testa anatomica, libro, monete, tavolozza, montagna;
cristallo prismatico per Qualsiasi. Nessuna categoria creata/rinominata.
13 WebP in Object Storage; manifest precedente conservato in
`backend/category_art/previous-glossy-3d-v5.json`. Asset precedenti non cancellati.
Luce di selezione NON disegnata nel bitmap: `category-tile-effects.tsx` la anima
solo quando selezionata; in CategoryGrid `all` accende tutte. Home mantiene il suo
focus indipendente. Font Manrope Medium, palette reference in theme.ts.
Le note seguenti sono storiche, non descrivono la famiglia attualmente pubblicata.

## Serie vettoriale originale (approvata)
`category-icon.tsx` contiene i 13 disegni SVG originali completi (`CATEGORY_DRAWINGS`).
Non è stata cancellata, sostituita o convertita in immagini. Rimane utilizzabile
nei piccoli badge e come fallback offline/errore per tutte le card.

Per usare di nuovo i vettori nelle card: impostare `CATEGORY_VISUAL_MODE = "line"`
in `category-artwork.tsx`. Nessuna modifica ai dati o alla navigazione è necessaria.

## Serie illustrata — glass-2026-09-v1
13 soggetti originali + cristallo per «Qualsiasi argomento», un soggetto per card.
Materiale satinato/vetro, luce cyan-violet, tinta della categoria, soggetto nella
zona alta e sfumatura scura sotto le etichette. Animali usa il **bassotto** ambrato
richiesto (non la balena né il primo cane).

Le immagini 480px WebP sono in Emergent Managed Object Storage, servite soltanto
via API dell'app `/api/category-media/{id}?v=...`; cache locale memory-disk.
Il manifest persistente è `backend/category_art_manifest.json`; le sorgenti e
lo script di importazione sono conservati separatamente nel backend.
Nessuna chiamata AI avviene durante l'uso dell'app.

## Revisione riconoscibile — recognizable-2026-09-v2
- Approvati e invariati: Saturno, chip, colonna ionica, cervello e DNA.
- Nuovi soggetti: beuta scientifica, albero vivo, libro aperto, monete, tavolozza,
  globo terrestre. Bassotto naturale con pelo, espressione e zampa sollevata.
- Immagini al90% della larghezza in Argomenti/onboarding; al84% in Home.
  Tessere Home88px (prima96), immagine effettiva circa72px (prima94): -23% circa.
- La categoria Curiosità è ritirata:12categorie attive,13icone SVG archiviate.
  La vecchia illustrazione del cubo rimane nello storage, non appare nei picker.
- Le sorgenti v1 e v2 sono conservate separatamente. Il manifest punta solo
  agli asset attivi; gli asset approvati mantengono esattamente lo stesso hash.