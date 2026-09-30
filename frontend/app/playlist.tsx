// PAUSE — Playlist (Premium): "Pausa da 10 minuti".
// Backend curates 2-3 unread stories that fit ~N minutes of narration; here we
// present the queue and drop the user into the first story's deep-dive.
// Real continuous playback across stories will re-use the same audio player.
import { useMemo } from "react";
import {
  View, Text, ScrollView, Pressable, ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";
import { LinearGradient } from "expo-linear-gradient";

import { api } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography } from "@/src/theme";
import { useUserId } from "@/src/session";
import { usePremiumFlag } from "@/src/premium";
import { useI18n } from "@/src/i18n";
import { StoryHero } from "@/src/components/story-hero";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";

const DEFAULT_MINUTES = 10;

export default function Playlist() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const isPremium = usePremiumFlag();
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["playlist", userId, DEFAULT_MINUTES],
    queryFn: () => api.playlist(userId!, DEFAULT_MINUTES),
    enabled: !!userId && isPremium,
  });

  const first = data?.stories?.[0];
  const rest = useMemo(() => data?.stories?.slice(1) ?? [], [data]);

  if (userId && !isPremium) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]} testID="playlist-locked">
        <Header onBack={() => router.back()} title={t.playlist_title} sub={t.playlist_locked} colors={colors} styles={styles} />
        <View style={styles.locked}>
          <View style={[styles.lockOrb, { backgroundColor: colors.brand + "1A", borderColor: colors.brand + "44" }]}>
            <Ionicons name="lock-closed" size={26} color={colors.brand} />
          </View>
          <Text style={styles.lockedText}>{t.playlist_locked}</Text>
          <Pressable
            testID="playlist-go-premium"
            style={[styles.cta, { backgroundColor: colors.brand }]}
            onPress={() => router.replace("/premium")}
          >
            <Ionicons name="diamond" size={16} color={colors.onBrand} />
            <Text style={[styles.ctaText, { color: colors.onBrand }]}>{t.premium}</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <Screen style={[styles.container, { paddingTop: insets.top }]} testID="playlist-screen">
      <Header onBack={() => router.back()} title={t.playlist_title} sub={t.playlist_sub} colors={colors} styles={styles} />

      {isLoading || !data ? (
        <View style={styles.loading}><ActivityIndicator color={colors.brand} /></View>
      ) : data.stories.length === 0 ? (
        <View style={styles.empty}>
          <View style={[styles.lockOrb, { backgroundColor: colors.surfaceSecondary, borderColor: colors.border }]}>
            <Ionicons name="musical-notes-outline" size={26} color={colors.muted} />
          </View>
          <Text style={styles.emptyText}>{t.playlist_empty}</Text>
          <Pressable testID="playlist-rebuild-empty" onPress={() => refetch()} style={[styles.cta, { backgroundColor: colors.brand }]}>
            <Ionicons name="refresh" size={16} color={colors.onBrand} />
            <Text style={[styles.ctaText, { color: colors.onBrand }]}>{t.playlist_rebuild}</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xxl }}
          showsVerticalScrollIndicator={false}
        >
          {/* Big "Now playing" card */}
          {first ? (
            <Pressable
              onPress={() => router.push(`/deep-dive/${first.id}`)}
              testID="playlist-now-playing"
              style={({ pressed }) => [styles.nowCard, pressed && { opacity: 0.92 }]}
            >
              <StoryHero story={first} style={styles.heroBg} iconSize={44} />
              <LinearGradient
                colors={["rgba(5,7,12,0.15)", "rgba(5,7,12,0.85)"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 0, y: 1 }}
                style={styles.heroOverlay}
              />
              <View style={styles.nowContent}>
                <View style={styles.playPill}>
                  <Ionicons name="play" size={11} color="#FFFFFF" />
                  <Text style={styles.playText}>{t.playlist_now}</Text>
                </View>
                <Text style={styles.nowTitle} numberOfLines={2}>{first.title}</Text>
                <Text style={styles.nowMeta}>
                  {first.category_name.toUpperCase()} · {first.deep_dive_time_min} min
                </Text>
              </View>
            </Pressable>
          ) : null}

          <View style={styles.totalRow}>
            <Ionicons name="time-outline" size={14} color={colors.muted} />
            <Text style={styles.totalText}>{t.playlist_total(data.total_min)}</Text>
            <Pressable
              testID="playlist-rebuild"
              onPress={() => refetch()}
              hitSlop={8}
              style={styles.rebuildBtn}
            >
              <Ionicons name="refresh" size={14} color={colors.brand} />
              <Text style={[styles.rebuildText, { color: colors.brand }]}>{t.playlist_rebuild}</Text>
              {isFetching ? <ActivityIndicator size="small" color={colors.brand} /> : null}
            </Pressable>
          </View>

          {rest.length > 0 ? (
            <>
              <Text style={styles.eyebrow}>{t.playlist_up_next}</Text>
              {rest.map((s, i) => (
                <Pressable
                  key={s.id}
                  onPress={() => router.push(`/deep-dive/${s.id}`)}
                  testID={`playlist-item-${s.id}`}
                  style={({ pressed }) => [styles.row, pressed && { opacity: 0.92 }]}
                >
                  <StoryHero story={s} style={styles.thumb} iconSize={22} size="thumb" />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.rowMeta}>
                      {String(i + 2).padStart(2, "0")} · {s.category_name.toUpperCase()}
                    </Text>
                    <Text style={styles.rowTitle} numberOfLines={2}>{s.title}</Text>
                    <Text style={styles.rowSub} numberOfLines={1}>{s.deep_dive_time_min} min</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={18} color={colors.muted} />
                </Pressable>
              ))}
            </>
          ) : null}
        </ScrollView>
      )}
    </Screen>
  );
}

