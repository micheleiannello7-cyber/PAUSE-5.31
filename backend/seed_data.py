"""
PAUSE — Seed data.
14 stories across 10 categories. Each story has a strong hook, 5-7 chapters
of real substance (following spec: prima le basi → poi il concetto principale
→ poi l'approfondimento), a curated Unsplash image, and a summary.

Chapter icons cycle through Ionicons that match the semantic feel of a
chapter (foundation / expansion / detail / extras / memory).
"""

# Chapter icon presets used cyclically — different set per story feel
DEFAULT_CHAPTER_ICONS = [
    "flash",         # base
    "aperture",      # expansion
    "sunny",         # deep dive
    "image",         # visual
    "bulb",          # insight
    "planet",        # zoom out
    "sparkles",      # extra
]

GLOWS = ["#00E5FF", "#B200FF", "#FF6D00", "#FF006A", "#00E676"]

def _chapters(items):
    out = []
    for i, (title, body, icon) in enumerate(items):
        out.append({
            "number": i + 1,
            "title": title,
            "body": body,
            "icon": icon,
            "glow_color": GLOWS[i % len(GLOWS)],
        })
    return out


CATEGORIES = [
    {"id": "scienza",       "name": "Scienza",       "icon": "planet-outline",    "color": "#00DFFF", "emoji_key": "science"},
    {"id": "spazio",        "name": "Spazio",        "icon": "rocket-outline",    "color": "#A85AFF", "emoji_key": "space"},
    {"id": "tecnologia",    "name": "Tecnologia",    "icon": "hardware-chip-outline", "color": "#4F8CFF", "emoji_key": "tech"},
    {"id": "natura",        "name": "Natura",        "icon": "leaf-outline",      "color": "#00E878", "emoji_key": "nature"},
    {"id": "animali",       "name": "Animali",       "icon": "paw-outline",       "color": "#FF9A3C", "emoji_key": "animals"},
    {"id": "storia",        "name": "Storia",        "icon": "book-outline",      "color": "#E4B76A", "emoji_key": "history"},
    {"id": "psicologia",    "name": "Psicologia",    "icon": "sparkles-outline",  "color": "#FF5CB8", "emoji_key": "mind"},
    {"id": "corpo-umano",   "name": "Corpo umano",   "icon": "heart-outline",     "color": "#FF4D6D", "emoji_key": "body"},
    {"id": "cultura",       "name": "Cultura",       "icon": "globe-outline",     "color": "#00DAB4", "emoji_key": "culture"},
    {"id": "curiosita",     "name": "Curiosità",     "icon": "help-circle-outline", "color": "#A85AFF", "emoji_key": "curiosity"},
    {"id": "economia",      "name": "Economia & Denaro", "icon": "cash-outline",  "color": "#FFE14D", "emoji_key": "money"},
    {"id": "arte",          "name": "Arte & Design", "icon": "color-palette-outline", "color": "#E76BEF", "emoji_key": "art"},
    {"id": "geografia",     "name": "Geografia & Viaggi", "icon": "map-outline", "color": "#B8F03C", "emoji_key": "geo"},
]

CATEGORY_NAMES_EN = {
    "scienza": "Science", "spazio": "Space", "tecnologia": "Technology", "natura": "Nature",
    "animali": "Animals", "storia": "History", "psicologia": "Psychology", "corpo-umano": "Human Body",
    "cultura": "Culture", "curiosita": "Curiosities", "economia": "Money & Economics",
    "arte": "Art & Design", "geografia": "Geography & Travel",
}
for _c in CATEGORIES:
    _c["name_en"] = CATEGORY_NAMES_EN[_c["id"]]

