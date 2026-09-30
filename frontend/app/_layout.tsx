import { QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { LogBox, View, ActivityIndicator } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { useEffect } from "react";

import { ErrorBoundary } from "@/src/components/error-boundary";
import { MorphHost } from "@/src/components/morph-host";
import { queryClient } from "@/src/query-client";
import { ThemeProvider, useTheme } from "@/src/theme";
import { useLoadFonts } from "@/src/utils/fonts";
import { I18nProvider, useI18n } from "@/src/i18n";
import { loadPrefs } from "@/src/prefs-sync";
import { registerLaunch } from "@/src/coach-tips";
import { AuthProvider } from "@/src/auth";

// prewarm icon fonts on Android Expo Go — preserve original logic
import Ionicons from "@react-native-vector-icons/ionicons";
import Feather from "@react-native-vector-icons/feather";
try {
  // @ts-ignore
  Ionicons.loadFont?.();
  // @ts-ignore
  Feather.loadFont?.();
} catch {}

LogBox.ignoreAllLogs(true);

// Applies the preferences stored on the user's profile (theme, accent colour,
// language) once at startup. Local storage already seeded the first paint;
// the backend value wins only when the user made an explicit choice there
// (e.g. after a reinstall or on a new device).
function PrefsSync() {
  const { mode, accent, setMode, setAccent } = useTheme();
  const { lang, setLang } = useI18n();
  useEffect(() => {
    let alive = true;
    registerLaunch();
    loadPrefs().then((p) => {
      if (!alive) return;
      if (p.theme_mode && p.theme_mode !== mode) setMode(p.theme_mode);
      if (p.theme_accent && p.theme_accent !== accent) setAccent(p.theme_accent);
      if (p.lang && p.lang !== lang) setLang(p.lang);
    });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on mount
  }, []);
  return null;
}

// Waits for fonts + persisted language/theme before mounting routes (avoids a
// first fetch in the wrong language or a flash of the wrong scheme).
function AppStack({ fontsLoaded }: { fontsLoaded: boolean }) {
  const { ready } = useI18n();
  const { colors, scheme, ready: themeReady } = useTheme();
  if (!fontsLoaded || !ready || !themeReady) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.surface, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator color={colors.brand} />
      </View>
    );
  }
  return (
    <>
      <PrefsSync />
      <StatusBar style={scheme === "dark" ? "light" : "dark"} />
      <MorphHost>
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.surface },
          // Transizioni fluide ovunque: push nativo stile iOS (la schermata
          // sotto scivola indietro con parallasse e si scurisce) anche su
          // Android, con gesto di ritorno a tutto schermo; le schermate
          // "modali" salgono dal basso. Sul web (nessuna transizione nativa)
          // ogni schermata entra con un fade morbido, vedi <Screen />.
          animation: "ios_from_right",
          animationDuration: 380,
          animationMatchesGesture: true,
          gestureEnabled: true,
          fullScreenGestureEnabled: true,
        }}
      >
        <Stack.Screen name="index" options={{ animation: "fade", animationDuration: 300 }} />
        <Stack.Screen name="onboarding" options={{ animation: "fade", animationDuration: 450 }} />
        <Stack.Screen name="(tabs)" options={{ animation: "fade", animationDuration: 450 }} />
        {/* Il lettore gestisce da sé lo swipe verso destra (vedi <SwipeBack />).
            Aperto dalla card della Home (morph=1) entra senza animazione nativa:
            la transizione è il livello <StoryMorph /> sopra lo stack. */}
        <Stack.Screen name="deep-dive/[id]" options={({ route }) => ({
          gestureEnabled: false, fullScreenGestureEnabled: false,
          animation: (route.params as { morph?: string } | undefined)?.morph === "1" ? "none" : "ios_from_right",
        })} />
        <Stack.Screen name="pause-limit" options={{ animation: "fade_from_bottom", animationDuration: 420 }} />
        <Stack.Screen name="premium" options={{ presentation: "modal", animation: "slide_from_bottom", animationDuration: 400 }} />
        <Stack.Screen name="unlock" options={{ presentation: "modal", animation: "slide_from_bottom", animationDuration: 400 }} />
      </Stack>
      </MorphHost>
    </>
  );
}

function Root() {
  const fontsLoaded = useLoadFonts();
  const { colors } = useTheme();
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: colors.surface }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <I18nProvider>
              <AppStack fontsLoaded={fontsLoaded} />
            </I18nProvider>
          </AuthProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <Root />
      </ThemeProvider>
    </ErrorBoundary>
  );
}
