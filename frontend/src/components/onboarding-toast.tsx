// PAUSE — onboarding: messaggio breve e curato (icona + titolo + riga di aiuto)
// che compare sopra il footer quando l'utente prova ad andare avanti senza
// aver scelto un formato o un argomento. Si chiude da solo.
import { useEffect } from "react";
import { View, Text } from "react-native";
import Animated, { FadeInDown, FadeOutDown, Easing } from "react-native-reanimated";
import Ionicons from "@react-native-vector-icons/ionicons";
import { makeStyles, useTheme, spacing, typography, radius, withAlpha } from "@/src/theme";

export type OnboardingNotice = { title: string; body: string; icon?: "grid-outline" | "layers-outline" | "lock-closed-outline" | "book-outline" };

export function OnboardingToast({
  notice, bottom, onHide, testID = "onboarding-toast",
}: { notice: OnboardingNotice | null; bottom: number; onHide: () => void; testID?: string }) {
  const styles = useStyles();
  const { colors } = useTheme();

  useEffect(() => {
    if (!notice) return;
    const id = setTimeout(onHide, 2800);
    return () => clearTimeout(id);
  }, [notice, onHide]);

  if (!notice) return null;
  return (
    <Animated.View
      pointerEvents="none"
      entering={FadeInDown.duration(300).easing(Easing.out(Easing.cubic))}
      exiting={FadeOutDown.duration(220)}
      style={[styles.wrap, { bottom }]}
      testID={testID}
      accessibilityLiveRegion="polite"
    >
      <View style={styles.iconWrap}>
        <Ionicons name={notice.icon ?? "grid-outline"} size={18} color={colors.brand} />
      </View>
      <View style={styles.text}>
        <Text style={styles.title} testID={`${testID}-title`}>{notice.title}</Text>
        <Text style={styles.body}>{notice.body}</Text>
      </View>
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: {
    position: "absolute", left: spacing.xl, right: spacing.xl,
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    padding: spacing.md, borderRadius: radius.lg,
    backgroundColor: colors.surfaceSecondary,
    borderWidth: 1, borderColor: withAlpha(colors.brand, 0.45),
    boxShadow: `0px 8px 28px ${withAlpha(colors.brand, 0.22)}` as any,
  },
  iconWrap: {
    width: 38, height: 38, borderRadius: 19, alignItems: "center", justifyContent: "center",
    backgroundColor: withAlpha(colors.brand, 0.12),
  },
  text: { flex: 1, gap: 2 },
  title: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 14 },
  body: { color: colors.onSurfaceSecondary, fontFamily: typography.body, fontSize: 12.5, lineHeight: 17 },
}));
