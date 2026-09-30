// PAUSE — fine della storia (variante "Prossima scoperta"): conclusione "Da
// ricordare" editoriale direttamente sullo sfondo cinematico, i tre dati della
// storia, Mi piace / Salva / Condividi (oggetti 3D, con stato acceso/spento) in
// un'unica barra e, in fondo, la card della prossima scoperta con copertina,
// titolo e freccia. Il contenuto compare con una dissolvenza morbida quando si
// arriva in fondo, e il Salva mostra una conferma ampia "Aggiunto ai salvati".
import { View, Text, Pressable, StyleSheet } from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Extrapolation, interpolate, useAnimatedStyle, SharedValue } from "react-native-reanimated";
import * as Haptics from "@/src/haptics";

import { Story, StoryPreview } from "@/src/api";
import { makeStyles, useTheme, spacing, radius, typography, withAlpha } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { GlowButton, GlowOrb } from "@/src/components/glass";
import { READER_MAX_W } from "@/src/components/reader-section";
import { StoryHero } from "@/src/components/story-hero";
import { HighlightedTitle } from "@/src/components/highlighted-title";
import { StoryInfoGrid } from "@/src/components/story-info-grid";
import { ActionIcon3D } from "@/src/components/action-icon-3d";

type Props = {
  story: Story;
  liked: boolean;
  onLike: () => void;
  bookmarked: boolean;
  onBookmark: () => void;
  onShare: () => void;
  onNext: () => void;
  /** Torna alla Home (tasto a sinistra della storia consigliata). */
  onHome: () => void;
  /** Prossima storia già precaricata: alimenta la card "Prossima scoperta". */
  next?: StoryPreview | null;
  bottomInset: number;
  /** Notifica un salvataggio/rimozione: il deep-dive mostra un banner ampio. */
  onSaved?: (saved: boolean) => void;
  /** Posizione di scroll, altezza pagina e Y del finale: per la dissolvenza
      morbida del contenuto quando si arriva in fondo alla storia. */
  scrollY?: SharedValue<number>;
  pageH?: SharedValue<number>;
  endTop?: SharedValue<number>;
};

