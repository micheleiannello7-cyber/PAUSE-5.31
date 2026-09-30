// PAUSE — conferma ampia del salvataggio nella schermata finale della storia.
// Banner fisso rispetto allo schermo (vive nel deep-dive, fuori dallo scroll),
// centrato in basso e ben visibile: disco cyan con il segnalibro + testo
// "Aggiunto ai salvati". Compare al tocco e si ritira da solo. Colori dal tema.
import { useEffect, useRef, useState } from "react";
import { View, Text } from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import Animated, { FadeInDown, FadeOutDown } from "react-native-reanimated";

import { makeStyles, useTheme, spacing, radius, typography, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";

/** Valore che, cambiando, fa comparire il banner: { saved, n } dove n cresce a
 *  ogni tocco così anche due salvataggi uguali di fila riattivano l'animazione. */
export function SaveConfirmToast({ trigger, bottomInset }: {
  trigger: { saved: boolean; n: number } | null;
  bottomInset: number;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();
  const [shown, setShown] = useState<{ saved: boolean } | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!trigger) return;
    setShown({ saved: trigger.saved });
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setShown(null), 2000);
  }, [trigger]);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  if (!shown) return null;

  return (
    <Animated.View
      key={trigger?.n}
      entering={FadeInDown.springify().damping(16).mass(0.7)}
      exiting={FadeOutDown.duration(220)}
      pointerEvents="none"
      style={[styles.wrap, { bottom: bottomInset + spacing.xxl }]}
      testID="save-confirm"
    >
      <View style={[styles.pill, { borderColor: withAlpha(colors.cyan, shown.saved ? 0.55 : 0.3) }]}>
        <View style={[styles.icon, { backgroundColor: shown.saved ? colors.cyan : colors.surfaceTertiary }]}>
          <Ionicons name={shown.saved ? "bookmark" : "bookmark-outline"} size={18} color={shown.saved ? colors.onGradient : colors.onSurfaceSecondary} />
        </View>
        <Text style={styles.text} numberOfLines={1}>{shown.saved ? t.saved_confirm : t.unsaved_confirm}</Text>
      </View>
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: { position: "absolute", left: 0, right: 0, alignItems: "center" },
  pill: {
    flexDirection: "row", alignItems: "center", gap: spacing.sm + 2,
    paddingLeft: 8, paddingRight: 20, height: 52, borderRadius: radius.pill, borderWidth: 1,
    backgroundColor: colors.glassBgStrong,
    boxShadow: `0px 12px 30px ${colors.glassShadow}` as any,
  },
  icon: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    boxShadow: `0px 0px 16px ${colors.cyanGlow}` as any,
  },
  text: { color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 15, letterSpacing: 0.2 },
}));
