// PAUSE — Small pill telling a "Curiosità" (quick read) apart from a
// "Mini lezione" (guided steps + objective). Rendered on every card / header
// where a story appears so the two formats are recognisable at a glance.
import { View, Text, StyleProp, ViewStyle } from "react-native";

import { StoryPreview, isLesson } from "@/src/api";
import { makeStyles, useTheme, typography, radius } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { KindIcon } from "./kind-icon";

export function KindBadge({
  story, style, size = "md", overlay = false,
}: {
  story: StoryPreview;
  style?: StyleProp<ViewStyle>;
  size?: "sm" | "md";
  /** Over a photo: dark translucent background instead of tinted surface. */
  overlay?: boolean;
}) {
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const lesson = isLesson(story);
  const tint = lesson ? colors.warning : colors.brand;
  const small = size === "sm";
  return (
    <View
      testID={`kind-badge-${lesson ? "lesson" : "story"}`}
      style={[
        styles.pill,
        small && styles.pillSm,
        overlay
          ? { backgroundColor: colors.glassBgLit, borderColor: tint + "66", boxShadow: `0px 4px 12px ${colors.glassShadow}` as any }
          : { backgroundColor: tint + "1A", borderColor: tint + "66" },
        style,
      ]}
    >
      <KindIcon kind={lesson ? "lessons" : "stories"} size={small ? 16 : 20} glow={false} />
      <Text style={[styles.text, small && styles.textSm, { color: tint }]}>
        {lesson ? t.lesson_badge : t.curiosity_badge}
      </Text>
    </View>
  );
}

const useStyles = makeStyles(() => ({
  pill: {
    alignSelf: "flex-start",
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingLeft: 5, paddingRight: 9, paddingVertical: 3,
    borderRadius: radius.pill, borderWidth: 1,
  },
  pillSm: { paddingLeft: 4, paddingRight: 7, paddingVertical: 2, gap: 4 },
  text: { fontFamily: typography.bodyBold, fontSize: 9.5, letterSpacing: 1.4 },
  textSm: { fontSize: 8.5, letterSpacing: 1.2 },
}));
