// PAUSE — Salvati. One clean list of the stories the reader bookmarked,
// grouped by category (with a filter row when there are several). Hearts
// ("Mi interessa") are NOT a list here: they only tune what the Home proposes.
import { useState, useMemo, useCallback } from "react";
import {
  View, Text, StyleSheet, Pressable, SectionList, ScrollView, ActivityIndicator, RefreshControl, TextInput,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Image } from "expo-image";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";

import { api, StoryPreview, heroUrl, isLesson } from "@/src/api";
import { colors, spacing, radius, typography } from "@/src/theme";
import { useUserId } from "@/src/session";
import { useStoryActions } from "@/src/hooks/use-story-actions";
import { getReadingProgress } from "@/src/reading-progress";
import { HighlightedTitle } from "@/src/components/highlighted-title";
import { LimitBadge } from "@/src/components/limit-badge";
import { KindBadge } from "@/src/components/kind-badge";
import { LessonCover } from "@/src/components/lesson-cover";
import { useI18n } from "@/src/i18n";
import { CoachTip } from "@/src/coach-tips";

type Cat = { id: string; name: string; color: string; icon: string };
type Section = { cat: Cat; data: StoryPreview[] };

export default function Bookmarks() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const [activeCat, setActiveCat] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const { t } = useI18n();

  const q = useQuery({
    queryKey: ["bookmarks", userId],
    queryFn: () => api.bookmarks(userId!),
    enabled: !!userId,
  });
  const progress = useQuery({
    queryKey: ["reading-progress", userId],
    queryFn: () => getReadingProgress(userId!),
    enabled: !!userId,
  });
  // Progress lives in AsyncStorage: re-read it every time the tab is shown.
  useFocusEffect(useCallback(() => { if (userId) progress.refetch(); }, [userId])); // eslint-disable-line react-hooks/exhaustive-deps

  // Group by category (biggest group first) — one section per category.
  const needle = search.trim().toLowerCase();
  const sections = useMemo<Section[]>(() => {
    const map = new Map<string, Section>();
    for (const s of q.data ?? []) {
      if (needle && !`${s.title} ${s.hook} ${s.category_name}`.toLowerCase().includes(needle)) continue;
      let sec = map.get(s.category_id);
      if (!sec) {
        sec = { cat: { id: s.category_id, name: s.category_name, color: s.category_color, icon: s.category_icon }, data: [] };
        map.set(s.category_id, sec);
      }
      sec.data.push(s);
    }
    return Array.from(map.values()).sort((a, b) => b.data.length - a.data.length);
  }, [q.data, needle]);

  const visible = activeCat ? sections.filter((s) => s.cat.id === activeCat) : sections;
  const count = q.data?.length ?? 0;
  const subtitle = count ? `${count} ${count === 1 ? t.saved_sub_1 : t.saved_sub_n}` : t.saved_sub_empty;
  // "Riprendi": the story left mid-read, if it's one of the saved ones.
  const resume = progress.data && q.data?.some((s) => s.id === progress.data!.story.id) ? progress.data : null;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]} testID="saved-screen">
      <CoachTip id="saved" text={t.tip_saved} icon="bookmark-outline" style={{ bottom: insets.bottom + spacing.md }} />
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <View style={styles.titleIcon}>
            <Ionicons name="bookmark" size={18} color={colors.brand} />
          </View>
          <Text style={styles.title}>{t.saved}</Text>
          <View style={{ flex: 1 }} />
          <LimitBadge testID="bookmarks-limit-badge" />
        </View>
        <Text style={styles.subtitle} testID="saved-subtitle">{subtitle}</Text>
      </View>

      {count > 0 ? (
        <View style={styles.searchWrap}>
          <Ionicons name="search-outline" size={16} color={colors.muted} />
          <TextInput
            value={search}
            onChangeText={setSearch}
            placeholder={t.saved_search_ph}
            placeholderTextColor={colors.muted}
            style={styles.searchInput}
            returnKeyType="search"
            autoCorrect={false}
            clearButtonMode="while-editing"
            testID="saved-search"
          />
          {search ? (
            <Pressable onPress={() => setSearch("")} hitSlop={8} testID="saved-search-clear">
              <Ionicons name="close-circle" size={16} color={colors.muted} />
            </Pressable>
          ) : null}
        </View>
      ) : null}

      {sections.length > 1 ? (
        <View style={styles.chipRowWrap}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
            <CatChip label={t.all_categories} color={colors.brand} active={activeCat === null} onPress={() => setActiveCat(null)} testID="saved-cat-all" />
            {sections.map(({ cat, data }) => (
              <CatChip
                key={cat.id}
                label={`${cat.name} · ${data.length}`}
                icon={cat.icon}
                color={cat.color}
                active={activeCat === cat.id}
                onPress={() => setActiveCat(activeCat === cat.id ? null : cat.id)}
                testID={`saved-cat-${cat.id}`}
              />
            ))}
          </ScrollView>
        </View>
      ) : null}

      {q.isLoading ? (
        <View style={styles.loading}><ActivityIndicator color={colors.brand} /></View>
      ) : (
        <SectionList
          sections={visible}
          keyExtractor={(s) => s.id}
          stickySectionHeadersEnabled={false}
          renderSectionHeader={({ section }) => (
            <View style={styles.sectionHead} testID={`saved-section-${section.cat.id}`}>
              <View style={[styles.sectionOrb, { backgroundColor: section.cat.color + "22", borderColor: section.cat.color + "55" }]}>
                <Ionicons name={section.cat.icon as any} size={13} color={section.cat.color} />
              </View>
              <Text style={styles.sectionName}>{section.cat.name}</Text>
              <Text style={styles.sectionCount}>{section.data.length}</Text>
            </View>
          )}
          renderItem={({ item }) => (
            <SavedCard story={item} userId={userId} onPress={() => router.push(`/deep-dive/${item.id}`)} />
          )}
          ListHeaderComponent={
            resume && !activeCat ? (
              <Pressable
                onPress={() => router.push(`/deep-dive/${resume.story.id}`)}
                style={({ pressed }) => [styles.resume, pressed && { opacity: 0.92 }]}
                testID="saved-resume"
              >
                <Ionicons name="play-circle" size={22} color={colors.brand} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.resumeEyebrow}>{t.saved_resume}</Text>
                  <Text style={styles.resumeTitle} numberOfLines={1}>{resume.story.title}</Text>
                </View>
                <View style={styles.resumeTrack}>
                  <View style={[styles.resumeFill, { width: `${Math.round(resume.progress * 100)}%` }]} />
                </View>
              </Pressable>
            ) : null
          }
          ListFooterComponent={
            count ? (
              <View style={styles.hint} testID="saved-like-hint">
                <Ionicons name="heart-outline" size={13} color={colors.muted} />
                <Text style={styles.hintText}>{t.saved_hint_like}</Text>
              </View>
            ) : null
          }
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl + insets.bottom }}
          ItemSeparatorComponent={() => <View style={{ height: spacing.sm }} />}
          SectionSeparatorComponent={() => <View style={{ height: spacing.sm }} />}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brand} />
          }
          ListEmptyComponent={
            needle ? (
              <View style={styles.empty} testID="saved-search-empty">
                <Ionicons name="search-outline" size={28} color={colors.muted} />
                <Text style={styles.emptyText}>{t.saved_search_empty}</Text>
              </View>
            ) : (
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>{t.saved_empty_title}</Text>
              <Text style={styles.emptyText}>{t.saved_empty_text}</Text>
              <Pressable style={styles.exploreBtn} onPress={() => router.push("/(tabs)/discover")} testID="explore-bookmarks">
                <Text style={styles.exploreText}>{t.discover_something}</Text>
                <Ionicons name="arrow-forward" size={16} color={colors.brand} />
              </Pressable>
            </View>
            )
          }
        />
      )}
    </View>
  );
}

