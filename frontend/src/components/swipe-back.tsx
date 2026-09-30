// PAUSE — ritorno alla Home dal lettore con uno swipe che parte dal bordo
// sinistro o destro dello schermo. La schermata di lettura NON si muove mai in
// orizzontale (solo scroll verticale): il gesto, appena è chiaramente uno swipe
// dal bordo verso l'interno, fa scattare il ritorno — di norma la transizione
// inversa verso la card della Home (onRelease), altrimenti il back normale.
// Il tasto indietro di sistema (Android) resta gestito dal navigatore.
import { ReactNode, useRef } from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { runOnJS, useSharedValue } from "react-native-reanimated";

const EDGE = 48;
// Spostamento del dito oltre il quale il gesto è un "indietro" e scatta subito
// (senza aspettare il rilascio); al rilascio basta meno, o una spinta decisa.
const TRIGGER = 56;
const RELEASE_MIN = 32;

export function SwipeBack({ children, onBack, onRelease }: {
  children: ReactNode; onBack: () => void;
  /** Allo scatto del gesto: se restituisce true il ritorno è gestito altrove
   *  (transizione verso la card della Home); altrimenti si torna indietro normalmente. */
  onRelease?: () => boolean;
}) {
  const { width } = useWindowDimensions();
  // +1 = partito dal bordo sinistro, -1 = dal bordo destro, 0 = non dal bordo.
  const dir = useSharedValue(0);
  const fired = useSharedValue(false);
  const leaving = useRef(false);

  const go = () => {
    if (leaving.current) return;
    leaving.current = true;
    if (onRelease?.()) return;
    onBack();
  };

  const pan = Gesture.Pan()
    .activeOffsetX([-12, 12])
    .failOffsetY([-14, 14])
    .onBegin((e) => {
      fired.value = false;
      dir.value = e.x <= EDGE ? 1 : e.x >= width - EDGE ? -1 : 0;
    })
    .onUpdate((e) => {
      if (dir.value === 0 || fired.value) return;
      if (Math.sign(e.translationX) === dir.value && Math.abs(e.translationX) >= TRIGGER) {
        fired.value = true;
        runOnJS(go)();
      }
    })
    .onEnd((e) => {
      if (dir.value === 0 || fired.value) return;
      const sameWay = Math.sign(e.translationX) === dir.value;
      if (sameWay && (Math.abs(e.translationX) >= RELEASE_MIN || Math.abs(e.velocityX) > 600)) {
        fired.value = true;
        runOnJS(go)();
      }
    });

  return (
    <GestureDetector gesture={pan}>
      <View style={styles.fill} testID="reader-swipe-back">{children}</View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
});
