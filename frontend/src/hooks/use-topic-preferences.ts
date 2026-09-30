import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Haptics from "@/src/haptics";
import { api } from "@/src/api";
import { StoryKind } from "@/src/components/kind-icon";
import { toggleInterest } from "@/src/components/category-grid";
import { toggleContentMode } from "@/src/components/onboarding-modes";

type Change = { interests: string[] } | { modes: StoryKind[] };

// Una sola scrittura alla volta: niente risposte fuori ordine tra formati e argomenti.
// `onLocked` fires when a free reader taps the Premium-only "mini lessons" mode.
export function useTopicPreferences(userId: string | null, onLocked?: () => void) {
  const qc = useQueryClient();
  const userQuery = useQuery({ queryKey: ["user", userId], queryFn: () => api.user(userId!), enabled: !!userId });
  const { data: user } = userQuery;
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [modes, setModes] = useState<Set<StoryKind>>(new Set(["stories", "lessons"]));
  const writing = useRef(false);
  const save = useMutation({
    mutationFn: (change: Change) => "interests" in change
      ? api.setInterests(userId!, change.interests) : api.setContentModes(userId!, change.modes),
    onMutate: () => qc.cancelQueries({ queryKey: ["user", userId] }),
    onSuccess: (state) => {
      // Il mazzo Home si aggiorna soltanto dopo la conferma reale del backend.
      qc.setQueryData(["user", userId], state);
      qc.invalidateQueries({ queryKey: ["discover-next"] });
      qc.invalidateQueries({ queryKey: ["browse"] });
    },
    onError: () => {
      setSelected(new Set(user?.interests ?? []));
      setModes(new Set(user?.content_modes ?? ["stories", "lessons"]));
    },
    onSettled: () => {
      writing.current = false;
      qc.invalidateQueries({ queryKey: ["user", userId] });
    },
  });
  useEffect(() => {
    if (!user || save.isPending) return;
    setSelected(new Set(user.interests));
    setModes(new Set(user.content_modes));
  }, [user, save.isPending]);

  const submit = (change: Change) => {
    if (!userId || !user || writing.current) return;
    writing.current = true;
    Haptics.selectionAsync().catch(() => {});
    if ("interests" in change) setSelected(new Set(change.interests));
    else setModes(new Set(change.modes));
    save.mutate(change);
  };
  const onToggleCategory = (id: string) => {
    submit({ interests: Array.from(toggleInterest(selected, id)) });
  };
  // Le mini lezioni sono solo Premium: per l'utente base il tocco apre il paywall.
  const onToggleMode = (mode: StoryKind) => {
    if (mode === "lessons" && !user?.is_premium) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
      onLocked?.();
      return;
    }
    const next = toggleContentMode(modes, mode);
    if (next.size !== modes.size) submit({ modes: Array.from(next) });
  };
  return { selected, modes, onToggleCategory, onToggleMode, save, userQuery };
}