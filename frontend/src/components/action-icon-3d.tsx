// PAUSE — icone 3D delle azioni di fine storia (Mi piace, Salva, Condividi),
// nello stesso stile degli oggetti 3D dell'app (kind-*.png). Mi piace e Salva
// hanno due stati: spento (oggetto grigio-lavanda) e acceso (oggetto colorato
// pieno). Il passaggio è una dissolvenza incrociata tra i due oggetti, con un
// piccolo balzo e un alone che si accende — fluido e armonioso; lo spegnimento
// è una dissolvenza più corta e quieta. Condividi ha un solo stato e rimbalza al tocco.
import { useEffect, useRef } from "react";
import { Pressable, StyleProp, StyleSheet, ViewStyle } from "react-native";
import { Image } from "expo-image";
import Animated, { Easing, useAnimatedStyle, useSharedValue, withSequence, withSpring, withTiming } from "react-native-reanimated";

import { withAlpha } from "@/src/theme";
import { BOOKMARK_3D } from "./icon-3d-assets";

const ART = {
  heart: { base: require("../../assets/images/act-heart-base.png"), active: require("../../assets/images/act-heart-active.png") },
  bookmark: BOOKMARK_3D,
  share: { base: require("../../assets/images/act-share-v2.png"), active: null },
} as const;

export type ActionKind = keyof typeof ART;

export function ActionIcon3D({ kind, active = false, glowColor, size = 34, onPress, style, testID, accessibilityLabel }: {
  kind: ActionKind;
  /** Stato acceso (solo cuore e segnalibro): il cambio anima la dissolvenza tra i due oggetti. */
  active?: boolean;
  /** Colore dell'alone quando è acceso. */
  glowColor: string;
  size?: number;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  testID: string;
  accessibilityLabel?: string;
}) {
  const art = ART[kind];
  const on = useSharedValue(active ? 1 : 0);
  const scale = useSharedValue(1);
  const first = useRef(true);

  useEffect(() => {
    // Al montaggio lo stato si mostra com'è, senza animare.
    if (first.current) { first.current = false; on.value = active ? 1 : 0; return; }
    if (!art.active) return;
    if (active) {
      on.value = withTiming(1, { duration: 360, easing: Easing.out(Easing.cubic) });
      scale.value = withSequence(
        withTiming(0.84, { duration: 90, easing: Easing.out(Easing.quad) }),
        withTiming(1.24, { duration: 170, easing: Easing.out(Easing.quad) }),
        withSpring(1, { damping: 9, stiffness: 190 }),
      );
    } else {
      on.value = withTiming(0, { duration: 260, easing: Easing.out(Easing.quad) });
      scale.value = withSequence(withTiming(0.9, { duration: 100 }), withSpring(1, { damping: 12, stiffness: 210 }));
    }
  }, [active, art.active, on, scale]);

  const press = () => {
    // Senza secondo stato (Condividi) il riscontro è il solo rimbalzo.
    if (!art.active) scale.value = withSequence(withTiming(0.86, { duration: 80 }), withSpring(1, { damping: 9, stiffness: 260 }));
    onPress();
  };

  const wrap = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  const baseStyle = useAnimatedStyle(() => ({ opacity: 1 - on.value }));
  // L'oggetto acceso nasce dal centro di quello spento mentre lo sostituisce.
  const activeStyle = useAnimatedStyle(() => ({ opacity: on.value, transform: [{ scale: 0.7 + 0.3 * on.value }] }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: on.value }));

  return (
    <Pressable
      onPress={press} hitSlop={8} testID={testID} style={[styles.cell, style]}
      accessibilityRole="button" accessibilityLabel={accessibilityLabel} accessibilityState={{ selected: active }}
    >
      <Animated.View style={[{ width: size, height: size }, styles.wrap, wrap]}>
        {art.active ? (
          <Animated.View
            pointerEvents="none"
            style={[styles.glow, {
              width: size * 0.7, height: size * 0.7, borderRadius: size * 0.35,
              backgroundColor: withAlpha(glowColor, 0.26),
              boxShadow: `0px 0px ${Math.round(size * 0.6)}px ${withAlpha(glowColor, 0.7)}` as any,
            }, glowStyle]}
          />
        ) : null}
        <Animated.View testID={`${testID}-base`} style={[StyleSheet.absoluteFill, baseStyle]}>
          <Image source={art.base} style={StyleSheet.absoluteFill} contentFit="contain" transition={0} />
        </Animated.View>
        {art.active ? (
          <Animated.View testID={`${testID}-active`} style={[StyleSheet.absoluteFill, activeStyle]}>
            <Image source={art.active} style={StyleSheet.absoluteFill} contentFit="contain" transition={0} />
          </Animated.View>
        ) : null}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  cell: { flex: 1, minHeight: 44, minWidth: 44, alignItems: "center", justifyContent: "center", paddingVertical: 2 },
  wrap: { alignItems: "center", justifyContent: "center" },
  glow: { position: "absolute" },
});
