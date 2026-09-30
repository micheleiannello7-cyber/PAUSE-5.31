// PAUSE — bottom bar in vetro scuro: attaccata al bordo inferiore con i soli
// angoli superiori arrotondati, quattro voci con icone lineari della stessa
// famiglia. La voce attiva prende il colore del tema (palette accento scelta
// nel Profilo) con un alone morbido e un sottile indicatore sotto; il resto
// resta neutro e scuro. Stesse destinazioni e testID del tab bar precedente.
import { Pressable, StyleSheet, Text, View } from "react-native";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Ionicons from "@react-native-vector-icons/ionicons";
import * as Haptics from "@/src/haptics";
import { makeStyles, typography, useTheme, withAlpha } from "@/src/theme";

// Icone lineari: casa · card (Argomenti, non la bussola) · segnalibro · profilo.
const TAB_ICONS: Record<string, string> = { discover: "home", explore: "albums", bookmarks: "bookmark", profile: "person" };

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
          const icon = TAB_ICONS[route.name] ?? "ellipse";
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
              testID={options.tabBarButtonTestID}
              accessibilityRole="tab"
              accessibilityState={{ selected: focused }}
              accessibilityLabel={options.tabBarAccessibilityLabel ?? label}
              style={({ pressed }) => [styles.item, pressed && styles.pressed]}
            >
              <View style={styles.iconWrap}>
                {focused ? <View style={[styles.halo, { backgroundColor: withAlpha(colors.brand, 0.14), boxShadow: `0px 0px 18px ${withAlpha(colors.brand, 0.42)}` as any }]} /> : null}
                <Ionicons name={(focused ? icon : `${icon}-outline`) as any} size={24} color={tint} />
              </View>
              <Text style={[styles.label, { color: tint }, focused && styles.labelOn]} numberOfLines={1}>{label}</Text>
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
    backgroundColor: "transparent", paddingTop: 8,
  },
  sheen: { position: "absolute", top: 0, left: 0, right: 0, height: 34 },
  topLine: { position: "absolute", top: 0, left: 36, right: 36, height: 1 },
  row: { flexDirection: "row", alignItems: "flex-start" },
  item: { flex: 1, minHeight: 56, alignItems: "center", justifyContent: "flex-start", paddingTop: 2 },
  pressed: { opacity: 0.7 },
  iconWrap: { width: 34, height: 30, alignItems: "center", justifyContent: "center" },
  halo: { position: "absolute", width: 30, height: 30, borderRadius: 15 },
  label: { fontFamily: typography.bodyMedium, fontSize: 11, marginTop: 3 },
  labelOn: { fontFamily: typography.bodyBold },
  indicator: { width: 16, height: 3, borderRadius: 2, marginTop: 4, backgroundColor: "transparent" },
}));
