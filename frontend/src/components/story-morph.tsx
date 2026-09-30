// PAUSE — transizione card Home ↔ lettura, versione "copertina che respira".
// Un solo movimento continuo: la copertina della card cresce (traslazione +
// scala, mai layout) fino alla grande copertina dell'apertura del lettore;
// il fondo notte del lettore sale sotto di lei e l'apertura (titolo, dati,
// introduzione) compare intera in dissolvenza dal basso mentre il corpo della
// card svanisce. Niente misure intermedie, niente elementi che viaggiano da
// soli: parte al primo fotogramma utile e arriva su una schermata identica al
// lettore, che si monta sotto quando la corsa è quasi conclusa e riceve il
// testimone con una dissolvenza breve. Il ritorno è lo stesso percorso,
// all'indietro, verso la cornice reale della card misurata sulla Home.
import { useEffect, useRef, useState } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import Animated, { Easing, Extrapolation, interpolate, runOnJS, SharedValue, useAnimatedStyle, useSharedValue, withTiming } from "react-native-reanimated";

import { StoryPreview } from "@/src/api";
import { makeStyles, spacing, typography, useTheme, withAlpha } from "@/src/theme";
import { StoryHero } from "./story-hero";
import { DECK_BADGES_GAP, DECK_BADGES_H } from "./deck-badges";
import { StoryInfoGrid } from "./story-info-grid";
import { HighlightedTitle } from "./highlighted-title";
import { ReaderIntro, IntroRect, readerCoverFrame } from "./reader-intro";
import { ReaderAtmosphere } from "./reader-atmosphere";
import { ReaderFrame } from "./reader-frame";
import { CoverNightSkin, CoverSeam } from "./reader-cover-backdrop";
import { useMorphHost } from "./morph-host";

export type MorphRect = IntroRect;

export const MORPH_DURATION = 680;
// Partenza decisa e atterraggio lungo e morbido (curva "emphasized" dei
// sistemi mobili): nessun rimbalzo, nessuna coda ferma.
export const MORPH_EASING = Easing.bezier(0.3, 0, 0.1, 1);
// Chiusura: il livello si dissolve sopra la card nell'ultimo tratto.
const CLOSE_FADE_MS = 150;
// Chiusura da un capitolo: prima l'apertura compare in dissolvenza, poi rientra.
const FADE_IN_MS = 220;
// Chiusura con swipe: la schermata torna dritta prima di rientrare.
const SLIDE_BACK_MS = 200;
// Ritorno: attesa massima perché la Home abbia il layout definitivo.
const HOME_SETTLE_MAX_MS = 240;
// Geometria della card Home (home-story-card): bordo, padding del corpo, tasto cuffie, raggio.
const CARD_BORDER = 1, CARD_PAD = 16, LISTEN_W = 54, CARD_RADIUS = 19;
const sameRect = (a: MorphRect, b: MorphRect) =>
  Math.abs(a.x - b.x) < 0.5 && Math.abs(a.y - b.y) < 0.5 && Math.abs(a.width - b.width) < 0.5 && Math.abs(a.height - b.height) < 0.5;
const CLAMP = Extrapolation.CLAMP;
const lerp = (p: number, a: number, b: number) => { "worklet"; return a + (b - a) * p; };

