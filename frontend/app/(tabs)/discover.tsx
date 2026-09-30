import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { View, Text, ActivityIndicator, Animated as RNAnimated, LayoutChangeEvent, Platform, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";
import * as Haptics from "@/src/haptics";
import { Image } from "expo-image";
import Animated, { useAnimatedStyle, useReducedMotion, useSharedValue, withTiming } from "react-native-reanimated";
import { api, StoryPreview, hasHero, heroUrl } from "@/src/api";
import { makeStyles, useTheme, spacing, typography, radius, withAlpha } from "@/src/theme";
import { useUserId } from "@/src/session";
import { getReadingProgress, ReadingProgress } from "@/src/reading-progress";
import { getHomeOffCategories, saveHomeOffCategories } from "@/src/home-focus";
import { PauseLogo } from "@/src/components/pause-logo";
import { GradientButton } from "@/src/components/gradient-button";
import { HomeCategoryCarousel } from "@/src/components/home-category-carousel";
import { HomeExploreTile } from "@/src/components/home-controls";
import { HomeStoryDeck, CardRect, DECK_BELOW_CARD_H } from "@/src/components/home-story-deck";
import { StoryMorph, MORPH_DURATION, MORPH_EASING } from "@/src/components/story-morph";
import { useMorphHost } from "@/src/components/morph-host";
import { LimitBadge } from "@/src/components/limit-badge";
import { useLimitGate } from "@/src/hooks/use-limit-gate";
import { OnboardingToast, OnboardingNotice } from "@/src/components/onboarding-toast";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { HomeBackdrop } from "@/src/components/home-backdrop";
import { ResumeCard } from "@/src/components/resume-card";
import { MilestoneCelebration } from "@/src/components/milestone-celebration";
import { useReadingMilestone } from "@/src/milestones";
import { useI18n } from "@/src/i18n";

const DECK_BATCH = 7;
// Copertine da avere in cache prima di mostrare il mazzo (attuale + 2 a destra).
const COVERS_BEFORE_SHOW = 3;
// Nuovo lotto quando mancano così poche card alla fine della linea.
const PREFETCH_AHEAD = 3;
const COVER_WARM_TIMEOUT_MS = 2500;

// Scarica le copertine in cache (memoria+disco). Una rete lenta o un'immagine
// mancante non deve bloccare la Home: si va avanti comunque dopo il timeout.
function warmCovers(stories: StoryPreview[]): Promise<void> {
  const urls = stories.filter(hasHero).map((s) => heroUrl(s, "hero"));
  if (!urls.length) return Promise.resolve();
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, COVER_WARM_TIMEOUT_MS);
    Promise.all(urls.map((u) => Image.prefetch(u, "memory-disk").catch(() => false)))
      .then(() => { clearTimeout(timer); resolve(); });
  });
}

