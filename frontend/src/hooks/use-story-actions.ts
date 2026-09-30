// Optimistic bookmark / like toggles shared by Story preview and Deep Dive.
// The icon flips instantly (with a light haptic) and the server response is
// reconciled afterwards; on failure the previous state is restored. A 402
// from the API means the free quota (20 saved / 20 hearts) is full: we roll
// back and offer the paywall.
import { useCallback } from "react";
import { Alert } from "react-native";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import * as Haptics from "@/src/haptics";

import { api, ApiError, UserState } from "@/src/api";
import { useI18n } from "@/src/i18n";

type Kind = "bookmark" | "like";
const FIELD: Record<Kind, "bookmarked_story_ids" | "liked_story_ids"> = {
  bookmark: "bookmarked_story_ids",
  like: "liked_story_ids",
};

export function useStoryActions(userId: string | null | undefined, storyId: string | undefined) {
  const qc = useQueryClient();
  const router = useRouter();
  const { t } = useI18n();

  const toggle = useCallback(
    async (kind: Kind) => {
      if (!userId || !storyId) return;
      const key = ["user", userId];
      const field = FIELD[kind];
      const previous = qc.getQueryData<UserState>(key);

      try {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
      } catch {}

      if (previous) {
        const has = previous[field].includes(storyId);
        qc.setQueryData<UserState>(key, {
          ...previous,
          [field]: has ? previous[field].filter((x) => x !== storyId) : [...previous[field], storyId],
        });
      }

      try {
        const next = kind === "bookmark"
          ? await api.toggleBookmark(userId, storyId)
          : await api.toggleLike(userId, storyId);
        qc.setQueryData<UserState>(key, next);
      } catch (e) {
        if (previous) qc.setQueryData<UserState>(key, previous);
        if (e instanceof ApiError && e.status === 402) {
          Alert.alert(t.saved_limit_title, t.saved_limit_body, [
            { text: t.not_now, style: "cancel" },
            { text: t.go_premium, onPress: () => router.push("/premium") },
          ]);
        }
      } finally {
        qc.invalidateQueries({ queryKey: ["bookmarks"] });
      }
    },
    [qc, userId, storyId, router, t],
  );

  return { toggle };
}