STORIES = [
    # --------------------- SCIENZA / NATURA ---------------------
    {
        "id": "sky-blue-sunset-orange",
        "category_id": "scienza",
        "category_name": "Scienza · Natura",
        "category_icon": "planet-outline",
        "category_color": "#00D2FF",
        "title": "Perché il cielo è blu e il tramonto è arancione?",
        "highlight_words": ["cielo", "blu"],
        "hook": "Lo stesso cielo, colori diversi. Non è magia, ma una questione di luce, atmosfera e lunghezza delle onde luminose.",
        "hero_image": "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("La luce del Sole",
             "La luce che ci raggiunge dal Sole ci sembra bianca, ma in realtà è la somma di tutti i colori dell'arcobaleno: dal violetto al rosso. Ogni colore corrisponde a un'onda con una lunghezza precisa: le onde blu e violette sono corte e vibrano velocemente, quelle rosse e arancioni sono più lunghe e ampie. Quando questa luce entra nell'atmosfera, non arriva dritta ai nostri occhi: incontra un oceano di molecole di gas, polveri e microscopiche particelle che la deviano in tutte le direzioni.",
             "sunny"),
            ("Perché il cielo è blu",
             "Le onde più corte, cioè il blu e il violetto, urtano molto più spesso contro le molecole d'aria e vengono \"sparpagliate\" in ogni direzione. Questo fenomeno si chiama diffusione di Rayleigh. Il nostro occhio è più sensibile al blu che al violetto, quindi il cielo ci appare blu. È come se l'atmosfera prendesse la componente blu della luce solare e la spargesse sopra le nostre teste, mentre i colori più caldi (rosso e arancione) proseguono quasi indisturbati.",
             "cloud"),
            ("E il tramonto?",
             "Al tramonto il Sole è basso sull'orizzonte, quindi la sua luce deve attraversare uno strato di atmosfera molto più spesso rispetto a mezzogiorno. In questo lungo percorso, le onde corte (blu e verdi) vengono diffuse e assorbite fino a scomparire, mentre le onde più lunghe (rosso, arancione, giallo) sopravvivono al viaggio e riescono ad arrivare ai nostri occhi. È lo stesso motivo per cui l'alba, con angolazione simile, ha colori caldi e vellutati.",
             "sunny"),
            ("Non solo atmosfera",
             "Anche la presenza di polveri, inquinamento, vapore acqueo e umidità può rendere i colori del tramonto più intensi o particolari. Dopo un'eruzione vulcanica, per esempio, i tramonti possono diventare incredibilmente rossi per mesi: le microparticelle sospese nell'aria filtrano ancora di più la luce. Anche una giornata dopo un temporale regala tramonti più puliti e brillanti, perché l'aria è più libera da pulviscolo.",
             "leaf"),
            ("Un dettaglio sorprendente",
             "Lo stesso principio spiega perché il mare riflette il colore del cielo, perché Marte ha albe blu (l'atmosfera rarefatta e polverosa diffonde diversamente la luce), e perché le nebulose lontane appaiono con colori così vividi nelle foto astronomiche. In fondo, il cielo non è solo sopra di noi: è anche dentro di noi, ogni volta che ci ricordiamo quanto sia straordinaria la luce.",
             "bulb"),
            ("Un piccolo esperimento",
             "Puoi vedere Rayleigh a casa tua: riempi un bicchiere d'acqua, aggiungi una goccia di latte e illumina di lato con la torcia del telefono. L'acqua diventerà azzurrina di lato e leggermente arancione dall'altro. Le microgocce di grasso del latte imitano le molecole dell'atmosfera: diffondono di più il blu e lasciano passare il rosso. È esattamente quello che succede nel cielo, in scala molto più piccola.",
             "flask"),
        ]),
        "summary": "Il cielo è blu di giorno per la diffusione della luce, arancione al tramonto perché i raggi rossi viaggiano più lontano nell'atmosfera.",
    },
    {
        "id": "why-we-yawn",
        "category_id": "corpo-umano",
        "category_name": "Corpo umano",
        "category_icon": "heart-outline",
        "category_color": "#FF006A",
        "title": "Perché sbadigliamo (e perché è contagioso)?",
        "highlight_words": ["sbadigliamo", "contagioso"],
        "hook": "Non è solo sonno o noia: lo sbadiglio è uno dei riflessi più misteriosi del nostro corpo, e ci lega agli altri più di quanto pensi.",
        "hero_image": "https://images.unsplash.com/photo-1552057426-c4dbcae005b9?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Cos'è davvero uno sbadiglio",
             "Uno sbadiglio è un riflesso involontario: bocca spalancata, inspirazione lunga e profonda, breve stiramento dei muscoli facciali, poi un'espirazione più corta. Dura in media 6 secondi. Comincia già nel grembo materno intorno alla dodicesima settimana di gestazione, e continua per tutta la vita: quasi tutti i vertebrati sbadigliano, dai pesci ai serpenti fino ai mammiferi. È uno dei comportamenti più antichi che condividiamo con il resto del regno animale.",
             "moon"),
            ("Non serve per prendere ossigeno",
             "L'idea più diffusa è che sbadigliamo per far entrare più ossigeno nel sangue quando ne abbiamo poco. Studi degli anni '80 hanno smontato questa teoria: respirare aria ricca di ossigeno non riduce la frequenza degli sbadigli, e chi vive ad alta quota non sbadiglia più degli altri. Lo sbadiglio ha una funzione diversa, più sofisticata, che gli scienziati stanno ancora cercando di comprendere del tutto.",
             "leaf"),
            ("La teoria del raffreddamento",
             "Una delle ipotesi più solide oggi è che lo sbadiglio serva a raffreddare il cervello. Aprendo bene la bocca e inspirando aria fresca, il flusso sanguigno del viso viene raffreddato leggermente, e questo aiuterebbe il cervello a tornare a una temperatura ottimale. Si sbadiglia infatti di più quando la temperatura ambientale è vicina a quella corporea, e meno quando fa freddo. Un piccolo sistema di aria condizionata interno.",
             "snow"),
            ("Il collegamento con l'attenzione",
             "Sbadigliamo prima di dormire, ma anche appena svegli: è nei momenti di transizione dell'attenzione che il cervello ha più bisogno di \"resettarsi\". Studenti prima di un esame, atleti prima di una gara, piloti prima di un volo: sbadigliano tutti. Non è noia, è preparazione. È il modo del cervello di alzare il volume dell'allerta prima di uno sforzo importante.",
             "flash"),
            ("Perché è contagioso",
             "Vedere qualcuno sbadigliare (o anche solo leggerne la parola) attiva nel cervello i neuroni specchio, gli stessi coinvolti nell'empatia. Circa il 60% delle persone sbadiglia per imitazione. Curiosità: nei bambini sotto i 5 anni e nelle persone con difficoltà empatiche, l'effetto contagio è molto ridotto. In un certo senso, sbadigliare insieme è una piccolissima forma di connessione emotiva.",
             "people"),
            ("Anche gli animali si contagiano",
             "Il contagio dello sbadiglio è stato osservato in scimpanzé, cani, lupi, pappagalli e persino nei pesci in gruppo. I cani sono particolarmente sensibili: sbadigliano più spesso quando è il loro padrone a farlo che uno sconosciuto. È una prova indiretta di quanto il legame emotivo tra specie diverse sia reale e misurabile. La prossima volta che il tuo cane ti imita, sappi che è complimento evolutivo.",
             "paw"),
        ]),
        "summary": "Sbadigliamo per raffreddare il cervello e riattivare l'attenzione. Il contagio dipende dai neuroni specchio, legati all'empatia.",
    },
    # --------------------- SPAZIO ---------------------
    {
        "id": "black-holes-basics",
        "category_id": "spazio",
        "category_name": "Spazio",
        "category_icon": "rocket-outline",
        "category_color": "#B200FF",
        "title": "Cos'è davvero un buco nero?",
        "highlight_words": ["buco", "nero"],
        "hook": "Non sono buchi, non sono neri e non 'succhiano' tutto. Ma sono forse la cosa più affascinante e strana dell'universo.",
        "hero_image": "https://images.unsplash.com/photo-1543722530-d2c3201371e7?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Prima: cos'è la gravità",
             "Newton ci ha detto che due masse si attraggono. Einstein ha aggiunto un dettaglio rivoluzionario: la massa non attrae, deforma lo spazio-tempo attorno a sé, come una palla pesante su un tappeto elastico. Gli oggetti \"cadono\" verso una massa non perché siano tirati, ma perché scivolano lungo la curva. Più la massa è concentrata, più la curva è ripida. Un buco nero è la curva più estrema che possa esistere.",
             "planet"),
            ("Quando nasce un buco nero",
             "Le stelle massicce, molto più grandi del Sole, terminano la loro vita in un modo drammatico: quando finiscono il combustibile nucleare, il loro nucleo collassa sotto il proprio peso in pochissimi secondi. Se la massa residua supera una soglia critica (circa 3 volte la massa del Sole), nulla può fermare il collasso. La materia si comprime in uno spazio infinitamente piccolo, chiamato singolarità. È nato un buco nero.",
             "flame"),
            ("L'orizzonte degli eventi",
             "Attorno a un buco nero c'è un confine invisibile chiamato orizzonte degli eventi. È il punto oltre il quale la velocità necessaria per scappare supera quella della luce. E siccome nulla può viaggiare più veloce della luce, nulla può più tornare indietro. Non è una superficie fisica: è una zona di sola andata. Se ci cadessi dentro, dal tuo punto di vista non succederebbe nulla di strano fino a un certo punto, ma dall'esterno la tua immagine sembrerebbe rallentare fino a congelarsi.",
             "aperture"),
            ("Perché sono \"neri\"",
             "Un buco nero non emette luce perché la luce stessa non può uscire dal suo orizzonte. Ma non è nero come una parete: è una regione di spazio da cui nulla ci raggiunge. La prima \"foto\" di un buco nero, pubblicata nel 2019, non mostra il buco nero in sé, ma il disco di gas caldissimo che gli gira intorno a velocità enorme. Quell'anello arancione è ciò che sta per essere inghiottito.",
             "eye-off"),
            ("Il tempo si comporta in modo strano",
             "Vicino a un buco nero il tempo scorre più lentamente rispetto a chi è lontano. È un effetto della relatività chiamato dilatazione temporale. Se potessi orbitare vicino all'orizzonte degli eventi per un anno, sulla Terra potrebbero passarne migliaia. Non è fantascienza: è già stato misurato anche in miniatura, tra un satellite GPS e un orologio a terra, con una precisione altissima.",
             "hourglass"),
            ("Non risucchiano tutto",
             "Il mito più diffuso è che i buchi neri \"aspirino\" tutto ciò che passa vicino. Non è così: se il Sole diventasse un buco nero della stessa massa, la Terra continuerebbe a orbitare tranquillamente. Un buco nero agisce come qualsiasi altro corpo massiccio, solo con una zona di non ritorno molto vicina al centro. Al centro di quasi tutte le galassie, inclusa la nostra, c'è un buco nero super-massiccio: è una parte normale dell'universo.",
             "sparkles"),
        ]),
        "summary": "I buchi neri sono regioni con gravità così intensa che nemmeno la luce può fuggire, ma non 'aspirano' nulla che sia già in orbita stabile.",
    },
    {
        "id": "mars-red",
        "category_id": "spazio",
        "category_name": "Spazio",
        "category_icon": "rocket-outline",
        "category_color": "#B200FF",
        "title": "Perché Marte è rosso?",
        "highlight_words": ["Marte", "rosso"],
        "hook": "Il pianeta che ci osserva da sempre deve il suo colore a un dettaglio che conosciamo bene anche sulla Terra: la ruggine.",
        "hero_image": "https://images.unsplash.com/photo-1614732414444-096e5f1122d5?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Un pianeta diverso da tutti",
             "Marte è il quarto pianeta del sistema solare, più piccolo della Terra ma con un giorno quasi identico (24 ore e 37 minuti). La sua atmosfera è sottilissima, meno dell'1% di quella terrestre, ed è composta soprattutto da anidride carbonica. Non ha oceani, né vegetazione, né vita conosciuta: solo deserti, canyon e vulcani spenti. Eppure, guardato dalla Terra, brilla di un rosso caldo inconfondibile.",
             "planet"),
            ("Il colore che si vede a occhio nudo",
             "Il colore rossastro di Marte è visibile anche a occhio nudo, ed è per questo che le civiltà antiche gli davano nomi legati alla guerra e al sangue: per i Romani era Mars, dio della guerra. Ma quel rosso non è drammatico né violento. È un'ossidazione lenta, la stessa che fa arrugginire una vecchia bicicletta lasciata sotto la pioggia, distribuita su tutta la superficie del pianeta.",
             "eye"),
            ("Ferro ovunque",
             "La superficie marziana è ricca di ferro. Nel corso di miliardi di anni, questo ferro ha reagito con piccole quantità di ossigeno presenti nell'aria e nei minerali, trasformandosi in ossidi di ferro: la ruggine. Ogni granello di polvere marziana è ricoperto da uno strato microscopico di ossido di ferro, e ne basta pochissimo per dare a tutto il pianeta la sua tinta caratteristica. È letteralmente un pianeta arrugginito.",
             "hammer"),
            ("Il vento sposta il colore",
             "Marte ha tempeste di polvere gigantesche, alcune capaci di ricoprire l'intero pianeta per settimane. Il vento marziano solleva la polvere rossa e la ridistribuisce continuamente, coprendo rocce di altri colori. Sotto quello strato di ruggine, il vero terreno marziano contiene rocce basaltiche scure, argille verdastre e minerali chiari. Sarebbe un mondo molto più vario, se non fosse costantemente re-verniciato dalla polvere.",
             "cloud"),
            ("Un rosso che cambia",
             "Il colore di Marte non è uniforme. Alcune regioni, come Syrtis Major, appaiono più scure e grigio-verdi perché i loro venti spazzano via la polvere. Altre, come Tharsis, sono chiaramente arancioni per l'accumulo. I rover come Curiosity e Perseverance hanno mostrato tramonti marziani sorprendenti: sono blu, non arancioni. La polvere fine assorbe il rosso e lascia passare il blu, esattamente al contrario di quello che succede sulla Terra.",
             "aperture"),
            ("Perché ci interessa così tanto",
             "Il rosso di Marte è anche il motivo per cui il pianeta ci affascina. Studiare quella ruggine significa capire un passato in cui Marte, miliardi di anni fa, probabilmente aveva acqua liquida in superficie e forse le condizioni per una vita semplice. Quel colore è una cartolina antica: ci racconta un pianeta che è cambiato molto, e potrebbe insegnare qualcosa anche sul futuro del nostro.",
             "sparkles"),
        ]),
        "summary": "Marte è rosso perché la sua superficie è coperta da polvere di ossido di ferro: letteralmente, è un pianeta arrugginito.",
    },
    # --------------------- TECNOLOGIA ---------------------
    {
        "id": "how-oled-works",
        "category_id": "tecnologia",
        "category_name": "Tecnologia",
        "category_icon": "hardware-chip-outline",
        "category_color": "#00E676",
        "title": "Come funziona uno schermo OLED?",
        "highlight_words": ["schermo", "OLED"],
        "hook": "Perché i neri di un OLED sembrano davvero neri, e perché i colori bruciano di più? Tutto parte da come nasce la luce nel display.",
        "hero_image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Cos'è uno schermo",
             "Uno schermo è una griglia di puntini colorati chiamati pixel. Ogni pixel è capace di mostrare un colore diverso, cambiando molto velocemente. Se ne allinei milioni uno accanto all'altro, dalla giusta distanza il tuo cervello smette di vedere i singoli puntini e li interpreta come un'immagine continua. Le due grandi famiglie di schermi moderni si dividono per un dettaglio semplice ma fondamentale: chi produce la luce.",
             "phone-portrait"),
            ("Come funziona un LCD",
             "Negli schermi LCD (Liquid Crystal Display), la luce non viene creata dai pixel. Dietro lo schermo c'è una lampada bianca (di solito a LED) sempre accesa. Ogni pixel è come una piccola \"veneziana\" molecolare che fa passare più o meno luce, e davanti c'è un filtro colorato (rosso, verde o blu). Il problema è che quella lampada è sempre accesa: anche quando lo schermo mostra il nero, in realtà sta cercando di bloccare tutta la luce, ma un po' filtra sempre. Per questo il \"nero\" LCD è sempre un grigio scuro.",
             "flashlight"),
            ("La rivoluzione OLED",
             "Un pixel OLED (Organic Light Emitting Diode) è invece un piccolissimo LED che produce direttamente la luce del colore che deve mostrare. Non serve una lampada dietro: ogni pixel è un mini-sole autoilluminante. Se un pixel deve mostrare il nero, semplicemente si spegne. Zero luce emessa. Il risultato è un nero assoluto, mai grigio, e contrasti che l'LCD non può replicare.",
             "bulb"),
            ("Perché i colori sono più vividi",
             "Poiché ogni pixel OLED accende la propria luce solo quando serve, i colori accanto al nero risaltano di più. Un tramonto arancione su uno sfondo scuro sembra bruciare. È lo stesso motivo per cui i film in HDR fatti per OLED sono così potenti: le zone luminose e quelle scure convivono nella stessa scena senza compromessi. Ogni pixel è indipendente, quindi lo schermo non è più costretto a scegliere \"o luminoso o scuro\", può fare entrambi contemporaneamente.",
             "color-palette"),
            ("Gli svantaggi",
             "Non tutto è perfetto. I pixel OLED sono organici e col tempo si consumano, soprattutto quelli blu, che invecchiano più in fretta. Se una parte dello schermo mostra sempre la stessa immagine (una barra di navigazione, un logo), può rimanere leggermente più scura: è il famoso \"burn-in\". I produttori usano trucchi software (spostare i pixel, cambiare luminosità dei pixel usati troppo) per prevenirlo, ma è un limite fisico reale della tecnologia.",
             "warning"),
            ("Cosa arriva dopo",
             "Le nuove generazioni si chiamano QD-OLED e MicroLED. Il QD-OLED aggiunge \"quantum dots\" davanti ai pixel OLED per rendere i colori ancora più puri. Il MicroLED sostituisce i pixel organici con LED inorganici microscopici: stessi vantaggi dell'OLED, ma senza il rischio di burn-in e con luminosità enormi. È probabilmente il futuro degli schermi, ma è ancora costosissimo. Nel frattempo, l'OLED resta lo stato dell'arte per smartphone, TV di fascia alta e monitor da lavoro colorimetrico.",
             "sparkles"),
        ]),
        "summary": "Gli OLED producono luce pixel per pixel, quindi il nero è vero nero e i colori risaltano di più. Gli LCD invece hanno una lampada sempre accesa dietro.",
    },
    {
        "id": "how-wifi-works",
        "category_id": "tecnologia",
        "category_name": "Tecnologia",
        "category_icon": "hardware-chip-outline",
        "category_color": "#00E676",
        "title": "Come fa il Wi-Fi ad attraversare i muri?",
        "highlight_words": ["Wi-Fi", "muri"],
        "hook": "Non è magia, non è invisibile. Il Wi-Fi è luce che semplicemente non riesci a vedere, e sfida i muri di casa tua ogni giorno.",
        "hero_image": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Cos'è un'onda elettromagnetica",
             "Ogni volta che spingi un elettrone avanti e indietro molto velocemente, crei un'increspatura invisibile nel campo elettromagnetico che si propaga nello spazio: un'onda. La luce del Sole, quella di una lampadina, i raggi X, i raggi gamma sono tutti onde elettromagnetiche. Cambiano solo per la loro frequenza. Il Wi-Fi non è diverso: è una forma di luce, solo che il nostro occhio non riesce a vederla.",
             "radio"),
            ("La differenza è solo la frequenza",
             "La luce visibile ha frequenze altissime, centinaia di terahertz. Il Wi-Fi lavora a frequenze molto più basse, tipicamente 2,4 o 5 GHz (miliardi di oscillazioni al secondo). Frequenze più basse significano onde più lunghe, e onde più lunghe passano più facilmente attraverso i muri, il vetro, il legno. Ecco perché la luce di una lampada si ferma davanti a una parete, ma il Wi-Fi la attraversa senza problemi.",
             "pulse"),
            ("Il router come traduttore",
             "Il router è una piccola stazione radio. Prende i dati che gli arrivano via cavo (il tuo browser che chiede Instagram, per esempio) e li trasforma in un'onda modulata: un pattern preciso di variazioni di intensità che codifica i bit 0 e 1. Il tuo telefono ha una piccolissima antenna che sente quelle onde, decodifica il pattern e ricostruisce i dati. È esattamente come quando una radio trasforma le onde elettromagnetiche in musica.",
             "wifi"),
            ("Perché a volte è lento",
             "Le pareti in cemento armato, l'acqua, i corpi umani assorbono energia dalle onde Wi-Fi. Anche altri dispositivi (microonde, Bluetooth, telefoni cordless) usano la stessa banda 2,4 GHz e creano interferenza. Più segnali si sovrappongono, più il router deve rispedire i pacchetti che si perdono. Il risultato è una connessione più lenta, non perché il router \"non ce la fa\", ma perché sta letteralmente urlando in una stanza rumorosa.",
             "volume-high"),
            ("2,4 GHz vs 5 GHz",
             "La banda a 2,4 GHz ha onde più lunghe, attraversa meglio i muri, arriva più lontano, ma è satura e più lenta. La banda a 5 GHz ha onde più corte, non passa altrettanto bene tra le pareti, ma è veloce e meno affollata. Molti router moderni offrono entrambe: il tuo dispositivo sceglie automaticamente quella migliore in base a distanza e velocità. È il compromesso classico tra portata e velocità.",
             "options"),
            ("Il futuro: Wi-Fi 7 e oltre",
             "Il Wi-Fi 7 aggiunge una nuova banda a 6 GHz, ancora meno satura, con velocità potenziali oltre i 40 Gbps. Nel frattempo si stanno sperimentando comunicazioni Li-Fi: connessioni via luce visibile, letteralmente lampeggiando una lampadina LED così velocemente che il tuo occhio non se ne accorge ma un ricevitore sì. In un futuro non troppo lontano, il tuo router potrebbe essere una lampadina del soffitto.",
             "sparkles"),
        ]),
        "summary": "Il Wi-Fi è un'onda elettromagnetica come la luce, ma a frequenza più bassa: per questo attraversa i muri e trasporta dati.",
    },
    # --------------------- NATURA / ANIMALI ---------------------
    {
        "id": "bees-communicate",
        "category_id": "animali",
        "category_name": "Animali",
        "category_icon": "paw-outline",
        "category_color": "#FF9100",
        "title": "Come fanno le api a parlarsi?",
        "highlight_words": ["api", "parlarsi"],
        "hook": "Nell'alveare non c'è confusione: c'è un vero linguaggio, fatto di danze, vibrazioni e profumi. E funziona meglio del nostro GPS.",
        "hero_image": "https://images.unsplash.com/photo-1550439062-609e1531270e?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Un alveare non è caos",
             "Un alveare può contenere fino a 60.000 api, tutte impegnate in compiti diversi: bottinatrici che cercano nettare, nutrici che accudiscono le larve, guardiane che difendono l'ingresso, operaie che ventilano. Nonostante i numeri, non ci sono scontri: ogni ape sa cosa fare e dove andare. Il segreto è una comunicazione continua, precisa, che gli scienziati studiano da oltre un secolo e non hanno ancora finito di decifrare.",
             "layers"),
            ("La danza dell'ape",
             "Quando una bottinatrice trova un buon campo di fiori, torna all'alveare e comincia a \"danzare\" sui favi. Non è metaforico: è una vera coreografia. Se il cibo è vicino (meno di 100 metri), fa una danza circolare. Se è lontano, esegue la famosa \"danza dell'addome\", scoperta da Karl von Frisch (Nobel nel 1973): cammina in linea retta scodinzolando, poi torna indietro a semicerchio, e ripete.",
             "musical-notes"),
            ("Come trasmette le coordinate",
             "L'angolo della linea retta rispetto alla verticale del favo indica la direzione rispetto al Sole. La durata dello scodinzolìo indica la distanza: circa un secondo per ogni chilometro. È letteralmente una mappa danzata. Le altre api toccano l'ape danzatrice con le antenne per sentire le vibrazioni, e poi partono con precisione millimetrica verso il fiore giusto. Il tutto senza una parola, senza un occhio, solo con il corpo.",
             "compass"),
            ("Non solo movimento",
             "La comunicazione dell'ape usa anche i feromoni: profumi chimici prodotti da ghiandole specifiche. La regina emette un feromone che tiene l'alveare unito e informa tutte del suo stato di salute. Le guardiane rilasciano un allarme chimico quando qualcuno minaccia l'ingresso, e in pochi secondi centinaia di api arrivano a difendere. Ogni odore ha un significato preciso, come parole in un vocabolario invisibile.",
             "cloud"),
            ("Il ronzio conta",
             "Anche il suono conta. Le api producono ronzii diversi a seconda del contesto: un ronzio d'allarme, uno di corteggiamento, uno che significa \"sciamiamo\" quando una parte dell'alveare deve lasciarlo. La regina fa un ronzio caratteristico chiamato \"tooting\": un mini-canto che serve a mostrare autorità sulle rivali. In un alveare c'è musica, e ogni nota ha un significato biologico preciso.",
             "musical-note"),
            ("Perché ci riguarda",
             "Capire la comunicazione delle api non è una curiosità: è vitale. Le api impollinano circa il 75% delle coltivazioni alimentari umane. Quando i pesticidi disturbano la loro capacità di orientarsi o di danzare, l'intero sistema alimentare traballa. Studiare il loro linguaggio significa anche capire come proteggerle. E, in cambio, ci insegnano che una comunità di 60.000 individui può funzionare in armonia usando ballo, profumo e vibrazione, senza mai un litigio inutile.",
             "sparkles"),
        ]),
        "summary": "Le api comunicano con una danza che indica direzione e distanza, con feromoni e vibrazioni. È uno dei linguaggi più raffinati del regno animale.",
    },
    {
        "id": "octopus-brains",
        "category_id": "animali",
        "category_name": "Animali",
        "category_icon": "paw-outline",
        "category_color": "#FF9100",
        "title": "Il polpo ha davvero otto cervelli?",
        "highlight_words": ["polpo", "cervelli"],
        "hook": "Non è una leggenda del web: il polpo ha un modo di 'pensare' che assomiglia più a un collettivo che a un individuo.",
        "hero_image": "https://images.unsplash.com/photo-1580019542155-247062e19ce4?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Un animale alieno",
             "I polpi appartengono ai cefalopodi, un gruppo che si è separato dal nostro ramo evolutivo circa 600 milioni di anni fa. Sono così diversi da noi che studiarli è quasi come studiare una forma di intelligenza aliena. Vivono in ambienti ostili, cambiano colore in un istante, aprono barattoli, risolvono labirinti. E hanno un sistema nervoso costruito in un modo radicalmente diverso dal nostro.",
             "eye"),
            ("Un cervello centrale piccolo",
             "Il polpo ha un cervello centrale a forma di ciambella (letteralmente: attraversato dall'esofago) che contiene circa 100 milioni di neuroni. Meno di un cane, poco più di un topo. Se guardassimo solo quello, non sembrerebbe un fuoriclasse dell'intelligenza. Ma qui arriva il colpo di scena: il resto del suo sistema nervoso non è al centro, è sparso ovunque.",
             "flash"),
            ("La maggior parte dei neuroni è nelle braccia",
             "Sui suoi otto tentacoli il polpo ha circa 300 milioni di neuroni distribuiti, cioè due terzi del totale. Ogni braccio è una specie di piccolo \"mini-cervello\" con la sua rete neurale locale. Le braccia possono muoversi, esplorare, afferrare e persino risolvere problemi semplici senza aspettare l'ok del cervello centrale. È come se ognuno dei suoi arti avesse un pilota semi-autonomo.",
             "hand-left"),
            ("Ecco perché 'otto cervelli'",
             "L'espressione popolare nasce da qui: il polpo ha un cervello centrale + otto \"cervelli\" nervosi periferici. Non sono cervelli veri e propri, ma reti locali capaci di prendere decisioni. In esperimenti, un braccio staccato può ancora reagire agli stimoli e afferrare oggetti per parecchi minuti. La coordinazione tra centro e periferia è simile a un'orchestra jazz: il direttore dà il tono, ma ogni musicista improvvisa.",
             "layers"),
            ("Un colore che sente il mondo",
             "I polpi cambiano colore in meno di un secondo, mimetizzandosi perfettamente. Il paradosso? Studi recenti mostrano che sono probabilmente daltonici. Come fanno? Sembra che la loro pelle abbia recettori simili a quelli degli occhi: la pelle stessa \"vede\" i colori attorno e li imita, senza bisogno di passare dal cervello. È letteralmente una forma di visione distribuita, sparsa su tutta la superficie del corpo.",
             "color-palette"),
            ("Cosa ci insegna",
             "Il polpo è la prova che l'intelligenza può nascere in forme che noi facciamo fatica a immaginare. Non serve un unico cervello enorme: si può pensare distribuiti, in parallelo, con una parte del corpo che si occupa di sé stessa mentre un'altra fa altro. È un modello che stiamo studiando anche per progettare robot e intelligenze artificiali di nuova generazione: non un centro che decide tutto, ma tanti nodi che collaborano.",
             "sparkles"),
        ]),
        "summary": "Il polpo ha un cervello centrale piccolo ma due terzi dei neuroni sono nelle braccia: pensa in modo distribuito.",
    },
    # --------------------- STORIA ---------------------
    {
        "id": "why-romans-fell",
        "category_id": "storia",
        "category_name": "Storia",
        "category_icon": "book-outline",
        "category_color": "#FF6D00",
        "title": "Perché è crollato l'Impero Romano?",
        "highlight_words": ["Impero", "Romano"],
        "hook": "Non è caduto in un giorno. Non è caduto per un motivo solo. E in un certo senso, non è mai davvero finito.",
        "hero_image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Un impero enorme",
             "Nel suo momento migliore, intorno al 117 d.C., l'Impero Romano si estendeva dalla Britannia all'attuale Iraq, dalla Germania all'Egitto: circa 5 milioni di km² e 60-70 milioni di abitanti, un quinto della popolazione mondiale dell'epoca. Aveva strade lunghe migliaia di chilometri, acquedotti, terme pubbliche, una moneta comune. Sembrava eterno. E per secoli lo è stato.",
             "planet"),
            ("Il primo problema: la successione",
             "A partire dal III secolo, l'Impero entrò in una crisi drammatica. In 50 anni si susseguirono decine di imperatori, molti uccisi dai propri soldati. Ogni cambio di potere era una piccola guerra civile, e ogni piccola guerra civile indeboliva le difese ai confini. L'Impero smise di essere una macchina prevedibile e diventò un continuo cantiere di violenza politica.",
             "swap-horizontal"),
            ("L'economia si spezza",
             "Le monete d'argento vennero \"tosate\": ogni imperatore ne riduceva la quantità di metallo prezioso per pagare truppe e favori. Il risultato fu una delle prime grandi inflazioni della storia. I prezzi esplosero, il commercio si ridusse, le persone tornarono al baratto. Diocleziano provò a fissare i prezzi per legge, ma non funzionò. Un impero che non riesce più a farsi accettare la propria moneta è un impero fragile.",
             "trending-down"),
            ("Le migrazioni ai confini",
             "Nel IV e V secolo, popoli spinti dalle invasioni degli Unni (dall'Asia centrale) premevano sui confini del Reno e del Danubio: Goti, Vandali, Franchi, Sassoni. Alcuni chiesero di entrare pacificamente, altri fecero pressione con le armi. L'Impero, che un tempo li avrebbe assorbiti nel proprio esercito, non aveva più le risorse per farlo bene. Nel 410 Roma stessa venne saccheggiata da Alarico: un colpo psicologico enorme.",
             "arrow-forward"),
            ("Un cristianesimo che cambia tutto",
             "Nel 313 Costantino legalizzò il cristianesimo, e nel 380 divenne religione di stato. In pochi decenni, un impero fondato sulle divinità civiche cambiò identità profonda. Non fu una \"causa\" del crollo, come pensava Gibbon, ma cambiò completamente cosa significasse \"essere romani\". Sant'Agostino, nel 410, scrisse La città di Dio proprio per rispondere alla domanda: se Roma cade, che significa? La risposta segnò il pensiero occidentale.",
             "star"),
            ("Non è caduta davvero",
             "La data ufficiale della fine è il 476 d.C., quando l'ultimo imperatore d'Occidente, Romolo Augusto, fu deposto. Ma l'Impero d'Oriente (Bisanzio) continuò per altri mille anni, fino al 1453. Il diritto romano, il latino, l'architettura, la Chiesa cattolica sono eredità che ancora oggi camminano con noi. In un certo senso, l'Impero non è crollato: si è dissolto lentamente nell'Europa moderna, come uno zucchero in un caffè.",
             "sparkles"),
        ]),
        "summary": "L'Impero Romano d'Occidente crollò per un mix di crisi politica, economica, migratoria e culturale. Ma le sue radici sopravvivono in tutta l'Europa moderna.",
    },
    # --------------------- PSICOLOGIA ---------------------
    {
        "id": "brain-doesnt-see",
        "category_id": "psicologia",
        "category_name": "Psicologia",
        "category_icon": "sparkles-outline",
        "category_color": "#FF006A",
        "title": "Perché il tuo cervello non vede davvero il mondo",
        "highlight_words": ["cervello", "vede"],
        "hook": "Ciò che chiami 'vedere' è in realtà una previsione, un montaggio, una storia che il tuo cervello ti racconta in tempo reale.",
        "hero_image": "https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("La luce entra nell'occhio",
             "Quando guardi qualcosa, la luce riflessa dall'oggetto entra dalla pupilla, viene messa a fuoco dal cristallino e proiettata capovolta sulla retina, in fondo al bulbo oculare. Lì miliardi di cellule fotorecettrici (coni e bastoncelli) trasformano la luce in impulsi elettrici. Ma quello che arriva al cervello non è un'immagine: è un flusso di segnali confusi, incompleti, parziali. Da lì comincia il vero lavoro.",
             "eye"),
            ("Il punto cieco",
             "Nel fondo di ogni occhio c'è un buco. Letteralmente: il punto in cui il nervo ottico esce dalla retina non ha fotorecettori. Se il cervello si limitasse a mostrarti quello che gli arriva, vedresti un buco nero al centro del tuo campo visivo. Invece non lo vedi mai. Il cervello riempie quella zona con quello che pensa dovrebbe esserci in base al contesto. È il tuo primo, quotidiano, deep fake interno.",
             "eye-off"),
            ("Vediamo previsioni, non fotografie",
             "Il cervello non aspetta i segnali per costruire una scena: continua a fare previsioni su cosa sta per vedere e le confronta con l'input reale. Se le previsioni sono buone, ti sembra tutto stabile. Se sbagliano, ti sorprendi. Questo modello, chiamato \"predictive processing\", spiega perché guidare in una strada conosciuta è così automatico: gran parte di quello che \"vedi\" è in realtà memoria, non nuovi dati.",
             "aperture"),
            ("Il colore non esiste là fuori",
             "Il colore non è una proprietà degli oggetti: è un'interpretazione del cervello. Le mele non sono \"rosse\", riflettono onde luminose che il tuo cervello traduce in rosso. Un daltonico non è cieco al rosso: il suo cervello lo interpreta diversamente. E anche tra persone \"normali\" ci sono differenze: il famoso vestito bianco-e-oro / blu-e-nero del 2015 non era una malattia: era una prova che ogni cervello costruisce il colore secondo i propri criteri.",
             "color-palette"),
            ("Il cervello taglia il film",
             "I tuoi occhi non si muovono in modo fluido: fanno saltini rapidi chiamati \"saccadi\". Durante ognuno di quei saltini, l'immagine è troppo veloce per essere elaborata, quindi il cervello letteralmente cancella quel breve tratto e ti mostra solo i \"fotogrammi\" utili. È il motivo per cui allo specchio non riesci mai a vederti battere le palpebre da solo: quei brevissimi momenti vengono nascosti al tuo montaggio interno.",
             "film"),
            ("Le illusioni sono normali",
             "Ogni volta che vedi un'illusione ottica, non è un errore del tuo cervello: è la prova che sta funzionando bene. Le illusioni sfruttano le scorciatoie che il cervello usa continuamente per costruire il mondo in fretta. Le scorciatoie sono utili il 99% del tempo, e ti fregano solo negli esperimenti fatti apposta. In un certo senso, la vera magia non sono le illusioni: è che quasi sempre il tuo cervello ci azzecca.",
             "sparkles"),
        ]),
        "summary": "Non vedi il mondo così com'è: il tuo cervello lo ricostruisce con previsioni, memoria e piccoli ritocchi. Vedere è sempre un atto creativo.",
    },
    {
        "id": "why-time-flies",
        "category_id": "psicologia",
        "category_name": "Psicologia",
        "category_icon": "sparkles-outline",
        "category_color": "#FF006A",
        "title": "Perché il tempo vola quando ti diverti?",
        "highlight_words": ["tempo", "vola"],
        "hook": "Un'ora in coda alla posta dura una settimana. Un weekend con gli amici dura mezz'ora. Il tempo esiste, ma tu lo percepisci in modo bizzarro.",
        "hero_image": "https://images.unsplash.com/photo-1495364141860-b0d03eccd065?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Il tempo oggettivo",
             "Il tempo misurato dagli orologi è preciso e uguale per tutti: un secondo è un secondo. Gli orologi atomici moderni sbagliano meno di un secondo in 100 milioni di anni. Eppure tu vivi in un altro tempo, molto più elastico: quello percepito. Non è un difetto, è come funziona il cervello. Le due dimensioni convivono, e ogni giorno ti trovi a saltare tra un tempo oggettivo e un tempo interiore.",
             "time"),
            ("Il tempo è memoria",
             "Il cervello non ha un orologio unico: costruisce la percezione del tempo mettendo insieme quanti \"eventi\" hai registrato in memoria. Più eventi diversi vivi in un intervallo, più quell'intervallo ti sembra lungo dopo. Meno eventi, più corto. Un'ora in cui non succede nulla, mentre la stai vivendo, sembra lunghissima; ma nella memoria sembra corta. È un paradosso reale, provato in laboratorio.",
             "hourglass"),
            ("Perché ti diverti e vola",
             "Quando ti diverti, il cervello è pienamente coinvolto in quello che sta facendo. Non fa da \"osservatore\" del tempo: è dentro all'esperienza. Questo stato, che gli psicologi chiamano flow, riduce l'attenzione al passare dei minuti. Poi guardi l'orologio e scopri che sono passate tre ore. È lo stesso motivo per cui i bambini piccoli, sempre pienamente presenti a quello che fanno, hanno una percezione del tempo diversa dalla nostra.",
             "flash"),
            ("Perché in coda dura un'eternità",
             "Quando sei annoiato, il cervello ha poco da elaborare, quindi si mette in \"modalità osservatore\" e presta attenzione al tempo stesso. Il tempo diventa il compito principale, e ogni secondo pesa doppio. È lo stesso motivo per cui un dolore acuto dura tantissimo mentre lo vivi: la parte del cervello che monitorizza il tempo è pienamente attivata perché tutto il resto è fermo.",
             "sad"),
            ("Perché gli anni sembrano più corti",
             "Da adulti, molte delle nostre giornate si somigliano: routine, gli stessi tragitti, gli stessi ambienti. Il cervello \"comprime\" i giorni ripetitivi in un unico ricordo e i mesi passano in fretta nella memoria. I bambini vivono continuamente cose nuove, quindi in retrospettiva le loro estati durano un'eternità. La ricetta per rallentare il tempo da adulti è semplice, non facile: fare cose nuove.",
             "calendar"),
            ("Cosa puoi farci",
             "Se vuoi ricordare di più della tua vita, non serve fermare il tempo: basta rompere la routine. Un viaggio, un corso, un incontro nuovo, un percorso diverso per tornare a casa. Ogni piccolo elemento inatteso lascia una traccia in memoria e allunga la percezione retrospettiva del tempo. Il tempo non si ferma, ma si può letteralmente rendere più denso, momento dopo momento.",
             "sparkles"),
        ]),
        "summary": "Il cervello percepisce il tempo in base al numero di eventi memorizzati. Più novità vivi, più il tempo sembra rallentare.",
    },
    # --------------------- CULTURA / CURIOSITA ---------------------
    {
        "id": "espresso-italian",
        "category_id": "cultura",
        "category_name": "Cultura",
        "category_icon": "globe-outline",
        "category_color": "#00D2FF",
        "title": "Perché l'espresso è solo italiano?",
        "highlight_words": ["espresso", "italiano"],
        "hook": "Un rituale di 30 secondi che il resto del mondo prova a copiare e non ci riesce mai davvero. Il segreto? Non è solo il caffè.",
        "hero_image": "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Cos'è un espresso",
             "L'espresso è un metodo di estrazione del caffè: acqua a circa 90°C viene spinta a 9 bar di pressione attraverso 7 grammi di caffè macinato fine per 25-30 secondi. Il risultato è una tazzina da 25-30 ml con una crema densa e nocciola. Non è \"caffè forte\": è caffè concentrato, dove aromi, oli e caffeina sono estratti in modo diverso da qualsiasi altro metodo al mondo.",
             "cafe"),
            ("Un'invenzione del Novecento",
             "La macchina espresso nasce all'inizio del '900. Nel 1901 Luigi Bezzera brevetta il primo modello industriale: usare vapore per accelerare l'estrazione. Ma il vero salto arriva nel 1938 con Gaggia: la leva a molla che spinge l'acqua non con vapore ma con pressione meccanica. È quel gesto, quella leva, a creare la crema per la prima volta. Da lì l'espresso diventa quello che conosciamo.",
             "hardware-chip"),
            ("Perché in Italia funziona",
             "L'espresso in Italia è ovunque: ogni bar ne fa centinaia al giorno. Questa altissima frequenza tiene le macchine perfettamente tarate, il caffè sempre fresco, i baristi allenati. In un paese in cui in media si prende un espresso in 3 minuti e in piedi al bancone, l'infrastruttura sociale sostiene la qualità. In un paese dove il caffè si prende una volta al giorno, seduti, la macchina è quasi sempre fredda.",
             "flame"),
            ("Non è solo la macchina",
             "L'acqua italiana è mediamente adatta all'espresso: né troppo dura né troppo dolce. Le miscele italiane classiche mescolano Arabica e Robusta in proporzioni diverse per bilanciare aroma, corpo e crema. Anche la macinatura, che deve essere finissima e regolata quotidianamente in base all'umidità, richiede esperienza. Fuori dall'Italia si trova ottimo caffè, ma spesso manca l'insieme di piccoli dettagli quotidiani.",
             "water"),
            ("Il rituale sociale",
             "Un espresso non è solo la bevanda: è il rituale attorno alla bevanda. Il bancone, i due o tre minuti in cui parli con il barista o con lo sconosciuto accanto, il momento breve ma completo in cui ti fermi. Fuori dall'Italia, gli spazi \"caffè\" sono spesso concepiti per stare seduti a lungo: bello, ma è un'esperienza diversa. L'espresso è una pausa, non un accompagnamento.",
             "people"),
            ("Il resto del mondo prova",
             "Australia, Giappone, USA e nord Europa hanno una loro cultura del caffè d'autore, spesso di altissima qualità, ma quasi mai basata sull'espresso classico. Fanno filtri, latte art, cold brew. Molti locali di caffè specialty italiano stanno spingendo verso nuove miscele monorigine e macchine più sofisticate. Non è una guerra: è una prova che, quando l'espresso è fatto bene, resta uno dei modi più concentrati e magici di gustare un chicco.",
             "sparkles"),
        ]),
        "summary": "L'espresso è una tecnica precisa che dipende da macchina, acqua, miscela e rituale sociale. L'Italia ha tutti questi ingredienti insieme.",
    },
    {
        "id": "why-we-sleep",
        "category_id": "corpo-umano",
        "category_name": "Corpo umano",
        "category_icon": "heart-outline",
        "category_color": "#FF006A",
        "title": "Perché passiamo un terzo della vita a dormire?",
        "highlight_words": ["dormire"],
        "hook": "Ogni notte perdi coscienza per ore. Sembra un difetto evolutivo. In realtà è forse l'invenzione biologica più importante che hai a disposizione.",
        "hero_image": "https://images.unsplash.com/photo-1531353826977-0941b4779a1c?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Un enigma evolutivo",
             "Se un animale passa un terzo della vita immobile, indifeso, incosciente, è una condanna evolutiva. Eppure dormono tutti i mammiferi, gli uccelli, i rettili, perfino i pesci e alcuni insetti. L'evoluzione, che scarta tutto ciò che non serve, ha conservato il sonno per centinaia di milioni di anni. Il che significa una cosa sola: dormire deve fare qualcosa di straordinariamente utile, altrimenti sarebbe stato eliminato.",
             "moon"),
            ("Le fasi del sonno",
             "Il sonno non è un unico stato: è una sequenza di cicli di circa 90 minuti che si ripetono 4-6 volte a notte. Ogni ciclo attraversa sonno leggero, sonno profondo (slow wave sleep) e sonno REM (con i sogni). Il sonno profondo domina la prima parte della notte, il REM aumenta verso il mattino. Ogni fase ha un ruolo diverso: se salti anche solo un ciclo, il tuo cervello se ne accorge il giorno dopo.",
             "layers"),
            ("Il cervello si pulisce",
             "Durante il sonno profondo, il cervello attiva un sistema chiamato glinfatico: gli spazi tra i neuroni si allargano fino al 60% e il liquido cerebrospinale li attraversa lavando via prodotti di scarto. Uno di questi è la beta-amiloide, la proteina implicata nell'Alzheimer. In pratica dormire è come lavare il cervello. Poche notti insonni raddoppiano l'accumulo di queste sostanze: è biologicamente misurabile.",
             "water"),
            ("La memoria si consolida",
             "Ciò che impari durante il giorno viene fissato di notte. Il cervello rigioca a velocità aumentata le informazioni importanti e le trasferisce dalla memoria a breve termine (ippocampo) a quella a lungo termine (corteccia). Studenti che dormono 8 ore dopo aver studiato ricordano fino al 40% in più rispetto a chi dorme meno. Non si studia \"nel sonno\": si consolida ciò che si è studiato quando si era svegli.",
             "book"),
            ("I sogni servono davvero",
             "Il REM è la fase in cui sogniamo di più. In quella fase il cervello elabora emozioni, unisce ricordi apparentemente scollegati, e allena la capacità di risolvere problemi. Molte grandi intuizioni artistiche e scientifiche sono nate da sogni: la struttura del benzene di Kekulé, alcune melodie dei Beatles, l'idea per Frankenstein di Mary Shelley. Il REM è la fabbrica creativa notturna.",
             "cloud"),
            ("Cosa succede se non dormi",
             "Dopo 17 ore senza sonno le tue capacità cognitive equivalgono a chi ha 0,5 g/l di alcol nel sangue. Dopo 24 ore, 1,0 g/l. La privazione cronica di sonno aumenta il rischio di malattie cardiovascolari, diabete, depressione, obesità. Il sonno non è \"tempo perso\": è una delle poche attività che il tuo corpo pretende attivamente per potersi mantenere in ordine. È forse la miglior medicina naturale che possiedi.",
             "sparkles"),
        ]),
        "summary": "Dormire ripulisce il cervello, consolida la memoria ed elabora emozioni. È uno dei processi biologici più importanti che facciamo.",
    },
    {
        "id": "aurora-borealis",
        "category_id": "natura",
        "category_name": "Natura",
        "category_icon": "leaf-outline",
        "category_color": "#00E676",
        "title": "Come si accende un'aurora boreale?",
        "highlight_words": ["aurora", "boreale"],
        "hook": "Non è nebbia, non è un riflesso: è una tempesta solare che dipinge il cielo. E ha bisogno di un miracolo silenzioso: il campo magnetico della Terra.",
        "hero_image": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Tutto comincia dal Sole",
             "Il Sole non è una palla di fuoco tranquilla: è un reattore turbolento che, in continuazione, sputa nello spazio flussi di particelle cariche (elettroni e protoni). Questo flusso si chiama vento solare, e viaggia nello spazio a centinaia di chilometri al secondo. Durante le tempeste solari (eruzioni sulla superficie della stella), il vento può essere molto più intenso: miliardi di tonnellate di particelle scagliate contro il resto del sistema solare.",
             "sunny"),
            ("Lo scudo invisibile",
             "La Terra ha un campo magnetico generato dal proprio nucleo di ferro fuso in rotazione. Questo campo si estende per migliaia di chilometri nello spazio e forma una specie di bolla protettiva chiamata magnetosfera. Senza di essa, il vento solare eroderebbe l'atmosfera come sta facendo con quella di Marte da miliardi di anni. Il campo magnetico è letteralmente la pelle invisibile del pianeta.",
             "shield"),
            ("Dove il vento passa",
             "Il campo magnetico terrestre è più aperto ai poli, come le calamite. Nelle regioni polari, alcune particelle del vento solare riescono a scendere lungo le linee del campo e a penetrare nell'atmosfera. È lì, tra 100 e 300 chilometri di quota, che comincia lo spettacolo. Prima di arrivare a terra queste particelle incontrano l'aria, ricca di ossigeno e azoto.",
             "compass"),
            ("La luce nasce da un urto",
             "Quando una particella solare urta un atomo di ossigeno o di azoto, gli trasferisce energia. L'atomo, così caricato, torna al suo stato normale rilasciando un piccolo lampo di luce. Miliardi di piccoli lampi contemporanei creano il velo colorato che vediamo dal terreno. Il meccanismo è identico a quello di un tubo al neon: gas eccitato da elettroni che emette luce.",
             "flash"),
            ("Perché i colori cambiano",
             "L'ossigeno a 100 km di altitudine emette luce verde: il colore più comune. Sopra i 200 km emette rosso, molto più raro. L'azoto emette blu e viola. Ogni volta che vedi un'aurora rossa in cima al velo verde, stai vedendo ossigeno molto in alto. Le aurore più spettacolari accendono più colori insieme, perché la tempesta solare è così intensa da spingere le particelle a quote diverse contemporaneamente.",
             "color-palette"),
            ("Non solo nell'artico",
             "Aurora \"boreale\" è al nord, \"australe\" al sud (Antartide, Nuova Zelanda). Durante tempeste solari eccezionali le aurore possono scendere fino alle latitudini di Italia, Spagna, Messico. La grande tempesta di Carrington del 1859 le rese visibili anche in Cuba. Con l'attuale ciclo solare di massima attività (2024-2026), le probabilità di vederle a latitudini insolite sono più alte del solito: un occhio al cielo notturno, ogni tanto, potrebbe premiarti.",
             "sparkles"),
        ]),
        "summary": "Le aurore nascono dallo scontro tra particelle solari e atomi della nostra atmosfera, guidate dal campo magnetico terrestre.",
    },
    {
        "id": "why-yawn-cat",
        "category_id": "curiosita",
        "category_name": "Curiosità",
        "category_icon": "help-circle-outline",
        "category_color": "#B200FF",
        "title": "Perché i gatti fanno le fusa?",
        "highlight_words": ["gatti", "fusa"],
        "hook": "Il suono più rilassante del pianeta è anche uno dei più misteriosi. E fa più cose di quanto immagini.",
        "hero_image": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=1200&q=80&auto=format&fit=crop",
        "reading_time_min": 2,
        "deep_dive_time_min": 3,
        "chapters": _chapters([
            ("Un motorino biologico",
             "Le fusa sono una vibrazione ritmica che il gatto produce continuamente mentre inspira ed espira. La frequenza è tra 25 e 150 Hz, un intervallo particolarmente basso. Ascoltata da vicino sembra un piccolo motore, e non a caso: il gatto è probabilmente l'animale che più si avvicina a un dispositivo meccanico integrato nel corpo. Tutti i felini piccoli fanno le fusa; i grandi (leoni, tigri) no, perché la loro laringe è costruita diversamente per ruggire.",
             "musical-note"),
            ("Come nascono",
             "Il meccanismo è controllato dal cervello: un segnale ritmico oscilla tra 25 e 150 volte al secondo e comanda ai muscoli della laringe di aprirsi e chiudersi rapidamente. Ogni volta che il gatto respira, l'aria attraversa questa laringe che vibra e produce il caratteristico ronron. È un movimento involontario ma controllato: il gatto sceglie di attivarlo, un po' come noi scegliamo di sorridere.",
             "pulse"),
            ("Non solo per felicità",
             "Il pensiero comune è che il gatto fa le fusa perché è felice, e in gran parte è vero. Ma non è l'unico motivo. I gatti fanno le fusa anche quando sono spaventati, malati, feriti o addirittura in fin di vita. In quei casi le fusa hanno una funzione diversa: si auto-consolano, un po' come noi ci dondoliamo o cantiamo sottovoce quando siamo tesi.",
             "sad"),
            ("Fanno guarire?",
             "Studi hanno mostrato che la frequenza delle fusa (25-150 Hz) coincide con l'intervallo che accelera la guarigione ossea e la rigenerazione dei tessuti muscolari negli esperimenti di laboratorio. Anche negli astronauti si usano frequenze simili per contrastare la perdita di massa ossea in assenza di gravità. Non è provato al 100% che le fusa guariscano il gatto, ma molte prove suggeriscono che sia una specie di terapia interna.",
             "medkit"),
            ("La comunicazione con noi",
             "Alcuni gatti hanno sviluppato un tipo speciale di fusa detto solicitation purr: una miscela di ronron con un piccolo miagolio ad alta frequenza (300-600 Hz) sovrapposto. Quella frequenza è vicina a quella del pianto di un neonato umano. Non è un caso: attiva nel nostro cervello un istinto di cura immediato. In pratica, alcuni gatti hanno imparato a manipolarci in modo evolutivamente elegante.",
             "megaphone"),
            ("Fanno bene anche a noi",
             "Vivere con un gatto che fa le fusa abbassa la pressione arteriosa, riduce il cortisolo (ormone dello stress) e diminuisce il rischio di infarto negli anziani secondo alcuni studi. È il motivo per cui la pet therapy con i gatti funziona così bene. Il tuo gatto non lo fa apposta, ma quel piccolo motore che accende ogni sera sul tuo divano è, con ogni probabilità, uno dei migliori antidoti quotidiani allo stress moderno.",
             "sparkles"),
        ]),
        "summary": "Le fusa sono vibrazioni prodotte dalla laringe: aiutano il gatto a rilassarsi, guarire e comunicare con noi in modo sorprendentemente sofisticato.",
    },
]

