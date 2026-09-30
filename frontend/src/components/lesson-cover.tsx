// PAUSE — Visual cover for Mini lessons. Lessons have no photo hero, so we
// render a branded gradient tinted with the category colour plus its icon.
// Reused wherever a story hero image would appear (home card, preview,
// deep-dive, saved thumbnails) so lessons stay visually coherent with stories
// while being instantly recognisable.
import { View, Text, StyleSheet, StyleProp, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import { makeStyles, useTheme, radius, typography, spacing } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { KindIcon } from "./kind-icon";

export function LessonCover({
  color,
  icon,
  style,
  iconSize = 64,
  showBadge = true,
}: {
  color: string;
  icon: string;
  style?: StyleProp<ViewStyle>;
  iconSize?: number;
  showBadge?: boolean;
}) {
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <View style={[styles.wrap, style]}>
      <LinearGradient
        colors={[color + "4D", color + "1A", colors.surfaceSecondary]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={[styles.orb, { backgroundColor: color + "22", borderColor: color + "55", boxShadow: `0px 0px 24px ${color}80` }]}>
        <Ionicons name={icon as any} size={iconSize} color={color} />
      </View>
      {showBadge ? (
        <View style={[styles.badge, { borderColor: color + "66", backgroundColor: colors.surface + "CC" }]}>
          <KindIcon kind="lessons" size={18} glow={false} />
          <Text style={[styles.badgeText, { color }]}>{t.lesson_badge}</Text>
        </View>
      ) : null}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: {
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    backgroundColor: colors.surfaceSecondary,
  },
  orb: {
    alignItems: "center",
    justifyContent: "center",
    aspectRatio: 1,
    padding: spacing.lg,
    borderRadius: 999,
    borderWidth: 1,
  },
  badge: {
    position: "absolute",
    top: spacing.md,
    left: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: radius.pill,
    borderWidth: 1,
  },
  badgeText: { fontFamily: typography.bodyBold, fontSize: 9, letterSpacing: 1.5 },
}));
