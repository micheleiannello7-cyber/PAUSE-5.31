# PAUSE — Product Requirements (Preview)

> ⚠️ **OBBLIGATORIO PRIMA DI QUALSIASI INTERVENTO:** leggere e rispettare
> [`/app/memory/CONSTITUTION.md`](./CONSTITUTION.md) — la Costituzione tecnica permanente
> e vincolante di PAUSE (regola "minimum change", niente riscritture, niente rigenerazione
> di contenuti/asset, niente AI a runtime, identità visiva dark-navy/cyan/glass).
> Lingua dell'utente: **italiano**.

## Ripristino PAUSE-5.30 + ritocchi (30 settembre 2026 — sessione corrente)
- Repo PAUSE-5.30 importato in /app (preservati .git/.emergent/.env/node_modules); backend: 12 categorie, 493 storie; `.env` backend esteso con EMERGENT_LLM_KEY, ENFORCE_LIMIT=false, TTS_ENABLED=false.
- ESPLORA: in griglia Argomenti/onboarding l'oggetto 3D (`CategoryArtMark` plain) è intero, sporge solo il bordo alto (`ALL_POKE=14`, tessera non più `overflow:hidden`, sfondo con borderRadius). In Home `HomeExploreTile`: art 106, top 0 su paddingTop 16 → sporgono solo ~16px.
- Autofocus lettura rallentato del 20%: `SCROLL_MS` 720 → 864.
- Transizione Home↔lettura: `MORPH_DURATION` 680; apertura parte 2 frame dopo la misura, la Home (`leave`=making) si sposta nello stesso frame con stesso passo; il lettore si monta solo a fine corsa (tolto commit anticipato); ritorno senza `InteractionManager`.
- Finale storia: "Da ricordare" in contenitore vetro (`remember-card`, barra accento cyan); separatore netto + titolo "Prossima scoperta" più grande (17); copertina della prossima storia `flexGrow` (min 190) senza freccia; dati con icone 3D (`StoryInfoGrid` testID `next-info-grid`); tasti Home/Leggi in fondo alla schermata.

## Finale storia — dissolvenza d'ingresso + conferma ampia del Salva (30 settembre 2026)
- Richiesta utente: (1) far comparire il riquadro finale con una dissolvenza morbida arrivando
  in fondo; (2) conferma "Aggiunto ai salvati" più visibile toccando Salva nel finale.
- Dissolvenza: `reader-ending.tsx` riceve `scrollY/pageH/endTop` (gli stessi shared value del
  `ReaderEndingBackdrop`) e avvolge il contenuto in `Animated.View` con opacity 0→1 + translateY
  26→0 interpolati su `[endTop - pageH*0.5, endTop - pageH*0.12]`: il blocco "Da ricordare" sale e
  compare appena prima di toccare il fondo. Fallback a opacità piena se i valori non ci sono.
- Conferma Salva: nuovo `save-confirm-toast.tsx`, banner FISSO rispetto allo schermo montato nel
  root del deep-dive (fuori dallo scroll), centrato in basso (`bottom: insets.bottom + xxl`), disco
  cyan con segnalibro + testo. `ReaderEnding` non usa più il mini-toast sul tasto Salva: `handleBookmark`
  dà l'haptic e chiama `onSaved(willSave)`; il deep-dive incrementa un trigger `{saved, n}` così anche
  salvataggi ripetuti rilanciano l'animazione. testID `save-confirm`. Like/Condividi invariati.
- Nuove chiavi i18n `saved_confirm` / `unsaved_confirm` (IT "Aggiunto ai salvati" / "Rimosso dai salvati").
- Verifica visiva 390×844: banner "Aggiunto ai salvati" ben visibile in basso, finale con dissolvenza.

## Schermata finale storia — variante "Prossima scoperta" (mock B) integrata (30 settembre 2026)
- Richiesta utente: integrare la modifica della schermata finale della storia lasciata pronta
  dall'agente precedente. Trovati i mockup `frontend/public/mock/ending-{a,b,c}.html`; l'allegato
  visivo dell'utente corrisponde a **ending-b.html** → integrata quella variante.
- `src/components/reader-ending.tsx` rifatto secondo mock B (nessuna GlassSurface/SectionDivider):
  occhiello "DA RICORDARE" con codina luminosa, sommario editoriale (Sora) sullo sfondo, linea cyan,
  3 pill (categoria · minuti · N capitoli), Mi piace/Salva/Condividi affiancati (riuso `EndActionButton`,
  testID invariati like-button/bookmark-button/share-story) e card **Prossima scoperta** con copertina
  (`StoryHero`), titolo `HighlightedTitle`, freccia `GlowOrb` (testID next-story) + chips tipo/categoria/min.
  Fallback al vecchio pulsante testuale finché la prossima storia non è precaricata.
- `app/deep-dive/[id].tsx`: prefetch `useQuery(["nextStory", id, userId])`, prop `next={nextStory}`
  passata a `ReaderEnding`; `onNext` riusa la storia precaricata (anteprima == storia che si apre),
  controllo crediti/limite invariato.
- Nuova chiave i18n `next_discovery` (IT "Prossima scoperta" / EN "Next discovery").
- Verifica visiva 390×844: finale renderizza come da mock B con dati reali della prossima storia.

## Ripristino ambiente da GitHub PAUSE-5.29 (30 settembre 2026 — sessione corrente)
- Richiesta utente: «https://github.com/micheleiannello7-cyber/PAUSE-5.29.git questa è la mia app, Estrapolala e dammi la preview pronta completa grazie».
- Repo clonato e copiato in `/app` preservando i file di piattaforma (`.git`, `.emergent`,
  `.env` di frontend/backend, `node_modules`). Nessuna riscrittura di codice/contenuti/asset
  (rispetto della CONSTITUTION: regola "minimum change").
- **Backend**: `pip install -r requirements.txt` (con `--extra-index-url` per `emergentintegrations`).
  `backend/.env` esteso con `EMERGENT_LLM_KEY` (Universal Key), `ENFORCE_LIMIT="false"`,
  `TTS_ENABLED="false"`. Seed automatico all'avvio: **12 categorie, 493 storie**. `/api/health` = ok.
- **Frontend**: Expo SDK 57, `yarn install` completato (le `@react-native-vector-icons/*` mancavano
  nei node_modules del template → reinstallate). Metro `:3000`, preview attiva.
- **Icone 3D categorie**: servite da `/api/category-media/<id>` via `media_cache/` locale (HTTP 200,
  nessun re-upload necessario dopo questo fork). Warning non bloccanti "nessuna storia con questo id"
  su alcune cover orfane (fallback previsto).
- Verifica visiva 390×844: onboarding (login Google + guest) e step selezione interessi con tutte
  le 12 tessere 3D renderizzano correttamente.

