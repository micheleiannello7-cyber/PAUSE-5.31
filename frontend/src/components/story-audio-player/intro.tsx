import { useRef } from "react";
import { View, LayoutChangeEvent, StyleProp, ViewStyle } from "react-native";
import { spacing } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { IntroCtaButton } from "@/src/components/intro-cta-button";
import { useAudio } from "./context";
import { AudioCard } from "./audio-card";

// "Ascolta" dell'introduzione: stesso componente e stessa misura di
// "Leggi", con le cuffie 3D. Avvia la narrazione e apre il player.
export function IntroListenButton({ onListen, style, testID = "deep-dive-listen-ai" }:
  { onListen: () => void; style?: StyleProp<ViewStyle>; testID?: string }) {
  const { t } = useI18n();
  const a = useAudio();
  if (!a.isPremium) return null;
  return <IntroCtaButton testID={testID} icon="headphones" label={t.audio_listen_short} loading={a.buffering} style={style}
    onPress={() => { if (!a.playing) a.togglePlay(); onListen(); }} />;
}

export function InFlowAudioCard({ testID = "deep-dive-audio-player" }: { testID?: string }) {
  const ref = useRef<View>(null);
  const { cardScreenYSV, cardHeightSV, isPremium } = useAudio();
  const onLayout = (e: LayoutChangeEvent) => {
    cardHeightSV.value = e.nativeEvent.layout.height;
    ref.current?.measureInWindow((_x, y, _w, height) => {
      cardScreenYSV.value = y;
      cardHeightSV.value = height;
    });
  };
  if (!isPremium) return null;
  return <View ref={ref} onLayout={onLayout} style={{ marginTop: spacing.sm }}><AudioCard testID={testID} /></View>;
}
