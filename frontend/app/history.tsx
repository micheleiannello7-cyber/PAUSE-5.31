// PAUSE — Cronologia: la piccola biblioteca personale delle storie scoperte.
// Costruita sul log `completions` già esistente (nessun tracking parallelo).
// Base: ultimi 10 giorni, nessuna ricerca/filtro. Premium: tutto, ricerca per
// titolo, filtri per categoria e periodo. Tutti i colori dal tema (makeStyles).
import { useEffect, useMemo, useState } from "react";
import { View, Text, Pressable, SectionList, ScrollView, ActivityIndicator, TextInput, RefreshControl } from "react-native";
import Animated, { FadeInUp, FadeIn, Easing } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import { useQuery } from "@tanstack/react-query";

import { api, HistoryItem } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography, withAlpha } from "@/src/theme";
import { useUserId } from "@/src/session";
import { useI18n } from "@/src/i18n";
import { StoryHero } from "@/src/components/story-hero";
import { HighlightedTitle } from "@/src/components/highlighted-title";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";

type Period = "all" | "7d" | "30d" | "year";
type Section = { key: string; title: string; data: HistoryItem[] };

const PERIOD_DAYS: Record<Period, number | null> = { all: null, "7d": 7, "30d": 30, year: 365 };
const DAY_MS = 86_400_000;

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function History() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const { t, lang } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const locale = lang === "it" ? "it-IT" : "en-GB";

  const [search, setSearch] = useState("");
  const [needle, setNeedle] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [period, setPeriod] = useState<Period>("all");
  const [activeCat, setActiveCat] = useState<string | null>(null);
  useEffect(() => {
    const id = setTimeout(() => setNeedle(search.trim()), 250);
    return () => clearTimeout(id);
  }, [search]);

  const since = useMemo(() => {
    const days = PERIOD_DAYS[period];
    return days ? new Date(Date.now() - days * DAY_MS).toISOString() : undefined;
  }, [period]);

  const q = useQuery({
    queryKey: ["history", userId, needle, since],
    queryFn: () => api.history(userId!, { q: needle || undefined, since }),
    enabled: !!userId,
  });
  const premium = !!q.data?.is_premium;
  const items = useMemo(() => q.data?.items ?? [], [q.data]);

  // Categorie presenti nella cronologia (per i chip Premium), con conteggio.
  const cats = useMemo(() => {
    const map = new Map<string, { id: string; name: string; color: string; n: number }>();
    for (const it of items) {
      const c = map.get(it.story.category_id) ?? { id: it.story.category_id, name: it.story.category_name, color: it.story.category_color, n: 0 };
      c.n += 1;
      map.set(c.id, c);
    }
    return Array.from(map.values()).sort((a, b) => b.n - a.n);
  }, [items]);

  // Raggruppamento per periodo: Oggi · Ieri · "29 settembre" (ultimi 30 giorni) · "Settembre 2026".
  const sections = useMemo<Section[]>(() => {
    const now = new Date();
    const today = startOfDay(now);
    const out: Section[] = [];
    const index = new Map<string, Section>();
    for (const it of items) {
      if (activeCat && it.story.category_id !== activeCat) continue;
      const d = new Date(it.read_at);
      const dayStart = startOfDay(d);
      const diffDays = Math.round((today - dayStart) / DAY_MS);
      let key: string;
      let title: string;
      if (diffDays <= 0) { key = "today"; title = t.history_today; }
      else if (diffDays === 1) { key = "yesterday"; title = t.history_yesterday; }
      else if (diffDays <= 30) { key = `d-${dayStart}`; title = capitalize(d.toLocaleDateString(locale, { day: "numeric", month: "long" })); }
      else { key = `m-${d.getFullYear()}-${d.getMonth()}`; title = capitalize(d.toLocaleDateString(locale, { month: "long", year: "numeric" })); }
      let sec = index.get(key);
      if (!sec) { sec = { key, title, data: [] }; index.set(key, sec); out.push(sec); }
      sec.data.push(it);
    }
    return out;
  }, [items, activeCat, t, locale]);

  const readLabel = (iso: string): string => {
    const d = new Date(iso);
    const diffDays = Math.round((startOfDay(new Date()) - startOfDay(d)) / DAY_MS);
    if (diffDays <= 1) return d.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
    const sameYear = d.getFullYear() === new Date().getFullYear();
    return d.toLocaleDateString(locale, sameYear ? { day: "numeric", month: "short" } : { day: "numeric", month: "short", year: "numeric" });
  };

  const filtering = !!needle || period !== "all" || !!activeCat;
  const empty = !!q.data && items.length === 0 && !filtering;
  const visibleCount = sections.reduce((n, s) => n + s.data.length, 0);
  const filtersActive = period !== "all" || !!activeCat;

  return (
    <Screen style={[styles.container, { paddingTop: insets.top }]} testID="history-screen">
      <View style={styles.header}>
        <Pressable onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/profile"))} testID="history-back" hitSlop={8} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={24} color={colors.onSurface} />
        </Pressable>
        <View style={styles.headerTitle}>
          <Text style={styles.title} numberOfLines={1} testID="history-title">{t.history_title}</Text>
        </View>
        <HomeButton testID="history-home" />
      </View>

      {premium && (q.data!.total > 0) ? (
        <Animated.View entering={FadeIn.duration(260)} style={styles.tools} testID="history-tools">
          <View style={styles.searchRow}>
            <View style={styles.searchWrap}>
              <Ionicons name="search-outline" size={16} color={colors.muted} />
              <TextInput
                value={search}
                onChangeText={setSearch}
                placeholder={t.history_search_ph}
                placeholderTextColor={colors.muted}
                style={styles.searchInput}
                returnKeyType="search"
                autoCorrect={false}
                testID="history-search"
              />
              {search ? (
                <Pressable onPress={() => setSearch("")} hitSlop={8} testID="history-search-clear">
                  <Ionicons name="close-circle" size={16} color={colors.muted} />
                </Pressable>
              ) : null}
            </View>
            <Pressable
              onPress={() => setShowFilters((v) => !v)}
              testID="history-filters-toggle"
              accessibilityRole="button"
              accessibilityLabel={t.history_filters}
              accessibilityState={{ expanded: showFilters }}
              style={[styles.filterBtn, (showFilters || filtersActive) && styles.filterBtnActive]}
            >
              <Ionicons name="options-outline" size={18} color={showFilters || filtersActive ? colors.brand : colors.muted} />
              {filtersActive ? <View style={styles.filterDot} /> : null}
            </Pressable>
          </View>
          {showFilters ? (
            <Animated.View entering={FadeIn.duration(200)} testID="history-filters">
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
                {(["all", "7d", "30d", "year"] as Period[]).map((p) => (
                  <Chip
                    key={p}
                    label={p === "all" ? t.history_all : p === "7d" ? t.history_7d : p === "30d" ? t.history_30d : t.history_year}
                    icon="calendar-outline"
                    color={colors.brand}
                    active={period === p}
                    onPress={() => setPeriod(p)}
                    testID={`history-period-${p}`}
                  />
                ))}
              </ScrollView>
              {cats.length > 1 ? (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
                  <Chip label={t.history_all} color={colors.brand} active={activeCat === null} onPress={() => setActiveCat(null)} testID="history-cat-all" />
                  {cats.map((c) => (
                    <Chip key={c.id} label={`${c.name} · ${c.n}`} color={c.color} active={activeCat === c.id}
                      onPress={() => setActiveCat(activeCat === c.id ? null : c.id)} testID={`history-cat-${c.id}`} />
                  ))}
                </ScrollView>
              ) : null}
            </Animated.View>
          ) : null}
        </Animated.View>
      ) : null}

      {q.isLoading ? (
        <View style={styles.center}><ActivityIndicator color={colors.brand} /></View>
      ) : q.isError ? (
        <View style={styles.center} testID="history-error">
          <Text style={styles.emptyText}>{t.load_error}</Text>
          <Pressable onPress={() => q.refetch()} style={styles.retryBtn} testID="history-retry">
            <Text style={styles.retryText}>{t.retry}</Text>
          </Pressable>
        </View>
      ) : empty ? (
        <View style={styles.center} testID="history-empty">
          <View style={styles.emptyOrb}>
            <Ionicons name="library-outline" size={32} color={colors.brand} />
          </View>
          <Text style={styles.emptyTitle}>{t.history_empty_t}</Text>
          <Text style={styles.emptyText}>{t.history_empty_b}</Text>
        </View>
      ) : (
        <SectionList
          sections={sections}
          keyExtractor={(it) => it.story.id}
          stickySectionHeadersEnabled={false}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xxl }}
          refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brand} />}
          renderSectionHeader={({ section }) => (
            <View style={styles.sectionHead} testID={`history-section-${section.key}`}>
              <Text style={styles.sectionTitle}>{section.title}</Text>
              <View style={styles.sectionLine} />
              <Text style={styles.sectionCount}>{section.data.length}</Text>
            </View>
          )}
          renderItem={({ item, index }) => (
            <HistoryCard item={item} index={index} when={readLabel(item.read_at)} onPress={() => router.push(`/deep-dive/${item.story.id}`)} />
          )}
          ItemSeparatorComponent={() => <View style={{ height: spacing.sm + 2 }} />}
          ListEmptyComponent={
            <View style={styles.center} testID="history-filter-empty">
              <Ionicons name="search-outline" size={28} color={colors.muted} />
              <Text style={styles.emptyText}>{t.history_search_empty}</Text>
            </View>
          }
          ListFooterComponent={
            !premium && q.data ? (
              <Pressable onPress={() => router.push("/premium")} testID="history-premium-card" style={({ pressed }) => [styles.premiumWrap, pressed && { opacity: 0.9 }]}>
                <LinearGradient pointerEvents="none" colors={[withAlpha(colors.brandSecondary, 0.28), withAlpha(colors.brand, 0.14)]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.premiumBg} />
                <View style={styles.premiumIcon}>
                  <Ionicons name="diamond" size={18} color={colors.brand} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.premiumTitle}>{t.history_premium_t}</Text>
                  <Text style={styles.premiumBody} testID="history-premium-body">{t.history_premium_b(q.data.hidden_count)}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={colors.brand} />
              </Pressable>
            ) : visibleCount > 0 ? <View style={{ height: spacing.md }} /> : null
          }
        />
      )}
    </Screen>
  );
}

