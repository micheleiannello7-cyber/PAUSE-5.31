// PAUSE — indicatore sotto il mazzo della Home. Non "pallini a numero fisso":
// a sinistra piccoli punti per le card già attraversate, al centro la card
// attuale (punto un po' più grande con alone nel colore del tema), a destra una
// linea sottilissima che sfuma, per dire che si può continuare — non quanto manca.
// Il punto attivo resta fermo al centro: i punti passati crescono verso sinistra.
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { FadeIn } from "react-native-reanimated";
import { useTheme, withAlpha } from "@/src/theme";

// Punti passati mostrati al massimo; i più vecchi si attenuano (la storia continua a sinistra).
const MAX_PAST = 6;
const DOT = 4;
const DOT_GAP = 7;
const ACTIVE = 7;
const LINE_W = 112;
export const DECK_PROGRESS_H = 20;

export function DeckProgress({ cursor, total }: { cursor: number; total: number }) {
  const { colors } = useTheme();
  const past = Math.min(cursor, MAX_PAST);
  const pastW = MAX_PAST * DOT + (MAX_PAST - 1) * DOT_GAP;
  return (
    <View style={styles.row} testID="discover-deck-dots" accessibilityLabel={`${cursor + 1} / ${total}`}>
      {/* Card già viste: allineate a destra, verso il punto attivo. */}
      <View style={[styles.past, { width: pastW }]}>
        {Array.from({ length: past }, (_, i) => {
          // i = 0 è la più lontana: più tenue; l'ultima passata è la più chiara.
          const strength = past === 1 ? 1 : 0.35 + (0.65 * i) / (past - 1);
          return (
            <Animated.View key={cursor - past + i} entering={FadeIn.duration(260)} testID={`discover-deck-dot-${i}`}
              style={[styles.dot, { backgroundColor: withAlpha(colors.brand, 0.22 + 0.5 * strength) }]} />
          );
        })}
      </View>
      {/* Card attuale. */}
      <View testID="discover-deck-dot-active"
        style={[styles.active, { backgroundColor: colors.brand, boxShadow: `0px 0px 10px ${withAlpha(colors.brand, 0.7)}` as any }]} />
      {/* Continuazione: parte dal punto e si spegne verso destra. */}
      <LinearGradient
        colors={[withAlpha(colors.brand, 0.62), withAlpha(colors.brand, 0.28), withAlpha(colors.brand, 0)]}
        locations={[0, 0.45, 1]}
        start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }}
        style={[styles.line, { width: LINE_W }]}
        testID="discover-deck-continue"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  row: { height: DECK_PROGRESS_H, flexDirection: "row", alignItems: "center", justifyContent: "center" },
  past: { flexDirection: "row", alignItems: "center", justifyContent: "flex-end", gap: DOT_GAP, marginRight: DOT_GAP + 1 },
  dot: { width: DOT, height: DOT, borderRadius: DOT / 2 },
  active: { width: ACTIVE, height: ACTIVE, borderRadius: ACTIVE / 2 },
  line: { height: 1.5, borderRadius: 1, marginLeft: -1 },
});
