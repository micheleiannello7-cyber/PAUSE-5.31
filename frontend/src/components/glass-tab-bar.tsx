// PAUSE — bottom bar in vetro scuro: attaccata al bordo inferiore con i soli
// angoli superiori arrotondati, quattro oggetti 3D della stessa famiglia.
// Stato neutro → colorato con dissolvenza; Salvati riusa il segnalibro del
// lettore. Etichetta/indicatore seguono il tema. Destinazioni e testID invariati.
import { Pressable, StyleSheet, Text, View } from "react-native";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { TabIcon3D } from "./tab-icon-3d";
import { TAB_ART_3D } from "./icon-3d-assets";
import * as Haptics from "@/src/haptics";
import { makeStyles, typography, useTheme, withAlpha } from "@/src/theme";

type Route = { key: string; name: string; params?: object };
type Props = {
  state: { index: number; routes: Route[] };
  descriptors: Record<string, { options: { title?: string; tabBarButtonTestID?: string; tabBarAccessibilityLabel?: string } }>;
  navigation: {
    emit: (e: { type: string; target: string; canPreventDefault?: boolean }) => { defaultPrevented?: boolean };
    navigate: (name: string, params?: object) => void;
  };
};

export function GlassTabBar({ state, descriptors, navigation }: Props) {
  const { colors, scheme } = useTheme();
  const insets = useSafeAreaInsets();
  const styles = useStyles();
  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 10) }]} testID="glass-tab-bar">
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <BlurView intensity={38} tint={scheme === "dark" ? "dark" : "light"} experimentalBlurMethod="dimezisBlurView" style={StyleSheet.absoluteFill} />
        <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.overlay }]} />
        {/* Riflesso sottile nel colore del tema, solo verso il bordo alto. */}
        <LinearGradient colors={[withAlpha(colors.brand, 0.09), withAlpha(colors.brand, 0)]} locations={[0, 1]} style={styles.sheen} />
        <View style={[styles.topLine, { backgroundColor: withAlpha(colors.brand, 0.32) }]} />
      </View>
      <View style={styles.row}>
        {state.routes.map((route, index) => {
          const { options } = descriptors[route.key];
          const focused = state.index === index;
          const label = options.title ?? route.name;
          const icon = (route.name in TAB_ART_3D ? route.name : "discover") as keyof typeof TAB_ART_3D;
          const testID = options.tabBarButtonTestID ?? `tab-${route.name}`;
          const tint = focused ? colors.brand : colors.muted;
          const onPress = () => {
            const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });
            if (focused || event.defaultPrevented) return;
            Haptics.selectionAsync().catch(() => {});
            navigation.navigate(route.name, route.params);
          };
          return (
            <Pressable
              key={route.key}
              onPress={onPress}
              onLongPress={() => navigation.emit({ type: "tabLongPress", target: route.key })}
              testID={testID}
              accessibilityRole="tab"
              accessibilityState={{ selected: focused }}
              aria-selected={focused}
              accessibilityLabel={options.tabBarAccessibilityLabel ?? label}
              style={({ pressed }) => [styles.item, pressed && styles.pressed]}
            >
              <View style={styles.iconWrap}>
                {focused ? <View style={[styles.halo, { backgroundColor: withAlpha(colors.brand, 0.14), boxShadow: `0px 0px 18px ${withAlpha(colors.brand, 0.42)}` as any }]} /> : null}
                <TabIcon3D route={icon} focused={focused} testID={`${testID}-icon`} />
              </View>
              <Text testID={`${testID}-label`} style={[styles.label, { color: tint }, focused && styles.labelOn]} numberOfLines={1}>{label}</Text>
              <View style={[styles.indicator, focused && { backgroundColor: colors.brand, boxShadow: `0px 0px 8px ${withAlpha(colors.brand, 0.7)}` as any }]} />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  bar: {
    borderTopLeftRadius: 24, borderTopRightRadius: 24, overflow: "hidden",
    borderTopWidth: 1, borderTopColor: colors.glassBorder,
    backgroundColor: "transparent", paddingTop: 6,
  },
  sheen: { position: "absolute", top: 0, left: 0, right: 0, height: 34 },
  topLine: { position: "absolute", top: 0, left: 36, right: 36, height: 1 },
  row: { flexDirection: "row", alignItems: "flex-start" },
  item: { flex: 1, minHeight: 58, alignItems: "center", justifyContent: "flex-start", paddingTop: 2 },
  pressed: { opacity: 0.7 },
  iconWrap: { width: 38, height: 34, alignItems: "center", justifyContent: "center" },
  halo: { position: "absolute", width: 30, height: 30, borderRadius: 15 },
  label: { fontFamily: typography.bodyMedium, fontSize: 11, lineHeight: 14, marginTop: 1 },
  labelOn: { fontFamily: typography.bodyBold },
  indicator: { width: 16, height: 3, borderRadius: 2, marginTop: 3, backgroundColor: "transparent" },
}));
