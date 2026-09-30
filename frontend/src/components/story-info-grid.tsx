// PAUSE — scheda informativa della storia (presentazione, sotto l'introduzione):
// una pillola con tre sezioni — Tipo · Categoria · Durata — e separatori sottili.
// Gli stessi oggetti 3D affiancano i valori, senza tessere colorate né aloni.
import { Fragment } from "react";
import { View, Text } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";

import { StoryPreview, isLesson } from "@/src/api";
import { makeStyles, typography, useTheme, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { KindIcon } from "./kind-icon";
import { CategoryArtMark } from "./category-artwork";

const ICON = 24;
// Orologio 3D generato nello stesso stile delle icone categoria e dei CTA.
const CLOCK = require("../../assets/images/kind-clock.png");

export function StoryInfoGrid({ story, minutes, inline = false, testID = "story-info-grid" }: {
  story: StoryPreview; minutes: number;
  /** Lettura editoriale: stessi tre dati in una riga leggera, senza pillola né fondo. */
  inline?: boolean; testID?: string;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();
  const lesson = isLesson(story);
  const category = story.category_name.split("·")[0].trim();
  const cells = [
    { id: "kind", value: lesson ? t.lesson_badge : t.curiosity_badge,
      // Il PNG di lampadina/libri ha margini trasparenti (~15%): la si
      // ingrandisce perché l'oggetto visibile arrivi all'altezza degli altri due.
      icon: <KindIcon kind={lesson ? "lessons" : "stories"} size={ICON + 8} glow={false} testID={`${testID}-kind-icon`} /> },
    { id: "category", value: category,
      // Ritaglio stretto (senza i margini trasparenti dello studio) in un
      // riquadro un po' più largo che alto: anche gli oggetti larghi (pianeta)
      // arrivano all'altezza di lampadina/libri e orologio, senza tagli.
      icon: <CategoryArtMark categoryId={story.category_id} color={story.category_color} size={ICON} aspect={1.3} plain tight testID={`${testID}-category-icon`} /> },
    { id: "time", value: `${minutes} ${t.min}`,
      icon: <Image source={CLOCK} style={styles.clock} contentFit="contain" transition={0} testID={`${testID}-time-icon`} /> },
  ];
  return (
    <View style={[styles.grid, inline && styles.gridInline]} testID={testID}>
      {cells.map((c, index) => (
        <Fragment key={c.id}>
          {index > 0 && (
            <LinearGradient
              pointerEvents="none"
              colors={[withAlpha(colors.intro, 0), withAlpha(inline ? colors.brand : colors.intro, inline ? 0.32 : 0.24), withAlpha(colors.intro, 0)]}
              style={styles.divider}
              testID={`${testID}-divider-${index}`}
            />
          )}
          <View style={[styles.cell, c.id === "category" ? styles.cellGrow : styles.cellFixed]} testID={`${testID}-${c.id}`}>
            <View style={styles.iconWrap}>{c.icon}</View>
            <Text style={[styles.value, c.id !== "time" && styles.uppercase, c.id === "kind" && styles.kindValue]} numberOfLines={2} testID={`${testID}-${c.id}-value`}>{c.value}</Text>
          </View>
        </Fragment>
      ))}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  grid: {
    flexDirection: "row", alignItems: "center", minHeight: 56,
    paddingHorizontal: 6, paddingVertical: 10, borderRadius: 999, overflow: "hidden",
    backgroundColor: withAlpha(colors.surfaceDeep, 0.78), borderWidth: 1,
    borderColor: withAlpha(colors.intro, 0.22),
  },
  // Lettura: contenitore "vetro" che racchiude i tre dati (i soli separatori
  // non bastavano a tenerli insieme sopra alla copertina).
  gridInline: {
    alignSelf: "stretch", borderRadius: 16, paddingHorizontal: 10, paddingVertical: 8, minHeight: 54,
    backgroundColor: withAlpha(colors.surfaceDeep, 0.58), borderWidth: 1, borderColor: withAlpha(colors.brand, 0.26),
    boxShadow: `inset 0px 0px 22px ${withAlpha(colors.brand, 0.08)}, 0px 6px 22px ${withAlpha(colors.surfaceDeep, 0.5)}` as any,
  },
  // Tipo e durata occupano solo lo spazio del loro contenuto; la categoria (il
  // nome più lungo e variabile) prende tutto il resto e va su due righe: così
  // icone e scritte non si sovrappongono mai, qualunque combinazione.
  cell: { flexDirection: "row", paddingHorizontal: 5, gap: 5, alignItems: "center", justifyContent: "center" },
  cellFixed: { flexGrow: 0, flexShrink: 0 },
  cellGrow: { flex: 1, minWidth: 0 },
  divider: { width: 1, height: 28 },
  iconWrap: { width: ICON + 8, height: ICON + 8, flexShrink: 0, alignItems: "center", justifyContent: "center" },
  clock: { width: ICON + 2, height: ICON + 2 },
  // Solo i valori lunghi vanno su due righe: la barra resta unica anche su telefoni piccoli.
  value: { flexShrink: 1, color: colors.textWarm, fontFamily: typography.bodyMedium, fontSize: 11, lineHeight: 15, textAlign: "left" },
  // "MINI LEZIONE" va su due righe (MINI / LEZIONE), "CURIOSITÀ" resta su una.
  kindValue: { maxWidth: 74 },
  uppercase: { textTransform: "uppercase", letterSpacing: 0.15 },
}));
