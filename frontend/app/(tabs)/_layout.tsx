import { Tabs } from "expo-router";
import { Platform } from "react-native";
import { useTheme } from "@/src/theme";
import { useLimitGate } from "@/src/hooks/use-limit-gate";
import { useI18n } from "@/src/i18n";
import { GlassTabBar } from "@/src/components/glass-tab-bar";

export default function TabsLayout() {
  // Global limit gate — polls backend and redirects to /pause-limit if blocked.
  useLimitGate();
  const { t } = useI18n();
  const { colors } = useTheme();
  return (
    <Tabs
      tabBar={(props) => <GlassTabBar {...(props as any)} />}
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: colors.surface },
        // Web's shift driver can retain a translated scene after rapid tab changes.
        // Keep the native transition; web switches tabs without a stale transform.
        animation: Platform.OS === "web" ? "none" : "shift",
      }}
    >
      <Tabs.Screen name="discover" options={{ title: t.tab_home, tabBarButtonTestID: "tab-home" }} />
      <Tabs.Screen name="explore" options={{ title: t.tab_explore, tabBarButtonTestID: "tab-explore" }} />
      <Tabs.Screen name="bookmarks" options={{ title: t.tab_saved, tabBarButtonTestID: "tab-saved" }} />
      <Tabs.Screen name="profile" options={{ title: t.tab_profile, tabBarButtonTestID: "tab-profile" }} />
    </Tabs>
  );
}
