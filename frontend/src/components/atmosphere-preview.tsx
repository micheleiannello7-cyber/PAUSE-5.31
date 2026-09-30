// PAUSE — mini-anteprima dell'atmosfera di lettura di un tema (Profilo →
// colore accento): la stessa struttura del lettore in piccolo — fondo quasi
// nero, luci morbide agli angoli, cornice perimetrale, poche righe di "testo"
// — con i colori dell'accento scelto. Usa gli stessi parametri di
// theme.ts (atmosphere.base/tint/secondary/frame + brand): nessun sistema parallelo.
import { StyleSheet, View } from "react-native";
import { Image } from "expo-image";

import { Accent, ColorScheme, withAlpha } from "@/src/theme";

const GLOW = require("../../assets/images/reader-glow.png");

export function AtmospherePreview({ accent, scheme, width = 64, height = 92 }: {
  accent: Accent; scheme: ColorScheme; width?: number; height?: number;
}) {
  const set = accent[scheme];
  const a = set.atmosphere;
  const big = Math.max(width, height);
  const textLine = scheme === "dark" ? "rgba(247,243,235,0.55)" : "rgba(11,14,23,0.45)";
  return (
    <View style={[styles.box, { width, height, backgroundColor: a.base, borderColor: withAlpha(a.frame, 0.55) }]} pointerEvents="none" testID={`atmosphere-preview-${accent.id}`}>
      {/* Stessa composizione del lettore: tinta in alto a sinistra e in basso a destra, secondaria negli angoli opposti. */}
      <Light x={-big * 0.5} y={-big * 0.45} size={big * 1.1} color={a.tint} />
      <Light x={width - big * 0.6} y={height - big * 0.6} size={big * 1.1} color={a.tint} />
      <Light x={width - big * 0.5} y={-big * 0.5} size={big * 0.9} color={a.secondary} alpha={0.9} />
      <Light x={-big * 0.5} y={height - big * 0.45} size={big * 0.9} color={a.secondary} alpha={0.9} />
      {/* Poche righe di lettura: numero grande, occhiello, titolo, testo. */}
      <View style={styles.lines}>
        <View style={[styles.line, { width: "36%", height: 3, backgroundColor: set.brand }]} />
        <View style={[styles.line, { width: "78%", height: 4, backgroundColor: textLine }]} />
        <View style={[styles.line, { width: "62%", height: 4, backgroundColor: textLine }]} />
        <View style={[styles.line, styles.gap, { width: "84%", backgroundColor: withAlpha(a.frame, scheme === "dark" ? 0.22 : 0.3) }]} />
        <View style={[styles.line, { width: "84%", backgroundColor: withAlpha(a.frame, scheme === "dark" ? 0.22 : 0.3) }]} />
        <View style={[styles.line, { width: "70%", backgroundColor: withAlpha(a.frame, scheme === "dark" ? 0.22 : 0.3) }]} />
      </View>
    </View>
  );
}

function Light({ x, y, size, color, alpha = 1 }: { x: number; y: number; size: number; color: string; alpha?: number }) {
  return (
    <View style={[styles.light, { left: x, top: y, width: size, height: size, opacity: alpha }]}>
      <Image source={GLOW} style={StyleSheet.absoluteFill} contentFit="fill" tintColor={color} transition={0} cachePolicy="memory" accessible={false} />
    </View>
  );
}

const styles = StyleSheet.create({
  box: { borderRadius: 12, borderWidth: 1, overflow: "hidden" },
  light: { position: "absolute" },
  lines: { position: "absolute", left: 8, right: 8, top: 18, gap: 3.5 },
  line: { height: 2, borderRadius: 2 },
  gap: { marginTop: 4 },
});
