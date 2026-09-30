import { useRef, useCallback, useEffect, useMemo, useState } from "react";
import {
  View, Text, StyleSheet, ActivityIndicator, Share, useWindowDimensions, LayoutChangeEvent, Platform, BackHandler,
} from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, {
  useSharedValue, useAnimatedScrollHandler, useAnimatedRef, useAnimatedReaction, runOnJS, interpolate, Extrapolation, withTiming, Easing, scrollTo,
} from "react-native-reanimated";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { captureRef } from "react-native-view-shot";
import * as Sharing from "expo-sharing";
import * as Haptics from "@/src/haptics";
import { Gesture, GestureDetector } from "react-native-gesture-handler";

import { api } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography, withAlpha, ThemeColors } from "@/src/theme";
import { useUserId } from "@/src/session";
import { useStoryActions } from "@/src/hooks/use-story-actions";
import { saveReadingProgress, clearReadingProgress, getReadingProgress, toStoryPreview } from "@/src/reading-progress";
import { SwipeBack } from "@/src/components/swipe-back";
import { ReaderCoverBackdrop } from "@/src/components/reader-cover-backdrop";
import { ReaderEndingBackdrop } from "@/src/components/reader-ending-backdrop";
import { ReaderAtmosphere } from "@/src/components/reader-atmosphere";
import { ReaderFrame } from "@/src/components/reader-frame";
import { ReaderIntro, readerCoverFrame } from "@/src/components/reader-intro";
import { StoryAudioProvider, AudioSheet, AudioMiniBadge, IntroListenButton } from "@/src/components/story-audio-player";
import { ReaderHeader, READER_HEADER_H } from "@/src/components/reader-header";
import { ChapterSection, ChapterTrack } from "@/src/components/reader-section";
import { ReaderEnding } from "@/src/components/reader-ending";
import { SaveConfirmToast } from "@/src/components/save-confirm-toast";
import { Screen } from "@/src/components/screen";
import { StoryShareCard, SHARE_CARD_WIDTH } from "@/src/components/story-share-card";
import { useMorphHost } from "@/src/components/morph-host";
import { StoryMorph, MorphRect } from "@/src/components/story-morph";
import { useI18n } from "@/src/i18n";
import { CoachTip } from "@/src/coach-tips";

// Cornice della card Home ("x,y,w,h" nell'URL) da cui è partita la transizione.
function parseRect(value?: string): MorphRect | null {
  const n = (value ?? "").split(",").map(Number);
  return n.length === 4 && n.every((v) => Number.isFinite(v)) && n[2] > 0 && n[3] > 0 ? { x: n[0], y: n[1], width: n[2], height: n[3] } : null;
}

// Spostamento del dito (punti) oltre il quale il gesto verticale cambia sezione subito.
const STEP_TRIGGER = 28;
// Un capitolo più alto di una schermata occupa più schermate intere (vedi
// ChapterSection): si avanza di una schermata alla volta, poi al capitolo seguente.
const OVERFLOW_TOL = 24;
// Autofocus dei capitoli: scorrimento lento e morbido (deciso, non a scatti),
// così l'intestazione del capitolo che cresce dall'anticipazione si vede bene.
const SCROLL_MS = 864;
const SCROLL_EASING = Easing.inOut(Easing.cubic);

