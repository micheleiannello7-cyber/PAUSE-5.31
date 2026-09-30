# PAUSE — copertine, ripresa 25 settembre 2026

## Autorizzazione e confini
L'utente ha chiesto di riprendere creazione/correzione finché c'è credito e ha confermato. Intervento limitato agli asset di copertina e ai relativi metadati. Nessuna modifica al codice di frontend/backend, alle storie, ai capitoli, all'audio o alle preferenze. Costituzione rispettata: backup prima, staging, controllo visivo, pubblicazione esplicita.

## Baseline e generazione
- `resume_baseline.json`: 437 ID/titoli, metadati originali e SHA-256 dei documenti esclusi i campi delle copertine.
- `a08de6ae79d149199e4b0a75fc7b3477.json`: 10 copertine mancanti completate; errori 0; nessun arresto per quota.
- Master WebP, hero 1200px e thumb 600px nello storage gestito, nessuna generazione durante l'uso dell'app.

## Revisione
- `../cover_review_final/catalog.json`: snapshot delle 428 immagini disponibili all'inizio della revisione mentre la generazione proseguiva; download riusciti 428/428. Le altre 9 nuove immagini sono state visionate separatamente.
- Esaminate direttamente tutte le 36 tavole del catalogo. I due controlli automatici PDF iniziali hanno omesso alcune testate stampate: NON assumerli come prova di assenza di errori. Prevale il controllo diretto delle immagini e dei master.
- Le ripetizioni fra fotografie tematicamente pertinenti non sono state sostituite automaticamente.
- Conservati i casi dubbi o intenzionali: cavallo con coperta zebrata (#029, esperimento descritto nei capitoli), doppio arcobaleno (#186, colori secondari effettivamente invertiti), metafore surreali coerenti. Nessun restyling arbitrario.

## Interventi tracciati
- `corrections_orbit.json`: Sole sulla traiettoria → composizione con Sole chiaramente interno all'orbita. Master verificato e pubblicato.
- `corrections_local_01.json`: 3 correzioni locali senza AI (mancino specchiato, testate orologio/telescopio ritagliate). Verificate e pubblicate.
- `corrections_editorial_01.json`: 7 rigenerazioni mirate (etichetta, giramenti, caffè/tre mani, deserto/spiaggia, Voyager/galassia, pelle/manicure, clima/strumento astronomico). Verificate e pubblicate.
- `corrections_local_02.json`: 7 ritagli di testate/marchi/caption indesiderati; controllati visivamente e pubblicati senza AI.
- `corrections_editorial_02.json`: 9 soggetti errati/artefatti confermati (migrazione, due storie di api mellifere, gladiatori, melodie, evoluzione biologica, Zanzibar, spezie, caricatore). **BLOCCATO DAL CREDITO**: il primo tentativo, `bird-migration`, ha ricevuto `Budget has been exceeded`; nessuna immagine generata in questo batch, nessuna sostituzione eseguita, nessun retry. Report marcato `stopped`, `stop_reason=budget_or_quota`.

Totale pubblicato: **10 copertine nuove + 17 copertine esistenti corrette = 27 ID aggiornati**. La correzione dell'orbita è un secondo passaggio su una delle 10 nuove, non una ventottesima storia. 10 correzioni effettuate localmente senza AI; 18 immagini AI prodotte con successo (10 nuove + 1 orbita corretta + 7 sostituzioni).

Ogni cartella `*_staged/` contiene `report.json` con metadati precedenti/successivi, candidati e `previous_originals/` per i master sostituiti. I vecchi oggetti nello storage non vengono cancellati. Non ripetere generazioni già pagate: riusare i candidati e consultare prima i report.

## Verifiche finali completate
- Suite `backend/tests/test_iter33_cover_resume_readonly.py`: **8/8 PASS**; report `test_reports/iteration_1.json` e JUnit `test_reports/pytest/pytest_results.xml`.
- Catalogo 437/437, ID identici alla baseline; digest SHA-256 non-cover identici per tutti i documenti, esattamente 27 ID con copertina modificata. Titoli, capitoli e riferimenti audio invariati.
- Tutti i 27 dettagli storia HTTP 200; 54 media hero/thumb HTTP 200, WebP, portrait, vincoli di dimensione rispettati, storage path e digest validi.
- Tutti i report delle pubblicazioni coerenti e backup degli originali disponibili; nessun processo di generazione attivo.
- Anteprima mobile 390×844: Home, categorie e lettori (colore, orbite, Hilbert, deserti, caffè) con apertura capitolo/navigazione verificati, nessun errore console. Nessuna verifica su dispositivo fisico dell'utente.
- I 9 ID sospesi sono identici alla baseline, mantenendo le vecchie copertine. Nessun retry per budget, nessuna chiamata AI durante i test.
- Il tester ha segnalato soltanto un flag di onboarding preesistente (`ALWAYS_SHOW_ONBOARDING=true`, intenzionale fase test), non una regressione di questo intervento: lasciato invariato come richiesto dalla Costituzione.

## Ripresa futura
Prossimo intervento limitato alle 9 correzioni in `corrections_editorial_02.json`, solo dopo nuova disponibilità di credito e richiesta dell'utente. Il report contiene intenzionalmente uno stop persistente che impedisce retry accidentali; non rimuoverlo o aggirarlo durante normali verifiche. Restano da generare TUTTI e 9 i candidati del batch 02, non c'è un'immagine pagata da recuperare in quella cartella.