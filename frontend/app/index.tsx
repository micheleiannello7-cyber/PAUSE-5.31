import { useEffect } from "react";
import { View, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { makeStyles, useTheme } from "@/src/theme";
import { getOrCreateUserId, isOnboarded } from "@/src/session";

// Fase test/programmazione: mostra SEMPRE l'onboarding (presentazione →
// categorie → home) a ogni apertura. Metti a false per ripristinare lo skip.
const ALWAYS_SHOW_ONBOARDING = true;

export default function Index() {
  const router = useRouter();
  const styles = useStyles();
  const { colors } = useTheme();

  useEffect(() => {
    (async () => {
      await getOrCreateUserId();
      const onboarded = await isOnboarded();
      const goHome = !ALWAYS_SHOW_ONBOARDING && onboarded;
      router.replace(goHome ? "/(tabs)/discover" : "/onboarding");
    })();
  }, [router]);

  return (
    <View style={styles.container} testID="root-loader">
      <ActivityIndicator color={colors.brand} />
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
}));
