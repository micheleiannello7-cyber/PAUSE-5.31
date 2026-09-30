// PAUSE — piccole etichette "editoriali" del lettore. Ora in vetro (design
// system Glassmorphism condiviso): pillole traslucide con bordo luminoso
// molto sottile, come il pulsante "Ascolta" del deep-dive.
//   - CategoryTag: icona nel colore della categoria + nome in maiuscoletto
//   - MetaPill:    informazione secondaria (es. "3 min")
import { View, Text, StyleProp, ViewStyle } from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";

import { makeStyles, useTheme, typography } from "@/src/theme";
import { GlassPill } from "@/src/components/glass";

export function CategoryTag({
  name, icon, style, testID = "category-tag",
}: { name: string; icon: string; color: string; style?: StyleProp<ViewStyle>; testID?: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  // Solo la categoria principale ("Scienza · Natura" → "SCIENZA").
  const label = name.split("·")[0].trim().toUpperCase();
  return (
    <GlassPill
      style={[styles.tagOuter, style]}
      testID={testID}
      tone="neutral"
      height={34}
    >
      <View style={styles.iconWrap}>
        <Ionicons name={icon as any} size={12} color={colors.onSurfaceTertiary} />
      </View>
      <Text testID={`${testID}-label`} style={styles.tagText} numberOfLines={1} ellipsizeMode="tail">{label}</Text>
    </GlassPill>
  );
}

export function MetaPill({
  icon, label, style, testID = "meta-pill",
}: { icon: string; label: string; style?: StyleProp<ViewStyle>; testID?: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <GlassPill style={[styles.metaOuter, style]} testID={testID} height={34}>
      <Ionicons name={icon as any} size={13} color={colors.cyanSoft} style={{ marginLeft: 12 }} />
      <Text style={styles.metaText}>{label}</Text>
    </GlassPill>
  );
}

// Meta "in linea" per la reading experience: niente pillola, solo icona cyan
// e testo caldo. Sta allo stesso livello del titolo, non sembra un pulsante.
export function MetaInline({
  icon, label, style, testID = "meta-inline",
}: { icon: string; label: string; style?: StyleProp<ViewStyle>; testID?: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <View style={[styles.inline, style]} testID={testID}>
      <Ionicons name={icon as any} size={13} color={colors.cyanSoft} />
      <Text style={styles.inlineText}>{label}</Text>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  tagOuter: { flexShrink: 1, paddingLeft: 5, paddingRight: 13 },
  iconWrap: { width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center", marginRight: 8 },
  tagText: { flexShrink: 1, color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 10.5, letterSpacing: 1.6 },
  metaOuter: { paddingRight: 12, gap: 5 },
  metaText: { color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 12, marginLeft: 5 },
  inline: { flexDirection: "row", alignItems: "center", gap: 5, height: 34, paddingHorizontal: 4 },
  inlineText: { color: colors.textWarmSecondary, fontFamily: typography.bodyMedium, fontSize: 12.5, letterSpacing: 0.4 },
}));
