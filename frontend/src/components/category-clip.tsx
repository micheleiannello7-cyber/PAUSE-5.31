// PAUSE — clip "hero" di una categoria (~3s, generato in image-to-video dalla
// stessa illustrazione): al tocco della tile il video si sovrappone
// all'immagine con una dissolvenza, gira una volta e poi svanisce lasciando
// di nuovo l'illustrazione ferma. Muto, senza controlli.
import { useEffect } from "react";
import { StyleSheet } from "react-native";
import { useVideoPlayer, VideoView } from "expo-video";
import { useEvent } from "expo";
import Animated, { FadeIn, FadeOut } from "react-native-reanimated";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/src/api";

/** id categoria → URL assoluto del clip (solo quelle generate). */
export function useCategoryClips() {
  const { data } = useQuery({ queryKey: ["category-clips"], queryFn: api.categoryClips, staleTime: 60 * 60 * 1000 });
  return data ?? {};
}

export function CategoryClip({ uri, onEnd, testID }: { uri: string; onEnd: () => void; testID: string }) {
  const player = useVideoPlayer(uri, (p) => {
    p.loop = false;
    p.muted = true;
    p.play();
  });
  const { status } = useEvent(player, "statusChange", { status: player.status });
  const { isPlaying } = useEvent(player, "playingChange", { isPlaying: player.playing });

  // Fine clip (o errore di caricamento): si torna all'illustrazione ferma.
  useEffect(() => {
    if (status === "error") onEnd();
  }, [status, onEnd]);
  useEffect(() => {
    if (status === "readyToPlay" && !isPlaying && player.currentTime > 0.5) onEnd();
  }, [status, isPlaying, player, onEnd]);

  return (
    <Animated.View entering={FadeIn.duration(220)} exiting={FadeOut.duration(320)} style={StyleSheet.absoluteFill} pointerEvents="none" testID={testID}>
      <VideoView player={player} style={StyleSheet.absoluteFill} contentFit="cover" nativeControls={false} />
    </Animated.View>
  );
}
