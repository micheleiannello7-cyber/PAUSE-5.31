// PAUSE — vibrazione (feedback tattile) con interruttore globale.
// Stessa API di `expo-haptics` (impactAsync / selectionAsync /
// notificationAsync + enum), ma ogni chiamata è un no-op se il lettore ha
// spento la vibrazione in Profilo → Impostazioni. La scelta è salvata in
// locale e letta all'avvio.
import { useEffect, useState } from "react";
import * as ExpoHaptics from "expo-haptics";
import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "pause.haptics.v1";
let enabled = true;
const listeners = new Set<(v: boolean) => void>();

AsyncStorage.getItem(KEY).then((raw) => {
  if (raw === "0") { enabled = false; listeners.forEach((l) => l(false)); }
}).catch(() => {});

export const ImpactFeedbackStyle = ExpoHaptics.ImpactFeedbackStyle;
export const NotificationFeedbackType = ExpoHaptics.NotificationFeedbackType;

export function isHapticsEnabled() { return enabled; }

export async function setHapticsEnabled(value: boolean) {
  enabled = value;
  listeners.forEach((l) => l(value));
  try { await AsyncStorage.setItem(KEY, value ? "1" : "0"); } catch {}
}

export function useHapticsEnabled(): [boolean, (v: boolean) => void] {
  const [value, setValue] = useState(enabled);
  useEffect(() => {
    listeners.add(setValue);
    setValue(enabled);
    return () => { listeners.delete(setValue); };
  }, []);
  return [value, setHapticsEnabled];
}

export function impactAsync(style?: ExpoHaptics.ImpactFeedbackStyle): Promise<void> {
  return enabled ? ExpoHaptics.impactAsync(style) : Promise.resolve();
}
export function selectionAsync(): Promise<void> {
  return enabled ? ExpoHaptics.selectionAsync() : Promise.resolve();
}
export function notificationAsync(type?: ExpoHaptics.NotificationFeedbackType): Promise<void> {
  return enabled ? ExpoHaptics.notificationAsync(type) : Promise.resolve();
}
