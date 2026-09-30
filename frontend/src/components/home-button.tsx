// PAUSE — shared "back to Home" button (design system Glassmorphism).
import { useRouter } from "expo-router";
import Ionicons from "@react-native-vector-icons/ionicons";
import { useTheme } from "@/src/theme";
import { GlassIconButton } from "@/src/components/glass";

export function HomeButton({ testID = "home-button" }: { testID?: string }) {
  const router = useRouter();
  const { colors } = useTheme();
  return (
    <GlassIconButton
      testID={testID}
      onPress={() => router.replace("/(tabs)/discover")}
      accessibilityLabel="go-home"
      size={38}
    >
      <Ionicons name="home" size={17} color={colors.onSurface} />
    </GlassIconButton>
  );
}