// Occhiello con la codina luminosa che sfuma verso destra (come nel mockup).
function EyebrowLine({ label, color, large = false, testID }: { label: string; color: string; /** Titolo di sezione più grande (Prossima scoperta). */ large?: boolean; testID?: string }) {
  const styles = useStyles();
  return (
    <View style={styles.eyebrowRow} testID={testID}>
      <Text style={[styles.eyebrow, large && styles.eyebrowLarge, { color }]}>{label}</Text>
      <LinearGradient
        colors={[withAlpha(color, 0.55), withAlpha(color, 0)]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
        style={styles.eyebrowFade}
      />
    </View>
  );
}

export function ReaderEnding({ story, liked, onLike, bookmarked, onBookmark, onShare, onNext, onHome, next, bottomInset, onSaved, scrollY, pageH, endTop }: Props) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();

  const handleBookmark = () => {
    const willSave = !bookmarked;
    Haptics.notificationAsync(
      willSave ? Haptics.NotificationFeedbackType.Success : Haptics.NotificationFeedbackType.Warning,
    ).catch(() => {});
    onBookmark();
    onSaved?.(willSave);
  };

  const handleLike = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    onLike();
  };
  const handleShare = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    onShare();
  };

  // Dissolvenza morbida: il contenuto sale e compare appena prima di arrivare
  // in fondo (stessa logica dello sfondo finale). Se i valori non ci sono
  // (caso improbabile), resta pienamente visibile.
  const reveal = useAnimatedStyle(() => {
    if (!scrollY || !pageH || !endTop) return { opacity: 1 };
    const end = endTop.value;
    if (end <= 0) return { opacity: 1 };
    const from = end - pageH.value * 0.5;
    const to = end - pageH.value * 0.12;
    const p = interpolate(scrollY.value, [from, to], [0, 1], Extrapolation.CLAMP);
    return { opacity: p, transform: [{ translateY: interpolate(p, [0, 1], [26, 0]) }] };
  });

  return (
    <Animated.View style={[styles.section, reveal, { paddingBottom: bottomInset + spacing.md }]} testID="deep-dive-ending">
      {/* Da ricordare — sommario editoriale direttamente sullo sfondo. */}
      {/* Contenitore in vetro: il riassunto ha più rilievo e si stacca dal resto. */}
      <View style={[styles.rememberCard, { borderColor: withAlpha(colors.cyan, 0.32), boxShadow: `inset 0px 0px 26px ${withAlpha(colors.cyan, 0.07)}, 0px 10px 28px ${colors.glassShadow}` as any }]} testID="remember-card">
        <LinearGradient pointerEvents="none" colors={[withAlpha(colors.cyan, 0.1), withAlpha(colors.surfaceDeep, 0.55)]} style={StyleSheet.absoluteFill} />
        <View style={[styles.rememberAccent, { backgroundColor: colors.cyan, boxShadow: `0px 0px 10px ${colors.cyanGlow}` as any }]} />
        <EyebrowLine label={t.remember} color={colors.cyan} />
        <Text style={styles.summary} testID="summary-card" numberOfLines={7}>{story.summary}</Text>
      </View>

      {/* Mi piace / Salva / Condividi uniti in un'unica barra: oggetti 3D nello
          stile dell'app, con stato acceso/spento — stesso vetro della griglia sotto le card. */}
      <View style={styles.actionBar} testID="deep-dive-actions">
        <ActionIcon3D kind="heart" active={liked} glowColor={colors.error} onPress={handleLike} testID="like-button" accessibilityLabel={t.i_like} />
        <LinearGradient
          pointerEvents="none"
          colors={[withAlpha(colors.intro, 0), withAlpha(colors.intro, 0.24), withAlpha(colors.intro, 0)]}
          style={styles.actionDivider}
        />
        <ActionIcon3D kind="bookmark" active={bookmarked} glowColor={colors.cyan} onPress={handleBookmark} testID="bookmark-button" accessibilityLabel={t.save_verb} />
        <LinearGradient
          pointerEvents="none"
          colors={[withAlpha(colors.intro, 0), withAlpha(colors.intro, 0.24), withAlpha(colors.intro, 0)]}
          style={styles.actionDivider}
        />
        <ActionIcon3D kind="share" glowColor={colors.brand} onPress={handleShare} testID="share-story" accessibilityLabel={t.share} />
      </View>

      {/* Prossima scoperta: card con la copertina della prossima storia. */}
      {next ? (
        <View style={styles.nextWrap} testID="next-discovery">
          {/* Separatore netto tra "Da ricordare" e la prossima scoperta. */}
          <LinearGradient pointerEvents="none" colors={[withAlpha(colors.cyan, 0), withAlpha(colors.cyan, 0.45), withAlpha(colors.cyan, 0)]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.divider} />
          <EyebrowLine label={t.next_discovery} color={colors.cyan} large testID="next-discovery-title" />
          <Pressable
            onPress={onNext}
            testID="next-story"
            accessibilityRole="button"
            accessibilityLabel={`${t.next_discovery}: ${next.title}`}
            style={({ pressed }) => [styles.nextCard, { borderColor: withAlpha(colors.cyan, 0.4) }, pressed && styles.nextCardPressed]}
          >
            <StoryHero story={next} style={StyleSheet.absoluteFill} size="hero" />
            <LinearGradient
              colors={["transparent", withAlpha(colors.surface, 0.9)]}
              locations={[0.3, 1]}
              style={StyleSheet.absoluteFill}
            />
            <HighlightedTitle title={next.title} highlight={next.highlight_words} style={styles.nextTitle} numberOfLines={3} />
          </Pressable>
          {/* Stessi tre dati 3D (tipo · categoria · durata) del resto dell'app. */}
          <StoryInfoGrid story={next} minutes={next.reading_time_min} inline testID="next-info-grid" />
          {/* Due scelte: a sinistra torna alla Home, a destra leggi la storia consigliata. */}
          <View style={styles.nextCtas}>
            <Pressable onPress={onHome} testID="ending-home-btn" accessibilityRole="button" accessibilityLabel={t.back_home}
              style={({ pressed }) => [styles.ctaGhost, pressed && styles.ctaPressed]}>
              <Ionicons name="home-outline" size={18} color={colors.textWarm} />
              <Text style={styles.ctaGhostText} numberOfLines={1}>{t.back_home}</Text>
            </Pressable>
            <Pressable onPress={onNext} testID="ending-read-btn" accessibilityRole="button" accessibilityLabel={t.read_story}
              style={({ pressed }) => [styles.ctaPrimary, { backgroundColor: colors.cyan }, pressed && styles.ctaPressed]}>
              <Text style={[styles.ctaPrimaryText, { color: colors.onGradient }]} numberOfLines={1}>{t.read_story}</Text>
              <Ionicons name="arrow-forward" size={18} color={colors.onGradient} />
            </Pressable>
          </View>
        </View>
      ) : (
        // Fallback finché la prossima storia non è precaricata: tasto testuale.
        <GlowButton onPress={onNext} height={62} style={styles.nextBtn} contentStyle={styles.nextBtnInner} testID="next-story" accessibilityLabel={t.next_story}>
          <Text style={styles.nextLabel} numberOfLines={2}>{t.next_story}</Text>
          <GlowOrb size={34}>
            <Ionicons name="arrow-forward" size={18} color={colors.onGradient} />
          </GlowOrb>
        </GlowButton>
      )}
    </Animated.View>
  );
}