export default function Discover() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const qc = useQueryClient();
  const { t, lang } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const { width: windowWidth } = useWindowDimensions();
  const width = Math.min(windowWidth, 600);
  const gridPadding = width * 0.078;
  const { data: userState } = useQuery({
    queryKey: ["user", userId], queryFn: () => api.user(userId!), enabled: !!userId,
  });
  const interests = useMemo(() => userState?.interests?.filter((i) => i !== "all") ?? [], [userState?.interests]);
  // ESPLORA scelta negli argomenti: in Home niente fila di categorie, solo la tessera ESPLORA.
  const exploreMode = !!userState?.interests?.includes("all");
  // Saluto personalizzato in Home: solo il primo nome/nickname, se impostato.
  const firstName = useMemo(() => {
    const n = userState?.display_name?.trim();
    return n ? n.split(/\s+/)[0].slice(0, 18) : null;
  }, [userState?.display_name]);
  const { data: categories } = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const tileCats = useMemo(() => {
    if (exploreMode) return [];
    const all = categories ?? [];
    const mine = interests.length ? all.filter((c) => interests.includes(c.id)) : all;
    const order = ["scienza", "spazio", "tecnologia", "natura", "animali", "storia", "arte", "corpo-umano"];
    return [...(mine.length ? mine : all)].sort((a, b) => {
      const rank = (id: string) => order.includes(id) ? order.indexOf(id) : order.length;
      return rank(a.id) - rank(b.id);
    }).slice(0, 8);
  }, [categories, interests, exploreMode]);
  // Tessere spente dall'utente in Home (multi-selezione, salvata sul dispositivo).
  // Di default tutte le categorie scelte sono accese; almeno una resta sempre accesa.
  const [offCats, setOffCats] = useState<string[] | null>(null);
  useEffect(() => {
    if (!userId) return;
    getHomeOffCategories(userId).then(setOffCats);
  }, [userId]);
  const activeIds = useMemo(() => {
    const off = new Set(offCats ?? []);
    const on = tileCats.filter((c) => !off.has(c.id)).map((c) => c.id);
    return on.length ? on : tileCats.map((c) => c.id);
  }, [tileCats, offCats]);
  const allOn = activeIds.length === tileCats.length;
  const deckInterests = useMemo(() => allOn ? interests : activeIds, [allOn, interests, activeIds]);
  const interestsKey = deckInterests.join(",");
  const modesKey = [...(userState?.content_modes ?? ["stories", "lessons"])].sort().join(",");
  const ready = !!userId && !!userState && !!categories && offCats !== null;

  // Avviso breve sotto le tessere: "tieni attiva almeno una categoria".
  const [toastVisible, setToastVisible] = useState(false);
  const toastOpacity = useRef(new RNAnimated.Value(0)).current;
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showMinOneToast = useCallback(() => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
    setToastVisible(true);
    RNAnimated.timing(toastOpacity, { toValue: 1, duration: 160, useNativeDriver: Platform.OS !== "web" }).start();
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => {
      RNAnimated.timing(toastOpacity, { toValue: 0, duration: 240, useNativeDriver: Platform.OS !== "web" }).start(() => setToastVisible(false));
    }, 2200);
  }, [toastOpacity]);
  useEffect(() => () => { if (toastTimer.current) clearTimeout(toastTimer.current); }, []);

  const toggleCat = useCallback((id: string) => {
    const isOn = activeIds.includes(id);
    if (isOn && activeIds.length === 1) { showMinOneToast(); return; }
    Haptics.selectionAsync().catch(() => {});
    const currentOff = tileCats.map((c) => c.id).filter((c) => !activeIds.includes(c));
    const next = isOn ? [...currentOff, id] : currentOff.filter((c) => c !== id);
    setOffCats(next);
    if (userId) void saveHomeOffCategories(userId, next);
  }, [activeIds, tileCats, userId, showMinOneToast]);

  // Avviso ricarica: quando i crediti salgono rispetto all'ultimo valore visto
  // (anche tra un'apertura e l'altra dell'app), un toast breve in Home.
  const limit = useLimitGate();
  const [rechargeNotice, setRechargeNotice] = useState<OnboardingNotice | null>(null);
  const credits = limit?.credits;
  useEffect(() => {
    if (!userId || credits === undefined) return;
    const key = `pause.credits_seen.${userId}`;
    (async () => {
      const stored = await AsyncStorage.getItem(key);
      if (stored !== null && credits > Number(stored)) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        setRechargeNotice({ title: t.credit_back_t, body: t.credit_back_b, icon: "book-outline" });
      }
      await AsyncStorage.setItem(key, String(credits));
    })();
  }, [credits, userId]); // eslint-disable-line react-hooks/exhaustive-deps

  const [resume, setResume] = useState<ReadingProgress | null>(null);
  const showResume = !!resume && resume.progress < 0.95;
  // Ritorno dalla lettura sotto il livello di transizione: si segnala al livello
  // quando il layout della Home è definitivo (la card "riprendi" può comparire
  // e restringere il mazzo), così il rientro punta alla cornice reale della card.
  const morph = useMorphHost();
  const showResumeRef = useRef(showResume);
  showResumeRef.current = showResume;
  const resumePending = useRef(false);
  useFocusEffect(useCallback(() => {
    if (!userId) return;
    getReadingProgress(userId).then((p) => {
      const next = !!p && p.progress < 0.95;
      if (next === showResumeRef.current) { setResume(p); morph.homeSettled(); return; }
      resumePending.current = true;
      setResume(p);
    });
  }, [userId, morph.homeSettled]));
  const completedCount = userState?.completed_story_ids.length;
  const { milestone, dismiss: dismissMilestone } = useReadingMilestone(userId, completedCount);

  // Il mazzo è una linea temporale: la card aperta è la prima, le successive
  // stanno a destra e a sinistra restano SOLO quelle già fatte scorrere.
  const [deck, setDeck] = useState<StoryPreview[]>([]);
  const [cursor, setCursor] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [exhausted, setExhausted] = useState(false);
  const generation = useRef(0);
  const audienceKey = useRef<string | null>(null);
  const resetDeck = useCallback(() => {
    generation.current += 1;
    setDeck([]);
    setCursor(0);
    setLoading(false);
    setExhausted(false);
    setError(false);
  }, []);

  const loadBatch = useCallback(async (excludeIds: string[]) => {
    if (!userId) return;
    const requestGeneration = generation.current;
    setLoading(true);
    try {
      // Una sola richiesta per tutto il mazzo, poi copertine già in cache
      // prima di mostrare le card: niente immagini che compaiono in ritardo.
      const stories = await api.discoverBatch(userId, deckInterests, excludeIds, DECK_BATCH);
      if (requestGeneration !== generation.current) return;
      const fresh = stories.filter((s) => !excludeIds.includes(s.id));
      await warmCovers(fresh.slice(0, COVERS_BEFORE_SHOW));
      if (requestGeneration !== generation.current) return;
      void warmCovers(fresh.slice(COVERS_BEFORE_SHOW));
      if (fresh.length < DECK_BATCH) setExhausted(true);
      setDeck((prev) => {
        const seen = new Set(prev.map((s) => s.id));
        return [...prev, ...fresh.filter((s) => !seen.has(s.id))];
      });
      setError(false);
    } catch {
      if (requestGeneration !== generation.current) return;
      if (excludeIds.length === 0) setError(true);
      else setExhausted(true);
    } finally {
      if (requestGeneration === generation.current) setLoading(false);
    }
  }, [userId, deckInterests]);

  useEffect(() => {
    if (!ready) return;
    const currentKey = `${userId}|${interestsKey}|${modesKey}|${lang}`;
    if (audienceKey.current !== currentKey) {
      audienceKey.current = currentKey;
      resetDeck();
      return;
    }
    if (exhausted || loading || error) return;
    // Si aggiunge solo in coda (mai accanto al dito): il prossimo lotto parte
    // quando mancano poche card alla fine, così la card a destra c'è sempre.
    if (deck.length === 0 || cursor >= deck.length - PREFETCH_AHEAD) void loadBatch(deck.map((s) => s.id));
  }, [ready, userId, interestsKey, modesKey, lang, exhausted, loading, error, deck, cursor, loadBatch, resetDeck]);

  const showEmpty = deck.length === 0 && (exhausted || (error && !loading));
  // Home statica: niente scroll. Il mazzo prende tutto lo spazio che resta
  // sopra le categorie (misurato a layout); la card occupa tutto ciò che resta
  // sopra i tre dati e l'indicatore, senza tetto: si adatta allo schermo.
  const [deckAreaH, setDeckAreaH] = useState(0);
  const onDeckLayout = useCallback((e: LayoutChangeEvent) => {
    const h = Math.round(e.nativeEvent.layout.height);
    if (h > 0 && h !== deckAreaH) setDeckAreaH(h);
  }, [deckAreaH]);
  const cardHeight = Math.max(170, deckAreaH - DECK_BELOW_CARD_H - 8);
  // La card "riprendi" è comparsa/sparita e il mazzo si è ridimensionato: ora
  // la Home è stabile per il livello di ritorno (misurerà la card da qui).
  useEffect(() => {
    if (!resumePending.current) return;
    resumePending.current = false;
    morph.homeSettled();
  }, [deckAreaH, morph.homeSettled]);
  // Dalla card si parte sempre dall'introduzione (nessun salto al capitolo 1).
  // Con la cornice della card toccata parte la transizione "morph": la
  // copertina resta ferma e diventa quella del lettore, il resto della Home
  // fa spazio (logo in alto, "riprendi" e categorie in basso) e il lettore
  // entra sotto già identico. Senza cornice (o con "riduci movimento"): push normale.
  const reducedMotion = useReducedMotion();
  const making = useSharedValue(0);
  const headerAway = useAnimatedStyle(() => ({ opacity: 1 - making.value, transform: [{ translateY: -26 * making.value }] }));
  const belowAway = useAnimatedStyle(() => ({ opacity: 1 - making.value, transform: [{ translateY: 40 * making.value }] }));
  // Al ritorno gli elementi riprendono posto. Se sopra sta per partire il
  // percorso inverso (copertina che rientra nella card), è il livello a dare
  // il via (homeReturn) nello stesso istante e con lo stesso passo; se il
  // livello non partisse, dopo poco si rientra comunque.
  const morphActive = useRef(false);
  morphActive.current = morph.active;
  const returning = useRef(false);
  const homeReturnRef = morph.homeReturn;
  useEffect(() => {
    homeReturnRef.current = () => {
      returning.current = true;
      making.value = withTiming(0, { duration: MORPH_DURATION, easing: MORPH_EASING });
    };
    return () => { homeReturnRef.current = null; };
  }, [homeReturnRef, making]);
  useFocusEffect(useCallback(() => {
    returning.current = false;
    if (!morphActive.current) { making.value = withTiming(0, { duration: 320 }); return; }
    const fallback = setTimeout(() => { if (!returning.current) making.value = withTiming(0, { duration: 320 }); }, 900);
    return () => clearTimeout(fallback);
  }, [making]));
  const homeCardRef = morph.homeCard;
  const registerActive = useCallback((measure: (() => Promise<CardRect | null>) | null) => { homeCardRef.current = measure; }, [homeCardRef]);
  const openStory = useCallback((story: StoryPreview, rect?: CardRect) => {
    if (morph.active) return;
    if (!rect || reducedMotion) { router.push(`/deep-dive/${story.id}`); return; }
    const ready = qc.prefetchQuery({ queryKey: ["story", story.id], queryFn: () => api.story(story.id) });
    const frame = [rect.x, rect.y, rect.width, rect.height].map(Math.round).join(",");
    morph.show(<StoryMorph story={story} from={rect} premium={!!userState?.is_premium} ready={ready} leave={making}
      onCommit={() => router.push(`/deep-dive/${story.id}?morph=1&rect=${frame}`)} />);
  }, [router, morph, reducedMotion, qc, making, userState?.is_premium]);
  const listenStory = useCallback((story: StoryPreview) => {
    if (userState?.is_premium) router.push(`/deep-dive/${story.id}?listen=1`);
  }, [router, userState?.is_premium]);

  return (
    <View testID="home-screen" style={[styles.container, { paddingTop: insets.top }]}>
      <HomeBackdrop />
      <Animated.View style={[styles.header, { width }, headerAway]} testID="home-header">
        <PauseLogo prominent />
        <View style={styles.headerRight}>
          <LimitBadge testID="home-credits" timerOnTap />
          {firstName ? (
            <View style={styles.greeting} testID="home-greeting">
              <Text style={styles.greetingHi} numberOfLines={1}>{t.greeting},</Text>
              <Text style={styles.greetingName} numberOfLines={1} testID="home-greeting-name">{firstName}</Text>
            </View>
          ) : null}
        </View>
      </Animated.View>
      <View testID="home-content" style={[styles.content, { width }]}>
        <View style={styles.deckArea} onLayout={onDeckLayout} testID="home-deck-area">
        {showEmpty ? (
          <View testID="discover-empty" style={styles.empty}>
            <Ionicons name="checkmark-circle-outline" size={44} color={colors.success} />
            <Text testID="discover-empty-title" style={styles.emptyTitle}>{t.explored_all}</Text>
            <Text testID="discover-empty-message" style={styles.emptyText}>{t.explored_all_sub}</Text>
            <GradientButton label={t.restart} icon="refresh" onPress={resetDeck} testID="reset-skipped" style={styles.resetBtn} />
          </View>
        ) : deck[cursor] && deckAreaH > 0 ? (
          <HomeStoryDeck key={`${interestsKey}|${lang}|${generation.current}`} deck={deck} cursor={cursor} width={width} height={cardHeight} onChange={setCursor} onOpen={openStory}
            registerActive={registerActive} away={making} onListen={userState?.is_premium ? listenStory : undefined} />
        ) : (
          <View testID="discover-loading" style={styles.loading}><ActivityIndicator color={colors.brand} /></View>
        )}
        </View>
        <Animated.View style={belowAway}>
        {showResume && resume ? (
          <View style={[styles.resumeSection, { marginHorizontal: gridPadding }]}>
            <ResumeCard progress={resume} onPress={() => router.push(`/deep-dive/${resume.story.id}`)} />
          </View>
        ) : null}
        {exploreMode ? (
          <View style={[styles.catsSection, { paddingHorizontal: gridPadding }]} testID="home-categories">
            <HomeExploreTile width={width - gridPadding * 2} label={t.any_topic} sub={t.any_topic_sub} onPress={() => router.push("/(tabs)/explore")} />
          </View>
        ) : tileCats.length ? (
          <View style={styles.catsSection} testID="home-categories">
            <View style={[styles.catsHead, { paddingHorizontal: gridPadding }]}>
              <Text testID="home-categories-title" style={styles.catsTitle}>{t.your_categories}</Text>
            </View>
            <HomeCategoryCarousel
              categories={tileCats} activeIds={activeIds} onToggle={toggleCat} width={width} padding={gridPadding}
              overlay={toastVisible ? (
                <RNAnimated.View pointerEvents="none" style={[styles.toastWrap, { opacity: toastOpacity }]} testID="home-min-one-toast">
                  <View style={styles.toast}>
                    <Ionicons name="alert-circle" size={14} color={colors.error} />
                    <Text style={styles.toastText} testID="home-min-one-toast-text">{t.home_min_one_category}</Text>
                  </View>
                </RNAnimated.View>
              ) : null}
            />
          </View>
        ) : null}
        </Animated.View>
      </View>
      <MilestoneCelebration milestone={milestone} onClose={dismissMilestone} onStats={() => { dismissMilestone(); router.push("/stats"); }} />
      <OnboardingToast notice={rechargeNotice} bottom={insets.bottom + spacing.xxl} onHide={() => setRechargeNotice(null)} testID="credit-back-toast" />
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: colors.surface, alignItems: "center" },
  header: { paddingHorizontal: 12, height: 58, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  headerRight: { flexShrink: 1, flexDirection: "row", alignItems: "center", gap: spacing.md },
  greeting: { flexShrink: 1, alignItems: "flex-end" },
  greetingHi: { color: colors.onSurfaceTertiary, fontFamily: typography.bodyMedium, fontSize: 11, letterSpacing: 0.3, lineHeight: 14 },
  greetingName: { color: colors.brand, fontFamily: typography.displayBold, fontSize: 17, letterSpacing: -0.2, lineHeight: 21, maxWidth: 130 },
  content: { flex: 1, alignSelf: "center", paddingBottom: 12 },
  deckArea: { flex: 1, justifyContent: "center", minHeight: 190 },
  catsSection: {},
  catsHead: { height: 38, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  catsTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 16 },
  toastWrap: { position: "absolute", left: 0, right: 0, top: 0, bottom: 0, alignItems: "center", justifyContent: "center" },
  toast: {
    flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 12, height: 34, borderRadius: radius.md,
    backgroundColor: withAlpha(colors.surface, 0.94), borderWidth: 1, borderColor: withAlpha(colors.error, 0.55),
    boxShadow: `0px 6px 18px ${withAlpha(colors.surface, 0.6)}` as any,
  },
  toastText: { color: colors.onSurface, fontFamily: typography.bodyMedium, fontSize: 12 },
  resumeSection: { marginTop: 10 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
  pressed: { opacity: 0.92 },
  empty: { flex: 1, alignItems: "center", justifyContent: "center", paddingVertical: 48, gap: spacing.md },
  emptyTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 18 },
  emptyText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 20, paddingHorizontal: spacing.lg },
  resetBtn: { alignSelf: "stretch", marginTop: spacing.sm },
}));