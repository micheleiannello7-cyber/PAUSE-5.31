// PAUSE — design tokens + runtime theme (dark / light / system) with Premium
// accent palettes. Every colour in the UI comes from `useTheme().colors`
// (or `makeStyles`); hex literals are only used here.
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { StyleSheet, useColorScheme } from "react-native";
import { storage } from "@/src/utils/storage";

export type ColorScheme = "light" | "dark";
export type ThemeMode = ColorScheme | "system";
export type AccentId = "aurora" | "tramonto" | "foresta" | "oceano" | "orchidea";

const MODE_KEY = "pause.theme.mode";
const ACCENT_KEY = "pause.theme.accent";

// ---------------------------------------------------------------------------
// Base palettes (surfaces, text, lines, status). Accent colours are layered on.
// ---------------------------------------------------------------------------
const darkBase = {
  surface: "#05070C",
  onSurface: "#F4F5F8",
  surfaceSecondary: "#0D1018",
  onSurfaceSecondary: "#E0E2E8",
  surfaceTertiary: "#161A25",
  onSurfaceTertiary: "#C3C6D1",
  surfaceInverse: "#F4F5F8",
  onSurfaceInverse: "#05070C",
  muted: "#8A8F9E",

  success: "#00E676",
  onSuccess: "#000000",
  warning: "#FF9100",
  onWarning: "#000000",
  error: "#FF006A",
  onError: "#FFFFFF",

  border: "#1B1F2B",
  borderStrong: "#2B3040",
  divider: "#12151E",

  // Translucent helpers (pills over content, progress tracks, photo scrims).
  overlay: "rgba(16,18,26,0.85)",
  overlayStrong: "rgba(11,15,24,0.94)",
  track: "rgba(255,255,255,0.10)",
  glass: "rgba(255,255,255,0.06)",
  scrim: "rgba(5,7,12,0.55)",
  shadow: "#000000",

  // --- Glassmorphism design tokens -----------------------------------------
  // Vetro traslucido a due livelli (pill/card e superfici più grandi), con
  // bordo sottile luminoso, highlight superiore e ombra morbida.
  glassBg: "rgba(255,255,255,0.04)",       // superfici piatte (pill, badge)
  glassBgStrong: "rgba(20,26,40,0.55)",    // card, header, modal
  glassBgSoft: "rgba(255,255,255,0.02)",   // hover/pressed
  glassBorder: "rgba(255,255,255,0.10)",
  glassBorderStrong: "rgba(255,255,255,0.18)",
  glassHighlight: "rgba(255,255,255,0.24)", // linea luminosa sul bordo alto
  glassInner: "rgba(255,255,255,0.06)",     // inner glow molto sottile
  glassShadow: "rgba(0,0,0,0.45)",          // shadow diffusa per depth
  glassBgLit: "rgba(255,255,255,0.09)",     // vetro "illuminato" sopra le foto
  glassSheen: "rgba(255,255,255,0.13)",     // riflesso frosted dall'alto
  // Reading experience: bianco caldo per titolo/testo, tinta notte sull'immagine.
  textWarm: "#F7F3EB",
  textWarmSecondary: "#D9D4C9",
  nightTint: "rgba(8,14,30,0.30)",
  surfaceDeep: "#080B15",
  // Category art is a dark, image-backed surface in both themes.
  artworkSurface: "#05070C",
  // Occhiello "Introduzione" del lettore: pervinca, un colore tutto suo, distinto
  // dall'azzurro delle parole evidenziate, dai colori dei capitoli e dall'ambra di "Da ricordare".
  intro: "#A9B4FF",
};

