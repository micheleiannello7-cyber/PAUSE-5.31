import { useState } from "react";
import { View, StyleSheet } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { Category, categoryArtworkUrl, categoryIllustrationUrl } from "@/src/api";
import { makeStyles, useTheme, withAlpha, radius, categoryTilePalette as palette } from "@/src/theme";
import { CategoryIcon } from "./category-icon";

export const CATEGORY_VISUAL_MODE: "illustrated" | "line" = "illustrated";
const ART_VERSION = "reference-3d-v6";
type ArtworkProps = {
  category: Pick<Category, "id" | "color" | "illustration_generated">;
  testID: string; wide?: boolean; compact?: boolean; cornerRadius?: number;
  /** Stile "vetro" (onboarding): solo l'oggetto 3D ritagliato, senza piastrella nera, con alone morbido. */
  glass?: boolean;
  /** User's reference: full-size cinematic artwork, separate interactive light. */
  reference?: boolean;
  /** Sfumatura verso il fondo tessera sulla parte bassa dell'oggetto (false quando il nome sta sotto, non sopra). */
  fade?: boolean;
  /** Sorgente immagine alternativa (anteprime di nuove famiglie di icone). */
  uriOverride?: string;
  /** Lato dell'oggetto nella tessera larga (`wide`), quando la tessera è più bassa del riferimento. */
  bannerSize?: number;
};

export function CategoryArtwork({ category, ...props }: ArtworkProps) {
  const uri = props.uriOverride
    ? props.uriOverride
    : props.reference
    ? categoryArtworkUrl(category.id, category.illustration_generated || ART_VERSION)
    : props.glass
    ? categoryArtworkUrl(category.id, category.id === "all" ? ART_VERSION : (category.illustration_generated || ART_VERSION), true)
    : category.id === "all"
      ? categoryArtworkUrl("all", ART_VERSION)
      : categoryIllustrationUrl(category);
  return <Artwork key={`${CATEGORY_VISUAL_MODE}:${uri}`} category={category} uri={uri} {...props} />;
}

function Artwork({ category, uri, testID, wide = false, compact = false, cornerRadius = radius.lg, glass = false, reference = false, fade = true, bannerSize }: Omit<ArtworkProps, "uriOverride"> & { uri: string | null }) {
  const styles = useStyles();
  const { colors } = useTheme();
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const showImage = CATEGORY_VISUAL_MODE === "illustrated" && !!uri && !failed;
  const imageStyle = wide ? [styles.bannerImage, glass && styles.glassBanner, bannerSize ? { width: bannerSize, height: bannerSize, top: -Math.round(bannerSize * 0.08), right: 4 } : null] : [styles.image, compact && styles.compactImage, glass && styles.glassImage, reference && styles.referenceImage];
  return (
    <View testID={testID} style={[styles.fill, { borderRadius: cornerRadius }, glass && styles.glassFill, reference && styles.referenceFill]} accessibilityState={{ busy: showImage && !loaded }}>
      {glass && !reference ? (
        <View pointerEvents="none" style={[wide ? styles.glowWide : styles.glow, { backgroundColor: withAlpha(category.color, 0.16), boxShadow: `0px 0px ${wide ? 34 : 26}px ${wide ? 12 : 8}px ${withAlpha(category.color, 0.16)}` as any }]} />
      ) : null}
      {(!showImage || !loaded) ? (
        <View style={[imageStyle, styles.center]} testID={`${testID}-fallback`}>
          <CategoryIcon categoryId={category.id} color={category.color} highlightColor={colors.onGradient} size={compact ? 34 : 35} testID={`${testID}-line-icon`} />
        </View>
      ) : null}
      {showImage ? <View style={imageStyle} pointerEvents="none">
        <Image testID={`${testID}-image`} source={{ uri: uri! }} style={StyleSheet.absoluteFill}
          contentFit="contain" cachePolicy="memory-disk" recyclingKey={uri} transition={0}
          onLoad={() => setLoaded(true)} onError={() => setFailed(true)} />
      </View> : null}
      {/* Quiet framing, not desaturation: the new objects retain their full
          colour. No luminous backplates or clips from the previous art family. */}
      {reference && !wide && fade ? <LinearGradient
        colors={[withAlpha(palette.surface, 0), withAlpha(palette.surface, 0), palette.surface, palette.surface]}
        locations={[0, 0.49, 0.70, 1]} style={StyleSheet.absoluteFill}
      /> : null}
      {!wide && !glass && !reference ? <LinearGradient
        colors={[withAlpha(colors.artworkSurface, 0), withAlpha(colors.artworkSurface, 0), withAlpha(colors.artworkSurface, 0.94), colors.artworkSurface]}
        locations={[0, 0.48, 0.81, 1]} style={StyleSheet.absoluteFill}
      /> : null}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  fill: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: colors.artworkSurface, overflow: "hidden", pointerEvents: "none" },
  glassFill: { backgroundColor: "transparent" },
  referenceFill: { backgroundColor: palette.surface },
  referenceImage: { top: 1, left: "1%", width: "98%", aspectRatio: 1 },
  image: { position: "absolute", top: -2, left: "5%", width: "90%", aspectRatio: 1 },
  compactImage: { top: 0, left: "9%", width: "82%" },
  glassImage: { top: "8%", left: "17%", width: "66%" },
  bannerImage: { position: "absolute", top: -9, right: 0, width: 106, height: 106 },
  glassBanner: { top: -2, right: 12, width: 92, height: 92 },
  glow: { position: "absolute", top: "14%", left: "32%", width: "36%", aspectRatio: 1, borderRadius: 999 },
  glowWide: { position: "absolute", top: 14, right: 26, width: 56, height: 56, borderRadius: 28 },
  center: { alignItems: "center", justifyContent: "center" },
}));

// Icona 3D della categoria "nuda" (senza fondo né sfumatura), per badge e
// pillole: stessa immagine della Home; se non carica, torna l'icona a linea.
export function CategoryArtMark({ categoryId, color, size, plain = false, tight = false, aspect = 1, testID }: { categoryId: string; color: string; size: number; /** Senza piastrella scura dietro: solo l'oggetto 3D. */ plain?: boolean; /** Ritaglio stretto sull'oggetto: riempie il riquadro come le altre icone 3D. */ tight?: boolean; /** Larghezza/altezza del riquadro: >1 lascia agli oggetti larghi (es. pianeta) l'altezza piena. */ aspect?: number; testID: string }) {
  const { colors } = useTheme();
  const [failed, setFailed] = useState(false);
  if (failed) return <CategoryIcon categoryId={categoryId} color={color} highlightColor={colors.onGradient} size={Math.round(size * 0.7)} testID={`${testID}-line-icon`} />;
  return (
    <Image testID={testID} source={{ uri: categoryArtworkUrl(categoryId, ART_VERSION, plain, tight) }} style={{ width: Math.round(size * aspect), height: size, borderRadius: plain ? 0 : Math.round(size * 0.3), backgroundColor: plain ? "transparent" : colors.artworkSurface }}
      contentFit="contain" cachePolicy="memory-disk" transition={0} onError={() => setFailed(true)} />
  );
}