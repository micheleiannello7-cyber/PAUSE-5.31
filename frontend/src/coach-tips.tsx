// PAUSE — mini guida non invasiva: piccoli suggerimenti contestuali mostrati
// solo nei primi 3 avvii dell'app. Ogni tip compare una volta per avvio, si
// chiude da solo dopo qualche secondo o con un tocco.
import React, { useEffect, useState } from "react";
import { Text, Pressable, StyleProp, ViewStyle, Platform, View } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Animated, { Easing, FadeInUp, FadeOutDown } from "react-native-reanimated";
import Ionicons from "@react-native-vector-icons/ionicons";

import { makeStyles, useTheme, spacing, radius, typography } from "@/src/theme";
import { useI18n } from "@/src/i18n";

const LAUNCHES_KEY = "pause.launches";
const MAX_GUIDED_LAUNCHES = 3;
const SHOW_DELAY_MS = 900;
const AUTO_HIDE_MS = 8000;

let launchCount: number | null = null;
let launchPromise: Promise<number> | null = null;
const shownThisSession = new Set<string>();

// Da chiamare una volta per avvio: incrementa il contatore persistente.
export function registerLaunch(): Promise<number> {
  if (launchPromise) return launchPromise;
  launchPromise = (async () => {
    let n = 1;
    try {
      const raw = await AsyncStorage.getItem(LAUNCHES_KEY);
      n = (raw ? parseInt(raw, 10) || 0 : 0) + 1;
      await AsyncStorage.setItem(LAUNCHES_KEY, String(n));
    } catch {}
    launchCount = n;
    return n;
  })();
  return launchPromise;
}

// true se il tip `id` va mostrato ora (primi 3 avvii, non ancora visto in questa sessione).
function useCoachTip(id: string) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    let alive = true;
    let hideTimer: ReturnType<typeof setTimeout> | undefined;
    const showTimer = setTimeout(async () => {
      const n = launchCount ?? (await registerLaunch());
      if (!alive || n > MAX_GUIDED_LAUNCHES || shownThisSession.has(id)) return;
      shownThisSession.add(id);
      setVisible(true);
      hideTimer = setTimeout(() => alive && setVisible(false), AUTO_HIDE_MS);
    }, SHOW_DELAY_MS);
    return () => {
      alive = false;
      clearTimeout(showTimer);
      if (hideTimer) clearTimeout(hideTimer);
    };
  }, [id]);
  return { visible, dismiss: () => setVisible(false) };
}

export function CoachTip({
  id, text, icon = "bulb-outline", style, testID,
}: { id: string; text: string; icon?: string; style?: StyleProp<ViewStyle>; testID?: string }) {
  const { visible, dismiss } = useCoachTip(id);
  const styles = useStyles();
  const { colors } = useTheme();
  const { lang } = useI18n();
  if (!visible) return null;
  const bubble = (
    <Pressable testID={`coach-dismiss-${id}`} onPress={(event) => { event.stopPropagation(); dismiss(); }}
      style={styles.bubble} accessibilityRole="button" accessibilityLabel={lang === "it" ? "Chiudi suggerimento" : "Dismiss tip"}>
      <Ionicons name={icon as any} size={16} color={colors.brand} />
      <Text style={styles.text}>{text}</Text>
      <Ionicons name="close" size={14} color={colors.muted} />
    </Pressable>
  );
  // Web exiting-layout clones can expand document width and scroll it sideways.
  if (Platform.OS === "web") {
    return <View style={[styles.wrap, style]} testID={testID ?? `coach-tip-${id}`}>{bubble}</View>;
  }
  return (
    <Animated.View
      entering={FadeInUp.duration(320).easing(Easing.linear)}
      exiting={FadeOutDown.duration(220).easing(Easing.linear)}
      style={[styles.wrap, style]}
      testID={testID ?? `coach-tip-${id}`}
    >
      {bubble}
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: { position: "absolute", left: spacing.lg, right: spacing.lg, zIndex: 50, alignItems: "center" },
  bubble: {
    flexDirection: "row", alignItems: "center", gap: spacing.sm,
    paddingVertical: 10, paddingHorizontal: spacing.md, borderRadius: radius.lg,
    backgroundColor: colors.overlayStrong, borderWidth: 1, borderColor: colors.brand + "66",
    boxShadow: "0px 8px 20px rgba(0,0,0,0.35)", elevation: 8,
  },
  text: { flex: 1, color: colors.onSurface, fontFamily: typography.bodyMedium, fontSize: 12, lineHeight: 17 },
}));
