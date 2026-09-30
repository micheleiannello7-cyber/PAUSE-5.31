import { Pressable, Text, ActivityIndicator, StyleProp, ViewStyle, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import * as Haptics from "@/src/haptics";
import Animated, { useSharedValue, useAnimatedStyle, withSpring, withTiming } from "react-native-reanimated";
import { makeStyles, useTheme, typography, radius } from "@/src/theme";

type Props = {
  label: string;
  onPress: () => void;
  icon?: string | null;
  disabled?: boolean;
  loading?: boolean;
  testID?: string;
  style?: StyleProp<ViewStyle>;
};

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

// Primary CTA: brand gradient, white label, optional trailing icon.
// Al tocco si comprime leggermente (scale) e dà un feedback aptico leggero.
export function GradientButton({
  label, onPress, icon = "arrow-forward", disabled, loading, testID, style,
}: Props) {
  const styles = useStyles();
  const { colors } = useTheme();
  const scale = useSharedValue(1);
  const anim = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  const onPressIn = () => {
    scale.value = withTiming(0.96, { duration: 90 });
  };
  const onPressOut = () => {
    scale.value = withSpring(1, { damping: 14, stiffness: 260 });
  };
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    onPress();
  };

  return (
    <AnimatedPressable
      onPress={handlePress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      disabled={disabled || loading}
      testID={testID}
      style={[styles.wrap, { opacity: disabled ? 0.4 : 1 }, style, anim]}
    >
      <LinearGradient
        colors={colors.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.inner}
      >
        {loading ? (
          <ActivityIndicator color={colors.onGradient} />
        ) : (
          <>
            <Text style={styles.label}>{label}</Text>
            {icon ? <Ionicons name={icon as any} size={18} color={colors.onGradient} /> : null}
          </>
        )}
      </LinearGradient>
      {/* Top glass highlight — vetro illuminato */}
      <View pointerEvents="none" style={styles.highlight} />
    </AnimatedPressable>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: {
    borderRadius: radius.lg, overflow: "hidden",
    boxShadow: `0px 6px 20px ${colors.brandSecondary}59, 0px 0px 12px ${colors.cyanGlow}`,
  },
  inner: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    minHeight: 54, paddingHorizontal: 20,
  },
  label: { color: colors.onGradient, fontFamily: typography.bodyBold, fontSize: 15 },
  highlight: {
    position: "absolute", top: 0, left: 16, right: 16, height: 1.2,
    backgroundColor: colors.glassHighlight, opacity: 0.7, borderRadius: 1,
  },
}));