const lightBase: typeof darkBase = {
  surface: "#F5F7FB",
  onSurface: "#0B0E17",
  surfaceSecondary: "#FFFFFF",
  onSurfaceSecondary: "#1C2130",
  surfaceTertiary: "#E9ECF4",
  onSurfaceTertiary: "#3A4052",
  surfaceInverse: "#0B0E17",
  onSurfaceInverse: "#F5F7FB",
  muted: "#5B6275",

  success: "#0F8A4B",
  onSuccess: "#FFFFFF",
  warning: "#B35C00",
  onWarning: "#FFFFFF",
  error: "#C8105A",
  onError: "#FFFFFF",

  border: "#DDE1EA",
  borderStrong: "#C3C9D6",
  divider: "#E8EBF2",

  overlay: "rgba(255,255,255,0.88)",
  overlayStrong: "rgba(255,255,255,0.96)",
  track: "rgba(11,14,23,0.10)",
  glass: "rgba(11,14,23,0.05)",
  scrim: "rgba(5,7,12,0.55)",
  shadow: "#1C2130",

  // --- Glassmorphism design tokens (light) ---------------------------------
  glassBg: "rgba(255,255,255,0.55)",
  glassBgStrong: "rgba(255,255,255,0.72)",
  glassBgSoft: "rgba(255,255,255,0.35)",
  glassBorder: "rgba(11,14,23,0.10)",
  glassBorderStrong: "rgba(11,14,23,0.18)",
  glassHighlight: "rgba(255,255,255,0.85)",
  glassInner: "rgba(11,14,23,0.04)",
  glassShadow: "rgba(28,33,48,0.18)",
  glassBgLit: "rgba(255,255,255,0.62)",
  glassSheen: "rgba(255,255,255,0.80)",
  textWarm: "#0B0E17",
  textWarmSecondary: "#2A3040",
  nightTint: "rgba(255,255,255,0)",
  surfaceDeep: "#EDF0F6",
  artworkSurface: "#05070C",
  // Occhiello "Introduzione" del lettore: pervinca, un colore tutto suo, distinto
  // dall'azzurro delle parole evidenziate, dai colori dei capitoli e dall'ambra di "Da ricordare".
  intro: "#5B6CFF",
};

// ---------------------------------------------------------------------------
// Accents — Premium palettes built from the tones already in the app
// (cyan / violet / orange / pink / green / blue). Light variants are darker so
// text stays legible on white; gradients keep white labels in both schemes.
// ---------------------------------------------------------------------------
// Atmosfera della lettura: stessa struttura per tutti i temi (fondo quasi
// nero, luci morbide ai bordi, centro calmo), cambia solo la tonalità —
// sempre scura, desaturata, mai sgargiante.
// base = fondo quasi nero · tint = luce atmosferica principale · secondary =
// seconda luce · glow = filo d'accento · frame = luce della cornice perimetrale
// (una tonalità del tema che conserva sempre una componente blu/ciano PAUSE).
type Atmosphere = { base: string; tint: string; secondary: string; glow: string; frame: string };
type AccentSet = { brand: string; brandSecondary: string; gradient: [string, string]; atmosphere: Atmosphere };
export type Accent = { id: AccentId; dark: AccentSet; light: AccentSet };

export const ACCENTS: Accent[] = [
  {
    id: "aurora",
    dark: { brand: "#3FD9FF", brandSecondary: "#9B4DFF", gradient: ["#9B4DFF", "#3FE0FF"], atmosphere: { base: "#060A16", tint: "#143B68", secondary: "#0E4658", glow: "#3FE0FF", frame: "#5FDCFF" } },
    light: { brand: "#0B7FA6", brandSecondary: "#6D28D9", gradient: ["#6D28D9", "#0891B2"], atmosphere: { base: "#F4F6FB", tint: "#D9E6F6", secondary: "#D6EEF4", glow: "#0B7FA6", frame: "#0B7FA6" } },
  },
  {
    id: "tramonto",
    dark: { brand: "#FF9A3C", brandSecondary: "#FF3D8A", gradient: ["#FF006A", "#FF9100"], atmosphere: { base: "#0B0806", tint: "#4A2812", secondary: "#4F331C", glow: "#FF9A3C", frame: "#E8B384" } },
    light: { brand: "#C2410C", brandSecondary: "#BE185D", gradient: ["#BE185D", "#EA580C"], atmosphere: { base: "#FBF6F1", tint: "#F6E3D0", secondary: "#F3E6D8", glow: "#C2410C", frame: "#C2410C" } },
  },
  {
    id: "foresta",
    dark: { brand: "#00E676", brandSecondary: "#3FD9FF", gradient: ["#00A86B", "#3FE0FF"], atmosphere: { base: "#050B0A", tint: "#0F3F3A", secondary: "#114A30", glow: "#2FD9A8", frame: "#6FE6CF" } },
    light: { brand: "#047857", brandSecondary: "#0B7FA6", gradient: ["#047857", "#0891B2"], atmosphere: { base: "#F2F8F6", tint: "#D6ECE6", secondary: "#D9F0E4", glow: "#047857", frame: "#047857" } },
  },
  {
    id: "oceano",
    dark: { brand: "#5B9CFF", brandSecondary: "#00D2FF", gradient: ["#2E5BFF", "#00D2FF"], atmosphere: { base: "#050814", tint: "#122A62", secondary: "#0F3B70", glow: "#5B9CFF", frame: "#7AB6FF" } },
    light: { brand: "#1D4ED8", brandSecondary: "#0B7FA6", gradient: ["#1D4ED8", "#0891B2"], atmosphere: { base: "#F3F5FB", tint: "#D8E2F7", secondary: "#D6E8F6", glow: "#1D4ED8", frame: "#1D4ED8" } },
  },
  {
    id: "orchidea",
    dark: { brand: "#D98BFF", brandSecondary: "#FF4D9D", gradient: ["#B200FF", "#FF4D9D"], atmosphere: { base: "#090612", tint: "#301A56", secondary: "#42183A", glow: "#D98BFF", frame: "#CFA6FF" } },
    light: { brand: "#7E22CE", brandSecondary: "#BE185D", gradient: ["#7E22CE", "#DB2777"], atmosphere: { base: "#F8F4FB", tint: "#E8DAF6", secondary: "#F3DCE8", glow: "#7E22CE", frame: "#7E22CE" } },
  },
];
export const DEFAULT_ACCENT: AccentId = "aurora";

