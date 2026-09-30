// PAUSE — Stats & badges. Top numbers are for everyone; the curiosity map,
// activity history, badge collection and monthly recap card are Premium.
// Data comes from GET /api/user/{id}/stats (see backend/stats.py).
import { useRef, useState } from "react";
import {
  View, Text, ScrollView, Pressable, ActivityIndicator, StyleSheet, Platform,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import ViewShot, { captureRef } from "react-native-view-shot";
import * as Sharing from "expo-sharing";

import { api, Stats, Badge, StatsCategory } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography, withAlpha } from "@/src/theme";
import { useUserId } from "@/src/session";
import { usePremiumFlag } from "@/src/premium";
import { useI18n } from "@/src/i18n";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";
import { GlassSurface, GlassIconButton, GlassPill, GlowButton, AmbientGlow } from "@/src/components/glass";

// 3 sharable styles for the monthly recap card. Aurora reuses the user's
// active accent so the Wrapped feels personal; Notte and Neon are fixed
// palettes so users can pick a vibe that isn't tied to their accent choice.
type WrappedStyle = "aurora" | "notte" | "neon";
const WRAPPED_STYLES: { id: WrappedStyle; gradient: [string, string, string]; icon: string }[] = [
  { id: "aurora", gradient: ["#050712", "#050712", "#050712"], icon: "sparkles" },
  { id: "notte", gradient: ["#050718", "#1A1550", "#3B1E7B"], icon: "moon" },
  { id: "neon", gradient: ["#FF006A", "#B200FF", "#00D2FF"], icon: "flash" },
];

