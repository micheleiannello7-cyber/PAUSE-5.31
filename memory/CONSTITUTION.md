# PAUSE — COSTITUZIONE TECNICA E REGOLE PERMANENTI DEL PROGETTO

> ⚠️ REGOLA PERMANENTE E VINCOLANTE.
> Ogni agente AI che lavora su PAUSE deve leggere, comprendere e rispettare questo documento
> PRIMA di effettuare qualsiasi modifica, deploy, refactoring o intervento sul progetto.
> Vale indipendentemente da: agente, chat, sessione, deploy, funzionalità, modifica grafica,
> backend, frontend, ottimizzazione, bug fix, refactoring, aggiornamento dipendenze.
>
> Lingua dell'utente: **italiano**. Rispondere sempre in italiano.

---

## 1. REGOLA PRINCIPALE — NON ROMPERE CIÒ CHE GIÀ FUNZIONA

PAUSE è un'applicazione già sviluppata.

Il fatto che un agente ritenga che una determinata parte possa essere implementata "meglio" NON autorizza automaticamente a modificarla.

Prima di modificare qualsiasi cosa:

1. Comprendere come funziona attualmente.
2. Individuare quali componenti dipendono da quella parte.
3. Verificare che la modifica non rompa altre funzionalità.
4. Modificare solamente ciò che è necessario.
5. Mantenere tutto ciò che non è coinvolto nella richiesta.

NON riscrivere componenti funzionanti solo per renderli "più puliti", "moderni" o conformi alle preferenze dell'agente.

## 2. PRIORITÀ ASSOLUTE

In caso di conflitto tra istruzioni, utilizzare questo ordine di priorità:

1. Sicurezza e integrità dei dati
2. Funzionamento attuale dell'app
3. Requisiti espliciti dell'utente
4. Questa Costituzione
5. Compatibilità con l'architettura esistente
6. Performance e scalabilità
7. Pulizia/refactoring del codice
8. Preferenze personali dell'agente

Un agente NON deve sacrificare una funzionalità esistente per ottenere un codice teoricamente più elegante.

## 3. NON MODIFICARE CIÒ CHE NON È STATO RICHIESTO

Se l'utente chiede una modifica specifica: MODIFICARE SOLAMENTE CIÒ CHE È NECESSARIO PER OTTENERE QUELLA MODIFICA.

Non modificare automaticamente: altre schermate, colori, font, layout, animazioni, database, API, autenticazione, TTS, sistema Premium, algoritmo, navigazione, componenti non coinvolti — a meno che sia tecnicamente indispensabile.

Se una modifica richiede realmente di intervenire su un'altra parte dell'app, spiegarne il motivo prima di procedere quando possibile.

## 4. NON RISCRIVERE L'APP

È vietato effettuare automaticamente: riscritture complete, migrazioni massicce, sostituzioni dell'intero frontend/backend/database/framework, refactoring globale — solo perché una soluzione diversa potrebbe essere teoricamente migliore.

Preferire sempre: **MODIFICA INCREMENTALE → TEST → VERIFICA → MODIFICA SUCCESSIVA.**

## 5. BACKEND E DATABASE

Il database contiene dati importanti.

NON: cancellare dati, resettare il database, eliminare collezioni/tabelle, modificare strutture in modo distruttivo, cambiare identificativi esistenti, alterare dati delle storie, eliminare progressi degli utenti — senza una richiesta esplicita e una procedura sicura.

Qualsiasi modifica allo schema deve essere: compatibile con i dati esistenti, non distruttiva, migrabile, verificata prima del deploy.

NON utilizzare dati fittizi al posto dei dati reali esistenti.

## 6. CONTENUTI DI PAUSE

Le storie di PAUSE sono contenuti PRE-GENERATI.

Il modello è: **GENERAZIONE → SALVATAGGIO → DISTRIBUZIONE** (NON: utente → richiesta AI → generazione).

Storie, capitoli, introduzioni, immagini e audio già esistenti sono ASSET DI PRODUZIONE.
NON rigenerarli automaticamente. NON sostituirli con placeholder. NON modificarli durante un normale intervento tecnico.

## 7. AUDIO / TTS

Gli audio TTS già presenti sono asset esistenti. Premere "Ascolta" deve utilizzare l'audio già disponibile.

