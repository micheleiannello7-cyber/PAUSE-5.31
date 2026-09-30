// PAUSE — tasto di fine storia (Mi piace / Salva / Condividi): vetro del tema,
// tinta dell'azione quando è attivo, piccolo rimbalzo al tocco e conferma
// breve ("Salvato", "Ti piace") che compare sopra il tasto stesso, con una
// vibrazione leggera. Tutti i colori vengono dal tema (chiaro/scuro).
import { useEffect, useRef, useState } from "react";
import { Text, Pressable, StyleProp, ViewStyle } from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import Animated, {
  FadeInDown, FadeOutUp, useSharedValue, useAnimatedStyle, withSequence, withSpring, withTiming, interpolateColor,
} from "react-native-reanimated";
import * as Haptics from "@/src/haptics";

import { makeStyles, useTheme, radius, typography, spacing, withAlpha } from "@/src/theme";

type IconName = "heart" | "heart-outline" | "bookmark" | "bookmark-outline" | "share-outline";

export function EndActionButton({
  icon, label, active = false, tint, toastText, onPress, style, testID, accessibilityLabel,
}: {
  icon: IconName;
  label: string;
  /** Stato attivo (già salvato / già piaciuto): bordo e icona nella tinta. */
  active?: boolean;
  /** Colore dell'azione (es. colors.error per il cuore, colors.cyan per il segnalibro). */
  tint?: string;
  /** Testo della conferma da mostrare sopra il tasto dopo il tocco. */
  toastText?: string;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
  accessibilityLabel?: string;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const accent = tint ?? colors.cyan;
  // Colori con alpha calcolati sul thread JS: dentro il worklet di
  // useAnimatedStyle non si possono chiamare funzioni non-worklet (withAlpha),
  // altrimenti su nativo Reanimated crasha ("call a Remote Function").
  const accentBorder = withAlpha(accent, 0.6);
  const accentBg = withAlpha(accent, 0.16);
  const scale = useSharedValue(1);
  const on = useSharedValue(active ? 1 : 0);
  const [toast, setToast] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { on.value = withTiming(active ? 1 : 0, { duration: 260 }); }, [active, on]);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const press = () => {
    scale.value = withSequence(withTiming(0.92, { duration: 80 }), withSpring(1, { damping: 9, stiffness: 260 }));
    if (toastText) {
      Haptics.notificationAsync(active ? Haptics.NotificationFeedbackType.Warning : Haptics.NotificationFeedbackType.Success).catch(() => {});
      setToast(toastText);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setToast(null), 1400);
    }
    onPress();
  };

  const surface = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    borderColor: interpolateColor(on.value, [0, 1], [colors.glassBorderStrong, accentBorder]),
    backgroundColor: interpolateColor(on.value, [0, 1], [colors.glassBgLit, accentBg]),
  }));

  return (
    <Animated.View style={[styles.wrap, style]}>
      {toast ? (
        <Animated.View
          entering={FadeInDown.duration(200)}
          exiting={FadeOutUp.duration(180)}
          style={[styles.toast, { borderColor: withAlpha(accent, 0.5) }]}
          pointerEvents="none"
          testID={testID ? `${testID}-toast` : undefined}
        >
          <Text style={[styles.toastText, { color: accent }]} numberOfLines={1}>{toast}</Text>
        </Animated.View>
      ) : null}
      <Pressable
        onPress={press}
        hitSlop={8}
        testID={testID}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel ?? label}
        accessibilityState={{ selected: active }}
        style={styles.press}
      >
        <Animated.View style={[styles.btn, surface]}>
          <Ionicons name={icon} size={18} color={active ? accent : colors.textWarm} />
          <Text style={[styles.label, active && { color: accent }]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.6}>{label}</Text>
        </Animated.View>
      </Pressable>
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: { position: "relative" },
  press: { alignSelf: "stretch" },
  btn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    minHeight: 50, paddingHorizontal: spacing.sm, borderRadius: radius.pill, borderWidth: 1,
    boxShadow: `0px 6px 16px ${colors.glassShadow}` as any,
  },
  label: { flexShrink: 1, color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 13.5, letterSpacing: 0 },
  toast: {
    position: "absolute", left: 0, right: 0, top: -40, alignItems: "center", alignSelf: "center", zIndex: 5,
    marginHorizontal: spacing.sm, paddingHorizontal: 12, minHeight: 30, justifyContent: "center",
    borderRadius: radius.pill, borderWidth: 1, backgroundColor: colors.glassBgStrong,
    boxShadow: `0px 6px 18px ${colors.glassShadow}` as any,
  },
  toastText: { fontFamily: typography.bodyBold, fontSize: 12.5, letterSpacing: 0.3 },
}));
