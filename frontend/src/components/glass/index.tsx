// PAUSE — Glassmorphism design system primitives.
//
// Ispirato al pulsante "Ascolta" del deep-dive: superfici traslucide, bordo
// sottile luminoso, highlight superiore, glow morbido, backdrop blur.
// Ogni primitiva accetta children/props limitate e non gestisce logica di app:
// serve solo a mantenere un LINGUAGGIO VISIVO coerente su tutta PAUSE.
//
//   • GlassSurface   — contenitore vetro (card, panel, sheet, header)
//   • GlassPill      — pill compatta (badge categoria, meta info)
//   • GlassIconButton — pulsante rotondo (back, bookmark, more, arrow)
//   • GlowButton     — CTA cyan glow (Ascolta e derivati)
//
// Nota web: BlurView di expo-blur usa CSS backdrop-filter su web (supportato
// nei browser moderni, degrada in un semplice bg semi-trasparente).

import React from "react";
import { View, Pressable, StyleProp, ViewStyle, StyleSheet } from "react-native";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withRepeat,
  Easing,
} from "react-native-reanimated";

import { useTheme, radius, spacing } from "@/src/theme";

// --- Palette helper -------------------------------------------------------

export function useGlassPalette() {
  const { colors, scheme } = useTheme();
  const isDark = scheme === "dark";
  const tint: "light" | "dark" | "systemChromeMaterial" = isDark ? "dark" : "light";
  return { colors, scheme, isDark, tint } as const;
}

// --- Sheen: riflesso frosted dall'alto, comune a tutte le superfici -------
// È quello che trasforma un "rettangolo scuro con bordo" in vetro illuminato:
// una luce morbida che entra dal bordo superiore e svanisce verso il centro.

function Sheen({ radius: r, strength = 1 }: { radius: number; strength?: number }) {
  const { colors } = useGlassPalette();
  return (
    <LinearGradient
      pointerEvents="none"
      colors={[colors.glassSheen, "transparent"]}
      locations={[0, 0.62]}
      style={[StyleSheet.absoluteFill, { borderRadius: r, opacity: strength }]}
    />
  );
}

// --- AmbientGlow: sorgente di luce diffusa dietro un blocco di UI ---------
// Usata per dare profondità (titolo che "emerge" dalla foto, header, card).

export function AmbientGlow({
  color,
  alpha = 0.16,
  size = 220,
  style,
}: { color: string; alpha?: number; size?: number; style?: StyleProp<ViewStyle> }) {
  return (
    <View
      pointerEvents="none"
      style={[
        {
          position: "absolute",
          width: size,
          height: size * 0.45,
          borderRadius: size,
          backgroundColor: withAlphaHex(color, alpha * 0.5),
          boxShadow: `0px 0px ${Math.round(size * 0.45)}px ${Math.round(size * 0.2)}px ${withAlphaHex(color, alpha)}` as any,
        },
        style,
      ]}
    />
  );
}

// --- GlassSurface ---------------------------------------------------------

export type GlassIntensity = "soft" | "regular" | "strong";

type SurfaceProps = {
  intensity?: GlassIntensity;
  radiusOverride?: number;
  glow?: boolean;         // aggiunge un soft outer glow cyan (default: false)
  glowColor?: string;     // override per accent-color glow (categorie)
  borderColor?: string;   // override del bordo (stato attivo / categoria)
  highlight?: boolean;    // linea luminosa sul bordo alto (default: true)
  style?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
  children?: React.ReactNode;
  testID?: string;
};

