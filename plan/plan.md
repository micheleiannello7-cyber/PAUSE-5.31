# PAUSE — Home più compatta e premium (carousel, bottom bar, atmosfera, bordi luminosi)

Restyling della sola Home di PAUSE: categorie in carousel orizzontale, bottom bar in stile glass che segue il tema, sfondo atmosferico navy e bordi delle card con luce ambientale delicata.
Subito dopo (stessa consegna, già concordato): nuova schermata Premium con i nuovi prezzi e primo passo dell'onboarding alleggerito.

## Per chi è
Utenti di PAUSE che aprono la Home più volte al giorno per una "pausa" di curiosità: devono trovare la storia del giorno e le proprie categorie senza scorrere, in un ambiente visivo calmo, scuro e coerente, che non affatica nell'uso prolungato.

## Funzionalità ed esperienza

### 1. Categorie — carousel orizzontale
- La griglia 2×4 di "Le tue categorie" viene sostituita da una sola riga scorrevole a swipe manuale (nessun autoplay, nessuna freccia).
- Stesse categorie, stesse icone 3D, stessi colori, bordo colorato, barra luminosa in basso, stile glass/dark: cambia solo la disposizione e la dimensione.
- Card leggermente più piccole della versione a griglia (icona 3D ancora perfettamente riconoscibile).
- Su ogni larghezza di schermo: 3–4 card intere + una porzione della successiva sempre visibile (calcolata sulla larghezza, quindi mai tagliata "per caso").
- Sotto il carousel: piccolo indicatore lineare di posizione (come nel mockup), niente altro.
- Tutte le categorie restano raggiungibili scorrendo; il tap su una card mantiene il comportamento attuale.

### 2. Rimozione di "Vedi tutte"
- Il link "Vedi tutte" sparisce del tutto; l'intestazione resta solo "Le tue categorie".
- L'elenco completo resta disponibile dal tab Argomenti.

### 3. Bottom bar — stile del mockup
- Barra scura, glass, attaccata al bordo inferiore con solo gli angoli superiori arrotondati.
- Quattro voci: **Home · Argomenti · Salvati · Profilo** (stesse destinazioni di oggi; il secondo tab passa da "Esplora" ad "Argomenti").
- Icone lineari della stessa famiglia: casa arrotondata; per Argomenti una piccola forma a card rettangolare (non la bussola del mockup, come richiesto); segnalibro; profilo.
- Voce attiva: icona e testo nel colore del tema con alone morbido e un sottile indicatore sotto. Il resto della barra resta neutro/scuro.

### 4. Colore dinamico dal tema
- La palette accento scelta nel Profilo (blu, viola, verde, rosso, ecc.) pilota: icona/testo attivo, glow, indicatore, riflesso sottile della barra, tinte dello sfondo e luce dei bordi.
- Toni sempre scuri, desaturati, mai neon.

### 5. Sfondo atmosferico della Home
- Un unico sistema: base navy/blue-black profonda con 2–3 diffusioni luminose molto morbide (in alto a sinistra, a destra a metà, in basso) e centro scuro per la leggibilità del testo.
- Cambia solo la tonalità in base al tema (blu → cyan/blu; viola → indigo/violetto; verde → teal/smeraldo; rosso → burgundy/carminio attenuato).
- Nessuna stella, pianeta, texture, particella o forma geometrica. Sfondo statico (niente animazioni) per non pesare sullo scrolling.

### 6. Bordi delle card
- Card storia principale, card categoria e ogni altra card della Home ricevono un bordo sottilissimo con glow diffuso nel colore del tema, quasi impercettibile.
- I colori propri delle categorie restano: la luce del tema si somma come riflesso ambientale, non li sostituisce.
- Struttura e contenuto della card storia non cambiano.

### 7. Ciò che non cambia
- Nessun intervento su backend, dati, autenticazione, contenuti, audio/TTS, salvataggi, progressi, funzioni dei tab.
- Nessuna sezione "Storie in evidenza" o altro contenuto sotto le categorie.

## Flusso utente
1. Apro l'app → Home con sfondo atmosferico nel tono del mio tema, logo e contatore in alto come oggi.
2. Card della storia principale con bordo appena illuminato → tap = apertura storia come oggi.
3. Sotto, "Le tue categorie": scorro a destra con il pollice, l'ultima card spunta a metà e mi invita a trascinare; tap su una card = comportamento attuale.
4. Bottom bar: tocco Argomenti/Salvati/Profilo → la voce si accende nel colore del tema. Cambio palette nel Profilo → sfondo, bordi e barra si ritingono all'istante.

## Sensazione UI/UX
Ambiente unico e coordinato: sfondo → card → luce sottile sui bordi → contenuto → bottom bar. Dark navy/near-black, accenti nel colore del tema usati con parsimonia, glass, angoli arrotondati, molto spazio negativo. Illuminazione "ambientale" e mai fluorescente; Home più corta verticalmente e più ricca.

## Fasi

### Fase 1 — Home (costruita ora)
Carousel categorie, rimozione "Vedi tutte", bottom bar glass a tema, icone lineari, sfondo atmosferico adattivo, bordi luminosi delicati, verifica su larghezze diverse.

### Fase 2 — Premium e onboarding (già concordata: parte subito dopo la fase 1, stessa consegna)
- Prezzi: Mensile €3,99 · Annuale €29,99 con claim "€2,49/mese", "Risparmi 37%" e 7 giorni gratis · A vita €49,99.
- Schermata Premium rifatta da zero mantenendo l'hero con le 3 copertine a ventaglio; mostra solo vantaggi reali: audio completo (4 voci, 2×, timer, offline, ascolto in background), scegli tu la storia, playlist "pausa da 10 minuti", statistiche avanzate e recap, preferiti illimitati (gratis 20), 6 storie a sessione e pausa di 2 h (invece di 5 / 4 h), accesso anticipato 7 giorni, 5 colori accento. "Lezioni guidate" rimossa.
- Onboarding: primo passo con solo login Google/Apple + nome; genere ed età dietro un link "Aggiungi dettagli (facoltativo)".

### Fase 3 — Successive (non ora)
- Abbonamenti reali via RevenueCat al posto dell'attivazione anteprima.
- Ricerca storie per titolo/argomento.

## Assunzioni
- Il mockup guida solo: carousel, atmosfera dello sfondo, luce dei bordi, stile della bottom bar. L'icona di Argomenti è a forma di card, non la bussola del mockup.
- L'indicatore lineare sotto il carousel viene aggiunto perché presente nel mockup; niente altro sotto le categorie.
- Header della Home (logo PAUSE, contatore in alto a destra) e card storia con i suoi pallini restano com'erano.
- I temi supportati sono le palette accento già presenti nell'app; nessuna nuova palette.
- Nel tema chiaro dell'app lo sfondo atmosferico resta scuro/navy come da richiesta ("molto scuro, profondo").
- Sfondo statico; nessun movimento atmosferico.
- La versione 2×4 resta in uso ovunque compaia fuori dalla Home (es. tab Argomenti).
- Per la card parzialmente visibile: circa il 40 % della card successiva a fine riga, con 3 card intere sui telefoni stretti e 4 su quelli larghi.