## Ripristino ambiente da GitHub PAUSE-5.26 (29 settembre 2026 — sessione corrente)
- Richiesta utente: «https://github.com/micheleiannello7-cyber/PAUSE-5.26.git questa è la mia app, Estrapolala e dammi la preview pronta completa grazie».
- Repo importato preservando i file di piattaforma. Dipendenze backend/frontend installate.
- **Backend**: seed all'avvio **12 categorie, 441 storie**. `/api/health` = ok.
  Warning non bloccanti: alcune cover orfane ("nessuna storia con questo id") con fallback Unsplash.
- **Test credentials**: creato utente test `user_testpause001` (pause.test@example.com) con
  session token Bearer in `/app/memory/test_credentials.md` (l'app usa SOLO login social
  Google/Apple — niente email/password).
- **Fix auth**: retry su `authMe()` al cold boot in `frontend/src/auth.tsx` — un 401
  transitorio della challenge edge non cancella più il token di sessione.
- **Test (iteration 2)**: 14/14 backend PASS, frontend PASS — flusso autenticato,
  4 tab (Home/Explore/Saved/Profile), lettore 6 capitoli, bookmark persistente.
  TTS disabilitato by design in preview (`TTS_ENABLED="false"`).

## Home restyle + Premium v3 + onboarding snello (giugno 2026 — sessione corrente)
- **Home** (`app/(tabs)/discover.tsx`): categorie in carousel orizzontale
  (`src/components/home-category-carousel.tsx`: 4 card intere + 40% della successiva, 3 sotto 360px,
  indicatore lineare), rimosso "Vedi tutte". Sfondo atmosferico generativo statico
  (`home-backdrop.tsx`, colori `atmos*` del tema). Bordi/glow con `colors.brand` su card storia,
  tessere, resume card e `story-morph` homeEdge.
- **Bottom bar** custom `src/components/glass-tab-bar.tsx` (Tabs `tabBar` prop): glass, angoli alti
  arrotondati, voce attiva nel colore del tema con alone + indicatore; icona Argomenti = `albums`.
  testID tab-home/tab-explore/tab-saved/tab-profile invariati.
- **Premium** (`app/premium.tsx` rifatto, hero a ventaglio invariato): prezzi in `src/premium.ts`
  Mensile €3,99 · Annuale €29,99 (claim `YEARLY_PER_MONTH` = €2,49/mese, Risparmi 37%, 7 gg gratis) ·
  A vita €49,99. Tabella Gratis/Premium con SOLE funzioni reali (5→6 storie, 4→2 h pausa, audio,
  catalogo, playlist, statistiche, preferiti 20→∞, accesso anticipato 7 gg, 1→5 colori accento).
  Attivazione ancora placeholder (RevenueCat = fase successiva).
- **Onboarding** (`onboarding-profile.tsx`): passo 1 = login + nome; genere/età dietro
  "Aggiungi dettagli (facoltativo)" (`onboarding-profile-more`).
- Test: `/app/test_reports/iteration_1.json` — tutti PASS.

## Icone 3D categorie mancanti dopo il fork (30 settembre 2026)
- Causa: l'Object Storage del nuovo ambiente era vuoto → `/api/category-media/*` rispondeva 404
  e il frontend mostrava il fallback a linea. Le cover storie funzionavano perché in `media_cache/`.
- Fix: ri-upload dei byte già approvati (`backend/category_art/reference-3d-v4/<id>.webp`) agli stessi
  percorsi di `import-report.json`. Script idempotente: `python backend/restore_reference_category_art.py`
  (eseguirlo a ogni nuovo fork se le icone tornano a linea). Nessuna rigenerazione AI.

## Summary
App mobile Expo (React Native + FastAPI + MongoDB) che trasforma i momenti morti in
curiosità / mini-lezioni, con una "pausa" intenzionale tra le sessioni. Contenuti
pre-generati (storie, capitoli, copertine, audio TTS) distribuiti dal backend.

## Ripristino ambiente da GitHub PAUSE-5.21 (giugno 2026 — sessione corrente)
- Richiesta utente: «Questa è la mia app https://github.com/micheleiannello7-cyber/PAUSE-5.21.git rendi la preview disponibile completa».
- Repo clonato e copiato in `/app` preservando i file di piattaforma (`.git`, `.emergent`,
  `.env` di frontend/backend). Env NON modificati salvo aggiunta chiavi backend.
- **Backend**: FastAPI `:8001`, MongoDB locale, `pip install -r requirements.txt` completato.
  `backend/.env` esteso con `EMERGENT_LLM_KEY` (Universal Key) e `ENFORCE_LIMIT="false"`.
  Seed automatico all'avvio: **12 categorie, 430 storie**. `/api/health` = ok.
- **Frontend**: Expo SDK 57, `yarn install` completato (vector-icons presenti). Metro `:3000`,
  preview attiva. Onboarding + tessere 3D categorie renderizzano correttamente a 390×844.


## Ripristino ambiente da GitHub PAUSE-5.18 (25 settembre 2026 — sessione corrente)
- Richiesta utente: «Questa è la mia app, estrapolala e dammi la preview pronta completa».
- Codice clonato da `github.com/micheleiannello7-cyber/PAUSE-5.18` e copiato in `/app`
  preservando i file di piattaforma (`.git`, `.emergent`, `.env` di frontend/backend).
- **Backend**: FastAPI su `:8001`, MongoDB locale, `requirements.txt` installato
  (con `--extra-index-url` per `emergentintegrations`; aggiunti i pacchetti mancanti
  `emoji`, `elevenlabs`, `fal_client`, ecc.). Seed automatico all'avvio: **430 contenuti**,
  12 categorie. Health `/api/health` = ok.
- **Frontend**: Expo SDK 57. Eseguito `yarn install` (le vector-icons
  `@react-native-vector-icons/*` mancavano nei node_modules del template → bundling
  fallito finché non installate). Metro su `:3000`, preview attiva.
- **Env**: `backend/.env` esteso con `EMERGENT_LLM_KEY` (Universal Key, gratuita) e
  `ENFORCE_LIMIT="false"`. URL/porte nei `.env` NON modificati. Stripe/ElevenLabs
  volutamente non configurati (integrazioni idle).
- **Copertine**: sync all'avvio verso l'Object Storage gestito. La prima sync locale
  era abortita da un 500 transitorio dell'Object Storage sotto carico → aggiunta
  resilienza per-file in `backend/covers_sync.py` (retry ×3 + continue, nessuna
  generazione AI, nessun costo). Resync finale: **58 caricate, 265 già presenti,
  16 senza storia (ritirate), 0 fallite**. Le storie senza copertina generata usano il
  fallback hero Unsplash già previsto.

## Verifica preview (sessione corrente)
- `/api/health` = ok, `/api/categories` e `/api/stories` restituiscono dati.
- Frontend caricato a 390×844: intro cinematica (logo PAUSE, CTA "Start your pause")
  → onboarding "What do you want to read?" (card glass Curiosità / Mini lezioni)
  navigabile. Nessun errore di bundling dopo `yarn install`.

