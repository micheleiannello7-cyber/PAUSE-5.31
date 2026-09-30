"""Standalone seed: adds the "Sport & Movimento" category + content.

Run once: `python seed_pack_sport.py`. Idempotent (upserts by id). Stories are
backdated well past the early-access window so free users see them immediately.
The main startup seeder only upserts its own known ids, so these documents
survive restarts untouched.
"""
import asyncio
import os
from datetime import datetime, timezone, timedelta

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

CAT = {
    "id": "sport",
    "color": "#FF7A00",
    "emoji_key": "sport",
    "icon": "basketball-outline",
    "name": "Sport & Movimento",
    "name_en": "Sports & Movement",
}

GLOW = ["#00E5FF", "#B200FF", "#FF6D00", "#FF006A", "#00E676"]
ICONS = ["fitness", "flame", "trophy", "walk", "heart"]
HERO = "https://images.unsplash.com/photo-1517649763962-0c623066013b"


def story(sid, kind, title, title_en, hook, hook_en, hlw, hlw_en, summary, summary_en, chapters, objective=None, objective_en=None):
    ch_it = []
    ch_en = []
    for i, (t_it, b_it, t_en, b_en) in enumerate(chapters):
        ch_it.append({"number": i + 1, "title": t_it, "body": b_it, "icon": ICONS[i % len(ICONS)], "glow_color": GLOW[i % len(GLOW)]})
        ch_en.append({"title": t_en, "body": b_en})
    doc = {
        "id": sid,
        "category_color": CAT["color"],
        "category_icon": CAT["icon"],
        "category_id": CAT["id"],
        "category_name": CAT["name"],
        "chapters": ch_it,
        "deep_dive_time_min": 3,
        "hero_image": HERO,
        "highlight_words": hlw,
        "hook": hook,
        "kind": kind,
        "reading_time_min": 2,
        "summary": summary,
        "title": title,
        "translations": {"en": {"title": title_en, "highlight_words": hlw_en, "hook": hook_en, "summary": summary_en, "chapters": ch_en}},
    }
    if kind == "lesson":
        doc["objective"] = objective
        doc["translations"]["en"]["objective"] = objective_en
    return doc


