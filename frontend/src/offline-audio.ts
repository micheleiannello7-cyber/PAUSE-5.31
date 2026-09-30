// PAUSE — offline audio (native). Downloads a narrated mp3 into the app's
// document directory so Premium listeners can play saved stories without a
// connection. The web build swaps in offline-audio.web.ts (unsupported).
import { Directory, File, Paths } from "expo-file-system";

export const OFFLINE_SUPPORTED = true;

function dir(): Directory {
  const d = new Directory(Paths.document, "pause-audio");
  if (!d.exists) d.create();
  return d;
}

function fileFor(key: string): File {
  return new File(dir(), `${key}.mp3`);
}

export function offlineKey(storyId: string, lang: string, voice: string) {
  return `${storyId}-${lang}-${voice}`;
}

export function getOfflineUri(key: string): string | null {
  try {
    const f = fileFor(key);
    return f.exists && (f.size ?? 0) > 0 ? f.uri : null;
  } catch {
    return null;
  }
}

export async function downloadOffline(key: string, url: string): Promise<string> {
  const target = fileFor(key);
  if (target.exists) target.delete();
  const out = await File.downloadFileAsync(url, target);
  return out.uri;
}

export function removeOffline(key: string) {
  try {
    const f = fileFor(key);
    if (f.exists) f.delete();
  } catch {}
}
