// PAUSE — offline audio is a native-only feature; the web preview streams.
export const OFFLINE_SUPPORTED = false;

export function offlineKey(storyId: string, lang: string, voice: string) {
  return `${storyId}-${lang}-${voice}`;
}

export function getOfflineUri(_key: string): string | null {
  return null;
}

export async function downloadOffline(_key: string, _url: string): Promise<string> {
  throw new Error("Offline audio is not available on web");
}

export function removeOffline(_key: string) {}
