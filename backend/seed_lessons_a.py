"""PAUSE — Mini lezioni scritte a mano (parte A): scienza, spazio, tecnologia, natura, animali, storia, psicologia.
Ogni lezione insegna UN concetto in 5 passi, con obiettivo dichiarato. IT + EN."""
from story_builder import mk_lesson as L, ICON_POOL, GLOWS

LESSONS = [
    # ------------------------------ SCIENZA ------------------------------
    L("scienza", "lez-metodo-scientifico",
      "Come ragiona uno scienziato: il metodo in 4 passi", ["metodo"],
      "Non serve un laboratorio per pensare come uno scienziato. Serve un'abitudine: dubitare in modo ordinato.",
      "Applicare il metodo scientifico a una domanda di tutti i giorni, distinguendo ipotesi, test e conclusione.",
      "Osserva, formula un'ipotesi che si possa smentire, mettila alla prova e accetta il verdetto dei dati. Ripeti.",
      [
          ("Passo 1 — Osserva e chiedi",
           "Tutto parte da una domanda precisa. \"Perché la pianta sul davanzale sta morendo?\" è meglio di \"perché le piante muoiono?\". Una buona domanda è piccola, concreta e riguarda qualcosa che puoi misurare: quanta acqua riceve, quanta luce, da quanto tempo ingiallisce."),
          ("Passo 2 — Formula un'ipotesi falsificabile",
           "Un'ipotesi è una spiegazione provvisoria che può essere smentita. \"La pianta ha poca luce\" è falsificabile: se la sposti e non migliora, l'ipotesi cade. \"La pianta è sfortunata\" non lo è. Il segreto del metodo è scegliere idee che possano perdere."),
          ("Passo 3 — Metti alla prova cambiando UNA cosa",
           "Sposta la pianta alla luce ma lascia tutto il resto uguale: stessa acqua, stesso vaso. Se cambi due cose insieme non saprai quale ha funzionato. Questo è il principio del gruppo di controllo: confrontare due situazioni identiche tranne che per un dettaglio."),
          ("Passo 4 — Concludi e ricomincia",
           "Dopo una settimana guardi il risultato. Se la pianta migliora, l'ipotesi regge (per ora). Se no, ne formuli un'altra. La scienza non dimostra verità definitive: elimina spiegazioni sbagliate una alla volta. Chi cambia idea davanti ai dati non ha perso, ha imparato."),
      ],
      en={
          "title": "How a scientist thinks: the method in 4 steps", "highlight_words": ["method"],
          "hook": "You don't need a lab to think like a scientist. You need a habit: doubting in an orderly way.",
          "objective": "Apply the scientific method to an everyday question, separating hypothesis, test and conclusion.",
          "summary": "Observe, form a hypothesis that can be disproved, test it and accept the verdict of the data. Repeat.",
          "chapters": [
              ("Step 1 — Observe and ask", "Everything starts with a precise question. \"Why is the plant on my windowsill dying?\" beats \"why do plants die?\". A good question is small, concrete and about something you can measure: how much water it gets, how much light, how long it has been yellowing."),
              ("Step 2 — Form a falsifiable hypothesis", "A hypothesis is a provisional explanation that can be disproved. \"The plant gets too little light\" is falsifiable: move it and if nothing improves, the idea fails. \"The plant is unlucky\" is not. The secret of the method is choosing ideas that can lose."),
              ("Step 3 — Test by changing ONE thing", "Move the plant into the light but keep everything else the same: same water, same pot. Change two things at once and you won't know which one worked. This is the control-group principle: compare two situations identical except for a single detail."),
              ("Step 4 — Conclude and start again", "After a week you look at the result. If the plant improves, the hypothesis holds (for now). If not, you form another one. Science does not prove final truths: it eliminates wrong explanations one at a time. Changing your mind in front of data isn't losing — it's learning."),
          ],
      }),

    L("scienza", "lez-energia-conservazione",
      "Cos'è davvero l'energia (e perché non si crea mai)", ["energia"],
      "Diciamo \"ho finito l'energia\" ma l'energia non finisce mai: cambia solo forma. Capirlo cambia il modo di guardare tutto.",
      "Riconoscere le principali forme di energia e usare il principio di conservazione per spiegare fenomeni quotidiani.",
      "L'energia è la capacità di produrre un cambiamento. Si trasforma (cinetica, potenziale, termica, chimica) ma la quantità totale resta uguale.",
      [
          ("Una definizione operativa",
           "L'energia è ciò che serve per far accadere qualcosa: sollevare, scaldare, muovere, illuminare. Si misura in joule. Un joule è circa l'energia per alzare una mela di un metro. Una barretta di cioccolato ne contiene circa un milione."),
          ("Le forme principali",
           "Cinetica: energia del movimento (un'auto che corre). Potenziale: energia \"in attesa\" per posizione (un sasso in cima a una collina) o per forma (una molla compressa). Chimica: nei legami tra atomi (cibo, benzina). Termica: agitazione delle molecole. Elettrica, luminosa, nucleare completano il quadro."),
          ("La regola d'oro: si conserva",
           "In un sistema chiuso la quantità totale di energia non cambia mai. Un pendolo trasforma potenziale in cinetica e viceversa; l'attrito la trasforma in calore, ma la somma è costante. Nessuna macchina crea energia dal nulla: la converte, sempre perdendone una parte in calore."),
          ("Applicalo a una giornata",
           "La colazione (chimica) diventa movimento (cinetica) e calore corporeo (termica). La luce del sole (luminosa) diventa zucchero nelle piante (chimica). Quando \"finisci l'energia\" hai semplicemente trasformato quella disponibile in forme meno utili, soprattutto calore disperso."),
      ],
      en={
          "title": "What energy really is (and why it is never created)", "highlight_words": ["energy"],
          "hook": "We say \"I'm out of energy\", but energy never runs out: it only changes form. Understanding this changes how you see everything.",
          "objective": "Recognise the main forms of energy and use the conservation principle to explain everyday phenomena.",
          "summary": "Energy is the capacity to produce change. It transforms (kinetic, potential, thermal, chemical) but the total amount stays the same.",
          "chapters": [
              ("A working definition", "Energy is what it takes to make something happen: lift, heat, move, light up. It is measured in joules. One joule is roughly the energy to raise an apple by one metre. A chocolate bar holds about a million."),
              ("The main forms", "Kinetic: energy of motion (a speeding car). Potential: energy \"waiting\" because of position (a rock on a hilltop) or shape (a compressed spring). Chemical: in the bonds between atoms (food, petrol). Thermal: the jiggling of molecules. Electrical, light and nuclear complete the picture."),
              ("The golden rule: it is conserved", "In a closed system the total amount of energy never changes. A pendulum turns potential into kinetic and back; friction turns it into heat, but the sum is constant. No machine creates energy from nothing: it converts it, always losing some as heat."),
              ("Apply it to a day", "Breakfast (chemical) becomes movement (kinetic) and body heat (thermal). Sunlight (light) becomes sugar in plants (chemical). When you \"run out of energy\" you have simply turned what was available into less useful forms — mostly dispersed heat."),
          ],
      }),

    # ------------------------------ SPAZIO ------------------------------
    L("spazio", "lez-orientarsi-stelle",
      "Come orientarsi con le stelle in 4 mosse", ["stelle"],
      "Prima del GPS chiunque sapeva trovare il nord guardando in alto. Puoi impararlo stasera, dal balcone.",
      "Trovare la Stella Polare (o la Croce del Sud) e ricavare i punti cardinali senza strumenti.",
      "Trova il Grande Carro, prolunga di cinque volte il lato corto e arrivi alla Polare: quella direzione è il nord. Il resto segue.",
      [
          ("Passo 1 — Trova il Grande Carro",
           "Nell'emisfero nord cerca sette stelle luminose a forma di pentola con manico: è il Grande Carro, parte dell'Orsa Maggiore. È visibile tutto l'anno, anche se ruota intorno al polo celeste nel corso della notte e delle stagioni."),
          ("Passo 2 — Prolunga il lato corto",
           "Prendi le due stelle del bordo esterno della \"pentola\" (quelle opposte al manico). Traccia una linea immaginaria e prolungala di circa cinque volte la loro distanza: incontri una stella di media luminosità, sola. È la Polare, la punta del manico del Piccolo Carro."),
          ("Passo 3 — Dalla Polare ai punti cardinali",
           "La Polare sta quasi esattamente sopra il polo nord: guardandola, hai il nord davanti, il sud dietro, l'est a destra e l'ovest a sinistra. La sua altezza sull'orizzonte, in gradi, coincide con la tua latitudine: a Roma è a circa 42°."),
          ("Passo 4 — E nell'emisfero sud?",
           "Non esiste una stella polare australe luminosa. Si usa la Croce del Sud: prolunga l'asse lungo della croce di circa 4,5 volte e arrivi a un punto vuoto del cielo, il polo sud celeste. Scendi in verticale fino all'orizzonte: quello è il sud."),
      ],
      en={
          "title": "How to navigate by the stars in 4 moves", "highlight_words": ["stars"],
          "hook": "Before GPS anyone could find north by looking up. You can learn it tonight, from your balcony.",
          "objective": "Find the North Star (or the Southern Cross) and derive the cardinal points without instruments.",
          "summary": "Find the Big Dipper, extend the short side five times and you reach Polaris: that direction is north. The rest follows.",
          "chapters": [
              ("Step 1 — Find the Big Dipper", "In the northern hemisphere look for seven bright stars shaped like a saucepan with a handle: the Big Dipper, part of Ursa Major. It is visible all year, although it rotates around the celestial pole through the night and the seasons."),
              ("Step 2 — Extend the short side", "Take the two stars on the outer edge of the \"pan\" (opposite the handle). Draw an imaginary line and extend it about five times their distance: you meet a lone star of medium brightness. That is Polaris, the tip of the Little Dipper's handle."),
              ("Step 3 — From Polaris to the cardinal points", "Polaris sits almost exactly above the north pole: facing it, north is ahead, south behind, east to your right, west to your left. Its height above the horizon, in degrees, equals your latitude: in Rome it is about 42°."),
              ("Step 4 — And in the southern hemisphere?", "There is no bright southern pole star. Use the Southern Cross: extend the long axis of the cross about 4.5 times and you reach an empty spot in the sky, the south celestial pole. Drop straight down to the horizon: that is south."),
          ],
      }),

    L("spazio", "lez-orbite-gravita",
      "Perché i pianeti non cadono nel Sole: le orbite spiegate", ["orbite"],
      "La Terra cade verso il Sole in ogni istante. Eppure non lo raggiunge mai. Il trucco è la velocità laterale.",
      "Spiegare un'orbita come caduta continua e collegare velocità, distanza e durata dell'anno.",
      "Un'orbita è una caduta che manca sempre il bersaglio: la gravità tira verso il centro, la velocità laterale spinge di lato. L'equilibrio dei due produce il cerchio (o l'ellisse).",
      [
          ("La palla di cannone di Newton",
           "Immagina di sparare una palla di cannone in orizzontale da una montagna. Cade e tocca terra dopo qualche chilometro. Sparala più forte: cade più lontano. A circa 28.000 km/h la curva della caduta coincide con la curvatura della Terra: la palla cade per sempre senza toccare il suolo. È in orbita."),
          ("Due ingredienti, un equilibrio",
           "La gravità del Sole tira la Terra verso il centro. La velocità della Terra (circa 107.000 km/h) la spinge in linea retta. Sommando le due, la traiettoria si incurva in un anello. Se la velocità sparisse, cadremmo nel Sole in circa 64 giorni. Se raddoppiasse, scapperemmo via."),
          ("Più lontano, più lento, più lungo",
           "La gravità si indebolisce con la distanza, quindi i pianeti lontani orbitano più lentamente e su percorsi più lunghi. Mercurio completa un giro in 88 giorni, Nettuno in 165 anni. È la terza legge di Keplero: il quadrato del periodo cresce con il cubo della distanza."),
          ("Perché le orbite sono ellissi",
           "Quasi nessuna orbita è un cerchio perfetto. Se un corpo va un po' più veloce del necessario in un punto, si allontana, rallenta, ricade e riaccelera: il risultato è un'ellisse. La Terra è a 147 milioni di km dal Sole a gennaio e a 152 a luglio: l'ellisse è leggera, ma c'è."),
      ],
      en={
          "title": "Why planets don't fall into the Sun: orbits explained", "highlight_words": ["orbits"],
          "hook": "Earth falls toward the Sun every instant. Yet it never gets there. The trick is sideways speed.",
          "objective": "Explain an orbit as continuous falling and connect speed, distance and the length of a year.",
          "summary": "An orbit is a fall that always misses the target: gravity pulls to the centre, sideways speed pushes aside. Their balance produces a circle (or an ellipse).",
          "chapters": [
              ("Newton's cannonball", "Imagine firing a cannonball horizontally from a mountain. It falls and lands a few kilometres away. Fire harder: it lands farther. At about 28,000 km/h the curve of its fall matches Earth's curvature: the ball falls forever without touching the ground. It is in orbit."),
              ("Two ingredients, one balance", "The Sun's gravity pulls Earth toward the centre. Earth's speed (about 107,000 km/h) pushes it in a straight line. Add the two and the path bends into a ring. If the speed vanished we would fall into the Sun in about 64 days. If it doubled, we would escape."),
              ("Farther, slower, longer", "Gravity weakens with distance, so distant planets orbit more slowly along longer paths. Mercury completes a lap in 88 days, Neptune in 165 years. That is Kepler's third law: the square of the period grows with the cube of the distance."),
              ("Why orbits are ellipses", "Almost no orbit is a perfect circle. If a body moves slightly faster than needed at one point, it drifts away, slows, falls back and speeds up again: the result is an ellipse. Earth is 147 million km from the Sun in January and 152 in July: a gentle ellipse, but an ellipse."),
          ],
      }),

    # ------------------------------ TECNOLOGIA ------------------------------
    L("tecnologia", "lez-password-sicura",
      "Come si costruisce una password davvero sicura", ["password"],
      "\"P@ssw0rd!\" sembra furba. Un computer la indovina in meno di un secondo. La lunghezza batte la complessità.",
      "Capire come vengono violate le password e costruirne una resistente e memorizzabile con il metodo delle frasi.",
      "Le password si violano per tentativi: ogni carattere in più moltiplica il lavoro. Usa frasi lunghe, mai riutilizzate, e un gestore di password.",
      [
          ("Come vengono violate",
           "Nessuno \"indovina\" a mano. Un programma prova miliardi di combinazioni al secondo, partendo dalle più comuni: parole del dizionario, nomi, date, sostituzioni banali come 0 al posto di O. \"P@ssw0rd!\" è nella lista dei primi tentativi."),
          ("La matematica della lunghezza",
           "Con 8 caratteri tra lettere, numeri e simboli le combinazioni sono circa 6 milioni di miliardi: un computer moderno le esaurisce in ore. Ogni carattere aggiunto moltiplica per circa 90. A 16 caratteri servono milioni di anni. La lunghezza è la difesa più economica."),
          ("Il metodo della frase",
           "Scegli quattro o cinque parole a caso e incollale: \"tramonto-bicicletta-42-formaggio\". È lunga, facile da ricordare, impossibile da indovinare. Evita citazioni famose e frasi personali (il nome del cane è pubblico su Instagram)."),
          ("Le due regole che contano davvero",
           "Prima: mai la stessa password su due siti. Quando un sito viene bucato, i ladri provano la coppia email-password ovunque. Seconda: usa un gestore di password che le generi e ricordi per te, e attiva la verifica in due passaggi sugli account importanti."),
      ],
      en={
          "title": "How to build a truly secure password", "highlight_words": ["password"],
          "hook": "\"P@ssw0rd!\" looks clever. A computer guesses it in under a second. Length beats complexity.",
          "objective": "Understand how passwords are cracked and build a strong, memorable one using the passphrase method.",
          "summary": "Passwords are cracked by trial: every extra character multiplies the work. Use long phrases, never reused, and a password manager.",
          "chapters": [
              ("How they are cracked", "Nobody \"guesses\" by hand. A program tries billions of combinations per second, starting with the most common: dictionary words, names, dates, trivial swaps like 0 for O. \"P@ssw0rd!\" is on the list of first attempts."),
              ("The maths of length", "With 8 characters mixing letters, digits and symbols there are about 6 quadrillion combinations: a modern computer exhausts them in hours. Each added character multiplies by about 90. At 16 characters it takes millions of years. Length is the cheapest defence."),
              ("The passphrase method", "Pick four or five random words and glue them: \"sunset-bicycle-42-cheese\". Long, easy to remember, impossible to guess. Avoid famous quotes and personal phrases (your dog's name is public on Instagram)."),
              ("The two rules that really matter", "First: never the same password on two sites. When one site is breached, thieves try the email-password pair everywhere. Second: use a password manager that generates and remembers them for you, and turn on two-step verification for important accounts."),
          ],
      }),

    L("tecnologia", "lez-algoritmo",
      "Cos'è un algoritmo: imparare a pensare per passi", ["algoritmo"],
      "Una ricetta, le istruzioni per un mobile, il percorso per la scuola: usi algoritmi da sempre. Ora impari a scriverli.",
      "Definire un algoritmo, riconoscerne le tre strutture base e scriverne uno semplice in linguaggio naturale.",
      "Un algoritmo è una sequenza finita di passi non ambigui che risolve un problema. Si costruisce con sequenza, scelta e ripetizione.",
      [
          ("La definizione, senza computer",
           "Un algoritmo è un elenco ordinato di istruzioni precise che, eseguite, portano a un risultato. \"Fai bollire l'acqua, butta la pasta, aspetta 10 minuti, scola\" è un algoritmo. \"Cuoci finché è buona\" no: è ambiguo. Il computer esegue solo ciò che è definito senza margine di interpretazione."),
          ("Le tre strutture base",
           "Sequenza: fai A, poi B, poi C. Scelta (se… allora… altrimenti): se piove prendi l'ombrello, altrimenti gli occhiali da sole. Ripetizione (finché…): finché il bicchiere non è pieno, versa. Ogni programma esistente, dal termostato a un'intelligenza artificiale, è combinazione di queste tre."),
          ("Scriviamone uno: trovare il numero più grande",
           "Hai una lista di numeri. Algoritmo: 1) chiama \"massimo\" il primo numero; 2) per ogni numero successivo, se è più grande del massimo, diventa il nuovo massimo; 3) alla fine della lista, il massimo è la risposta. Sequenza, ripetizione e scelta, insieme."),
          ("Perché un algoritmo può essere lento",
           "Due algoritmi corretti possono avere velocità diversissime. Cercare un nome sfogliando l'elenco pagina per pagina richiede in media metà elenco. Aprire a metà, decidere se il nome è prima o dopo, e ripetere (ricerca binaria) trova qualunque nome tra un milione in soli 20 passi. Pensare bene i passi vale più di un computer veloce."),
      ],
      en={
          "title": "What an algorithm is: learning to think in steps", "highlight_words": ["algorithm"],
          "hook": "A recipe, furniture instructions, the route to school: you have always used algorithms. Now you learn to write them.",
          "objective": "Define an algorithm, recognise its three basic structures and write a simple one in plain language.",
          "summary": "An algorithm is a finite sequence of unambiguous steps that solves a problem. It is built from sequence, selection and repetition.",
          "chapters": [
              ("The definition, no computer needed", "An algorithm is an ordered list of precise instructions that, when followed, produce a result. \"Boil water, add pasta, wait 10 minutes, drain\" is an algorithm. \"Cook until it's good\" is not: it's ambiguous. A computer only executes what is defined with no room for interpretation."),
              ("The three basic structures", "Sequence: do A, then B, then C. Selection (if… then… else): if it rains take the umbrella, otherwise the sunglasses. Repetition (while…): while the glass is not full, pour. Every program in existence, from a thermostat to an AI, is a combination of these three."),
              ("Let's write one: find the largest number", "You have a list of numbers. Algorithm: 1) call the first number \"max\"; 2) for every following number, if it is larger than max, it becomes the new max; 3) at the end of the list, max is the answer. Sequence, repetition and selection, together."),
              ("Why an algorithm can be slow", "Two correct algorithms can differ hugely in speed. Finding a name by flipping through a directory page by page takes half the book on average. Opening in the middle, deciding whether the name comes before or after, and repeating (binary search) finds any name among a million in just 20 steps. Thinking the steps through beats a faster computer."),
          ],
      }),

    # ------------------------------ NATURA ------------------------------
    L("natura", "lez-ciclo-acqua",
      "Il ciclo dell'acqua: dove va la pioggia di oggi", ["ciclo"],
      "L'acqua che bevi ha attraversato nuvole, ghiacciai e dinosauri. Non se ne crea di nuova: gira, da miliardi di anni.",
      "Descrivere le quattro fasi del ciclo dell'acqua e spiegare perché l'acqua dolce è una risorsa limitata.",
      "Evaporazione, condensazione, precipitazione e raccolta: il Sole muove l'acqua in un ciclo chiuso. Solo il 2,5% è dolce e quasi tutta è ghiaccio o falda.",
      [
          ("Fase 1 — Evaporazione",
           "Il Sole scalda oceani, laghi e suolo: le molecole d'acqua più energetiche sfuggono come vapore. Anche le piante contribuiscono con la traspirazione dalle foglie: una grande quercia rilascia centinaia di litri al giorno. Il vapore è invisibile e sale perché è più leggero dell'aria."),
          ("Fase 2 — Condensazione",
           "Salendo, l'aria si raffredda e il vapore torna liquido attorno a minuscole particelle di polvere o sale: nascono le goccioline che formano le nuvole. Una nuvola è acqua sospesa, non vapore. Lo stesso accade sul vetro freddo di una bibita in estate."),
          ("Fase 3 — Precipitazione",
           "Le goccioline si urtano, si fondono e crescono finché l'aria non le sostiene più: cadono come pioggia, o come neve e grandine se fa freddo abbastanza. Una goccia di pioggia media è formata da circa un milione di goccioline di nuvola."),
          ("Fase 4 — Raccolta e il conto finale",
           "L'acqua scorre in fiumi verso il mare, si infiltra nelle falde sotterranee o resta secoli nei ghiacciai. Poi il ciclo ricomincia. Sul totale, il 97,5% è salata; del 2,5% dolce, due terzi sono ghiaccio. Quella facilmente accessibile in fiumi e laghi è meno dello 0,01%: per questo sprecarla conta."),
      ],
      en={
          "title": "The water cycle: where today's rain goes", "highlight_words": ["cycle"],
          "hook": "The water you drink has passed through clouds, glaciers and dinosaurs. No new water is made: it circulates, and has for billions of years.",
          "objective": "Describe the four phases of the water cycle and explain why fresh water is a limited resource.",
          "summary": "Evaporation, condensation, precipitation and collection: the Sun drives water through a closed loop. Only 2.5% is fresh and almost all of it is ice or groundwater.",
          "chapters": [
              ("Phase 1 — Evaporation", "The Sun warms oceans, lakes and soil: the most energetic water molecules escape as vapour. Plants contribute too, transpiring through their leaves: a large oak releases hundreds of litres a day. Vapour is invisible and rises because it is lighter than air."),
              ("Phase 2 — Condensation", "As it rises, the air cools and the vapour turns back to liquid around tiny particles of dust or salt: droplets form, and droplets form clouds. A cloud is suspended water, not vapour. The same happens on the cold glass of a summer drink."),
              ("Phase 3 — Precipitation", "Droplets collide, merge and grow until the air can no longer hold them: they fall as rain, or as snow and hail if it is cold enough. An average raindrop is made of about a million cloud droplets."),
              ("Phase 4 — Collection, and the final count", "Water flows in rivers to the sea, seeps into underground aquifers or sits for centuries in glaciers. Then the cycle restarts. Of the total, 97.5% is salty; of the 2.5% fresh, two thirds is ice. The easily reachable part in rivers and lakes is under 0.01%: that is why wasting it matters."),
          ],
      }),

    L("natura", "lez-leggere-nuvole",
      "Come leggere le nuvole per prevedere il tempo", ["nuvole"],
      "I marinai lo facevano senza app. Tre forme di nuvola e una regola sull'altezza bastano per capire cosa succederà tra qualche ora.",
      "Riconoscere cirri, cumuli e strati e collegarli a un'evoluzione probabile del tempo nelle ore successive.",
      "Nuvole alte e sottili (cirri) annunciano un cambiamento; cumuli bianchi isolati significano bel tempo; strati grigi uniformi portano pioggia leggera e lunga; cumulonembi a torre, temporale.",
      [
          ("Le tre famiglie",
           "Le nuvole prendono il nome dalla forma e dall'altezza. Cirri: filamenti bianchi altissimi, sopra i 6.000 metri, fatti di ghiaccio. Cumuli: batuffoli a base piatta a media altezza. Strati: coperte grigie uniformi e basse. Il prefisso \"nembo\" indica che sta piovendo."),
          ("Cirri: il preavviso",
           "Cirri sottili che si infittiscono da ovest nel giro di mezza giornata sono spesso il bordo anteriore di una perturbazione: il fronte caldo arriva in 12-24 ore. Un cielo con pochi cirri isolati invece resta stabile. Se noti anche un alone attorno al Sole o alla Luna, la pioggia è più probabile."),
          ("Cumuli: leggi la crescita",
           "Cumuli piccoli, bianchi e ben separati alle 10 del mattino indicano una giornata serena. Se nel primo pomeriggio crescono in altezza e le sommità diventano scure o a forma di cavolfiore, l'aria è instabile: possono trasformarsi in cumulonembi, torri di temporale con incudine in cima."),
          ("Strati e la regola dell'altezza",
           "Una coperta grigia bassa e uniforme (stratocumuli o nembostrati) porta pioggia fine ma prolungata. Regola pratica: più le nuvole si abbassano e si uniformano nel corso delle ore, più il peggioramento è vicino; più si alzano e si frammentano, più il tempo migliora."),
      ],
      en={
          "title": "How to read clouds to forecast the weather", "highlight_words": ["clouds"],
          "hook": "Sailors did it without apps. Three cloud shapes and one rule about height are enough to know what happens in a few hours.",
          "objective": "Recognise cirrus, cumulus and stratus and link them to a likely weather evolution in the following hours.",
          "summary": "High thin clouds (cirrus) announce change; isolated white cumulus mean fair weather; uniform grey stratus bring light, long rain; towering cumulonimbus, a storm.",
          "chapters": [
              ("The three families", "Clouds are named by shape and height. Cirrus: very high white filaments above 6,000 metres, made of ice. Cumulus: flat-bottomed puffs at medium height. Stratus: uniform low grey blankets. The prefix \"nimbo\" means it is raining."),
              ("Cirrus: the early warning", "Thin cirrus thickening from the west over half a day is often the leading edge of a weather system: the warm front arrives in 12-24 hours. A sky with a few isolated cirrus stays stable instead. If you also notice a halo around the Sun or Moon, rain is more likely."),
              ("Cumulus: read the growth", "Small, white, well-separated cumulus at 10 a.m. point to a fine day. If by early afternoon they grow taller and their tops turn dark or cauliflower-shaped, the air is unstable: they can become cumulonimbus, storm towers with an anvil on top."),
              ("Stratus and the height rule", "A low, uniform grey blanket (stratocumulus or nimbostratus) brings fine but prolonged rain. Rule of thumb: the lower and more uniform clouds become over the hours, the closer the deterioration; the higher and more broken they become, the more the weather improves."),
          ],
      }),

    # ------------------------------ ANIMALI ------------------------------
    L("animali", "lez-classificare-animali",
      "Come si classificano gli animali: la mappa in 4 livelli", ["classificano"],
      "Un delfino è un pesce? Un pipistrello è un uccello? Con quattro domande in ordine non sbagli più.",
      "Usare i criteri di base (colonna vertebrale, respirazione, pelle, riproduzione) per collocare un animale nella sua classe.",
      "Prima chiedi: ha la colonna vertebrale? Poi: respira con branchie o polmoni? Che pelle ha? Come nascono i piccoli? Le risposte portano a pesci, anfibi, rettili, uccelli o mammiferi.",
      [
          ("Livello 1 — Vertebrato o invertebrato?",
           "La prima divisione riguarda lo scheletro interno. I vertebrati (pesci, anfibi, rettili, uccelli, mammiferi) sono solo il 3% delle specie. Il resto sono invertebrati: insetti, ragni, molluschi, meduse, vermi. Un polpo, pur intelligentissimo, è un invertebrato."),
          ("Livello 2 — Come respira e che pelle ha?",
           "I pesci respirano con le branchie e hanno squame. Gli anfibi nascono in acqua con branchie e da adulti passano ai polmoni, con pelle nuda e umida. I rettili hanno polmoni e squame secche. Uccelli: polmoni e piume. Mammiferi: polmoni e peli, anche pochi (il delfino ne ha alla nascita)."),
          ("Livello 3 — Come nascono i piccoli?",
           "Pesci, anfibi, rettili e uccelli depongono uova (con eccezioni). I mammiferi partoriscono piccoli vivi e li allattano: è il latte il vero marchio della classe. Il platypus depone uova ma allatta: è un mammifero, con un'eccezione che conferma quanto la natura ami i confini sfumati."),
          ("Applica: delfino e pipistrello",
           "Il delfino: colonna vertebrale sì, polmoni (sale a respirare), pelle liscia con pochi peli alla nascita, partorisce e allatta. Mammifero, non pesce. Il pipistrello: vertebrato, polmoni, pelo, partorisce e allatta. Mammifero, non uccello: le ali sono mani con dita lunghissime rivestite di pelle."),
      ],
      en={
          "title": "How animals are classified: the 4-level map", "highlight_words": ["classified"],
          "hook": "Is a dolphin a fish? Is a bat a bird? With four questions in order you'll never get it wrong again.",
          "objective": "Use basic criteria (backbone, breathing, skin, reproduction) to place an animal in its class.",
          "summary": "First ask: does it have a backbone? Then: gills or lungs? What kind of skin? How are the young born? The answers lead to fish, amphibians, reptiles, birds or mammals.",
          "chapters": [
              ("Level 1 — Vertebrate or invertebrate?", "The first split is about the internal skeleton. Vertebrates (fish, amphibians, reptiles, birds, mammals) are only 3% of species. The rest are invertebrates: insects, spiders, molluscs, jellyfish, worms. An octopus, however brilliant, is an invertebrate."),
              ("Level 2 — How does it breathe, what skin does it have?", "Fish breathe with gills and have scales. Amphibians are born in water with gills and switch to lungs as adults, with bare moist skin. Reptiles have lungs and dry scales. Birds: lungs and feathers. Mammals: lungs and hair, even very little (a dolphin has some at birth)."),
              ("Level 3 — How are the young born?", "Fish, amphibians, reptiles and birds lay eggs (with exceptions). Mammals give birth to live young and nurse them: milk is the true hallmark of the class. The platypus lays eggs yet nurses: it is a mammal, an exception that shows how much nature loves blurry lines."),
              ("Apply it: dolphin and bat", "The dolphin: backbone yes, lungs (it surfaces to breathe), smooth skin with a few hairs at birth, gives birth and nurses. Mammal, not fish. The bat: vertebrate, lungs, fur, gives birth and nurses. Mammal, not bird: its wings are hands with very long fingers covered in skin."),
          ],
      }),

    L("animali", "lez-ecolocalizzazione",
      "Come funziona l'ecolocalizzazione: vedere con le orecchie", ["ecolocalizzazione"],
      "Un pipistrello al buio totale evita un filo sottile come un capello. Non lo vede: lo ascolta. Ecco come.",
      "Spiegare il principio dell'eco, come pipistrelli e delfini lo usano e perché lo stesso principio è nel sonar e nell'ecografia.",
      "Emetti un suono, misura quanto tempo impiega l'eco a tornare e da quale direzione: ottieni distanza e posizione. Pipistrelli, delfini, sonar ed ecografie funzionano così.",
      [
          ("Il principio: il tempo dell'eco",
           "Il suono viaggia nell'aria a circa 340 metri al secondo. Se gridi verso una parete e l'eco torna dopo un secondo, la parete è a 170 metri (il suono ha fatto andata e ritorno). Ridurre tutto a millesimi di secondo e a oggetti piccoli è esattamente ciò che fa un pipistrello."),
          ("Il pipistrello: ultrasuoni e volto a imbuto",
           "Emette dalla bocca o dal naso fino a 200 impulsi al secondo a frequenze di 20-100 kHz, oltre il nostro udito. Le onde corte rimbalzano anche su una zanzara. Le orecchie grandi e mobili captano l'eco; il cervello confronta il ritardo tra le due orecchie e ricava la direzione con precisione di pochi gradi."),
          ("Il delfino: suoni nell'acqua",
           "Nell'acqua il suono corre quattro volte più veloce e più lontano. Il delfino produce clic nelle cavità nasali e li focalizza con il \"melone\", il cuscinetto di grasso sulla fronte, come una lente acustica. Riceve l'eco attraverso la mascella inferiore. Distingue una pallina di plastica da una di metallo a 100 metri."),
          ("La stessa idea nelle nostre mani",
           "Il sonar delle navi manda impulsi verso il fondale e misura il ritorno: così si tracciano le mappe degli oceani. L'ecografia usa ultrasuoni che rimbalzano sui tessuti del corpo e ricostruisce un'immagine. I sensori di parcheggio delle auto fanno lo stesso. Abbiamo copiato il pipistrello, con un ritardo di 50 milioni di anni."),
      ],
      en={
          "title": "How echolocation works: seeing with your ears", "highlight_words": ["echolocation"],
          "hook": "A bat in total darkness dodges a thread as thin as a hair. It doesn't see it: it hears it. Here is how.",
          "objective": "Explain the echo principle, how bats and dolphins use it, and why the same idea powers sonar and ultrasound scans.",
          "summary": "Emit a sound, measure how long the echo takes to return and from which direction: you get distance and position. Bats, dolphins, sonar and ultrasound all work this way.",
          "chapters": [
              ("The principle: echo timing", "Sound travels through air at about 340 metres per second. If you shout at a wall and the echo returns after one second, the wall is 170 metres away (the sound went there and back). Shrinking that to thousandths of a second and tiny objects is exactly what a bat does."),
              ("The bat: ultrasound and a funnel face", "It emits up to 200 pulses a second from mouth or nose at 20-100 kHz, beyond our hearing. Short waves bounce even off a mosquito. Large mobile ears catch the echo; the brain compares the delay between the two ears and works out direction to within a few degrees."),
              ("The dolphin: sound in water", "In water sound travels four times faster and farther. The dolphin produces clicks in its nasal cavities and focuses them with the \"melon\", the fatty pad on its forehead, like an acoustic lens. It receives the echo through its lower jaw. It can tell a plastic ball from a metal one at 100 metres."),
              ("The same idea in our hands", "Ships' sonar sends pulses to the seabed and times the return: that is how ocean maps are drawn. Ultrasound scans use high-frequency sound bouncing off body tissues to build an image. Car parking sensors do the same. We copied the bat, 50 million years late."),
          ],
      }),

    # ------------------------------ STORIA ------------------------------
    L("storia", "lez-linea-del-tempo",
      "Come leggere una linea del tempo: secoli, a.C. e d.C.", ["tempo"],
      "\"Il XV secolo\" sono gli anni 1400. Sembra un trucco, e infatti c'è una regola semplice che nessuno spiega mai.",
      "Convertire anni in secoli e viceversa, calcolare durate a cavallo dell'anno zero e collocare eventi su una linea del tempo.",
      "Il secolo è il numero delle centinaia più uno (1492 → XV secolo). Prima di Cristo si conta a ritroso e non esiste l'anno zero: da 50 a.C. a 50 d.C. passano 99 anni.",
      [
          ("La regola del +1",
           "Il I secolo va dall'anno 1 al 100; il II dal 101 al 200. Per trovare il secolo di un anno prendi le centinaia e aggiungi uno: 1492 → 14 + 1 = XV secolo. 2024 → XXI. Attenzione agli anni tondi: il 1500 è ancora XV secolo, il 1501 apre il XVI."),
          ("Prima di Cristo si conta al contrario",
           "Gli anni avanti Cristo scorrono a ritroso: 300 a.C. viene prima di 200 a.C. Il III secolo a.C. va dal 300 al 201 a.C. Cesare muore nel 44 a.C., quindi nel I secolo a.C.; Augusto muore nel 14 d.C., nel I secolo d.C. Due imperatori, stesso \"primo secolo\", lati opposti."),
          ("Non esiste l'anno zero",
           "Il calendario passa direttamente dall'1 a.C. all'1 d.C. Per calcolare una durata a cavallo della nascita di Cristo somma gli anni e togli uno: da 50 a.C. a 50 d.C. sono 99 anni, non 100. Piccolo dettaglio che fa sbagliare molti calcoli sull'età di Roma."),
          ("Disegna la tua linea",
           "Prendi un foglio, traccia una riga e segna a intervalli regolari i secoli. Colloca tre eventi che conosci: la caduta di Roma (476), la scoperta dell'America (1492), la Rivoluzione francese (1789). Vedere gli spazi tra le date insegna più di qualsiasi elenco: tra Roma e Colombo passano mille anni, tra Colombo e oggi solo cinquecento."),
      ],
      en={
          "title": "How to read a timeline: centuries, BC and AD", "highlight_words": ["timeline"],
          "hook": "\"The 15th century\" means the 1400s. It looks like a trick, and indeed there's a simple rule nobody ever explains.",
          "objective": "Convert years to centuries and back, calculate spans across year zero and place events on a timeline.",
          "summary": "The century is the hundreds digit plus one (1492 → 15th century). Before Christ we count backwards and there is no year zero: from 50 BC to AD 50 is 99 years.",
          "chapters": [
              ("The +1 rule", "The 1st century runs from year 1 to 100; the 2nd from 101 to 200. To find a year's century take the hundreds and add one: 1492 → 14 + 1 = 15th century. 2024 → 21st. Beware round years: 1500 is still the 15th century, 1501 opens the 16th."),
              ("Before Christ counts backwards", "BC years run in reverse: 300 BC comes before 200 BC. The 3rd century BC runs from 300 to 201 BC. Caesar dies in 44 BC, so in the 1st century BC; Augustus dies in AD 14, in the 1st century AD. Two emperors, same \"first century\", opposite sides."),
              ("There is no year zero", "The calendar jumps straight from 1 BC to AD 1. To calculate a span across the birth of Christ, add the years and subtract one: from 50 BC to AD 50 is 99 years, not 100. A small detail that trips up many calculations about the age of Rome."),
              ("Draw your own line", "Take a sheet, draw a line and mark the centuries at regular intervals. Place three events you know: the fall of Rome (476), Columbus (1492), the French Revolution (1789). Seeing the gaps between dates teaches more than any list: a thousand years separate Rome and Columbus, only five hundred separate Columbus and today."),
          ],
      }),

    L("storia", "lez-valutare-fonte",
      "Come valutare una fonte storica (e una notizia di oggi)", ["fonte"],
      "Gli storici hanno un metodo per non farsi ingannare da documenti falsi e testimoni di parte. Funziona anche con i social.",
      "Distinguere fonti primarie e secondarie e applicare le cinque domande dello storico a qualunque documento o notizia.",
      "Chi lo ha scritto, quando, per chi, perché e cosa dicono le altre fonti? Cinque domande separano un documento affidabile da una versione di comodo.",
      [
          ("Primarie e secondarie",
           "Una fonte primaria nasce nel periodo studiato: una lettera, un'iscrizione, un registro, una foto. Una secondaria la interpreta dopo: un libro di storia, un documentario. Le primarie sono più vicine ai fatti ma non più oggettive: anche chi scriveva nel 1300 aveva interessi e pregiudizi."),
          ("Le prime tre domande: chi, quando, per chi",
           "Chi ha prodotto la fonte e che posizione aveva? Un generale che racconta la propria battaglia tende a vincerla. Quando è stata scritta: durante i fatti o trent'anni dopo, a memoria? Per chi: un diario privato, un rapporto ufficiale, un discorso pubblico cambiano completamente ciò che si dice e si omette."),
          ("Le altre due: perché e cosa dicono gli altri",
           "Perché è stata prodotta: informare, convincere, giustificare, vendere? Poi il passo decisivo, la corroborazione: altre fonti indipendenti confermano? Se un evento è raccontato da nemici, alleati e neutrali in modo compatibile, è solido. Se esiste un'unica voce, resta un'ipotesi."),
          ("Applicalo a oggi",
           "Un post virale è una fonte. Chi lo pubblica e con che interesse? È del momento o riciclato da anni prima? Per quale pubblico? Per informare o per indignare? Lo confermano testate indipendenti? Le stesse cinque domande che smontano un falso medievale smontano una bufala in trenta secondi."),
      ],
      en={
          "title": "How to evaluate a historical source (and today's news)", "highlight_words": ["source"],
          "hook": "Historians have a method to avoid being fooled by forged documents and biased witnesses. It works on social media too.",
          "objective": "Tell primary from secondary sources and apply the historian's five questions to any document or news item.",
          "summary": "Who wrote it, when, for whom, why, and what do other sources say? Five questions separate a reliable document from a convenient version.",
          "chapters": [
              ("Primary and secondary", "A primary source originates in the period studied: a letter, an inscription, a ledger, a photo. A secondary one interprets it later: a history book, a documentary. Primary sources are closer to the facts but not more objective: someone writing in 1300 had interests and prejudices too."),
              ("The first three questions: who, when, for whom", "Who produced the source and what was their position? A general recounting his own battle tends to win it. When was it written: during the events or thirty years later, from memory? For whom: a private diary, an official report and a public speech completely change what is said and what is left out."),
              ("The other two: why, and what others say", "Why was it produced: to inform, persuade, justify, sell? Then the decisive step, corroboration: do other independent sources confirm it? If an event is told compatibly by enemies, allies and neutrals, it is solid. If there is a single voice, it remains a hypothesis."),
              ("Apply it today", "A viral post is a source. Who posts it and with what interest? Is it current or recycled from years ago? For which audience? To inform or to outrage? Do independent outlets confirm it? The same five questions that dismantle a medieval forgery dismantle a hoax in thirty seconds."),
          ],
      }),

    # ------------------------------ PSICOLOGIA ------------------------------
    L("psicologia", "lez-memoria-tecniche",
      "Come funziona la memoria e come usarla meglio", ["memoria"],
      "Non hai una brutta memoria. Hai un sistema di archiviazione che nessuno ti ha spiegato. Quattro regole lo fanno rendere il doppio.",
      "Descrivere le tre fasi della memoria e applicare ripetizione distanziata, richiamo attivo e associazione per ricordare di più.",
      "Codifica, immagazzinamento, recupero. Si ricorda ciò che si richiama attivamente, a intervalli crescenti, collegato a ciò che già si sa.",
      [
          ("Le tre fasi",
           "Codifica: l'informazione entra e viene trasformata in tracce neurali; l'attenzione decide cosa passa. Immagazzinamento: la memoria a breve termine tiene circa 4-7 elementi per pochi secondi; il consolidamento, soprattutto nel sonno, li sposta nella memoria a lungo termine. Recupero: ritrovare la traccia quando serve. Molti \"vuoti\" sono problemi di recupero, non di archivio."),
          ("Regola 1 — Richiama, non rileggere",
           "Rileggere dà una sensazione di familiarità che inganna. Chiudere il libro e provare a riscrivere ciò che ricordi è dieci volte più efficace: lo sforzo del recupero rinforza la traccia. Fai domande a te stesso, usa flashcard, spiega a qualcuno."),
          ("Regola 2 — Distanzia le ripetizioni",
           "La curva dell'oblio: dopo un giorno si perde oltre la metà di quanto appreso. Ma ogni ripasso fatto poco prima di dimenticare appiattisce la curva. Ripassa dopo un giorno, poi tre, poi una settimana, poi un mese. Stesso tempo totale, ricordo che dura anni invece di giorni."),
          ("Regola 3 e 4 — Associa e dormi",
           "Il cervello ricorda meglio ciò che ha agganci: collega il nuovo a immagini, luoghi, storie (le date diventano età di persone che conosci, i nomi diventano immagini buffe). Poi dormi: durante il sonno profondo l'ippocampo rigioca la giornata e trasferisce i ricordi alla corteccia. Studiare fino alle 3 sottrae l'unico momento in cui la memoria si salva davvero."),
      ],
      en={
          "title": "How memory works and how to use it better", "highlight_words": ["memory"],
          "hook": "You don't have a bad memory. You have a filing system nobody ever explained. Four rules make it twice as effective.",
          "objective": "Describe the three stages of memory and apply spaced repetition, active recall and association to remember more.",
          "summary": "Encoding, storage, retrieval. You remember what you actively recall, at growing intervals, linked to what you already know.",
          "chapters": [
              ("The three stages", "Encoding: information enters and is turned into neural traces; attention decides what gets through. Storage: short-term memory holds about 4-7 items for a few seconds; consolidation, mostly during sleep, moves them to long-term memory. Retrieval: finding the trace when needed. Many \"blanks\" are retrieval problems, not storage problems."),
              ("Rule 1 — Recall, don't reread", "Rereading gives a misleading sense of familiarity. Closing the book and trying to write down what you remember is ten times more effective: the effort of retrieval strengthens the trace. Quiz yourself, use flashcards, explain it to someone."),
              ("Rule 2 — Space your repetitions", "The forgetting curve: after one day more than half of what you learned is gone. But every review done just before forgetting flattens the curve. Review after one day, then three, then a week, then a month. Same total time, a memory that lasts years instead of days."),
              ("Rules 3 and 4 — Associate, and sleep", "The brain remembers what has hooks: link new material to images, places, stories (dates become the ages of people you know, names become funny pictures). Then sleep: during deep sleep the hippocampus replays the day and hands memories to the cortex. Studying until 3 a.m. steals the only moment when memory truly saves."),
          ],
      }),

    L("psicologia", "lez-bias-conferma",
      "Il bias di conferma: come riconoscerlo in te stesso", ["bias"],
      "Cerchi prove che ti danno ragione e scarti quelle contrarie. Lo fanno tutti, anche gli scienziati. Ma si può allenare l'antidoto.",
      "Definire il bias di conferma, riconoscerne tre segnali tipici e applicare due tecniche per ridurlo nelle decisioni.",
      "Il bias di conferma ci fa cercare, interpretare e ricordare le informazioni in modo da confermare ciò che già crediamo. Antidoti: cercare attivamente la smentita e considerare l'opposto.",
      [
          ("Che cos'è",
           "È la tendenza a dare più peso a ciò che conferma le nostre idee e a ignorare o svalutare ciò che le contraddice. Non è stupidità: il cervello risparmia energia evitando di rimettere in discussione ciò che crede di sapere. Il costo è che le convinzioni sbagliate durano molto più del dovuto."),
          ("I tre segnali",
           "Primo: cerchi solo dove sai di trovare conferme (una ricerca \"il caffè fa bene\" dà risultati diversi da \"il caffè fa male\"). Secondo: interpreti dati ambigui a tuo favore. Terzo: ricordi vividamente i casi che ti danno ragione e dimentichi gli altri. Se un dibattito ti lascia più convinto di prima, il bias ha lavorato."),
          ("Antidoto 1 — Cerca la smentita",
           "Prima di decidere, chiediti: \"quale prova mi farebbe cambiare idea?\" e vai a cercarla davvero. Leggi il miglior argomento della parte opposta, non il peggiore. Se non riesci a immaginare nulla che ti smentirebbe, non hai un'opinione: hai una fede."),
          ("Antidoto 2 — Considera l'opposto",
           "Tecnica testata in laboratorio: prima di concludere, scrivi tre motivi per cui potresti avere torto. Riduce misurabilmente l'errore. Funziona anche in gruppo: nominare un \"avvocato del diavolo\" con il compito esplicito di attaccare la decisione fa emergere rischi che nessuno voleva vedere."),
      ],
      en={
          "title": "Confirmation bias: how to spot it in yourself", "highlight_words": ["bias"],
          "hook": "You look for evidence that proves you right and discard what doesn't. Everyone does it, scientists included. But the antidote can be trained.",
          "objective": "Define confirmation bias, recognise three typical signs and apply two techniques to reduce it in decisions.",
          "summary": "Confirmation bias makes us seek, interpret and remember information so it confirms what we already believe. Antidotes: actively seek disproof and consider the opposite.",
          "chapters": [
              ("What it is", "It is the tendency to give more weight to what confirms our ideas and to ignore or discount what contradicts them. It is not stupidity: the brain saves energy by not re-examining what it thinks it knows. The cost is that wrong beliefs last far longer than they should."),
              ("The three signs", "First: you only search where you know you'll find confirmation (a search for \"coffee is good for you\" gives different results from \"coffee is bad for you\"). Second: you interpret ambiguous data in your favour. Third: you vividly remember the cases that prove you right and forget the rest. If a debate leaves you more convinced than before, the bias has been at work."),
              ("Antidote 1 — Seek the disproof", "Before deciding, ask: \"what evidence would change my mind?\" and genuinely go looking for it. Read the other side's best argument, not its worst. If you can't imagine anything that would refute you, you don't have an opinion: you have a faith."),
              ("Antidote 2 — Consider the opposite", "A lab-tested technique: before concluding, write three reasons you might be wrong. It measurably reduces error. It works in groups too: appointing a \"devil's advocate\" whose explicit job is to attack the decision surfaces risks nobody wanted to see."),
          ],
      }),
]


