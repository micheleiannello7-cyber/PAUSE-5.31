// PAUSE — Story audio player: badge piccolo che riapre il player. Vive nella
// barra in alto, a destra, alla quota della riga "3 DI 7 + barra" (mai sopra
// il titolo, mai sopra il testo). Compare solo dopo che l'utente ha toccato
// "Ascolta" e il foglio è chiuso. Cuffie 3D + equalizzatore quando la voce
// sta leggendo; bordo azzurro in riproduzione.

import { useEffect } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { BlurView } from "expo-blur";
import { Image } from "expo-image";
import Animated, {
  Easing, useAnimatedStyle, useSharedValue, withDelay, withRepeat, withSequence, withSpring, withTiming,
} from "react-native-reanimated";

import { makeStyles, useTheme, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { useAudio } from "./context";

const HEADPHONES = require("../../../assets/images/kind-headphones.png");
const SIZE = 34;

export function AudioMiniBadge({ visible, onPress, testID = "audio-mini-badge" }: {
  visible: boolean; onPress: () => void; testID?: string;
}) {
  const styles = useStyles();
  const { colors, scheme } = useTheme();
  const { t } = useI18n();
  const { playing, buffering, isPremium } = useAudio();
  const shown = useSharedValue(0);
  useEffect(() => {
    shown.value = visible ? withSpring(1, { damping: 16, stiffness: 180 }) : withTiming(0, { duration: 180 });
  }, [visible, shown]);
  const wrapStyle = useAnimatedStyle(() => ({
    opacity: shown.value,
    transform: [{ scale: 0.7 + shown.value * 0.3 }],
  }));
  if (!isPremium) return null;
  return (
    <Animated.View style={wrapStyle} pointerEvents={visible ? "auto" : "none"} testID={`${testID}-wrap`}>
      <Pressable testID={testID} onPress={onPress} accessibilityRole="button" accessibilityLabel={t.audio_listen_short}
        hitSlop={10} style={({ pressed }) => [styles.badge, { borderColor: playing ? withAlpha(colors.cyan, 0.9) : withAlpha(colors.onGradient, 0.22) }, pressed && styles.pressed]}>
        <BlurView pointerEvents="none" tint={scheme === "dark" ? "dark" : "light"} intensity={30} style={StyleSheet.absoluteFill} />
        <Image source={HEADPHONES} style={styles.art} contentFit="contain" transition={0} />
        <View style={styles.status} testID={`${testID}-status`}>
          {buffering ? <ActivityIndicator size="small" color={colors.cyan} style={styles.spinner} /> : playing ? <Equalizer color={colors.cyan} /> : null}
        </View>
      </Pressable>
    </Animated.View>
  );
}

// Tre barrette che "respirano" in sequenza mentre la voce sta leggendo.
function Equalizer({ color }: { color: string }) {
  const styles = useStyles();
  return (
    <View style={styles.eq} testID="audio-mini-badge-equalizer">
      {[0, 1, 2].map((i) => <Bar key={i} delay={i * 140} color={color} />)}
    </View>
  );
}

function Bar({ delay, color }: { delay: number; color: string }) {
  const styles = useStyles();
  const h = useSharedValue(0.4);
  useEffect(() => {
    h.value = withDelay(delay, withRepeat(withSequence(
      withTiming(1, { duration: 320, easing: Easing.inOut(Easing.quad) }),
      withTiming(0.35, { duration: 320, easing: Easing.inOut(Easing.quad) }),
    ), -1, true));
  }, [delay, h]);
  const style = useAnimatedStyle(() => ({ transform: [{ scaleY: h.value }] }));
  return <Animated.View style={[styles.bar, { backgroundColor: color }, style]} />;
}

const useStyles = makeStyles((colors) => ({
  badge: {
    width: SIZE, height: SIZE, borderRadius: SIZE / 2, alignItems: "center", justifyContent: "center", overflow: "hidden",
    backgroundColor: withAlpha(colors.artworkSurface, 0.55), borderWidth: 1,
  },
  pressed: { opacity: 0.85, transform: [{ scale: 0.95 }] },
  art: { width: SIZE * 0.62, height: SIZE * 0.62 },
  status: { position: "absolute", right: 2, bottom: 2, width: 12, height: 12, alignItems: "center", justifyContent: "center" },
  spinner: { transform: [{ scale: 0.5 }] },
  eq: { flexDirection: "row", alignItems: "flex-end", gap: 1.5, height: 8 },
  bar: { width: 2, height: 8, borderRadius: 1, transformOrigin: "bottom" },
}));
