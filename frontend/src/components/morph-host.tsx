// PAUSE — livello "ospite" sopra tutto lo stack (anche sopra la barra dei tab):
// ci vive la transizione card Home → lettura (story-morph). Chi apre la storia
// vi monta l'overlay; il lettore, appena disegnato sotto, lo congeda con una
// dissolvenza breve. Finché è attivo assorbe i tocchi (niente doppi tap).
// Per il ritorno, la Home registra qui (solo ref, nessun ri-render) come
// misurare la card attiva e segnala quando il suo layout è di nuovo stabile:
// il livello rientra nella cornice reale della card, non in quella di partenza.
import { createContext, MutableRefObject, ReactNode, useCallback, useContext, useMemo, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import Animated, { Easing, runOnJS, useAnimatedStyle, useSharedValue, withTiming } from "react-native-reanimated";

export type HostRect = { x: number; y: number; width: number; height: number };

type MorphHostCtx = {
  show: (node: ReactNode) => void; dismiss: () => void; clear: () => void; active: boolean;
  /** Il lettore sotto è disegnato e stabile: il livello può dissolversi appena finisce la sua animazione. */
  ready: boolean; markReady: () => void;
  /** Home: misura la card attiva del mazzo (coordinate finestra). */
  homeCard: MutableRefObject<(() => Promise<HostRect | null>) | null>;
  /** Home: fa rientrare logo e categorie insieme al livello che torna nella card. */
  homeReturn: MutableRefObject<(() => void) | null>;
  /** Ritorno: prima di tornare alla Home si arma l'attesa; la Home segnala quando il layout è stabile. */
  armHomeSettle: () => void; homeSettled: () => void; waitHomeSettled: (timeoutMs: number) => Promise<void>;
};

const noop = () => {};
const Ctx = createContext<MorphHostCtx>({
  show: noop, dismiss: noop, clear: noop, active: false, ready: false, markReady: noop,
  homeCard: { current: null }, homeReturn: { current: null },
  armHomeSettle: noop, homeSettled: noop, waitHomeSettled: () => Promise.resolve(),
});

export const useMorphHost = () => useContext(Ctx);

export function MorphHost({ children }: { children: ReactNode }) {
  const [node, setNode] = useState<ReactNode>(null);
  const [ready, setReady] = useState(false);
  const fade = useSharedValue(1);
  const clear = useCallback(() => setNode(null), []);
  const show = useCallback((next: ReactNode) => { fade.value = 1; setReady(false); setNode(next); }, [fade]);
  const markReady = useCallback(() => setReady(true), []);
  const dismiss = useCallback(() => {
    fade.value = withTiming(0, { duration: 150, easing: Easing.out(Easing.quad) }, (done) => { if (done) runOnJS(clear)(); });
  }, [fade, clear]);
  const homeCard = useRef<(() => Promise<HostRect | null>) | null>(null);
  const homeReturn = useRef<(() => void) | null>(null);
  const settled = useRef(true);
  const waiters = useRef<(() => void)[]>([]);
  const armHomeSettle = useCallback(() => { settled.current = false; }, []);
  const homeSettled = useCallback(() => {
    settled.current = true;
    const list = waiters.current; waiters.current = [];
    list.forEach((resolve) => resolve());
  }, []);
  const waitHomeSettled = useCallback((timeoutMs: number) => new Promise<void>((resolve) => {
    if (settled.current) { resolve(); return; }
    let done = false;
    const finish = () => { if (done) return; done = true; clearTimeout(timer); resolve(); };
    const timer = setTimeout(finish, timeoutMs);
    waiters.current.push(finish);
  }), []);
  const style = useAnimatedStyle(() => ({ opacity: fade.value }));
  const value = useMemo(() => ({
    show, dismiss, clear, active: node != null, ready, markReady, homeCard, homeReturn, armHomeSettle, homeSettled, waitHomeSettled,
  }), [show, dismiss, clear, node, ready, markReady, armHomeSettle, homeSettled, waitHomeSettled]);
  return (
    <Ctx.Provider value={value}>
      <View style={styles.fill}>
        {children}
        {node != null ? (
          <Animated.View style={[StyleSheet.absoluteFill, style]} testID="morph-host">{node}</Animated.View>
        ) : null}
      </View>
    </Ctx.Provider>
  );
}

const styles = StyleSheet.create({ fill: { flex: 1 } });