# ---------------------------------------------------------------------------
# 5° passo — le mini lezioni ora hanno la stessa gerarchia delle curiosità:
# 5 capitoli + la voce "Da ricordare" (summary). Il 5° passo è generato da
# generate_lesson_step5.py e vive in seed_lessons_step5.STEP5; qui lo appendiamo
# come capitolo 5 a ciascuna lezione (IT nel doc, EN in translations.en).
# ---------------------------------------------------------------------------
try:
    from seed_lessons_step5 import STEP5
except Exception:
    STEP5 = {}


def _append_step5(lesson: dict) -> None:
    extra = STEP5.get(lesson["id"])
    if not extra:
        return
    pool = ICON_POOL[lesson["category_id"]]
    idx = len(lesson["chapters"])  # 0-based index of the new chapter (=4)
    it_title, it_body = extra["it"]
    lesson["chapters"].append({
        "number": idx + 1,
        "title": it_title,
        "body": it_body,
        "icon": pool[idx % len(pool)],
        "glow_color": GLOWS[idx % len(GLOWS)],
    })
    tr = lesson.get("translations", {}).get("en")
    if tr is not None:
        en_title, en_body = extra["en"]
        tr["chapters"].append({"title": en_title, "body": en_body})


for _lesson in LESSONS:
    _append_step5(_lesson)
