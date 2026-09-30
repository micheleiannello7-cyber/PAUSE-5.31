// PAUSE — API client. Uses Expo config with the public env fallback.
import Constants from "expo-constants";
export const BASE = Constants.expoConfig?.extra?.backendUrl ?? process.env.EXPO_PUBLIC_BACKEND_URL;
if (!BASE) {
  // Fail loudly at startup instead of producing "undefined/api/..." requests
  // that surface as a generic network error much later.
  console.error("[PAUSE] EXPO_PUBLIC_BACKEND_URL is not set in frontend/.env — API calls will fail.");
}

// Current content language — set by the I18nProvider. Appended to every GET.
let currentLang = "it";
export function setApiLang(lang: string) {
  currentLang = lang;
}
export function getApiLang() {
  return currentLang;
}

// Bearer token dell'account (Google/Apple) — impostato da src/auth.tsx.
let authToken: string | null = null;
export function setApiAuthToken(token: string | null) {
  authToken = token;
}

// Abort a request that stalls so a flaky connection never traps the UI on a
// spinner forever (react-query can then retry / surface an error state).
const REQUEST_TIMEOUT_MS = 15000;

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(status: number, path: string, code?: string) {
    super(`API ${status} ${path}`);
    this.status = status;
    this.code = code;
  }
}

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const isGet = !opts?.method || opts.method === "GET";
  const url = isGet ? `${BASE}/api${path}${path.includes("?") ? "&" : "?"}lang=${currentLang}` : `${BASE}/api${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      ...opts,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(opts?.headers ?? {}),
      },
    });
    if (!res.ok) {
      let code: string | undefined;
      try {
        const body = await res.json();
        code = typeof body?.detail === "object" ? body.detail?.code : undefined;
      } catch {}
      throw new ApiError(res.status, path, code);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export type Category = {
  id: string;
  name: string;
  story_count: number;
  lesson_count: number;
  icon: string;
  color: string;
  emoji_key: string;
  illustration_generated?: string | null;
};

// URL for a category illustration (AI generated).
export function categoryIllustrationUrl(cat: Pick<Category, "id" | "illustration_generated">): string | null {
  if (!cat.illustration_generated) return null;
  return categoryArtworkUrl(cat.id, cat.illustration_generated);
}

export function categoryArtworkUrl(id: string, version: string, cutout = false, tight = false): string {
  // Content-addressed artwork + a shared delivery revision reset any old
  // cached image/failure state when moving to the new sculptural 3D family.
  // `cutout` = solo l'oggetto 3D, senza lo sfondo nero dello studio;
  // `tight` = ritaglio stretto sull'oggetto (stessa altezza visiva delle altre icone 3D).
  return `${BASE}/api/category-media/${encodeURIComponent(id)}?v=${encodeURIComponent(version)}&delivery=reference-3d-v7${cutout ? "&cutout=true&cut=2" : ""}${cutout && tight ? "&tight=true" : ""}`;
}

export type Chapter = {
  number: number;
  title: string;
  body: string;
  icon: string;
  glow_color: string;
};

export type StoryPreview = {
  id: string;
  category_id: string;
  category_name: string;
  category_icon: string;
  category_color: string;
  title: string;
  highlight_words: string[];
  hook: string;
  hero_image: string;
  hero_image_generated?: string | null;
  hero_image_thumb?: string | null;
  reading_time_min: number;
  deep_dive_time_min: number;
  kind?: "story" | "lesson";
  objective?: string | null;
  is_new?: boolean;
};

export type StoryRecap = StoryPreview & { summary: string };

// Story credits ("storie disponibili"): token bucket, +1 every recharge_seconds.
export type LimitCheck = {
  enforce: boolean; credits: number; capacity: number; recharge_seconds: number;
  next_credit_in: number; next_credit_at?: string | null;
  session_count: number; session_seconds: number; limit: number; is_premium: boolean;
  reached: boolean; blocked: boolean; blocked_until?: string | null; remaining_seconds?: number;
};

export type HistoryItem = { story: StoryPreview; read_at: string; reread: boolean };
export type HistoryResponse = {
  items: HistoryItem[]; is_premium: boolean; window_days: number | null; hidden_count: number; total: number;
};

export type Story = StoryPreview & {
  chapters: Chapter[];
  summary: string;
};

export type UserState = {
  user_id: string;
  interests: string[];
  completed_story_ids: string[];
  bookmarked_story_ids: string[];
  liked_story_ids: string[];
  session_count: number;
  total_minutes: number;
  streak_days: number;
  best_streak: number;
  last_active_date: string | null;
  limit_enabled: boolean;
  is_premium: boolean;
  listen_seconds: number;
  unlocked_categories: string[];
  content_modes: ("stories" | "lessons")[];
  theme_mode?: "light" | "dark" | "system" | null;
  theme_accent?: string | null;
  lang?: "it" | "en" | null;
  display_name?: string | null;
  gender?: Gender | null;
  age?: number | null;
};

export type Gender = "man" | "woman" | "other";
export type ProfileInput = { display_name?: string; gender?: Gender; age?: number };

export type Playlist = { minutes: number; total_min: number; stories: StoryPreview[] };

export type StatsCategory = {
  id: string; name: string; icon: string; color: string; read: number; total: number; ratio: number;
};
export type Badge = {
  id: string; icon: string; title: string; description: string; target: number; value: number; unlocked: boolean;
};
export type Stats = {
  stories: number;
  minutes: number;
  listen_minutes: number;
  streak_days: number;
  best_streak: number;
  categories_explored: number;
  categories_total: number;
  categories: StatsCategory[];
  history: { date: string; active: boolean }[];
  badges: Badge[];
  badges_unlocked: number;
  month: {
    key: string; stories: number; minutes: number; listen_minutes: number;
    active_days: number; categories: number; top_category: StatsCategory | null;
  };
};

export type VoiceId = "nova" | "onyx" | "echo" | "shimmer";
export const VOICES: VoiceId[] = ["nova", "onyx", "echo", "shimmer"];
export const FREE_VOICE: VoiceId = "nova";
export const FREE_SAVED_LIMIT = 20;

// True when the story has any cover to show (AI generated or curated photo).
export function hasHero(story: StoryPreview | Story): boolean {
  return !!story.hero_image_generated || !!story.hero_image;
}

// Mini lessons: guided step-by-step content (kind="lesson" + objective).
export function isLesson(story: StoryPreview | Story): boolean {
  return story.kind === "lesson";
}

// Cover URL. Generated covers come from Object Storage through the backend
// (content-addressed path → `?v=` makes the URL immutable-cacheable);
// `size: "thumb"` picks the ≤600px WebP for lists. Curated Unsplash photos
// are already served by a CDN in WebP/AVIF; we only ask for a smaller width
// when a thumbnail is enough.
export function heroUrl(story: StoryPreview | Story, size: "hero" | "thumb" = "hero"): string {
  if (story.hero_image_generated) {
    const path = (size === "thumb" && story.hero_image_thumb) || story.hero_image_generated;
    return `${BASE}/api/media/${story.id}?size=${size}&v=${encodeURIComponent(path)}`;
  }
  if (size === "thumb" && story.hero_image.includes("images.unsplash.com")) {
    return story.hero_image.replace(/([?&])w=\d+/, "$1w=600");
  }
  return story.hero_image;
}

export type TtsStatus = {
  story_id: string;
  lang: string;
  voice: VoiceId;
  content_hash: string;
  ready: boolean;
  generating: boolean;
  error: string | null; // last generation failure for this combination (recent)
  key: string | null;
  size: number | null;
  url: string; // path under BASE, versioned with the content hash
};

export function absoluteUrl(path: string): string {
  return path.startsWith("http") ? path : `${BASE}${path}`;
}

export function voiceSampleUrl(voice: VoiceId): string {
  return `${BASE}/api/tts/voice-sample?voice=${voice}&lang=${currentLang}`;
}

export type AuthUser = {
  user_id: string;
  email: string | null;
  name: string | null;
  picture: string | null;
  provider: "google" | "apple" | null;
};
export type AuthResult = { session_token: string; user: AuthUser };

export const api = {
  authSession: (session_id: string) =>
    req<AuthResult>(`/auth/session`, { method: "POST", body: JSON.stringify({ session_id }) }),
  authApple: (identity_token: string, full_name: string | null, email: string | null) =>
    req<AuthResult>(`/auth/apple`, { method: "POST", body: JSON.stringify({ identity_token, full_name, email }) }),
  authMe: () => req<AuthUser>(`/auth/me`),
  authLogout: () => req<{ ok: boolean }>(`/auth/logout`, { method: "POST" }),
  categories: () => req<Category[]>("/categories"),
  /** id categoria → URL assoluto del clip hero (~3s), solo per quelle generate. */
  categoryClips: async () => {
    const m = await req<Record<string, string>>("/category-clips");
    return Object.fromEntries(Object.entries(m).map(([k, v]) => [k, `${BASE}${v}`]));
  },
  stories: (params?: { category_id?: string; interests?: string[]; limit?: number; user_id?: string }) => {
    const qs = new URLSearchParams();
    if (params?.category_id) qs.set("category_id", params.category_id);
    if (params?.interests?.length) qs.set("interests", params.interests.join(","));
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.user_id) qs.set("user_id", params.user_id);
    const s = qs.toString();
    return req<StoryPreview[]>(`/stories${s ? "?" + s : ""}`);
  },
  discoverNext: (user_id: string, interests?: string[], exclude?: string[]) => {
    const qs = new URLSearchParams({ user_id });
    if (interests?.length) qs.set("interests", interests.join(","));
    if (exclude?.length) qs.set("exclude", exclude.join(","));
    return req<StoryPreview>(`/discover-next?${qs.toString()}`);
  },
  /** Un intero mazzo (fino a 14 storie uniche) in una sola richiesta. */
  discoverBatch: (user_id: string, interests?: string[], exclude?: string[], count = 7) => {
    const qs = new URLSearchParams({ user_id, count: String(count) });
    if (interests?.length) qs.set("interests", interests.join(","));
    if (exclude?.length) qs.set("exclude", exclude.join(","));
    return req<StoryPreview[]>(`/discover-batch?${qs.toString()}`);
  },
  story: (id: string) => req<Story>(`/stories/${id}`),
  related: (id: string) => req<StoryPreview[]>(`/stories/${id}/related`),
  nextStory: (id: string, user_id?: string) =>
    req<StoryPreview>(`/stories/${id}/next${user_id ? `?user_id=${user_id}` : ""}`),
  playlist: (user_id: string, minutes = 10) => req<Playlist>(`/playlist?user_id=${user_id}&minutes=${minutes}`),
  user: (id: string) => req<UserState>(`/user/${id}`),
  stats: (id: string) => req<Stats>(`/user/${id}/stats`),
  bookmarks: (id: string) => req<StoryPreview[]>(`/user/${id}/bookmarks`),
  sessionStories: (id: string) => req<StoryRecap[]>(`/user/${id}/session-stories`),
  setInterests: (user_id: string, interests: string[]) =>
    req<UserState>(`/user/interests`, { method: "POST", body: JSON.stringify({ user_id, interests }) }),
  setPremium: (user_id: string, active: boolean) =>
    req<UserState>(`/user/premium`, { method: "POST", body: JSON.stringify({ user_id, active }) }),
  setContentModes: (user_id: string, modes: ("stories" | "lessons")[]) =>
    req<UserState>(`/user/content-modes`, { method: "POST", body: JSON.stringify({ user_id, modes }) }),
  createPurchase: (user_id: string, category_id: string, return_url: string) =>
    req<{ purchase_id: string; checkout_url: string }>(`/purchases`, {
      method: "POST", body: JSON.stringify({ user_id, category_id, return_url }),
    }),
  purchaseStatus: (purchase_id: string) =>
    req<{ purchase_id: string; user_id: string; category_id: string; status: "pending" | "paid" | "cancelled" | "error" }>(
      `/purchases/${purchase_id}`,
    ),
  setLimitEnabled: (user_id: string, enabled: boolean) =>
    req<UserState>(`/user/limit-setting`, { method: "POST", body: JSON.stringify({ user_id, enabled }) }),
  setPreferences: (user_id: string, prefs: { theme_mode?: string; theme_accent?: string; lang?: string }) =>
    req<UserState>(`/user/preferences`, { method: "POST", body: JSON.stringify({ user_id, ...prefs }) }),
  setProfile: (user_id: string, profile: ProfileInput) =>
    req<UserState>(`/user/profile`, { method: "POST", body: JSON.stringify({ user_id, ...profile }) }),
  toggleBookmark: (user_id: string, story_id: string) =>
    req<UserState>(`/user/bookmark`, { method: "POST", body: JSON.stringify({ user_id, story_id }) }),
  toggleLike: (user_id: string, story_id: string) =>
    req<UserState>(`/user/like`, { method: "POST", body: JSON.stringify({ user_id, story_id }) }),
  complete: (user_id: string, story_id: string, minutes = 2, seconds = 0) =>
    req<UserState>(`/user/complete`, { method: "POST", body: JSON.stringify({ user_id, story_id, minutes, seconds }) }),
  listen: (user_id: string, story_id: string, seconds: number) =>
    req<UserState>(`/user/listen`, { method: "POST", body: JSON.stringify({ user_id, story_id, seconds }) }),
  limitCheck: (user_id: string) =>
    req<LimitCheck>(`/user/${user_id}/limit-check`),
  history: (user_id: string, filters?: { q?: string; category_id?: string; since?: string }) => {
    const qs = new URLSearchParams();
    if (filters?.q) qs.set("q", filters.q);
    if (filters?.category_id) qs.set("category_id", filters.category_id);
    if (filters?.since) qs.set("since", filters.since);
    const s = qs.toString();
    return req<HistoryResponse>(`/user/${user_id}/history${s ? "?" + s : ""}`);
  },
  ttsStatus: (story_id: string, opts?: { voice?: VoiceId; preview?: boolean }) => {
    const qs = new URLSearchParams();
    if (opts?.voice && opts.voice !== FREE_VOICE) qs.set("voice", opts.voice);
    if (opts?.preview) qs.set("preview", "true");
    const s = qs.toString();
    return req<TtsStatus>(`/tts/status/${story_id}${s ? "?" + s : ""}`);
  },
  warmupTts: (story_id: string, voice?: VoiceId) =>
    req<{ story_id: string; status: "cached" | "generating"; url: string }>(
      `/tts/warmup/${story_id}?lang=${currentLang}${voice && voice !== FREE_VOICE ? `&voice=${voice}` : ""}`,
      { method: "POST" },
    ),
};
