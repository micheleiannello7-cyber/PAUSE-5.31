"""
AI image prompts per story (id -> prompt).
Used by the generation script (generate_images.py) to produce a semantically
coherent hero image via Gemini Nano Banana.

Also contains curated fallback Unsplash URLs (id -> url) with strictly topic-
relevant photography, used until AI images are generated. The one you already
noticed (Marte) is fixed here.
"""

# Prompts crafted to be SPECIFIC per story and stylistically consistent
# (dark editorial mood, magazine-quality, brand palette #00D2FF / #B200FF /
# #FF006A). Every prompt names the concrete subject to avoid off-topic outputs.

STORY_IMAGE_PROMPTS: dict[str, str] = {
    "sky-blue-sunset-orange":
        "A dramatic wide-angle photograph of a sunset horizon where the sky "
        "transitions from deep cyan-blue at the top to warm amber and orange "
        "near the horizon. Cinematic light, subtle clouds, silhouetted "
        "mountains at the bottom. Dark editorial magazine mood, ultra-high "
        "detail, 16:9.",

    "why-we-yawn":
        "Close-up portrait photograph of a person yawning, mouth open, eyes "
        "half-closed, softly lit against a dark navy background. Moody, "
        "editorial, subtle blue-magenta rim light, cinematic depth of field, "
        "16:9.",

    "black-holes-basics":
        "Astrophysical rendering of a black hole with a glowing orange "
        "accretion disk swirling around a perfectly dark center, surrounded "
        "by warped starlight and gravitational lensing. Deep space, cinematic, "
        "scientifically inspired (Interstellar-like), 16:9.",

    "mars-red":
        "The planet Mars seen from space: rusty red-orange surface with "
        "visible polar ice cap, deep atmospheric craters and Olympus Mons "
        "silhouette, black cosmos in the background, no other planets, no "
        "moons. Ultra-realistic NASA-like photography, cinematic, 16:9.",

    "how-oled-works":
        "Macro photograph of an OLED display sub-pixel matrix glowing in "
        "vivid red, green and blue on a pitch-black background. Ultra-close "
        "detail, tech editorial mood, cyan rim light, 16:9.",

    "how-wifi-works":
        "Dark abstract visualization of Wi-Fi radio waves radiating in "
        "concentric cyan and magenta ripples from a stylized router on a "
        "dark navy background. Futuristic, holographic, editorial tech mood, "
        "16:9.",

    "bees-communicate":
        "Macro photograph of honeybees on a golden honeycomb inside a hive, "
        "one bee performing the waggle dance in the center, warm amber "
        "lighting against a dark background. Ultra-detailed, National "
        "Geographic style, 16:9.",

    "octopus-brains":
        "Underwater photograph of a common octopus with tentacles unfurling "
        "against a dark deep-sea background, subtle bioluminescent cyan and "
        "magenta accents on its skin. Editorial, mysterious, ultra-detailed, "
        "16:9.",

    "why-romans-fell":
        "Cinematic wide shot of the Roman Colosseum at dusk, dramatic warm "
        "orange sunset light hitting weathered stone, deep shadows, small "
        "silhouettes at the base for scale. Editorial history-magazine mood, "
        "16:9.",

    "brain-doesnt-see":
        "Abstract artistic representation of a human brain made of glowing "
        "cyan and magenta neural connections against a deep dark navy "
        "background, with a suggestion of an eye at the front. Editorial, "
        "moody, neuroscience-inspired, 16:9.",

    "why-time-flies":
        "Long-exposure photograph of a wristwatch with light trails swirling "
        "around it against a dark background, cyan and warm-orange motion "
        "streaks suggesting the passage of time. Cinematic, editorial, 16:9.",

    "espresso-italian":
        "Overhead close-up photograph of a small ceramic espresso cup with "
        "rich hazelnut crema on top, sitting on a dark marble bar counter, "
        "warm ambient light, subtle steam rising. Editorial food-magazine "
        "mood, 16:9.",

    "why-we-sleep":
        "Cinematic photograph of a person sleeping in a soft bed, seen from "
        "above with a dark navy blanket, subtle moonlight from a window "
        "casting cool cyan-blue tones. Calm, editorial, dreamy, 16:9.",

    "aurora-borealis":
        "Wide-angle photograph of vivid green and magenta aurora borealis "
        "curtains dancing across a starry night sky over a dark snowy "
        "landscape with distant mountains. Ultra-high detail, National "
        "Geographic style, 16:9.",

    "why-yawn-cat":
        "Close-up portrait photograph of a domestic cat purring, half-closed "
        "amber eyes, relaxed pose, softly lit against a dark background, "
        "subtle cyan rim light. Editorial, warm, ultra-detailed, 16:9.",
}


