// PAUSE — onboarding, scelta del formato. Due card (Curiosità / Mini lezioni):
// quando l'utente ne accende una, sotto si apre un pannello che spiega in breve
// che cos'è quel formato; con entrambe accese compaiono entrambe le spiegazioni.
// In fase "argomenti" le stesse scelte si riducono a due pillole compatte.
import { View, Text, Pressable, StyleProp, ViewStyle } from "react-native";
import Animated, { FadeInDown, FadeOutUp, LinearTransition, Easing } from "react-native-reanimated";
import Ionicons from "@react-native-vector-icons/ionicons";

import { makeStyles, spacing, typography, radius, withAlpha } from "@/src/theme";
import { KindIcon, StoryKind } from "@/src/components/kind-icon";
import { ONB } from "@/src/components/onboarding-palette";
import { useI18n } from "@/src/i18n";

const ORDER: StoryKind[] = ["stories", "lessons"];
// Negli argomenti almeno un formato resta attivo, in entrambe le schermate.
export function toggleContentMode(prev: Set<StoryKind>, mode: StoryKind, requireOne = true): Set<StoryKind> {
  const next = new Set(prev);
  if (next.has(mode)) next.delete(mode);
  else next.add(mode);
  return requireOne && next.size === 0 ? new Set(prev) : next;
}
const ENTER = FadeInDown.duration(360).easing(Easing.out(Easing.cubic));
const EXIT = FadeOutUp.duration(200);
const LAYOUT = LinearTransition.duration(320).easing(Easing.inOut(Easing.cubic));

export function useModeCopy() {
  const { t } = useI18n();
  return {
    label: (k: StoryKind) => (k === "stories" ? t.onb_toggle_stories : t.onb_toggle_lessons),
    desc: (k: StoryKind) => (k === "stories" ? t.onb_stories_desc : t.onb_lessons_desc),
  };
}

export function ModeCards({ modes, onToggle }: { modes: Set<StoryKind>; onToggle: (k: StoryKind) => void }) {
  const styles = useStyles();
  const { t } = useI18n();
  const { label, desc } = useModeCopy();
  const active = ORDER.filter((k) => modes.has(k));

  return (
    <View testID="onboarding-modes">
      <View style={styles.row}>
        {ORDER.map((k) => {
          const on = modes.has(k);
          return (
            <Pressable
              key={k}
              onPress={() => onToggle(k)}
              testID={`onboarding-mode-${k}`}
              accessibilityRole="switch"
              aria-checked={on}
              accessibilityState={{ checked: on }}
              style={({ pressed }) => [
                styles.card,
                on && styles.cardOn,
                pressed && styles.pressed,
              ]}
            >
              <View style={styles.cardTop}>
                <KindIcon kind={k} size={52} lit={on} glow />
                <Ionicons name={on ? "checkmark-circle" : "ellipse-outline"} size={20} color={on ? ONB.cyan : ONB.glassBorderStrong} />
              </View>
              <Text style={[styles.cardLabel, on && { color: ONB.text }]}>{label(k)}</Text>
            </Pressable>
          );
        })}
      </View>

      {/* Pannello a tendina: una voce per ogni formato acceso. */}
      <Animated.View layout={LAYOUT} style={styles.panel} testID="onboarding-mode-panel">
        {active.length === 0 ? (
          <Animated.Text key="hint" entering={ENTER} exiting={EXIT} style={styles.hint} testID="onboarding-mode-hint">
            {t.onb_modes_hint}
          </Animated.Text>
        ) : (
          active.map((k, i) => (
            <Animated.View
              key={k}
              entering={ENTER.delay(i * 70)}
              exiting={EXIT}
              layout={LAYOUT}
              style={[styles.explain, i > 0 && styles.explainDivider]}
              testID={`onboarding-mode-explain-${k}`}
            >
              <KindIcon kind={k} size={30} lit glow={false} />
              <View style={styles.explainText}>
                <Text style={styles.explainTitle}>{label(k)}</Text>
                <Text style={styles.explainBody}>{desc(k)}</Text>
              </View>
            </Animated.View>
          ))
        )}
      </Animated.View>
    </View>
  );
}

