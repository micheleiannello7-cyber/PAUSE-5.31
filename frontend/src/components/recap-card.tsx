import { View, Text } from "react-native";

import { StoryRecap } from "@/src/api";
import { makeStyles, spacing, radius, typography } from "@/src/theme";
import { StoryHero } from "@/src/components/story-hero";

// Card of the session recap: thumbnail + category + title (no summary/intro).
// Shared between /pause-limit and /read-stories.
export function RecapCard({ story, index }: { story: StoryRecap; index: number }) {
  const styles = useStyles();
  return (
    <View style={styles.card} testID={`recap-${story.id}`}>
      <View style={styles.head}>
        <StoryHero story={story} style={styles.thumb} iconSize={22} size="thumb" />
        <View style={{ flex: 1 }}>
          <Text style={styles.meta}>{index} · {story.category_name.toUpperCase()}</Text>
          <Text style={styles.title} numberOfLines={2}>{story.title}</Text>
        </View>
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  card: {
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
    borderRadius: radius.lg, overflow: "hidden",
  },
  head: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md },
  thumb: { width: 56, height: 56, borderRadius: radius.md, backgroundColor: colors.surfaceTertiary, overflow: "hidden" },
  meta: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1.5, marginBottom: 3 },
  title: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 14, lineHeight: 19 },
}));
