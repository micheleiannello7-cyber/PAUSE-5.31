import { useEffect } from "react";
import { StyleSheet } from "react-native";
import { Image } from "expo-image";
import Animated, { Easing, useAnimatedStyle, useReducedMotion, useSharedValue, withTiming } from "react-native-reanimated";
import { TAB_ART_3D } from "./icon-3d-assets";

export function TabIcon3D({ route, focused, testID }: {
  route: keyof typeof TAB_ART_3D; focused: boolean; testID: string;
}) {
  const art = TAB_ART_3D[route];
  const reducedMotion = useReducedMotion();
  const selected = useSharedValue(focused ? 1 : 0);
  useEffect(() => {
    selected.value = withTiming(focused ? 1 : 0, {
      duration: reducedMotion ? 0 : 220, easing: Easing.out(Easing.quad),
    });
  }, [focused, reducedMotion, selected]);
  const motion = useAnimatedStyle(() => ({ transform: [{ scale: 1 + selected.value * 0.06 }] }));
  const base = useAnimatedStyle(() => ({ opacity: 1 - selected.value }));
  const active = useAnimatedStyle(() => ({ opacity: selected.value }));
  return (
    <Animated.View pointerEvents="none" testID={testID} style={[styles.icon, motion]}>
      <Animated.View testID={`${testID}-base`} style={[StyleSheet.absoluteFill, base]}>
        <Image source={art.base} contentFit="contain" transition={0} style={StyleSheet.absoluteFill} />
      </Animated.View>
      <Animated.View testID={`${testID}-active`} style={[StyleSheet.absoluteFill, active]}>
        <Image source={art.active} contentFit="contain" transition={0} style={StyleSheet.absoluteFill} />
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({ icon: { width: 34, height: 34 } });