// PAUSE — Shareable story card. Rendered off-screen inside a ViewShot and
// captured as a PNG when the reader taps "Condividi": cover, category, title,
// hook and the PΛUSE brand, ready to send to friends. The card is a brand
// asset: it always uses the dark palette so it looks identical whatever theme
// the sender has picked.
import { View, Text, StyleSheet } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";

import { Story, heroUrl, isLesson } from "@/src/api";
import { useTheme, typography, radius, spacing } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { PauseMark } from "@/src/components/pause-logo";
import { LessonCover } from "@/src/components/lesson-cover";

export const SHARE_CARD_WIDTH = 360;
const CARD_BG = "#05070C";
const CARD_TEXT = "#F4F5F8";
const CARD_TEXT_SOFT = "rgba(244,245,248,0.78)";

export function StoryShareCard({ story }: { story: Story }) {
  const { colors } = useTheme();
  const { t } = useI18n();
  const accent = story.category_color;
  return (
    <View style={styles.card} testID="story-share-card">
      <View style={styles.hero}>
        {isLesson(story) && !story.hero_image_generated ? (
          <LessonCover color={accent} icon={story.category_icon} iconSize={64} showBadge={false} style={StyleSheet.absoluteFill} />
        ) : (
          <Image source={{ uri: heroUrl(story) }} style={StyleSheet.absoluteFill} contentFit="cover" cachePolicy="memory-disk" />
        )}
        <LinearGradient
          colors={["rgba(5,7,12,0.15)", "rgba(5,7,12,0.35)", CARD_BG]}
          locations={[0, 0.6, 1]}
          style={StyleSheet.absoluteFill}
        />
        <View style={[styles.chip, { backgroundColor: accent }]}>
          <Ionicons name={story.category_icon as any} size={11} color={CARD_BG} />
          <Text style={styles.chipText}>{story.category_name.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.body}>
        <Text style={styles.title}>{story.title}</Text>
        <View style={[styles.rule, { backgroundColor: accent }]} />
        <Text style={styles.hook} numberOfLines={4}>{story.hook}</Text>
      </View>

      <View style={styles.footer}>
        <View style={styles.brandRow}>
          <PauseMark size={26} />
          <Text style={styles.wordmark}>PΛUSE</Text>
        </View>
        <View style={{ flex: 1, alignItems: "flex-end" }}>
          <Text style={[styles.cta, { color: colors.gradient[1] }]}>{t.share_card_cta}</Text>
          <Text style={styles.tagline}>{t.tagline}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { width: SHARE_CARD_WIDTH, backgroundColor: CARD_BG, borderRadius: radius.lg, overflow: "hidden" },
  hero: { height: 230, justifyContent: "flex-end", padding: spacing.lg },
  chip: {
    alignSelf: "flex-start", flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: radius.pill,
  },
  chipText: { color: CARD_BG, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1.4 },
  body: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, gap: spacing.sm + 2 },
  title: { color: CARD_TEXT, fontFamily: typography.displayBold, fontSize: 24, lineHeight: 30 },
  rule: { width: 40, height: 3, borderRadius: 2 },
  hook: { color: CARD_TEXT_SOFT, fontFamily: typography.body, fontSize: 14, lineHeight: 21 },
  footer: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    padding: spacing.lg, marginTop: spacing.sm,
    borderTopWidth: 1, borderTopColor: "rgba(244,245,248,0.10)",
  },
  brandRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  wordmark: { color: CARD_TEXT, fontFamily: typography.displayBold, fontSize: 15, letterSpacing: 4 },
  cta: { fontFamily: typography.bodyBold, fontSize: 11 },
  tagline: { color: CARD_TEXT_SOFT, fontFamily: typography.body, fontSize: 9, letterSpacing: 1.2, marginTop: 2 },
});
