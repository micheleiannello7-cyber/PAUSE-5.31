// PAUSE — "Le tue categorie" in Home: una sola riga scorrevole a swipe (niente
// autoplay, niente frecce). Le card sono le stesse tessere in vetro della
// griglia, solo disposte in fila: su ogni larghezza stanno 3–4 card intere più
// una porzione (~40%) della successiva, che invita a trascinare. Sotto, un
// piccolo indicatore lineare di posizione.
import { ReactNode } from "react";
import { StyleSheet, View } from "react-native";
import Animated, { Extrapolation, interpolate, useAnimatedScrollHandler, useAnimatedStyle, useSharedValue } from "react-native-reanimated";
import { Category } from "@/src/api";
import { useTheme, withAlpha } from "@/src/theme";
import { HomeCategoryTile } from "./home-controls";

const GAP = 12;
// Porzione della card successiva sempre visibile a fine riga.
const PEEK = 0.4;
const INDICATOR_W = 64;

// Card intere per riga: 3 sui telefoni stretti, 4 dagli altri in su. La misura
// viene dalla larghezza, così la card "a metà" non è mai tagliata per caso.
export function carouselTileSize(width: number, padding: number): number {
  const full = width < 360 ? 3 : 4;
  return Math.floor((width - padding - GAP * full) / (full + PEEK));
}

export function HomeCategoryCarousel({ categories, activeIds, onToggle, width, padding, overlay }: {
  categories: Category[];
  activeIds: string[];
  onToggle: (id: string) => void;
  /** Larghezza della Home (già limitata a 600). */
  width: number;
  /** Margine laterale della Home: la fila parte allineata al titolo. */
  padding: number;
  /** Livello sopra alla fila (es. avviso "almeno una categoria"). */
  overlay?: ReactNode;
}) {
  const { colors } = useTheme();
  const size = carouselTileSize(width, padding);
  const contentW = categories.length * size + Math.max(0, categories.length - 1) * GAP + padding * 2;
  const scrollable = contentW > width + 1;
  const maxScroll = Math.max(1, contentW - width);
  const scrollX = useSharedValue(0);
  const onScroll = useAnimatedScrollHandler({ onScroll: (e) => { scrollX.value = e.contentOffset.x; } });
  const thumbW = Math.max(16, Math.round(INDICATOR_W * Math.min(1, width / contentW)));
  const thumbStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: interpolate(scrollX.value, [0, maxScroll], [0, INDICATOR_W - thumbW], Extrapolation.CLAMP) }],
  }));

  return (
    <View testID="home-category-carousel">
      <View>
        <Animated.ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          onScroll={onScroll}
          scrollEventThrottle={16}
          style={{ width }}
          contentContainerStyle={[styles.row, { paddingHorizontal: padding, gap: GAP }]}
          testID="home-category-list"
        >
          {categories.map((cat) => (
            <HomeCategoryTile key={cat.id} cat={cat} size={size} glass active={activeIds.includes(cat.id)} onPress={() => onToggle(cat.id)} />
          ))}
        </Animated.ScrollView>
        {overlay}
      </View>
      {scrollable ? (
        <View style={styles.indicatorWrap} testID="home-category-indicator">
          <View style={[styles.track, { width: INDICATOR_W, backgroundColor: withAlpha(colors.brand, 0.16) }]}>
            <Animated.View style={[styles.thumb, { width: thumbW, backgroundColor: colors.brand, boxShadow: `0px 0px 8px ${withAlpha(colors.brand, 0.6)}` as any }, thumbStyle]} />
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  // Un filo di spazio verticale: la luce ambientale delle card non viene tagliata.
  row: { paddingVertical: 6, alignItems: "flex-start" },
  indicatorWrap: { alignItems: "center", paddingTop: 6 },
  track: { height: 3, borderRadius: 2, overflow: "hidden" },
  thumb: { height: 3, borderRadius: 2 },
});
