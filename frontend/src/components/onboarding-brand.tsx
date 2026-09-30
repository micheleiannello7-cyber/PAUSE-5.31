import { StyleSheet, Text, View } from "react-native";
import { Image } from "expo-image";
import Svg, { Path } from "react-native-svg";
import { typography } from "@/src/theme";

// Simbolo PAUSE: icona 3D lucida (anello con gradiente magenta→blu→ciano e due
// barre) generata da zero sul mockup dell'utente, con sfondo trasparente.
const PAUSE_MARK = require("../../assets/images/pause-mark.png");

// Vector wordmark stays sharp at every device pixel ratio. Fixed reference
// palette deliberately does not change with the user's light/dark theme.
export function OnboardingBrand({ unit, top }: { unit: number; top: number }) {
  return (
    <View testID="onboarding-brand" style={[styles.brand, { top }]} accessible accessibilityLabel="PAUSE">
      <View style={styles.markWrap}>
        {/* Alone morbido blu/viola dietro l'anello: profondità senza effetto gaming. */}
        <View pointerEvents="none" style={[styles.glow, { width: 190 * unit, height: 190 * unit, borderRadius: 95 * unit }]} />
        <Image
          testID="onboarding-pause-mark"
          source={PAUSE_MARK}
          contentFit="contain"
          transition={0}
          accessible={false}
          style={{ width: 300 * unit, height: 300 * unit, marginVertical: -21 * unit }}
        />
      </View>
      <View testID="onboarding-wordmark" style={[styles.wordmarkRow, { gap: 33 * unit, marginTop: 17 * unit }]}>
        {["P", "A", "U", "S", "E"].map((letter) => letter === "A" ? (
          <Svg key={letter} width={58 * unit} height={61 * unit} viewBox="0 0 60 64" testID="onboarding-wordmark-a">
            <Path d="M 5 60 L 30 5 L 55 60" fill="none" stroke="#F6F8FF" strokeWidth="6.4" strokeLinecap="square" strokeLinejoin="round" />
          </Svg>
        ) : <Text key={letter} testID={`onboarding-wordmark-${letter.toLowerCase()}`} style={[styles.wordmark, { fontSize: 78 * unit, lineHeight: 96 * unit }]} maxFontSizeMultiplier={1}>{letter}</Text>)}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  brand: { position: "absolute", left: 0, right: 0, alignItems: "center" },
  markWrap: { alignItems: "center", justifyContent: "center" },
  glow: { position: "absolute", backgroundColor: "#3B63FF22", boxShadow: "0px 0px 70px 30px #3F6BFF3D, 0px 0px 40px 10px #8A4CF52E" },
  wordmarkRow: { flexDirection: "row", alignItems: "center" },
  wordmark: {
    color: "#F6F8FF", fontFamily: typography.display, includeFontPadding: false,
    textShadowColor: "#6FB8FF66", textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 14,
  },
});