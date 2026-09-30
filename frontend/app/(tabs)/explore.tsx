import { View, Text, ScrollView, ActivityIndicator, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/src/api";
import { makeStyles, spacing, typography } from "@/src/theme";
import { useUserId } from "@/src/session";
import { ALL_ID } from "@/src/components/category-grid";
import { TopicPicker, TopicsBackdrop } from "@/src/components/topic-picker";
import { LimitBadge } from "@/src/components/limit-badge";
import { ONB } from "@/src/components/onboarding-palette";
import { useI18n } from "@/src/i18n";
import { CoachTip } from "@/src/coach-tips";
import { useTopicPreferences } from "@/src/hooks/use-topic-preferences";

// Stesso picker dell'onboarding, con autosave e navigazione dei tab invariati.
export default function Explore() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const { t } = useI18n();
  const styles = useStyles();
  const cats = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const { selected, modes, onToggleCategory, onToggleMode, save, userQuery } = useTopicPreferences(userId, () => router.push("/premium"));
  const count = selected.has(ALL_ID) ? cats.data?.length ?? 0 : selected.size;
  const isPremium = !!userQuery.data?.is_premium;
  const failed = cats.isError || userQuery.isError;
  const loading = !cats.data || !userQuery.data;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]} testID="explore-screen">
      <TopicsBackdrop />
      <CoachTip id="topics" text={t.tip_topics} icon="grid-outline" style={{ bottom: insets.bottom + spacing.md }} />
      {failed ? (
        <View style={styles.message} testID="explore-load-error">
          <Text style={styles.errorText} testID="explore-load-error-text">{t.load_error}</Text>
          <Pressable testID="explore-retry" accessibilityRole="button" onPress={() => { cats.refetch(); userQuery.refetch(); }} style={({ pressed }) => [styles.retry, pressed && styles.pressed]}>
            <Text style={styles.status} testID="explore-retry-label">{t.retry}</Text>
          </Pressable>
        </View>
      ) : loading ? (
        <ActivityIndicator color={ONB.cyan} style={styles.message} testID="explore-loading" />
      ) : (
        <ScrollView style={styles.scroll} testID="explore-scroll" showsVerticalScrollIndicator={false}
          bounces={false} contentContainerStyle={{ paddingBottom: insets.bottom + spacing.md }}>
          <TopicPicker testID="explore" modeIdPrefix="explore" categories={cats.data!} selected={selected} modes={modes} columns={4}
            onToggleCategory={onToggleCategory} onToggleMode={onToggleMode} disabled={save.isPending} lockedModes={isPremium ? undefined : new Set(["lessons"])}
            titleAccessory={<LimitBadge testID="explore-limit-badge" />}
            status={<View testID="explore-save-status" accessibilityLiveRegion="polite">
              <View style={styles.statusRow}>
                <Text style={styles.status} testID="interests-count">{count === 0 ? t.no_interests : `${count} ${count === 1 ? t.interest_1 : t.interests}`}</Text>
                {save.isPending ? <ActivityIndicator size="small" color={ONB.cyan} testID="explore-saving" /> : null}
              </View>
              {save.isError ? <Text style={styles.saveError} testID="explore-save-error">{t.preferences_save_error}</Text> : null}
            </View>} />
        </ScrollView>
      )}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: ONB.bgTop },
  scroll: { flex: 1 },
  statusRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: spacing.sm, minHeight: 20 },
  status: { color: ONB.cyan, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 1.5, textTransform: "uppercase" },
  message: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, paddingHorizontal: spacing.xl },
  errorText: { color: ONB.text, fontFamily: typography.body, fontSize: 16, textAlign: "center" },
  saveError: { color: colors.warning, fontFamily: typography.body, fontSize: 13, lineHeight: 19, marginBottom: spacing.md },
  retry: { minHeight: 44, paddingHorizontal: spacing.xl, justifyContent: "center", borderWidth: 1, borderColor: ONB.glassBorder, borderRadius: 22 },
  pressed: { opacity: 0.7 },
}));