export function ModeChips({ modes, onToggle, disabled = false, idPrefix = "onboarding", style, locked }: {
  modes: Set<StoryKind>; onToggle: (k: StoryKind) => void; disabled?: boolean; idPrefix?: string; style?: StyleProp<ViewStyle>;
  /** Formati riservati a Premium: mai accesi, con lucchetto; il tocco resta attivo (apre il paywall). */
  locked?: Set<StoryKind>;
}) {
  const styles = useStyles();
  const { label } = useModeCopy();
  return (
    <View style={[styles.chipRow, style]} testID={`${idPrefix}-mode-chips`}>
      {ORDER.map((k) => {
        const isLocked = !!locked?.has(k);
        const on = !isLocked && modes.has(k);
        return (
          <Pressable
            key={k}
            onPress={() => onToggle(k)}
            testID={`${idPrefix}-chip-${k}`}
            disabled={disabled}
            accessibilityRole="switch"
            aria-checked={on}
            accessibilityState={{ checked: on, disabled }}
            style={({ pressed }) => [
              styles.chip,
              on && styles.chipOn,
              pressed && styles.pressed,
            ]}
          >
            <KindIcon kind={k} size={22} lit={on} glow={false} testID={`${idPrefix}-chip-${k}-icon`} />
            <Text testID={`${idPrefix}-chip-${k}-label`} style={[styles.chipLabel, on && { color: ONB.text }]}>{label(k)}</Text>
            {on ? <Ionicons name="checkmark" size={14} color={ONB.cyan} /> : null}
            {isLocked ? <Ionicons name="lock-closed" size={13} color={ONB.cyan} testID={`${idPrefix}-chip-${k}-lock`} /> : null}
          </Pressable>
        );
      })}
    </View>
  );
}

const useStyles = makeStyles(() => ({
  row: { flexDirection: "row", gap: spacing.md },
  card: {
    flex: 1, gap: 8, padding: spacing.md, minHeight: 124, borderRadius: radius.lg,
    backgroundColor: "rgba(12,26,58,0.62)", borderWidth: 1.5, borderColor: ONB.glassBorder,
  },
  cardOn: {
    borderColor: withAlpha(ONB.cyan, 0.75), backgroundColor: "rgba(16,38,80,0.72)",
    boxShadow: `0px 0px 22px ${withAlpha(ONB.cyan, 0.22)}` as any,
  },
  cardTop: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between" },
  cardLabel: { color: ONB.textSecondary, fontFamily: typography.bodyBold, fontSize: 16, marginTop: 2 },
  pressed: { opacity: 0.86, transform: [{ scale: 0.98 }] },

  panel: {
    marginTop: spacing.md, borderRadius: radius.lg, overflow: "hidden",
    backgroundColor: "rgba(12,26,58,0.55)", borderWidth: 1, borderColor: ONB.glassBorder,
  },
  hint: {
    color: ONB.muted, fontFamily: typography.body, fontSize: 13, lineHeight: 18,
    paddingHorizontal: spacing.md, paddingVertical: spacing.md, textAlign: "center",
  },
  explain: { flexDirection: "row", gap: spacing.md, padding: spacing.md, alignItems: "flex-start" },
  explainDivider: { borderTopWidth: 1, borderTopColor: ONB.glassBorder },
  explainText: { flex: 1, gap: 3 },
  explainTitle: { color: ONB.text, fontFamily: typography.bodyBold, fontSize: 14 },
  explainBody: { color: ONB.textSecondary, fontFamily: typography.body, fontSize: 13, lineHeight: 19 },

  chipRow: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.lg },
  chip: {
    flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, minHeight: 44,
    paddingHorizontal: 8, paddingVertical: 6, borderRadius: radius.pill,
    backgroundColor: "rgba(12,26,58,0.62)", borderWidth: 1.5, borderColor: ONB.glassBorder,
  },
  chipOn: {
    borderColor: withAlpha(ONB.cyan, 0.7), backgroundColor: "rgba(16,38,80,0.72)",
    boxShadow: `0px 0px 18px ${withAlpha(ONB.cyan, 0.2)}` as any,
  },
  chipLabel: { flexShrink: 1, color: ONB.textSecondary, fontFamily: typography.bodyBold, fontSize: 13, textAlign: "center" },
}));
