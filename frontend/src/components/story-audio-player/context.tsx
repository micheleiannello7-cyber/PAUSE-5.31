// PAUSE — Story audio player: shared React context (owns the expo-audio
// player + all cross-component state). Split out of the monolithic file for
// clarity; behaviour is identical to the previous single-file version.

import React, {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from "react";
import { useAudioPlayer, useAudioPlayerStatus, setAudioModeAsync } from "expo-audio";
import { SharedValue, useSharedValue } from "react-native-reanimated";
import * as Haptics from "@/src/haptics";
import { useRouter } from "expo-router";

import { api, getApiLang, voiceSampleUrl, VoiceId, FREE_VOICE, TtsStatus, absoluteUrl } from "@/src/api";
import { usePremiumFlag } from "@/src/premium";
import { useUserId } from "@/src/session";
import { useAudioPrefs, getSavedPosition, savePosition, clearPosition } from "@/src/audio-prefs";
import { OFFLINE_SUPPORTED, offlineKey, getOfflineUri, downloadOffline, removeOffline } from "@/src/offline-audio";
import { getCachedAudioUri, cacheAudioInBackground } from "@/src/audio-cache";

import { FREE_MAX_SPEED, FULL_HEIGHT, OfflineState, Panel, RESUME_MIN_SECONDS } from "./constants";

// How often we ask the backend whether a first-time narration is ready.
const GENERATION_POLL_MS = 2500;
const GENERATION_TIMEOUT_MS = 4 * 60 * 1000;

export type Ctx = {
  playing: boolean;
  duration: number;
  position: number;
  progress: number;
  isLoaded: boolean;
  buffering: boolean;
  isPremium: boolean;
  rate: number;
  setRate: (v: number) => void;
  voice: VoiceId;
  setVoice: (v: VoiceId) => void;
  playSample: (v: VoiceId) => void;
  panel: Panel;
  setPanel: (p: Panel | ((prev: Panel) => Panel)) => void;
  togglePlay: () => void;
  skip: (delta: number) => void;
  preview: boolean;
  resumeFrom: number | null;
  /** True when the narration could not be generated right now (provider error). */
  unavailable: boolean;
  offline: OfflineState;
  download: () => void;
  removeDownload: () => void;
  cardScreenYSV: SharedValue<number>;
  cardHeightSV: SharedValue<number>;
};

const AudioCtx = createContext<Ctx | null>(null);

export function useAudio(): Ctx {
  const ctx = useContext(AudioCtx);
  if (!ctx) throw new Error("Audio components must be used inside <StoryAudioProvider>");
  return ctx;
}

export function StoryAudioProvider({
  storyId, preview = false, autoplay = false, onFinished, children,
}: {
  storyId: string;
  preview?: boolean;
  autoplay?: boolean;
  onFinished?: () => void;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const userId = useUserId();
  const isPremium = usePremiumFlag();
  const premiumRef = useRef(isPremium);
  premiumRef.current = isPremium;
  const [prefs, updatePrefs] = useAudioPrefs();
  const lang = getApiLang();

  // Free listeners always get Nova at ≤1.5× even if prefs were set while premium.
  const voice: VoiceId = isPremium ? prefs.voice : FREE_VOICE;
  const rate = isPremium ? prefs.rate : Math.min(prefs.rate, FREE_MAX_SPEED);

  const offKey = offlineKey(storyId, lang, voice);
  const [localUri, setLocalUri] = useState<string | null>(() => getOfflineUri(offKey));
  useEffect(() => { setLocalUri(getOfflineUri(offKey)); }, [offKey]);

  // --- Asset resolution ----------------------------------------------------
  // Ask the backend whether this story+lang+voice+content already has audio.
  // Nothing is generated until the listener actually taps play (no
  // speculative TTS cost); once generated the URL is persistent and cached.
  const [status, setStatus] = useState<TtsStatus | null>(null);
  const [generating, setGenerating] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [wantPlay, setWantPlay] = useState(false);
  useEffect(() => {
    let alive = true;
    setStatus(null);
    setUnavailable(false);
    if (!isPremium) return;
    api.ttsStatus(storyId, { voice, preview }).then((s) => { if (alive) setStatus(s); }).catch(() => {});
    return () => { alive = false; };
  }, [storyId, lang, voice, preview, isPremium]);

  // Previews are a few seconds of speech: the server renders them inline.
  const remoteUrl = status && (status.ready || preview) ? absoluteUrl(status.url) : null;
  const cacheKey = status?.ready ? status.key : null;
  const [cachedUri, setCachedUri] = useState<string | null>(null);
  useEffect(() => { setCachedUri(cacheKey ? getCachedAudioUri(cacheKey) : null); }, [cacheKey]);

  const source = useMemo(() => {
    if (!isPremium) return null;
    const uri = localUri ?? cachedUri ?? remoteUrl;
    return uri ? { uri } : null;
  }, [localUri, cachedUri, remoteUrl, isPremium]);

  const player = useAudioPlayer(source);
  const status_ = useAudioPlayerStatus(player);
  const samplePlayer = useAudioPlayer();
  const [starting, setStarting] = useState(false);
  const [panel, setPanel] = useState<Panel>("none");
  const [resumeFrom, setResumeFrom] = useState<number | null>(null);
  useEffect(() => {
    if (isPremium) return;
    setWantPlay(false);
    setPanel("none");
    try { player.pause(); samplePlayer.pause(); } catch {}
  }, [isPremium, player, samplePlayer]);
  const [offline, setOffline] = useState<OfflineState>(
    !OFFLINE_SUPPORTED || preview ? "unsupported" : localUri ? "ready" : "none",
  );

  const firstSourceRef = useRef(true);
  useEffect(() => {
    if (firstSourceRef.current) { firstSourceRef.current = false; return; }
    if (!source) return;
    try { player.replace(source); } catch {}
  }, [player, source]);

  useEffect(() => {
    setAudioModeAsync({
      playsInSilentMode: true,
      shouldPlayInBackground: isPremium, // background listening is a Premium perk
      allowsRecording: false,
    }).catch(() => {});
  }, [isPremium]);

  useEffect(() => () => {
    try { player.pause(); } catch {}
    try { samplePlayer.pause(); } catch {}
  }, [player, samplePlayer]);

  useEffect(() => {
    try { player.setPlaybackRate(rate, "high"); } catch {}
  }, [player, rate, source]);

  const isLoaded = !!source && status_.isLoaded;
  const duration = isLoaded && isFinite(status_.duration) ? status_.duration : 0;
  const position = isLoaded ? status_.currentTime : 0;
  const playing = !!status_.playing;
  const buffering = starting || generating || (!!source && !isLoaded);
  const progress = duration > 0 ? Math.min(1, Math.max(0, position / duration)) : 0;

  // Fill the local cache once, the first time this asset actually plays, so
  // the next session never re-downloads it (native only; web = HTTP cache).
  useEffect(() => {
    if (!playing || preview || !cacheKey || cachedUri || localUri || !remoteUrl) return;
    cacheAudioInBackground(cacheKey, remoteUrl);
  }, [playing, preview, cacheKey, cachedUri, localUri, remoteUrl]);

  // First-ever listen of this content version: request generation and poll
  // until the persistent asset exists. Concurrent listeners share one job
  // server-side; the provider is called exactly once per combination.
  const ensureAudio = useCallback(async (): Promise<TtsStatus | null> => {
    if (!premiumRef.current) return null;
    if (status?.ready) return status;
    setGenerating(true);
    setUnavailable(false);
    try {
      await api.warmupTts(storyId, voice);
      const deadline = Date.now() + GENERATION_TIMEOUT_MS;
      while (premiumRef.current && Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, GENERATION_POLL_MS));
        if (!premiumRef.current) return null;
        const s = await api.ttsStatus(storyId, { voice, preview });
        if (!premiumRef.current) return null;
        if (s.ready) { setStatus(s); return s; }
        if (s.error && !s.generating) break; // provider failed: stop waiting
      }
      setUnavailable(true);
      return null;
    } catch {
      setUnavailable(true);
      return null;
    } finally {
      setGenerating(false);
    }
  }, [status, storyId, voice, preview]);

  useEffect(() => {
    if (!wantPlay || !isLoaded || !isPremium) return;
    setWantPlay(false);
    try { player.play(); } catch {}
  }, [wantPlay, isLoaded, player, isPremium]);

  // --- Exact resume (Premium) ---------------------------------------------
  const restoredRef = useRef<string | null>(null);
  useEffect(() => {
    if (!isLoaded || duration <= 0 || preview) return;
    const key = `${storyId}|${lang}`;
    if (restoredRef.current === key) return;
    restoredRef.current = key;
    if (!isPremium) return;
    getSavedPosition(storyId, lang).then((saved) => {
      if (saved > RESUME_MIN_SECONDS && saved < duration - RESUME_MIN_SECONDS) {
        setResumeFrom(saved);
        try { player.seekTo(saved); } catch {}
      }
    });
  }, [isLoaded, duration, storyId, lang, isPremium, preview, player]);

  const posBucket = Math.floor(position / 3);
  useEffect(() => {
    if (preview || !playing || position < RESUME_MIN_SECONDS) return;
    savePosition(storyId, lang, position);
  }, [posBucket, playing, preview, storyId, lang, position]);

  // --- End of track --------------------------------------------------------
  const finishedRef = useRef(false);
  useEffect(() => {
    if (status_.didJustFinish && !finishedRef.current) {
      finishedRef.current = true;
      if (!preview) clearPosition(storyId, lang);
      setResumeFrom(null);
      onFinished?.();
    }
    if (!status_.didJustFinish && playing) finishedRef.current = false;
  }, [status_.didJustFinish, playing, preview, storyId, lang, onFinished]);

  // --- Autoplay (playlist) -------------------------------------------------
  const autoRef = useRef(false);
  useEffect(() => {
    if (!isPremium || !autoplay || autoRef.current || !status) return;
    autoRef.current = true;
    if (source) { setWantPlay(true); return; }
    ensureAudio().then((s) => { if (s) setWantPlay(true); });
  }, [autoplay, status, source, ensureAudio, isPremium]);

  // --- Listening time → backend (flush every 30s and on unmount) -----------
  const listenedRef = useRef(0);
  const flush = useCallback(() => {
    if (!userId || listenedRef.current < 5 || preview) { listenedRef.current = 0; return; }
    const secs = Math.round(listenedRef.current);
    listenedRef.current = 0;
    api.listen(userId, storyId, secs).catch(() => {});
  }, [userId, storyId, preview]);
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      listenedRef.current += 1;
      if (listenedRef.current >= 30) flush();
    }, 1000);
    return () => clearInterval(id);
  }, [playing, flush]);
  useEffect(() => () => flush(), [flush]);

  const requirePremium = useCallback((fn: () => void) => {
    if (isPremium) fn();
    else router.push("/premium");
  }, [isPremium, router]);

  const setRate = (v: number) => {
    if (!premiumRef.current) return;
    if (v > FREE_MAX_SPEED) return requirePremium(() => updatePrefs({ rate: v }));
    updatePrefs({ rate: v });
  };
  const setVoice = (v: VoiceId) => {
    if (!premiumRef.current) return;
    if (v !== FREE_VOICE) return requirePremium(() => updatePrefs({ voice: v }));
    updatePrefs({ voice: v });
  };
  const playSample = (v: VoiceId) => {
    if (!premiumRef.current) return;
    Haptics.selectionAsync().catch(() => {});
    try {
      samplePlayer.replace({ uri: voiceSampleUrl(v) });
      samplePlayer.play();
    } catch {}
  };

  const togglePlay = async () => {
    if (!premiumRef.current) return;
    Haptics.selectionAsync().catch(() => {});
    if (playing) { player.pause(); return; }
    if (!source) {
      // Nothing to play yet: generate once (or wait for a job in progress),
      // then start as soon as the persistent asset is loaded.
      if (generating) return;
      setWantPlay(true);
      const s = await ensureAudio();
      if (!s) setWantPlay(false);
      return;
    }
    setStarting(true);
    try {
      if (duration > 0 && position >= duration - 0.2) await player.seekTo(0);
      setResumeFrom(null);
      player.play();
    } finally {
      setTimeout(() => setStarting(false), 500);
    }
  };

  const skip = (delta: number) => {
    if (!premiumRef.current) return;
    Haptics.selectionAsync().catch(() => {});
    const target = Math.max(0, Math.min(duration || Number.MAX_SAFE_INTEGER, position + delta));
    player.seekTo(target);
  };

  const download = () => requirePremium(async () => {
    if (offline !== "none") return;
    setOffline("downloading");
    try {
      const url = remoteUrl ?? (await ensureAudio().then((s) => (s ? absoluteUrl(s.url) : null)));
      if (!url) throw new Error("audio unavailable");
      await downloadOffline(offKey, url);
      setLocalUri(getOfflineUri(offKey));
      setOffline("ready");
    } catch {
      setOffline("none");
    }
  });
  const removeDownload = () => {
    removeOffline(offKey);
    setOffline("none");
    setLocalUri(null);
  };

  const cardScreenYSV = useSharedValue<number>(600);
  const cardHeightSV = useSharedValue<number>(FULL_HEIGHT);

  const value: Ctx = {
    playing, duration, position, progress, isLoaded, buffering, isPremium,
    rate, setRate, voice, setVoice, playSample,
    panel, setPanel, togglePlay, skip, preview, resumeFrom, unavailable,
    offline, download, removeDownload, cardScreenYSV, cardHeightSV,
  };

  return <AudioCtx.Provider value={value}>{children}</AudioCtx.Provider>;
}
