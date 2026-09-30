// PAUSE — una sezione (capitolo) della lettura verticale continua: il testo
// vive direttamente sul fondo, senza card. Numero del capitolo grande e quasi
// trasparente come elemento grafico, occhiello "CAPITOLO X" nel colore del
// tema, titolo, corpo in paragrafi brevi. Nessun contenuto extra.
import { useEffect, useState } from "react";
import { View, Text } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Extrapolation, interpolate, SharedValue, useAnimatedStyle, useDerivedValue, useSharedValue } from "react-native-reanimated";

import { Chapter, Story } from "@/src/api";
import { makeStyles, useTheme, spacing, typography, withAlpha } from "@/src/theme";
import { HighlightedTitle } from "@/src/components/highlighted-title";

// Larghezza di lettura controllata: su tablet il testo non si allarga oltre
// una riga confortevole, su telefono usa tutta la larghezza meno i margini.
export const READER_MAX_W = 640;
const LONG_PARAGRAPH = 520;
// Geometria della sezione (deve coincidere con gli stili qui sotto).
const NORMAL_PAD = { top: spacing.xxl + spacing.md, bottom: spacing.xl };
const TIGHT_PAD = { top: spacing.xl, bottom: spacing.lg };
const SECTION_GAP = spacing.sm + 2;
// Sforo massimo (punti) oltre la schermata che la versione compatta può assorbire.
const TIGHT_MAX_OVERFLOW = 120;
// Intestazione del capitolo: spazio sopra all'occhiello (dove sta il numero in
// filigrana), altezza dell'occhiello, distanza occhiello → titolo, corpo del titolo.
const HEAD_TOP = spacing.xxl, HEAD_TOP_TIGHT = spacing.md;
const EYEBROW_LH = 16;
const EYEBROW_GAP = spacing.sm + 2, EYEBROW_GAP_TIGHT = spacing.sm;
const TITLE_FONT = 31;
// Anticipazione: la stessa intestazione, ridotta (titolo a 22 pt), in fondo alla
// schermata precedente — filo (1) + spacing.md, occhiello, spacing.xs, titolo.
const TEASER_FONT = 22;
const TEASER_SCALE = TEASER_FONT / TITLE_FONT;
const TEASER_EYEBROW_Y = spacing.md + 1;
const TEASER_TITLE_Y = TEASER_EYEBROW_Y + EYEBROW_LH + spacing.xs;
// Spazio fra l'anticipazione e il fondo della schermata (fa da padding inferiore).
const LAND_PAD = spacing.xl;
const teaserHeight = (titleH: number) => { "worklet"; return TEASER_TITLE_Y + titleH * TEASER_SCALE; };

/** Quote dello scroll che guidano la trasformazione anticipazione → intestazione. */
export type ChapterTrack = {
  scrollY: SharedValue<number>;
  /** Inizio di ogni sezione nello scroll (coordinate contenuto). */
  tops: SharedValue<number[]>;
  /** Altezza dello ScrollView. */
  pageH: SharedValue<number>;
  /** Fondo della barra: le sezioni si allineano qui (+ spacing.sm). */
  headerBottom: number;
};

// Solo presentazione: il testo resta identico, ma un capitolo molto lungo
// viene mostrato in due paragrafi spezzati alla fine di una frase.
export function splitParagraphs(body: string): string[] {
  const lines = body.split(/\n+/).map((s) => s.trim()).filter(Boolean);
  if (lines.length > 1) return lines;
  const text = lines[0] ?? "";
  if (text.length <= LONG_PARAGRAPH) return [text];
  const mid = text.length / 2;
  let cut = -1;
  const re = /[.!?»"”]\s+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const end = m.index + m[0].length;
    if (cut < 0 || Math.abs(end - mid) < Math.abs(cut - mid)) cut = end;
  }
  if (cut <= 0 || cut >= text.length - 40) return [text];
  return [text.slice(0, cut).trim(), text.slice(cut).trim()];
}