export function GlassSurface({
  intensity = "regular",
  radiusOverride,
  glow = false,
  glowColor,
  borderColor,
  highlight = true,
  style,
  contentStyle,
  children,
  testID,
}: SurfaceProps) {
  const { colors, tint, isDark } = useGlassPalette();
  const blurAmount = intensity === "soft" ? 18 : intensity === "strong" ? 60 : 34;
  const bg =
    intensity === "soft" ? colors.glassBg :
    intensity === "strong" ? colors.glassBgStrong :
    colors.glassBgLit;
  const r = radiusOverride ?? radius.lg;
  const shadow = glow
    ? { boxShadow: `0px 10px 32px ${glowColor ?? colors.cyanGlow}, 0px 2px 10px ${colors.glassShadow}` as any }
    : { boxShadow: `0px 12px 28px ${colors.glassShadow}` as any };
  return (
    <View
      testID={testID}
      style={[{ borderRadius: r, overflow: "hidden" }, shadow, style]}
    >
      <BlurView
        intensity={blurAmount}
        tint={tint}
        experimentalBlurMethod="dimezisBlurView"
        style={[StyleSheet.absoluteFill, { borderRadius: r }]}
      />
      <View
        pointerEvents="none"
        style={[StyleSheet.absoluteFill, { borderRadius: r, backgroundColor: bg }]}
      />
      <Sheen radius={r} strength={intensity === "soft" ? 0.7 : 1} />
      <View
        pointerEvents="none"
        style={[
          StyleSheet.absoluteFill,
          {
            borderRadius: r,
            borderWidth: 1,
            borderColor: borderColor ?? (glow ? colors.glassBorderStrong : colors.glassBorder),
          },
        ]}
      />
      {highlight ? (
        <View
          pointerEvents="none"
          style={{
            position: "absolute",
            top: 0,
            left: 10,
            right: 10,
            height: 1,
            backgroundColor: colors.glassHighlight,
            opacity: isDark ? 0.7 : 0.9,
            borderRadius: 1,
          }}
        />
      ) : null}
      <View style={contentStyle}>{children}</View>
    </View>
  );
}

// --- GlassPill ------------------------------------------------------------

type PillProps = {
  style?: StyleProp<ViewStyle>;
  children?: React.ReactNode;
  testID?: string;
  height?: number;
  tone?: "neutral" | "cyan" | "accent";
  accentColor?: string; // per categorie / warning
};

export function GlassPill({
  style,
  children,
  testID,
  height = 34,
  tone = "neutral",
  accentColor,
}: PillProps) {
  const { colors, tint, isDark } = useGlassPalette();
  const glowTint =
    tone === "cyan" ? colors.cyanGlowSoft :
    tone === "accent" ? (accentColor ? withAlphaHex(accentColor, 0.22) : colors.cyanGlowSoft) :
    colors.glassShadow;
  const borderColor =
    tone === "cyan" ? withAlphaHex(colors.cyan, 0.45) :
    tone === "accent" ? (accentColor ? withAlphaHex(accentColor, 0.40) : colors.glassBorder) :
    colors.glassBorder;
  const bg =
    tone === "cyan" ? withAlphaHex(colors.cyan, 0.10) :
    tone === "accent" && accentColor ? withAlphaHex(accentColor, 0.10) :
    colors.glassBgLit;

  return (
    <View
      testID={testID}
      style={[
        {
          flexDirection: "row",
          alignItems: "center",
          height,
          borderRadius: height / 2,
          overflow: "hidden",
          boxShadow: `0px 6px 16px ${glowTint}` as any,
        },
        style,
      ]}
    >
      <BlurView
        intensity={30}
        tint={tint}
        experimentalBlurMethod="dimezisBlurView"
        style={[StyleSheet.absoluteFill, { borderRadius: height / 2 }]}
      />
      <View
        pointerEvents="none"
        style={[StyleSheet.absoluteFill, { borderRadius: height / 2, backgroundColor: bg }]}
      />
      <Sheen radius={height / 2} />
      <View
        pointerEvents="none"
        style={[StyleSheet.absoluteFill, { borderRadius: height / 2, borderWidth: 1, borderColor }]}
      />
      <View
        pointerEvents="none"
        style={{
          position: "absolute",
          top: 0,
          left: 10,
          right: 10,
          height: 1,
          backgroundColor: colors.glassHighlight,
          opacity: isDark ? 0.6 : 0.8,
          borderRadius: 1,
        }}
      />
      {children}
    </View>
  );
}