## Architettura
- `backend/server.py`: API `/api/*`, seed idempotente all'avvio, sync asset in background
  (copertine locali + importate, artwork categorie, cache media, adozione audio TTS legacy).
- `backend/storage.py`: helper Object Storage gestito (richiede `EMERGENT_LLM_KEY`).
- `frontend/app/*`: expo-router (intro, onboarding, tabs, browse, playlist, premium,
  stats, deep-dive, ecc.). Tema in `frontend/src/theme.ts`, i18n in `frontend/src/i18n.tsx`.

## File protetti (mai modificare)
`frontend/metro.config.js`, campo `main` di `package.json`, URL/porte nei `.env`
(`EXPO_PACKAGER_PROXY_URL`, `EXPO_PACKAGER_HOSTNAME`, `EXPO_PUBLIC_BACKEND_URL`, `MONGO_URL`),
`frontend/eas.json` (gestito da Emergent).

## Backlog / note
- Integrazioni a pagamento (Stripe, ElevenLabs) restano disattivate finché non richieste.
- Nessuna rigenerazione AI di contenuti/copertine/audio senza richiesta esplicita.

## Categorie 3D da riferimento — 25 settembre 2026
- Richiesta esplicita: rigenerare icone categorie fedeli all'allegato, incluse tessere
  dark arrotondate, font e luce inferiore accesa solo alla selezione. Conferma:
  «Si procedi, sii fedele all allegato». Con `all` tutte le luci sono accese.
- Pubblicata famiglia `reference-3d-v6`: 12 categorie reali + cristallo `all`.
  Beuta, Saturno, chip cyan, germoglio, zampa, busto classico, loto/Psicologia,
  testa con cervello/Corpo umano, libro, monete/Economia, tavolozza/Arte, montagna.
  Nessuna categoria aggiunta/rinominata; quelle dell'allegato non presenti ignorate.
- 13 WebP 480px (circa 334KB complessivi) salvati in Object Storage gestito;
  manifest `backend/category_art_manifest.json`. Vecchio manifest conservato in
  `backend/category_art/previous-glossy-3d-v5.json`; vecchi oggetti non cancellati.
  Sorgenti/crop/import report: `backend/category_art/reference-3d-v4/` (nome cartella
  di lavorazione; versione pubblicata v6). Script offline `import_reference_categories.py`.
  Nessuna AI a runtime, né modifiche a storie, copertine, audio, dati degli utenti.
- `CategoryGrid` condiviso da onboarding ed Explore: artwork grande, bordi SVG,
  Manrope Medium (approssimazione del font del riferimento, non identificabile con
  certezza dalla sola immagine), conteggi dinamici preservati, luce SVG/Animated 180ms.
  2 colonne su schermi piccoli, 3 standard, 4 tablet. `category-tile-effects.tsx`
  condiviso anche dalle tessere Home (qui la luce rappresenta il focus del mazzo).
- Palette dedicata in `src/theme.ts`, costante nei temi chiaro/scuro per rispettare
  il riferimento. `CategoryArtwork` ha variante `reference`; cache revision v6 anche
  per i badge. Logica/persistenza filtri invariata: all resta esclusivo.
- Self-test: 12 categorie API con versione v6; preview 390×844 IT/EN; caricamento
  icone, Scienza singola, 13 luci con Qualsiasi e passaggio Qualsiasi→Arte PASS.
  Lint file modificati PASS; nessun errore TypeScript nei file modificati.
- Verifica finale `test_reports/iteration_7.json`: backend 17/17 PASS (13 immagini,
  categorie e cutout badge); onboarding, salvataggio, selezioni, Home, intro storia,
  IT/EN 320/390/430, temi chiaro/scuro, assenza overflow/ID duplicati PASS.
  Test esclusivamente in preview browser; nessun dispositivo nativo disponibile.
  Driver animazione luci nativo iOS/Android, JS web per evitare warning di fallback.
- P0: nessun blocco nel perimetro richiesto.
- P1: validazione visiva dell'utente su dispositivo iOS/Android.
- P2: eventuali ritocchi delle singole icone solo su richiesta.

## Home statica + multi-selezione, barra lettura "Copertina" — 25 settembre 2026
- Richiesta: Home senza scroll (tutto in una schermata); tessere Home = categorie
  scelte in onboarding/Esplora, tutte accese; tocco accende/spegne singolarmente
  (non più esclusivo); il mazzo segue le categorie attive; se si spegne l'ultima
  accesa → avviso "Tieni attiva almeno una categoria" (toast ~2s + haptic errore).
- `discover.tsx`: `ScrollView` → `View` statico; il mazzo occupa lo spazio residuo
  (misurato a layout, `home-deck-area`), card alta = area − 20, clamp 170..width×1.2.
  Stato spente per utente in AsyncStorage `pause.home_off.<uid>` (`src/home-focus.ts`):
  si salvano le SPENTE così una categoria nuova parte accesa; se tutte accese il mazzo
  usa gli interessi originali (comportamento precedente). Chiave i18n `home_min_one_category`.
- Barra lettore (`reader-header.tsx`), variante "Copertina" scelta dall'utente fra 5
  mockup (route temporanea `/dev-header-options`, rimossa): miniatura copertina 42px
  (`StoryHero` thumb), titolo a sinistra mai troncato (corpo 15.5→13.5 per lunghezza,
  max 82 caratteri in DB verificati a 320/390px), occhiello "CAPITOLO n DI N" con icona
  libro (ultima pagina "DA RICORDARE" con segnalibro ambra), filo di progresso 2px a tutta
  larghezza sul bordo inferiore. Nuova prop `story` (+ `labelIcon`); animazioni
  reveal/solid/progress e badge audio (`corner`, centrato in altezza) invariati.
  `READER_HEADER_H` resta 96.
- Test `test_reports/iteration_8.json`: tutto PASS (Home statica 390/375, luci, toggle,
  toast, persistenza, mazzo filtrato, header lettore 320/390, intro→capitolo, fine).

## Lettura: contenitori capitoli dark-glass monocromatici — 25 settembre 2026
- Richiesta (solo raffinamento visivo + scroll, nessuna nuova schermata): miniatura
  header più grande; capitoli in contenitori vetro scuro premium/minimal con UNA sola
  famiglia cromatica per storia (dal tema/categoria) e variazioni lievi tra capitoli;
  fondo lettura dark-navy stabile; copertina solo nell'apertura (esce verso l'alto,
  non più espansa a tutto schermo dietro ai capitoli); schermata finale con lo sfondo
  cinematico dell'onboarding profilo; scroll/snap, barra superiore e pulsanti invariati.
