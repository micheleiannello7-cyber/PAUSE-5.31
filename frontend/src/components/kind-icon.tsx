// PAUSE — icone 3D dei due formati: lampadina = Curiosità, libri con tocco =
// Mini lezione. `lit` controlla lo stato acceso/spento: quando passa a true
// la lampadina "si accende" (breve sfarfallio, alone caldo, piccolo rimbalzo);
// i libri si illuminano di ciano e fanno un piccolo balzo.
import { useEffect } from "react";
import { View, StyleSheet, StyleProp, ViewStyle } from "react-native";
import { Image } from "expo-image";
import Animated, {
  useSharedValue, useAnimatedStyle, withTiming, withSequence, withSpring, withDelay, Easing,
} from "react-native-reanimated";

import { useTheme, withAlpha } from "@/src/theme";

export type StoryKind = "stories" | "lessons";

// Nota: i file sono nominati al contrario (kind-lesson.png = lampadina,
// kind-bulb.png = libri con tocco); la mappa qui sotto è quella corretta.
const SOURCES = {
  stories: require("../../assets/images/kind-lesson.png"),
  lessons: require("../../assets/images/kind-bulb.png"),
} as const;

export function KindIcon({
  kind, size = 20, lit = true, glow, style, testID,
}: {
  kind: StoryKind;
  size?: number;
  /** false = spenta/attenuata; il passaggio a true anima l'accensione. */
  lit?: boolean;
  /** Alone luminoso dietro l'icona (default: solo da 28px in su). */
  glow?: boolean;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}) {
  const { colors } = useTheme();
  const showGlow = glow ?? size >= 28;
  const glowColor = kind === "stories" ? colors.warning : colors.cyan;

  const bright = useSharedValue(lit ? 1 : 0);
  const scale = useSharedValue(1);
  const lift = useSharedValue(0);

  useEffect(() => {
    if (lit) {
      if (kind === "stories") {
        // Accensione: due sfarfallii veloci, poi luce piena.
        bright.value = withSequence(
          withTiming(1, { duration: 90 }),
          withTiming(0.35, { duration: 70 }),
          withTiming(1, { duration: 80 }),
          withTiming(0.7, { duration: 60 }),
          withTiming(1, { duration: 220, easing: Easing.out(Easing.quad) }),
        );
      } else {
        bright.value = withTiming(1, { duration: 320, easing: Easing.out(Easing.cubic) });
        lift.value = withSequence(withTiming(-size * 0.12, { duration: 140, easing: Easing.out(Easing.quad) }), withSpring(0, { damping: 9, stiffness: 180 }));
      }
      scale.value = withSequence(withTiming(1.12, { duration: 140, easing: Easing.out(Easing.quad) }), withDelay(40, withSpring(1, { damping: 10, stiffness: 160 })));
    } else {
      bright.value = withTiming(0, { duration: 220 });
      scale.value = withTiming(1, { duration: 200 });
      lift.value = withTiming(0, { duration: 200 });
    }
  }, [lit, kind, size, bright, scale, lift]);

  const imgStyle = useAnimatedStyle(() => ({
    opacity: 0.42 + 0.58 * bright.value,
    transform: [{ translateY: lift.value }, { scale: scale.value }],
  }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: bright.value }));

  return (
    <View style={[{ width: size, height: size }, styles.wrap, style]} testID={testID}>
      {showGlow ? (
        <Animated.View
          pointerEvents="none"
          style={[
            styles.glow,
            {
              width: size * 0.7, height: size * 0.7, borderRadius: size * 0.35,
              backgroundColor: withAlpha(glowColor, 0.28),
              boxShadow: `0px 0px ${Math.round(size * 0.55)}px ${withAlpha(glowColor, 0.75)}` as any,
            },
            glowStyle,
          ]}
        />
      ) : null}
      <Animated.View style={[StyleSheet.absoluteFill, imgStyle]}>
        <Image source={SOURCES[kind]} style={StyleSheet.absoluteFill} contentFit="contain" transition={0} />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { alignItems: "center", justifyContent: "center" },
  glow: { position: "absolute" },
});
