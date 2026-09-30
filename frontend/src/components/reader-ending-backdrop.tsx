// PAUSE — sfondo della schermata finale della lettura: lo stesso linguaggio
// visivo dell'onboarding "Raccontaci qualcosa di te" (lago notturno con
// pianeta + veli dark-navy). Livello fisso dietro allo scroll, che compare
// gradualmente solo quando si arriva all'ultima pagina ("Da ricordare").
import { StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Extrapolation, interpolate, SharedValue, useAnimatedStyle } from "react-native-reanimated";

import { withAlpha } from "@/src/theme";
import { ONB } from "./onboarding-palette";

const ARTWORK = require("../../assets/images/onboarding-profile-bg.jpg");

export function ReaderEndingBackdrop({ scrollY, pageH, endTop }: {
  scrollY: SharedValue<number>; pageH: SharedValue<number>;
  /** Posizione (nello scroll) a cui la schermata finale è tutta in vista. */
  endTop: SharedValue<number>;
}) {
  const fade = useAnimatedStyle(() => {
    const end = endTop.value;
    if (end <= 0) return { opacity: 0 };
    return { opacity: interpolate(scrollY.value, [end - pageH.value * 0.55, end], [0, 1], Extrapolation.CLAMP) };
  });
  return (
    <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, fade]} testID="reader-ending-backdrop">
      <Image source={ARTWORK} contentFit="cover" contentPosition="center" transition={0} cachePolicy="memory-disk" accessible={false} style={StyleSheet.absoluteFill} />
      <LinearGradient
        colors={[withAlpha(ONB.bgTop, 0.62), withAlpha(ONB.bgTop, 0.34), withAlpha(ONB.bgTop, 0.3), withAlpha(ONB.bgTop, 0.46), withAlpha(ONB.bgTop, 0.72), withAlpha(ONB.bgTop, 0.84)]}
        locations={[0, 0.16, 0.36, 0.58, 0.82, 1]}
        style={StyleSheet.absoluteFill}
      />
      <View style={[StyleSheet.absoluteFill, { backgroundColor: withAlpha(ONB.bgTop, 0.12) }]} />
    </Animated.View>
  );
}