// --- GlassIconButton (back, bookmark, more, arrow) ------------------------

type IconBtnProps = {
  onPress?: () => void;
  disabled?: boolean;
  size?: number;
  style?: StyleProp<ViewStyle>;
  children?: React.ReactNode;
  testID?: string;
  accessibilityLabel?: string;
  hitSlop?: number;
  active?: boolean; // rende il bordo cyan
};

export function GlassIconButton({
  onPress,
  disabled,
  size = 40,
  style,
  children,
  testID,
  accessibilityLabel,
  hitSlop = 8,
  active,
}: IconBtnProps) {
  const { colors, tint, isDark } = useGlassPalette();
  const scale = useSharedValue(1);
  const anim = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  const onIn = () => { scale.value = withTiming(0.94, { duration: 80 }); };
  const onOut = () => { scale.value = withSpring(1, { damping: 14, stiffness: 260 }); };

  return (
    <AnimatedPressable
      onPress={onPress}
      onPressIn={onIn}
      onPressOut={onOut}
      disabled={disabled}
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      hitSlop={hitSlop}
      style={[
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          overflow: "hidden",
          opacity: disabled ? 0.35 : 1,
          boxShadow: active
            ? (`0px 0px 16px ${colors.cyanGlowSoft}, 0px 6px 16px ${colors.glassShadow}` as any)
            : (`0px 6px 18px ${colors.glassShadow}` as any),
        },
        anim,
        style,
      ]}
    >
      <BlurView
        intensity={36}
        tint={tint}
        experimentalBlurMethod="dimezisBlurView"
        style={[StyleSheet.absoluteFill, { borderRadius: size / 2 }]}
      />
      <View
        pointerEvents="none"
        style={[
          StyleSheet.absoluteFill,
          {
            borderRadius: size / 2,
            backgroundColor: active ? withAlphaHex(colors.cyan, 0.10) : colors.glassBgLit,
          },
        ]}
      />
      <Sheen radius={size / 2} />
      <View
        pointerEvents="none"
        style={[
          StyleSheet.absoluteFill,
          {
            borderRadius: size / 2,
            borderWidth: 1,
            borderColor: active ? withAlphaHex(colors.cyan, 0.55) : colors.glassBorder,
          },
        ]}
      />
      <View
        pointerEvents="none"
        style={{
          position: "absolute",
          top: 0,
          left: size * 0.22,
          right: size * 0.22,
          height: 1,
          backgroundColor: colors.glassHighlight,
          opacity: isDark ? 0.7 : 0.85,
          borderRadius: 1,
        }}
      />
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        {children}
      </View>
    </AnimatedPressable>
  );
}

// --- GlowButton (Ascolta e derivati) --------------------------------------

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

type GlowBtnProps = {
  onPress?: () => void;
  disabled?: boolean;
  active?: boolean; // audio in riproduzione: attiva pulsazione delicata
  height?: number;
  style?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
  children?: React.ReactNode;
  testID?: string;
  accessibilityLabel?: string;
};

