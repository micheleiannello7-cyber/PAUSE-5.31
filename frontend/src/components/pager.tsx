// PAUSE — horizontal pager + dots. Used wherever we replace a long vertical
// scroll with discrete, swipeable pages (deep-dive reading, paywall benefits,
// home deck position).
import { forwardRef, useImperativeHandle, useRef, useState, ReactNode } from "react";
import {
  View, Text, ScrollView, Pressable, StyleSheet, LayoutChangeEvent,
  NativeSyntheticEvent, NativeScrollEvent, StyleProp, ViewStyle,
} from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import { makeStyles, useTheme, spacing, typography } from "@/src/theme";

export type PagerHandle = { goTo: (index: number, animated?: boolean) => void };

type PagerProps = {
  pages: ReactNode[];
  page: number;
  onPageChange: (index: number) => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
};

// Controlled horizontal pager: one full-width page per child. The page index
// is derived from the scroll offset so dots update live while swiping.
export const Pager = forwardRef<PagerHandle, PagerProps>(function Pager(
  { pages, page, onPageChange, style, testID }, ref,
) {
  const scrollRef = useRef<ScrollView>(null);
  const [width, setWidth] = useState(0);
  const lastReported = useRef(page);
  const pendingInitial = useRef(page);

  useImperativeHandle(ref, () => ({
    goTo: (index, animated = true) => {
      if (!width) { pendingInitial.current = index; return; }
      scrollRef.current?.scrollTo({ x: index * width, animated });
    },
  }), [width]);

  const onLayout = (e: LayoutChangeEvent) => {
    const w = Math.round(e.nativeEvent.layout.width);
    if (w && w !== width) {
      setWidth(w);
      // Restore the requested page once we know the page width (resume).
      const idx = pendingInitial.current;
      if (idx > 0) requestAnimationFrame(() => scrollRef.current?.scrollTo({ x: idx * w, animated: false }));
    }
  };

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    if (!width) return;
    const idx = Math.max(0, Math.min(pages.length - 1, Math.round(e.nativeEvent.contentOffset.x / width)));
    if (idx !== lastReported.current) {
      lastReported.current = idx;
      onPageChange(idx);
    }
  };

  return (
    <View style={[styles.fill, style]} onLayout={onLayout} testID={testID}>
      {width > 0 ? (
        <ScrollView
          ref={scrollRef}
          horizontal
          pagingEnabled
          bounces={false}
          showsHorizontalScrollIndicator={false}
          onScroll={onScroll}
          scrollEventThrottle={16}
          style={styles.fill}
          contentContainerStyle={{ width: width * pages.length, flexGrow: 1 }}
        >
          {pages.map((p, i) => (
            <View key={i} style={{ width, height: "100%" }}>
              {p}
            </View>
          ))}
        </ScrollView>
      ) : null}
    </View>
  );
});

// Row of dots; the active one stretches into a short pill in the accent colour.
export function PagerDots({
  count, index, color, style, testID = "pager-dots", onSelect,
}: { count: number; index: number; color?: string; style?: StyleProp<ViewStyle>; testID?: string; onSelect?: (index: number) => void }) {
  const s = useDotStyles();
  const { colors } = useTheme();
  const active = color ?? colors.brand;
  return (
    <View style={[s.row, style]} testID={testID} accessibilityLabel={`${index + 1} / ${count}`}>
      {Array.from({ length: count }, (_, i) => (
        <Pressable
          key={i}
          onPress={onSelect ? () => onSelect(i) : undefined}
          disabled={!onSelect || i === index}
          hitSlop={10}
          accessibilityRole={onSelect ? "button" : undefined}
          style={[s.dot, i === index && { width: 20, backgroundColor: active }]}
          testID={i === index ? "pager-dot-active" : `pager-dot-${i}`}
        />
      ))}
    </View>
  );
}

// Footer used by paged screens: prev / dots / next, thumb-reachable. With
// `onEndNext` the forward arrow stays active on the last page (e.g. "next
// story") instead of greying out.
export function PagerNav({
  count, index, onPrev, onNext, onEndNext, color, label, testID = "pager-nav",
}: { count: number; index: number; onPrev: () => void; onNext: () => void; onEndNext?: () => void; color?: string; label?: string; testID?: string }) {
  const s = useDotStyles();
  const { colors } = useTheme();
  const canPrev = index > 0;
  const atEnd = index >= count - 1;
  const canNext = !atEnd || !!onEndNext;
  return (
    <View style={s.navRow} testID={testID}>
      <Pressable
        onPress={onPrev}
        disabled={!canPrev}
        hitSlop={8}
        testID="pager-prev"
        style={({ pressed }) => [s.navBtn, !canPrev && s.navBtnDisabled, pressed && canPrev && s.navBtnPressed]}
      >
        <Ionicons name="chevron-back" size={20} color={canPrev ? colors.onSurface : colors.muted} />
      </Pressable>
      <View style={s.navCenter}>
        <PagerDots count={count} index={index} color={color} />
        {label ? <Text style={s.navLabel} testID="deep-dive-page-label">{label}</Text> : null}
      </View>
      <Pressable
        onPress={atEnd && onEndNext ? onEndNext : onNext}
        disabled={!canNext}
        hitSlop={8}
        testID="pager-next"
        style={({ pressed }) => [s.navBtn, !canNext && s.navBtnDisabled, pressed && canNext && s.navBtnPressed]}
      >
        <Ionicons name={atEnd && onEndNext ? "arrow-forward" : "chevron-forward"} size={20} color={canNext ? colors.onSurface : colors.muted} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({ fill: { flex: 1 } });

const useDotStyles = makeStyles((colors) => ({
  row: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6 },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.borderStrong },
  navRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: spacing.xl,
  },
  navCenter: { flex: 1, alignItems: "center", justifyContent: "center", gap: 5 },
  navLabel: {
    color: colors.muted, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1.5,
    textAlign: "center", textTransform: "uppercase",
  },
  navBtn: {
    width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.borderStrong,
  },
  navBtnDisabled: { opacity: 0.35, borderColor: colors.border },
  navBtnPressed: { backgroundColor: colors.surfaceTertiary, borderColor: colors.brand },
}));
