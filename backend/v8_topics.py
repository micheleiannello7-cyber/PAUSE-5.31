"""PAUSE v8 — argomenti curati a mano: 5 curiosità + 5 mini lezioni per ogni categoria.
Titoli scelti per non sovrapporsi al catalogo esistente. I testi (6 capitoli IT + EN)
vengono scritti da generate_v8.py e salvati in v8_content.json, poi caricati da seed_pack_v8.py."""

# category_id -> {"story": [(title_it, title_en), ...], "lesson": [(title_it, title_en), ...]}
TOPICS = {
    "scienza": {
        "story": [
            ("Perché l'acqua calda gela prima di quella fredda?", "Why does hot water freeze faster than cold water?"),
            ("Perché il vetro è trasparente se è fatto di sabbia?", "Why is glass transparent if it's made of sand?"),
            ("Perché il fuoco è caldo e di che cosa è fatta una fiamma?", "Why is fire hot, and what is a flame made of?"),
            ("Perché l'elio ti fa la voce da cartone animato?", "Why does helium give you a cartoon voice?"),
            ("Perché il pane lievita? La chimica delle bolle", "Why does bread rise? The chemistry of bubbles"),
        ],
        "lesson": [
            ("Leggere la tavola periodica: cosa dice una casella in 6 passi", "Reading the periodic table: what a square tells you in 6 steps"),
            ("Massa, peso e forza: le differenze che confondono tutti", "Mass, weight and force: the differences everyone mixes up"),
            ("Come funziona una leva: sollevare tanto con poco", "How a lever works: lifting a lot with a little"),
            ("Che cos'è la luce: onde, particelle e colori", "What light is: waves, particles and colours"),
            ("Correlazione non è causa: leggere uno studio scientifico", "Correlation isn't causation: how to read a scientific study"),
        ],
    },
    "spazio": {
        "story": [
            ("Perché nello spazio non c'è suono?", "Why is there no sound in space?"),
            ("Come si sceglie il nome di una stella o di un cratere?", "How do stars and craters get their names?"),
            ("Quanto pesa la Terra e come l'abbiamo misurata?", "How much does Earth weigh, and how did we measure it?"),
            ("Perché i razzi partono quasi sempre verso est?", "Why do rockets almost always launch toward the east?"),
            ("Che cosa è successo alle sonde Voyager, oltre il Sistema Solare", "What happened to the Voyager probes beyond the Solar System"),
        ],
        "lesson": [
            ("Leggere una foto del telescopio spaziale: colori veri e falsi", "Reading a space-telescope photo: true and false colours"),
            ("Come si trova un esopianeta in 6 passi", "How an exoplanet is discovered in 6 steps"),
            ("Le stagioni della Terra: inclinazione, non distanza", "Earth's seasons: tilt, not distance"),
            ("Come funziona un satellite meteo e cosa vede", "How a weather satellite works and what it sees"),
            ("Vedere la Stazione Spaziale passare: guida in 6 passi", "Spotting the Space Station overhead: a 6-step guide"),
        ],
    },
    "tecnologia": {
        "story": [
            ("Perché la barra di caricamento non dice mai la verità?", "Why does the progress bar never tell the truth?"),
            ("Come fa Shazam a riconoscere una canzone in tre secondi?", "How does Shazam recognise a song in three seconds?"),
            ("Perché le foto JPEG perdono qualità ogni volta che le salvi?", "Why do JPEG photos lose quality every time you save them?"),
            ("Come fa il telefono a sapere che l'hai girato?", "How does your phone know you've rotated it?"),
            ("Perché il caricatore rimane caldo anche quando non carica nulla?", "Why does a charger stay warm even when it's charging nothing?"),
        ],
        "lesson": [
            ("Che cos'è un file: bit, byte e formati spiegati bene", "What a file is: bits, bytes and formats explained"),
            ("Come funziona la crittografia end-to-end in 6 passi", "How end-to-end encryption works in 6 steps"),
            ("Cookie e tracciamento: chi ti segue online e come limitarlo", "Cookies and tracking: who follows you online and how to limit it"),
            ("Aggiornare o no? Capire le patch di sicurezza", "To update or not? Understanding security patches"),
            ("Riconoscere un deepfake: 6 controlli pratici", "Spotting a deepfake: 6 practical checks"),
        ],
    },
    "natura": {
        "story": [
            ("Perché il muschio cresce solo da un lato degli alberi (forse)?", "Why does moss grow on only one side of trees (maybe)?"),
            ("Come nasce un arcobaleno doppio?", "How does a double rainbow form?"),
            ("Perché alcune spiagge sono nere e altre bianche?", "Why are some beaches black and others white?"),
            ("Perché la sabbia del deserto canta?", "Why does desert sand sing?"),
            ("Come fanno i fiumi a disegnare le loro curve?", "How do rivers draw their curves?"),
        ],
        "lesson": [
            ("Riconoscere le rocce: sedimentarie, vulcaniche, metamorfiche", "Recognising rocks: sedimentary, volcanic, metamorphic"),
            ("Le maree: leggere una tabella prima di andare al mare", "Tides: reading a tide table before heading to the beach"),
            ("Coltivare un orto sul balcone in 6 passi", "Growing a balcony vegetable garden in 6 steps"),
            ("Come si forma una grotta: l'acqua che scolpisce la pietra", "How a cave forms: water carving stone"),
            ("Osservare gli insetti impollinatori: cosa cercare e quando", "Watching pollinators: what to look for and when"),
        ],
    },
    "animali": {
        "story": [
            ("Perché i cani inclinano la testa quando gli parli?", "Why do dogs tilt their heads when you talk to them?"),
            ("Come fanno le lucciole a produrre luce senza scaldarsi?", "How do fireflies make light without heat?"),
            ("Perché i fenicotteri sono rosa?", "Why are flamingos pink?"),
            ("I corvi si ricordano le facce delle persone", "Crows remember human faces"),
            ("Come fanno le balene a dormire senza affogare?", "How do whales sleep without drowning?"),
        ],
        "lesson": [
            ("Leggere il linguaggio del corpo di un gatto in 6 segnali", "Reading a cat's body language in 6 signals"),
            ("Come migrano gli animali: bussole, stelle e odori", "How animals migrate: compasses, stars and smells"),
            ("Predatori e prede: come funziona una caccia", "Predators and prey: how a hunt works"),
            ("Come si allevano i piccoli nel regno animale", "How animals raise their young"),
            ("Osservare gli animali in natura senza disturbarli", "Watching wildlife without disturbing it"),
        ],
    },
    "storia": {
        "story": [
            ("Perché guidiamo a destra (e gli inglesi a sinistra)?", "Why do we drive on the right (and the British on the left)?"),
            ("Chi ha inventato il fine settimana?", "Who invented the weekend?"),
            ("Come si sapeva che ora fosse prima degli orologi?", "How did people know the time before clocks?"),
            ("La Via della Seta non era una strada", "The Silk Road wasn't a road"),
            ("Perché il Colosseo ha i buchi nelle pareti?", "Why does the Colosseum have holes in its walls?"),
        ],
        "lesson": [
            ("Leggere un documento antico: 6 domande da farsi", "Reading an old document: 6 questions to ask"),
            ("Come nascono le rivoluzioni: gli ingredienti che si ripetono", "How revolutions start: the ingredients that repeat"),
            ("La Guerra Fredda in 6 passi: capire il mondo diviso", "The Cold War in 6 steps: understanding a divided world"),
            ("Come si scrive la storia: chi decide cosa ricordare", "How history gets written: who decides what we remember"),
            ("Visitare un sito archeologico e capire cosa vedi", "Visiting an archaeological site and understanding what you see"),
        ],
    },
    "psicologia": {
        "story": [
            ("Perché le canzoni ti restano in testa?", "Why do songs get stuck in your head?"),
            ("Perché ci vergogniamo per gli altri?", "Why do we feel embarrassed for other people?"),
            ("Perché il volto di uno sconosciuto ci sembra subito simpatico o no?", "Why does a stranger's face instantly seem likeable or not?"),
            ("Perché parliamo da soli (e fa bene)?", "Why do we talk to ourselves (and why it's good)?"),
            ("Il cervello odia perdere più di quanto ami vincere", "The brain hates losing more than it loves winning"),
        ],
        "lesson": [
            ("Dire di no senza sentirsi in colpa: il metodo in 6 passi", "Saying no without guilt: the 6-step method"),
            ("Come funziona l'attenzione e perché il multitasking non esiste", "How attention works and why multitasking doesn't exist"),
            ("Riconoscere il burnout prima che arrivi", "Recognising burnout before it hits"),
            ("Litigare bene: 6 regole per una discussione che risolve", "Arguing well: 6 rules for a discussion that resolves"),
            ("La gratitudine funziona davvero? Cosa dice la ricerca", "Does gratitude really work? What the research says"),
        ],
    },
    "corpo-umano": {
        "story": [
            ("Perché ci vengono i brividi quando abbiamo la febbre?", "Why do we shiver when we have a fever?"),
            ("Perché il cuore batte a sinistra (ma non del tutto)?", "Why does the heart beat on the left (but not entirely)?"),
            ("Perché ci vengono le lacrime quando ridiamo?", "Why do we cry when we laugh?"),
            ("Perché il caffè fa venire sonno a qualcuno?", "Why does coffee make some people sleepy?"),
            ("Perché i denti da latte cadono?", "Why do baby teeth fall out?"),
        ],
        "lesson": [
            ("Leggere le analisi del sangue: 6 valori da conoscere", "Reading a blood test: 6 values worth knowing"),
            ("Postura e respiro: 6 minuti per stare meglio alla scrivania", "Posture and breath: 6 minutes to feel better at your desk"),
            ("Come funzionano i vaccini, spiegato passo per passo", "How vaccines work, step by step"),
            ("Il sistema nervoso: come un pensiero muove una mano", "The nervous system: how a thought moves a hand"),
            ("Camminare bene: quanto, come e perché conta", "Walking well: how much, how and why it matters"),
        ],
    },
    "cultura": {
        "story": [
            ("Perché il caffè si beve al bar e il tè con cerimonia?", "Why is coffee drunk at the bar and tea with ceremony?"),
            ("Da dove viene l'usanza di soffiare le candeline?", "Where does blowing out birthday candles come from?"),
            ("Perché il venerdì si mangia pesce in tanti paesi?", "Why is fish eaten on Fridays in so many countries?"),
            ("Perché il bianco è il colore delle spose (solo da poco)?", "Why is white the bridal colour (only recently)?"),
            ("Chi ha deciso che la settimana ha sette giorni?", "Who decided the week has seven days?"),
        ],
        "lesson": [
            ("Come nasce un dialetto: capire le lingue d'Italia", "How a dialect is born: understanding the languages of Italy"),
            ("Capire il jazz: 6 cose da ascoltare", "Understanding jazz: 6 things to listen for"),
            ("Le religioni del mondo in 6 passi: cosa hanno in comune", "World religions in 6 steps: what they share"),
            ("Come si legge un fumetto: la grammatica delle vignette", "How to read a comic: the grammar of panels"),
            ("Le feste del calendario: perché cadono quando cadono", "Calendar holidays: why they fall when they do"),
        ],
    },
    "curiosita": {
        "story": [
            ("Perché il ghiaccio del freezer sa di frigorifero?", "Why does freezer ice taste like the fridge?"),
            ("Perché la carta igienica è quasi sempre bianca?", "Why is toilet paper almost always white?"),
            ("Perché il rumore del mare rilassa?", "Why is the sound of the sea relaxing?"),
            ("Perché il rubinetto gocciola sempre con lo stesso ritmo?", "Why does a tap always drip with the same rhythm?"),
            ("Perché i biscotti diventano molli e il pane duro?", "Why do biscuits go soft and bread goes hard?"),
        ],
        "lesson": [
            ("Probabilità nella vita reale: 6 casi in cui l'intuito sbaglia", "Probability in real life: 6 cases where intuition fails"),
            ("Perché l'aereo vola: la portanza spiegata bene", "Why planes fly: lift explained properly"),
            ("Il caso e la casualità: come si genera un numero a caso", "Chance and randomness: how a random number is made"),
            ("Come si misura il tempo: dal pendolo all'orologio atomico", "How time is measured: from the pendulum to the atomic clock"),
            ("Ottimizzare la fila al supermercato: la scienza delle code", "Choosing the fastest supermarket queue: the science of lines"),
        ],
    },
    "economia": {
        "story": [
            ("Perché il caffè al bar costa 1 euro e a Londra 4?", "Why does a coffee cost 1 euro in Italy and 4 in London?"),
            ("Perché i saldi iniziano tutti lo stesso giorno?", "Why do sales all start on the same day?"),
            ("Chi decide quanto vale un euro rispetto al dollaro?", "Who decides how much a euro is worth against a dollar?"),
            ("Perché esistono le monete da 1 centesimo se costano più di 1 centesimo?", "Why do 1-cent coins exist if they cost more than 1 cent to make?"),
            ("Perché i biglietti aerei cambiano prezzo ogni ora?", "Why do plane ticket prices change every hour?"),
        ],
        "lesson": [
            ("Leggere lo scontrino: IVA, sconti e trucchi in 6 passi", "Reading a receipt: VAT, discounts and tricks in 6 steps"),
            ("Abbonamenti e costi nascosti: fare i conti in 6 passi", "Subscriptions and hidden costs: doing the maths in 6 steps"),
            ("Come funziona la pensione: contributi, anni e assegno", "How pensions work: contributions, years and payout"),
            ("Il prezzo giusto: come si decide quanto far pagare", "The right price: how businesses decide what to charge"),
            ("Come funziona un'assicurazione e quando serve davvero", "How insurance works and when you really need it"),
        ],
    },
    "arte": {
        "story": [
            ("Perché le statue antiche hanno spesso il naso rotto?", "Why do ancient statues so often have broken noses?"),
            ("Perché i quadri antichi sono così scuri?", "Why are old paintings so dark?"),
            ("Chi ha inventato la cornice?", "Who invented the picture frame?"),
            ("Perché la Torre di Pisa non cade?", "Why doesn't the Tower of Pisa fall?"),
            ("Perché i cartoni animati hanno quattro dita?", "Why do cartoon characters have four fingers?"),
        ],
        "lesson": [
            ("Disegnare un volto: proporzioni in 6 passi", "Drawing a face: proportions in 6 steps"),
            ("Capire il design di un oggetto: 6 domande", "Understanding an object's design: 6 questions"),
            ("Il restauro: come si riporta in vita un'opera", "Restoration: how a work of art is brought back to life"),
            ("Leggere un logo: perché funziona (o no)", "Reading a logo: why it works (or doesn't)"),
            ("La luce in fotografia: 6 situazioni da riconoscere", "Light in photography: 6 situations to recognise"),
        ],
    },
    "geografia": {
        "story": [
            ("Perché esiste una linea che cambia data in mezzo al Pacifico?", "Why is there a date line in the middle of the Pacific?"),
            ("Perché alcune isole compaiono e scompaiono?", "Why do some islands appear and disappear?"),
            ("Perché il Polo Nord magnetico si sposta?", "Why does the magnetic North Pole move?"),
            ("Perché il Mar Morto si chiama così e si sta restringendo?", "Why is the Dead Sea called that, and why is it shrinking?"),
            ("Il paese che ha una capitale in tre città", "The country with a capital in three cities"),
        ],
        "lesson": [
            ("Leggere una previsione meteo in 6 passi", "Reading a weather forecast in 6 steps"),
            ("Il vulcano sotto casa: convivere con il rischio in Italia", "The volcano next door: living with risk in Italy"),
            ("Come nasce un fiume e dove finisce", "How a river begins and where it ends"),
            ("Le correnti oceaniche: il riscaldamento globale del mare", "Ocean currents: the sea's global heating system"),
            ("Viaggiare in treno in Europa: pianificare in 6 passi", "Travelling Europe by train: planning in 6 steps"),
        ],
    },
}


def all_topics():
    """Flat list in seed order: [(cat_id, kind, title_it, title_en), ...]."""
    out = []
    for cat_id, kinds in TOPICS.items():
        for kind in ("story", "lesson"):
            for title_it, title_en in kinds[kind]:
                out.append((cat_id, kind, title_it, title_en))
    return out