export function StoryMorph({ story, from: fromProp, premium, ready, onCommit, direction = "open", offsetX = 0, fadeIn = false, leave }: {
  story: StoryPreview;
  /** Cornice della card nella Home (coordinate finestra). */
  from: MorphRect;
  premium: boolean;
  /** Apertura: storia completa in cache, il lettore si apre solo quando c'è. */
  ready?: Promise<unknown>;
  /** Apertura: apre il lettore (già identico sotto). Chiusura: torna alla Home (sotto il livello). */
  onCommit: () => void;
  /** "close": il percorso inverso, dall'apertura del lettore alla card della Home. */
  direction?: "open" | "close";
  /** Chiusura da swipe: spostamento orizzontale al rilascio, riassorbito prima del rientro. */
  offsetX?: number;
  /** Chiusura da un capitolo: l'apertura compare in dissolvenza prima di rientrare nella card. */
  fadeIn?: boolean;
  /** Apertura: valore della Home (logo, categorie) che si sposta con lo stesso passo, dallo stesso fotogramma. */
  leave?: SharedValue<number>;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { width: winW, height: windowH } = useWindowDimensions();
  // Altezza reale del livello (= area del lettore sotto), misurata a layout:
  // la schermata finale coincide al pixel con l'apertura del lettore.
  const [layerH, setLayerH] = useState<number | null>(null);
  const winH = layerH ?? windowH;
  const host = useMorphHost();
  const closing = direction === "close";
  const [from, setFrom] = useState(fromProp);
  const p = useSharedValue(closing ? 1 : 0);
  const veil = useSharedValue(closing && fadeIn ? 0 : 1);
  const slideX = useSharedValue(offsetX);
  const still = useSharedValue(0);

  // Stessa geometria dell'apertura del lettore (stesso `onFit`).
  const [reserveCap, setReserveCap] = useState<number | null>(null);
  const cover = readerCoverFrame(winW, winH, reserveCap);
  const [pageMeasured, setPageMeasured] = useState(false);
  const to: MorphRect = { x: cover.left, y: cover.top, width: cover.width, height: cover.height };
  const coverShift = { x: from.x + from.width / 2 - (to.x + to.width / 2), y: from.y + from.height / 2 - (to.y + to.height / 2) };
  const coverScale = { x: from.width / to.width, y: from.height / to.height };
  const inset = CARD_BORDER + CARD_PAD;
  const cardFont = Math.min(31, Math.max(20, from.width * (story.title.length > 65 ? 0.056 : 0.062)));

  const measured = layerH != null && pageMeasured && reserveCap != null;
  const [animDone, setAnimDone] = useState(false);
  const dataReadyRef = useRef(!ready);
  const animDoneRef = useRef(false);
  const [dataWake, setDataWake] = useState(0);
  const started = useRef(false);
  const committed = useRef(false);
  useEffect(() => {
    if (!ready) return;
    const arrived = () => { dataReadyRef.current = true; if (animDoneRef.current) setDataWake((n) => n + 1); };
    ready.then(arrived, arrived);
  }, [ready]);
  const { dismiss: hostDismiss } = host;
  const safetyDismiss = useRef<ReturnType<typeof setTimeout> | null>(null);
  const commitOpen = useRef(() => {});
  commitOpen.current = () => {
    if (committed.current) return;
    committed.current = true;
    onCommit();
    safetyDismiss.current = setTimeout(hostDismiss, 2500);
  };
  useEffect(() => () => { if (safetyDismiss.current) clearTimeout(safetyDismiss.current); }, []);

  // Apertura: parte due fotogrammi dopo che la geometria è nota (il montaggio
  // del livello è già disegnato, niente salto iniziale) e la Home si sposta
  // nello stesso istante. Il lettore si monta solo a corsa finita: nessun
  // lavoro pesante durante l'animazione, sotto c'è già una schermata identica.
  useEffect(() => {
    if (closing || !measured || started.current) return;
    started.current = true;
    let cancelled = false;
    const finishOpen = () => { animDoneRef.current = true; setAnimDone(true); };
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (cancelled) return;
      const timing = { duration: MORPH_DURATION, easing: MORPH_EASING };
      if (leave) leave.value = withTiming(1, timing);
      p.value = withTiming(1, timing, (done) => { if (done) runOnJS(finishOpen)(); });
    }));
    return () => { cancelled = true; };
  }, [closing, measured, p, leave]);
  useEffect(() => {
    if (closing || !animDone || !dataReadyRef.current) return;
    commitOpen.current();
  }, [closing, animDone, dataWake]);
  // Scambio solo quando il lettore sotto è disegnato: dissolvenza tra due schermate identiche.
  useEffect(() => {
    if (closing || !animDone || !host.ready) return;
    host.dismiss();
  }, [closing, animDone, host.ready, host.dismiss]);
  // Rete di sicurezza assoluta: mai un'app bloccata dietro al livello.
  useEffect(() => {
    const timer = setTimeout(() => {
      if (started.current) return;
      started.current = true;
      committed.current = true;
      onCommit();
      host.dismiss();
    }, 900);
    return () => clearTimeout(timer);
  }, [onCommit, host.dismiss]);

  // Chiusura: sotto si torna alla Home, si aspetta il suo layout definitivo, si
  // rilegge la cornice reale della card e tutto vi rientra — mentre la Home fa
  // rientrare logo e categorie con lo stesso passo.
  const { armHomeSettle, waitHomeSettled, homeCard: homeCardRef, homeReturn: homeReturnRef, clear: hostClear } = host;
  useEffect(() => {
    if (!closing || !measured || started.current) return;
    started.current = true;
    const lead = fadeIn ? FADE_IN_MS : 0;
    if (fadeIn) veil.value = withTiming(1, { duration: FADE_IN_MS, easing: Easing.out(Easing.quad) });
    const slideLead = offsetX !== 0 ? Math.round(SLIDE_BACK_MS * 0.7) : 0;
    let cancelled = false;
    let fadeTimer: ReturnType<typeof setTimeout> | null = null;
    const start = () => {
      if (cancelled) return;
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (cancelled) return;
        homeReturnRef.current?.();
        p.value = withTiming(0, { duration: MORPH_DURATION, easing: MORPH_EASING }, (done) => { if (done) runOnJS(hostClear)(); });
        fadeTimer = setTimeout(hostDismiss, MORPH_DURATION - CLOSE_FADE_MS);
      }));
    };
    const commit = setTimeout(async () => {
      if (offsetX !== 0) slideX.value = withTiming(0, { duration: SLIDE_BACK_MS, easing: Easing.out(Easing.cubic) });
      armHomeSettle();
      onCommit();
      await Promise.all([waitHomeSettled(HOME_SETTLE_MAX_MS), new Promise((resolve) => setTimeout(resolve, slideLead))]);
      let fresh: MorphRect | null = null;
      try { fresh = (await homeCardRef.current?.()) ?? null; } catch { fresh = null; }
      if (cancelled) return;
      if (fresh && fresh.width > 0 && fresh.height > 0 && !sameRect(fresh, fromProp)) setFrom(fresh);
      start();
    }, lead);
    const safety = setTimeout(hostClear, lead + SLIDE_BACK_MS + HOME_SETTLE_MAX_MS + MORPH_DURATION + 1500);
    return () => { cancelled = true; clearTimeout(commit); clearTimeout(safety); if (fadeTimer) clearTimeout(fadeTimer); };
  }, [closing, measured, fadeIn, offsetX, onCommit, p, veil, slideX, fromProp, armHomeSettle, waitHomeSettled, homeCardRef, homeReturnRef, hostClear, hostDismiss]);

  // --- Stili animati: solo trasformazioni e opacità ---
  const veilStyle = useAnimatedStyle(() => ({ opacity: veil.value }));
  const slide = useAnimatedStyle(() => ({ transform: [{ translateX: slideX.value }] }));
  // Fondo notte + cornice del lettore: salgono nella prima metà della corsa.
  const bgStyle = useAnimatedStyle(() => ({ opacity: interpolate(p.value, [0, 0.55], [0, 1], CLAMP) }));
  // Copertina: cornice del lettore che all'inizio è schiacciata sulla card;
  // l'immagine dentro è contro-scalata (mai deformata) e copre sempre il ritaglio.
  const coverStyle = useAnimatedStyle(() => {
    const sx = lerp(p.value, coverScale.x, 1);
    const sy = lerp(p.value, coverScale.y, 1);
    return {
      borderRadius: lerp(p.value, CARD_RADIUS, cover.radius),
      transform: [{ translateX: coverShift.x * (1 - p.value) }, { translateY: coverShift.y * (1 - p.value) }, { scaleX: sx }, { scaleY: sy }],
    };
  });
  const coverImageStyle = useAnimatedStyle(() => {
    const sx = lerp(p.value, coverScale.x, 1);
    const sy = lerp(p.value, coverScale.y, 1);
    const u = Math.max(sx, sy);
    return { transform: [{ scaleX: u / sx }, { scaleY: u / sy }] };
  });
  const homeSkin = useAnimatedStyle(() => ({ opacity: interpolate(p.value, [0, 0.45], [1, 0], CLAMP) }));
  const readerSkin = useAnimatedStyle(() => ({ opacity: interpolate(p.value, [0.3, 0.8], [0, 1], CLAMP) }));
  // Corpo della card (titolo, cuffie, tre dati): segue la copertina e svanisce subito.
  const cardBody = useAnimatedStyle(() => ({
    opacity: interpolate(p.value, [0, 0.3], [1, 0], CLAMP),
    transform: [{ translateX: coverShift.x * (1 - p.value) - coverShift.x }, { translateY: coverShift.y * (1 - p.value) - coverShift.y }],
  }));
  // Apertura del lettore (titolo, dati, introduzione, invito): compare intera,
  // salendo di poco, nella seconda metà della corsa.
  const pageStyle = useAnimatedStyle(() => ({
    opacity: interpolate(p.value, [0.42, 0.95], [0, 1], CLAMP),
    transform: [{ translateY: interpolate(p.value, [0.42, 1], [22, 0], CLAMP) }],
  }));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, veilStyle]} testID="story-morph"
      onLayout={(e) => { const h = Math.round(e.nativeEvent.layout.height); if (h > 0 && h !== layerH && !started.current) setLayerH(h); }}>
      {layerH == null ? null : <>
      <Animated.View style={[StyleSheet.absoluteFill, bgStyle]} pointerEvents="none">
        <ReaderAtmosphere animated={false} />
      </Animated.View>
      <Animated.View style={[StyleSheet.absoluteFill, readerSkin]} pointerEvents="none"><CoverSeam top={cover.height} /></Animated.View>

      <Animated.View style={[StyleSheet.absoluteFill, slide]}>
        {/* Apertura identica al lettore: un solo blocco che compare in dissolvenza. */}
        <Animated.View style={[styles.page, { width: winW, height: winH, paddingTop: cover.top }, pageStyle]} pointerEvents="none">
          <ReaderIntro story={story} coverH={cover.reserve} minHeight={winH - cover.top} bottomInset={insets.bottom} reveal={still} prefix="story-morph"
            onLayout={() => setPageMeasured(true)} onFit={setReserveCap} />
        </Animated.View>

        {/* Copertina: dalla card alla grande copertina dell'apertura. */}
        <Animated.View style={[styles.cover, { left: to.x, top: to.y, width: to.width, height: to.height }, coverStyle]} testID="story-morph-cover">
          <Animated.View style={[StyleSheet.absoluteFill, coverImageStyle]}>
            <StoryHero story={story} style={StyleSheet.absoluteFill} iconSize={64} transition={0} />
            <Animated.View style={[StyleSheet.absoluteFill, readerSkin]}><CoverNightSkin /></Animated.View>
          </Animated.View>
          <Animated.View style={[StyleSheet.absoluteFill, homeSkin]}>
            <LinearGradient colors={[withAlpha(colors.artworkSurface, 0), withAlpha(colors.artworkSurface, 0.1), withAlpha(colors.artworkSurface, 0.86), withAlpha(colors.artworkSurface, 0.97)]}
              locations={[0, 0.42, 0.74, 1]} style={StyleSheet.absoluteFill} />
          </Animated.View>
          <Animated.View style={[StyleSheet.absoluteFill, styles.homeEdge, homeSkin]} />
        </Animated.View>

        {/* Corpo della card Home (titolo in fondo alla card, tre dati sotto): svanisce con la partenza. */}
        <Animated.View style={[styles.floating, { left: from.x, top: from.y, width: from.width }, cardBody]} pointerEvents="none" testID="story-morph-title">
          <View style={[styles.cardBody, { height: from.height, padding: inset }]}>
            <View style={{ flex: 1, marginRight: premium ? LISTEN_W : 0 }}>
              <HighlightedTitle title={story.title} highlight={story.highlight_words} style={[styles.cardTitle, { fontSize: cardFont, lineHeight: cardFont * 1.14 }]}
                numberOfLines={4} adjustsFontSizeToFit minimumFontScale={0.8} />
            </View>
            {premium ? (
              <View style={styles.listen}><Ionicons name="headset-outline" size={19} color={colors.cyan} /></View>
            ) : null}
          </View>
          <View style={{ marginTop: DECK_BADGES_GAP, height: DECK_BADGES_H, justifyContent: "center" }} testID="story-morph-badges">
            <StoryInfoGrid story={story} minutes={story.reading_time_min} inline testID="story-morph-home-grid" />
          </View>
        </Animated.View>
      </Animated.View>
      <Animated.View style={[StyleSheet.absoluteFill, bgStyle]} pointerEvents="none"><ReaderFrame /></Animated.View>
      </>}
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  page: { position: "absolute", left: 0, top: 0 },
  floating: { position: "absolute" },
  cover: { position: "absolute", overflow: "hidden", backgroundColor: colors.surfaceSecondary },
  homeEdge: { borderWidth: 1, borderColor: withAlpha(colors.brand, 0.42) },
  cardBody: { flexDirection: "row", alignItems: "flex-end" },
  listen: {
    width: 44, height: 44, borderRadius: 24,
    borderWidth: 1, borderColor: colors.glassBorderStrong, backgroundColor: colors.scrim, alignItems: "center", justifyContent: "center",
  },
  cardTitle: {
    color: colors.onGradient, fontFamily: typography.displayBold, letterSpacing: -0.6,
    textShadowColor: withAlpha(colors.artworkSurface, 0.85), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 6,
  },
}));