# Override every story's hero_image with the CURATED topic-specific URL from
# image_prompts.STORY_IMAGE_URLS. This is the single source of truth for
# fallback images (used until AI-generated ones are ready).
try:
    from image_prompts import STORY_IMAGE_URLS as _IMG
    for _s in STORIES:
        _override = _IMG.get(_s["id"])
        if _override:
            _s["hero_image"] = _override
except Exception:
    pass

# Merge expansion packs.
try:
    from seed_data_more import MORE_STORIES as _MORE_A
    STORIES.extend(_MORE_A)
except Exception as _e:
    print(f"seed_data_more not loaded: {_e}")

try:
    from seed_data_more_b import MORE_STORIES_B as _MORE_B
    STORIES.extend(_MORE_B)
except Exception as _e:
    print(f"seed_data_more_b not loaded: {_e}")

# Storie scritte a mano per completare 10 storie per categoria (v5.2)
for _mod in (
    "seed_pack_economia",
    "seed_pack_arte",
    "seed_pack_geografia",
    "seed_pack_topup_a",
    "seed_pack_topup_b",
):
    try:
        _m = __import__(_mod)
        STORIES.extend(_m.STORIES)
    except Exception as _e:
        print(f"{_mod} not loaded: {_e}")

# Pack v4: storie + lezioni (ex lavoro interrotto, ora integrati al seed).
for _mod in ("seed_pack_v4_a", "seed_pack_v4_b", "seed_pack_v4_c"):
    try:
        _m = __import__(_mod)
        STORIES.extend(_m.STORIES)
        STORIES.extend(_m.LESSONS)
    except Exception as _e:
        print(f"{_mod} not loaded: {_e}")

