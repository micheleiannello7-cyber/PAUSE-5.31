import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, { cancelAnimation, Easing, Extrapolation, interpolate, runOnJS, runOnUI, useAnimatedStyle, useReducedMotion, useSharedValue, withSequence, withSpring, withTiming, type SharedValue } from "react-native-reanimated";
import * as Haptics from "@/src/haptics";
import { StoryPreview } from "@/src/api";
import { makeStyles } from "@/src/theme";
import { HomeStoryCard } from "./home-story-card";
import { DeckBadges, DECK_BADGES_GAP, DECK_BADGES_H } from "./deck-badges";
import { DeckProgress, DECK_PROGRESS_H } from "./deck-progress";

/** Altezza di ciò che il mazzo mostra sotto la card (dati + indicatore): la card prende il resto. */
export const DECK_BELOW_CARD_H = DECK_BADGES_GAP + DECK_BADGES_H + DECK_PROGRESS_H;

type Props = {
  deck: StoryPreview[]; cursor: number; width: number; height: number; onChange: (index: number) => void; onOpen: (story: StoryPreview, rect?: CardRect) => void; onListen?: (story: StoryPreview) => void;
  /** Registra come misurare la card attiva (coordinate finestra): serve al ritorno dalla lettura per rientrare nella cornice reale. */
  registerActive?: (measure: (() => Promise<CardRect | null>) | null) => void;
  /** 0→1 mentre la Home "fa spazio" alla lettura: dati e indicatore sotto la card svaniscono subito (la copia in movimento li sostituisce). */
  away?: SharedValue<number>;
};
/** Cornice della card toccata, in coordinate finestra (per la transizione verso la lettura). */
export type CardRect = { x: number; y: number; width: number; height: number };

// Molla del centraggio: morbida, senza rimbalzo (smorzamento ≈ critico):
// la card rallenta dolcemente e si posa al centro invece di scattarvi sopra.
const SNAP_SPRING = { damping: 24, stiffness: 100, mass: 1, restDisplacementThreshold: 0.3, restSpeedThreshold: 0.3 };

