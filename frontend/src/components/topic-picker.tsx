// Unica interfaccia per argomenti e formati: onboarding e tab Categorie.
// La persistenza resta al chiamante (conferma onboarding / autosave Categorie).
import { ReactNode, useState } from "react";
import { StyleSheet, View, Text } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import { Category } from "@/src/api";
import { spacing, radius, typography, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { CategoryGrid } from "./category-grid";
import { ModeChips } from "./onboarding-modes";
import { StoryKind } from "./kind-icon";
import { ONB } from "./onboarding-palette";

type Props = {
  categories: Category[]; selected: Set<string>; modes: Set<StoryKind>;
  onToggleCategory: (id: string) => void; onToggleMode: (mode: StoryKind) => void;
  /** Formati bloccati (es. mini lezioni per l'utente base): pillola con lucchetto, il tocco apre il paywall. */
  lockedModes?: Set<StoryKind>;
  testID: string; modeIdPrefix?: string; disabled?: boolean; staggerIn?: boolean;
  titleAccessory?: ReactNode; status?: ReactNode; columns?: number;
  /** Schermo intero senza scorrimento: spaziature compatte e griglia adattata all'altezza rimasta. */
  fit?: boolean;
};

export function TopicPicker({ categories, selected, modes, onToggleCategory, onToggleMode, lockedModes,
  testID, modeIdPrefix = "onboarding", disabled = false, staggerIn = false, titleAccessory, status, columns, fit = false }: Props) {
  const { t } = useI18n();
  const formats = modes.size === 2 ? t.onb_formats_both : modes.has("lessons") ? t.onb_formats_lessons : t.onb_formats_stories;
  // Titolo su una sola riga: il corpo segue la larghezza disponibile accanto
  // all'accessorio (Sora Bold ≈ 0,56 em per carattere).
  const [titleW, setTitleW] = useState(0);
  const titleSize = titleW > 0 ? Math.max(15, Math.min(24, Math.floor(titleW / (t.onb_title.length * 0.56)))) : 20;
  // Altezza rimasta per la griglia (solo in modalità schermo intero).
  const [gridH, setGridH] = useState(0);
  const gap = fit ? styles.gapFit : styles.gap;
  return (
    <View style={[styles.content, fit && styles.contentFit]} testID={`${testID}-picker`}>
      <ModeChips modes={modes} onToggle={onToggleMode} disabled={disabled} idPrefix={modeIdPrefix} style={gap} locked={lockedModes} />
      <View style={[styles.titleRow, gap]}>
        <View style={styles.titleBox} onLayout={(e) => setTitleW(Math.floor(e.nativeEvent.layout.width))}>
          <Text style={[styles.title, { fontSize: titleSize, lineHeight: Math.round(titleSize * 1.25) }]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.7} testID={`${testID}-title`}>{t.onb_title}</Text>
        </View>
        {titleAccessory}
      </View>
      {/* Un solo riquadro, due spiegazioni distinte: cosa fa la scelta · non è definitiva. */}
      <Animated.View entering={FadeIn.delay(120).duration(360)} style={[styles.hintCard, gap, fit && styles.hintCardFit]} testID={`${testID}-hint`}>
        <View style={styles.hintRow}>
          <View style={styles.hintBullet}><Ionicons name="sparkles-outline" size={15} color={ONB.cyan} /></View>
          <Text style={[styles.hintText, fit && styles.hintTextFit]} testID={`${testID}-hint-text`}>{t.onb_topics_hint.replace("{formats}", formats)}</Text>
        </View>
        <View style={styles.hintDivider} />
        <View style={styles.hintRow} testID={`${testID}-change-note`}>
          <View style={styles.hintBullet}><Ionicons name="options-outline" size={15} color={ONB.cyan} /></View>
          <Text style={[styles.hintText, fit && styles.hintTextFit]}>
            <Text style={styles.hintNoteTitle} testID={`${testID}-change-note-title`}>{t.onb_topics_change_t}</Text>
            <Text style={styles.hintNote} testID={`${testID}-change-note-text`}>{` — ${t.onb_topics_change_b}`}</Text>
          </Text>
        </View>
      </Animated.View>
      {status}
      {fit ? (
        <View style={styles.gridFit} onLayout={(e) => setGridH(Math.floor(e.nativeEvent.layout.height))}>
          {gridH > 0 ? (
            <CategoryGrid compact glass staggerIn={staggerIn} disabled={disabled} categories={categories} columns={columns} maxHeight={gridH}
              selected={selected} modes={Array.from(modes)} onToggle={onToggleCategory} />
          ) : null}
        </View>
      ) : (
        <CategoryGrid compact glass staggerIn={staggerIn} disabled={disabled} categories={categories} columns={columns}
          selected={selected} modes={Array.from(modes)} onToggle={onToggleCategory} />
      )}
    </View>
  );
}

export function TopicsBackdrop() {
  return (
    <View pointerEvents="none" style={styles.backdrop}>
      <LinearGradient colors={[ONB.bgTop, ONB.bgMid, ONB.bgBottom]} locations={[0, 0.45, 1]} style={StyleSheet.absoluteFill} />
      <View style={styles.orb} />
      <View style={styles.orbViolet} />
    </View>
  );
}

// Palette ONB intenzionalmente fissa nei due temi; preserva lo stile approvato.
const styles = StyleSheet.create({
  content: { paddingHorizontal: spacing.xl, paddingTop: spacing.lg, paddingBottom: spacing.lg },
  contentFit: { flex: 1, paddingTop: spacing.sm + 2, paddingBottom: 0 },
  gap: { marginBottom: spacing.lg },
  gapFit: { marginBottom: spacing.sm + 2 },
  gridFit: { flex: 1, minHeight: 0 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  titleBox: { flex: 1, minWidth: 0 },
  title: { color: ONB.text, fontFamily: typography.displayBold, fontSize: 28, lineHeight: 34, letterSpacing: -0.3,
    textShadowColor: withAlpha(ONB.cyan, 0.25), textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 18 },
  hintCard: { padding: spacing.md, gap: spacing.sm + 2,
    borderRadius: radius.lg, backgroundColor: "rgba(12,26,58,0.65)",
    borderWidth: 1, borderColor: withAlpha(ONB.cyan, 0.32), boxShadow: `0px 0px 24px ${withAlpha(ONB.cyan, 0.08)}` },
  hintCardFit: { padding: spacing.sm + 2, gap: spacing.sm },
  hintTextFit: { fontSize: 12.5, lineHeight: 17, paddingTop: 4 },
  hintRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm + 2 },
  hintBullet: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center",
    backgroundColor: withAlpha(ONB.cyan, 0.1), borderWidth: 1, borderColor: withAlpha(ONB.cyan, 0.3) },
  hintDivider: { height: 1, backgroundColor: withAlpha(ONB.cyan, 0.16), marginLeft: 26 + spacing.sm + 2 },
  hintText: { flex: 1, color: ONB.textSecondary, fontFamily: typography.body, fontSize: 13, lineHeight: 19, paddingTop: 3 },
  hintNote: { color: withAlpha(ONB.textSecondary, 0.9) },
  hintNoteTitle: { color: ONB.text, fontFamily: typography.bodyBold },
  backdrop: { position: "absolute", top: 0, right: 0, bottom: 0, left: 0, overflow: "hidden" },
  orb: { position: "absolute", top: -140, right: -110, width: 340, height: 340, borderRadius: 170,
    backgroundColor: ONB.orb, boxShadow: "0px 0px 150px 70px rgba(31,75,255,0.16)" },
  orbViolet: { position: "absolute", bottom: 120, left: -160, width: 300, height: 300, borderRadius: 150,
    backgroundColor: "rgba(120,60,255,0.06)", boxShadow: "0px 0px 140px 60px rgba(120,60,255,0.08)" },
});