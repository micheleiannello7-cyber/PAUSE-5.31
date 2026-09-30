// PAUSE — Browse (Premium): pick the next story by category instead of the
// "surprise" one. Free users bounce to the paywall; the grid + list is
// available only when `is_premium` is true.
import { useMemo, useState, useEffect } from "react";
import {
  View, Text, ScrollView, Pressable, ActivityIndicator, StyleSheet,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";

import { api, StoryPreview } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography } from "@/src/theme";
import { useUserId } from "@/src/session";
import { usePremiumFlag } from "@/src/premium";
import { useI18n } from "@/src/i18n";
import { LinearGradient } from "expo-linear-gradient";
import { StoryHero } from "@/src/components/story-hero";
import { KindBadge } from "@/src/components/kind-badge";
import { CategoryTag, MetaPill } from "@/src/components/reader-meta";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";

const ALL = "all";

export default function Browse() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const params = useLocalSearchParams<{ category_id?: string }>();
  const userId = useUserId();
  const isPremium = usePremiumFlag();
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();

  const [categoryId, setCategoryId] = useState<string>(params.category_id ?? ALL);
  const [onlyNew, setOnlyNew] = useState(false);

  const { data: categories } = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const { data: user } = useQuery({
    queryKey: ["user", userId], queryFn: () => api.user(userId!), enabled: !!userId,
  });

  const unlocked = useMemo(() => new Set(user?.unlocked_categories ?? []), [user]);
  const hasUnlocked = unlocked.size > 0;
  const hasAccess = isPremium || hasUnlocked;

  // If the user has consumable unlocks but no Premium, restrict the chip row
  // to those categories only and default to the first one.
  const availableCategories = useMemo(() => {
    if (!categories) return [];
    if (isPremium) return categories;
    return categories.filter((c) => unlocked.has(c.id));
  }, [categories, isPremium, unlocked]);

  useEffect(() => {
    if (isPremium) return;
    // If not premium and current chip isn't in the unlocked set, pin to first unlocked.
    if (categoryId === ALL || !unlocked.has(categoryId)) {
      if (availableCategories.length > 0) setCategoryId(availableCategories[0].id);
    }
  }, [isPremium, availableCategories, categoryId, unlocked]);
  const { data: stories, isLoading } = useQuery({
    queryKey: ["browse", categoryId, userId],
    queryFn: () => api.stories({
      category_id: categoryId === ALL ? undefined : categoryId,
      limit: 60,
      user_id: userId ?? undefined,
    }),
  });

  const completed = useMemo(() => new Set(user?.completed_story_ids ?? []), [user]);
  const visible = useMemo(
    () => (onlyNew ? (stories ?? []).filter((s) => s.is_new) : stories ?? []),
    [stories, onlyNew],
  );
  const newCount = useMemo(() => (stories ?? []).filter((s) => s.is_new).length, [stories]);

  // Not premium AND no consumable unlock → paywall.
  if (user && !hasAccess) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]} testID="browse-locked">
        <Header onBack={() => router.back()} title={t.browse_title} sub={t.browse_locked} colors={colors} styles={styles} />
        <View style={styles.locked}>
          <View style={[styles.lockOrb, { backgroundColor: colors.brand + "1A", borderColor: colors.brand + "44" }]}>
            <Ionicons name="lock-closed" size={26} color={colors.brand} />
          </View>
          <Text style={styles.lockedText}>{t.browse_locked}</Text>
          <Pressable
            testID="browse-go-premium"
            style={[styles.cta, { backgroundColor: colors.brand }]}
            onPress={() => router.replace("/premium")}
          >
            <Ionicons name="diamond" size={16} color={colors.onBrand} />
            <Text style={[styles.ctaText, { color: colors.onBrand }]}>{t.premium}</Text>
          </Pressable>
          <Pressable
            testID="browse-go-unlock"
            style={[styles.cta, { backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.warning + "66" }]}
            onPress={() => router.replace("/unlock")}
          >
            <Ionicons name="key-outline" size={16} color={colors.warning} />
            <Text style={[styles.ctaText, { color: colors.warning }]}>{t.consumable_price}</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <Screen style={[styles.container, { paddingTop: insets.top }]} testID="browse-screen">
      <Header onBack={() => router.back()} title={t.browse_title} sub={t.browse_sub} colors={colors} styles={styles} />

      {/* "Solo nuove" toggle: Premium-only quick filter to spotlight the
          early-access catalogue. Hidden when the user has no new stories. */}
      {newCount > 0 ? (
        <View style={styles.onlyNewRow}>
          <Pressable
            testID="only-new-toggle"
            onPress={() => setOnlyNew((v) => !v)}
            style={[
              styles.onlyNewPill,
              {
                borderColor: onlyNew ? colors.brand : colors.border,
                backgroundColor: onlyNew ? colors.brand + "1F" : colors.surfaceSecondary,
              },
            ]}
          >
            <Ionicons name="sparkles" size={13} color={onlyNew ? colors.brand : colors.muted} />
            <Text style={[styles.onlyNewText, { color: onlyNew ? colors.brand : colors.onSurface }]}>
              {t.browse_only_new}
            </Text>
            <View style={[styles.onlyNewCount, { backgroundColor: onlyNew ? colors.brand : colors.surfaceTertiary }]}>
              <Text style={[styles.onlyNewCountText, { color: onlyNew ? colors.onBrand : colors.muted }]}>
                {newCount}
              </Text>
            </View>
          </Pressable>
        </View>
      ) : null}

      {/* Filter chips: chrome, horizontal single-row scroller */}
      <View style={styles.chipsRow}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipsContent}
        >
          <Chip
            active={categoryId === ALL}
            label={t.any_topic}
            onPress={() => setCategoryId(ALL)}
            testID="chip-all"
            colors={colors}
            styles={styles}
          />
          {categories?.map((c) => (
            <Chip
              key={c.id}
              active={categoryId === c.id}
              label={c.name}
              onPress={() => setCategoryId(c.id)}
              testID={`chip-${c.id}`}
              tint={c.color}
              colors={colors}
              styles={styles}
            />
          ))}
        </ScrollView>
      </View>

      {isLoading || !stories ? (
        <View style={styles.loading}><ActivityIndicator color={colors.brand} /></View>
      ) : visible.length === 0 ? (
        <View style={styles.empty}>
          <View style={[styles.lockOrb, { backgroundColor: colors.surfaceSecondary, borderColor: colors.border }]}>
            <Ionicons name="book-outline" size={26} color={colors.muted} />
          </View>
          <Text style={styles.emptyText}>{onlyNew ? t.browse_only_new_empty : t.browse_empty}</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xxl, paddingTop: spacing.md }}
          showsVerticalScrollIndicator={false}
        >
          {visible.map((s) => (
            <StoryRow key={s.id} story={s} read={completed.has(s.id)} onPress={() => router.push(`/deep-dive/${s.id}`)} colors={colors} styles={styles} />
          ))}
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
      <Pressable onPress={onBack} testID="browse-back" hitSlop={8} style={styles.backBtn}>
        <Ionicons name="chevron-back" size={24} color={colors.onSurface} />
      </Pressable>
      <View style={styles.headerTitle}>
        <Text style={styles.title} numberOfLines={1} adjustsFontSizeToFit>{title}</Text>
        <Text style={styles.subtitle} numberOfLines={2}>{sub}</Text>
      </View>
      <HomeButton testID="browse-home" />
    </View>
  );
}