// Linea temporale, non anello: a sinistra ci sono solo le card già fatte
// scorrere, a destra quelle ancora da vedere. Alla prima apertura nulla a sinistra.
// Il cambio card è immediato: la nuova card diventa subito "attiva" (toccabile,
// scorribile) mentre la molla finisce di centrarla. Nessuna attesa tra un gesto e l'altro.
export function HomeStoryDeck({ deck, cursor, width, height, onChange, onOpen, onListen, registerActive, away }: Props) {
  const styles = useStyles();
  const belowStyle = useAnimatedStyle(() => ({ opacity: away ? interpolate(away.value, [0, 0.12], [1, 0], Extrapolation.CLAMP) : 1 }));
  const cardWidth = width * 0.866;
  const stride = cardWidth + width * 0.021;
  const canPrev = cursor > 0;
  const canNext = cursor < deck.length - 1;
  const position = useSharedValue(0);
  const tx = useSharedValue(0);
  // Offset di tx all'inizio del trascinamento: permette di "prendere" una card
  // ancora in movimento senza salti.
  const startTx = useSharedValue(0);
  // Verso dell'ultimo scorrimento (+1 avanti, -1 indietro): serve allo zoom
  // di anticipo per sapere quale card è quella "in arrivo".
  const travel = useSharedValue(0);
  const started = useSharedValue(false);
  // Idle hint: a small sideways sway of the whole deck after 7s of inactivity.
  const nudge = useSharedValue(0);
  // Vero appena il dito si sposta: un trascinamento (anche elastico ai bordi)
  // non deve mai contare come tocco che apre la storia.
  const dragged = useSharedValue(false);
  const mounted = useRef(true);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [virtualPage, setVirtualPage] = useState(0);

  const armIdle = useCallback(() => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    if (!canNext) return;
    idleTimer.current = setTimeout(function sway() {
      if (!mounted.current) return;
      if (tx.value === 0) {
        nudge.value = withSequence(
          withTiming(-stride * 0.07, { duration: 420, easing: Easing.inOut(Easing.quad) }),
          withTiming(stride * 0.035, { duration: 360, easing: Easing.inOut(Easing.quad) }),
          withTiming(0, { duration: 480, easing: Easing.out(Easing.cubic) }),
        );
      }
      idleTimer.current = setTimeout(sway, 7000);
    }, 7000);
  }, [canNext, stride, tx, nudge]);
  const stopNudge = useCallback(() => {
    cancelAnimation(nudge);
    nudge.value = withTiming(0, { duration: 140 });
    armIdle();
  }, [nudge, armIdle]);

  useFocusEffect(useCallback(() => {
    armIdle();
    return () => {
      if (idleTimer.current) clearTimeout(idleTimer.current);
      idleTimer.current = null;
      cancelAnimation(nudge);
      nudge.value = 0;
    };
  }, [armIdle, nudge]));
  const finish = useCallback((target: number, page: number) => {
    if (!mounted.current) return;
    setVirtualPage(page);
    onChange(target);
  }, [onChange]);

  useLayoutEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; cancelAnimation(tx); };
  }, [tx]);

  // Commit immediato sul thread UI: la card vicina diventa quella centrale e
  // tx viene riallineato nello stesso frame (nessun salto visivo), poi la molla
  // finisce il centraggio. Chiamabile anche a metà di un'animazione precedente.
  const commit = useCallback((direction: number) => {
    "worklet";
    cancelAnimation(tx);
    travel.value = direction;
    position.value = position.value + direction;
    tx.value = tx.value + direction * stride;
    tx.value = withSpring(0, SNAP_SPRING);
  }, [tx, travel, position, stride]);

  const move = useCallback((direction: number) => {
    const target = cursor + direction;
    if (target < 0 || target >= deck.length) return;
    cancelAnimation(nudge);
    nudge.value = 0;
    armIdle();
    runOnUI(commit)(direction);
    finish(target, virtualPage + direction);
  }, [cursor, deck.length, virtualPage, commit, finish, nudge, armIdle]);

  const gesture = useMemo(() => Gesture.Pan().activeOffsetX([-10, 10]).failOffsetY([-18, 18])
    .onBegin(() => { dragged.value = false; runOnJS(stopNudge)(); })
    // Prende la card dov'è, anche se la molla la sta ancora centrando.
    .onStart(() => { cancelAnimation(tx); startTx.value = tx.value; started.value = true; })
    .onUpdate((event) => {
      if (Math.abs(event.translationX) > 8) dragged.value = true;
      // Oltre i bordi della linea (inizio o fine) la card resiste: elastico, non scorre.
      const blocked = (event.translationX > 0 && !canPrev) || (event.translationX < 0 && !canNext);
      if (!blocked) travel.value = event.translationX < 0 ? 1 : -1;
      tx.value = startTx.value + event.translationX * (blocked ? 0.16 : 1);
    })
    .onEnd((event) => {
      if (canNext && (event.translationX < -stride * 0.17 || event.velocityX < -450)) runOnJS(move)(1);
      else if (canPrev && (event.translationX > stride * 0.17 || event.velocityX > 450)) runOnJS(move)(-1);
      else tx.value = withSpring(0, SNAP_SPRING);
    })
    .onFinalize((_event, success) => {
      if (started.value && !success) tx.value = withSpring(0, SNAP_SPRING);
      started.value = false;
    }), [tx, startTx, started, travel, dragged, canPrev, canNext, stride, move, stopNudge]);

  const slots = [canPrev ? -1 : null, 0, canNext ? 1 : null].filter((s): s is number => s !== null);
  return (
    <View style={styles.container} testID="home-story-deck">
      <GestureDetector gesture={gesture}>
        <View collapsable={false}>
        <View testID="discover-swipe-area" style={[styles.viewport, { width, height }]} collapsable={false}
          accessibilityRole="adjustable" accessibilityValue={{ min: 1, max: deck.length, now: cursor + 1 }}
          accessibilityActions={[{ name: "increment" }, { name: "decrement" }]}
          onAccessibilityAction={({ nativeEvent }) => move(nativeEvent.actionName === "increment" ? 1 : -1)}>
          {slots.map((slot) => {
            const story = deck[cursor + slot];
            return <StoryLayer key={`${virtualPage + slot}-${story.id}`} story={story} slot={slot} page={virtualPage + slot}
              width={cardWidth} left={(width - cardWidth) / 2} stride={stride} position={position} tx={tx} nudge={nudge} travel={travel}
              register={slot === 0 ? registerActive : undefined}
              // Tocco tattile leggerissimo solo quando si sceglie una storia, mai scorrendo il mazzo.
              onOpen={(rect) => { if (dragged.value) return; Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {}); onOpen(story, rect); }}
              onListen={onListen ? () => { if (!dragged.value) onListen(story); } : undefined} />;
          })}
        </View>
        {/* Sotto la card: i tre dati della storia attuale (sfumano al cambio card). */}
        <Animated.View style={belowStyle}><DeckBadges story={deck[cursor]} width={cardWidth} /></Animated.View>
        </View>
      </GestureDetector>
      <Animated.View style={belowStyle}><DeckProgress cursor={cursor} total={deck.length} /></Animated.View>
    </View>
  );
}