NON generare nuovamente audio durante la normale esperienza dell'utente. NON eliminare file audio esistenti. NON cambiare il sistema TTS senza una richiesta specifica.

## 8. IMMAGINI E COVER

Le immagini e le cover già generate fanno parte dell'identità visiva di PAUSE.

NON sostituirle automaticamente. NON rigenerarle solo perché un agente preferisce un altro stile. NON cambiare i riferimenti alle immagini senza verificare che tutti i componenti che le utilizzano continuino a funzionare.

## 9. DESIGN UI/UX

PAUSE ha un'identità visiva precisa. Il design deve rimanere coerente con:

- estetica premium
- dark navy / near-black
- accenti cyan/turchese
- glassmorphism
- immagini cinematiche realistiche
- bordi arrotondati
- tipografia moderna
- ampio spazio negativo
- interfaccia editoriale
- sensazione premium e tecnologica

NON introdurre casualmente: colori completamente nuovi, stili gaming, neon eccessivo, dashboard style, elementi troppo colorati, icone inutili, componenti visivamente incoerenti.

Quando viene richiesta una modifica grafica, mantenere sempre la stessa identità visiva.
(Riferimenti nel codice: `frontend/src/theme.ts`, `frontend/src/onboarding-palette.ts`, prop `glass` di `CategoryArtwork`/`CategoryGrid`.)

## 10. FUNZIONALITÀ ESISTENTI

Quando viene modificata una schermata, TUTTE LE FUNZIONALITÀ GIÀ PRESENTI devono continuare a funzionare, salvo esplicita richiesta contraria.

Prima di rimuovere un elemento chiedersi: "Questo elemento ha una funzione oltre alla sua presenza visiva?"

Non eliminare pulsanti, dati, eventi, navigazione o funzioni semplicemente perché non sono immediatamente visibili nel codice modificato.

## 11. REFACTORING

Consentito solamente quando: è necessario per la modifica richiesta; riduce concretamente un problema; non modifica il comportamento dell'app; è verificabile.

NON fare refactoring globale durante una normale richiesta di modifica.

## 12. PERFORMANCE E SCALABILITÀ

PAUSE deve crescere mantenendo bassi i costi. Principi permanenti:

- contenuti AI pre-generati, immagini pre-generate, audio TTS pre-generato
- nessuna generazione AI inutile durante l'utilizzo
- evitare query database inutili e richieste duplicate
- utilizzare caching quando appropriato
- utilizzare storage/CDN per asset pesanti quando disponibile
- non utilizzare il backend come proxy inutile per grandi file
- minimizzare bandwidth e operazioni server

NON introdurre servizi infrastrutturali complessi senza reale necessità (microservizi, Kubernetes, Redis, code, sistemi distribuiti, servizi esterni). La semplicità è una caratteristica dell'architettura.

## 13. COSTI

Prima di introdurre un servizio esterno chiedersi: è realmente necessario? può essere fatto con l'infrastruttura esistente? genera un costo ricorrente? aumenta il costo per utente? esiste una soluzione più semplice?

Preferire sempre: **BASSI COSTI + BUONA PERFORMANCE + SEMPLICITÀ + PORTABILITÀ.**

## 14. NESSUN AI RUNTIME NON NECESSARIO

Non introdurre chiamate a modelli AI durante: apertura della Home, apertura di una storia, lettura, navigazione, raccomandazioni normali, caricamento immagini, riproduzione audio — se il risultato può essere ottenuto dai dati già presenti.

L'AI va usata principalmente durante la PRODUZIONE DEI CONTENUTI.

## 15. PORTABILITÀ

Utilizzare: standard comuni, API documentate, database esportabile, asset esportabili, configurazioni documentate, variabili d'ambiente.

L'app deve poter essere migrata in futuro senza una riscrittura completa.

## 16. DEPLOY

Prima di ogni deploy importante:

1. Verificare il codice.
2. Verificare eventuali errori di build.
3. Verificare le funzionalità coinvolte.
4. Verificare che il database sia integro.
5. Verificare che gli asset siano accessibili.
6. Verificare che non siano stati eliminati dati.
7. Verificare che le funzionalità non coinvolte non siano cambiate.

Un deploy NON è riuscito solo perché la build termina senza errori.

## 17. TEST DI REGRESSIONE

Dopo ogni modifica significativa verificare almeno: apertura app, login, registrazione, Home, categorie, apertura storia, lettura, immagini, audio, progressi, completamento storia, preferiti, personalizzazione, limite di utilizzo, Premium, navigazione.

