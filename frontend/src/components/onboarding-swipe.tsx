// PAUSE — onboarding: scorrimento laterale tra le tre schermate. Il contenuto
// segue il dito (attenuato); oltre la soglia si chiede al genitore se si può
// procedere: se sì scivola via e cambia schermata, altrimenti rimbalza e il
// genitore mostra un messaggio (es. "scegli almeno un argomento").
import { ReactNode, useRef } from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, {
  useSharedValue, useAnimatedStyle, withTiming, withSpring, withSequence, runOnJS, Easing, interpolate, Extrapolation,
} from "react-native-reanimated";

/** 1 = avanti (swipe verso sinistra), -1 = indietro (swipe verso destra). */
export type SwipeDir = 1 | -1;

const OUT = { duration: 240, easing: Easing.out(Easing.cubic) };
const BACK = { damping: 18, stiffness: 190 };

export function OnboardingSwipe({
  children, canGo, onGo, onBlocked, testID,
}: {
  children: ReactNode;
  canGo: (dir: SwipeDir) => boolean;
  onGo: (dir: SwipeDir) => void;
  onBlocked: (dir: SwipeDir) => void;
  testID?: string;
}) {
  const { width } = useWindowDimensions();
  const x = useSharedValue(0);
  const leaving = useRef(false);

  const finish = (dir: SwipeDir, far: boolean) => {
    if (leaving.current) return;
    if (!far) { x.value = withSpring(0, BACK); return; }
    if (!canGo(dir)) {
      // Rimbalzo: piccolo scatto nella direzione tentata, poi rientro a molla.
      x.value = withSequence(withTiming(-dir * 22, { duration: 90 }), withSpring(0, { damping: 12, stiffness: 240 }));
      onBlocked(dir);
      return;
    }
    leaving.current = true;
    x.value = withTiming(-dir * width * 0.55, OUT, (done) => {
      if (done) runOnJS(onGo)(dir);
    });
  };

  const pan = Gesture.Pan()
    .activeOffsetX([-18, 18])
    .failOffsetY([-16, 16])
    .onUpdate((e) => { x.value = e.translationX * 0.42; })
    .onEnd((e) => {
      const dir: SwipeDir = e.translationX < 0 ? 1 : -1;
      const far = Math.abs(e.translationX) > width * 0.22 || Math.abs(e.velocityX) > 650;
      runOnJS(finish)(dir, far);
    });

  const slide = useAnimatedStyle(() => ({
    transform: [{ translateX: x.value }],
    opacity: interpolate(Math.abs(x.value), [0, width * 0.55], [1, 0], Extrapolation.CLAMP),
  }));

  return (
    <GestureDetector gesture={pan}>
      <View style={styles.fill} testID={testID}>
        <Animated.View style={[styles.fill, slide]}>{children}</Animated.View>
      </View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({ fill: { flex: 1 } });
