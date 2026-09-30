import { View, Text, ScrollView, Pressable, ActivityIndicator } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import Ionicons from "@react-native-vector-icons/ionicons";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography } from "@/src/theme";
import { useUserId } from "@/src/session";
import { useI18n } from "@/src/i18n";
import { RecapCard } from "@/src/components/recap-card";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";

// Screen opened from the counter badge on Home/Explore: shows ONLY the list of
// stories read in the current session ("Le tue pillole di oggi").
export default function ReadStories() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();

  const recap = useQuery({
    queryKey: ["session-stories", userId],
    queryFn: () => api.sessionStories(userId!),
    enabled: !!userId,
  });

  const empty = !!recap.data && recap.data.length === 0;

  return (
    <Screen style={[styles.container, { paddingTop: insets.top }]} testID="read-stories-screen">
      <View style={[styles.header, { paddingHorizontal: spacing.xl }]}>
        <Pressable onPress={() => router.back()} testID="read-stories-back" hitSlop={8} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={24} color={colors.onSurface} />
        </Pressable>
        <View style={styles.headerTitle}>
          <Text style={styles.title} numberOfLines={1} adjustsFontSizeToFit>
            {t.pl_recap_title}
          </Text>
          <Text style={styles.subtitle} numberOfLines={2}>{t.pl_recap_sub}</Text>
        </View>
        {/* Invisible spacer to keep the title visually centred. Same size as
            the back button, no fill/border so it doesn't render as a chip. */}
        <HomeButton testID="read-stories-home" />
      </View>

      {recap.isLoading ? (
        <View style={styles.loading}>
          <ActivityIndicator color={colors.brand} />
        </View>
      ) : empty ? (
        <View style={styles.empty} testID="read-stories-empty">
          <View style={styles.emptyOrb}>
            <Ionicons name="book-outline" size={34} color={colors.brand} />
          </View>
          <Text style={styles.emptyText}>{t.recap_empty}</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xl }}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.list} testID="read-stories-list">
            {recap.data?.map((s, i) => <RecapCard key={s.id} story={s} index={i + 1} />)}
          </View>
        </ScrollView>
      )}
    </Screen>
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
  list: { gap: spacing.md, paddingTop: spacing.md },
  empty: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, paddingHorizontal: spacing.xxl },
  emptyOrb: {
    width: 72, height: 72, borderRadius: 36, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  emptyText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 21 },
}));
