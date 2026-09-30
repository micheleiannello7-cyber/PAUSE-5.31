// Font loader for PAUSE — bundled fonts (Sora display, Manrope body).
import { useEffect, useState } from "react";
import * as Font from "expo-font";

export const FONT_SOURCES = {
  Sora_600SemiBold: require("../../assets/fonts/Sora-SemiBold.ttf"),
  Sora_700Bold: require("../../assets/fonts/Sora-Bold.ttf"),
  Manrope_400Regular: require("../../assets/fonts/Manrope-Regular.ttf"),
  Manrope_500Medium: require("../../assets/fonts/Manrope-Medium.ttf"),
  Manrope_600SemiBold: require("../../assets/fonts/Manrope-SemiBold.ttf"),
};

// Resolves to `true` once fonts are loaded. Fail-open after 3s so a hanging
// font request (restricted webviews) can never block the UI.
export function useLoadFonts() {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let cancelled = false;
    const done = () => {
      if (!cancelled) setReady(true);
    };
    const timer = setTimeout(done, 3000);
    Font.loadAsync(FONT_SOURCES)
      .catch(() => {})
      .finally(() => {
        clearTimeout(timer);
        done();
      });
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);
  return ready;
}