export function GlowButton({
  onPress,
  disabled,
  active,
  height = 46,
  style,
  contentStyle,
  children,
  testID,
  accessibilityLabel,
}: GlowBtnProps) {
  const { colors, tint, isDark } = useGlassPalette();
  const scale = useSharedValue(1);
  const glow = useSharedValue(0.65);

  React.useEffect(() => {
    // Respiro lento e delicato quando l'audio è attivo — luce che pulsa
    // dall'interno, mai neon. Da fermo resta un glow morbido costante.
    if (active) {
      glow.value = withRepeat(
        withTiming(1, { duration: 1600, easing: Easing.inOut(Easing.sin) }),
        -1,
        true,
      );
    } else {
      glow.value = withTiming(0.65, { duration: 500 });
    }
  }, [active, glow]);

  const glowStyle = useAnimatedStyle(() => ({ opacity: glow.value }));
  const pressStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  const onIn = () => { scale.value = withTiming(0.97, { duration: 90 }); };
  const onOut = () => { scale.value = withSpring(1, { damping: 14, stiffness: 260 }); };
  const r = height / 2;
  const cyanA = (a: number) => withAlphaHex(colors.cyan, a);

  return (
    <View style={[{ borderRadius: r }, style]}>
      {/* Outer glow — sotto il pulsante, così non viene tagliato dall'overflow. */}
      <Animated.View
        pointerEvents="none"
        style={[
          {
            position: "absolute",
            top: 2,
            left: 4,
            right: 4,
            bottom: -2,
            borderRadius: r,
            boxShadow: `0px 0px 28px 2px ${colors.cyanGlow}, 0px 10px 22px ${colors.glassShadow}` as any,
          },
          glowStyle,
        ]}
      />
      <AnimatedPressable
        onPress={onPress}
        onPressIn={onIn}
        onPressOut={onOut}
        disabled={disabled}
        testID={testID}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        style={[
          { height, borderRadius: r, overflow: "hidden", opacity: disabled ? 0.5 : 1 },
          pressStyle,
        ]}
      >
        <BlurView
          intensity={44}
          tint={tint}
          experimentalBlurMethod="dimezisBlurView"
          style={[StyleSheet.absoluteFill, { borderRadius: r }]}
        />
        {/* Vetro tinto cyan: più luminoso a sinistra (dove sta l'icona) e in alto. */}
        <LinearGradient
          pointerEvents="none"
          colors={[cyanA(isDark ? 0.26 : 0.16), cyanA(isDark ? 0.10 : 0.06), cyanA(isDark ? 0.16 : 0.10)]}
          locations={[0, 0.55, 1]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[StyleSheet.absoluteFill, { borderRadius: r }]}
        />
        <Sheen radius={r} />
        {/* Inner glow: la luce risale dal basso — "illuminato dall'interno". */}
        <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, glowStyle]}>
          <LinearGradient
            colors={["transparent", cyanA(isDark ? 0.20 : 0.12)]}
            locations={[0.45, 1]}
            style={[StyleSheet.absoluteFill, { borderRadius: r }]}
          />
        </Animated.View>
        <View
          pointerEvents="none"
          style={[
            StyleSheet.absoluteFill,
            { borderRadius: r, borderWidth: 1.2, borderColor: cyanA(isDark ? 0.58 : 0.45) },
          ]}
        />
        {/* Highlight sul bordo alto */}
        <View
          pointerEvents="none"
          style={{
            position: "absolute",
            top: 0,
            left: height * 0.45,
            right: height * 0.45,
            height: 1.2,
            backgroundColor: colors.glassHighlight,
            opacity: isDark ? 0.75 : 0.85,
            borderRadius: 1,
          }}
        />
        <View
          style={[
            {
              flex: 1,
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "center",
              gap: spacing.sm + 2,
              paddingHorizontal: spacing.lg,
            },
            contentStyle,
          ]}
        >
          {children}
        </View>
      </AnimatedPressable>
    </View>
  );
}

// --- GlowOrb: disco cyan luminoso che ospita l'icona play/pausa -----------
// Rende l'icona audio "ben evidente" dentro il pulsante Ascolta.

export function GlowOrb({ size = 28, children, style }: { size?: number; children?: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  const { colors } = useGlassPalette();
  return (
    <View
      pointerEvents="none"
      style={[
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          overflow: "hidden",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: `0px 0px 14px ${colors.cyanGlow}` as any,
        },
        style,
      ]}
    >
      <LinearGradient
        colors={[colors.cyanSoft, colors.cyan]}
        start={{ x: 0.2, y: 0 }}
        end={{ x: 0.8, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View
        pointerEvents="none"
        style={{
          position: "absolute", top: 1, left: size * 0.22, right: size * 0.22, height: 1,
          backgroundColor: colors.glassHighlight, opacity: 0.9, borderRadius: 1,
        }}
      />
      {children}
    </View>
  );
}

// --- helper: hex ("#RRGGBB") + alpha in [0,1] -> rgba ---------------------
function withAlphaHex(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`;
}
