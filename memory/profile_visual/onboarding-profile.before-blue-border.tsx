// PAUSE — onboarding, passo "Raccontaci qualcosa di te" (dati personali).
// Replica del mockup: sfondo dedicato (lago notturno con pianeta), logo,
// titolo con "te" in gradiente, tre schede in vetro (nome/nickname, genere,
// età) e CTA a gradiente viola→ciano. Palette fissa ONB come il resto
// dell'onboarding (identica in tema chiaro e scuro).
import React, { useMemo, useRef, useState } from "react";
import {
  Dimensions, FlatList, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import Svg, { Defs, LinearGradient as SvgGradient, Stop, Text as SvgText } from "react-native-svg";
import * as Haptics from "expo-haptics";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useI18n } from "@/src/i18n";
import { Gender } from "@/src/api";
import { radius, spacing, typography, withAlpha } from "@/src/theme";
import { OnboardingBrand } from "./onboarding-brand";
import { ONB } from "./onboarding-palette";

const ARTWORK = require("../../assets/images/onboarding-profile-bg.jpg");
// Stesso gradiente del pulsante della presentazione (riferimento fisso del brand).
const CTA_BORDER = ["#E08CFF", "#7FA0FF", "#7FEBFF"] as const;
const CTA_FILL = ["#8A2BE8", "#5B3BF5", "#3556F2", "#2A8CF0", "#22C4F2"] as const;
// Materiale fisso per entrambi i temi: un solo velo quasi nero traslucido.
// Non sommare un fondo alle schede: renderebbe di nuovo il vetro opaco.
const CARD_TOP = "rgba(8,12,20,0.48)";
const CARD_MID = "rgba(4,9,16,0.40)";
const CARD_BOTTOM = "rgba(3,7,13,0.56)";
const BORDER = "rgba(40,210,255,0.22)";
const ICON_FILL = "rgba(9,13,22,0.24)";
const CHIP_FILL = "rgba(3,7,13,0.14)";
const SELECT_FILL = "rgba(3,7,13,0.18)";
const PLACEHOLDER = "#8FA6C9";
const AGES = Array.from({ length: 108 }, (_, i) => 13 + i); // 13 … 120
const AGE_ROW = 52;
export const MIN_NAME = 2;

export type ProfileDraft = { name: string; gender: Gender | null; age: number | null };

