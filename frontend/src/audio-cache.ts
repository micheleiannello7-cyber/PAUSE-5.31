// PAUSE — transparent local audio cache (native). The first play streams the
// persistent URL while the same file is downloaded once into the OS cache
// directory; every later play of that asset key is served from disk, so the
// backend / storage are never asked for the same bytes twice. The OS may
// purge this directory under pressure (unlike the Premium "offline" copy in
// the document directory, see offline-audio.ts).
import { Directory, File, Paths } from "expo-file-system";

const inflight = new Set<string>();

function dir(): Directory {
  const d = new Directory(Paths.cache, "pause-audio-cache");
  if (!d.exists) d.create();
  return d;
}

function fileFor(key: string): File {
  return new File(dir(), `${key}.mp3`);
}

export function getCachedAudioUri(key: string): string | null {
  try {
    const f = fileFor(key);
    return f.exists && (f.size ?? 0) > 0 ? f.uri : null;
  } catch {
    return null;
  }
}

export async function cacheAudioInBackground(key: string, url: string): Promise<void> {
  if (inflight.has(key) || getCachedAudioUri(key)) return;
  inflight.add(key);
  try {
    const target = fileFor(key);
    const tmp = new File(dir(), `${key}.part`);
    if (tmp.exists) tmp.delete();
    const out = await File.downloadFileAsync(url, tmp);
    if (target.exists) target.delete();
    out.move(target);
  } catch {
    // Streaming already works; a failed cache fill just means we retry next time.
  } finally {
    inflight.delete(key);
  }
}
