// PAUSE — preferences sync between the device and the user's backend profile.
//
// Theme, accent colour and language are stored on the user profile (server
// side) so they survive reinstalls and travel across devices. Local storage
// still seeds the first paint (no flash of the wrong theme); the backend value
// is applied on top when present, because it is only written on an explicit
// user choice. All calls are fire-and-forget: a sync failure must never
// block the UI (local persistence already covers the session).
import { api } from "@/src/api";
import { getOrCreateUserId } from "@/src/session";
import type { AccentId, ThemeMode } from "@/src/theme";
import type { Lang } from "@/src/i18n";

export type PrefsPatch = {
  theme_mode?: ThemeMode;
  theme_accent?: AccentId;
  lang?: Lang;
};

let uidPromise: Promise<string> | null = null;
function userId(): Promise<string> {
  if (!uidPromise) uidPromise = getOrCreateUserId();
  return uidPromise;
}

// Push a preference change to the profile (best effort).
export function savePrefs(patch: PrefsPatch) {
  userId()
    .then((id) => api.setPreferences(id, patch))
    .catch(() => {});
}

// Read the preferences stored on the profile (reinstall / new device).
export async function loadPrefs(): Promise<PrefsPatch> {
  try {
    const id = await userId();
    const s = await api.user(id);
    return {
      theme_mode: (s.theme_mode as ThemeMode) || undefined,
      theme_accent: (s.theme_accent as AccentId) || undefined,
      lang: (s.lang as Lang) || undefined,
    };
  } catch {
    return {};
  }
}
