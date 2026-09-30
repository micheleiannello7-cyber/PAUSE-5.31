// PAUSE — on web the browser HTTP cache handles repeated plays (the audio
// URL is content-versioned and served immutable); no file cache needed.
export function getCachedAudioUri(_key: string): string | null {
  return null;
}

export async function cacheAudioInBackground(_key: string, _url: string): Promise<void> {}