export default function StatsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const isPremium = usePremiumFlag();
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();

  const { data, isLoading } = useQuery({
    queryKey: ["stats", userId],
    queryFn: () => api.stats(userId!),
    enabled: !!userId,
  });

  const monthShareRef = useRef<View>(null);
  const [wrappedStyle, setWrappedStyle] = useState<WrappedStyle>("aurora");

  const onShare = async () => {
    if (!monthShareRef.current) return;
    try {
      const uri = await captureRef(monthShareRef, { format: "png", quality: 1 });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, { dialogTitle: t.stats_share });
      }
    } catch {
      // silent — sharing may not be available on web
    }
  };

  return (
    <Screen style={[styles.container, { paddingTop: insets.top }]} testID="stats-screen">
      <LinearGradient colors={[colors.surface, colors.surfaceDeep]} locations={[0.3, 1]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <AmbientGlow color={colors.cyan} alpha={0.12} size={300} style={{ top: -40, left: -120 }} />
      <View style={[styles.header, { paddingHorizontal: spacing.xl }]}>
        <GlassIconButton onPress={() => router.back()} testID="stats-back" size={38} accessibilityLabel="back">
          <Ionicons name="chevron-back" size={20} color={colors.onSurface} />
        </GlassIconButton>
        <View style={styles.headerTitle}>
          <Text style={styles.title} numberOfLines={1} adjustsFontSizeToFit>{t.stats_title}</Text>
        </View>
        <HomeButton testID="stats-home" />
      </View>

      {isLoading || !data ? (
        <View style={styles.loading}><ActivityIndicator color={colors.brand} /></View>
      ) : (
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xxl }}
          showsVerticalScrollIndicator={false}
        >
          {/* Top numbers — free */}
          <View style={styles.numbersGrid} testID="stats-numbers">
            <NumberCell icon="book" label={t.stats_stories} value={data.stories} colors={colors} styles={styles} />
            <NumberCell icon="time" label={t.stats_read_min} value={data.minutes} colors={colors} styles={styles} tint={colors.brandSecondary} />
            <NumberCell icon="headset" label={t.stats_listen_min} value={data.listen_minutes} colors={colors} styles={styles} tint={colors.info} />
            <NumberCell icon="flame" label={t.stats_best_streak} value={data.best_streak} colors={colors} styles={styles} tint={colors.warning} />
            <NumberCell
              icon="grid"
              label={t.stats_categories}
              value={data.categories_explored}
              max={data.categories_total}
              colors={colors}
              styles={styles}
              tint={colors.success}
            />
          </View>

          {/* Premium sections */}
          {!isPremium ? (
            <LockedPremium onPress={() => router.push("/premium")} colors={colors} styles={styles} t={t} />
          ) : (
            <>
              <SectionTitle eyebrow={t.stats_map} sub={t.stats_map_sub} colors={colors} styles={styles} />
              <GlassSurface intensity="regular" contentStyle={styles.mapCard} testID="stats-map">
                {data.categories.slice(0, 8).map((c) => (
                  <CategoryBar key={c.id} cat={c} colors={colors} styles={styles} />
                ))}
              </GlassSurface>

              <SectionTitle
                eyebrow={t.stats_history}
                sub={t.stats_history_sub(data.history.filter((d) => d.active).length)}
                colors={colors}
                styles={styles}
              />
              <GlassSurface intensity="regular" contentStyle={styles.historyRow} testID="stats-history">
                {data.history.map((d) => (
                  <View
                    key={d.date}
                    style={[
                      styles.historyDot,
                      d.active
                        ? { backgroundColor: colors.cyan, boxShadow: `0px 0px 8px ${colors.cyanGlow}` as any }
                        : { backgroundColor: colors.track },
                    ]}
                  />
                ))}
              </GlassSurface>

              <SectionTitle
                eyebrow={t.stats_badges}
                sub={t.stats_badges_sub(data.badges_unlocked, data.badges.length)}
                colors={colors}
                styles={styles}
              />
              <View style={styles.badgeGrid} testID="stats-badges">
                {data.badges.map((b) => (
                  <BadgeCell key={b.id} badge={b} colors={colors} styles={styles} />
                ))}
              </View>

              <SectionTitle eyebrow={t.stats_month} sub="" colors={colors} styles={styles} />
              {/* 3-style Wrapped picker: users personalise the card before
                  sharing (Aurora reuses their accent, Notte and Neon are
                  fixed vibes). Hidden until we have data.month. */}
              <View style={styles.wrappedPickerRow} testID="wrapped-picker">
                {WRAPPED_STYLES.map((s) => {
                  const active = wrappedStyle === s.id;
                  const swatch = s.id === "aurora" ? colors.gradient : (s.gradient.slice(-2) as [string, string]);
                  return (
                    <Pressable
                      key={s.id}
                      onPress={() => setWrappedStyle(s.id)}
                      testID={`wrapped-style-${s.id}`}
                      style={[
                        styles.wrappedChip,
                        { borderColor: active ? colors.brand : colors.border },
                      ]}
                    >
                      <LinearGradient
                        colors={swatch}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={styles.wrappedChipSwatch}
                      >
                        <Ionicons name={s.icon as any} size={12} color="#FFFFFF" />
                      </LinearGradient>
                      <Text style={[styles.wrappedChipText, { color: active ? colors.onSurface : colors.muted }]}>
                        {s.id === "aurora" ? t.wrapped_aurora : s.id === "notte" ? t.wrapped_notte : t.wrapped_neon}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              <ViewShot ref={monthShareRef} style={styles.recapWrap}>
                <MonthRecap
                  stats={data}
                  colors={colors}
                  styles={styles}
                  variant={wrappedStyle}
                  gradient={
                    wrappedStyle === "aurora"
                      ? colors.gradient
                      : WRAPPED_STYLES.find((s) => s.id === wrappedStyle)!.gradient
                  }
                  t={t}
                />
              </ViewShot>
              {Platform.OS !== "web" ? (
                <Pressable
                  testID="stats-share"
                  onPress={onShare}
                  style={[styles.shareBtn, { backgroundColor: colors.brand }]}
                >
                  <Ionicons name="share-social" size={16} color={colors.onBrand} />
                  <Text style={[styles.shareText, { color: colors.onBrand }]}>{t.stats_share}</Text>
                </Pressable>
              ) : null}
            </>
          )}
        </ScrollView>
      )}
    </Screen>
  );
}

function NumberCell({
  icon, label, value, max, tint, colors, styles,
}: {
  icon: string; label: string; value: number; max?: number; tint?: string; colors: any; styles: any;
}) {
  const color = tint ?? colors.brand;
  return (
    <View style={[styles.numberCell, { borderColor: color + "33" }]} testID={`stat-${icon}`}>
      <Ionicons name={icon as any} size={16} color={color} />
      <Text style={styles.numberValue}>
        {value}
        {max != null ? <Text style={styles.numberMax}> / {max}</Text> : null}
      </Text>
      <Text style={styles.numberLabel} numberOfLines={2}>{label}</Text>
    </View>
  );
}

function SectionTitle({
  eyebrow, sub, colors, styles,
}: { eyebrow: string; sub: string; colors: any; styles: any }) {
  return (
    <View style={{ marginTop: spacing.xl, marginBottom: spacing.md }}>
      <Text style={styles.sectionEyebrow}>{eyebrow}</Text>
      {sub ? <Text style={styles.sectionSub}>{sub}</Text> : null}
    </View>
  );
}

function CategoryBar({
  cat, colors, styles,
}: { cat: StatsCategory; colors: any; styles: any }) {
  const ratio = Math.max(0.03, Math.min(1, cat.ratio));
  return (
    <View style={styles.mapRow} testID={`map-${cat.id}`}>
      <Text style={styles.mapName} numberOfLines={1}>{cat.name}</Text>
      <View style={[styles.mapTrack, { backgroundColor: colors.surfaceTertiary }]}>
        <View style={[styles.mapFill, { width: `${ratio * 100}%`, backgroundColor: cat.color }]} />
      </View>
      <Text style={styles.mapValue}>{cat.read}/{cat.total}</Text>
    </View>
  );
}

function BadgeCell({ badge, colors, styles }: { badge: Badge; colors: any; styles: any }) {
  const unlocked = badge.unlocked;
  return (
    <View
      style={[
        styles.badgeCell,
        {
          borderColor: unlocked ? colors.brand : colors.border,
          backgroundColor: unlocked ? colors.brand + "14" : colors.surfaceSecondary,
        },
      ]}
      testID={`badge-${badge.id}`}
    >
      <View
        style={[
          styles.badgeOrb,
          {
            backgroundColor: unlocked ? colors.brand : colors.surfaceTertiary,
          },
        ]}
      >
        <Ionicons
          name={badge.icon as any}
          size={20}
          color={unlocked ? colors.onBrand : colors.muted}
        />
      </View>
      <Text style={[styles.badgeTitle, { color: unlocked ? colors.onSurface : colors.muted }]} numberOfLines={1}>
        {badge.title}
      </Text>
      <Text style={styles.badgeDesc} numberOfLines={2}>{badge.description}</Text>
      {!unlocked ? (
        <View style={[styles.badgeProgressTrack, { backgroundColor: colors.surfaceTertiary }]}>
          <View
            style={[
              styles.badgeProgressFill,
              { width: `${Math.min(100, (badge.value / badge.target) * 100)}%`, backgroundColor: colors.brand },
            ]}
          />
        </View>
      ) : null}
    </View>
  );
}

function MonthRecap({
  stats, colors, styles, variant, gradient, t,
}: { stats: Stats; colors: any; styles: any; variant: WrappedStyle; gradient: readonly string[]; t: any }) {
  const m = stats.month;
  return (
    <View style={styles.recap} testID={`stats-month-recap-${variant}`}>
      <LinearGradient
        colors={gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.recapContent}>
        <Text style={styles.recapEyebrow}>{m.key}</Text>
        <Text style={styles.recapHeadline}>{t.wrapped_headline(m.stories)}</Text>
        <View style={styles.recapGrid}>
          <RecapStat value={m.minutes} label={t.wrapped_min_read} styles={styles} />
          <RecapStat value={m.listen_minutes} label={t.wrapped_min_listen} styles={styles} />
          <RecapStat value={m.active_days} label={t.wrapped_active_days} styles={styles} />
          <RecapStat value={m.categories} label={t.wrapped_categories} styles={styles} />
        </View>
        {m.top_category ? (
          <View style={styles.recapTopRow}>
            <Ionicons name={m.top_category.icon as any} size={14} color="rgba(255,255,255,0.9)" />
            <Text style={styles.recapTopText}>{t.wrapped_top_category}: {m.top_category.name}</Text>
          </View>
        ) : null}
        <Text style={styles.recapFooter}>P^USE — one pause, a thousand discoveries.</Text>
      </View>
    </View>
  );
}

function RecapStat({ value, label, styles }: { value: number; label: string; styles: any }) {
  return (
    <View style={styles.recapStat}>
      <Text style={styles.recapValue}>{value}</Text>
      <Text style={styles.recapLabel}>{label}</Text>
    </View>
  );
}

function LockedPremium({ onPress, colors, styles, t }: { onPress: () => void; colors: any; styles: any; t: any }) {
  return (
    <Pressable onPress={onPress} testID="stats-locked" style={({ pressed }) => [styles.locked, pressed && { opacity: 0.92 }]}>
      <LinearGradient
        colors={[colors.brand + "22", colors.brandSecondary + "22"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.lockedInner}>
        <View style={[styles.lockOrb, { backgroundColor: colors.brand + "22", borderColor: colors.brand + "55" }]}>
          <Ionicons name="lock-closed" size={22} color={colors.brand} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.lockedTitle}>{t.stats_locked_title}</Text>
          <Text style={styles.lockedSub}>{t.stats_locked_sub}</Text>
        </View>
        <View style={[styles.lockedPill, { backgroundColor: colors.brand }]}>
          <Ionicons name="diamond" size={11} color={colors.onBrand} />
          <Text style={[styles.lockedPillText, { color: colors.onBrand }]}>{t.premium}</Text>
        </View>
      </View>
    </Pressable>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: colors.surface },
  header: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    paddingTop: spacing.md, paddingBottom: spacing.md,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  headerSpacer: { width: 36, height: 36 },
  headerTitle: { flex: 1, alignItems: "center", gap: 3 },
  title: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 16, textAlign: "center" },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },

  numbersGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginTop: spacing.md },
  numberCell: {
    flexBasis: "31%", flexGrow: 1, minWidth: 100, gap: 6,
    padding: spacing.md, borderRadius: radius.md, borderWidth: 1,
    backgroundColor: colors.surfaceSecondary,
  },
  numberValue: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 22 },
  numberMax: { color: colors.muted, fontFamily: typography.body, fontSize: 14 },
  numberLabel: { color: colors.muted, fontFamily: typography.body, fontSize: 11, lineHeight: 15 },

  sectionEyebrow: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2 },
  sectionSub: { color: colors.muted, fontFamily: typography.body, fontSize: 12, marginTop: 2 },

  mapCard: {
    padding: spacing.md, borderRadius: radius.lg, gap: spacing.md,
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  mapRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  mapName: { width: 90, color: colors.onSurface, fontFamily: typography.body, fontSize: 12 },
  mapTrack: { flex: 1, height: 8, borderRadius: 4, overflow: "hidden" },
  mapFill: { height: "100%", borderRadius: 4 },
  mapValue: { width: 44, color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11, textAlign: "right" },

  historyRow: {
    flexDirection: "row", gap: 4, padding: spacing.md, borderRadius: radius.lg,
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
    justifyContent: "space-between",
  },
  historyDot: { width: 16, height: 16, borderRadius: 8, flexShrink: 0 },

  badgeGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  badgeCell: {
    flexBasis: "48%", flexGrow: 1, minWidth: 140, gap: 6,
    padding: spacing.md, borderRadius: radius.md, borderWidth: 1,
  },
  badgeOrb: { width: 34, height: 34, borderRadius: 17, alignItems: "center", justifyContent: "center", marginBottom: 4 },
  badgeTitle: { fontFamily: typography.bodyBold, fontSize: 13 },
  badgeDesc: { color: colors.muted, fontFamily: typography.body, fontSize: 11, lineHeight: 15, minHeight: 30 },
  badgeProgressTrack: { height: 4, borderRadius: 2, overflow: "hidden", marginTop: 4 },
  badgeProgressFill: { height: "100%", borderRadius: 2 },

  recapWrap: { borderRadius: radius.lg, overflow: "hidden" },
  wrappedPickerRow: {
    flexDirection: "row", gap: spacing.sm, marginBottom: spacing.md, flexWrap: "wrap",
  },
  wrappedChip: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingLeft: 5, paddingRight: spacing.md, height: 34,
    borderRadius: radius.pill, borderWidth: 1.5,
    backgroundColor: colors.surfaceSecondary,
  },
  wrappedChipSwatch: {
    width: 24, height: 24, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
  },
  wrappedChipText: { fontFamily: typography.bodyBold, fontSize: 12 },
  recap: { minHeight: 240 },
  recapContent: { padding: spacing.xl, gap: spacing.md },
  recapEyebrow: { color: "rgba(255,255,255,0.75)", fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2 },
  recapHeadline: { color: "#FFFFFF", fontFamily: typography.displayBold, fontSize: 24, lineHeight: 28 },
  recapGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md, marginTop: spacing.sm },
  recapStat: { flexBasis: "45%", flexGrow: 1 },
  recapValue: { color: "#FFFFFF", fontFamily: typography.displayBold, fontSize: 22 },
  recapLabel: { color: "rgba(255,255,255,0.8)", fontFamily: typography.body, fontSize: 11 },
  recapTopRow: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: spacing.sm },
  recapTopText: { color: "rgba(255,255,255,0.9)", fontFamily: typography.bodyMedium, fontSize: 12 },
  recapFooter: { color: "rgba(255,255,255,0.7)", fontFamily: typography.body, fontSize: 10, marginTop: spacing.md, letterSpacing: 1 },

  shareBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.sm,
    paddingVertical: spacing.md, borderRadius: radius.pill, marginTop: spacing.md,
  },
  shareText: { fontFamily: typography.bodyBold, fontSize: 14 },

  locked: {
    marginTop: spacing.xl, borderRadius: radius.lg, overflow: "hidden",
    borderWidth: 1, borderColor: colors.brand + "44",
  },
  lockedInner: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.lg },
  lockOrb: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  lockedTitle: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 14 },
  lockedSub: { color: colors.muted, fontFamily: typography.body, fontSize: 12, marginTop: 2, lineHeight: 16 },
  lockedPill: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: radius.pill,
  },
  lockedPillText: { fontFamily: typography.bodyBold, fontSize: 10 },
}));
