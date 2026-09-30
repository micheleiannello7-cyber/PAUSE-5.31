import { Text } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import { makeStyles, useTheme, typography, radius } from "@/src/theme";
import { useI18n } from "@/src/i18n";

// Small gradient pill: "SPAZIO · SCOPERTA"
export function CategoryChip({ name, icon }: { name: string; icon: string }) {
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const label = name.includes("·") ? name : `${name} · ${t.discovery}`;
  return (
    <LinearGradient
      colors={colors.gradient}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 0 }}
      style={styles.chip}
    >
      <Ionicons name={icon as any} size={11} color={colors.onGradient} />
      <Text style={styles.text} numberOfLines={1} ellipsizeMode="tail">{label.toUpperCase()}</Text>
    </LinearGradient>
  );
}

const useStyles = makeStyles((colors) => ({
  chip: {
    alignSelf: "flex-start",
    maxWidth: "100%",
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: radius.pill,
  },
  text: { color: colors.onGradient, fontFamily: typography.bodyBold, fontSize: 9.5, letterSpacing: 1.4, flexShrink: 1 },
}));