function Header({
  onBack, title, sub, colors, styles,
}: { onBack: () => void; title: string; sub: string; colors: any; styles: any }) {
  return (
    <View style={[styles.header, { paddingHorizontal: spacing.xl }]}>
      <Pressable onPress={onBack} testID="playlist-back" hitSlop={8} style={styles.backBtn}>
        <Ionicons name="chevron-back" size={24} color={colors.onSurface} />
      </Pressable>
      <View style={styles.headerTitle}>
        <Text style={styles.title} numberOfLines={1} adjustsFontSizeToFit>{title}</Text>
        <Text style={styles.subtitle} numberOfLines={2}>{sub}</Text>
      </View>
      <HomeButton testID="playlist-home" />
    </View>
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
  subtitle: { color: colors.muted, fontFamily: typography.body, fontSize: 11, textAlign: "center", lineHeight: 15 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
  empty: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, paddingHorizontal: spacing.xxl },
  emptyText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 21 },
  nowCard: {
    height: 240, borderRadius: radius.lg, overflow: "hidden",
    backgroundColor: colors.surfaceSecondary, marginTop: spacing.md, marginBottom: spacing.md,
  },
  heroBg: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  heroOverlay: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  nowContent: { position: "absolute", left: 0, right: 0, bottom: 0, padding: spacing.lg, gap: 6 },
  playPill: {
    flexDirection: "row", alignItems: "center", gap: 4, alignSelf: "flex-start",
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: radius.pill,
    backgroundColor: "rgba(255,255,255,0.16)",
  },
  playText: { color: "#FFFFFF", fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1.2 },
  nowTitle: { color: "#FFFFFF", fontFamily: typography.displayBold, fontSize: 22, lineHeight: 26 },
  nowMeta: { color: "rgba(255,255,255,0.75)", fontFamily: typography.body, fontSize: 12, letterSpacing: 0.6 },
  totalRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: spacing.lg },
  totalText: { color: colors.muted, fontFamily: typography.body, fontSize: 12, flex: 1 },
  rebuildBtn: { flexDirection: "row", alignItems: "center", gap: 6 },
  rebuildText: { fontFamily: typography.bodyBold, fontSize: 12 },
  eyebrow: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2, marginBottom: spacing.sm },
  row: {
    flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md,
    borderRadius: radius.lg, backgroundColor: colors.surfaceSecondary,
    borderWidth: 1, borderColor: colors.border, marginBottom: spacing.md,
  },
  thumb: { width: 56, height: 56, borderRadius: radius.md, overflow: "hidden" },
  rowMeta: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1.2 },
  rowTitle: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 14, marginTop: 2 },
  rowSub: { color: colors.muted, fontFamily: typography.body, fontSize: 11, marginTop: 2 },
  locked: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.lg, paddingHorizontal: spacing.xxl },
  lockOrb: { width: 72, height: 72, borderRadius: 36, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  lockedText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 21 },
  cta: {
    flexDirection: "row", alignItems: "center", gap: spacing.sm,
    paddingVertical: spacing.md, paddingHorizontal: spacing.xl, borderRadius: radius.pill,
  },
  ctaText: { fontFamily: typography.bodyBold, fontSize: 14 },
}));
