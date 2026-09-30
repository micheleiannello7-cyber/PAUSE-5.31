import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSegments } from "expo-router";
import { api } from "@/src/api";
import { useUserId } from "@/src/session";

// Watches the limit. If blocked, redirects to /pause-limit unless we're already
// on the pause-limit or onboarding screens. Also exposes remaining seconds so
// UI (badge/timer) can subscribe.
export function useLimitGate() {
  const userId = useUserId();
  const router = useRouter();
  const segments = useSegments();

  const q = useQuery({
    queryKey: ["limit", userId],
    queryFn: () => api.limitCheck(userId!),
    enabled: !!userId,
    refetchInterval: 30_000,
  });

  useEffect(() => {
    // Let the reader finish the current story: redirect only from the tabs / other screens.
    const inLimit = (segments as string[]).some((s) =>
      s === "pause-limit" || s === "onboarding" || s === "deep-dive" || s === "story" || s === "history",
    );
    if (q.data?.blocked && !inLimit) {
      router.replace("/pause-limit");
    }
  }, [q.data?.blocked, segments, router, q.data]);

  return q.data;
}
