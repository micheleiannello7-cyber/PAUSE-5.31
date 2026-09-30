import { Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Category } from "@/src/api";
import { makeStyles, radius, typography, useTheme, withAlpha, categoryTilePalette as palette } from "@/src/theme";
import { DirectionIcon } from "./category-icon";
import { CategoryArtwork, CategoryArtMark } from "./category-artwork";
import { CategorySelectionLight, CategoryTileEdge } from "./category-tile-effects";

export function HomeCategoryTile({ cat, active, onPress, size, iconUri }: {
  cat: Category; active: boolean; onPress: () => void; size: number;
  /** Stile dark-navy in vetro (come l'onboarding): gradiente, bordo chiaro, icona ritagliata con alone. */
  glass?: boolean;
  /** Sorgente alternativa dell'icona (anteprime). */
  iconUri?: string;
}) {
  const styles = useStyles();
  const color = palette.accents[cat.id] || cat.color;
  return (
    <Pressable
      testID={`home-cat-${cat.id}`} onPress={onPress}
      accessibilityRole="button" accessibilityLabel={cat.name}
      accessibilityState={{ selected: active }}
      style={({ pressed }) => [styles.tile, { width: size, height: Math.round(size * 1.32) },
        pressed && styles.pressed]}
    >
      {/* Stesso vetro e stessa luce di selezione delle tessere della schermata Argomenti. */}
      <LinearGradient colors={[palette.top, palette.surface]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <CategoryArtwork category={cat} testID={`home-category-art-${cat.id}`} compact reference cornerRadius={radius.md} uriOverride={iconUri} />
      <View style={styles.tileNameWrap}>
        <Text testID={`home-cat-label-${cat.id}`} style={styles.tileName} numberOfLines={2}>{cat.name}</Text>
      </View>
      <CategorySelectionLight id={`home-${cat.id}`} color={color} active={active} />
      <CategoryTileEdge color={color} rounded={radius.md} active={active} />
    </Pressable>
  );
}

// Home con ESPLORA attiva: al posto della fila di categorie, una sola tessera
// larga con l'oggetto 3D di ESPLORA interamente dentro il vetro.
// Il tocco porta agli Argomenti.
export function HomeExploreTile({ onPress, label, sub, width }: { onPress: () => void; label: string; sub: string; width: number }) {
  const styles = useStyles();
  const color = palette.accents.all;
  const art = Math.min(76, Math.floor(width * 0.25));
  return (
    <Pressable
      testID="home-explore-tile" onPress={onPress}
      accessibilityRole="button" accessibilityLabel={label}
      style={({ pressed }) => [styles.exploreWrap, { width }, pressed && styles.pressed]}
    >
      <View testID="home-explore-container" style={[styles.exploreTile, { width, paddingRight: art + 28, borderColor: withAlpha(color, 0.5), boxShadow: `0px 8px 28px ${withAlpha(color, 0.22)}` as any }]}>
        <LinearGradient colors={[palette.top, palette.surface]} style={StyleSheet.absoluteFill} pointerEvents="none" />
        <View style={styles.exploreText}>
          <Text testID="home-explore-label" style={[styles.exploreName, { color }]} numberOfLines={1}>{label}</Text>
          <Text testID="home-explore-sub" style={styles.exploreSub} numberOfLines={2}>{sub}</Text>
        </View>
        <View pointerEvents="none" style={[styles.exploreArt, { width: art, height: art, top: (92 - art) / 2, right: 12 }]}>
          <CategoryArtMark categoryId="all" color={color} size={art} plain testID="home-explore-art" />
        </View>
        <View style={styles.exploreLightWrap} pointerEvents="none">
          <CategorySelectionLight id="home-explore" color={color} active />
        </View>
        <CategoryTileEdge color={color} rounded={radius.lg} active />
      </View>
    </Pressable>
  );
}

export function HomeNavButton({ direction, disabled, onPress, label }: {
  direction: "prev" | "next"; disabled: boolean; onPress: () => void; label: string;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress} disabled={disabled} testID={`discover-${direction}`}
      accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }}
      style={({ pressed }) => [styles.arrow, disabled && styles.disabled, pressed && styles.pressed]}
    >
      <View pointerEvents="none" style={styles.highlight} />
      <DirectionIcon direction={direction} color={colors.onSurface} />
    </Pressable>
  );
}

const useStyles = makeStyles((colors) => ({
  tile: {
    paddingBottom: 2, paddingHorizontal: 2,
    borderRadius: radius.md, backgroundColor: palette.surface,
    alignItems: "center", justifyContent: "flex-end", overflow: "hidden",
    // Luce ambientale del tema attorno alla tessera: si somma al colore della categoria.
    boxShadow: `0px 4px 16px ${withAlpha(colors.brand, 0.14)}` as any,
  },
  highlight: { position: "absolute", top: 0, left: 12, right: 12, height: 1, backgroundColor: colors.glassHighlight },
  tileNameWrap: { height: 26, alignItems: "center", justifyContent: "center", alignSelf: "stretch" },
  tileName: { color: palette.text, fontFamily: typography.bodyMedium, fontSize: 10.5, lineHeight: 13, textAlign: "center" },
  arrow: {
    width: 48, height: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.glassBorderStrong,
  },
  pressed: { opacity: 0.75, transform: [{ scale: 0.96 }] },
  disabled: { opacity: 0.3 },
  exploreWrap: { alignSelf: "center", paddingTop: 16 },
  exploreTile: {
    height: 92, borderRadius: radius.lg, borderWidth: 1, backgroundColor: palette.surface, overflow: "hidden",
    justifyContent: "center", paddingLeft: 18,
  },
  exploreText: { gap: 3 },
  exploreName: { fontFamily: typography.bodyBold, fontSize: 15, letterSpacing: 2.2 },
  exploreSub: { color: palette.text, fontFamily: typography.bodyMedium, fontSize: 12, lineHeight: 16, opacity: 0.85 },
  exploreLightWrap: { position: "absolute", left: 0, right: 0, bottom: 0, alignItems: "center" },
  exploreArt: { position: "absolute" },
}));