function Chip({
  active, label, onPress, testID, tint, colors, styles,
}: {
  active: boolean; label: string; onPress: () => void; testID: string; tint?: string; colors: any; styles: any;
}) {
  const border = active ? (tint ?? colors.brand) : colors.border;
  const bg = active ? (tint ?? colors.brand) + "22" : colors.surfaceSecondary;
  const fg = active ? (tint ?? colors.brand) : colors.onSurface;
  return (
    <Pressable onPress={onPress} testID={testID} style={[styles.chip, { borderColor: border, backgroundColor: bg }]}>
      <Text style={[styles.chipText, { color: fg }]}>{label}</Text>
    </Pressable>
  );
}

// Card in stile lettore: copertina che sfuma in un velo scuro, categoria e
// durata in alto sul testo, solo il titolo (niente descrizione).
function StoryRow({
  story, read, onPress, colors, styles,
}: { story: StoryPreview; read: boolean; onPress: () => void; colors: any; styles: any }) {
  const { t } = useI18n();
  return (
    <Pressable onPress={onPress} testID={`browse-story-${story.id}`} style={({ pressed }) => [styles.row, pressed && { opacity: 0.92 }]}>
      <StoryHero story={story} style={StyleSheet.absoluteFill} iconSize={40} />
      <LinearGradient
        colors={["rgba(5,7,12,0.05)", "rgba(5,7,12,0.45)", "rgba(5,7,12,0.92)"]}
        locations={[0.15, 0.55, 1]}
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.rowTop}>
        <KindBadge story={story} size="sm" overlay />
        {story.is_new ? (
          <View style={[styles.newPill, { backgroundColor: colors.overlay, borderColor: colors.brand }]}>
            <Text style={[styles.newPillText, { color: colors.brand }]}>{t.new_badge}</Text>
          </View>
        ) : null}
        <View style={{ flex: 1 }} />
        {read ? (
          <View style={[styles.readPill, { backgroundColor: colors.overlay }]}>
            <Ionicons name="checkmark" size={12} color={colors.success} />
          </View>
        ) : null}
      </View>
      <View style={styles.rowBody}>
        <View style={styles.metaLine}>
          <CategoryTag name={story.category_name} icon={story.category_icon} color={story.category_color} />
          <View style={{ flex: 1 }} />
          <MetaPill icon="time-outline" label={`${story.reading_time_min} ${t.min}`} />
        </View>
        <Text style={styles.rowTitle} numberOfLines={2}>{story.title}</Text>
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
  subtitle: { color: colors.muted, fontFamily: typography.body, fontSize: 11, textAlign: "center", lineHeight: 15 },
  chipsRow: { height: 56, justifyContent: "center" },
  chipsContent: { gap: 8, paddingHorizontal: spacing.xl, alignItems: "center" },
  onlyNewRow: {
    paddingHorizontal: spacing.xl, paddingTop: spacing.sm, paddingBottom: spacing.xs,
    flexDirection: "row",
  },
  onlyNewPill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingLeft: spacing.md, paddingRight: 6, paddingVertical: 6,
    borderRadius: radius.pill, borderWidth: 1,
  },
  onlyNewText: { fontFamily: typography.bodyBold, fontSize: 12 },
  onlyNewCount: { minWidth: 20, height: 20, paddingHorizontal: 6, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  onlyNewCountText: { fontFamily: typography.bodyBold, fontSize: 10 },
  chip: {
    height: 36, paddingHorizontal: spacing.md, borderRadius: radius.pill,
    borderWidth: 1, alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  chipText: { fontFamily: typography.bodyBold, fontSize: 12 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
  empty: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, paddingHorizontal: spacing.xxl },
  emptyText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 21 },
  row: {
    height: 176, justifyContent: "space-between", overflow: "hidden",
    borderRadius: radius.lg + 4, backgroundColor: colors.surfaceSecondary,
    borderWidth: 1, borderColor: colors.border, marginBottom: spacing.md,
  },
  rowTop: { flexDirection: "row", alignItems: "center", gap: spacing.sm, padding: spacing.md },
  rowBody: { padding: spacing.lg, paddingTop: 0, gap: spacing.sm + 2 },
  metaLine: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  rowTitle: {
    color: colors.onGradient, fontFamily: typography.displayBold, fontSize: 19, lineHeight: 24, letterSpacing: -0.3,
    textShadowColor: "rgba(0,0,0,0.5)", textShadowRadius: 8,
  },
  newPill: {
    paddingHorizontal: 7, paddingVertical: 3, borderRadius: radius.pill,
    borderWidth: 1, flexShrink: 0,
  },
  newPillText: { fontFamily: typography.bodyBold, fontSize: 9, letterSpacing: 1 },
  readPill: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center" },
  locked: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.lg, paddingHorizontal: spacing.xxl },
  lockOrb: {
    width: 72, height: 72, borderRadius: 36, alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },
  lockedText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 21 },
  cta: {
    flexDirection: "row", alignItems: "center", gap: spacing.sm,
    paddingVertical: spacing.md, paddingHorizontal: spacing.xl, borderRadius: radius.pill,
  },
  ctaText: { fontFamily: typography.bodyBold, fontSize: 14 },
}));
