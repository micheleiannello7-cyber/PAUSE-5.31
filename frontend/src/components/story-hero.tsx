// PAUSE — cover of a story wherever a hero image appears (home card, preview,
// deep-dive, thumbnails). Uses the photo when the story has one, otherwise a
// branded gradient tinted with the category colour and its icon.
import { useId, useState } from "react";
import { View, StyleSheet, StyleProp, ViewStyle } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";

import { StoryPreview, heroUrl } from "@/src/api";
import { makeStyles, spacing } from "@/src/theme";

export function StoryHero({
  story, style, iconSize = 64, transition = 200, size = "hero",
}: {
  story: StoryPreview;
  style?: StyleProp<ViewStyle>;
  iconSize?: number;
  transition?: number;
  /** "thumb" requests the ≤600px variant for list thumbnails. */
  size?: "hero" | "thumb";
}) {
  const styles = useStyles();
  const instance = useId();
  const [failedUris, setFailedUris] = useState<string[]>([]);
  const generated = heroUrl(story, size);
  const photo = heroUrl({ ...story, hero_image_generated: null, hero_image_thumb: null }, size);
  const uri = [generated, photo].find((candidate) => candidate && !failedUris.includes(candidate));
  const testID = `story-hero-${story.id}-${size}-${instance}`;
  if (uri) {
    return (
      <Image
        testID={`${testID}-image`} accessibilityLabel={story.title}
        source={{ uri }} style={style} contentFit="cover" transition={transition}
        cachePolicy="memory-disk" recyclingKey={uri}
        onError={() => setFailedUris((current) => current.includes(uri) ? current : [...current, uri])}
      />
    );
  }
  const color = story.category_color;
  return (
    <View testID={`${testID}-fallback`} accessibilityLabel={story.title} style={[styles.wrap, style]}>
      <LinearGradient
        colors={[color + "66", color + "22", color + "00"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={[styles.orb, { backgroundColor: color + "22", borderColor: color + "55", boxShadow: `0px 0px 24px ${color}80` }]}>
        <Ionicons name={story.category_icon as any} size={iconSize} color={color} />
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: {
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    backgroundColor: colors.surfaceTertiary,
  },
  orb: {
    alignItems: "center",
    justifyContent: "center",
    aspectRatio: 1,
    padding: spacing.lg,
    borderRadius: 999,
    borderWidth: 1,
  },
}));
