// PAUSE — CTA dell'introduzione ("Inizia a leggere" / "Ascolta"): pulsante in
// vetro con icona 3D (stesso linguaggio delle icone categoria). I due pulsanti
// condividono lo stesso componente così restano identici per misura.
// Il libro, al tocco, "sfoglia una pagina" (rotateY di una lamina) mentre
// l'oggetto fa un piccolo rimbalzo; le cuffie fanno solo il rimbalzo.
import { ActivityIndicator, Pressable, StyleProp, StyleSheet, Text, View, ViewStyle } from "react-native";
import { BlurView } from "expo-blur";
import { Image } from "expo-image";
import Animated, {
  useSharedValue, useAnimatedStyle, withSequence, withTiming, withSpring, withDelay, runOnJS, Easing, interpolate, Extrapolation,
} from "react-native-reanimated";

import { makeStyles, radius, typography, useTheme, withAlpha } from "@/src/theme";

const ART = {
  book: require("../../assets/images/kind-book.png"),
  headphones: require("../../assets/images/kind-headphones.png"),
};
const ICON = 38;

export function IntroCtaButton({ label, icon, onPress, testID, style, loading = false, flat = false }: {
  label: string; /** Senza icona: pulsante solo testo, più pulito. */ icon?: keyof typeof ART; onPress: () => void; testID: string; style?: StyleProp<ViewStyle>; loading?: boolean;
  /** Senza sfocatura (livello di transizione): una vista sfocata dentro un genitore che si dissolve non rende bene ed è pesante da muovere. */
  flat?: boolean;
}) {
  const styles = useStyles();
  const { colors, scheme } = useTheme();
  const flip = useSharedValue(0);   // 0 → 1: la pagina ruota da destra a sinistra
  const bounce = useSharedValue(1);
  const glowColor = icon === "book" ? colors.cyan : colors.brand;

  const press = () => {
    if (!icon) { onPress(); return; }
    bounce.value = withSequence(withTiming(1.12, { duration: 150, easing: Easing.out(Easing.quad) }), withDelay(60, withSpring(1, { damping: 9, stiffness: 170 })));
    if (icon !== "book") { onPress(); return; }
    flip.value = 0;
    flip.value = withTiming(1, { duration: 520, easing: Easing.inOut(Easing.cubic) }, (done) => {
      if (done) { flip.value = 0; runOnJS(onPress)(); }
    });
  };

  const artStyle = useAnimatedStyle(() => ({ transform: [{ scale: bounce.value }] }));
  // La pagina è la metà destra del libro stesso: ruota sul dorso verso
  // sinistra e, superata la verticale, si dissolve.
  const pageStyle = useAnimatedStyle(() => ({
    opacity: flip.value === 0 ? 0 : interpolate(flip.value, [0, 0.5, 0.85], [1, 1, 0], Extrapolation.CLAMP),
    transform: [{ perspective: 220 }, { rotateY: `${interpolate(flip.value, [0, 1], [0, -160])}deg` }],
  }));
  const pageShade = useAnimatedStyle(() => ({ opacity: interpolate(flip.value, [0, 0.5, 1], [0, 0.45, 0.6], Extrapolation.CLAMP) }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: interpolate(flip.value, [0, 0.5, 1], [0.35, 1, 0.35]) }));

  return (
    <Pressable
      testID={testID}
      onPress={press}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ busy: loading }}
      style={({ pressed }) => [styles.button, !icon && styles.buttonPlain, pressed && styles.pressed, style]}
    >
      {flat ? null : <BlurView pointerEvents="none" tint={scheme === "dark" ? "dark" : "light"} intensity={30} style={StyleSheet.absoluteFill} />}
      {icon ? <View style={styles.iconWrap}>
        <Animated.View pointerEvents="none" style={[styles.glow, { backgroundColor: withAlpha(glowColor, 0.28), boxShadow: `0px 0px 18px ${withAlpha(glowColor, 0.8)}` as any }, glowStyle]} />
        {loading ? <ActivityIndicator color={colors.textWarm} size="small" /> : (
          <Animated.View style={[styles.art, artStyle]}>
            <Image source={ART[icon]} style={StyleSheet.absoluteFill} contentFit="contain" transition={0} />
            {icon === "book" ? (
              <Animated.View pointerEvents="none" style={[styles.page, pageStyle]}>
                <Image source={ART.book} style={styles.pageArt} contentFit="contain" transition={0} />
                <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: colors.artworkSurface }, pageShade]} />
              </Animated.View>
            ) : null}
          </Animated.View>
        )}
      </View> : null}
      {!icon && loading ? <ActivityIndicator color={colors.textWarm} size="small" /> :
        <Text testID={`${testID}-label`} style={[styles.label, !icon && styles.labelPlain]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.78}>{label}</Text>}
    </Pressable>
  );
}

const useStyles = makeStyles((colors) => ({
  button: {
    minHeight: 58, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingLeft: 8, paddingRight: 12, paddingVertical: 8, borderRadius: radius.pill, overflow: "hidden",
    backgroundColor: withAlpha(colors.onGradient, 0.06), borderWidth: 1, borderColor: withAlpha(colors.onGradient, 0.22),
    boxShadow: `0px 8px 24px ${colors.glassShadow}` as any,
  },
  pressed: { opacity: 0.88, transform: [{ scale: 0.985 }] },
  buttonPlain: { paddingHorizontal: 20 },
  labelPlain: { fontSize: 15, lineHeight: 19, letterSpacing: 0.2 },
  iconWrap: { width: ICON + 4, height: ICON + 4, alignItems: "center", justifyContent: "center" },
  glow: { position: "absolute", width: ICON * 0.6, height: ICON * 0.6, borderRadius: ICON * 0.3 },
  art: { width: ICON, height: ICON },
  page: { position: "absolute", left: ICON * 0.5, top: 0, width: ICON * 0.5, height: ICON, overflow: "hidden", transformOrigin: "left center" },
  pageArt: { position: "absolute", left: -ICON * 0.5, top: 0, width: ICON, height: ICON },
  label: { flexShrink: 1, color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 13.5, lineHeight: 17, textAlign: "center" },
}));
