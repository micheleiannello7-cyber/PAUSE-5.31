import { useEffect, useState } from "react";
import { View, Text, Pressable, StyleSheet, ScrollView, Dimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import Ionicons from "@react-native-vector-icons/ionicons";
import MaterialDesignIcons from "@react-native-vector-icons/material-design-icons";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/src/api";
import { RecapCard } from "@/src/components/recap-card";
import { colors, spacing, radius, typography, withAlpha } from "@/src/theme";
import { useUserId } from "@/src/session";
import { PauseLogo } from "@/src/components/pause-logo";
import { GradientText } from "@/src/components/gradient-text";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";
import { useI18n } from "@/src/i18n";
import { formatCountdown } from "@/src/components/limit-badge";

// Sunset hill at dusk — person with dog looking at the horizon (bundled, AI generated).
const HERO = require("../assets/images/pause-hero.jpg");

const PURPLE = colors.brandSecondary;
const CYAN = colors.brand;
const GREEN = colors.success;
const { width } = Dimensions.get("window");

export default function PauseLimit() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const { t } = useI18n();

  const { data, refetch } = useQuery({
    queryKey: ["limit", userId],
    queryFn: () => api.limitCheck(userId!),
    enabled: !!userId,
    refetchInterval: 30_000,
  });
  const recap = useQuery({
    queryKey: ["session-stories", userId],
    queryFn: () => api.sessionStories(userId!),
    enabled: !!userId,
  });

  // Countdown al prossimo credito (mm:ss), aggiornato ogni secondo.
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const nextAtMs = data?.next_credit_at ? Date.parse(data.next_credit_at) : 0;
  const returnIn = formatCountdown(Math.floor((nextAtMs - now) / 1000));
  useEffect(() => {
    if (nextAtMs && now >= nextAtMs) refetch();
  }, [now >= nextAtMs, nextAtMs, refetch]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (data && !data.blocked) {
      refetch();
      router.replace("/(tabs)/discover");
    }
  }, [data?.blocked, data, refetch, router]);

  return (
    <Screen style={styles.container}>
      <ScrollView
        contentContainerStyle={{ paddingBottom: insets.bottom + spacing.xxl }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View style={styles.heroWrap}>
          <Image source={HERO} style={styles.hero} contentFit="cover" contentPosition="top" />
          <LinearGradient
            colors={["rgba(5,7,12,0.45)", "rgba(5,7,12,0.05)", "rgba(5,7,12,0.7)", colors.surface]}
            locations={[0, 0.3, 0.75, 1]}
            style={StyleSheet.absoluteFill}
          />
          <LinearGradient
            colors={["rgba(5,7,12,0.75)", "transparent"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 0.7, y: 0 }}
            style={StyleSheet.absoluteFill}
          />
          <View style={[styles.header, { paddingTop: insets.top + spacing.md }]}>
            <PauseLogo />
            <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
              <View style={styles.pill} testID="limit-timer">
                <Ionicons name="time-outline" size={15} color={colors.onSurface} />
                <Text style={styles.pillText}>{nextAtMs ? returnIn : t.limit_active}</Text>
              </View>
              <HomeButton testID="pause-limit-home" />
            </View>
          </View>

          <View style={styles.titleWrap}>
            <Text style={styles.titleWhite}>{t.stop_title}</Text>
            <GradientText
              lines={[t.stop_grad_1, t.stop_grad_2]}
              colors={[CYAN, PURPLE]}
              fontSize={32}
              lineHeight={38}
              width={width - spacing.xl * 2}
            />
          </View>
        </View>

        {/* Cards */}
        <View style={styles.cards}>
          <SessionStats
            stories={data?.session_count ?? recap.data?.length ?? 4}
            seconds={data?.session_seconds ?? 0}
            limit={data?.limit ?? 4}
          />

          <View style={styles.card}>
            <Orb color={CYAN}>
              <MaterialDesignIcons name="head-lightbulb-outline" size={26} color={CYAN} />
            </Orb>
            <Text style={styles.leadText}>{t.pl_lead}</Text>
          </View>

          <NumberedCard
            index={1}
            color={PURPLE}
            icon={<MaterialDesignIcons name="brain" size={26} color={PURPLE} />}
            title={t.pl_1_title}
            body={t.pl_1_body(data?.limit ?? 4)}
          />

          <NumberedCard
            index={2}
            color={GREEN}
            badgeColor={CYAN}
            icon={<Ionicons name="leaf-outline" size={24} color={GREEN} />}
            title={t.pl_2_title}
            body={t.pl_2_body}
          />

          <LinearGradient
            colors={["#6A3BDF", "#2E63CF", "#12AECF"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.finalCard}
          >
            <View style={styles.finalOrb}>
              <MaterialDesignIcons name="sprout-outline" size={26} color={colors.onBrandSecondary} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.finalTitle}>{t.pl_final_title}</Text>
              <Text style={styles.finalBody}>{t.pl_final_body(returnIn, data?.limit ?? 4, Math.round((data?.recharge_seconds ?? 7200) / 60))}</Text>
            </View>
          </LinearGradient>

          <Pressable onPress={() => router.push("/history")} testID="pause-limit-reread" accessibilityRole="button"
            style={({ pressed }) => [styles.rereadRow, pressed && { opacity: 0.85 }]}>
            <View style={styles.rereadIcon}>
              <Ionicons name="refresh-outline" size={18} color={colors.success} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.rereadTitle}>{t.pl_reread_cta}</Text>
              <Text style={styles.rereadSub}>{t.pl_reread_sub}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.muted} />
          </Pressable>

          {/* Recap of the stories just read */}
          {recap.data && recap.data.length > 0 ? (
            <View style={styles.recap} testID="session-recap">
              <Text style={styles.recapTitle}>{t.pl_recap_title}</Text>
              <Text style={styles.recapSub}>{t.pl_recap_sub}</Text>
              {recap.data.map((s, i) => <RecapCard key={s.id} story={s} index={i + 1} />)}
            </View>
          ) : null}
        </View>
      </ScrollView>
    </Screen>
  );
}