export function SectionDivider({ color }: { color?: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  const tint = color ?? colors.cyan;
  return (
    <View style={styles.divider} pointerEvents="none">
      <LinearGradient
        colors={[withAlpha(tint, 0), withAlpha(tint, 0.55), withAlpha(tint, 0)]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={styles.dividerLine}
      />
    </View>
  );
}

// Solo presentazione: le mini lezioni numerano i passi nel titolo
// ("Passo 3 — Osserva"): nel lettore il numero non serve, resta il titolo.
export function stripStepPrefix(title: string): string {
  return title.replace(/^\s*(passo|step)\s*\d+\s*[—–\-:·]\s*/i, "").trim() || title;
}

// Un capitolo occupa una schermata: in alto numero, occhiello, titolo e testo;
// in fondo — se c'è un capitolo dopo — lo spazio per la sua anticipazione.
// L'anticipazione È l'intestazione del capitolo seguente, ridotta e attenuata:
// scorrendo, si ingrandisce e sale fino a diventare numero, occhiello e titolo
// del capitolo — nessun doppione. Il capitolo successivo vero inizia
// alla schermata seguente (la lettura avanza a capitoli, non a scorrimento).
export function ChapterSection({ chapter, story, eyebrow, next, minHeight, pageOverlap = 0, index, track }: {
  chapter: Chapter; story: Story; eyebrow: string;
  /** Capitolo seguente (anticipazione in fondo alla schermata). */
  next?: Chapter | null;
  /** Altezza della schermata di lettura: il capitolo la riempie e l'anticipazione poggia sul fondo. */
  minHeight?: number;
  /** Capitoli su più schermate: di quanto la schermata seguente riprende la precedente (barra + una riga), così nessuna riga resta nascosta. */
  pageOverlap?: number;
  /** Posizione della sezione (0 = primo capitolo: nessuna anticipazione lo precede). */
  index: number;
  track: ChapterTrack;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  // Un solo colore per tutti i capitoli di tutte le storie: l'accento del tema
  // corrente dell'app (base = cyan), mai la categoria della storia.
  const tint = colors.brand;
  // Testo più alto di una schermata (caratteri grandi, telefoni bassi): il
  // capitolo occupa un numero intero di schermate, così l'anticipazione resta
  // in fondo all'ultima e il capitolo seguente inizia sempre su una schermata
  // nuova — mai la stessa intestazione due volte di seguito.
  // L'anticipazione si misura a layout (non si stima): così una schermata in
  // più compare solo quando il testo davvero non ci sta, mai per pochi punti.
  // Se sfora di poco, prima si prova la versione compatta (spazi e interlinea
  // ridotti): solo se non basta il capitolo prende una schermata in più.
  const [contentH, setContentH] = useState(0);
  const [tight, setTight] = useState(false);
  const pad = tight ? TIGHT_PAD : NORMAL_PAD;
  // L'anticipazione del capitolo seguente è un livello che "galleggia" in fondo
  // (l'intestazione del prossimo capitolo, ridotta): NON occupa spazio nel
  // layout. Così la sezione è alta quanto serve al SOLO testo: un capitolo il
  // cui testo sta in una schermata avanza sempre con un unico gesto, senza una
  // seconda schermata mezza vuota.
  const readH = pad.top + contentH + pad.bottom;
  const measured = contentH > 0;
  const overflow = minHeight && measured ? readH - minHeight : 0;
  useEffect(() => { setTight(false); }, [minHeight]);
  useEffect(() => {
    if (!tight && overflow > 0 && overflow <= TIGHT_MAX_OVERFLOW) setTight(true);
  }, [tight, overflow]);
  const pages = minHeight && measured ? Math.max(1, Math.ceil((readH - pageOverlap) / (minHeight - pageOverlap))) : 1;
  const sectionH = minHeight ? pages * minHeight - (pages - 1) * pageOverlap : undefined;
  return (
    <View style={[styles.section, { paddingTop: pad.top, paddingBottom: pad.bottom }, sectionH ? { minHeight: sectionH } : null]} testID={`deep-dive-chapter-${chapter.number}`}>
      <View style={styles.content} onLayout={(e) => { const h = Math.ceil(e.nativeEvent.layout.height); if (h !== contentH) setContentH(h); }}>
      <ChapterHeading chapter={chapter} story={story} eyebrow={eyebrow} tint={tint} tight={tight} padTop={pad.top} index={index} track={track} />
      <View style={[styles.body, tight && styles.bodyTight]}>
        {splitParagraphs(chapter.body).map((p, i) => (
          <Text key={i} style={[styles.paragraph, tight && styles.paragraphTight]}>{p}</Text>
        ))}
      </View>
      </View>
      {next ? <TeaserSpace next={next} /> : null}
    </View>
  );
}

// Intestazione del capitolo. Se un capitolo la precede, parte come anticipazione
// in fondo alla schermata precedente (ridotta, attenuata, con il filo sopra e il
// numero accanto all'occhiello) e, guidata dallo scroll, si ingrandisce e si posa
// al suo posto: il numero in filigrana compare, il filo e il numero piccolo spariscono.
function ChapterHeading({ chapter, story, eyebrow, tint, tight, padTop, index, track }: {
  chapter: Chapter; story: Story; eyebrow: string; tint: string; tight: boolean; padTop: number; index: number; track: ChapterTrack;
}) {
  const styles = useStyles();
  const number = String(chapter.number).padStart(2, "0");
  const headTop = tight ? HEAD_TOP_TIGHT : HEAD_TOP;
  const gap = tight ? EYEBROW_GAP_TIGHT : EYEBROW_GAP;
  const titleH = useSharedValue(0);
  const { scrollY, tops, pageH, headerBottom } = track;
  // 0 = anticipazione (la schermata precedente è allineata sotto la barra),
  // 1 = intestazione (questa sezione è allineata). Il primo capitolo nasce già intestazione.
  const p = useDerivedValue(() => {
    if (index === 0) return 1;
    const top = tops.value[index] ?? 0;
    if (top <= 0) return 1;
    return interpolate(scrollY.value, [top - pageH.value + spacing.sm, top - headerBottom - spacing.sm], [0, 1], Extrapolation.CLAMP);
  });
  // Sale (in coordinate contenuto) fin dentro lo spazio riservato in fondo alla sezione precedente.
  const groupStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: -(padTop + LAND_PAD + teaserHeight(titleH.value)) * (1 - p.value) }],
  }));
  const numberStyle = useAnimatedStyle(() => ({ opacity: p.value }));
  const dividerStyle = useAnimatedStyle(() => ({ opacity: 1 - p.value }));
  const eyebrowStyle = useAnimatedStyle(() => ({
    opacity: 0.6 + 0.4 * p.value,
    transform: [{ translateY: (TEASER_EYEBROW_Y - headTop) * (1 - p.value) }],
  }));
  const eyebrowNumberStyle = useAnimatedStyle(() => ({ opacity: 1 - p.value }));
  const titleStyle = useAnimatedStyle(() => ({
    opacity: 0.5 + 0.5 * p.value,
    transform: [
      { translateY: (TEASER_TITLE_Y - (headTop + EYEBROW_LH + gap)) * (1 - p.value) },
      { scale: TEASER_SCALE + (1 - TEASER_SCALE) * p.value },
    ],
  }));
  return (
    <Animated.View style={[styles.heading, { paddingTop: headTop }, groupStyle]} testID={`reader-chapter-heading-${chapter.number}`}>
      <Animated.View style={[styles.teaserDivider, dividerStyle]} pointerEvents="none"><SectionDivider color={tint} /></Animated.View>
      {/* Numero grande e quasi trasparente: elemento grafico, non informazione. */}
      <Animated.Text style={[styles.bigNumber, tight && styles.bigNumberTight, { color: withAlpha(tint, 0.13) }, numberStyle]} pointerEvents="none" testID={`reader-chapter-number-${chapter.number}`}>{number}</Animated.Text>
      <Animated.View style={[styles.eyebrowRow, { marginBottom: gap }, eyebrowStyle]}>
        <Text style={[styles.eyebrow, { color: tint }]} testID={`reader-chapter-eyebrow-${chapter.number}`}>{eyebrow.toUpperCase()}</Text>
        <Animated.Text style={[styles.eyebrow, styles.eyebrowNumber, { color: tint }, eyebrowNumberStyle]}>{number}</Animated.Text>
      </Animated.View>
      <Animated.View style={[styles.titleWrap, titleStyle]} onLayout={(e) => { titleH.value = e.nativeEvent.layout.height; }}>
        <HighlightedTitle
          title={stripStepPrefix(chapter.title)}
          highlight={story.highlight_words}
          highlightColor={tint}
          style={styles.title}
        />
      </Animated.View>
    </Animated.View>
  );
}

