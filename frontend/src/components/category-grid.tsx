import { useState } from "react";
import { View, Text, Pressable } from "react-native";
import Animated, { FadeInUp, Easing } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import { Category } from "@/src/api";
import { makeStyles, spacing, radius, typography, withAlpha, categoryTilePalette as palette } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { CategoryArtwork, CategoryArtMark } from "./category-artwork";
import { CategorySelectionLight, CategoryTileEdge } from "./category-tile-effects";

export const ALL_ID = "all";
// Modalità "adatta all'altezza": tessera larga più bassa e altezza minima delle tessere.
const FIT_ALL_H = 68;
const FIT_TILE_MIN = 66;
// Quanto l'oggetto 3D di ESPLORA sporge sopra il bordo della tessera larga.
const ALL_POKE = 14;

// Shared toggle logic: "all" is exclusive with specific categories.
export function toggleInterest(prev: Set<string>, id: string): Set<string> {
  const next = new Set(prev);
  if (id === ALL_ID) {
    return next.has(ALL_ID) ? new Set() : new Set([ALL_ID]);
  }
  next.delete(ALL_ID);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  return next;
}

// Same picker/persistence everywhere. Small phones use two columns to keep
// the reference artwork and existing full category names readable.
export function CategoryGrid({
  categories, selected, onToggle, modes, staggerIn = false, disabled = false, columns: fixedColumns, maxHeight,
}: { categories: Category[]; selected: Set<string>; onToggle: (id: string) => void; compact?: boolean; modes?: ("stories" | "lessons")[]; staggerIn?: boolean; disabled?: boolean; /** Stile "vetro" dark navy dell'onboarding (icone ritagliate, tessere con gradiente). */ glass?: boolean;
  /** Numero fisso di colonne (tessere dense, es. 4 nel tab Categorie per stare in una schermata). */ columns?: number;
  /** Altezza disponibile: la griglia intera (tessera "Qualsiasi" + righe) si adatta per starci senza scorrere. */ maxHeight?: number }) {
  const allActive = selected.has(ALL_ID);
  const { t } = useI18n();
  const styles = useStyles();
  // Ingresso progressivo (onboarding): ogni tessera sale e appare con un
  // piccolo ritardo a cascata; altrove la griglia compare subito.
  const enterAt = (order: number) =>
    staggerIn ? FadeInUp.delay(order * 55).duration(420).easing(Easing.out(Easing.cubic)) : undefined;
  // Larghezza tessere dal contenitore misurato: sempre 3 colonne centrate,
  // anche su schermi stretti (con le percentuali scendeva a 2 per riga).
  const [gridW, setGridW] = useState(0);
  const columns = fixedColumns ?? (gridW < 315 ? 2 : gridW >= 560 ? 4 : 3);
  const dense = fixedColumns != null;
  const tileW = gridW > 0 ? Math.floor((gridW - spacing.xs * 2 - spacing.sm * (columns - 1)) / columns) : undefined;
  // Adattamento in altezza (onboarding a schermo intero): la tessera "Qualsiasi"
  // si abbassa e le tessere prendono un'altezza esplicita calcolata sulle righe;
  // l'oggetto 3D si ridimensiona per restare sopra al nome.
  const fit = maxHeight != null && maxHeight > 0;
  const rows = Math.ceil(categories.length / columns);
  const naturalTileH = tileW ? Math.floor(tileW / (dense ? 0.76 : 0.72)) : 0;
  const fixedExtra = spacing.md + spacing.xs + spacing.sm * (rows - 1);
  // Prima si abbassa la tessera larga (fino a FIT_ALL_H), poi le tessere.
  const allH = fit && tileW ? Math.max(FIT_ALL_H, Math.min(90, maxHeight - rows * naturalTileH - fixedExtra)) : undefined;
  const allArt = (allH ?? 90) + ALL_POKE - 6;
  const tileH = fit && tileW && allH
    ? Math.max(FIT_TILE_MIN, Math.min(naturalTileH, Math.floor((maxHeight - allH - fixedExtra) / rows)))
    : undefined;
  const artSize = tileH && tileW ? Math.min(Math.floor(tileW * 0.82), tileH - (dense ? 32 : 38)) : undefined;
  const fitArt = artSize && tileW ? { width: artSize, height: artSize, left: Math.floor((tileW - artSize) / 2), aspectRatio: undefined } : null;

  // Count label reflects which content modes are active (curiosities / lessons
  // / both) so the numbers match what the user will actually receive.
  const showStories = !modes || modes.includes("stories");
  const showLessons = !!modes && modes.includes("lessons");
  const countFor = (c: Category): string => {
    if (showStories && showLessons) return `${c.story_count + c.lesson_count} ${t.items_n}`;
    if (showLessons && !showStories) return `${c.lesson_count} ${t.lessons_n}`;
    return `${c.story_count} ${t.stories_n}`;
  };

  return (
    <View testID="category-grid">
      <Animated.View entering={enterAt(0)}>
      <Pressable
        testID="chip-all"
        onPress={() => onToggle(ALL_ID)}
        disabled={disabled}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: allActive, disabled }}
        aria-checked={allActive}
        accessibilityLabel={t.any_topic}
        style={({ pressed }) => [
          styles.allCard,
          allH ? { minHeight: allH, paddingVertical: spacing.sm, paddingBottom: 14, marginBottom: spacing.md } : null,
          pressed && styles.pressed,
        ]}
      >
        <LinearGradient colors={[palette.top, palette.surface]} style={[styles.glassBg, styles.allBg]} pointerEvents="none" />
        {/* Oggetto 3D intero: resta dentro la tessera, solo il bordo alto sporge fuori. */}
        <View pointerEvents="none" style={[styles.allArt, { top: -ALL_POKE, width: allArt, height: allArt }]}>
          <CategoryArtMark categoryId="all" color={palette.accents.all} size={allArt} plain testID="category-art-all" />
        </View>
        <View style={styles.allText}>
          <Text testID="category-all-name" style={styles.allName} numberOfLines={2}>{t.any_topic}</Text>
          <Text testID="category-all-subtitle" style={styles.allSub} numberOfLines={2}>{t.any_topic_sub}</Text>
        </View>
        <View style={styles.allLight}><CategorySelectionLight id="all" color={palette.accents.all} active={allActive} /></View>
        <CategoryTileEdge color={palette.accents.all} rounded={radius.lg} active={allActive} />
      </Pressable>
      </Animated.View>

      <View style={styles.grid} onLayout={(e) => setGridW(Math.round(e.nativeEvent.layout.width))}>
        {tileW ? categories.map((c, i) => {
          const active = allActive || selected.has(c.id);
          const color = palette.accents[c.id] || c.color;
          return (
            <Animated.View key={c.id} entering={enterAt(i + 1)} style={{ width: tileW }}>
            <Pressable
              testID={`chip-${c.id}`}
              onPress={() => onToggle(c.id)}
              disabled={disabled}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: active, disabled }}
              aria-checked={active}
              accessibilityLabel={`${c.name}, ${countFor(c)}`}
              style={({ pressed }) => [
                styles.tile,
                dense && styles.denseTile,
                tileH ? { height: tileH, aspectRatio: undefined, minHeight: 0 } : null,
                pressed && styles.pressed,
              ]}
            >
              <LinearGradient colors={[palette.top, palette.surface]} style={styles.glassBg} pointerEvents="none" />
              {/* L'oggetto 3D sta nella parte alta della tessera: il nome resta sotto, senza coprirlo. */}
              <View style={[styles.artBox, fitArt]} pointerEvents="none"><CategoryArtwork category={c} reference fade={false} testID={`category-art-${c.id}`} /></View>
              <View style={styles.labels}>
                <Text testID={`category-name-${c.id}`} style={[styles.tileName, tileW >= 140 && styles.largeName, dense && styles.denseName]} numberOfLines={2}>{c.name}</Text>
                <CategorySelectionLight id={c.id} color={color} active={active} />
              </View>
              <CategoryTileEdge color={color} active={active} />
            </Pressable>
            </Animated.View>
          );
        }) : null}
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  allCard: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md, paddingBottom: 20, minHeight: 90,
    borderRadius: radius.lg, marginBottom: spacing.md,
    backgroundColor: palette.surface,
  },
  allBg: { borderRadius: radius.lg },
  allArt: { position: "absolute", right: spacing.md },
  allText: { width: "68%" },
  allName: {
    color: palette.text, fontFamily: typography.bodyMedium, fontSize: 16,
    textShadowColor: withAlpha(colors.artworkSurface, 0.9), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 6,
  },
  allSub: {
    color: withAlpha(colors.onGradient, 0.8), fontFamily: typography.body, fontSize: 11, lineHeight: 15, marginTop: 3,
    textShadowColor: withAlpha(colors.artworkSurface, 0.9), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 5,
  },

  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, paddingTop: spacing.xs, paddingHorizontal: spacing.xs, justifyContent: "center" },
  tile: {
    width: "100%", aspectRatio: 0.72, minHeight: 148, justifyContent: "flex-end", overflow: "hidden",
    borderRadius: 18,
    backgroundColor: palette.surface,
  },
  denseTile: { aspectRatio: 0.76, minHeight: 0, borderRadius: 14 },
  // Riquadro dell'oggetto 3D: in alto, un po' più stretto della tessera, così
  // finisce sopra alla zona del nome (niente scritte sopra all'icona).
  artBox: { position: "absolute", top: 2, left: "9%", width: "82%", aspectRatio: 1 },
  labels: { paddingHorizontal: 4, paddingBottom: 3, alignItems: "center" },
  tileName: { color: palette.text, fontFamily: typography.bodyMedium, fontSize: 12.5, lineHeight: 16, minHeight: 32, textAlign: "center", verticalAlign: "middle" },
  largeName: { fontSize: 15, lineHeight: 18, minHeight: 36 },
  denseName: { fontSize: 10, lineHeight: 12.5, minHeight: 25 },
  pressed: { opacity: 0.86, transform: [{ scale: 0.98 }] },
  allLight: { position: "absolute", bottom: 3, left: 0, right: 0 },
  glassBg: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
}));