function SessionStats({ stories, seconds, limit }: { stories: number; seconds: number; limit: number }) {
  const { t } = useI18n();
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  const time = m > 0 ? `${m}m` : `${s}s`;
  return (
    <View style={styles.statsCard} testID="session-stats">
      <Text style={styles.statsEyebrow}>{t.pl_stats_eyebrow}</Text>
      <View style={styles.statsRow}>
        <View style={styles.statCol}>
          <Ionicons name="book" size={18} color={CYAN} />
          <Text style={styles.statValue}>{Math.min(stories, limit)}</Text>
          <Text style={styles.statLabel}>{t.stories_read}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statCol}>
          <Ionicons name="time" size={18} color={PURPLE} />
          <Text style={styles.statValue}>{time}</Text>
          <Text style={styles.statLabel}>{t.pl_time_read}</Text>
        </View>
      </View>
    </View>
  );
}

function Orb({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <View style={[styles.orb, { backgroundColor: color + "14", borderColor: color + "40" }]}>
      {children}
    </View>
  );
}

function NumberedCard({
  index, color, badgeColor, icon, title, body,
}: { index: number; color: string; badgeColor?: string; icon: React.ReactNode; title: string; body: string }) {
  return (
    <View style={styles.card}>
      <Orb color={color}>{icon}</Orb>
      <View style={{ flex: 1 }}>
        <View style={styles.numRow}>
          <View style={[styles.numBadge, { backgroundColor: badgeColor ?? color }]}>
            <Text style={styles.numBadgeText}>{index}</Text>
          </View>
          <Text style={styles.numTitle}>{title}</Text>
        </View>
        <Text style={styles.numBody}>{body}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  heroWrap: { height: 420, justifyContent: "space-between" },
  hero: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  header: {
    paddingHorizontal: spacing.xl,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  pill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    backgroundColor: "rgba(5,7,12,0.55)", borderWidth: 1, borderColor: "rgba(255,255,255,0.18)",
    paddingHorizontal: 14, paddingVertical: 9, borderRadius: radius.pill,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(5,7,12,0.55)", borderWidth: 1, borderColor: "rgba(255,255,255,0.18)",
  },
  backSpacer: { width: 36, height: 36 },
  pillText: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 13 },
  titleWrap: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl },
  titleWhite: {
    color: colors.onSurface, fontFamily: typography.displayBold,
    fontSize: 32, lineHeight: 38,
  },
  cards: { paddingHorizontal: spacing.xl, marginTop: -spacing.md, gap: spacing.md },
  statsCard: {
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
    borderRadius: radius.lg + 2, padding: spacing.lg, gap: spacing.md,
  },
  statsEyebrow: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2 },
  statsRow: { flexDirection: "row", alignItems: "center" },
  statCol: { flex: 1, alignItems: "center", gap: 4 },
  statValue: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 24 },
  statLabel: { color: colors.muted, fontFamily: typography.body, fontSize: 11 },
  statDivider: { width: 1, height: 42, backgroundColor: colors.divider },
  card: {
    flexDirection: "row", gap: spacing.md, padding: spacing.lg, alignItems: "center",
    borderRadius: radius.lg + 2,
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  orb: {
    width: 56, height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },
  leadText: { flex: 1, color: colors.onSurface, fontFamily: typography.bodyMedium, fontSize: 15, lineHeight: 23 },
  numRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 6 },
  numBadge: { width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  numBadgeText: { color: colors.onBrandSecondary, fontFamily: typography.displayBold, fontSize: 12 },
  numTitle: { flex: 1, color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 15 },
  numBody: { color: colors.onSurfaceTertiary, fontFamily: typography.body, fontSize: 14, lineHeight: 21 },
  finalCard: {
    flexDirection: "row", gap: spacing.md, alignItems: "center",
    padding: spacing.lg, borderRadius: radius.lg + 2, marginTop: spacing.sm,
  },
  finalOrb: {
    width: 56, height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.14)", borderWidth: 1, borderColor: "rgba(255,255,255,0.3)",
  },
  finalTitle: { color: colors.onBrandSecondary, fontFamily: typography.displayBold, fontSize: 16, lineHeight: 22, marginBottom: 6 },
  finalBody: { color: "rgba(255,255,255,0.85)", fontFamily: typography.body, fontSize: 14, lineHeight: 20 },
  rereadRow: {
    marginTop: spacing.md, flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md,
    borderRadius: radius.lg - 2, backgroundColor: colors.glassBgStrong, borderWidth: 1, borderColor: withAlpha(colors.success, 0.35),
  },
  rereadIcon: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center", backgroundColor: withAlpha(colors.success, 0.12) },
  rereadTitle: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 14 },
  rereadSub: { color: colors.muted, fontFamily: typography.body, fontSize: 12, marginTop: 2 },
  recap: { marginTop: spacing.xl, gap: spacing.md },
  recapTitle: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2 },
  recapSub: { color: colors.muted, fontFamily: typography.body, fontSize: 13, marginTop: -spacing.sm, marginBottom: spacing.xs },
});