# Category illustration prompts — one image per category used as chip teaser.
# Style: dark editorial, single iconic subject on off-black background, subtle
# glow in the category's accent color, minimal, magazine-cover feel. 1:1 square.
CATEGORY_IMAGE_PROMPTS: dict[str, str] = {
    "scienza":
        "Minimal editorial illustration of a glowing atom with cyan electron "
        "orbits swirling around a bright nucleus, on a deep dark navy "
        "background. Ultra-clean, magazine-cover style, square 1:1.",
    "spazio":
        "Minimal editorial illustration of a purple-magenta nebula with a "
        "small crescent planet silhouette floating in dark cosmic space, "
        "stars scattered. Ultra-clean, magazine-cover style, square 1:1.",
    "tecnologia":
        "Minimal editorial illustration of a green glowing microchip on a "
        "dark navy background, with subtle circuit traces radiating outward. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "natura":
        "Minimal editorial illustration of a single vibrant green leaf with "
        "soft neon glow on a dark navy background, dew drop reflecting. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "animali":
        "Minimal editorial illustration of a warm orange fox silhouette with "
        "a subtle glow, side profile, on a deep dark background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "storia":
        "Minimal editorial illustration of an ancient stone column capital "
        "backlit by warm amber light against a deep dark background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "psicologia":
        "Minimal editorial illustration of a stylized human head profile "
        "made of glowing magenta neural threads on a dark navy background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "corpo-umano":
        "Minimal editorial illustration of a glowing pink anatomical heart "
        "with delicate vessels radiating outward on a deep dark background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "cultura":
        "Minimal editorial illustration of a cyan glowing globe outline "
        "with faint continent shapes on a deep dark background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "curiosita":
        "Minimal editorial illustration of a glowing purple question mark "
        "surrounded by tiny stars and sparkles on a deep dark background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
    "economia":
        "Minimal editorial illustration of a glowing golden-yellow coin "
        "balanced on a rising line chart, soft neon glow, on a deep dark navy "
        "background. Ultra-clean, magazine-cover style, square 1:1.",
    "arte":
        "Minimal editorial illustration of a paintbrush leaving a luminous "
        "hot-pink brushstroke that curls into a spiral on a deep dark "
        "background. Ultra-clean, magazine-cover style, square 1:1.",
    "geografia":
        "Minimal editorial illustration of a glowing sky-blue compass rose "
        "over faint topographic contour lines on a deep dark navy background. "
        "Ultra-clean, magazine-cover style, square 1:1.",
}


# Curated topic-specific Unsplash URLs (fallback until AI images are generated).
# Every URL was picked so it clearly matches the story subject (no generic
# landscapes, no wrong planets).
STORY_IMAGE_URLS: dict[str, str] = {
    "sky-blue-sunset-orange":
        "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=1200&q=80&auto=format&fit=crop",
    "why-we-yawn":
        "https://images.unsplash.com/photo-1580281657527-47f249e8f4df?w=1200&q=80&auto=format&fit=crop",
    "black-holes-basics":
        "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1200&q=80&auto=format&fit=crop",
    "mars-red":
        "https://images.unsplash.com/photo-1630839437035-dac17da580d0?w=1200&q=80&auto=format&fit=crop",
    "how-oled-works":
        "https://images.unsplash.com/photo-1601944179066-29786cb9d32a?w=1200&q=80&auto=format&fit=crop",
    "how-wifi-works":
        "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=1200&q=80&auto=format&fit=crop",
    "bees-communicate":
        "https://images.unsplash.com/photo-1568526381923-caf3fd520382?w=1200&q=80&auto=format&fit=crop",
    "octopus-brains":
        "https://images.unsplash.com/photo-1524704654690-b56c05c78a00?w=1200&q=80&auto=format&fit=crop",
    "why-romans-fell":
        "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1200&q=80&auto=format&fit=crop",
    "brain-doesnt-see":
        "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=1200&q=80&auto=format&fit=crop",
    "why-time-flies":
        "https://images.unsplash.com/photo-1495364141860-b0d03eccd065?w=1200&q=80&auto=format&fit=crop",
    "espresso-italian":
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=1200&q=80&auto=format&fit=crop",
    "why-we-sleep":
        "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=1200&q=80&auto=format&fit=crop",
    "aurora-borealis":
        "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1200&q=80&auto=format&fit=crop",
    "why-yawn-cat":
        "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=1200&q=80&auto=format&fit=crop",
}