export function buildColors(scheme: ColorScheme, accentId: AccentId) {
  const base = scheme === "dark" ? darkBase : lightBase;
  const accent = (ACCENTS.find((a) => a.id === accentId) ?? ACCENTS[0])[scheme];
  // Cyan luminoso: colore principale per azioni interattive / progress /
  // stato attivo / audio, indipendente dall'accento della categoria.
  const cyan = scheme === "dark" ? "#3FE0FF" : "#0891B2";
  const cyanSoft = scheme === "dark" ? "#7FE9FF" : "#22B8DE";
  return {
    ...base,
    brand: accent.brand,
    onBrand: scheme === "dark" ? "#05070C" : "#FFFFFF",
    brandPrimary: accent.brand,
    onBrandPrimary: scheme === "dark" ? "#05070C" : "#FFFFFF",
    brandSecondary: accent.brandSecondary,
    onBrandSecondary: "#FFFFFF",
    brandTertiary: scheme === "dark" ? base.surfaceTertiary : accent.brand + "14",
    onBrandTertiary: accent.brand,
    info: accent.brand,
    onInfo: scheme === "dark" ? "#05070C" : "#FFFFFF",
    gradient: accent.gradient,
    // Atmosfera della lettura (stessa struttura per ogni tema, tonalità del tema).
    atmosBase: accent.atmosphere.base,
    atmosTint: accent.atmosphere.tint,
    atmosSecondary: accent.atmosphere.secondary,
    atmosGlow: accent.atmosphere.glow,
    atmosFrame: accent.atmosphere.frame,
    // Label colour on top of the brand gradient (buttons, chips).
    onGradient: "#FFFFFF",
    // Cyan luminoso "PAUSE glass" — colore principale per interattività,
    // progress, audio, glow. Rimane costante fra accenti.
    cyan,
    cyanSoft,
    cyanGlow: scheme === "dark" ? "rgba(63,224,255,0.32)" : "rgba(8,145,178,0.20)",
    cyanGlowSoft: scheme === "dark" ? "rgba(63,224,255,0.14)" : "rgba(8,145,178,0.10)",
  };
}

export type ThemeColors = ReturnType<typeof buildColors>;

