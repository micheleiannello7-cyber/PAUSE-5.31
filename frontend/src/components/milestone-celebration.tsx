// PAUSE — festeggiamento di un traguardo di lettura (20, 40, 60… storie):
// coriandoli, medaglia animata, nome del livello e prossimo obiettivo.
// Stesso linguaggio "dark navy / vetro" dell'onboarding e delle tessere Home.
import { useEffect, useMemo } from "react";
import { Modal, Pressable, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import * as Haptics from "@/src/haptics";
import Animated, {
  Easing, useAnimatedStyle, useSharedValue, withDelay, withRepeat, withSequence, withSpring, withTiming,
} from "react-native-reanimated";
import { makeStyles, radius, typography, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { MILESTONE_STEP } from "@/src/milestones";
import { GradientButton } from "./gradient-button";
import { ONB } from "./onboarding-palette";

const TIERS: Record<number, { it: string; en: string; icon: string }> = {
  20: { it: "Lettore curioso", en: "Curious reader", icon: "ribbon" },
  40: { it: "Esploratore di idee", en: "Idea explorer", icon: "compass" },
  60: { it: "Mente aperta", en: "Open mind", icon: "planet" },
  80: { it: "Collezionista di storie", en: "Story collector", icon: "library" },
  100: { it: "Centurione", en: "Centurion", icon: "trophy" },
};
const TOP_TIER = { it: "Maestro della pausa", en: "Master of the pause", icon: "diamond" };

const CONFETTI_COLORS = [ONB.cyan, ONB.violet, ONB.cyanSoft, ONB.text, "#FFD166", "#FF6B9D"];
const PIECES = 28;

// Posizioni e ritardi pseudo-casuali ma stabili (stesso traguardo → stessa pioggia).
function seeded(seed: number) {
  let s = seed % 2147483647 || 1;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
}

function Confetti({ index, rnd, height }: { index: number; rnd: () => number; height: number }) {
  const x = rnd() * 100;
  const delay = rnd() * 700;
  const duration = 2200 + rnd() * 1400;
  const drift = (rnd() - 0.5) * 90;
  const size = 6 + rnd() * 6;
  const color = CONFETTI_COLORS[index % CONFETTI_COLORS.length];
  const round = rnd() > 0.6;
  const fall = useSharedValue(0);
  useEffect(() => {
    fall.value = withDelay(delay, withTiming(1, { duration, easing: Easing.out(Easing.quad) }));
  }, [fall, delay, duration]);
  const style = useAnimatedStyle(() => ({
    opacity: fall.value < 0.85 ? 1 : (1 - fall.value) / 0.15,
    transform: [
      { translateY: -40 + fall.value * (height + 80) },
      { translateX: Math.sin(fall.value * Math.PI * 2) * drift },
      { rotate: `${fall.value * 720 * (index % 2 ? 1 : -1)}deg` },
    ],
  }));
  return (
    <Animated.View pointerEvents="none" style={[{ position: "absolute", top: 0, left: `${x}%`, width: size, height: round ? size : size * 1.8, borderRadius: round ? size : 2, backgroundColor: color }, style]} />
  );
}

export function MilestoneCelebration({ milestone, onClose, onStats }: {
  milestone: number | null; onClose: () => void; onStats: () => void;
}) {
  const styles = useStyles();
  const { t, lang } = useI18n();
  const { height } = useWindowDimensions();
  const visible = milestone !== null;
  const tier = milestone !== null ? (TIERS[milestone] ?? TOP_TIER) : TOP_TIER;
  const tierName = lang === "en" ? tier.en : tier.it;
  const next = (milestone ?? 0) + MILESTONE_STEP;
  const rnd = useMemo(() => seeded((milestone ?? 1) * 7919), [milestone]);

  const pop = useSharedValue(0);
  const glow = useSharedValue(0.4);
  const rise = useSharedValue(0);
  useEffect(() => {
    if (!visible) { pop.value = 0; rise.value = 0; return; }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    pop.value = withDelay(120, withSpring(1, { damping: 11, stiffness: 150, mass: 0.9 }));
    rise.value = withDelay(320, withTiming(1, { duration: 420, easing: Easing.out(Easing.cubic) }));
    glow.value = withRepeat(withSequence(withTiming(1, { duration: 1100 }), withTiming(0.4, { duration: 1100 })), -1, true);
  }, [visible, pop, rise, glow]);
  const medalStyle = useAnimatedStyle(() => ({ transform: [{ scale: 0.3 + pop.value * 0.7 }, { rotate: `${(1 - pop.value) * -25}deg` }], opacity: pop.value }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: glow.value * pop.value, transform: [{ scale: 0.9 + glow.value * 0.25 }] }));
  const textStyle = useAnimatedStyle(() => ({ opacity: rise.value, transform: [{ translateY: (1 - rise.value) * 18 }] }));

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} statusBarTranslucent>
      <View style={styles.backdrop} testID="milestone-celebration">
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityLabel={t.milestone_continue} />
        <View pointerEvents="none" style={StyleSheet.absoluteFill}>
          {visible ? Array.from({ length: PIECES }, (_, i) => <Confetti key={`${milestone}-${i}`} index={i} rnd={rnd} height={height} />) : null}
        </View>
        <View style={styles.card}>
          <LinearGradient colors={[ONB.glassTop, ONB.glassBottom]} style={StyleSheet.absoluteFill} pointerEvents="none" />
          <View pointerEvents="none" style={styles.highlight} />
          <View style={styles.medalWrap}>
            <Animated.View style={[styles.glow, glowStyle]} />
            <Animated.View style={[styles.medal, medalStyle]} testID="milestone-medal">
              <LinearGradient colors={[ONB.violet, ONB.cyan]} start={{ x: 0.1, y: 0 }} end={{ x: 0.9, y: 1 }} style={styles.medalRing}>
                <View style={styles.medalInner}>
                  <Text style={styles.medalNumber} testID="milestone-number">{milestone}</Text>
                  <Ionicons name={tier.icon as any} size={16} color={ONB.cyan} />
                </View>
              </LinearGradient>
            </Animated.View>
          </View>
          <Animated.View style={[styles.copy, textStyle]}>
            <Text style={styles.eyebrow} testID="milestone-eyebrow">{t.milestone_eyebrow}</Text>
            <Text style={styles.title} testID="milestone-tier">{tierName}</Text>
            <Text style={styles.body} testID="milestone-body">
              {t.milestone_read.replace("{count}", String(milestone ?? 0))} {t.milestone_next.replace("{next}", String(next))}
            </Text>
          </Animated.View>
          <GradientButton label={t.milestone_continue} icon="sparkles" onPress={onClose} testID="milestone-continue" style={styles.cta} />
          <Pressable onPress={onStats} style={styles.link} testID="milestone-stats" accessibilityRole="button">
            <Text style={styles.linkText}>{t.milestone_stats}</Text>
            <Ionicons name="chevron-forward" size={13} color={ONB.textSecondary} />
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const useStyles = makeStyles(() => ({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: 28, backgroundColor: withAlpha(ONB.bgTop, 0.86) },
  card: { width: "100%", maxWidth: 360, alignItems: "center", paddingTop: 30, paddingBottom: 20, paddingHorizontal: 22, borderRadius: radius.lg, overflow: "hidden", borderWidth: 1, borderColor: ONB.glassBorderStrong, backgroundColor: ONB.glassBottom },
  highlight: { position: "absolute", top: 0, left: 24, right: 24, height: 1, backgroundColor: withAlpha(ONB.cyanSoft, 0.5) },
  medalWrap: { width: 150, height: 150, alignItems: "center", justifyContent: "center", marginBottom: 14 },
  glow: { position: "absolute", width: 150, height: 150, borderRadius: 75, backgroundColor: withAlpha(ONB.cyan, 0.22) },
  medal: { width: 118, height: 118 },
  medalRing: { flex: 1, borderRadius: 59, padding: 5, boxShadow: `0px 10px 30px ${withAlpha(ONB.violet, 0.45)}` as any },
  medalInner: { flex: 1, borderRadius: 54, backgroundColor: ONB.bgMid, alignItems: "center", justifyContent: "center", gap: 2, borderWidth: 1, borderColor: withAlpha(ONB.cyanSoft, 0.35) },
  medalNumber: { color: ONB.text, fontFamily: typography.displayBold, fontSize: 40, lineHeight: 44, letterSpacing: -1 },
  copy: { alignItems: "center", gap: 6, marginBottom: 22 },
  eyebrow: { color: ONB.cyan, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 2 },
  title: { color: ONB.text, fontFamily: typography.displayBold, fontSize: 24, lineHeight: 29, textAlign: "center", letterSpacing: -0.4 },
  body: { color: ONB.textSecondary, fontFamily: typography.body, fontSize: 13.5, lineHeight: 19, textAlign: "center", paddingHorizontal: 6 },
  cta: { alignSelf: "stretch" },
  link: { flexDirection: "row", alignItems: "center", gap: 2, minHeight: 44, paddingHorizontal: 12, marginTop: 4 },
  linkText: { color: ONB.textSecondary, fontFamily: typography.bodyMedium, fontSize: 12.5 },
}));