- `src/story-palette.ts`: famiglie per categoria (spazio cyan→blu→viola, scienza/tecnologia
  cyan→blu, natura/geografia turchese→petrolio, storia/cultura/economia/animali ambra-oro,
  psicologia viola, arte magenta, corpo-umano rosa; default cyan). `chapterTint(cat, i, n)`.
  Il `glow_color` casuale dei capitoli nel DB NON è più usato nel lettore (dato intatto).
- `reader-section.tsx`: card 26px, fondo `surfaceDeep` traslucido (0.56–0.74), bordo
  tinta 0.34, riflesso superiore, alone 36px a 0.10, occhiello con quadratino+punto,
  titolo con evidenziazione nella tinta; divider rimosso dai capitoli (resta nel finale);
  fade fuori-fuoco 0.38→0.55 (più leggero). Testo/capitoli identici, nessun extra.
- `reader-cover-backdrop.tsx`: niente morph a sfondo; la card copertina trasla con lo
  scroll (`translateY: -y`, stretch al pull come prima). Prop `morphEnd/screenW/screenH`
  rimosse. `[id].tsx`: velo tinta 0.10→0 in alto sul fondo notte; nuovo
  `reader-ending-backdrop.tsx` (artwork `onboarding-profile-bg.jpg` + veli ONB) che
  compare da 0.55 pagina prima della fine. Header: miniatura 42→56px (raggio 14).
- Sistema di scroll a pagine (spring nativo / snapToOffsets web) NON toccato.
- Test `test_reports/iteration_9.json`: tutto PASS (intro, copertina fuori schermo sui
  capitoli, etichette 1..6, palette spazio/storia, finale con sfondo+pulsanti, 320/390).
- Ritocco su richiesta: contenitori più evidenti (bordo tinta 0.58, alone 48px a 0.22 +
  ombra, riempimento `onSurface` 0.04–0.075 + velo tinta 0.16→0.03 su base `surfaceDeep`
  0.55, riflesso superiore 0.95).

## Bug fix: card Home non si apriva toccando il titolo — 25 settembre 2026
- Causa: in `home-story-card.tsx` la fascia titolo (Reanimated `Animated.View`) aveva
  `pointerEvents: "box-none"` solo nello style → su web ignorato, il click sul titolo veniva
  assorbito e non raggiungeva il `Pressable` a tutta card. Fix: `pointerEvents="box-none"`
  come prop (e `pointerEvents="none"` sul pannello anteprima). Il tasto Ascolta resta attivo.
- Test `test_reports/iteration_10.json`: tap su titolo/angolo/immagine/chip aprono la storia;
  swipe non apre; long-press anteprima ok; tessere e "Vedi tutte" ok.


---

## Restore / Setup Log — 2026-09-26
- Estratta l'app dal repo GitHub `PAUSE-5.19` e ripristinata nell'ambiente di anteprima corrente.
- Backend (FastAPI + MongoDB): dipendenze installate, seed automatico all'avvio → 12 categorie e 430 contenuti; `/api/health` OK (db: true).
- Aggiunta `EMERGENT_LLM_KEY` in `backend/.env` per l'Object Storage delle copertine (init/get/put). Verificato: `/api/category-media/*` e `/api/media/{id}?size=thumb` restituiscono WebP 200. 64 copertine storie presenti + arte categorie.
- Frontend (Expo SDK 57): `yarn install` completato; Metro avviato; intro cinematica + onboarding renderizzati correttamente.
- File `.env` di ambiente (EXPO_PACKAGER_*, MONGO_URL) preservati, non sovrascritti.
- Stripe / TTS ElevenLabs lasciati disattivati come nella configurazione originale.


## Account: Google (Emergent Auth) + Apple + Ospite — giugno 2026
- Richiesta: accesso Google su Android (solo Google), Apple + Google su iOS, ospite ovunque;
  integrato nel passo profilo dell'onboarding (nickname/genere/età), non in una schermata a parte.
- Onboarding: `START_STEP = 1` → profilo (con `AuthBlock`) → argomenti (formato saltato, resta nei chip).
  CTA profilo: "Continua come ospite" (ospite) / "Continua" (connesso). Nome account precompila il nickname.
- Frontend: `src/auth.tsx` (`AuthProvider`/`useAuth`: loading|authenticated|guest, Google via
  `auth.emergentagent.com` → `POST /api/auth/session`, Apple via `expo-apple-authentication` →
  `POST /api/auth/apple`, token in SecureStore/localStorage `pause.session_token`, Bearer in `api.ts`).
  Dopo il login l'app adotta lo `user_id` dell'account (`adoptUserId`), al logout nuovo id ospite (`resetUserId`).
  `src/components/auth-block.tsx` (bottoni/"Connesso come"/Esci). Profilo: nome account, riga Accedi/Esci.
- Backend: `backend/auth.py` (router `/api/auth/*`: session, apple, me, logout; collezioni `users`,
  `user_sessions` con indici + TTL). `.env`: `APPLE_AUDIENCES` = bundle id + `host.exp.Exponent`.
  `app.json`: `ios.usesAppleSignIn`, plugin `expo-apple-authentication`.
- Apple verificabile solo su iPhone reale (non Expo Go web/Android). Test: `test_reports/iteration_1.json`.

## Transizione card Home ↔ lettura più fluida — giugno 2026
- Problema: alla fine dell'apertura il livello restava fermo finché scattava il timer di sicurezza
  (il lettore non segnalava mai "pronto" quando la copertina è limitata dal quadrato), poi lo scambio
  "di colpo"; il ritorno faceva la transizione inversa solo dalla presentazione (swipe), mai dai
  capitoli né col tasto indietro Android.
- `story-morph.tsx`: 640ms ease-out quintico; il lettore si monta sotto già a p≥0.6 (fondo opaco);
  la dissolvenza parte solo quando animazione finita E lettore pronto (`MorphHost.ready/markReady`);
  partenza solo con scheda a misura (`sheetStable`). Chiusura da capitolo: `fadeIn` (200ms) poi rientro.
- `deep-dive/[id].tsx`: `markReady` quando la card non cambia più altezza; `morphBack` da ogni sezione;
  `BackHandler` Android → stesso percorso inverso; copertina senza fade d'ingresso se `morph=1`.
- Bug segnalato dall'utente (app "inchiodata" al tap): la partenza aspettava un secondo onLayout della
  scheda che su altezze da telefono (copertina limitata in altezza) non arriva mai (onLayout non si
  ripete per un solo spostamento) → livello fermo a p=0 che assorbiva i tocchi. Fix: niente gate di
  stabilità; `ReaderIntroSheet` prop `remeasure` (rimisura titolo/griglia quando cambia `cardH`), mete
  "taggate" con la card corrente, commit lettore a 40% via setTimeout, `Easing.out(cubic)` 640ms,
  rete di sicurezza assoluta 900ms (commit + dismiss), `markReady` via effect nel lettore, `sheetHint`
  per la chiusura (stessa geometria dal primo fotogramma).