const useStyles = makeStyles((colors) => ({
  section: {
    width: "100%", maxWidth: READER_MAX_W, alignSelf: "center",
    paddingHorizontal: spacing.xl, paddingTop: spacing.sm, gap: spacing.sm, flexGrow: 1,
  },
  eyebrowRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  eyebrow: { fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2, textTransform: "uppercase" },
  eyebrowLarge: { fontSize: 17, letterSpacing: 2.2 },
  divider: { height: 1, alignSelf: "stretch", marginBottom: spacing.md },
  eyebrowFade: { flex: 1, height: 1, borderRadius: 1 },
  summary: {
    color: colors.textWarm, fontFamily: typography.display, fontSize: 17.5, lineHeight: 25, letterSpacing: -0.1,
    textShadowColor: withAlpha(colors.surface, 0.6), textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 8,
  },
  rememberCard: {
    borderRadius: radius.lg, borderWidth: 1, overflow: "hidden",
    paddingVertical: spacing.md, paddingLeft: spacing.lg, paddingRight: spacing.md, gap: spacing.sm,
    backgroundColor: withAlpha(colors.surfaceDeep, 0.5),
  },
  rememberAccent: { position: "absolute", left: 0, top: spacing.md, bottom: spacing.md, width: 3, borderTopRightRadius: 2, borderBottomRightRadius: 2 },

  pills: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginTop: 2 },
  pill: {
    flexDirection: "row", alignItems: "center", gap: 6, height: 30, paddingHorizontal: 12,
    borderRadius: radius.pill, backgroundColor: colors.glassBgLit, borderWidth: 1, borderColor: colors.glassBorder,
  },
  dot: { width: 6, height: 6, borderRadius: 3 },
  pillText: { color: colors.onSurfaceSecondary, fontFamily: typography.bodyBold, fontSize: 12, letterSpacing: 0.2 },

  // Mi piace / Salva / Condividi uniti in un'unica pillola (come la griglia
  // dati sotto le card): fondo profondo, bordo sottile e separatori luminosi.
  actionBar: {
    flexDirection: "row", alignItems: "center", alignSelf: "stretch",
    minHeight: 58, paddingHorizontal: 6, paddingVertical: 8, borderRadius: 999, overflow: "hidden",
    backgroundColor: withAlpha(colors.surfaceDeep, 0.78), borderWidth: 1,
    borderColor: withAlpha(colors.intro, 0.22), marginTop: spacing.xs,
  },
  actionDivider: { width: 1, height: 28 },

  // La prossima scoperta prende tutto lo spazio rimasto: copertina alta e
  // tasti Home / Leggi in fondo alla schermata.
  nextWrap: { marginTop: spacing.lg, gap: spacing.sm, flexGrow: 1 },
  nextCard: {
    flexGrow: 1, minHeight: 190, borderRadius: radius.lg, overflow: "hidden", borderWidth: 1, justifyContent: "flex-end",
    backgroundColor: colors.surfaceTertiary,
    boxShadow: `0px 14px 34px ${colors.glassShadow}` as any,
  },
  nextCardPressed: { opacity: 0.92 },
  nextTitle: {
    color: colors.onGradient, fontFamily: typography.displayBold, fontSize: 20, lineHeight: 25,
    marginHorizontal: 16, marginBottom: 14,
  },

  nextBtn: { marginTop: spacing.xl, marginBottom: spacing.md },
  nextBtnInner: { justifyContent: "space-between", paddingHorizontal: spacing.lg + 4 },
  nextLabel: { flexShrink: 1, color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 16.5, letterSpacing: 0.1 },

  nextCtas: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm },
  ctaGhost: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    height: 48, paddingHorizontal: spacing.md, borderRadius: radius.pill, borderWidth: 1,
    borderColor: colors.glassBorderStrong, backgroundColor: colors.glassBgLit,
  },
  ctaGhostText: { color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 14, letterSpacing: 0.2 },
  ctaPrimary: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    height: 48, borderRadius: radius.pill,
    boxShadow: `0px 10px 24px ${colors.cyanGlow}` as any,
  },
  ctaPrimaryText: { fontFamily: typography.bodyBold, fontSize: 15, letterSpacing: 0.3 },
  ctaPressed: { opacity: 0.9 },
}));