// Lettura editoriale continua: un'unica pagina verticale — grande copertina,
// titolo, tre dati, introduzione, poi i capitoli uno dopo l'altro direttamente
// sul fondo (nessuna card) e la conclusione. Le "sezioni" (0 = intro,
// 1..n = capitoli, n+1 = fine) usano la stessa scala di sempre, così il
// progresso di lettura salvato resta compatibile; la sezione corrente è quella
// che attraversa la linea di lettura (≈ un terzo della schermata dall'alto).
export default function DeepDive() {
  // `start=1` (dalla Home "Leggi la curiosità"): si apre direttamente sul
  // primo capitolo, senza l'introduzione.
  const { id, start, listen, morph, rect } = useLocalSearchParams<{ id: string; start?: string; listen?: string; morph?: string; rect?: string }>();
  const insets = useSafeAreaInsets();
  const { height: winH, width: winW } = useWindowDimensions();
  const router = useRouter();
  const navigation = useNavigation();
  const qc = useQueryClient();
  const userId = useUserId();
  // Arrivo con la transizione dalla card della Home (morph=1): la schermata è
  // entrata senza animazione nativa sotto il livello di transizione, che qui
  // viene congedato appena l'apertura è disegnata. Il ritorno indietro
  // (senza percorso inverso) resta una dissolvenza: l'opzione si imposta solo
  // quando il livello è sparito, così il ri-render del navigatore non cade
  // mai dentro l'animazione.
  const morphHost = useMorphHost();
  useEffect(() => {
    if (morph !== "1") return;
    const safety = setTimeout(morphHost.dismiss, 1800);
    return () => clearTimeout(safety);
  }, [morph, morphHost.dismiss]);
  useEffect(() => {
    if (morph === "1" && !morphHost.active) navigation.setOptions({ animation: "fade", animationDuration: 260 });
  }, [morph, morphHost.active, navigation]);
  // Arrivo con la transizione: si monta prima solo l'apertura (identica al
  // livello di transizione, quindi leggera da disegnare); capitoli e fine si
  // montano appena il livello si è dissolto, così nessun lavoro pesante cade
  // dentro l'animazione o nello scambio. Apertura diretta su un capitolo o
  // senza transizione: tutto subito.
  const [chaptersReady, setChaptersReady] = useState(morph !== "1" || start === "1");
  useEffect(() => {
    if (chaptersReady || morphHost.active) return;
    const timer = setTimeout(() => setChaptersReady(true), 40);
    return () => clearTimeout(timer);
  }, [chaptersReady, morphHost.active]);
  const completedRef = useRef<string | null>(null);
  const shareRef = useRef<View>(null);
  const startedAtRef = useRef<number>(Date.now());
  const [section, setSection] = useState(0);
  const [audioOpen, setAudioOpen] = useState(listen === "1");
  // Il badge che riapre il player compare solo dopo il primo tocco su "Ascolta".
  const [listenStarted, setListenStarted] = useState(listen === "1");
  const openAudio = () => { setListenStarted(true); setAudioOpen(true); };
  // Il progresso di lettura si salva solo dopo un vero gesto del lettore
  // (non per la posizione su cui si è aperta la storia automaticamente).
  const touchedRef = useRef(false);
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();

  const { data: story, isLoading } = useQuery({
    queryKey: ["story", id],
    queryFn: () => api.story(id!),
    enabled: !!id,
  });
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => api.user(userId!),
    enabled: !!userId,
  });
  // Prossima storia precaricata: alimenta la card "Prossima scoperta" nella
  // schermata finale e viene riusata da onNext, così l'anteprima coincide con
  // ciò che si apre davvero.
  const { data: nextStory } = useQuery({
    queryKey: ["nextStory", id, userId],
    queryFn: () => api.nextStory(id!, userId ?? undefined),
    enabled: !!story && chaptersReady,
    staleTime: 5 * 60 * 1000,
  });
  const { toggle } = useStoryActions(userId, id);
  // Banner ampio di conferma del salvataggio nella schermata finale.
  const [savedTrigger, setSavedTrigger] = useState<{ saved: boolean; n: number } | null>(null);
  const isPremium = !!user?.is_premium;
  // Rilettura: fissata al primo caricamento dell'utente (non cambia quando la
  // storia viene segnata come letta durante questa stessa lettura).
  const wasReadRef = useRef<boolean | null>(null);
  if (wasReadRef.current === null && user && id) wasReadRef.current = user.completed_story_ids.includes(id);
  const isReread = wasReadRef.current === true;

  // Sezioni: intro · una per capitolo · conclusione ("Da ricordare" + prossima storia).
  const chapterCount = story?.chapters.length ?? 0;
  const sectionCount = chapterCount + 2;
  const lastSection = sectionCount - 1;

  // --- Scroll continuo: un solo ScrollView, nessuna pagina ---
  const scrollRef = useAnimatedRef<Animated.ScrollView>();
  const scrollY = useSharedValue(0);
  const headerSolid = useSharedValue(0);
  // Il titolo grande dell'apertura si attenua mentre scorre sotto la barra.
  const headerReveal = useSharedValue(0);
  const currentSV = useSharedValue(-1);
  const headerTop = insets.top + spacing.xs;
  const headerBottom = headerTop + READER_HEADER_H;
  // Altezza reale dello ScrollView, misurata a layout.
  const [pageH, setPageH] = useState(winH);
  const pageHSV = useSharedValue(winH);
  // Grande copertina dell'apertura: a tutta larghezza dall'alto (dietro la
  // barra), sfuma in basso nell'atmosfera. Lo stesso livello fisso dietro allo
  // scroll (ReaderCoverBackdrop) ha questa geometria e resta come traccia scura.
  // Si abbassa quanto serve (misura dell'apertura) perché titolo, dati e
  // introduzione siano leggibili per intero nella prima schermata.
  const [reserveCap, setReserveCap] = useState<number | null>(null);
  const cover = readerCoverFrame(winW, pageH, reserveCap);
  const [introMeasured, setIntroMeasured] = useState(false);
  // Arrivo dalla card della Home: dopo il primo layout dell'apertura la
  // geometria è quella definitiva ed è stata disegnata → il livello di
  // transizione sopra può dissolversi. Si aspetta che resti ferma per un paio
  // di fotogrammi: la dissolvenza avviene sempre tra due schermate identiche.
  useEffect(() => {
    if (morph !== "1" || !introMeasured) return;
    const timer = setTimeout(morphHost.markReady, 32);
    return () => clearTimeout(timer);
  }, [morph, introMeasured, cover.height, morphHost.markReady]);
  // Quota (nello scroll) del titolo grande: da qui in su la barra resta pulita.
  const bigTitleY = cover.top + cover.reserve + spacing.lg;
  const bigTitleSV = useSharedValue(bigTitleY);
  useEffect(() => { bigTitleSV.value = bigTitleY; }, [bigTitleY, bigTitleSV]);
  // Ultimo scroll programmatico (apertura su un capitolo, ripresa): solo un
  // movimento del lettore oltre quel punto conta come "gesto" per salvare.
  const autoY = useSharedValue(0);
  // Scorrimento animato controllato da noi (durata lenta e curva morbida):
  // un valore guida che, a ogni frame, posiziona lo ScrollView. Così l'autofocus
  // non usa la breve animazione nativa (troppo veloce) ma la nostra, più lenta.
  const animY = useSharedValue(0);
  useAnimatedReaction(() => animY.value, (y) => { scrollTo(scrollRef, 0, y, false); });
  const touchedSV = useSharedValue(false);
  const markTouched = () => { touchedRef.current = true; touchedSV.value = true; };

  // Inizio di ogni sezione nello scroll (capitoli, poi la fine). Si ricava
  // dalle altezze (apertura + sezioni in colonna, senza spazi), non dalla
  // posizione a layout: sul web `onLayout` scatta solo quando cambia la
  // dimensione, quindi la posizione delle sezioni seguenti resterebbe vecchia
  // quando un capitolo cresce (es. quando si misura la sua anticipazione).
  const topsRef = useRef<number[]>([]);
  const topsSV = useSharedValue<number[]>([]);
  const endTopSV = useSharedValue(0);
  const introHRef = useRef(0);
  const heightsRef = useRef<number[]>([]);
  const pendingSection = useRef<{ index: number; animated: boolean } | null>(null);
  const lastJumpRef = useRef(0);
  const jumpTo = useCallback((index: number, animated: boolean) => {
    const tops = topsRef.current;
    const target = index <= 0 ? 0 : index > tops.length ? -1 : Math.max(0, tops[index - 1] - headerBottom + spacing.sm);
    if (target < 0 || !Number.isFinite(target)) return false;
    lastJumpRef.current = index;
    autoY.value = target;
    if (animated) animY.value = withTiming(target, { duration: SCROLL_MS, easing: SCROLL_EASING });
    else { animY.value = target; scrollRef.current?.scrollTo({ y: target, animated: false }); }
    return true;
  }, [headerBottom, scrollRef, autoY, animY]);
  const coverTopRef = useRef(cover.top);
  coverTopRef.current = cover.top;
  const recomputeTops = useCallback(() => {
    if (introHRef.current <= 0) return;
    const heights = heightsRef.current;
    const tops: number[] = [];
    let y = coverTopRef.current + introHRef.current;
    // Solo le sezioni consecutive già misurate: dopo un buco la quota non è nota.
    for (let i = 0; i < heights.length && heights[i] > 0; i++) { tops.push(Math.round(y)); y += heights[i]; }
    const prev = topsRef.current;
    if (tops.length === prev.length && tops.every((v, i) => v === prev[i])) return;
    topsRef.current = tops;
    topsSV.value = tops;
    if (tops.length > chapterCount) endTopSV.value = Math.max(0, tops[chapterCount] - headerBottom);
    const pending = pendingSection.current;
    if (pending && pending.index <= tops.length && jumpTo(pending.index, pending.animated)) pendingSection.current = null;
    // Le quote sono cambiate prima di ogni gesto del lettore (es. capitolo che
    // cresce dopo la misura): la pagina resta allineata alla sezione di apertura.
    else if (!pending && !touchedRef.current && lastJumpRef.current > 0) jumpTo(lastJumpRef.current, false);
  }, [chapterCount, headerBottom, topsSV, endTopSV, jumpTo]);
  const onIntroLayout = (h: number) => {
    setIntroMeasured(true);
    if (h !== introHRef.current) { introHRef.current = h; recomputeTops(); }
  };
  const onSectionLayout = (index: number, e: LayoutChangeEvent) => {
    const h = Math.round(e.nativeEvent.layout.height);
    if (heightsRef.current[index] === h) return;
    const heights = heightsRef.current.slice();
    heights[index] = h;
    heightsRef.current = heights;
    recomputeTops();
  };
  useEffect(() => { recomputeTops(); }, [cover.top, recomputeTops]);
  const scrollToSection = useCallback((i: number, animated = true) => {
    if (!jumpTo(i, animated)) pendingSection.current = { index: i, animated };
  }, [jumpTo]);
  // Quote per l'intestazione dei capitoli, che nasce come anticipazione in fondo
  // alla schermata precedente e si posa al suo posto seguendo lo scroll.
  const chapterTrack = useMemo<ChapterTrack>(() => ({ scrollY, tops: topsSV, pageH: pageHSV, headerBottom }), [scrollY, topsSV, pageHSV, headerBottom]);

  // Lettura a capitoli: lo scorrimento libero è disattivato. Ogni gesto
  // verticale porta esattamente alla sezione successiva o precedente
  // (apertura, capitoli, fine), allineata sotto la barra — e scatta appena il
  // dito si è mosso abbastanza da rendere chiara l'intenzione, senza aspettare
  // il rilascio. Se una sezione è più alta della schermata, si avanza prima
  // di una schermata parziale, poi al capitolo seguente.
  const pageHRef = useRef(winH);
  const maxYRef = useRef(0);
  // Capitoli su più schermate: la schermata seguente riprende la precedente di
  // barra + una riga, così nessuna riga resta nascosta sotto la barra.
  const pageOverlap = headerBottom + spacing.lg;
  const step = useCallback((dir: 1 | -1) => {
    const maxY = maxYRef.current;
    const clampY = (v: number) => (maxY > 0 ? Math.min(v, maxY) : v);
    const viewH = pageHRef.current - headerBottom;
    const targets = [0, ...topsRef.current.filter((t) => t > 0).map((t) => clampY(Math.max(0, t - headerBottom + spacing.sm)))];
    const y = clampY(autoY.value);
    let target: number | undefined;
    if (dir > 0) {
      const next = targets.find((t) => t > y + 4);
      if (next === undefined) return;
      // L'apertura è sempre una schermata sola: da lì si va dritti al capitolo 1.
      target = y < targets[1] || next - y <= viewH + OVERFLOW_TOL ? next : y + viewH - pageOverlap;
    } else {
      const prev = [...targets].reverse().find((t) => t < y - 4);
      if (prev === undefined) return;
      target = prev === 0 || y - prev <= viewH + OVERFLOW_TOL ? prev : y - (viewH - pageOverlap);
    }
    target = clampY(Math.max(0, target));
    if (Math.abs(target - y) < 1) return;
    markTouched();
    autoY.value = target;
    animY.value = withTiming(target, { duration: SCROLL_MS, easing: SCROLL_EASING });
    if (Platform.OS !== "web") Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [headerBottom, pageOverlap, scrollRef, autoY]);
  const stepRef = useRef(step);
  stepRef.current = step;
  // Gesto verticale: scatta a STEP_TRIGGER punti di spostamento (o al
  // rilascio con una spinta decisa). Uno spostamento orizzontale lo fa
  // fallire, così lo swipe dal bordo per tornare indietro resta libero.
  const stepFired = useSharedValue(false);
  const pagePan = Gesture.Pan()
    .activeOffsetY([-6, 6])
    .failOffsetX([-18, 18])
    .onBegin(() => { stepFired.value = false; })
    .onUpdate((e) => {
      if (stepFired.value || Math.abs(e.translationY) < STEP_TRIGGER) return;
      stepFired.value = true;
      runOnJS(step)(e.translationY < 0 ? 1 : -1);
    })
    .onEnd((e) => {
      if (stepFired.value) return;
      if (Math.abs(e.translationY) >= 12 || Math.abs(e.velocityY) > 300) {
        stepFired.value = true;
        runOnJS(step)((e.translationY !== 0 ? e.translationY : -e.velocityY) < 0 ? 1 : -1);
      }
    });
  // Web con mouse: la rotellina avanza/arretra di un capitolo per "colpo".
  // Lo "scroll anchoring" del browser viene spento: quando una sezione cambia
  // altezza dopo la misura, Chrome sposterebbe la pagina di qualche riga da solo.
  const wrapRef = useRef<View>(null);
  useEffect(() => {
    if (Platform.OS !== "web") return;
    const scrollNode = (scrollRef.current as unknown as { getScrollableNode?: () => HTMLElement } | null)?.getScrollableNode?.();
    if (scrollNode?.style) scrollNode.style.overflowAnchor = "none";
    const node = wrapRef.current as unknown as HTMLElement | null;
    if (!node?.addEventListener) return;
    let acc = 0, lockUntil = 0;
    let reset: ReturnType<typeof setTimeout> | null = null;
    const onWheel = (ev: WheelEvent) => {
      ev.preventDefault();
      const now = Date.now();
      if (now < lockUntil) return;
      acc += ev.deltaY;
      if (reset) clearTimeout(reset);
      reset = setTimeout(() => { acc = 0; }, 160);
      if (Math.abs(acc) >= 40) {
        stepRef.current(acc > 0 ? 1 : -1);
        acc = 0;
        lockUntil = now + 760;
      }
    };
    node.addEventListener("wheel", onWheel, { passive: false });
    return () => { node.removeEventListener("wheel", onWheel); if (reset) clearTimeout(reset); };
    // Il contenitore esiste solo quando la storia è caricata.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [!!story]);

  const onScroll = useAnimatedScrollHandler({
    onScroll: (e) => {
      const y = e.contentOffset.y;
      scrollY.value = y;
      // Titolo grande sotto la barra → si attenua; la barra diventa vetro quando la copertina è quasi uscita.
      const titleTop = bigTitleSV.value - headerBottom;
      headerReveal.value = interpolate(y, [titleTop - 40, titleTop + 48], [0, 1], Extrapolation.CLAMP);
      headerSolid.value = interpolate(y, [cover.height * 0.45, cover.height * 0.95], [0, 1], Extrapolation.CLAMP);
      // Sezione corrente: l'ultima il cui inizio ha superato la linea di lettura
      // (un terzo della schermata sotto la barra); in fondo alla pagina si è alla fine.
      const line = y + headerBottom + (pageHSV.value - headerBottom) * 0.35;
      const tops = topsSV.value;
      let idx = 0;
      for (let i = 0; i < tops.length; i++) if (tops[i] > 0 && line >= tops[i]) idx = i + 1;
      const maxY = e.contentSize.height - e.layoutMeasurement.height;
      if (maxY > 0 && y >= maxY - 2 && tops.length >= sectionCount - 1) idx = sectionCount - 1;
      idx = Math.max(0, Math.min(sectionCount - 1, idx));
      if (idx !== currentSV.value) {
        currentSV.value = idx;
        runOnJS(setSection)(idx);
      }
    },
  });

  // Se l'altezza cambia a lettura in corso (browser: barra degli indirizzi che
  // si nasconde; tastiera; rotazione) le schermate si ridisegnano con la nuova
  // misura e la pagina si riallinea al capitolo corrente.
  const sectionRef = useRef(0);
  sectionRef.current = section;
  const layoutSeen = useRef(false);
  const onScrollLayout = (e: LayoutChangeEvent) => {
    const h = Math.round(e.nativeEvent.layout.height);
    if (h > 0 && h !== pageHRef.current) {
      const resnap = layoutSeen.current && sectionRef.current > 0;
      setPageH(h); pageHSV.value = h; pageHRef.current = h;
      if (resnap) requestAnimationFrame(() => scrollToSection(sectionRef.current, false));
    }
    layoutSeen.current = true;
  };
  const onContentSizeChange = (_w: number, h: number) => { maxYRef.current = Math.max(0, h - pageHRef.current); };
  // Apertura diretta su un capitolo (`start=1`): posiziona senza animazione.
  const startedAtChapter = useRef(false);
  useEffect(() => {
    if (start === "1" && story && !startedAtChapter.current) {
      startedAtChapter.current = true;
      requestAnimationFrame(() => scrollToSection(1, false));
    }
  }, [start, story, scrollToSection]);

  // Riprende dalla sezione in cui il lettore aveva lasciato questa storia.
  useEffect(() => {
    if (!userId || !id || !story) return;
    getReadingProgress(userId).then((p) => {
      if (p && p.story.id === id && p.page > 0 && p.page < lastSection) {
        setSection(p.page);
        requestAnimationFrame(() => scrollToSection(p.page, false));
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, id, !!story]);

  // Mark as completed once: when the reader reaches the end (or taps "next").
  // Nota: "completata" qui vale per crediti e statistiche (scatta dopo 5 s sul
  // capitolo 1); il segnalibro "riprendi" resta finché non si arriva in fondo.
  const markComplete = useCallback(async () => {
    if (!userId || !id || completedRef.current === id) return;
    completedRef.current = id;
    try {
      const secs = Math.round((Date.now() - startedAtRef.current) / 1000);
      await api.complete(userId, id, story?.deep_dive_time_min ?? 2, secs);
      qc.invalidateQueries({ queryKey: ["user"] });
      qc.invalidateQueries({ queryKey: ["limit"] });
    } catch {}
  }, [userId, id, story?.deep_dive_time_min, qc]);

  // A story consumes one credit only once the reader reaches chapter 1 and
  // stays there (or further) for 5 seconds: browsing the cover/intro or backing
  // out quickly costs nothing. Returning to the intro within 5 s cancels it.
  const markCompleteRef = useRef(markComplete);
  markCompleteRef.current = markComplete;
  const inChapters = section >= 1;
  useEffect(() => {
    if (!userId || !id || !inChapters) return;
    const timer = setTimeout(() => markCompleteRef.current(), 5000);
    return () => clearTimeout(timer);
  }, [userId, id, inChapters]);

  // Narration is resolved lazily by the audio player (status → persistent
  // URL); nothing is generated until the listener taps play.

  useEffect(() => {
    if (!story) return;
    const ratio = lastSection > 0 ? section / lastSection : 0;
    if (section >= lastSection) {
      if (userId) clearReadingProgress(userId);
      markComplete();
      return;
    }
    // Remember genuine mid-read positions only (skip the intro).
    if (userId && section > 0 && touchedRef.current) {
      saveReadingProgress(userId, { story: toStoryPreview(story), page: section, progress: ratio, updatedAt: Date.now() });
    }
  }, [section, story, lastSection, userId, id, markComplete]);

  // Tasto indietro di sistema (Android): stesso percorso inverso della card,
  // quando possibile (vedi morphBack più sotto). Hook prima del ritorno anticipato.
  const morphBackRef = useRef<(x: number) => boolean>(() => false);
  useEffect(() => {
    if (Platform.OS !== "android" || morph !== "1") return;
    const sub = BackHandler.addEventListener("hardwareBackPress", () => morphBackRef.current(0));
    return () => sub.remove();
  }, [morph]);

  if (isLoading || !story) {
    return (
      <View style={[styles.container, { justifyContent: "center", alignItems: "center" }]}>
        <ActivityIndicator color={colors.brand} />
      </View>
    );
  }

  const bookmarked = user?.bookmarked_story_ids.includes(story.id) ?? false;
  const liked = user?.liked_story_ids.includes(story.id) ?? false;

  const onNext = async () => {
    await markComplete();
    try {
      // Crediti esauriti → schermata di pausa con il countdown alla prossima storia.
      if (userId) {
        const limit = await api.limitCheck(userId);
        if (limit.blocked) {
          router.replace("/pause-limit");
          return;
        }
      }
      const next = nextStory ?? (await api.nextStory(story.id, userId ?? undefined));
      router.replace(`/deep-dive/${next.id}`);
    } catch {}
  };

  // Share a ready-made image card (cover + title + hook + brand). Falls back
  // to a plain text share where image sharing isn't available (e.g. web).
  const onShare = async () => {
    try {
      if (shareRef.current && (await Sharing.isAvailableAsync())) {
        const uri = await captureRef(shareRef, { format: "png", quality: 1, result: "tmpfile" });
        await Sharing.shareAsync(uri, { dialogTitle: t.share, mimeType: "image/png", UTI: "public.png" });
        return;
      }
    } catch {}
    Share.share({ message: `${story.title} — ${t.share_suffix}` }).catch(() => {});
  };

  const goBack = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/discover"));
  // Ritorno dal lettore (arrivati con la transizione dalla card): la schermata
  // "rientra" nella card della Home con il percorso inverso. Se si è già
  // scorso (anche di poco), il livello (apertura) compare prima in dissolvenza
  // sopra la pagina, poi rientra. Senza cornice: ritorno di sempre.
  const backRect = parseRect(rect);
  const morphBack = (x: number) => {
    if (morph !== "1" || !backRect || morphHost.active || !router.canGoBack()) return false;
    navigation.setOptions({ animation: "none" });
    morphHost.show(<StoryMorph direction="close" story={story} from={backRect} premium={isPremium} offsetX={x} fadeIn={scrollY.value > 8} onCommit={() => router.back()} />);
    return true;
  };
  morphBackRef.current = morphBack;
  const onBackPress = () => { if (!morphBack(0)) goBack(); };

  return (
    <Screen style={styles.container} animated={morph !== "1"}>
      <SwipeBack onBack={goBack} onRelease={morphBack}>
      {/* Atmosfera: fondo notte + traccia sfocata della copertina che si attenua nei capitoli. */}
      <ReaderAtmosphere scrollY={scrollY} fadeOver={pageH * 0.9} />
      {/* Grande copertina dell'apertura: sale appena e resta una traccia scura con lo scroll. */}
      <ReaderCoverBackdrop story={story} scrollY={scrollY} frame={cover} instant={morph === "1"} />
      {/* Schermata finale: sfondo cinematico dell'onboarding, compare solo in fondo. */}
      {chaptersReady ? <ReaderEndingBackdrop scrollY={scrollY} pageH={pageHSV} endTop={endTopSV} /> : null}
      <StoryAudioProvider key={story.id} storyId={story.id} autoplay={listen === "1" && isPremium}>
        <ReaderHeader
          topInset={headerTop}
          title={story.title}
          highlight={story.highlight_words}
          current={section}
          total={chapterCount}
          solid={headerSolid}
          onBack={onBackPress}
          corner={isPremium && listenStarted && !audioOpen ? <AudioMiniBadge visible onPress={() => setAudioOpen(true)} /> : null}
        />

        <GestureDetector gesture={pagePan}>
        <View ref={wrapRef} collapsable={false} style={styles.scroll}>
        <Animated.ScrollView
          ref={scrollRef}
          onScroll={onScroll}
          scrollEventThrottle={16}
          scrollEnabled={false}
          onLayout={onScrollLayout}
          onContentSizeChange={onContentSizeChange}
          contentContainerStyle={{ paddingTop: cover.top }}
          showsVerticalScrollIndicator={false}
          style={styles.scroll}
          testID="deep-dive-scroll"
        >
          {/* Apertura (sezione 0): spazio per la copertina (l'immagine vera è il
              livello fisso dietro), titolo, tre dati, introduzione e l'invito a
              scorrere in fondo alla prima schermata. */}
          <ReaderIntro story={story} coverH={cover.reserve} minHeight={pageH - cover.top} bottomInset={insets.bottom} reveal={headerReveal}
            listen={isPremium ? <IntroListenButton onListen={openAudio} style={styles.listen} /> : null}
            onLayout={onIntroLayout} onFit={setReserveCap} />

          {chaptersReady ? story.chapters.map((c, i) => (
            <View key={c.number} onLayout={(e) => onSectionLayout(i, e)} testID={`deep-dive-page-chapter-${c.number}`}>
              <ChapterSection chapter={c} story={story} eyebrow={t.chapter} next={story.chapters[i + 1] ?? null} minHeight={pageH - headerBottom} pageOverlap={pageOverlap}
                index={i} track={chapterTrack} />
            </View>
          )) : null}

          {chaptersReady ? <View onLayout={(e) => onSectionLayout(chapterCount, e)} style={[styles.ending, { minHeight: pageH - headerBottom }]} testID="deep-dive-page-end">
            <ReaderEnding
              story={story}
              next={nextStory}
              liked={liked}
              onLike={() => toggle("like")}
              bookmarked={bookmarked}
              onBookmark={() => toggle("bookmark")}
              onShare={onShare}
              onNext={onNext}
              onHome={onBackPress}
              bottomInset={insets.bottom}
              onSaved={(saved) => setSavedTrigger((p) => ({ saved, n: (p?.n ?? 0) + 1 }))}
              scrollY={scrollY}
              pageH={pageHSV}
              endTop={endTopSV}
            />
          </View> : null}
        </Animated.ScrollView>
        </View>
        </GestureDetector>

        {section === 1 ? (
          <CoachTip id="reader" text={t.tip_reader} icon="book-outline" style={{ top: headerBottom + spacing.md }} />
        ) : null}
        {/* Etichetta statica (nessuna animazione d'ingresso/uscita) e montata solo
            dopo lo scambio con il livello di transizione: nessun lavoro extra
            nella coda della transizione Home → lettura. */}
        {isReread && section === 0 && chaptersReady ? (
          <View pointerEvents="none" style={[styles.rereadWrap, { top: headerBottom + spacing.md }]} testID="reader-reread-label">
            <View style={styles.rereadPill}>
              <Ionicons name="refresh-outline" size={13} color={colors.success} />
              <Text style={styles.rereadText}>{t.reader_reread}</Text>
            </View>
          </View>
        ) : null}
        {isPremium ? <AudioSheet visible={audioOpen} onClose={() => setAudioOpen(false)} /> : null}
      </StoryAudioProvider>
      </SwipeBack>
      {/* Cornice luminosa nel colore del tema, lungo i bordi dello schermo. */}
      <ReaderFrame />
      {/* Conferma ampia del salvataggio: banner fisso, centrato in basso. */}
      <SaveConfirmToast trigger={savedTrigger} bottomInset={insets.bottom} />
      {/* Off-screen share card, captured as PNG on demand. */}
      {chaptersReady ? (
        <View style={styles.shareHidden}>
          <View ref={shareRef} collapsable={false}>
            <StoryShareCard story={story} />
          </View>
        </View>
      ) : null}
    </Screen>
  );
}

const useStyles = makeStyles((colors: ThemeColors) => ({
  container: { flex: 1, backgroundColor: colors.surface },
  scroll: { flex: 1 },
  rereadWrap: { position: "absolute", left: 0, right: 0, alignItems: "center", zIndex: 5 },
  rereadPill: {
    flexDirection: "row", alignItems: "center", gap: 6, height: 30, paddingHorizontal: 12, borderRadius: radius.pill,
    backgroundColor: colors.overlay, borderWidth: 1, borderColor: withAlpha(colors.success, 0.5),
  },
  rereadText: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 11.5 },
  shareHidden: { position: "absolute", left: -4000, top: 0, width: SHARE_CARD_WIDTH, pointerEvents: "none" },
  listen: { alignSelf: "flex-start", minWidth: 180 },
  ending: { paddingTop: spacing.sm, flexDirection: "column" },
}));
