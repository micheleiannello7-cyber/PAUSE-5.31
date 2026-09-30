// PAUSE — barra superiore minimale della lettura: tasto indietro, titolo
// compatto della storia (mai troncato: scende di corpo) e, a destra, il
// progresso "01 / 06" quando si è nei capitoli (o l'azione già esistente,
// es. il badge Ascolta). Sotto, una linea di progresso sottilissima a
// segmenti, uno per capitolo, nel colore del tema. Il fondo è un vetro molto
// trasparente che compare solo quando la copertina è scorsa via.
import { ReactNode } from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import Animated, { SharedValue, useAnimatedStyle, useDerivedValue, withTiming } from "react-native-reanimated";

import { makeStyles, useTheme, spacing, typography, withAlpha } from "@/src/theme";
import { HighlightedTitle } from "@/src/components/highlighted-title";

export const READER_HEADER_H = 60;

type Props = {
  topInset: number;
  title: string;
  highlight: string[];
  /** Capitolo corrente (1..total); 0 = introduzione, > total = fine. */
  current: number;
  total: number;
  /** 0..1, opacità del vetro di fondo (1 quando la copertina è scorsa via). */
  solid: SharedValue<number>;
  onBack: () => void;
  /** Azione a destra già esistente (es. riapri il player): al posto del progresso. */
  corner?: ReactNode;
};

const pad = (n: number) => String(n).padStart(2, "0");

export function ReaderHeader({ topInset, title, highlight, current, total, solid, onBack, corner }: Props) {
  const styles = useStyles();
  const { colors } = useTheme();
  const bg = useAnimatedStyle(() => ({ opacity: solid.value }));
  const n = title.length;
  const titleSize = n > 70 ? styles.titleXs : n > 55 ? styles.titleSm : n > 40 ? styles.titleMd : null;
  const inChapters = current > 0;
  const shown = Math.min(Math.max(current, 0), total);
  const label = inChapters ? `${pad(shown)} / ${pad(total)}` : "";
  // Il titolo compatto compare solo dal primo capitolo: sull'apertura la barra resta pulita.
  const titleIn = useDerivedValue(() => withTiming(inChapters ? 1 : 0, { duration: 280 }), [inChapters]);
  const titleFade = useAnimatedStyle(() => ({ opacity: titleIn.value, transform: [{ translateY: (1 - titleIn.value) * 6 }] }));

  return (
    <View style={[styles.wrap, { paddingTop: topInset }]} testID="reader-header">
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, bg]}>
        <LinearGradient colors={[withAlpha(colors.surface, 0.98), withAlpha(colors.surface, 0.95)]} style={StyleSheet.absoluteFill} />
        {/* Il contenuto scivola sotto la barra sfumando: nessun taglio netto. */}
        <LinearGradient colors={[withAlpha(colors.surface, 0.95), withAlpha(colors.surface, 0)]} style={styles.scrim} />
      </Animated.View>
      <View style={styles.row}>
        <Pressable onPress={onBack} hitSlop={10} style={styles.back} accessibilityRole="button" accessibilityLabel="Back" testID="reader-back">
          <Ionicons name="chevron-back" size={24} color={colors.textWarm} />
        </Pressable>
        <Animated.View style={[styles.copy, titleFade]} pointerEvents="none">
          <HighlightedTitle title={title} highlight={highlight} style={[styles.title, titleSize]} numberOfLines={2} testID="reader-header-title" />
        </Animated.View>
        <View style={styles.right}>
          {corner ? corner : (
            <Text style={[styles.label, !inChapters && styles.labelHidden]} numberOfLines={1} testID="deep-dive-page-label">
              {inChapters ? <><Text style={{ color: colors.textWarm }}>{pad(shown)}</Text>{" / "}{pad(total)}</> : label}
            </Text>
          )}
        </View>
      </View>
      {/* Linea di progresso a segmenti (uno per capitolo): sottile, nel colore del tema. */}
      <View style={[styles.track, !inChapters && styles.trackHidden]} accessibilityRole="progressbar" pointerEvents="none" testID="reader-progress">
        {Array.from({ length: Math.max(total, 1) }, (_, i) => (
          <View
            key={i}
            style={[styles.segment, { backgroundColor: i < shown ? colors.brand : withAlpha(colors.onSurface, 0.12) }, i < shown && { boxShadow: `0px 0px 8px ${withAlpha(colors.brand, 0.6)}` as any }]}
            testID={i < shown ? `reader-progress-fill-${i + 1}` : undefined}
          />
        ))}
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 20 },
  scrim: { position: "absolute", left: 0, right: 0, top: "100%", height: 28 },
  row: {
    height: READER_HEADER_H - 4, flexDirection: "row", alignItems: "center", gap: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  back: { width: 44, height: 44, alignItems: "center", justifyContent: "center", borderRadius: 22 },
  copy: { flex: 1, minWidth: 0, alignItems: "center", justifyContent: "center" },
  title: {
    color: colors.textWarm, fontFamily: typography.bodyMedium, fontSize: 14, lineHeight: 17, textAlign: "center",
    textShadowColor: withAlpha(colors.surface, 0.75), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 8,
  },
  titleMd: { fontSize: 13.5, lineHeight: 16 },
  titleSm: { fontSize: 13, lineHeight: 15.5 },
  titleXs: { fontSize: 12.5, lineHeight: 15 },
  right: { minWidth: 64, alignItems: "flex-end", justifyContent: "center" },
  label: { color: colors.textWarmSecondary, fontFamily: typography.bodyMedium, fontSize: 14, letterSpacing: 0.8, fontVariant: ["tabular-nums"] },
  labelHidden: { opacity: 0 },
  track: { flexDirection: "row", gap: 4, height: 2, marginHorizontal: spacing.md },
  trackHidden: { opacity: 0 },
  segment: { flex: 1, height: 2, borderRadius: 1 },
}));
