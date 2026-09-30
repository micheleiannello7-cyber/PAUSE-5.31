import { useEffect, useId, useRef } from "react";
import { Animated, Platform, StyleSheet, View } from "react-native";
import Svg, { Defs, LinearGradient, RadialGradient, Rect, Stop, Ellipse } from "react-native-svg";
import { categoryTilePalette as palette, withAlpha } from "@/src/theme";

/** Native SVG edge reflection. When `active`, the border/glow intensifies so
 *  the whole tile is clearly illuminated in its colour (selected state). */
export function CategoryTileEdge({ color, rounded = 17, active = false }: { color: string; rounded?: number; active?: boolean }) {
  const id = useId().replace(/:/g, "");
  const opacity = useRef(new Animated.Value(active ? 1 : 0)).current;
  useEffect(() => {
    const animation = Animated.timing(opacity, { toValue: active ? 1 : 0, duration: 220, useNativeDriver: Platform.OS !== "web" });
    animation.start();
    return () => animation.stop();
  }, [active, opacity]);
  return (
    <>
      {/* Base rim (always visible) */}
      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        <Svg width="100%" height="100%">
          <Defs>
            <LinearGradient id={id} x1="0%" y1="0%" x2="80%" y2="100%">
              <Stop offset="0" stopColor={palette.highlight} stopOpacity={0.75} />
              <Stop offset="0.22" stopColor={color} stopOpacity={0.46} />
              <Stop offset="0.52" stopColor={palette.highlight} stopOpacity={0.09} />
              <Stop offset="1" stopColor={color} stopOpacity={0.2} />
            </LinearGradient>
          </Defs>
          <Rect x="0.75" y="0.75" width="99%" height="99%" rx={rounded} fill="none" stroke={`url(#${id})`} strokeWidth="1.2" />
        </Svg>
      </View>
      {/* Selected-state glow: brighter tinted border + outer halo. */}
      <Animated.View
        pointerEvents="none"
        style={[StyleSheet.absoluteFill, {
          opacity,
          borderRadius: rounded,
          borderWidth: 1.75,
          borderColor: withAlpha(color, 1),
          boxShadow: `0px 0px 28px ${withAlpha(color, 0.78)}, 0px 0px 60px ${withAlpha(color, 0.42)}, inset 0px 0px 26px ${withAlpha(color, 0.4)}` as any,
        }]}
      />
    </>
  );
}

/** Only this layer emits selection light; artwork's intrinsic rim light is static. */
export function CategorySelectionLight({ id, color, active }: { id: string; color: string; active: boolean }) {
  const opacity = useRef(new Animated.Value(active ? 1 : 0)).current;
  const gradientId = useId().replace(/:/g, "");
  useEffect(() => {
    const animation = Animated.timing(opacity, { toValue: active ? 1 : 0, duration: 180, useNativeDriver: Platform.OS !== "web" });
    animation.start();
    return () => animation.stop();
  }, [active, opacity]);
  return (
    <View testID={`category-light-${id}`} accessibilityLabel={active ? "on" : "off"} pointerEvents="none" style={styles.light}>
      <View style={[styles.bar, { backgroundColor: palette.lightOff }]} />
      <Animated.View style={[styles.glow, { opacity }]} testID={`category-glow-${id}`}>
        <Svg width="100%" height="100%" viewBox="0 0 100 28">
          <Defs><RadialGradient id={gradientId} cx="50%" cy="50%" rx="50%" ry="50%">
            <Stop offset="0" stopColor={color} stopOpacity={0.62} />
            <Stop offset="0.45" stopColor={color} stopOpacity={0.22} />
            <Stop offset="1" stopColor={color} stopOpacity={0} />
          </RadialGradient></Defs>
          <Ellipse cx="50" cy="14" rx="48" ry="13" fill={`url(#${gradientId})`} />
        </Svg>
      </Animated.View>
      <Animated.View style={[styles.bar, { opacity, backgroundColor: color,
        boxShadow: `0px 0px 8px ${withAlpha(color, 0.95)}, 0px 0px 18px ${withAlpha(color, 0.55)}` }]} testID={`category-selected-${id}`} />
    </View>
  );
}

const styles = StyleSheet.create({
  light: { height: 13, width: "100%", alignItems: "center", justifyContent: "center" },
  bar: { position: "absolute", width: 27, height: 3, borderRadius: 3 },
  glow: { position: "absolute", width: 90, height: 28 },
});