// PAUSE — audio preferences + playback memory, persisted on device.
//
//  - voice / speed / sleep-timer default   → `pause.audio.prefs`
//  - last known position per story         → `pause.audio.pos.<storyId>.<lang>`
//    ("Ripresa ascolto": Premium resumes from the exact second, free restarts)
import { useCallback, useEffect, useState } from "react";
import { storage } from "@/src/utils/storage";
import { FREE_VOICE, VoiceId, VOICES } from "@/src/api";

const PREFS_KEY = "pause.audio.prefs";
const posKey = (storyId: string, lang: string) => `pause.audio.pos.${storyId}.${lang}`;

export type AudioPrefs = { voice: VoiceId; rate: number };
const DEFAULT_PREFS: AudioPrefs = { voice: FREE_VOICE, rate: 1 };

let cached: AudioPrefs | null = null;
const listeners = new Set<(p: AudioPrefs) => void>();

async function load(): Promise<AudioPrefs> {
  if (cached) return cached;
  const raw = await storage.getItem(PREFS_KEY, "");
  let parsed: Partial<AudioPrefs> = {};
  try { parsed = raw ? JSON.parse(raw) : {}; } catch {}
  cached = {
    voice: VOICES.includes(parsed.voice as VoiceId) ? (parsed.voice as VoiceId) : FREE_VOICE,
    rate: typeof parsed.rate === "number" ? parsed.rate : 1,
  };
  return cached;
}

export async function saveAudioPrefs(patch: Partial<AudioPrefs>) {
  const next = { ...(await load()), ...patch };
  cached = next;
  await storage.setItem(PREFS_KEY, JSON.stringify(next));
  listeners.forEach((l) => l(next));
}

// Shared across every player instance (deep-dive, playlist, profile).
export function useAudioPrefs(): [AudioPrefs, (patch: Partial<AudioPrefs>) => Promise<void>] {
  const [prefs, setPrefs] = useState<AudioPrefs>(cached ?? DEFAULT_PREFS);
  useEffect(() => {
    let alive = true;
    load().then((p) => { if (alive) setPrefs(p); });
    const l = (p: AudioPrefs) => { if (alive) setPrefs(p); };
    listeners.add(l);
    return () => { alive = false; listeners.delete(l); };
  }, []);
  const update = useCallback((patch: Partial<AudioPrefs>) => saveAudioPrefs(patch), []);
  return [prefs, update];
}

export async function getSavedPosition(storyId: string, lang: string): Promise<number> {
  const v = await storage.getItem(posKey(storyId, lang), 0);
  return typeof v === "number" && isFinite(v) ? v : 0;
}

export async function savePosition(storyId: string, lang: string, seconds: number) {
  await storage.setItem(posKey(storyId, lang), Math.max(0, Math.floor(seconds)));
}

export async function clearPosition(storyId: string, lang: string) {
  await storage.removeItem(posKey(storyId, lang));
}