function StoryLayer({ story, slot, page, width, left, stride, position, tx, nudge, travel, register, onOpen, onListen }: {
  story: StoryPreview; slot: number; page: number; width: number; left: number; stride: number;
  position: SharedValue<number>; tx: SharedValue<number>; nudge: SharedValue<number>; travel: SharedValue<number>;
  register?: (measure: (() => Promise<CardRect | null>) | null) => void; onOpen: (rect?: CardRect) => void; onListen?: () => void;
}) {
  const styles = useStyles();
  const reducedMotion = useReducedMotion();
  const layerRef = useRef<Animated.View>(null);
  // Al tocco si legge dove sta la card sullo schermo: la transizione verso la
  // lettura parte esattamente da lì. Se la misura non arriva, apertura normale.
  const open = () => {
    const node = layerRef.current;
    if (!node?.measureInWindow) { onOpen(); return; }
    node.measureInWindow((x, y, w, h) => onOpen(w > 0 && h > 0 ? { x, y, width: w, height: h } : undefined));
  };
  // Card attiva: la stessa misura, su richiesta, per il ritorno dalla lettura.
  useEffect(() => {
    if (!register) return;
    register(() => new Promise((resolve) => {
      const node = layerRef.current;
      if (!node?.measureInWindow) { resolve(null); return; }
      node.measureInWindow((x, y, w, h) => resolve(w > 0 && h > 0 ? { x, y, width: w, height: h } : null));
    }));
    return () => register(null);
  }, [register]);
  const animatedStyle = useAnimatedStyle(() => {
    const offset = page - position.value;
    const shift = tx.value / stride;
    const distance = offset + shift + nudge.value / stride;
    const side = Math.min(Math.abs(distance), 1);
    // Solo la card in arrivo anticipa lo zoom: quella che si avvicina al centro
    // nel verso dello scorrimento (il segno della distanza coincide con `travel`).
    // Il movimento idle (nudge) è escluso dal calcolo e non lo attiva.
    const d = offset + shift;
    const incoming = d !== 0 && Math.abs(d) < 1 && Math.sign(d) === travel.value;
    const progress = incoming && !reducedMotion ? 1 - Math.abs(d) : 0;
    const preview = progress * (1 - progress);
    // L'anticipo cresce subito, poi si annulla al centro (o tornando indietro).
    // Zoom orizzontale massimo 1.2%: resta nello spazio tra le card.
    return {
      opacity: Math.min(1, 1 - side * 0.48 + preview * 0.48),
      transform: [
        { translateX: distance * stride },
        { scaleX: 1 + preview * 0.048 },
        { scaleY: Math.min(1, 1 - side * 0.09 + preview * 0.09) },
      ],
    };
  });
  return (
    <Animated.View ref={layerRef} testID={`deck-layer-${slot === 0 ? "active" : slot < 0 ? "previous" : "next"}`} style={[styles.layer, { width, left }, animatedStyle]}>
      <HomeStoryCard story={story} active={slot === 0} instance={`slot-${slot}`} onOpen={open} onListen={onListen} />
    </Animated.View>
  );
}

const useStyles = makeStyles(() => ({
  container: { width: "100%" },
  viewport: { overflow: "hidden" },
  layer: { position: "absolute", top: 0, bottom: 0 },
}));