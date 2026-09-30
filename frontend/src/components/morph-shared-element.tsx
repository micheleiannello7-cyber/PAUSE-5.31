import { ReactNode } from "react";
import { LayoutChangeEvent, StyleSheet } from "react-native";
import Animated, { Extrapolation, interpolate, SharedValue, useAnimatedStyle } from "react-native-reanimated";
import { IntroRect } from "./reader-intro";

// Both text layouts follow exactly the same top-left and width. Their
// complementary opacity keeps the title present through the whole journey.
export function MorphSharedElement({ from, to, progress, destination = false, children, onLayout, testID }: {
  from: IntroRect; to: IntroRect; progress: SharedValue<number>; destination?: boolean;
  children: ReactNode; onLayout?: (event: LayoutChangeEvent) => void; testID: string;
}) {
  const width = destination ? to.width : from.width;
  const motion = useAnimatedStyle(() => {
    const p = progress.value;
    const mix = interpolate(p, [0.25, 0.75], [0, 1], Extrapolation.CLAMP);
    return {
      opacity: destination ? mix : 1 - mix,
      transform: [
        { translateX: from.x + (to.x - from.x) * p },
        { translateY: from.y + (to.y - from.y) * p },
        { scale: (from.width + (to.width - from.width) * p) / Math.max(1, width) },
      ],
    };
  });
  return <Animated.View testID={testID} pointerEvents="none" onLayout={onLayout}
    renderToHardwareTextureAndroid shouldRasterizeIOS style={[styles.layer, { width }, motion]}>{children}</Animated.View>;
}

const styles = StyleSheet.create({ layer: { position: "absolute", top: 0, left: 0, transformOrigin: "left top" } });