function Chip({ label, icon, color, active, onPress, testID }: { label: string; icon?: string; color: string; active: boolean; onPress: () => void; testID: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <Pressable onPress={onPress} testID={testID} accessibilityRole="button" accessibilityState={{ selected: active }}
      style={[styles.chip, active ? { backgroundColor: withAlpha(color, 0.16), borderColor: color } : { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
      {icon ? <Ionicons name={icon as any} size={12} color={active ? color : colors.muted} /> : null}
      <Text style={[styles.chipText, { color: active ? color : colors.muted }]}>{label}</Text>
    </Pressable>
  );
}

// Card compatta: copertina valorizzata · categoria · titolo · momento della lettura.
function HistoryCard({ item, index, when, onPress }: { item: HistoryItem; index: number; when: string; onPress: () => void }) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();
  const { story } = item;
  return (
    <Animated.View entering={FadeInUp.delay(Math.min(index, 8) * 45).duration(360).easing(Easing.out(Easing.cubic))}>
      <Pressable onPress={onPress} testID={`history-${story.id}`} accessibilityRole="button"
        style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}>
        <LinearGradient pointerEvents="none" colors={[colors.glassHighlight, "transparent"]} style={styles.cardSheen} />
        <StoryHero story={story} style={styles.thumb} iconSize={24} size="thumb" />
        <View style={styles.info}>
          <Text style={[styles.category, { color: story.category_color || colors.brand }]} numberOfLines={1}>{story.category_name.toUpperCase()}</Text>
          <HighlightedTitle title={story.title} highlight={story.highlight_words} style={styles.cardTitle} highlightColor={colors.brand} numberOfLines={2} />
          <View style={styles.metaRow}>
            <Ionicons name="time-outline" size={11} color={colors.muted} />
            <Text style={styles.metaText} testID={`history-${story.id}-date`}>{when}</Text>
            <View style={styles.rereadPill} testID={`history-${story.id}-free`}>
              <Ionicons name="refresh-outline" size={9} color={colors.success} />
              <Text style={styles.rereadText}>{t.history_reread}</Text>
            </View>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={16} color={colors.muted} />
      </Pressable>
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: colors.surface },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingHorizontal: spacing.xl, paddingTop: spacing.md, paddingBottom: spacing.md },
  backBtn: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  headerTitle: { flex: 1, alignItems: "center" },
  title: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 18, textAlign: "center" },
  tools: { paddingHorizontal: spacing.xl, gap: spacing.sm, marginBottom: spacing.xs },
  searchRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  searchWrap: {
    flex: 1, flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingHorizontal: spacing.md, height: 42,
    borderRadius: radius.md, backgroundColor: colors.glassBgStrong, borderWidth: 1, borderColor: colors.glassBorder,
  },
  searchInput: { flex: 1, color: colors.onSurface, fontFamily: typography.body, fontSize: 14, paddingVertical: 0 },
  filterBtn: {
    width: 42, height: 42, borderRadius: radius.md, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.glassBgStrong, borderWidth: 1, borderColor: colors.glassBorder,
  },
  filterBtnActive: { borderColor: withAlpha(colors.brand, 0.6), backgroundColor: withAlpha(colors.brand, 0.1) },
  filterDot: { position: "absolute", top: 7, right: 7, width: 6, height: 6, borderRadius: 3, backgroundColor: colors.brand },
  chipRow: { gap: spacing.sm, paddingVertical: 2, paddingRight: spacing.sm },
  chip: { flexDirection: "row", alignItems: "center", gap: 6, height: 32, paddingHorizontal: 12, borderRadius: radius.pill, borderWidth: 1 },
  chipText: { fontFamily: typography.bodyBold, fontSize: 12, letterSpacing: 0.3 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.sm, paddingHorizontal: spacing.xxl, paddingVertical: spacing.xxl },
  emptyOrb: {
    width: 76, height: 76, borderRadius: 38, alignItems: "center", justifyContent: "center", marginBottom: spacing.sm,
    backgroundColor: withAlpha(colors.brand, 0.1), borderWidth: 1, borderColor: withAlpha(colors.brand, 0.35),
    boxShadow: `0px 0px 30px ${withAlpha(colors.brand, 0.25)}` as any,
  },
  emptyTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 18, textAlign: "center" },
  emptyText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 21 },
  retryBtn: { marginTop: spacing.sm, minHeight: 44, paddingHorizontal: spacing.xl, justifyContent: "center", borderRadius: radius.pill, borderWidth: 1, borderColor: colors.brand },
  retryText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 14 },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingTop: spacing.lg, paddingBottom: spacing.sm },
  sectionTitle: { color: colors.onSurfaceSecondary, fontFamily: typography.bodyBold, fontSize: 12, letterSpacing: 1.6, textTransform: "uppercase" },
  sectionLine: { flex: 1, height: 1, backgroundColor: colors.divider },
  sectionCount: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11 },
  card: {
    flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.sm + 2, paddingRight: spacing.md,
    borderRadius: radius.lg - 2, overflow: "hidden",
    backgroundColor: colors.glassBgStrong, borderWidth: 1, borderColor: colors.glassBorder,
  },
  cardPressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  cardSheen: { position: "absolute", top: 0, left: 0, right: 0, height: 1.5, opacity: 0.6 },
  thumb: { width: 72, height: 72, borderRadius: radius.md, backgroundColor: colors.surfaceTertiary, overflow: "hidden" },
  info: { flex: 1, gap: 4, justifyContent: "center" },
  category: { fontFamily: typography.bodyBold, fontSize: 9.5, letterSpacing: 1.4 },
  cardTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 14, lineHeight: 18 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 1 },
  metaText: { color: colors.muted, fontFamily: typography.body, fontSize: 11 },
  rereadPill: { marginLeft: 4, flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 6, paddingVertical: 1, borderRadius: radius.pill, borderWidth: 1, borderColor: withAlpha(colors.success, 0.45), backgroundColor: withAlpha(colors.success, 0.08) },
  rereadText: { color: colors.success, fontFamily: typography.bodyBold, fontSize: 8.5, letterSpacing: 0.8 },
  premiumWrap: {
    flexDirection: "row", alignItems: "center", gap: spacing.md, marginTop: spacing.xl,
    padding: spacing.md, borderRadius: radius.lg - 2, overflow: "hidden",
    borderWidth: 1, borderColor: withAlpha(colors.brand, 0.4), backgroundColor: colors.glassBgStrong,
  },
  premiumBg: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  premiumIcon: {
    width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center",
    backgroundColor: withAlpha(colors.brand, 0.14), borderWidth: 1, borderColor: withAlpha(colors.brand, 0.4),
  },
  premiumTitle: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 14, lineHeight: 19 },
  premiumBody: { color: colors.onSurfaceTertiary, fontFamily: typography.body, fontSize: 12, lineHeight: 17, marginTop: 3 },
}));
