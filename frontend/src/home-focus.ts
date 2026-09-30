// PAUSE — Home: quali tessere categoria l'utente ha spento (per utente, in
// AsyncStorage). Si salva l'insieme delle SPENTE, non delle accese: così una
// categoria aggiunta in Esplora/onboarding si presenta accesa di default.
import AsyncStorage from "@react-native-async-storage/async-storage";

const key = (uid: string) => `pause.home_off.${uid}`;

export async function getHomeOffCategories(uid: string): Promise<string[]> {
  try {
    const raw = await AsyncStorage.getItem(key(uid));
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}

export async function saveHomeOffCategories(uid: string, off: string[]) {
  try {
    await AsyncStorage.setItem(key(uid), JSON.stringify(off));
  } catch {}
}
