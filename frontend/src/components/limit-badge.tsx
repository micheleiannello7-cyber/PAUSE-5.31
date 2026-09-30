// PAUSE — "storie disponibili": indicatore dei crediti di lettura, in ogni
// header (Home, Argomenti, Salvati). Libro 3D (asset dell'app) + numero di
// storie disponibili + uno slot per credito (l'ultimo slot Premium è dorato) +
// countdown al prossimo credito quando la ricarica è in corso (+1 ogni 2 h
// base, +1 ogni ora Premium).
// Con 0 crediti diventa il tasto verso la schermata di pausa.
import { useCallback, useEffect, useRef, useState } from "react";
import { View, Text, Pressable } from "react-native";
import { Image } from "expo-image";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";
import { makeStyles, useTheme, radius, typography, withAlpha } from "@/src/theme";
import { useLimitGate } from "@/src/hooks/use-limit-gate";
import { useI18n } from "@/src/i18n";

const BOOK = require("../../assets/images/kind-book.png");

export function formatCountdown(totalSeconds: number): string {
  const s = Math.max(0, totalSeconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = m.toString().padStart(2, "0");
  const ss = sec.toString().padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

// Il countdown resta visibile per questo tempo dopo un tocco (Home).
const TIMER_PEEK_MS = 5000;

export function LimitBadge({ testID = "limit-badge", timerOnTap = false }: {
  testID?: string;
  /** Home: il countdown è nascosto e compare solo toccando l'indicatore; un
      secondo tocco (col countdown visibile) apre le storie lette. */
  timerOnTap?: boolean;
}) {
  const router = useRouter();
  const qc = useQueryClient();
  const data = useLimitGate();
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const [now, setNow] = useState(Date.now());
  const [peek, setPeek] = useState(false);
  const peekTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => { if (peekTimer.current) clearTimeout(peekTimer.current); }, []);
  // La schermata resta montata sotto il lettore e durante le transizioni:
  // il countdown avanza solo quando è davvero visibile (niente lavoro sul
  // thread JS mentre qualcos'altro si muove).
  const [focused, setFocused] = useState(true);
  useFocusEffect(useCallback(() => { setFocused(true); return () => setFocused(false); }, []));

  const cap = data?.capacity ?? 4;
  const credits = Math.max(0, Math.min(cap, data?.credits ?? cap));
  const nextAtMs = data?.next_credit_at ? Date.parse(data.next_credit_at) : 0;
  const recharging = !!data && credits < cap && nextAtMs > 0;
  const blocked = !!data?.enforce && credits === 0;

  // Tick every second while a credit is recharging; when the countdown ends,
  // ask the backend once so the new credit shows up right away.
  useEffect(() => {
    if (!recharging || !focused) return;
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [recharging, focused]);
  const firedFor = useRef(0);
  useEffect(() => {
    if (!recharging || now < nextAtMs || firedFor.current === nextAtMs) return;
    firedFor.current = nextAtMs;
    qc.invalidateQueries({ queryKey: ["limit"] });
  }, [now, nextAtMs, recharging, qc]);

  if (!data) return null;

  const accent = blocked ? colors.brandSecondary : credits === 1 ? colors.warning : colors.brand;
  const remaining = Math.floor((nextAtMs - now) / 1000);
  const showTimer = recharging && (!timerOnTap || peek);
  const onPress = () => {
    if (blocked) { router.push("/pause-limit"); return; }
    if (timerOnTap && recharging && !peek) {
      setPeek(true);
      if (peekTimer.current) clearTimeout(peekTimer.current);
      peekTimer.current = setTimeout(() => setPeek(false), TIMER_PEEK_MS);
      return;
    }
    router.push("/read-stories");
  };

  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={t.credits_a11y(credits, cap)}
      hitSlop={{ top: 8, bottom: 8, left: 6, right: 6 }}
      onPress={onPress}
      style={({ pressed }) => [styles.pill, { borderColor: withAlpha(accent, blocked ? 0.55 : 0.3) }, pressed && styles.pressed]}
    >
      <View style={styles.bookWrap}>
        <View pointerEvents="none" style={[styles.bookGlow, { backgroundColor: withAlpha(accent, 0.35), boxShadow: `0px 0px 10px ${withAlpha(accent, 0.7)}` as any }]} />
        <Image source={BOOK} style={styles.book} contentFit="contain" transition={0} />
      </View>
      <Text testID={`${testID}-count`} style={[styles.count, { color: accent }]}>{credits}</Text>
      <View style={styles.slots} testID={`${testID}-slots`}>
        {Array.from({ length: cap }).map((_, i) => {
          const on = i < credits;
          const premiumSlot = !!data.is_premium && i === cap - 1;
          const slotColor = premiumSlot ? colors.warning : accent;
          return (
            <View
              key={i}
              testID={`${testID}-slot-${i}${on ? "-on" : "-off"}${premiumSlot ? "-premium" : ""}`}
              style={[
                styles.slot,
                premiumSlot && styles.slotPremium,
                on
                  ? { backgroundColor: slotColor, borderColor: slotColor, boxShadow: `0px 0px 6px ${withAlpha(slotColor, 0.85)}` as any }
                  : { backgroundColor: "transparent", borderColor: withAlpha(slotColor, 0.45) },
              ]}
            />
          );
        })}
      </View>
      {showTimer ? (
        <View style={styles.timer} testID={`${testID}-timer`}>
          <Ionicons name="time-outline" size={11} color={colors.onSurfaceTertiary} />
          <Text style={styles.timerText}>{formatCountdown(remaining)}</Text>
        </View>
      ) : null}
    </Pressable>
  );
}

const useStyles = makeStyles((colors) => ({
  pill: {
    height: 34, paddingLeft: 6, paddingRight: 10,
    flexDirection: "row", alignItems: "center", gap: 6,
    backgroundColor: colors.overlay, borderWidth: 1, borderRadius: radius.pill,
  },
  pressed: { opacity: 0.8 },
  bookWrap: { width: 24, height: 24, alignItems: "center", justifyContent: "center" },
  bookGlow: { position: "absolute", width: 14, height: 14, borderRadius: 7 },
  book: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  count: { fontFamily: typography.displayBold, fontSize: 15, letterSpacing: -0.3, minWidth: 10, textAlign: "center" },
  slots: { flexDirection: "row", alignItems: "center", gap: 3 },
  slot: { width: 7, height: 7, borderRadius: 2.5, borderWidth: 1 },
  slotPremium: { width: 8, height: 8, borderRadius: 2, transform: [{ rotate: "45deg" }], marginLeft: 1 },
  timer: { flexDirection: "row", alignItems: "center", gap: 3, marginLeft: 2 },
  timerText: { color: colors.onSurfaceTertiary, fontFamily: typography.bodyBold, fontSize: 11, fontVariant: ["tabular-nums"] },
}));
