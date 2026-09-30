// PAUSE — i tre dati della storia (Tipo · Categoria · Durata) sotto la card
// della Home, nello stesso "vetro" della scheda del lettore (StoryInfoGrid
// inline): al cambio card il blocco sfuma e risale con i dati della nuova.
import { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import Animated, { cancelAnimation, runOnJS, useAnimatedStyle, useSharedValue, withTiming } from "react-native-reanimated";
import { StoryPreview } from "@/src/api";
import { StoryInfoGrid } from "./story-info-grid";

// Geometria condivisa con la transizione verso il lettore (story-morph).
export const DECK_BADGES_GAP = 10;
export const DECK_BADGES_H = 54;

export function DeckBadges({ story, width }: { story: StoryPreview; width: number }) {
  const [shown, setShown] = useState(story);
  const opacity = useSharedValue(1);
  const lift = useSharedValue(0);

  // Nuova card: dissolvenza in uscita, poi si cambiano i dati.
  useEffect(() => {
    if (shown.id === story.id) return;
    cancelAnimation(opacity);
    opacity.value = withTiming(0, { duration: 110 }, (done) => { if (done) runOnJS(setShown)(story); });
  }, [story, shown.id, opacity]);
  // Dati cambiati: rientrano con una dissolvenza e un lieve movimento dal basso.
  useEffect(() => {
    lift.value = 6;
    lift.value = withTiming(0, { duration: 260 });
    opacity.value = withTiming(1, { duration: 240 });
  }, [shown, opacity, lift]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value, transform: [{ translateY: lift.value }] }));
  return (
    <View style={[styles.slot, { width }]} testID="deck-badges" pointerEvents="none">
      <Animated.View style={[styles.grid, style]} testID={`deck-badges-${shown.id}`}>
        <StoryInfoGrid story={shown} minutes={shown.reading_time_min} inline testID="home-story-meta" />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  slot: { height: DECK_BADGES_H, marginTop: DECK_BADGES_GAP, alignSelf: "center", justifyContent: "center" },
  grid: { alignSelf: "stretch" },
});
