// PAUSE — root container for stack screens. On native the navigator already
// animates the push/pop; on web (where the native stack has no transitions)
// the content eases in with a soft fade + slide so route changes never "flash".
import { ReactNode } from "react";
import { Platform, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import Animated, { FadeInRight, Easing } from "react-native-reanimated";

type Props = { children: ReactNode; style?: StyleProp<ViewStyle>; testID?: string; /** false: nessun ingresso animato sul web (es. arrivo con la transizione dalla card). */ animated?: boolean };

const enter = FadeInRight.duration(360)
  .easing(Easing.out(Easing.cubic))
  .withInitialValues({ opacity: 0, transform: [{ translateX: 16 }] });

export function Screen({ children, style, testID, animated = true }: Props) {
  if (Platform.OS !== "web" || !animated) {
    return <View style={style} testID={testID}>{children}</View>;
  }
  return (
    <View style={[style, styles.viewport]}>
      <Animated.View entering={enter} style={styles.fill} testID={testID}>
        {children}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  viewport: { flex: 1, overflow: "hidden" },
  fill: { flex: 1 },
});
