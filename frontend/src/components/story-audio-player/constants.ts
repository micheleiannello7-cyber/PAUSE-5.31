// PAUSE — Story audio player: shared constants, types and formatters.

export const SPEEDS = [0.8, 1, 1.25, 1.5, 1.75, 2] as const;
export const FREE_MAX_SPEED = 1.5;
export const FULL_HEIGHT = 84;
export const RESUME_MIN_SECONDS = 3;

export type Panel = "none" | "speed" | "voice";
export type OfflineState = "unsupported" | "none" | "downloading" | "ready";

export function fmt(sec: number): string {
  if (!isFinite(sec) || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export const speedLabel = (v: number) => `${v}×`;
