// PAUSE — "Resume reading": remembers the last deep-dive the user left
// half-read (per user, in AsyncStorage) so Home can offer a one-tap resume.
import AsyncStorage from "@react-native-async-storage/async-storage";
import { api, StoryPreview } from "@/src/api";

export type ReadingProgress = {
  story: StoryPreview;
  page: number; // pager index inside the deep-dive (0 = intro)
  progress: number; // 0..1 through the deep-dive
  updatedAt: number;
};

const key = (uid: string) => `pause.reading.${uid}`;

// Keep only the light preview fields (no chapters) so the stored blob stays small.
export function toStoryPreview(s: StoryPreview): StoryPreview {
  return {
    id: s.id,
    category_id: s.category_id,
    category_name: s.category_name,
    category_icon: s.category_icon,
    category_color: s.category_color,
    title: s.title,
    highlight_words: s.highlight_words,
    hook: s.hook,
    hero_image: s.hero_image,
    hero_image_generated: s.hero_image_generated,
    reading_time_min: s.reading_time_min,
    deep_dive_time_min: s.deep_dive_time_min,
    kind: s.kind,
    objective: s.objective,
  };
}

export async function saveReadingProgress(uid: string, p: ReadingProgress) {
  try {
    await AsyncStorage.setItem(key(uid), JSON.stringify(p));
  } catch {}
}

export async function getReadingProgress(uid: string): Promise<ReadingProgress | null> {
  try {
    const raw = await AsyncStorage.getItem(key(uid));
    const progress = raw ? (JSON.parse(raw) as ReadingProgress) : null;
    if (progress?.story.category_id === "curiosita") {
      try {
        const story = await api.story(progress.story.id);
        const refreshed = { ...progress, story: toStoryPreview(story) };
        await saveReadingProgress(uid, refreshed);
        return refreshed;
      } catch {
        // Offline: retain the same page and progress, never discard the session.
      }
    }
    return progress;
  } catch {
    return null;
  }
}

export async function clearReadingProgress(uid: string) {
  try {
    await AsyncStorage.removeItem(key(uid));
  } catch {}
}
