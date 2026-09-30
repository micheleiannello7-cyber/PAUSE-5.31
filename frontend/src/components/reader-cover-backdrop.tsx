// PAUSE — copertina del lettore: un solo livello fisso dietro allo scroll, a
// tutta larghezza dall'alto dello schermo (dietro la barra), che in basso
// sfuma nell'atmosfera del tema: l'atmosfera è presente "dietro" la copertina
// fin dall'inizio. Scorrendo la copertina sale appena (parallasse), si
// scurisce e si dissolve fino a restare una traccia scura, appena
// riconoscibile, dietro ai capitoli — mai una sostituzione brusca di sfondo.
// Solo transform e opacità: fluida anche su Android, in entrambe le direzioni.
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Extrapolation, interpolate, SharedValue, useAnimatedStyle } from "react-native-reanimated";

import { Story, isLesson } from "@/src/api";
import { makeStyles, useTheme, withAlpha } from "@/src/theme";
import { CoverFrame } from "./reader-intro";
import { StoryHero } from "./story-hero";
import { LessonCover } from "./lesson-cover";

// Quanto resta della copertina dietro ai capitoli (traccia scura).
const TRACE = 0.4;
// Parallasse: la copertina sale più lenta del contenuto e poi si ferma.
const PARALLAX = 0.28;
// Fascia di raccordo sotto la copertina: il fondo in cui la foto si è dissolta
// torna gradualmente all'atmosfera (luci comprese), senza una linea visibile.
export const COVER_SEAM = 150;

/** Raccordo sotto la copertina: dal fondo del tema di nuovo all'atmosfera, gradualmente. */
export function CoverSeam({ top }: { top: number }) {
  const { colors } = useTheme();
  return (
    <LinearGradient
      colors={[colors.atmosBase, withAlpha(colors.atmosBase, 0.6), withAlpha(colors.atmosBase, 0)]}
      locations={[0, 0.4, 1]}
      style={[styles.seam, { top }]}
      pointerEvents="none"
    />
  );
}

/** Pelle "lettura" della copertina: tinta notte + dissolvenza in basso nell'atmosfera del tema. */
export function CoverNightSkin() {
  const { colors } = useTheme();
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {/* Tinta notte: porta ogni foto verso la stessa temperatura blu-notte. */}
      <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.nightTint }]} />
      {/* In alto un velo leggero per la barra; in basso la foto si dissolve nell'atmosfera. */}
      <LinearGradient colors={[withAlpha(colors.atmosBase, 0.45), withAlpha(colors.atmosBase, 0)]} locations={[0, 1]} style={styles.top} />
      <LinearGradient
        colors={[withAlpha(colors.atmosBase, 0), withAlpha(colors.atmosBase, 0.35), withAlpha(colors.atmosBase, 0.86), colors.atmosBase]}
        locations={[0, 0.45, 0.82, 1]}
        style={styles.bottom}
      />
    </View>
  );
}

export function ReaderCoverBackdrop({ story, scrollY, frame, instant = false }: {
  story: Story; scrollY: SharedValue<number>; frame: CoverFrame;
  /** Arrivo con la transizione dalla card: la foto è già a schermo sopra, niente dissolvenza d'ingresso. */
  instant?: boolean;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const hasCover = !!story.hero_image_generated || (!isLesson(story) && !!story.hero_image);

  const box = useAnimatedStyle(() => {
    const y = scrollY.value;
    // Tirando verso il basso oltre l'inizio la foto segue un po' il dito e si stira.
    const pull = y < 0 ? -y : 0;
    return {
      opacity: interpolate(y, [frame.height * 0.25, frame.height * 1.1], [1, TRACE], Extrapolation.CLAMP),
      transform: [
        { translateY: -Math.min(Math.max(0, y), frame.height) * PARALLAX + pull * 0.45 },
        { scale: 1 + Math.min(0.1, pull / 700) },
      ],
    };
  });
  // Si scurisce mentre sale: perde importanza, resta atmosfera.
  const dim = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [0, frame.height * 0.9], [0, 0.5], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View
      style={[styles.box, { top: frame.top, left: frame.left, width: frame.width, height: frame.height + COVER_SEAM }, box]}
      pointerEvents="none"
      testID="chapter-cover-bg"
    >
      <View style={[styles.photo, { height: frame.height, borderRadius: frame.radius }]}>
        {hasCover ? (
          <StoryHero story={story} style={StyleSheet.absoluteFill} transition={instant ? 0 : 400} />
        ) : (
          <LessonCover color={colors.muted} icon={story.category_icon} iconSize={72} showBadge={false} style={StyleSheet.absoluteFill} />
        )}
        <CoverNightSkin />
        <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: colors.atmosBase }, dim]} />
      </View>
      <CoverSeam top={frame.height} />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  top: { position: "absolute", top: 0, left: 0, right: 0, height: "22%" },
  bottom: { position: "absolute", bottom: 0, left: 0, right: 0, height: "62%" },
  seam: { position: "absolute", left: 0, right: 0, height: COVER_SEAM },
});

const useStyles = makeStyles(() => ({
  box: { position: "absolute", overflow: "hidden" },
  photo: { position: "absolute", top: 0, left: 0, right: 0, overflow: "hidden" },
}));