function CatChip({
  label, icon, color, active, onPress, testID,
}: { label: string; icon?: string; color: string; active: boolean; onPress: () => void; testID: string }) {
  return (
    <Pressable
      onPress={onPress}
      testID={testID}
      style={[
        styles.catChip,
        active
          ? { backgroundColor: color + "22", borderColor: color }
          : { backgroundColor: colors.surfaceSecondary, borderColor: colors.border },
      ]}
    >
      {icon ? <Ionicons name={icon as any} size={12} color={active ? color : colors.muted} /> : null}
      <Text style={[styles.catChipText, { color: active ? color : colors.muted }]}>{label}</Text>
    </Pressable>
  );
}

// Uniform row: square thumb · title (2 lines) + meta · remove-bookmark button.
function SavedCard({ story, userId, onPress }: { story: StoryPreview; userId: string | null | undefined; onPress: () => void }) {
  const { t } = useI18n();
  const { toggle } = useStoryActions(userId, story.id);
  return (
    <Pressable onPress={onPress} testID={`bookmark-${story.id}`} style={({ pressed }) => [styles.card, { opacity: pressed ? 0.92 : 1 }]}>
      {isLesson(story) && !story.hero_image_generated ? (
        <LessonCover color={story.category_color} icon={story.category_icon} iconSize={28} showBadge={false} style={styles.thumb} />
      ) : (
        <Image source={{ uri: heroUrl(story, "thumb") }} style={styles.thumb} contentFit="cover" transition={200} cachePolicy="memory-disk" />
      )}
      <View style={styles.info}>
        <HighlightedTitle title={story.title} highlight={story.highlight_words} style={styles.cardTitle} highlightColor={colors.brand} numberOfLines={2} />
        <View style={styles.metaRow}>
          <Ionicons name="time-outline" size={11} color={colors.muted} />
          <Text style={styles.metaText}>{story.reading_time_min} {t.min}</Text>
          <KindBadge story={story} size="sm" />
          {story.is_new ? (
            <View style={[styles.newPill, { borderColor: colors.brand }]} testID={`bookmark-${story.id}-new`}>
              <Text style={[styles.newPillText, { color: colors.brand }]}>{t.new_badge}</Text>
            </View>
          ) : null}
        </View>
      </View>
      <Pressable onPress={() => toggle("bookmark")} hitSlop={8} style={styles.removeBtn} testID={`unsave-${story.id}`} accessibilityLabel={t.saved_remove}>
        <Ionicons name="bookmark" size={16} color={colors.brand} />
      </Pressable>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  header: {
    paddingHorizontal: spacing.xl, paddingTop: spacing.md, paddingBottom: spacing.md,
    gap: 6,
  },
  titleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  titleIcon: {
    width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.brand + "18", borderWidth: 1, borderColor: colors.brand + "40",
  },
  title: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 28, lineHeight: 34 },
  subtitle: { color: colors.muted, fontFamily: typography.body, fontSize: 13, marginLeft: 40 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
  searchWrap: {
    flexDirection: "row", alignItems: "center", gap: spacing.sm,
    marginHorizontal: spacing.xl, marginBottom: spacing.sm, paddingHorizontal: spacing.md, height: 42,
    borderRadius: radius.md, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  searchInput: { flex: 1, color: colors.onSurface, fontFamily: typography.body, fontSize: 14, paddingVertical: 0 },
  chipRowWrap: { height: 48, justifyContent: "center", marginBottom: spacing.xs },
  chipRow: { paddingHorizontal: spacing.xl, gap: spacing.sm, alignItems: "center" },
  catChip: {
    flexShrink: 0, flexDirection: "row", alignItems: "center", gap: 6,
    height: 34, paddingHorizontal: 12, borderRadius: radius.pill, borderWidth: 1,
  },
  catChipText: { fontFamily: typography.bodyBold, fontSize: 12, letterSpacing: 0.3 },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingTop: spacing.md, paddingBottom: spacing.sm },
  sectionOrb: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  sectionName: { flex: 1, color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 13, letterSpacing: 0.4, textTransform: "uppercase" },
  sectionCount: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 12 },
  card: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    backgroundColor: colors.surfaceSecondary, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border, padding: spacing.sm,
  },
  thumb: { width: 64, height: 64, borderRadius: radius.sm, overflow: "hidden" },
  info: { flex: 1, gap: 6, justifyContent: "center" },
  cardTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 14, lineHeight: 18 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  metaText: { color: colors.muted, fontFamily: typography.body, fontSize: 11, marginRight: 4 },
  newPill: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: radius.pill, borderWidth: 1, marginLeft: 6 },
  newPillText: { fontFamily: typography.bodyBold, fontSize: 8, letterSpacing: 1 },
  removeBtn: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.brand + "14", borderWidth: 1, borderColor: colors.brand + "44",
  },
  resume: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    padding: spacing.md, marginTop: spacing.sm, borderRadius: radius.md,
    backgroundColor: colors.brand + "12", borderWidth: 1, borderColor: colors.brand + "44",
  },
  resumeEyebrow: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 9, letterSpacing: 1.5 },
  resumeTitle: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 13, marginTop: 2 },
  resumeTrack: { width: 44, height: 4, borderRadius: 2, backgroundColor: colors.borderStrong, overflow: "hidden" },
  resumeFill: { height: "100%", backgroundColor: colors.brand },
  hint: { flexDirection: "row", alignItems: "flex-start", gap: 6, marginTop: spacing.xl, paddingHorizontal: spacing.xs },
  hintText: { flex: 1, color: colors.muted, fontFamily: typography.body, fontSize: 11, lineHeight: 15 },
  empty: { alignItems: "center", justifyContent: "flex-start", paddingTop: spacing.xxl, gap: spacing.sm, paddingHorizontal: spacing.xl },
  emptyTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 20, textAlign: "center" },
  emptyText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 20 },
  exploreBtn: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingVertical: 12, paddingHorizontal: spacing.xl,
    borderRadius: radius.pill, marginTop: spacing.md,
    borderWidth: 1, borderColor: colors.brand + "66",
  },
  exploreText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 14 },
});