- Test `iteration_2/3` (390×844) e `iteration_4.json` (390×700, 375×667, 390×844, 430×932: partenza
  ≤ ~360ms, fine ≤ ~1.3s, handoff 0px, chiusura da intro e capitolo, nessun overlay bloccato).

- Home: rimosso badge inferiore "Hai già letto X storie" (componente eliminato); nuovo contatore compatto nell'header (`home-read-counter`, icona libri 3D + numero da `completed_story_ids`) → tap apre `/read-stories` (riepilogo esistente della sessione). Card storie Home INVARIATE (tentativo di riduzione annullato su richiesta utente).
- Tab Categorie: griglia a 4 colonne con tessere dense (prop `columns` di CategoryGrid/TopicPicker), tutto in una schermata senza scroll su 390x844. Onboarding non toccato (3 colonne).
- Onboarding: parte direttamente dagli argomenti (`START_STEP = 3` in app/onboarding.tsx), formati preselezionati entrambi; intro/profilo/formato saltati temporaneamente.
- Lettura: contenitori capitoli con un unico colore = accento del tema app (`colors.brand`), identico per tutte le storie e capitoli; rimosso `src/story-palette.ts` (tinte per categoria).
- Test: /app/test_reports/iteration_11.json, iteration_12.json (tutti PASS).


