import { ActivityIndicator, Pressable, StyleProp, StyleSheet, Text, ViewStyle } from "react-native";
import { BlurView } from "expo-blur";
import Ionicons from "@react-native-vector-icons/ionicons";
import { makeStyles, radius, typography, useTheme, withAlpha } from "@/src/theme";

type Props = {
  label?: string; icon: string; onPress: () => void; testID: string;
  accessibilityLabel?: string; style?: StyleProp<ViewStyle>; overImage?: boolean;
  loading?: boolean; disabled?: boolean; compact?: boolean;
};

export function FrostedButton({ label, icon, onPress, testID, accessibilityLabel, style,
  overImage = false, loading = false, disabled = false, compact = false }: Props) {
  const styles = useStyles();
  const { colors, scheme } = useTheme();
  const color = overImage ? colors.onGradient : colors.textWarm;
  return (
    <Pressable testID={testID} onPress={(event) => { event.stopPropagation(); onPress(); }} disabled={disabled}
      accessibilityRole="button" accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled, busy: loading }}
      style={({ pressed }) => [styles.button, compact && styles.compact, overImage && styles.overImage,
        pressed && styles.pressed, disabled && styles.disabled, style]}>
      <BlurView pointerEvents="none" tint={overImage || scheme === "dark" ? "dark" : "light"}
        intensity={24} style={StyleSheet.absoluteFill} />
      {loading ? <ActivityIndicator color={color} size="small" /> : <Ionicons name={icon as any} size={18} color={color} />}
      {label ? <Text testID={`${testID}-label`} style={[styles.label, { color }]} numberOfLines={2}>{label}</Text> : null}
    </Pressable>
  );
}

const useStyles = makeStyles((colors) => ({
  button: { minHeight: 54, minWidth: 44, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingHorizontal: 14, paddingVertical: 10, borderRadius: radius.pill, overflow: "hidden",
    backgroundColor: colors.glassBgLit, borderWidth: 1, borderColor: colors.glassBorderStrong },
  overImage: { backgroundColor: withAlpha(colors.artworkSurface, 0.46), borderColor: withAlpha(colors.onGradient, 0.28) },
  compact: { minHeight: 44, paddingHorizontal: 12 },
  label: { flexShrink: 1, fontFamily: typography.bodyBold, fontSize: 13.5, lineHeight: 18, textAlign: "center" },
  pressed: { opacity: 0.78, transform: [{ scale: 0.98 }] },
  disabled: { opacity: 0.45 },
}));