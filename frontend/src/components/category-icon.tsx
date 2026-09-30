// Original PAUSE icon family. Hand-drawn 32-unit geometry, not icon-font glyphs.
// One consistent optical weight, faceted silhouettes and a restrained duotone fill.
import { memo } from "react";
import Svg, { Path } from "react-native-svg";
import { useTheme } from "@/src/theme";

type Drawing = { outline: string; fill: string; detail?: string; highlight?: string };

export const CATEGORY_DRAWINGS: Record<string, Drawing> = {
  scienza: {
    outline: "M12 5V13L5 26L7 28H25L27 26L20 13V5M10 4H22",
    fill: "M8 21H24L27 26L25 28H7L5 26Z",
    detail: "M9 21H23M15 17H18",
    highlight: "M12 4H20M15 24H18",
  },
  spazio: {
    outline: "M16 3L22 11V23H10V11ZM10 16L5 21V27L10 23M22 16L27 21V27L22 23",
    fill: "M16 3L22 11V23H16ZM10 16L5 21V27L10 23ZM22 16L27 21V27L22 23Z",
    detail: "M13 26L16 30L19 26",
    highlight: "M16 9L19 12L16 15L13 12Z",
  },
  tecnologia: {
    outline: "M10 8H22L24 10V22L22 24H10L8 22V10ZM11 3V8M21 3V8M11 24V29M21 24V29M3 11H8M3 21H8M24 11H29M24 21H29",
    fill: "M10 8H22L24 10V22L22 24H10L8 22V10Z",
    detail: "M16 3V8M16 24V29M3 16H8M24 16H29",
    highlight: "M13 13H19V19H13Z",
  },
  natura: {
    outline: "M8 25L6 16L12 7L27 4L25 19L17 26ZM5 29L23 11",
    fill: "M8 25L27 4L25 19L17 26Z",
    detail: "M13 21L12 14M18 16L24 16",
    highlight: "M9 25L20 14",
  },
  animali: {
    outline: "M5 4L15 10H17L27 4L25 22L16 29L7 22ZM7 14L16 24L25 14",
    fill: "M5 4L15 10L7 14ZM27 4L17 10L25 14ZM7 14L16 24L7 22ZM25 14L16 24L25 22Z",
    detail: "M10 16L12 17M22 16L20 17",
    highlight: "M14 24H18L16 26Z",
  },
  storia: {
    outline: "M3 11L16 4L29 11ZM7 15V24M13 15V24M19 15V24M25 15V24M5 28H27",
    fill: "M3 11L16 4L29 11ZM7 15H11V24H7ZM19 15H23V24H19Z",
    detail: "M4 25H28",
    highlight: "M8 11H24",
  },
  psicologia: {
    outline: "M16 6L12 3L8 6V10L4 13V22L8 26H12L16 29L20 26H24L28 22V13L24 10V6L20 3ZM16 6V29",
    fill: "M16 6L20 3L24 6V10L28 13V22L24 26H20L16 29Z",
    detail: "M8 10V15H12V21H8M24 10V15H20V21H24",
    highlight: "M12 8V11M20 8V11",
  },
  "corpo-umano": {
    outline: "M16 9L10 4L5 5L2 10V17L16 29L30 17V10L27 5L22 4Z",
    fill: "M16 9L22 4L27 5L30 10V17L16 29Z",
    highlight: "M5 16H10L13 11L17 22L20 16H27",
  },
  cultura: {
    outline: "M16 9L5 5V24L16 28L27 24V5ZM16 9V28",
    fill: "M16 9L27 5V24L16 28Z",
    detail: "M9 12L12 13M9 17L12 18M20 13L23 12M20 18L23 17",
    highlight: "M5 24L16 28L27 24",
  },
  curiosita: {
    outline: "M12 4H20L26 10V18L20 24H12L6 18V10ZM12 27H20M14 30H18",
    fill: "M16 4H20L26 10V18L20 24H16Z",
    detail: "M2 6L4 8M28 8L30 6M16 0V1",
    highlight: "M12 13L16 17L20 13M16 17V24",
  },
  economia: {
    outline: "M5 21H10V28H5ZM13 16H18V28H13ZM21 11H26V28H21Z",
    fill: "M5 21H10V28H5ZM13 16H18V28H13ZM21 11H26V28H21Z",
    highlight: "M5 14L13 7L18 9L27 3M22 3H27V8",
  },
  arte: {
    outline: "M5 27L8 13L25 4L28 7L19 24ZM5 27L16 16M22 6L26 10",
    fill: "M5 27L19 24L28 7L25 4L17 14Z",
    highlight: "M18 11L21 14L18 17L15 14Z",
    detail: "M10 29H25",
  },
  geografia: {
    outline: "M3 8L11 4L21 8L29 4V25L21 29L11 25L3 29ZM11 4V25M21 8V29",
    fill: "M3 8L11 4V25L3 29ZM21 8L29 4V25L21 29Z",
    highlight: "M16 10L20 22L16 19L12 22Z",
  },
};

const FALLBACK: Drawing = {
  outline: "M4 4H13V13H4ZM19 4H28V13H19ZM4 19H13V28H4ZM19 19H28V28H19Z",
  fill: "M4 4H13V13H4ZM19 19H28V28H19Z",
};

export const CategoryIcon = memo(function CategoryIcon({ categoryId, color, size = 40, active = false, testID, highlightColor }: {
  categoryId: string; color: string; size?: number; active?: boolean; testID: string; highlightColor?: string;
}) {
  const { colors } = useTheme();
  const drawing = CATEGORY_DRAWINGS[categoryId] ?? FALLBACK;
  return (
    <Svg width={size} height={size} viewBox="0 0 32 32" testID={testID} aria-hidden>
      <Path d={drawing.fill} fill={color} opacity={active ? 0.3 : 0.16} />
      <Path d={drawing.outline} fill="none" stroke={color} strokeWidth={1.65} strokeLinecap="square" strokeLinejoin="bevel" />
      {drawing.detail ? <Path d={drawing.detail} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="square" strokeLinejoin="bevel" /> : null}
      {drawing.highlight ? <Path d={drawing.highlight} fill="none" stroke={highlightColor ?? colors.onSurface} strokeWidth={1.65} strokeLinecap="square" strokeLinejoin="bevel" /> : null}
    </Svg>
  );
});

export function DirectionIcon({ direction, color }: { direction: "prev" | "next"; color: string }) {
  return (
    <Svg width={26} height={26} viewBox="0 0 32 32" testID={`discover-${direction}-icon`} aria-hidden>
      <Path d={direction === "prev" ? "M25 16H7M14 9L7 16L14 23" : "M7 16H25M18 9L25 16L18 23"}
        fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="square" strokeLinejoin="miter" />
    </Svg>
  );
}