export function OnboardingProfile({ value, onChange, onBack, onContinue, canContinue, saving }: {
  value: ProfileDraft;
  onChange: (next: ProfileDraft) => void;
  onBack: () => void;
  onContinue: () => void;
  canContinue: boolean;
  saving: boolean;
}) {
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  // Cornice congelata al primo render: su Android la finestra si restringe quando
  // appare/scompare la tastiera e lo sfondo "ballerebbe"; qui resta fisso.
  const [frame] = useState(() => Dimensions.get("window"));
  const { width, height } = frame;
  const [focused, setFocused] = useState(false);
  const [agePickerOpen, setAgePickerOpen] = useState(false);
  // Logo più piccolo della presentazione (nel mockup l'anello è ~13% della larghezza).
  const brandUnit = Math.min(width, 430) / 984 * 0.6;
  const brandHeight = 372 * brandUnit;
  const titleSize = Math.min(31, Math.max(24, width * 0.074));
  const [titleLine1, titleLine2] = t.onb_profile_title_a.split("\n");

  const setGender = (g: Gender) => {
    Haptics.selectionAsync().catch(() => {});
    onChange({ ...value, gender: g });
  };

  return (
    <View style={styles.root} testID="onboarding-profile">
      <View pointerEvents="none" style={[styles.backdrop, { width, height }]}>
        <Image source={ARTWORK} contentFit="cover" contentPosition="center" transition={0} cachePolicy="memory-disk" accessible={false} testID="onboarding-profile-artwork" style={StyleSheet.absoluteFill} />
        {/* Veli: cielo leggermente scurito per il logo, pianeta/lago visibili dietro al titolo,
            fondo progressivamente scuro dove poggiano le schede e la CTA (come nel mockup). */}
        <LinearGradient
          colors={[withAlpha(ONB.bgTop, 0.58), withAlpha(ONB.bgTop, 0.3), withAlpha(ONB.bgTop, 0.24), withAlpha(ONB.bgTop, 0.36), withAlpha(ONB.bgTop, 0.5), withAlpha(ONB.bgTop, 0.72), withAlpha(ONB.bgTop, 0.8)]}
          locations={[0, 0.12, 0.3, 0.44, 0.6, 0.82, 1]}
          style={StyleSheet.absoluteFill}
        />
      </View>

      <KeyboardAvoidingView style={styles.fill} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView
          style={styles.fill}
          contentContainerStyle={[styles.content, { paddingTop: insets.top + 10, paddingBottom: insets.bottom + spacing.md, minHeight: height }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          bounces={false}
          testID="onboarding-profile-scroll"
        >
          {/* Barra alta: freccia indietro a sinistra, logo centrato alla stessa altezza. */}
          <View style={[styles.header, { height: brandHeight }]}>
            <Pressable onPress={onBack} hitSlop={8} accessibilityRole="button" accessibilityLabel={t.onb_profile_back} testID="onboarding-profile-back" style={({ pressed }) => [styles.back, pressed && styles.pressed]}>
              <Ionicons name="arrow-back" size={22} color={ONB.text} />
            </Pressable>
            <OnboardingBrand unit={brandUnit} top={0} />
          </View>

          <View style={styles.titleWrap}>
            <Text style={[styles.title, { fontSize: titleSize, lineHeight: titleSize * 1.18 }]} testID="onboarding-profile-title">{titleLine1}</Text>
            <View style={styles.titleRow}>
              <Text style={[styles.title, { fontSize: titleSize, lineHeight: titleSize * 1.18 }]}>{titleLine2}</Text>
              <GradientWord word={t.onb_profile_title_b} fontSize={titleSize} />
            </View>
            <Text style={styles.subtitle} testID="onboarding-profile-subtitle">{t.onb_profile_sub}</Text>
          </View>

          <View style={styles.spacer} />

          {/* Nome o nickname */}
          <GlassField icon="person-outline" glow={focused} testID="onboarding-profile-name-card">
            <Text style={styles.label} testID="onboarding-profile-name-label">{t.onb_profile_name}</Text>
            <TextInput
              value={value.name}
              onChangeText={(name) => onChange({ ...value, name: name.slice(0, 40) })}
              placeholder={t.onb_profile_name_ph}
              placeholderTextColor={PLACEHOLDER}
              style={styles.input}
              hitSlop={11}
              autoCapitalize="words"
              autoCorrect={false}
              returnKeyType="done"
              maxLength={40}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              testID="onboarding-profile-name"
              accessibilityLabel={t.onb_profile_name}
            />
          </GlassField>

          {/* Genere */}
          <GlassField icon="male-female-outline" testID="onboarding-profile-gender-card">
            <Text style={styles.label} testID="onboarding-profile-gender-label">{t.onb_profile_gender}</Text>
            <View style={styles.chips}>
              {([["man", t.onb_profile_man], ["woman", t.onb_profile_woman], ["other", t.onb_profile_other]] as [Gender, string][]).map(([g, label]) => {
                const on = value.gender === g;
                return (
                  <Pressable key={g} onPress={() => setGender(g)} accessibilityRole="radio" accessibilityState={{ selected: on }} testID={`onboarding-profile-gender-${g}`} style={({ pressed }) => [styles.chip, on && styles.chipOn, pressed && styles.pressed]}>
                    <Text style={[styles.chipText, on && styles.chipTextOn]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.8}>{label}</Text>
                  </Pressable>
                );
              })}
            </View>
          </GlassField>

          {/* Età */}
          <GlassField icon="calendar-outline" testID="onboarding-profile-age-card">
            <Text style={styles.label} testID="onboarding-profile-age-label">{t.onb_profile_age}</Text>
            <Pressable onPress={() => setAgePickerOpen(true)} accessibilityRole="button" accessibilityLabel={t.onb_profile_age_ph} testID="onboarding-profile-age" style={({ pressed }) => [styles.select, pressed && styles.pressed]}>
              <Text style={[styles.selectText, value.age === null && styles.selectPlaceholder]} testID="onboarding-profile-age-value">
                {value.age === null ? t.onb_profile_age_ph : `${value.age} ${t.onb_profile_age_years}`}
              </Text>
              <Ionicons name="chevron-down" size={18} color={ONB.textSecondary} />
            </Pressable>
          </GlassField>

          <View style={styles.spacerSm} />

          <View style={styles.footer}>
            <Pressable
              onPress={onContinue}
              disabled={saving}
              accessibilityRole="button"
              accessibilityState={{ disabled: !canContinue }}
              testID="onboarding-profile-continue"
              style={({ pressed }) => [styles.cta, { opacity: canContinue ? 1 : 0.55 }, pressed && styles.ctaPressed]}
            >
              <LinearGradient colors={[...CTA_BORDER]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.ctaBorder}>
                <LinearGradient colors={[...CTA_FILL]} locations={[0, 0.3, 0.55, 0.8, 1]} start={{ x: 0, y: 0.7 }} end={{ x: 1, y: 0.3 }} style={styles.ctaFill}>
                  <LinearGradient colors={["#FFFFFF38", "#FFFFFF0E", "#FFFFFF00", "#12063A2A"]} locations={[0, 0.28, 0.55, 1]} style={StyleSheet.absoluteFill} />
                  <Text style={styles.ctaText} testID="onboarding-profile-continue-label">{t.onb_modes_next}</Text>
                  <Ionicons name="arrow-forward" size={22} color={ONB.text} />
                </LinearGradient>
              </LinearGradient>
            </Pressable>
            {/* Tre indicatori come nel mockup (stesso stile della presentazione); questo è il secondo passo. */}
            <View style={styles.dots} accessible={false} testID="onboarding-profile-dots">
              {[0, 1, 2].map((i) => <View key={i} testID={`onboarding-profile-dot-${i}`} style={[styles.dot, i === 1 && styles.dotOn]} />)}
            </View>
          </View>

          <View style={styles.spacerLg} />
        </ScrollView>
      </KeyboardAvoidingView>

      <AgePicker
        visible={agePickerOpen}
        value={value.age}
        onClose={() => setAgePickerOpen(false)}
        onPick={(age) => { Haptics.selectionAsync().catch(() => {}); onChange({ ...value, age }); setAgePickerOpen(false); }}
      />
    </View>
  );
}

// Parola finale del titolo con riempimento ciano→viola (come nel mockup).
function GradientWord({ word, fontSize }: { word: string; fontSize: number }) {
  const w = Math.ceil(fontSize * 0.62 * word.length) + 4;
  const h = Math.ceil(fontSize * 1.18);
  return (
    <Svg width={w} height={h} testID="onboarding-profile-title-accent">
      <Defs>
        <SvgGradient id="onbWord" x1="0" y1="0" x2="1" y2="0">
          <Stop offset="0" stopColor={ONB.cyan} />
          <Stop offset="1" stopColor={ONB.violet} />
        </SvgGradient>
      </Defs>
      <SvgText x={0} y={fontSize * 0.98} fontSize={fontSize} fontFamily={typography.displayBold} fontWeight="700" fill="url(#onbWord)">{word}</SvgText>
    </Svg>
  );
}

// Una sola superficie di vetro scuro: la fotografia resta visibile al suo interno.
// Nessun filo neon sul bordo inferiore e nessun alone sulle schede a riposo.
function GlassField({ icon, glow, testID, children }: { icon: string; glow?: boolean; testID: string; children: React.ReactNode }) {
  return (
    <View style={[styles.card, glow && styles.cardGlow]} testID={testID}>
      <LinearGradient colors={[CARD_TOP, CARD_MID, CARD_BOTTOM]} locations={[0, 0.45, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <View style={styles.cardRow}>
        <View style={styles.iconWrap}>
          <Ionicons name={icon as any} size={21} color={ONB.textSecondary} />
        </View>
        <View style={styles.cardBody}>{children}</View>
      </View>
    </View>
  );
}

function AgePicker({ visible, value, onClose, onPick }: { visible: boolean; value: number | null; onClose: () => void; onPick: (age: number) => void }) {
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  const listRef = useRef<FlatList<number>>(null);
  const initialIndex = useMemo(() => Math.max(0, AGES.indexOf(value ?? 25) - 2), [value]);
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={styles.sheetBackdrop}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityLabel={t.onb_profile_back} testID="onboarding-profile-age-backdrop" />
        <View style={[styles.sheet, { paddingBottom: insets.bottom + spacing.md }]} testID="onboarding-profile-age-sheet">
          <LinearGradient colors={["rgba(12,16,25,0.98)", "rgba(5,9,16,0.98)"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
          <View style={styles.sheetHandle} />
          <Text style={styles.sheetTitle} testID="onboarding-profile-age-sheet-title">{t.onb_profile_age_ph}</Text>
          <FlatList
            ref={listRef}
            data={AGES}
            keyExtractor={(a) => String(a)}
            initialScrollIndex={initialIndex}
            getItemLayout={(_, i) => ({ length: AGE_ROW, offset: AGE_ROW * i, index: i })}
            style={styles.sheetList}
            showsVerticalScrollIndicator={false}
            renderItem={({ item }) => {
              const on = item === value;
              return (
                <Pressable onPress={() => onPick(item)} accessibilityRole="button" accessibilityState={{ selected: on }} testID={`onboarding-profile-age-${item}`} style={({ pressed }) => [styles.ageRow, on && styles.ageRowOn, pressed && styles.pressed]}>
                  <Text style={[styles.ageText, on && styles.ageTextOn]}>{item} {t.onb_profile_age_years}</Text>
                  {on ? <Ionicons name="checkmark" size={18} color={ONB.cyan} /> : null}
                </Pressable>
              );
            }}
          />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: ONB.bgTop, overflow: "hidden" },
  backdrop: { position: "absolute", top: 0, left: 0 },
  fill: { flex: 1, backgroundColor: "transparent" },
  content: { paddingHorizontal: 28, flexGrow: 1 },
  header: { position: "relative" },
  back: {
    position: "absolute", left: -6, top: 2, zIndex: 2, width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center",
    backgroundColor: ICON_FILL, borderWidth: 1, borderColor: withAlpha(ONB.textSecondary, 0.12),
  },
  pressed: { opacity: 0.8 },
  spacer: { flexGrow: 1.1, minHeight: 22 },
  spacerSm: { flexGrow: 0.9, minHeight: 20 },
  spacerLg: { flexGrow: 2.4, minHeight: 12 },
  titleWrap: { alignItems: "center", marginTop: 34 },
  titleRow: { flexDirection: "row", alignItems: "flex-end", justifyContent: "center" },
  title: {
    color: ONB.text, fontFamily: typography.displayBold, textAlign: "center", letterSpacing: -0.6, includeFontPadding: false,
    textShadowColor: withAlpha(ONB.bgTop, 0.7), textShadowOffset: { width: 0, height: 2 }, textShadowRadius: 14,
  },
  subtitle: {
    color: ONB.textSecondary, fontFamily: typography.body, fontSize: 14.5, lineHeight: 21, textAlign: "center", marginTop: 12, paddingHorizontal: 6,
    textShadowColor: withAlpha(ONB.bgTop, 0.7), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 8,
  },
  // Bordi discreti e vetro senza fondo duplicato né glow permanente.
  card: {
    borderRadius: 26, overflow: "hidden", borderWidth: 1, borderColor: BORDER, marginBottom: 14,
    backgroundColor: "transparent",
  },
  cardGlow: { borderColor: withAlpha(ONB.cyan, 0.34), boxShadow: `0px 0px 16px ${withAlpha(ONB.cyan, 0.05)}` as any },
  cardRow: { flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 18, paddingLeft: 16, paddingRight: 16 },
  iconWrap: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: ICON_FILL, borderWidth: 1, borderColor: withAlpha(ONB.textSecondary, 0.08),
  },
  cardBody: { flex: 1, minWidth: 0, gap: 7 },
  label: { color: ONB.text, fontFamily: typography.bodyBold, fontSize: 14.5, lineHeight: 18 },
  input: { color: ONB.text, fontFamily: typography.body, fontSize: 14, lineHeight: 20, paddingVertical: 1, paddingHorizontal: 0, minHeight: 22, ...(Platform.OS === "web" ? ({ outlineStyle: "none" } as any) : null) },
  chips: { flexDirection: "row", gap: 4, marginTop: 2 },
  chip: {
    flex: 1, minHeight: 44, borderRadius: 12, overflow: "hidden", alignItems: "center", justifyContent: "center", paddingHorizontal: 6,
    backgroundColor: CHIP_FILL, borderWidth: 1, borderColor: withAlpha(ONB.textSecondary, 0.1),
  },
  chipOn: { borderColor: withAlpha(ONB.cyan, 0.36), backgroundColor: withAlpha(ONB.cyan, 0.07), boxShadow: `0px 0px 12px ${withAlpha(ONB.cyan, 0.045)}` as any },
  chipText: { color: ONB.textSecondary, fontFamily: typography.bodyMedium, fontSize: 14 },
  chipTextOn: { color: ONB.text, fontFamily: typography.bodyBold },
  select: {
    minHeight: 44, borderRadius: 12, flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 12, marginTop: 2,
    backgroundColor: SELECT_FILL, borderWidth: 1, borderColor: withAlpha(ONB.textSecondary, 0.1),
  },
  selectText: { color: ONB.text, fontFamily: typography.bodyMedium, fontSize: 14 },
  selectPlaceholder: { color: "#C2CFE6", fontFamily: typography.body },
  footer: { paddingTop: 0, paddingHorizontal: 4 },
  cta: { height: 54, borderRadius: 27, overflow: "hidden", boxShadow: "0px 10px 36px #4A5CFF80, -6px 0px 22px #A63BFF55, 6px 0px 22px #2BC6FF55" as any },
  ctaPressed: { opacity: 0.9, transform: [{ scale: 0.985 }] },
  ctaBorder: { flex: 1, padding: 1.4, borderRadius: 27, overflow: "hidden" },
  ctaFill: { flex: 1, borderRadius: 27, overflow: "hidden", flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 12 },
  ctaText: { color: ONB.text, fontFamily: typography.bodyBold, fontSize: 18, includeFontPadding: false },
  dots: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 9, marginTop: 18 },
  dot: { width: 6, height: 6, borderRadius: 6, backgroundColor: "#22345F" },
  dotOn: { width: 10, backgroundColor: "#37D3FF", boxShadow: "0px 0px 10px #37D3FFAA" as any },
  sheetBackdrop: { flex: 1, justifyContent: "flex-end", backgroundColor: withAlpha(ONB.bgTop, 0.7) },
  sheet: { maxHeight: "60%", borderTopLeftRadius: 28, borderTopRightRadius: 28, overflow: "hidden", borderWidth: 1, borderColor: BORDER, paddingTop: 10, paddingHorizontal: spacing.lg },
  sheetHandle: { alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: ONB.glassBorderStrong, marginBottom: 12 },
  sheetTitle: { color: ONB.text, fontFamily: typography.displayBold, fontSize: 18, marginBottom: 8, textAlign: "center" },
  sheetList: { flexGrow: 0 },
  ageRow: { height: AGE_ROW, borderRadius: radius.md, flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 16 },
  ageRowOn: { backgroundColor: withAlpha(ONB.cyan, 0.12) },
  ageText: { color: ONB.textSecondary, fontFamily: typography.bodyMedium, fontSize: 17 },
  ageTextOn: { color: ONB.text, fontFamily: typography.bodyBold },
});
