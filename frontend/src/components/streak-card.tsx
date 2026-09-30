import { View, Text, Pressable } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import Ionicons from "@react-native-vector-icons/ionicons";
import { UserState } from "@/src/api";
import { makeStyles, useTheme, spacing, typography } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { useLimitGate } from "@/src/hooks/use-limit-gate";
import { GlassSurface } from "@/src/components/glass";

// Glanceable progress card for the Home screen: streak, stories, minutes + session bar.
// Tapping it opens the full statistics screen.
export function StreakCard({ user }: { user?: UserState }) {
  const SESSION_LIMIT = user?.is_premium ? 6 : 5;
  const streak = user?.streak_days ?? 0;
  const stories = user?.completed_story_ids.length ?? 0;
  const minutes = user?.total_minutes ?? 0;
  const session = Math.min(user?.session_count ?? 0, SESSION_LIMIT);
  const pct = (session / SESSION_LIMIT) * 100;
  const { t } = useI18n();
  const router = useRouter();
  const styles = useStyles();
  const { colors } = useTheme();
  // La barra "sessione di oggi" ha senso solo se il limite è attivo.
  const limit = useLimitGate();
  const showSession = !!limit?.enforce;

  return (
    <GlassSurface intensity="regular" testID="streak-card-surface">
      <Pressable
        style={({ pressed }) => [styles.card, pressed && { opacity: 0.9 }]}
        testID="streak-card"
        onPress={() => router.push("/stats")}
      >
        <View style={styles.row}>
          <Stat icon="flame" color={colors.warning} value={streak} label={streak === 1 ? t.days_streak_1 : t.days_streak} />
          <View style={styles.sep} />
          <Stat icon="book" color={colors.cyan} value={stories} label={stories === 1 ? t.stories_read_1 : t.stories_read} />
          <View style={styles.sep} />
          <Stat icon="time" color={colors.brandSecondary} value={minutes} label={t.minutes} />
        </View>

        {showSession ? (
          <>
            <View style={styles.barHead}>
              <Text style={styles.barLabel}>{t.session_today}</Text>
              <Text style={styles.barValue}>{session} / {SESSION_LIMIT}</Text>
            </View>
            <View style={styles.track}>
              <LinearGradient
                colors={[colors.cyan, colors.cyanSoft]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={[styles.fill, { width: `${Math.max(pct, 2)}%` }]}
              />
            </View>
          </>
        ) : null}
        <View style={styles.footer}>
          <Ionicons name="stats-chart-outline" size={12} color={colors.cyan} />
          <Text style={styles.footerText}>{t.stats_row}</Text>
          <Ionicons name="chevron-forward" size={12} color={colors.muted} />
        </View>
      </Pressable>
    </GlassSurface>
  );
}

function Stat({ icon, color, value, label }: { icon: string; color: string; value: number; label: string }) {
  const styles = useStyles();
  return (
    <View style={styles.stat}>
      <View style={[styles.statOrb, { backgroundColor: color + "22", boxShadow: `0px 0px 12px ${color}55` as any }]}>
        <Ionicons name={icon as any} size={14} color={color} />
      </View>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.label} numberOfLines={1}>{label}</Text>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  card: { padding: spacing.lg, gap: spacing.lg },
  row: { flexDirection: "row", alignItems: "center" },
  stat: { flex: 1, alignItems: "center", gap: 4 },
  statOrb: { width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", marginBottom: 2 },
  sep: { width: 1, height: 40, backgroundColor: colors.glassBorder },
  value: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 22 },
  label: { color: colors.muted, fontFamily: typography.body, fontSize: 11 },
  barHead: { flexDirection: "row", justifyContent: "space-between", marginBottom: -spacing.sm },
  barLabel: { color: colors.muted, fontFamily: typography.body, fontSize: 12 },
  barValue: { color: colors.onSurfaceSecondary, fontFamily: typography.bodyBold, fontSize: 12 },
  track: { height: 5, borderRadius: 3, backgroundColor: colors.track, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 3 },
  footer: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: -spacing.sm },
  footerText: { flex: 1, color: colors.cyan, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 0.5 },
}));