// "#05070C" + 0.6 → "rgba(5,7,12,0.6)". Per gradienti che devono sfumare nel
// colore di superficie del tema corrente (chiaro o scuro).
export function withAlpha(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`;
}

// Extra tokens (not part of surface/on pattern)
export const chapterGlowColors = ["#00E5FF", "#B200FF", "#FF6D00", "#FF006A", "#00E676"];
export const summaryGradient: [string, string] = ["#003BFF", "#FF6D00"];

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 };
export const radius = { sm: 6, md: 12, lg: 20, pill: 999 };

export const typography = {
  display: "Sora_600SemiBold",
  displayBold: "Sora_700Bold",
  body: "Manrope_400Regular",
  bodyMedium: "Manrope_500Medium",
  bodyBold: "Manrope_600SemiBold",
};

// User reference: cinematic category tiles stay dark in both app themes.
// These accents belong to the artwork, not the user's premium accent palette.
export const categoryTilePalette = {
  surface: "#040A14", top: "#0C1C30", text: "#E8F1F8", muted: "#A7B7CB",
  highlight: "#C7E3FF", lightOff: "#253348",
  accents: {
    // Una tinta distinta per categoria, coerente con l'oggetto 3D dell'icona
    // (foglia verde, chip blu, cervello rosso-corallo, tavolozza orchidea…).
    // ESPLORA: bianco ghiaccio — tutti i colori insieme formano il bianco.
    all: "#EAF7FF", scienza: "#00DFFF", spazio: "#A85AFF", tecnologia: "#4F8CFF",
    natura: "#00E878", animali: "#FF9A3C", storia: "#E4B76A", psicologia: "#FF5CB8",
    "corpo-umano": "#FF4D6D", cultura: "#00DAB4", economia: "#FFE14D",
    arte: "#E76BEF", geografia: "#B8F03C",
  } as Record<string, string>,
};

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
type ThemeCtx = {
  scheme: ColorScheme;
  colors: ThemeColors;
  mode: ThemeMode;
  setMode: (m: ThemeMode) => void;
  accent: AccentId;
  setAccent: (a: AccentId) => void;
  ready: boolean;
};

const defaultColors = buildColors("dark", DEFAULT_ACCENT);
// Back-compat static exports for screens/components still using the pre-hook
// API (e.g. `import { colors } from "@/src/theme"`). These reflect the default
// dark + aurora accent; components that must react to theme changes should
// migrate to `useTheme()`.
export const colors = defaultColors;
export const brandGradient: [string, string] = defaultColors.gradient;

const ThemeContext = createContext<ThemeCtx>({
  scheme: "dark", colors: defaultColors, mode: "dark", setMode: () => {},
  accent: DEFAULT_ACCENT, setAccent: () => {}, ready: false,
});

const isMode = (v: unknown): v is ThemeMode => v === "light" || v === "dark" || v === "system";
const isAccent = (v: unknown): v is AccentId => ACCENTS.some((a) => a.id === v);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const system = useColorScheme();
  const [mode, setModeState] = useState<ThemeMode>("dark");
  const [accent, setAccentState] = useState<AccentId>(DEFAULT_ACCENT);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([storage.getItem(MODE_KEY, "dark"), storage.getItem(ACCENT_KEY, DEFAULT_ACCENT)])
      .then(([m, a]) => {
        if (cancelled) return;
        if (isMode(m)) setModeState(m);
        if (isAccent(a)) setAccentState(a);
      })
      .finally(() => { if (!cancelled) setReady(true); });
    return () => { cancelled = true; };
  }, []);

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    storage.setItem(MODE_KEY, m);
  }, []);
  const setAccent = useCallback((a: AccentId) => {
    setAccentState(a);
    storage.setItem(ACCENT_KEY, a);
  }, []);

  const scheme: ColorScheme = mode === "system" ? (system === "light" ? "light" : "dark") : mode;
  const colors = useMemo(() => buildColors(scheme, accent), [scheme, accent]);
  const value = useMemo(
    () => ({ scheme, colors, mode, setMode, accent, setAccent, ready }),
    [scheme, colors, mode, setMode, accent, setAccent, ready],
  );
  return React.createElement(ThemeContext.Provider, { value }, children);
}

export function useTheme(): ThemeCtx {
  return useContext(ThemeContext);
}

export function makeStyles<T extends StyleSheet.NamedStyles<T> | StyleSheet.NamedStyles<any>>(
  factory: (colors: ThemeColors) => T & StyleSheet.NamedStyles<any>,
): () => T {
  return function useStyles(): T {
    const { colors } = useTheme();
    return useMemo(() => StyleSheet.create(factory(colors)), [colors]);
  };
}