// Segnaposto in fondo alla sezione: l'anticipazione vera (l'intestazione del
// capitolo seguente, ridotta) è disegnata dal capitolo dopo e "galleggia" qui
// sopra grazie alla sua traslazione. Questo marcatore non occupa layout.
function TeaserSpace({ next }: { next: Chapter }) {
  const styles = useStyles();
  return (
    <View style={styles.teaserSpace} testID={`reader-chapter-preview-${next.number}`} pointerEvents="none"
      accessibilityElementsHidden importantForAccessibility="no-hide-descendants" />
  );
}

const useStyles = makeStyles((colors) => ({
  section: {
    width: "100%", maxWidth: READER_MAX_W, alignSelf: "center",
    paddingHorizontal: spacing.xl,
    gap: SECTION_GAP,
  },
  heading: {},
  teaserDivider: { position: "absolute", top: 0, left: 0, right: 0 },
  bigNumber: {
    position: "absolute", top: -spacing.lg, left: -4,
    fontFamily: typography.displayBold, fontSize: 96, lineHeight: 100, letterSpacing: -4,
  },
  divider: { alignItems: "center", marginBottom: spacing.md },
  dividerLine: { width: "62%", height: 1, borderRadius: 1 },
  eyebrowRow: { flexDirection: "row", height: EYEBROW_LH },
  eyebrow: { fontFamily: typography.bodyBold, fontSize: 12, lineHeight: EYEBROW_LH, letterSpacing: 3 },
  eyebrowNumber: { marginLeft: 7 },
  titleWrap: { transformOrigin: "left top" },
  title: {
    color: colors.textWarm, fontFamily: typography.displayBold, fontSize: TITLE_FONT, lineHeight: 37, letterSpacing: -0.7,
  },
  content: { gap: spacing.sm + 2 },
  body: { gap: spacing.md + 2, marginTop: spacing.sm },
  // Segnaposto dell'anticipazione: assoluto in fondo, non contribuisce all'altezza.
  teaserSpace: { position: "absolute", left: 0, right: 0, bottom: 0, height: 0 },
  teaserMeasure: { position: "absolute", left: 0, right: 0, top: 0, opacity: 0 },
  paragraph: { color: colors.textWarmSecondary, fontFamily: typography.body, fontSize: 17.5, lineHeight: 31, letterSpacing: 0.1 },
  // Versione compatta (capitolo che sfora di poco la schermata): stessi
  // elementi, spazi e interlinea ridotti, così resta su una schermata sola.
  bigNumberTight: { top: -spacing.md, fontSize: 76, lineHeight: 80, letterSpacing: -3 },
  bodyTight: { gap: spacing.sm + 2, marginTop: spacing.xs },
  paragraphTight: { fontSize: 16.5, lineHeight: 27 },
}));