# Mini-lesson cover prompts (id -> prompt). Dark, editorial, conceptual imagery
# that represents the ONE idea of the lesson. No text, no letters, no close-up
# faces. Vertical 3:4, moody premium lighting, brand palette accents.
LESSON_IMAGE_PROMPTS: dict[str, str] = {
    # --- scienza (parte A) ---
    "lez-metodo-scientifico":
        "A dark editorial still life of a small seedling in a glass beaker on a lab bench, a magnifying glass and a handwritten notebook beside it, moody cyan rim light, deep shadows, no text. Vertical 3:4.",
    "lez-energia-conservazione":
        "A cinematic photograph of a swinging pendulum with glowing motion trails against a pitch-black background, warm-to-cyan light gradient suggesting energy transformation, no text. Vertical 3:4.",
    "lez-orientarsi-stelle":
        "A dark night-sky photograph with the Big Dipper and Polaris highlighted, a faint silhouette of a person looking up from a hilltop, deep blue tones, no text. Vertical 3:4.",
    "lez-orbite-gravita":
        "A conceptual dark render of a curved spacetime grid with a bright planet orbiting a glowing star, subtle magenta and cyan light, cosmic background, no text. Vertical 3:4.",
    # --- tecnologia (parte A) ---
    "lez-password-sicura":
        "A moody macro photograph of a glowing padlock made of light over a dark keyboard, cyan and magenta reflections, cinematic security mood, no text. Vertical 3:4.",
    "lez-algoritmo":
        "A dark editorial flat-lay of interlocking gears and a flowchart of glowing nodes and arrows on a deep navy background, green accent light, no text. Vertical 3:4.",
    # --- natura (parte A) ---
    "lez-ciclo-acqua":
        "A cinematic landscape of evaporation and rain over a dark lake, sun rays and mist rising, water droplets and clouds forming a cycle, cool tones, no text. Vertical 3:4.",
    "lez-leggere-nuvole":
        "A dramatic sky photograph with layered cloud types, from wispy cirrus high up to towering cumulus, moody light before a storm, deep contrast, no text. Vertical 3:4.",
    # --- animali (parte A) ---
    "lez-classificare-animali":
        "A dark natural-history museum aesthetic: silhouettes of diverse animals arranged like a branching tree of life, warm amber spotlight, deep shadows, no text. Vertical 3:4.",
    "lez-ecolocalizzazione":
        "A dark underwater and cave scene showing a bat and a dolphin emitting glowing concentric sound waves, cyan ripples in blackness, cinematic, no text. Vertical 3:4.",
    # --- storia (parte A) ---
    "lez-linea-del-tempo":
        "A dark editorial concept of an illuminated horizontal timeline with glowing milestone dots receding into depth, warm amber light, deep shadows, no text. Vertical 3:4.",
    "lez-valutare-fonte":
        "A moody still life of an old document under a magnifying glass beside a modern screen, cyan light contrasting warm parchment, investigative mood, no text. Vertical 3:4.",
    # --- psicologia (parte A) ---
    "lez-memoria-tecniche":
        "A dark surreal image of a glowing memory palace: a corridor of doors with softly lit objects, magenta neural threads weaving through, no text. Vertical 3:4.",
    "lez-bias-conferma":
        "A conceptual dark portrait-free image of two opposing arrows and a brain silhouette made of glowing threads leaning toward one side, magenta light, no text. Vertical 3:4.",
    # --- economia (parte B) ---
    "lez-interesse-composto":
        "A cinematic dark photograph of a snowball of golden coins rolling and growing down a dark slope, warm glow, exponential curve suggested by light trail, no text. Vertical 3:4.",
    "lez-inflazione":
        "A moody editorial still life of a shrinking stack of banknotes and a rising price curve of light on a dark background, warm amber and red accents, no text. Vertical 3:4.",
    # --- arte (parte B) ---
    "lez-prospettiva":
        "A dark architectural photograph of a long corridor with parallel lines converging to a single glowing vanishing point, dramatic perspective, cyan light, no text. Vertical 3:4.",
    "lez-teoria-colore":
        "A dark studio still life of a colour wheel made of glowing paint swatches and three primary paint tubes, rich saturated hues on black, no text. Vertical 3:4.",
    # --- geografia (parte B) ---
    "lez-leggere-mappa":
        "A moody flat-lay of an old topographic paper map with a brass compass and magnifying glass, warm lamp light, deep shadows, no text visible. Vertical 3:4.",
    "lez-fusi-orari":
        "A dark render of Earth from space at the day-night terminator, glowing time-zone meridians as thin cyan lines, city lights on the dark side, no text. Vertical 3:4.",
    # --- cultura (parte B) ---
    "lez-etimologia":
        "A dark editorial image of ancient carved letters and roots morphing into modern glowing words, layered like sediment, warm amber and cyan light, no readable text. Vertical 3:4.",
    "lez-calendario":
        "A conceptual dark image of the Earth orbiting a bright Sun with a faint circular calendar ring of light around the orbit, cosmic background, no text. Vertical 3:4.",
    # --- corpo umano (parte B) ---
    "lez-respirazione":
        "A dark anatomical concept image of glowing lungs and a dome-shaped diaphragm below, soft cyan breath-like light flowing in and out, deep black background, no text. Vertical 3:4.",
    "lez-febbre":
        "A moody macro image of a glowing thermometer with rising mercury against a dark background, warm red-orange heat glow, cinematic, no text. Vertical 3:4.",
    # --- curiosità (parte B) ---
    "lez-ghiaccio-galleggia":
        "A cinematic close-up of ice cubes floating in a dark glass of water, half above and half below the surface, cool blue rim light, condensation, no text. Vertical 3:4.",
    "lez-eco":
        "A dark dramatic mountain valley at dusk with a small silhouetted figure and glowing concentric sound waves bouncing off a distant rock face, cyan ripples, no text. Vertical 3:4.",
}

