// PAUSE — transizione card Home ↔ lettura, versione "copertina che respira".
// Copertina, titolo e dati condividono un unico progresso. Le due impaginazioni
// del titolo seguono la stessa traiettoria con opacità complementari. Tutte le
// misure avvengono PRIMA di mostrare il livello; nel frattempo resta visibile
// la schermata reale. Il ritorno segue il percorso inverso verso la card Home.
import { useEffect, useRef, useState } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import Animated, { Easing, Extrapolation, interpolate, runOnJS, SharedValue, useAnimatedStyle, useSharedValue, withTiming } from "react-native-reanimated";

import { StoryPreview } from "@/src/api";
import { makeStyles, typography, useTheme, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { StoryHero } from "./story-hero";
import { DECK_BADGES_GAP, DECK_BADGES_H } from "./deck-badges";
import { StoryInfoGrid } from "./story-info-grid";
import { HighlightedTitle } from "./highlighted-title";
import { ReaderIntro, CoverTitle, IntroRect, introRects, readerCoverFrame } from "./reader-intro";
import { MorphSharedElement } from "./morph-shared-element";
import { IntroCtaButton } from "./intro-cta-button";
import { ReaderAtmosphere } from "./reader-atmosphere";
import { ReaderFrame } from "./reader-frame";
import { CoverNightSkin, CoverSeam } from "./reader-cover-backdrop";
import { useMorphHost } from "./morph-host";

export type MorphRect = IntroRect;

export const MORPH_DURATION = 680;
// Accelerazione e decelerazione simmetriche, senza rimbalzi o lunga coda ferma.
export const MORPH_EASING = Easing.inOut(Easing.sin);
// Ritorno: attesa massima perché la Home abbia il layout definitivo.
const HOME_SETTLE_MAX_MS = 240;
// Geometria della card Home (home-story-card): bordo, padding del corpo, tasto cuffie, raggio.
const CARD_BORDER = 1, CARD_PAD = 16, LISTEN_W = 54, CARD_RADIUS = 19;
const sameRect = (a: MorphRect, b: MorphRect) =>
  Math.abs(a.x - b.x) < 0.5 && Math.abs(a.y - b.y) < 0.5 && Math.abs(a.width - b.width) < 0.5 && Math.abs(a.height - b.height) < 0.5;
const CLAMP = Extrapolation.CLAMP;
const lerp = (p: number, a: number, b: number) => { "worklet"; return a + (b - a) * p; };

// Android/iOS: i blocchi il cui contenuto non cambia durante la corsa (fondo
// notte con le luci, apertura, corpo della card, cornice) vengono rasterizzati
// una volta sola: opacità e traslazioni costano poi come un'unica immagine.
const RASTER = { renderToHardwareTextureAndroid: true, shouldRasterizeIOS: true } as const;

export function StoryMorph({ story, from: fromProp, premium, ready, onCommit, direction = "open", initialReserveCap = null, leave }: {
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
  /** Ritorno: la geometria già misurata dal lettore, senza un primo frame diverso. */
  initialReserveCap?: number | null;
  /** Apertura: valore della Home (logo, categorie) che si sposta con lo stesso passo, dallo stesso fotogramma. */
  leave?: SharedValue<number>;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  const { width: winW, height: windowH } = useWindowDimensions();
  // Altezza reale del livello (= area del lettore sotto), misurata a layout:
  // la schermata finale coincide al pixel con l'apertura del lettore.
  const [layerH, setLayerH] = useState<number | null>(null);
  const winH = layerH ?? windowH;
  const host = useMorphHost();
  const closing = direction === "close";
  const [from, setFrom] = useState(fromProp);
  const originalFrom = useRef(fromProp).current;
  const p = useSharedValue(closing ? 1 : 0);
  const still = useSharedValue(0);

  // Stessa geometria dell'apertura del lettore (stesso `onFit`).
  const [reserveCap, setReserveCap] = useState<number | null>(initialReserveCap);
  const cover = readerCoverFrame(winW, winH, reserveCap);
  const [pageMeasured, setPageMeasured] = useState(false);
  const to: MorphRect = { x: cover.left, y: cover.top, width: cover.width, height: cover.height };
  const coverShift = { x: from.x + from.width / 2 - (to.x + to.width / 2), y: from.y + from.height / 2 - (to.y + to.height / 2) };
  const coverScale = { x: from.width / to.width, y: from.height / to.height };
  const inset = CARD_BORDER + CARD_PAD;
  const cardFont = Math.min(31, Math.max(20, winW * (story.title.length > 65 ? 0.056 : 0.062)));
  const [homeTitleH, setHomeTitleH] = useState(0);
  const [titleH, setTitleH] = useState(0);
  const [gridH, setGridH] = useState(0);
  const target = introRects(winW, cover.reserve, titleH, gridH);
  const sourceTitle = { x: from.x + inset, y: from.y + from.height - inset - homeTitleH,
    width: from.width - inset * 2 - (premium ? LISTEN_W : 0), height: homeTitleH };
  const sourceGrid = { x: from.x, y: from.y + from.height + DECK_BADGES_GAP, width: from.width, height: DECK_BADGES_H };
  const textMeasured = homeTitleH > 0 && titleH > 0 && gridH > 0;

  const measured = layerH != null && pageMeasured && reserveCap != null && textMeasured;
  const [geometryReady, setGeometryReady] = useState(false);
  // React layout and UI-thread styles do not commit in the same frame. Keep
  // the entire replacement hidden until both have received the final geometry.
  useEffect(() => {
    if (!measured || geometryReady) return;
    let second = 0;
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(() => setGeometryReady(true));
    });
    return () => { cancelAnimationFrame(first); cancelAnimationFrame(second); };
  }, [measured, geometryReady, layerH, reserveCap, homeTitleH, titleH, gridH]);
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
  const { dismiss: hostDismiss, ready: readerReady } = host;
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
    if (closing || !geometryReady || started.current) return;
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
  }, [closing, geometryReady, p, leave]);
  useEffect(() => {
    if (closing || !animDone || !dataReadyRef.current) return;
    commitOpen.current();
  }, [closing, animDone, dataWake]);
  // Scambio solo quando il lettore sotto è disegnato: dissolvenza tra due schermate identiche.
  useEffect(() => {
    if (closing || !animDone || !readerReady) return;
    hostDismiss();
  }, [closing, animDone, readerReady, hostDismiss]);
  // Rete di sicurezza assoluta: mai un'app bloccata dietro al livello.
  useEffect(() => {
    const timer = setTimeout(() => {
      if (started.current) return;
      started.current = true;
      committed.current = true;
      onCommit();
      hostDismiss();
    }, 900);
    return () => clearTimeout(timer);
  }, [onCommit, hostDismiss]);

  // Chiusura: sotto si torna alla Home, si aspetta il suo layout definitivo, si
  // rilegge la cornice reale della card e tutto vi rientra — mentre la Home fa
  // rientrare logo e categorie con lo stesso passo.
  const { armHomeSettle, waitHomeSettled, homeCard: homeCardRef, homeReturn: homeReturnRef, clear: hostClear } = host;
  useEffect(() => {
    if (!closing || !geometryReady || started.current) return;
    started.current = true;
    let cancelled = false;
    const start = () => {
      if (cancelled) return;
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (cancelled) return;
        homeReturnRef.current?.();
        p.value = withTiming(0, { duration: MORPH_DURATION, easing: MORPH_EASING }, (done) => { if (done) runOnJS(hostClear)(); });
      }));
    };
    const commit = setTimeout(async () => {
      armHomeSettle();
      onCommit();
      await waitHomeSettled(HOME_SETTLE_MAX_MS);
      let fresh: MorphRect | null = null;
      try {
        fresh = (await Promise.race([homeCardRef.current?.(), new Promise<null>((resolve) => setTimeout(() => resolve(null), 120))])) ?? null;
      } catch { fresh = null; }
      if (cancelled) return;
      if (fresh && fresh.width > 0 && fresh.height > 0 && !sameRect(fresh, originalFrom)) setFrom(fresh);
      start();
    }, 0);
    const safety = setTimeout(hostClear, HOME_SETTLE_MAX_MS + MORPH_DURATION + 1500);
    return () => { cancelled = true; clearTimeout(commit); clearTimeout(safety); };
  }, [closing, geometryReady, onCommit, p, originalFrom, armHomeSettle, waitHomeSettled, homeCardRef, homeReturnRef, hostClear]);

  // --- Stili animati: solo trasformazioni e opacità ---
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
  // Corpo della card (titolo, cuffie, tre dati): segue la copertina che cresce
  // e sfuma solo quando l'apertura del lettore è già comparsa, così il titolo
  // non sparisce mai lasciando un vuoto (nessun "salta e riappare").
  const cardBody = useAnimatedStyle(() => ({ opacity: interpolate(p.value, [0, 0.35], [1, 0], CLAMP) }));
  // Apertura del lettore (titolo, dati, introduzione, invito): comincia a
  // comparire mentre il corpo della card è ancora visibile — le due dissolvenze
  // si sovrappongono e il titolo resta sempre presente durante la corsa.
  const pageStyle = useAnimatedStyle(() => ({
    opacity: interpolate(p.value, [0.3, 0.72], [0, 1], CLAMP),
  }));

  return (
    <View style={StyleSheet.absoluteFill} testID="story-morph"
      onLayout={(e) => { const h = Math.round(e.nativeEvent.layout.height); if (h > 0 && h !== layerH && !started.current) setLayerH(h); }}>
      {layerH == null ? null : <View style={[StyleSheet.absoluteFill, { opacity: geometryReady ? 1 : 0 }]} testID="story-morph-content">
      <Animated.View style={[StyleSheet.absoluteFill, bgStyle]} pointerEvents="none" {...RASTER}>
        <ReaderAtmosphere animated={false} />
      </Animated.View>
      <Animated.View style={[StyleSheet.absoluteFill, readerSkin]} pointerEvents="none"><CoverSeam top={cover.height} /></Animated.View>

      <View style={StyleSheet.absoluteFill}>
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

        {/* Il testo è SOPRA la copertina, come nel lettore vero. */}
        <Animated.View style={[styles.page, { width: winW, height: winH, paddingTop: cover.top }, pageStyle]} pointerEvents="none" {...RASTER}>
          <ReaderIntro story={story} coverH={cover.reserve} minHeight={winH - cover.top} bottomInset={insets.bottom} reveal={still} prefix="story-morph"
            ghost={textMeasured} onTitleHeight={setTitleH} onGridHeight={setGridH}
            listen={premium ? <IntroCtaButton icon="headphones" label={t.audio_listen_short} onPress={() => {}} testID="story-morph-listen" flat style={styles.introListen} /> : null}
            onLayout={() => setPageMeasured(true)} onFit={(cap) => { if (!started.current) setReserveCap(cap); }} />
        </Animated.View>
        <MorphSharedElement from={sourceTitle} to={target.title} progress={p}
          onLayout={(e) => setHomeTitleH(e.nativeEvent.layout.height)} testID="story-morph-title">
          <HighlightedTitle title={story.title} highlight={story.highlight_words} style={[styles.cardTitle, { fontSize: cardFont, lineHeight: cardFont * 1.14 }]}
            numberOfLines={4} adjustsFontSizeToFit minimumFontScale={0.8} />
        </MorphSharedElement>
        <MorphSharedElement from={sourceTitle} to={target.title} progress={p} destination testID="story-morph-reader-title">
          <CoverTitle title={story.title} highlight={story.highlight_words} reveal={still} testID="story-morph-moving-title" />
        </MorphSharedElement>
        <MorphSharedElement from={sourceGrid} to={target.grid} progress={p} testID="story-morph-badges">
          <View style={{ height: DECK_BADGES_H, justifyContent: "center" }}>
            <StoryInfoGrid story={story} minutes={story.reading_time_min} inline testID="story-morph-home-grid" />
          </View>
        </MorphSharedElement>
        <MorphSharedElement from={sourceGrid} to={target.grid} progress={p} destination testID="story-morph-reader-badges">
          <StoryInfoGrid story={story} minutes={story.deep_dive_time_min} inline testID="story-morph-moving-grid" />
        </MorphSharedElement>
        {premium ? <Animated.View style={[styles.floating, { left: from.x + from.width - inset - 44, top: from.y + from.height - inset - 44 }, cardBody]} pointerEvents="none">
          <View style={styles.listen}><Ionicons name="headset-outline" size={19} color={colors.cyan} /></View>
        </Animated.View> : null}
      </View>
      <Animated.View style={[StyleSheet.absoluteFill, bgStyle]} pointerEvents="none" {...RASTER}><ReaderFrame /></Animated.View>
      </View>}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  page: { position: "absolute", left: 0, top: 0 },
  floating: { position: "absolute" },
  cover: { position: "absolute", overflow: "hidden", backgroundColor: colors.surfaceSecondary },
  homeEdge: { borderWidth: 1, borderColor: withAlpha(colors.brand, 0.42) },
  introListen: { alignSelf: "flex-start", minWidth: 180 },
  listen: {
    width: 44, height: 44, borderRadius: 24,
    borderWidth: 1, borderColor: colors.glassBorderStrong, backgroundColor: colors.scrim, alignItems: "center", justifyContent: "center",
  },
  cardTitle: {
    color: colors.onGradient, fontFamily: typography.displayBold, letterSpacing: -0.6,
    textShadowColor: withAlpha(colors.artworkSurface, 0.85), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 6,
  },
}));