STORIES = [
    story(
        "sport-second-wind", "story",
        "Il \"secondo fiato\": mito o realtà?",
        "The \"second wind\": myth or reality?",
        "A volte, dopo una fatica iniziale, correre diventa improvvisamente più facile. Cosa succede al corpo?",
        "Sometimes, after an initial struggle, running suddenly feels easier. What happens to the body?",
        ["secondo", "fiato"], ["second", "wind"],
        "Il secondo fiato nasce dall'adattamento di respiro, cuore e metabolismo allo sforzo: il corpo trova un nuovo equilibrio.",
        "The second wind comes from breathing, heart and metabolism adapting to effort: the body finds a new balance.",
        [
            ("L'attrito iniziale", "Nei primi minuti il corpo fatica a passare dall'energia immediata a quella prodotta con l'ossigeno. Respiro affannoso e gambe pesanti sono il prezzo di questa transizione.",
             "The initial friction", "In the first minutes the body struggles to switch from immediate energy to oxygen-based energy. Heavy breathing and legs are the price of that transition."),
            ("Il riequilibrio", "Dopo qualche minuto la respirazione si stabilizza, il cuore trova il ritmo giusto e i muscoli ricevono ossigeno a sufficienza. Ecco che lo sforzo sembra alleggerirsi.",
             "The rebalancing", "After a few minutes breathing stabilises, the heart finds its rhythm and muscles get enough oxygen. That's when the effort seems to lighten."),
            ("Testa e endorfine", "Contribuiscono anche le endorfine e un effetto psicologico: superato il disagio iniziale, la mente smette di concentrarsi sulla fatica.",
             "Mind and endorphins", "Endorphins and a psychological effect also help: past the initial discomfort, the mind stops focusing on the strain."),
        ],
    ),
    story(
        "sport-doms", "story",
        "Perché i muscoli fanno male due giorni dopo",
        "Why muscles ache two days later",
        "Il dolore muscolare spesso arriva il giorno dopo, o quello dopo ancora. Non è l'acido lattico.",
        "Muscle soreness often shows up the next day, or the one after. It's not lactic acid.",
        ["dolore", "muscolare"], ["muscle", "soreness"],
        "I DOMS derivano da micro-lesioni delle fibre e dall'infiammazione che le ripara, rendendo il muscolo più forte.",
        "DOMS come from micro-tears in the fibres and the inflammation that repairs them, making the muscle stronger.",
        [
            ("Non è l'acido lattico", "L'acido lattico viene smaltito in poche ore. Il dolore ritardato, chiamato DOMS, ha un'altra causa: piccole lesioni nelle fibre muscolari.",
             "It isn't lactic acid", "Lactic acid clears in a few hours. The delayed soreness, called DOMS, has another cause: tiny tears in the muscle fibres."),
            ("Micro-lesioni utili", "Sforzi nuovi o intensi creano micro-strappi. Il corpo li ripara con un processo infiammatorio che provoca gonfiore e sensibilità.",
             "Useful micro-tears", "New or intense efforts create micro-tears. The body repairs them with an inflammatory process that causes swelling and tenderness."),
            ("Più forti di prima", "Questa riparazione ricostruisce il muscolo un po' più robusto. È il motivo per cui, allenandosi con costanza, il dolore diminuisce.",
             "Stronger than before", "This repair rebuilds the muscle a little sturdier. That's why, with consistent training, the soreness fades."),
        ],
    ),
    story(
        "sport-marathon-wall", "story",
        "Il \"muro\" del maratoneta",
        "The marathon runner's \"wall\"",
        "Intorno al 30° chilometro molti maratoneti colpiscono un \"muro\". Perché proprio lì?",
        "Around the 30th kilometre many marathoners hit a \"wall\". Why exactly there?",
        ["muro", "maratoneta"], ["wall", "marathon"],
        "Il muro arriva quando finiscono le scorte di glicogeno: allenamento e alimentazione servono a spostarlo più in là.",
        "The wall hits when glycogen stores run out: training and nutrition push it further away.",
        [
            ("Il serbatoio di zuccheri", "I muscoli immagazzinano glicogeno, il carburante rapido. In una maratona le scorte bastano per circa due ore di corsa intensa.",
             "The sugar tank", "Muscles store glycogen, the fast fuel. In a marathon the stores last about two hours of intense running."),
            ("Quando finisce", "Esaurito il glicogeno, il corpo passa a bruciare grassi, più lenti da usare. Gambe pesanti e stanchezza improvvisa sono il \"muro\".",
             "When it runs out", "Once glycogen is gone, the body switches to burning fat, slower to use. Heavy legs and sudden fatigue are the \"wall\"."),
            ("Come spostarlo", "Allenamento, ritmo prudente e rifornimenti di zuccheri durante la gara aiutano a ritardare o evitare il muro.",
             "How to move it", "Training, a careful pace and taking on sugars during the race help delay or avoid the wall."),
        ],
    ),
    story(
        "sport-cold-water", "story",
        "Il ghiaccio dopo l'allenamento serve davvero?",
        "Does icing after training really help?",
        "Bagni gelati e borse del ghiaccio sono di moda tra gli atleti. Ma funzionano?",
        "Ice baths and ice packs are popular among athletes. But do they work?",
        ["ghiaccio", "recupero"], ["ice", "recovery"],
        "Il freddo riduce dolore e gonfiore a breve termine, ma usato sempre può frenare gli adattamenti dell'allenamento.",
        "Cold cuts pain and swelling short term, but used always it can blunt training adaptations.",
        [
            ("Effetto immediato", "Il freddo restringe i vasi sanguigni e attenua l'infiammazione: ci si sente meno indolenziti subito dopo lo sforzo.",
             "Immediate effect", "Cold narrows blood vessels and dampens inflammation: you feel less sore right after the effort."),
            ("Il rovescio della medaglia", "Proprio quell'infiammazione, però, è parte del processo che rende i muscoli più forti. Bloccarla sempre può ridurre i guadagni.",
             "The flip side", "Yet that very inflammation is part of what makes muscles stronger. Always blocking it can reduce the gains."),
            ("Quando usarlo", "Il ghiaccio è utile dopo gare o infortuni, meno in un normale ciclo di allenamento per la forza.",
             "When to use it", "Ice helps after races or injuries, less so during a normal strength-building cycle."),
        ],
    ),
    story(
        "sport-heart-athlete", "story",
        "Il cuore degli atleti batte più lento",
        "Athletes' hearts beat slower",
        "Molti sportivi hanno una frequenza cardiaca a riposo bassissima. È un buon segno.",
        "Many athletes have a very low resting heart rate. It's a good sign.",
        ["cuore", "atleti"], ["heart", "athletes"],
        "L'allenamento rende il cuore più grande ed efficiente: pompa più sangue a ogni battito, quindi ne servono meno.",
        "Training makes the heart larger and more efficient: it pumps more blood per beat, so fewer are needed.",
        [
            ("Un muscolo che si allena", "Il cuore è un muscolo. Con l'esercizio aerobico diventa più forte e le sue camere si dilatano leggermente.",
             "A muscle that trains", "The heart is a muscle. With aerobic exercise it grows stronger and its chambers widen slightly."),
            ("Più sangue per battito", "Un cuore più capiente spinge più sangue a ogni contrazione. Per fornire lo stesso ossigeno a riposo, basta battere meno spesso.",
             "More blood per beat", "A roomier heart pushes more blood per contraction. To deliver the same oxygen at rest, it needs to beat less often."),
            ("40 battiti al minuto", "Alcuni atleti di resistenza scendono sotto i 40 battiti a riposo, contro i 60-80 di una persona media.",
             "40 beats a minute", "Some endurance athletes drop below 40 resting beats, against 60-80 in an average person."),
        ],
    ),
    story(
        "sport-flow-state", "story",
        "La \"zona\": quando tutto viene facile",
        "The \"zone\": when everything flows",
        "Atleti e musicisti la chiamano \"flow\": quei momenti in cui il gesto sembra automatico e perfetto.",
        "Athletes and musicians call it \"flow\": moments when the move feels automatic and perfect.",
        ["zona", "flow"], ["zone", "flow"],
        "Il flow nasce quando la sfida è pari alle nostre capacità: il cervello riduce l'auto-controllo e il gesto diventa fluido.",
        "Flow arises when the challenge matches our skill: the brain eases self-monitoring and movement turns fluid.",
        [
            ("Sfida e abilità", "Il flow compare quando il compito è impegnativo ma alla nostra portata. Troppo facile annoia, troppo difficile stressa.",
             "Challenge and skill", "Flow appears when the task is demanding yet within reach. Too easy bores, too hard stresses."),
            ("Il cervello si zittisce", "Nel flow si attenua la parte del cervello che ci giudica. Senza quel \"rumore\" interno, i movimenti allenati escono da soli.",
             "The brain quiets", "In flow the self-judging part of the brain dims. Without that inner \"noise\", trained moves come out on their own."),
            ("Come favorirlo", "Obiettivi chiari, feedback immediato e concentrazione senza distrazioni rendono il flow più probabile.",
             "How to invite it", "Clear goals, instant feedback and distraction-free focus make flow more likely."),
        ],
    ),
    story(
        "sport-lesson-warmup", "lesson",
        "Come scaldarsi bene prima di allenarti",
        "How to warm up well before training",
        "Un buon riscaldamento riduce gli infortuni e migliora la prestazione. Ecco i passi essenziali.",
        "A good warm-up cuts injuries and boosts performance. Here are the essential steps.",
        ["riscaldamento"], ["warm-up"],
        "Scaldarsi significa aumentare gradualmente battito, temperatura e mobilità con movimenti dinamici, non stretching statico.",
        "Warming up means gradually raising heart rate, temperature and mobility with dynamic moves, not static stretching.",
        [
            ("Alza il motore", "Inizia con 3-5 minuti di attività leggera (camminata veloce, corsa lenta) per aumentare battito e temperatura del corpo.",
             "Raise the engine", "Start with 3-5 minutes of light activity (brisk walk, easy jog) to raise heart rate and body temperature."),
            ("Mobilità dinamica", "Fai movimenti ampi e controllati: slanci di gambe, rotazioni delle braccia, affondi. Preparano le articolazioni al gesto.",
             "Dynamic mobility", "Do broad, controlled moves: leg swings, arm circles, lunges. They prime the joints for the movement."),
            ("Specifico dello sport", "Concludi con qualche gesto simile a quello che farai, a bassa intensità: il corpo \"prova\" il movimento.",
             "Sport-specific", "Finish with a few low-intensity moves like the ones you'll perform: the body \"rehearses\" the motion."),
        ],
        objective="Costruire un riscaldamento in 3 fasi che previene infortuni.",
        objective_en="Build a 3-step warm-up that prevents injuries.",
    ),
    story(
        "sport-lesson-breathing", "lesson",
        "Respirare meglio quando corri",
        "Breathe better when you run",
        "Il respiro giusto rende la corsa più efficiente e meno faticosa. Impariamo a gestirlo.",
        "The right breathing makes running more efficient and less tiring. Let's learn to manage it.",
        ["respiro"], ["breathing"],
        "Respirare con il diaframma, con un ritmo regolare legato ai passi, migliora l'ossigenazione e la resistenza.",
        "Diaphragmatic breathing, in a steady rhythm tied to your steps, improves oxygenation and endurance.",
        [
            ("Respira con la pancia", "Usa il diaframma: la pancia si gonfia in inspirazione. È più efficiente del respiro corto di petto.",
             "Belly breathing", "Use the diaphragm: the belly expands on the inhale. It's more efficient than shallow chest breathing."),
            ("Trova un ritmo", "Lega il respiro ai passi, ad esempio inspira per 3 appoggi ed espira per 2. Un ritmo costante stabilizza lo sforzo.",
             "Find a rhythm", "Tie breathing to your steps, e.g. inhale for 3 footfalls and exhale for 2. A steady rhythm stabilises the effort."),
            ("Rilassa le spalle", "Spalle e mascella contratte sprecano energia. Tienile morbide: il respiro scorre meglio e corri più a lungo.",
             "Relax the shoulders", "Tense shoulders and jaw waste energy. Keep them loose: breathing flows better and you run longer."),
        ],
        objective="Applicare respiro diaframmatico e ritmo passo-respiro nella corsa.",
        objective_en="Apply diaphragmatic breathing and a step-breath rhythm while running.",
    ),
]


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    await db.categories.update_one({"id": CAT["id"]}, {"$set": CAT}, upsert=True)
    old_dt = datetime.now(timezone.utc) - timedelta(days=40)
    for s in STORIES:
        existing = await db.stories.find_one({"id": s["id"]}, {"_id": 0, "hero_image_generated": 1})
        payload = dict(s)
        payload["created_at"] = old_dt
        if existing and existing.get("hero_image_generated"):
            payload["hero_image_generated"] = existing["hero_image_generated"]
        await db.stories.update_one({"id": s["id"]}, {"$set": payload}, upsert=True)
    n = await db.stories.count_documents({"category_id": CAT["id"]})
    print(f"Seeded category '{CAT['id']}' with {n} stories")


if __name__ == "__main__":
    asyncio.run(main())