## Transizione card Home ↔ lettura: zero scatti a fine corsa — giugno 2026 (sessione corrente)
- Segnalazione utente (browser ed Expo Go): scatti/stutter verso la fine dell'apertura e in uscita.
- Diagnosi (misura fotogrammi in anteprima web): montaggio del lettore al 40% della corsa (+ suoi
  layout, `markReady`, `setOptions` a 600ms) → blocchi 50–120ms tra il 45% e il 90% del movimento;
  al ritorno offset di 1px (bordo card ignorato) e, tornando da un capitolo, la card "riprendi"
  restringe il mazzo → il livello rientrava nella cornice vecchia (salto ~90px all'ultimo frame).
- `story-morph.tsx`: commit lettore a `COMMIT_AT = 0.85` (residuo <0,5px) o a corsa finita, tramite ref
  (nessun ri-render a metà corsa; `dataReady` in ref); chiusura: `armHomeSettle` → `router.back` →
  `waitHomeSettled(240ms)` → rimisura card reale (`host.homeCard`) → `setFrom` → partenza + `homeReturn`
  (la Home rientra nello stesso istante). `CARD_BORDER = 1` in titolo/badge/cuffie.
- `morph-host.tsx`: ref `homeCard`, `homeReturn`; `armHomeSettle/homeSettled/waitHomeSettled`; fade 150ms.
- `discover.tsx`: registra la misura della card attiva (`HomeStoryDeck.registerActive`), segnala
  `homeSettled` dopo `getReadingProgress` (subito se la card "riprendi" non cambia, altrimenti dopo il
  nuovo `deckAreaH`); `making` al ritorno guidato da `homeReturn` (fallback 900ms).
- `deep-dive/[id].tsx`: `setOptions({animation:"fade"})` solo quando il livello è sparito;
  `markReady` con debounce 32ms su `cardH`. `intro-cta-button`/`reader-intro-sheet`: prop `flat`
  (niente BlurView nel livello: pesante e reso male dentro un genitore che si dissolve su iOS).
  `swipe-back.tsx`: reset x a 1200ms (mai prima che il livello sia a schermo).
- Misure dopo: 0 gap >28ms durante il movimento in 8 transizioni su 8 (apertura, chiusura da intro,
  chiusura da capitolo con card "riprendi"); atterraggio ≤0,3px.
- Follow-up utente: (1) ritorno = esatto inverso dell'apertura → in chiusura con swipe la presentazione
  prima torna al suo posto (`slideX` 220ms, ease-out) e il rientro nella card parte al 70% dello
  scorrimento (niente più traiettoria diagonale); (2) animazioni un po' più lente: `MORPH_DURATION`
  640→760ms, Home `making` 420→500ms, `FADE_IN_MS` 200→240ms. Verificato su web: 0 gap in movimento,
  atterraggio ≤0,3px.
- Bug utente: lo swipe dal bordo nel lettore spostava la schermata in orizzontale e spesso non tornava
  indietro (soglia 33% larghezza). `swipe-back.tsx` riscritto: nessuna traslazione (il lettore non si
  muove MAI in orizzontale, solo scroll verticale); il gesto dal bordo (48px) scatta appena il dito
  supera 56px verso l'interno (o al rilascio ≥32px / velocità >600) → `onRelease(0)` = morph inverso
  (offset 0, niente fase di scorrimento), altrimenti back normale. Fix collaterale: la rete di sicurezza
  `dismiss` 2500ms dell'apertura ora viene annullata allo smontaggio (colpiva il livello di ritorno se
  si tornava indietro entro ~3s dall'apertura).

## Lettura: redesign editoriale continuo + atmosfera a tema — giugno 2026 (sessione corrente)
- Richiesta utente: UI lettura rifatta (nessuna card per capitolo, scroll verticale continuo, grande
  copertina + titolo + 3 dati + introduzione + "Scorri per iniziare", capitoli con numero grande
  trasparente, header minimale "01 / 06", cornice luminosa a tema, sfondo atmosferico a tema);
  funzionalità/logica invariate; transizioni Home ↔ lettura mantenute.
- Nuovi: `reader-intro.tsx` (apertura; `introCoverSize()` = geometria copertina deterministica usata
  anche dal morph), `reader-atmosphere.tsx` (fondo a tema: base + 5 luci radiali = PNG
  `assets/images/reader-glow.png` tinto con `tintColor` — niente boxShadow: 30fps in morph —, traccia
  sfocata della copertina che si attenua con lo scroll, vignetta centrale; respiro 22s solo nativo,
  fermo con reduce-motion e sul web), `reader-frame.tsx` (cornice 1px `colors.brand`, alone interno cyan).
- `theme.ts`: `AccentSet.atmosphere {base, tint, secondary, glow}` per ogni accento (dark/light) →
  `colors.atmosBase/atmosTint/atmosSecondary/atmosGlow`.
- `reader-header.tsx` riscritto (indietro → morphBack o goBack, titolo compatto, "01 / 06", segmenti).
  `reader-section.tsx`: ChapterSection senza card, numero grande. `story-info-grid.tsx` prop `inline`.
  `reader-cover-backdrop.tsx`: dissolve e si scurisce uscendo. `reader-ending-backdrop.tsx`: `endTop`.
- `deep-dive/[id].tsx` riscritto: un solo ScrollView continuo, sezione corrente = linea di lettura al
  35% (tops misurati a layout, `pendingSection` per ripresa/start=1), fine = fondo pagina; salvataggio
  progresso/complete/limit/share/audio INVARIATI. `morphBack` `fadeIn={scrollY>8}`.
- `story-morph.tsx`: usa `ReaderIntro` + `ReaderAtmosphere` + `ReaderFrame`, geometria da
  `introCoverSize` (senza sheetHint). Eliminati `reader-intro-sheet.tsx`, `reader-page.tsx`.
- i18n: `deep_scroll_hint`.

---

## Ripristino ambiente da GitHub PAUSE-5.23 (giugno 2026 — sessione corrente)
- Richiesta utente: «estrapola la mia app e rendi la preview disponibile completa» — repo `github.com/micheleiannello7-cyber/PAUSE-5.23`.
- Repo clonato e copiato in `/app` preservando i file di piattaforma (`.git`, `.emergent`,
  `.env` di frontend/backend, `memory/test_credentials.md`). URL/porte nei `.env` NON modificati.
- **Backend**: FastAPI `:8001`, MongoDB locale, `pip install -r requirements.txt`
  (con `--extra-index-url` per `emergentintegrations`) completato. `backend/.env` esteso con
  `EMERGENT_LLM_KEY` (Universal Key), `ENFORCE_LIMIT="false"`, `TTS_ENABLED="false"`.
  Seed automatico all'avvio: **12 categorie, 430 storie**. `/api/health` = ok (db: true).
  Sync copertine verso Object Storage gestito ok (warning innocui su copertine di storie ritirate).
- **Frontend**: Expo SDK 57, `yarn install` completato. Metro `:3000`, preview attiva.
  Onboarding profilo (PAUSE, Google/Apple, "Continue as guest") renderizza a 390×844.
- **Scelta utente**: integrazioni a pagamento (ElevenLabs TTS, Stripe, OpenAI/Fal) lasciate
  DISATTIVATE per anteprima veloce (solo contenuti + copertine).

### Verifica redesign LETTURA (task lasciato in sospeso dall'agente precedente)
- L'agente precedente aveva implementato il redesign della schermata di lettura (deep-dive)
  ma NON aveva eseguito la verifica empirica dei 9 punti di accettazione (`Files modified: none`).
- Eseguito testing agent (Playwright, 390×844) → `test_reports/iteration_1.json`: **8.5/9 PASS**.
  T1 open transition, T2 header opacity in intro, T3 progressione 01..06/06, T4 ending in fondo,
  T5 back da intro, T7 immobilità orizzontale, T8 atmosphere/frame + no overflow, T9 zero errori
  console = PASS. T6 edge-swipe = PARZIALE (gesto nativo non simulabile su web; verificato
  equivalente: ResumeCard "riprendi da dove eri" compare in Home dopo scroll+back → resume ok).
- Nessun bug, nessuna modifica al codice richiesta. Da validare solo il gesto edge-swipe su
  device reale (Expo Go). testID reale apertura card Home: `home-story-<id>-open`.
- P2 cosmetico (facoltativo): migrare `textShadow*`→`textShadow` e `props.pointerEvents`→
  `style.pointerEvents` per silenziare warning RN Web (non bloccanti).


## Sfondo atmosferico lettura + copertina full-bleed (giugno 2026, fork)
Solo presentazione (nessuna modifica backend/contenuti):
- `theme.ts`: ogni accento ha `atmosphere { base, tint, secondary, glow, frame }` → `colors.atmosBase/atmosTint/atmosSecondary/atmosGlow/atmosFrame`. Un solo sistema generativo (PNG radiale tinto + gradienti), nuovi temi = solo colori.
- `reader-atmosphere.tsx`: fondo quasi nero + 6 luci morbide agli angoli/bordi nel colore del tema, centro protetto; respiro lentissimo (solo transform, fermo su web / riduci movimento).
- `reader-cover-backdrop.tsx`: copertina a tutta larghezza da top 0 che sfuma nell'atmosfera (`CoverNightSkin`), fascia di raccordo `CoverSeam`; con lo scroll parallasse 0.28, si scurisce e resta traccia (0.4). Condivisa con `story-morph`.
- `reader-intro.tsx`: `readerCoverFrame(winW, pageH)` → cornice + `reserve` (titolo entra nella dissolvenza).
- `reader-header.tsx`: titolo compatto visibile solo dal capitolo 1.
- `reader-section.tsx`: occhiello solo "CAPITOLO"; capitolo successivo mostra solo numero+titolo attenuati, paragrafo appare quando ci si arriva (`ChapterReveal`).
- `reader-frame.tsx`: cornice con `atmosFrame` + alone cyan interno.
- Test: iteration_2.json 8/8 PASS (apertura, header, reveal, 6 capitoli, morph Home→lettore, 5 accenti, tema chiaro).

## Anteprima temi, fix transizione, Argomenti compatti, tessere Home (giugno 2026, fork)
- Profilo → colore accento: `atmosphere-preview.tsx` (mini-lettore con base/tint/secondary/frame + brand del tema), 5 in una riga con nome.
- Fix morph Home→lettura: `story-morph.tsx` monta il lettore solo a fine animazione (rimosso COMMIT_AT); l'overlay mostra la schermata finale identica finché il lettore è pronto, poi dissolve.
- Argomenti/onboarding (`topic-picker.tsx`): titolo su una riga (font da larghezza misurata), nota "Nessuna scelta è definitiva" integrata nel riquadro hint; footer rimosso. i18n onb_title senza a capo.
- Home (`home-controls.tsx`): tessere categoria con vetro + `CategoryTileEdge active` come in Argomenti.
- Test: iteration_3.json 4/4 PASS.

## Autocentraggio capitoli + reveal fluido + hint a due righe (giugno 2026, fork)
- `deep-dive/[id].tsx`: `snapNear(y)` — a fine scorrimento (web debounce 170ms; nativo onEndDrag/onMomentumEnd) la pagina si allinea all'inizio della sezione più vicina entro min(200, 22% pagina). iteration_4 9/9 PASS.
- `reader-section.tsx`: corpo del capitolo successivo invisibile e 44pt più in basso; appare e sale verso il titolo mentre il capitolo si avvicina (dist 0.66h→0.24h). iteration_5 PASS.
- `topic-picker.tsx`: riquadro hint con due righe separate (pallino-icona ciascuna + divisore). iteration_5 PASS.

## Autocentraggio rapido + haptics mirati (giugno 2026, fork)
- `deep-dive/[id].tsx`: debounce web 90ms; raggio asimmetrico forward min(320, 36%h) / backward min(380, 44%h); `Haptics.impactAsync(Light)` solo nativo allo snap.
- `home-story-deck.tsx`: nessuna vibrazione allo swipe del mazzo; haptic Light solo al tocco che apre una storia.
- Test: iteration_6.json tutto PASS.

## Ripristino da repo GitHub + autocentraggio quasi immediato (giugno 2026, fork)
- Progetto ripristinato da https://github.com/micheleiannello7-cyber/PAUSE-5.24 ; seed DB: 12 categorie, 430 storie. TTS (ElevenLabs), Stripe, Fal.ai lasciati DISATTIVATI su richiesta utente.
- `deep-dive/[id].tsx`: sul web `scheduleSnap` stima la velocità dai campioni di scroll (px/ms): fermo/quasi fermo → snap dopo 16ms, in movimento → 55ms (prima debounce fisso 90ms). Nativo: `onEndDrag` (velocità <0.05) e `onMomentumEnd` → snap immediato.
- Stato: in attesa di verifica utente sulla reattività dell'autocentraggio.

## Lettura a capitoli (paging) + interruttore vibrazione (giugno 2026, fork)
- `deep-dive/[id].tsx`: scroll libero disattivato (`scrollEnabled={false}`). Pan verticale (RNGH) su un contenitore: a 28pt di spostamento (o al rilascio con spinta) `step(±1)` porta subito alla sezione successiva/precedente (apertura, capitoli, fine) allineata sotto la barra; sezioni più alte della schermata (+80pt) si leggono in due passi. Web: rotellina = un capitolo per colpo (lock 550ms). Rimossi snapNear/scheduleSnap.
- `src/haptics.ts`: wrapper di expo-haptics con flag globale persistito (`pause.haptics.v1`, AsyncStorage) + `useHapticsEnabled`. Tutti gli import `expo-haptics` in app/src ora puntano a `@/src/haptics`.
- Profilo → Impostazioni: riga "Vibrazione" (icona MDI `vibrate`, Switch `haptics-switch`), i18n it/en `haptics_row/haptics_hint`.

## Onboarding a schermo intero senza scroll (giugno 2026, fork)
- Profilo/accesso (`onboarding-profile.tsx`, `auth-block.tsx`): fattore di compattezza `k` (0…1) dall'altezza utile (altezza − insets; 640→860): logo, titolo, sottotitolo, spaziatori, padding schede, chip/select, pulsanti Google/Apple, CTA e puntini si stringono in modo continuo. Nulla rimosso. Lo ScrollView resta solo come rete di sicurezza (bounces off) per la tastiera.
- Argomenti (`onboarding.tsx`, `topic-picker.tsx` prop `fit`, `category-grid.tsx` prop `maxHeight`, `category-artwork.tsx` prop `bannerSize`): niente ScrollView; il picker è flex e la griglia misura l'altezza rimasta → la tessera "Qualsiasi" si abbassa (90→68) e le tessere ricevono un'altezza esplicita con oggetto 3D ridimensionato. Footer più compatto. Verificato senza scroll a 390×763 e 360×660.

## Anticipazione capitolo, transizione, cornice adattiva (giugno 2026, fork)
- `reader-section.tsx`: ogni capitolo = una schermata (`minHeight` = pageH − headerBottom); in fondo (`marginTop: auto`) l'anticipazione del capitolo seguente: divisore + numero + occhiello + titolo intero attenuati, MAI il testo (`reader-chapter-preview-N`). Rimosso il reveal animato (ChapterReveal) e il divisore tra sezioni.
- `deep-dive/[id].tsx`: con arrivo da transizione (`morph=1`) capitoli e fine si montano solo dopo la dissolvenza del livello (`chaptersReady`), per non rubare fotogrammi allo scambio.
- `story-morph.tsx`: il livello usa la propria altezza misurata (`layerH`, onLayout) invece di `useWindowDimensions` → geometria identica al lettore su Android; il rientro parte dopo `InteractionManager.runAfterInteractions` + 2 rAF.
- `src/screen-corners.ts` (`useScreenCornerRadius`, expo-device): raggio angoli schermo per modello (tabella iPhone modelId; famiglie Android Samsung/Pixel/…; fallback da insets); `reader-frame.tsx` usa quel raggio. Web = 28.

## Transizione: arrivo fluido di titolo e griglia (giugno 2026, fork)
- `story-morph.tsx`: MORPH_DURATION 680, MORPH_EASING `Easing.inOut(Easing.sin)` (niente coda quasi ferma); apertura: lettore montato a OPEN_COMMIT_AT 0.86 della corsa (solo se storia in cache) → scambio immediato a fine corsa; chiusura: `hostDismiss` (fade 150ms) avviato 150ms prima della fine → fusione con la card reale, `hostClear` a fine corsa come sicurezza.
- `deep-dive/[id].tsx`: anche ReaderEndingBackdrop e StoryShareCard (offscreen) montati solo con `chaptersReady`.

## Capitoli su più schermate senza duplicati (giugno 2026, fork)
- Bug: con testo più alto di una schermata il passo parziale mostrava l'anticipazione "05" seguita dal vero capitolo 05. Fix `reader-section.tsx`: il capitolo misura il proprio contenuto e occupa un numero intero di schermate, `sectionH = pages*minH − (pages−1)*pageOverlap` (overlap = headerBottom + 16 così nessuna riga resta sotto la barra); anticipazione sempre in fondo all'ultima schermata. `deep-dive`: passo parziale = viewH − pageOverlap, OVERFLOW_TOL 24; apertura→cap.1 e →apertura sempre salto pieno; se l'altezza dello ScrollView cambia (barra browser) si riallinea alla sezione corrente.

## 2026-09 — Categoria "ESPLORA" (ex "Qualsiasi argomento")
- Rinominata in ESPLORA / EXPLORE, sottotitolo "Ogni categoria è una scoperta" (i18n it/en, avviso onboarding).
- Icona 3D: script pronto `backend/generate_explore_icon.py` (Nano Banana, riferimento in `memory/icons_2026/explore-reference.png`).
  IN ATTESA: credito Universal Key esaurito. Quando ricaricato: `python generate_explore_icon.py generate` → revisione → `python generate_explore_icon.py publish`.

## 2026-09 — Fix lettore (capitoli)
- Un capitolo = una schermata; anticipazione compatta in fondo ("CAPITOLO 0X" + titolo, senza numero in filigrana).
- Modalità compatta automatica se il capitolo sfora di ≤120px; quote sezioni calcolate dalle altezze (web-safe); overflow-anchor:none sul web.

## 2026-09-29 — Produzione v9 (nuovi contenuti, copertina subito)
- `backend/v9_topics.py` rivisto dopo analisi dei 430 titoli: 63 nuovi argomenti (target 40/categoria).
- Run 1: 11 prodotti (cultura 33, economia 32, arte 32, geografia 32, corpo-umano 33) poi credito esaurito.
- Restano 52 (51 senza testo + "oro vs rame" con testo senza copertina). Riprendere: `cd /app/backend && nohup python produce_v9.py > ../memory/v9_production_2.stdout 2>&1 &`

## 2026-09-29 — Apertura lettore
- Titolo copertina −30% (24/22/20/18 px); griglia info in contenitore vetro con celle a misura (tipo/durata fisse, categoria elastica): mai sovrapposizioni.
- Copertina dinamica: `readerCoverFrame(winW, pageH, reserveCap)` con `ReaderIntro.onFit` (misura titolo+dati+intro+invito) → l'introduzione è sempre leggibile per intero nella prima schermata (min copertina 200px). Condiviso con story-morph.
- ESPLORA: accento bianco ghiaccio (#EAF7FF) quando selezionata.

## Card Home: titolo sopra, badge sotto + centraggio più morbido — giugno 2026 (sessione corrente)
- Richiesta utente: spostare la pillola dei 3 badge in fondo alla card (dove stava il titolo) invertendo
  l'ordine, così che la transizione card → lettura sia più fluida (elementi già quasi al loro posto);
  auto-centraggio del mazzo meno "veloce e secco".
- `home-story-card.tsx`: corpo in fondo alla card ora è una colonna — riga titolo (+ tasto cuffie) sopra,
  `StoryMetaChips` sotto (gap 10). Rimosso lo scrim superiore (non c'è più nulla in alto).
- `story-morph.tsx`: geometria di partenza aggiornata (`chipsFrom` sull'ultimo rigo della card,
  `titleFrom` = sopra i badge − `CHIP_GAP`, tasto cuffie allineato alla riga titolo); rimosso `topScrim`.
  Verificato su web: primo fotogramma del livello coincide con la card, arrivo identico al lettore.
- `home-story-deck.tsx`: `SNAP_SPRING` 190/22 → 100/24 (smorzamento ≈ critico, nessun rimbalzo, posa dolce).

## Lettura: anticipazione → intestazione capitolo senza doppioni — giugno 2026 (sessione corrente)
- Richiesta utente: il "CAPITOLO 0X + titolo" in fondo alla schermata non deve essere un doppione
  piccolo: deve ingrandirsi con una transizione morbida e diventare l'intestazione del capitolo seguente.
- `reader-section.tsx`: `ChapterHeading` (numero in filigrana, occhiello, titolo) è l'unico elemento; per i
  capitoli dall'indice 1 in su parte come anticipazione (scala 22/31, opacità 0.5, filo sopra, numero accanto
  all'occhiello) dentro lo spazio riservato in fondo alla sezione precedente (`TeaserSpace`, misura invisibile
  del titolo seguente, `LAND_PAD` 24 al posto del padding inferiore) e segue lo scroll: `p = interpolate(scrollY,
  [top − pageH + sm, top − headerBottom − sm])`, quote da `ChapterTrack` (scrollY, tops, pageH, headerBottom
  passate da `deep-dive/[id].tsx`). Titolo con `transformOrigin: "left top"`. Versione compatta: il titolo
  resta 31 pt (prima 28) così la misura dell'anticipazione coincide sempre.
- Verificato su web: stato anticipazione, fotogramma intermedio (ingrandimento + filigrana che compare), arrivo.

## 2026-09-30 — Produzione v9 completata
- Credito ricaricato: `produce_v9.py` run 3 → 51/52 ok + 1 rifatto con `--only` (copertina non restituita al primo
  tentativo). Catalogo: 493 storie, 0 senza copertina, 74 v9; tutte le categorie ≥ 40 (scienza 53).
- Resta in attesa (solo su richiesta): icona 3D "ESPLORA" (`generate_explore_icon.py generate` → revisione → `publish`).

## 2026-06 — Ripristino da repo GitHub (PAUSE-5.28)
- Repo `micheleiannello7-cyber/PAUSE-5.28` estratto e migrato in /app, preservando .git, .emergent e i file .env di piattaforma.
- Dipendenze backend (pip) e frontend (yarn) reinstallate; `EMERGENT_LLM_KEY` configurata in backend/.env per Object Storage + AI.
- Seed automatico all'avvio: 12 categorie, 493 storie. `/api/health` = ok (db: true).
- Preview verificata: onboarding, selezione categorie con artwork 3D da Object Storage, catalogo storie. App pronta.

## Update — Crediti a ricarica, limite argomenti, Cronologia (giu 2026)
- **Storie disponibili (token bucket)**: 5 base / 6 Premium, −1 quando il lettore resta >5 s sul capitolo 1 (storie nuove), +1 ogni 60 min per entrambi. Backend: `FREE_CAPACITY`, `PREMIUM_CAPACITY`, `RECHARGE_SECONDS`, campi `credits`/`credits_at` in `user_state`; `limit-check` restituisce `credits, capacity, next_credit_in, next_credit_at`. `ENFORCE_LIMIT="true"` in backend/.env. 0 crediti → `/pause-limit` con countdown mm:ss.
- **Limite argomenti**: base max 4 categorie specifiche (`FREE_TOPICS_LIMIT`, 402 `topics_limit`), ESPLORA sempre ok, Premium illimitato. Toast bloccante in onboarding e tab Argomenti (`topics-limit-toast`).
- **Indicatore crediti** `src/components/limit-badge.tsx` (libro 3D `kind-book.png`, numero, slot, 6° slot Premium dorato, timer) in Home (`home-credits`), Argomenti, Salvati. `home-read-counter.tsx` rimosso.
- **Premium screen**: righe "Storie disponibili 5→6 (+1 ogni 60 min)" e "Cronologia 10 giorni → Completa".
- **Cronologia** `app/history.tsx` (Profilo → "Le tue scoperte" → Cronologia): costruita su `completions` (rilettura loggata con `reread:true`, ignorata da stats). Base: ultimi 10 giorni + card Premium; Premium: tutto + ricerca titolo + filtri periodo/categoria. Endpoint `GET /api/user/{id}/history?q&category_id&since`.
- Test: `/app/test_reports/iteration_3.json` (backend 10/10, frontend OK).
- **Rilettura gratuita**: le storie già lette non consumano crediti (was_new); etichetta nel lettore sull'intro (`reader-reread-label`), pill "Rilettura gratuita" su ogni card della Cronologia, link "Rileggi le tue scoperte" nella schermata di pausa (`pause-limit-reread`); route `history` esclusa dal redirect del gate.
- **Avviso ricarica**: toast in Home (`credit-back-toast`) quando i crediti salgono rispetto all'ultimo valore visto (AsyncStorage `pause.credits_seen.<uid>`).
- Cronologia: header solo titolo (sottotitolo rimosso); ricerca Premium solo per titolo.
- **Regole crediti aggiornate**: base 4 crediti / +1 ogni 2 h; Premium 5 crediti / +1 ogni ora (`FREE_CAPACITY`, `PREMIUM_CAPACITY`, `FREE_RECHARGE_SECONDS`, `PREMIUM_RECHARGE_SECONDS`, `_recharge_for`). Calcolo su orario server (immune al cambio ora del dispositivo), continua con app chiusa, clamp automatico per dati esistenti. UI: ultimo slot Premium dorato, Premium screen con righe Storie 4→5, Ricarica 2h→1h, Argomenti 4→illimitati. Test pytest aggiornati (10/10).