Se la modifica riguarda solo una parte dell'app, il test può essere proporzionato, ma vanno controllate almeno le funzionalità direttamente collegate.

## 18. BACKUP

**BACKUP PRIMA, MODIFICA DOPO.** Mai operazioni distruttive senza possibilità di rollback. Ogni migrazione deve permettere il ritorno alla versione precedente.

## 19. GESTIONE DELLE RICHIESTE AMBIGUE

Se una richiesta può essere interpretata in più modi e una interpretazione potrebbe modificare significativamente l'app: NON scegliere arbitrariamente la soluzione più invasiva.

Preferire la soluzione: minima, reversibile, compatibile, coerente con l'app esistente. Se la differenza è sostanziale, chiedere chiarimento.

## 20. REGOLA "MINIMUM CHANGE"

**MODIFICARE IL MINIMO INDISPENSABILE PER OTTENERE IL RISULTATO RICHIESTO.**

- "sposta questo pulsante" ≠ "rifacciamo tutta la schermata"
- "aggiungi questa funzione" ≠ "riscriviamo il sistema"
- "ottimizza questa query" ≠ "cambiamo database"

## 21. PRIMA DI OGNI INTERVENTO

1. **COSA ESISTE?** Comprendere l'implementazione attuale.
2. **COSA È STATO CHIESTO?** Identificare esattamente la modifica richiesta.
3. **COSA DEVE RIMANERE INVARIATO?** Identificare tutte le funzionalità non coinvolte.
4. **QUAL È LA MODIFICA MINIMA?** Implementare la soluzione meno invasiva.
5. **COSA POTREBBE ROMPERSI?** Controllare dipendenze e possibili regressioni.
6. **COME VERIFICO?** Eseguire i test necessari prima di considerare concluso il lavoro.

## 22. DOCUMENTAZIONE INTERNA

Mantenere aggiornata la documentazione interna (`/app/memory/PRD.md` e questo file) su: architettura, database, componenti principali, API, autenticazione, storage, sistema audio, sistema immagini, sistema Premium, raccomandazione, struttura storie, dipendenze, variabili d'ambiente, deploy, rollback.

Quando una modifica importante cambia l'architettura, aggiornare la documentazione.

## 23. NESSUNA "OTTIMIZZAZIONE" NON RICHIESTA

Un agente NON deve modificare autonomamente parti dell'app solo perché "potrebbero essere migliori", "sono obsolete", "io preferisco questa soluzione", "questa architettura è più moderna", "questa libreria è più elegante".

Se non c'è un problema concreto, NON CAMBIARE.

## 24. PROTEGGERE IL LAVORO GIÀ FATTO

Tutto ciò che è già sviluppato e funziona è intenzionale fino a prova contraria. Non presumere che il codice precedente sia sbagliato. Prima di sostituire qualcosa, comprenderne la funzione e le dipendenze.

## 25. REGOLA FINALE

PAUSE evolve per aggiunte e miglioramenti incrementali, non attraverso continue riscritture.

Ogni nuovo agente deve comportarsi come se entrasse in un progetto sviluppato da un altro team e dovesse rispettarne l'architettura.

NON ricominciare da zero. NON "ripulire" ciò che non è stato richiesto. NON modificare funzionalità esistenti senza motivo. NON sacrificare stabilità per una soluzione teoricamente migliore. NON perdere dati o contenuti esistenti. NON introdurre costi ricorrenti senza necessità. NON rigenerare contenuti già presenti.

**CAPISCI → PROTEGGI → MODIFICA IL MINIMO → TESTA → VERIFICA → DEPLOYA.**

---

## Note operative correnti (contesto ambiente)

- Integrazioni AI: solo `EMERGENT_LLM_KEY` (gratuita). Stripe ed ElevenLabs sono volutamente NON configurati: non chiedere quelle chiavi se l'utente non lo richiede.
- File protetti (mai modificare): `frontend/metro.config.js`, campo `main` di `package.json`, URL/porte nei `.env` (`EXPO_PACKAGER_PROXY_URL`, `EXPO_PACKAGER_HOSTNAME`, `EXPO_PUBLIC_BACKEND_URL`, `MONGO_URL`).
- Tutte le rotte backend sotto `/api`, binding `0.0.0.0:8001`.