# Pack v5: storie + lezioni bilingue (ora integrati al seed, "attivala tutta").
for _mod in ("seed_pack_v5_a", "seed_pack_v5_b", "seed_pack_v5_c", "seed_pack_v5_d", "seed_pack_v5_e", "seed_pack_v7_arte_geo", "seed_pack_v8", "seed_pack_v9"):
    try:
        _m = __import__(_mod)
        STORIES.extend(getattr(_m, "STORIES", []))
        STORIES.extend(getattr(_m, "LESSONS", []))
    except Exception as _e:
        print(f"{_mod} not loaded: {_e}")

# Traduzioni EN scritte a mano per le storie v5.2 (mappa id -> translations['en'])
_EN_MAP = {}
for _mod in ("seed_en_economia", "seed_en_arte", "seed_en_geografia", "seed_en_topup", "seed_en_generated"):
    try:
        _m = __import__(_mod)
        _EN_MAP.update(_m.EN)
    except Exception as _e:
        print(f"{_mod} not loaded: {_e}")
if _EN_MAP:
    for _s in STORIES:
        _tr = _EN_MAP.get(_s["id"])
        if _tr:
            _s.setdefault("translations", {})["en"] = _tr

# Keep legacy source packs as an archive, but expose the current taxonomy.
from category_taxonomy import apply_seed_taxonomy
apply_seed_taxonomy(CATEGORIES, STORIES)
