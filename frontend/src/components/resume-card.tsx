// PAUSE — "Riprendi da dove eri": la storia lasciata a metà, in evidenza sotto
// il mazzo della Home. Vetro dark-navy come le tessere, copertina, percentuale
// e barra di avanzamento; tocco → riapre il lettore alla pagina giusta.
import { Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import { ReadingProgress } from "@/src/reading-progress";
import { makeStyles, radius, typography, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { StoryHero } from "./story-hero";
import { ONB } from "./onboarding-palette";

export function ResumeCard({ progress, onPress }: { progress: ReadingProgress; onPress: () => void }) {
  const { t } = useI18n();
  const styles = useStyles();
  const pct = Math.round(progress.progress * 100);
  return (
    <Pressable onPress={onPress} testID="resume-reading-card" accessibilityRole="button"
      accessibilityLabel={`${t.resume_eyebrow}. ${progress.story.title}. ${t.resume_left.replace("{pct}", String(pct))}`}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      <LinearGradient colors={[ONB.glassTop, ONB.glassBottom]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <View pointerEvents="none" style={styles.highlight} />
      <View style={styles.row}>
        <View style={styles.thumbWrap}>
          <StoryHero story={progress.story} style={styles.thumb} iconSize={24} size="thumb" />
          <View style={styles.pctPill}><Text testID="resume-reading-progress" style={styles.pctText}>{pct}%</Text></View>
        </View>
        <View style={styles.info}>
          <View style={styles.eyebrowRow}>
            <Ionicons name="bookmark" size={10} color={ONB.cyan} />
            <Text testID="resume-reading-label" style={styles.eyebrow}>{t.resume_eyebrow}</Text>
          </View>
          <Text testID="resume-reading-title" style={styles.title} numberOfLines={2}>{progress.story.title}</Text>
          <View style={styles.track}>
            <LinearGradient colors={[ONB.cyan, ONB.violet]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[styles.fill, { width: `${Math.max(pct, 4)}%` }]} />
          </View>
        </View>
        <View style={styles.play}><Ionicons name="play" size={16} color={ONB.bgTop} /></View>
      </View>
    </Pressable>
  );
}

const useStyles = makeStyles((colors) => ({
  card: { overflow: "hidden", borderRadius: radius.md, borderWidth: 1, borderColor: withAlpha(colors.brand, 0.34), backgroundColor: colors.artworkSurface, boxShadow: `0px 6px 22px ${withAlpha(colors.brand, 0.14)}` as any },
  highlight: { position: "absolute", top: 0, left: 14, right: 14, height: 1, backgroundColor: withAlpha(ONB.cyanSoft, 0.45) },
  row: { flexDirection: "row", alignItems: "center", gap: 12, padding: 8, paddingRight: 12 },
  thumbWrap: { position: "relative" },
  thumb: { width: 62, height: 62, borderRadius: radius.sm + 2, overflow: "hidden" },
  pctPill: { position: "absolute", bottom: -6, alignSelf: "center", paddingHorizontal: 6, height: 16, borderRadius: 8, alignItems: "center", justifyContent: "center", backgroundColor: ONB.bgTop, borderWidth: 1, borderColor: withAlpha(ONB.cyan, 0.6) },
  pctText: { color: ONB.cyan, fontFamily: typography.bodyBold, fontSize: 9 },
  info: { flex: 1, minWidth: 0, gap: 5 },
  eyebrowRow: { flexDirection: "row", alignItems: "center", gap: 5 },
  eyebrow: { color: ONB.cyan, fontFamily: typography.bodyBold, fontSize: 9, letterSpacing: 1.4 },
  title: { color: ONB.text, fontFamily: typography.bodyBold, fontSize: 13, lineHeight: 17 },
  track: { height: 4, borderRadius: 2, backgroundColor: withAlpha(ONB.cyanSoft, 0.14), overflow: "hidden" },
  fill: { height: "100%", borderRadius: 2 },
  play: { width: 38, height: 38, borderRadius: 19, alignItems: "center", justifyContent: "center", backgroundColor: ONB.cyan, paddingLeft: 2 },
  pressed: { opacity: 0.9 },
}));
