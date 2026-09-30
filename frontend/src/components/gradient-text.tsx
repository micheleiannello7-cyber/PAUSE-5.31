import { useId } from "react";
import { Dimensions } from "react-native";
import Svg, { Defs, LinearGradient, Stop, Text as SvgText } from "react-native-svg";
import { typography } from "@/src/theme";

// Real gradient-filled text (SVG) — works on iOS, Android and web.
// Pass pre-wrapped lines so layout is deterministic.
export function GradientText({
  lines, colors, fontSize = 32, lineHeight = 38, width,
}: {
  lines: string[];
  colors: [string, string];
  fontSize?: number;
  lineHeight?: number;
  width?: number;
}) {
  const id = `gt-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const w = width ?? Dimensions.get("window").width - 48;
  const h = lines.length * lineHeight;
  return (
    <Svg width={w} height={h}>
      <Defs>
        <LinearGradient id={id} x1="0" y1="0" x2="1" y2="0">
          <Stop offset="0" stopColor={colors[0]} />
          <Stop offset="1" stopColor={colors[1]} />
        </LinearGradient>
      </Defs>
      {lines.map((line, i) => (
        <SvgText
          key={i}
          x={0}
          y={i * lineHeight + fontSize * 0.85}
          fill={`url(#${id})`}
          fontSize={fontSize}
          fontFamily={typography.displayBold}
          fontWeight="700"
        >
          {line}
        </SvgText>
      ))}
    </Svg>
  );
}
