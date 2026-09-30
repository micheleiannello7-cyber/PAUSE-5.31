// PAUSE — atmosfera della Home: lo stesso sistema della lettura (fondo navy
// quasi nero, poche diffusioni luminose morbidissime, centro più scuro per la
// leggibilità), nella tonalità del tema scelto nel Profilo (atmosBase / Tint /
// Secondary / Glow in theme.ts). Statico: niente foto, stelle, texture o
// animazioni, così lo scorrimento resta leggero.
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useTheme, withAlpha } from "@/src/theme";

// Disco radiale bianco che sfuma a zero, tinto con il colore del tema.
const GLOW = require("../../assets/images/reader-glow.png");

export function HomeBackdrop() {
  const { colors } = useTheme();
  const { width: w, height: h } = useWindowDimensions();
  const big = Math.max(w, h);
  // Tre luci: in alto a sinistra, a destra a metà altezza, in basso. Più un
  // filo d'accento appena percettibile sul bordo alto.
  const lights = [
    { x: -big * 0.58, y: -big * 0.58, size: big * 1.3, color: colors.atmosTint, alpha: 1 },
    { x: w - big * 0.42, y: h * 0.42 - big * 0.5, size: big, color: colors.atmosSecondary, alpha: 0.9 },
    { x: w * 0.5 - big * 0.6, y: h - big * 0.5, size: big * 1.2, color: colors.atmosTint, alpha: 0.85 },
    { x: -big * 0.3, y: -big * 0.5, size: big * 0.7, color: colors.atmosGlow, alpha: 0.07 },
  ];
  return (
    <View pointerEvents="none" style={[styles.frame, { backgroundColor: colors.atmosBase }]} testID="home-backdrop">
      {lights.map((l, i) => (
        <View key={i} style={[styles.light, { left: l.x, top: l.y, width: l.size, height: l.size, opacity: l.alpha }]}>
          <Image source={GLOW} style={StyleSheet.absoluteFill} contentFit="fill" tintColor={l.color} transition={0} cachePolicy="memory" accessible={false} />
        </View>
      ))}
      {/* Protezione del contenuto: la fascia centrale resta più scura, i bordi respirano. */}
      <LinearGradient pointerEvents="none" testID="home-backdrop-veil"
        colors={[withAlpha(colors.atmosBase, 0.04), withAlpha(colors.atmosBase, 0.3), withAlpha(colors.atmosBase, 0.28), withAlpha(colors.atmosBase, 0.12)]}
        locations={[0, 0.35, 0.7, 1]} style={StyleSheet.absoluteFill} />
    </View>
  );
}

const styles = StyleSheet.create({
  frame: { position: "absolute", top: 0, right: 0, bottom: 0, left: 0, overflow: "hidden" },
  light: { position: "absolute" },
});