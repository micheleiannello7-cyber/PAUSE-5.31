import { useId } from "react";
import { View, Text } from "react-native";
import Svg, { Circle, Rect, Defs, LinearGradient, Stop } from "react-native-svg";
import { makeStyles, useTheme, typography } from "@/src/theme";
import { useI18n } from "@/src/i18n";

// Gradient ring with two rounded "pause" bars.
export function PauseMark({ size = 28 }: { size?: number }) {
  const { colors } = useTheme();
  // Unique gradient id per instance: on web, a shared id can resolve to a
  // hidden (display:none) screen's <defs> and the gradient stops painting.
  const gradId = `pauseGrad-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const fill = `url(#${gradId})`;
  return (
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Defs>
        <LinearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor={colors.gradient[0]} />
          <Stop offset="1" stopColor={colors.gradient[1]} />
        </LinearGradient>
      </Defs>
      <Circle cx="50" cy="50" r="43" stroke={fill} strokeWidth="6" fill="none" />
      <Rect x="33" y="29" width="12" height="42" rx="6" fill={fill} />
      <Rect x="55" y="29" width="12" height="42" rx="6" fill={fill} />
    </Svg>
  );
}

// "PΛUSE" wordmark with wide tracking. Uses Greek uppercase Lambda so the
// caret glyph sits at cap-height, matching the other letters visually.
export function PauseWordmark({ size = 16 }: { size?: number }) {
  const styles = useStyles();
  return (
    <Text style={[styles.word, { fontSize: size, letterSpacing: size * 0.38 }]} testID="pause-wordmark">
      PΛUSE
    </Text>
  );
}

// Compact header logo: mark + wordmark.
export function PauseLogo({ compact = false, prominent = false }: { compact?: boolean; prominent?: boolean }) {
  const styles = useStyles();
  return (
    <View style={styles.row} testID="pause-logo">
      <PauseMark size={prominent ? 40 : compact ? 22 : 28} />
      <PauseWordmark size={prominent ? 20 : compact ? 14 : 17} />
    </View>
  );
}

// Big centered lockup with tagline (onboarding / splash-like moments).
export function PauseHero() {
  const { t } = useI18n();
  const styles = useStyles();
  return (
    <View style={styles.hero}>
      <PauseMark size={84} />
      <PauseWordmark size={30} />
      <Text style={styles.tagline}>{t.tagline}</Text>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  row: { flexDirection: "row", alignItems: "center", gap: 10 },
  word: { color: colors.onSurface, fontFamily: typography.display },
  hero: { alignItems: "center", gap: 14 },
  tagline: {
    color: colors.muted, fontFamily: typography.bodyMedium,
    fontSize: 11, letterSpacing: 3,
  },
}));
