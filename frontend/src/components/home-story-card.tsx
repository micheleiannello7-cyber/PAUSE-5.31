import { useState } from "react";
import { View, Text, Pressable, StyleSheet, useWindowDimensions } from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { useAnimatedStyle, useSharedValue, withSpring, withTiming } from "react-native-reanimated";
import * as Haptics from "@/src/haptics";
import { StoryPreview, isLesson } from "@/src/api";
import { makeStyles, typography, useTheme, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { StoryHero } from "./story-hero";
import { HighlightedTitle } from "./highlighted-title";

export function HomeStoryCard({ story, active, instance, onOpen, onListen }: {
  story: StoryPreview; active: boolean; instance: string; onOpen: () => void; onListen?: () => void;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();
  const { width } = useWindowDimensions();
  const id = active ? `home-story-${story.id}` : `home-story-${story.id}-${instance}`;
  const lesson = isLesson(story);
  const fontSize = Math.min(31, Math.max(20, width * (story.title.length > 65 ? 0.056 : 0.062)));
  const label = lesson ? t.read_lesson : t.read_story;
  // Long-press preview: the hook slides up from the bottom while the finger is down.
  const preview = useSharedValue(0);
  const [panelHeight, setPanelHeight] = useState(160);
  const panelStyle = useAnimatedStyle(() => ({ transform: [{ translateY: (1 - preview.value) * panelHeight }], opacity: preview.value }));
  const bodyStyle = useAnimatedStyle(() => ({ opacity: 1 - preview.value }));
  const showPreview = () => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {}); preview.value = withSpring(1, { damping: 22, stiffness: 230, overshootClamping: true }); };
  const hidePreview = () => { preview.value = withTiming(0, { duration: 220 }); };
  return (
    <View style={styles.card} testID={active ? `story-card-${story.id}` : `deck-card-${story.id}-${instance}`}>
      <StoryHero story={story} style={StyleSheet.absoluteFill} iconSize={64} transition={0} />
      {/* Bottom scrim: title and badges always sit on a near-opaque dark band, whatever the artwork. */}
      <LinearGradient colors={[withAlpha(colors.artworkSurface, 0), withAlpha(colors.artworkSurface, 0.1), withAlpha(colors.artworkSurface, 0.86), withAlpha(colors.artworkSurface, 0.97)]}
        locations={[0, 0.42, 0.74, 1]} style={[StyleSheet.absoluteFill, styles.noTouch]} />
      <Pressable testID={`${id}-open`} style={StyleSheet.absoluteFill} onPress={onOpen} onLongPress={showPreview} onPressOut={hidePreview} delayLongPress={350}
        accessibilityRole="button" accessibilityLabel={`${label}: ${story.title}`} accessibilityHint={story.hook} />
      {/* Titolo in fondo alla card; i tre dati (tipo · categoria · durata)
          stanno sotto la card, nel mazzo (DeckBadges). */}
      <Animated.View style={[styles.body, bodyStyle]} pointerEvents="box-none">
        <View style={styles.titleRow} pointerEvents="box-none">
          <HighlightedTitle testID={`${id}-title`} title={story.title} highlight={story.highlight_words} style={[styles.title, { fontSize, lineHeight: fontSize * 1.14 }]}
            numberOfLines={4} adjustsFontSizeToFit minimumFontScale={0.8} />
          {onListen && <Pressable testID={active ? "home-listen-story" : `${id}-listen`} accessibilityRole="button" accessibilityLabel={t.audio_listen_short} onPress={onListen} style={styles.listen}>
            <Ionicons name="headset-outline" size={19} color={colors.cyan} />
          </Pressable>}
        </View>
      </Animated.View>
      <Animated.View testID={`${id}-preview`} style={[styles.panel, styles.noTouch, panelStyle]} pointerEvents="none"
        onLayout={({ nativeEvent }) => { const h = Math.ceil(nativeEvent.layout.height); if (h && h !== panelHeight) setPanelHeight(h); }}>
        <View style={styles.panelGrip} />
        <Text testID={`${id}-preview-title`} style={styles.panelTitle} numberOfLines={2}>{story.title}</Text>
        <Text testID={`${id}-hook`} style={styles.hook} numberOfLines={4}>{story.hook}</Text>
        <View style={styles.panelHintRow}>
          <Ionicons name="hand-left-outline" size={12} color={colors.cyan} />
          <Text testID={`${id}-preview-hint`} style={styles.panelHint}>{t.preview_release_hint}</Text>
        </View>
      </Animated.View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  // Bordo sottilissimo con luce ambientale nel colore del tema (riflesso, non neon).
  card: { flex: 1, borderRadius: 19, overflow: "hidden", justifyContent: "flex-end", backgroundColor: colors.artworkSurface, borderWidth: 1, borderColor: withAlpha(colors.brand, 0.42), boxShadow: `0px 0px 22px ${withAlpha(colors.brand, 0.16)}` as any },
  noTouch: { pointerEvents: "none" },
  body: { padding: 16, paddingBottom: 16, gap: 10, pointerEvents: "box-none" },
  titleRow: { flexDirection: "row", alignItems: "flex-end", gap: 10, pointerEvents: "box-none" },
  title: {
    flex: 1, color: colors.onGradient, fontFamily: typography.displayBold, letterSpacing: -0.6, pointerEvents: "none",
    textShadowColor: withAlpha(colors.artworkSurface, 0.85), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 6,
  },
  listen: { width: 44, minHeight: 44, borderRadius: 24, borderWidth: 1, borderColor: colors.glassBorderStrong, backgroundColor: colors.scrim, alignItems: "center", justifyContent: "center" },
  panel: {
    position: "absolute", left: 0, right: 0, bottom: 0, padding: 16, paddingTop: 10, gap: 8,
    borderTopLeftRadius: 19, borderTopRightRadius: 19, borderTopWidth: 1, borderColor: withAlpha(colors.cyanSoft, 0.5),
    backgroundColor: withAlpha(colors.artworkSurface, 0.96),
  },
  panelGrip: { alignSelf: "center", width: 34, height: 4, borderRadius: 2, backgroundColor: withAlpha(colors.onGradient, 0.35), marginBottom: 2 },
  panelTitle: { color: colors.onGradient, fontFamily: typography.displayBold, fontSize: 16, lineHeight: 20 },
  hook: { color: withAlpha(colors.onGradient, 0.92), fontFamily: typography.body, fontSize: 13.5, lineHeight: 19 },
  panelHintRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 2 },
  panelHint: { color: colors.cyan, fontFamily: typography.bodyMedium, fontSize: 10.5, letterSpacing: 0.3 },
}));
