// PAUSE — Consumable unlock: pay €1,99 one-off to browse a single category.
// Stripe-hosted Checkout: the backend creates the session, the browser opens
// it, Stripe redirects back into this screen (?purchase_id=…) and we poll
// /purchases/{id} — the server verifies payment_status with Stripe and grants
// the category. The client never decides that something is paid.
import { useEffect, useRef, useState } from "react";
import { View, Text, StyleSheet, ScrollView, Pressable, ActivityIndicator, Platform } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter, useLocalSearchParams } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Ionicons from "@react-native-vector-icons/ionicons";

import { api, Category } from "@/src/api";
import { useUserId } from "@/src/session";
import { usePremiumFlag } from "@/src/premium";
import { makeStyles, useTheme, spacing, radius, typography } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";

const PENDING_KEY = "pause.pending_purchase";
type Notice = { kind: "success" | "cancelled" | "pending" | "error" | "verifying"; text: string } | null;

export default function UnlockCategory() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const userId = useUserId();
  const isPremium = usePremiumFlag();
  const qc = useQueryClient();
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const params = useLocalSearchParams<{ purchase_id?: string; cancelled?: string }>();

  const { data: categories, isLoading } = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => api.user(userId!),
    enabled: !!userId,
  });

  const [pendingCat, setPendingCat] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const verifying = useRef<string | null>(null);

  // Poll the purchase until Stripe confirms it (or ~40s pass).
  const verify = async (purchaseId: string, cancelled = false) => {
    if (verifying.current === purchaseId) return;
    verifying.current = purchaseId;
    if (cancelled) {
      await AsyncStorage.removeItem(PENDING_KEY);
      setNotice({ kind: "cancelled", text: t.consumable_cancelled });
      return;
    }
    setNotice({ kind: "verifying", text: t.consumable_verifying });
    for (let i = 0; i < 20; i++) {
      try {
        const p = await api.purchaseStatus(purchaseId);
        if (p.status === "paid") {
          await AsyncStorage.removeItem(PENDING_KEY);
          await qc.invalidateQueries({ queryKey: ["user", userId] });
          setNotice({ kind: "success", text: t.consumable_success });
          return;
        }
        if (p.status === "cancelled" || p.status === "error") {
          await AsyncStorage.removeItem(PENDING_KEY);
          setNotice({ kind: "cancelled", text: t.consumable_cancelled });
          return;
        }
      } catch {}
      await new Promise((r) => setTimeout(r, 2000));
    }
    setNotice({ kind: "pending", text: t.consumable_pending });
  };

  // Return from Stripe: via URL params (web full-page redirect / deep link) or
  // via the purchase we stashed before leaving (browser closed early).
  useEffect(() => {
    if (!userId) return;
    if (params.purchase_id) {
      void verify(String(params.purchase_id), params.cancelled === "1");
      return;
    }
    AsyncStorage.getItem(PENDING_KEY).then((id) => { if (id) void verify(id); });
  }, [userId, params.purchase_id, params.cancelled]);

  const onUnlock = async (categoryId: string) => {
    if (!userId) return;
    setPendingCat(categoryId);
    setNotice(null);
    try {
      const returnUrl = Linking.createURL("unlock");
      const { purchase_id, checkout_url } = await api.createPurchase(userId, categoryId, returnUrl);
      await AsyncStorage.setItem(PENDING_KEY, purchase_id);
      if (Platform.OS === "web") {
        window.location.assign(checkout_url);
        return;
      }
      const res = await WebBrowser.openAuthSessionAsync(checkout_url, returnUrl);
      if (res.type === "success" && res.url) {
        const parsed = Linking.parse(res.url);
        void verify(purchase_id, parsed.queryParams?.cancelled === "1");
      } else {
        // Browser dismissed: the payment may still have gone through.
        void verify(purchase_id);
      }
    } catch {
      setNotice({ kind: "error", text: t.consumable_error });
    } finally {
      setPendingCat(null);
    }
  };

  const unlocked = new Set(user?.unlocked_categories ?? []);
  const goBack = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/explore"));
  const noticeColor = notice?.kind === "success" ? colors.success : notice?.kind === "error" ? colors.error : colors.brand;

  return (
    <Screen style={styles.container}>
      <ScrollView
        contentContainerStyle={{ paddingTop: insets.top + spacing.sm, paddingBottom: insets.bottom + spacing.xxl }}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.topBar}>
          <HomeButton testID="unlock-home" />
          <Pressable style={styles.closeBtn} onPress={goBack} testID="unlock-close" hitSlop={10}>
            <Ionicons name="close" size={22} color={colors.onSurface} />
          </Pressable>
        </View>

        <View style={styles.hero}>
          <LinearGradient colors={colors.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.crown}>
            <Ionicons name="key" size={24} color={colors.onGradient} />
          </LinearGradient>
          <Text style={styles.headline}>{t.consumable_title}</Text>
          <Text style={styles.sub}>{t.consumable_sub}</Text>
        </View>

        {notice ? (
          <View style={[styles.notice, { borderColor: noticeColor + "66", backgroundColor: noticeColor + "14" }]} testID="unlock-notice">
            {notice.kind === "verifying" ? (
              <ActivityIndicator size="small" color={noticeColor} />
            ) : (
              <Ionicons
                name={notice.kind === "success" ? "checkmark-circle" : notice.kind === "error" ? "alert-circle" : "information-circle"}
                size={18}
                color={noticeColor}
              />
            )}
            <Text style={[styles.noticeText, { color: noticeColor }]}>{notice.text}</Text>
          </View>
        ) : null}

        {isLoading || !categories ? (
          <ActivityIndicator color={colors.brand} style={{ marginTop: spacing.xxl }} />
        ) : (
          <View style={styles.list}>
            {categories.map((c) => (
              <CategoryRow
                key={c.id}
                cat={c}
                unlocked={isPremium || unlocked.has(c.id)}
                premium={isPremium}
                pending={pendingCat === c.id}
                onUnlock={() => onUnlock(c.id)}
                onOpen={() => router.push({ pathname: "/browse", params: { category_id: c.id } })}
              />
            ))}
          </View>
        )}

        <Text style={styles.note}>{t.consumable_preview_note}</Text>
        <Pressable onPress={() => router.push("/premium")} testID="unlock-goto-premium" style={styles.hintRow}>
          <Ionicons name="diamond-outline" size={14} color={colors.brand} />
          <Text style={styles.hintText}>{t.consumable_hint}</Text>
        </Pressable>
      </ScrollView>
    </Screen>
  );
}

function CategoryRow({
  cat, unlocked, premium, pending, onUnlock, onOpen,
}: {
  cat: Category;
  unlocked: boolean;
  premium: boolean;
  pending: boolean;
  onUnlock: () => void;
  onOpen: () => void;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { t } = useI18n();
  return (
    <View style={[styles.row, { borderColor: unlocked ? cat.color + "66" : colors.border }]} testID={`unlock-row-${cat.id}`}>
      <View style={[styles.orb, { backgroundColor: cat.color + "1A" }]}>
        <Ionicons name={cat.icon as any} size={20} color={cat.color} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.name} numberOfLines={1}>{cat.name}</Text>
        <Text style={styles.meta}>
          {cat.story_count} {t.stories_n} · {unlocked ? t.consumable_unlocked : t.consumable_price}
        </Text>
      </View>
      {unlocked ? (
        <Pressable
          onPress={onOpen}
          testID={`unlock-open-${cat.id}`}
          style={[styles.cta, { backgroundColor: cat.color + "22", borderColor: cat.color + "66" }]}
        >
          <Ionicons name={premium ? "diamond" : "checkmark-circle"} size={13} color={cat.color} />
          <Text style={[styles.ctaText, { color: cat.color }]}>{t.consumable_open}</Text>
        </Pressable>
      ) : (
        <Pressable
          onPress={onUnlock}
          disabled={pending}
          testID={`unlock-buy-${cat.id}`}
          style={[styles.cta, styles.ctaBrand, { opacity: pending ? 0.5 : 1 }]}
        >
          {pending ? (
            <ActivityIndicator size="small" color={colors.onBrand} />
          ) : (
            <Text style={[styles.ctaText, { color: colors.onBrand }]}>{t.consumable_unlock}</Text>
          )}
        </Pressable>
      )}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: colors.surface },
  topBar: { paddingHorizontal: spacing.xl, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  closeBtn: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
  },
  hero: { alignItems: "center", paddingHorizontal: spacing.xl, paddingTop: spacing.md, gap: spacing.md },
  crown: { width: 60, height: 60, borderRadius: 20, alignItems: "center", justifyContent: "center" },
  headline: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 22, textAlign: "center", lineHeight: 28 },
  sub: { color: colors.muted, fontFamily: typography.body, fontSize: 13, textAlign: "center", lineHeight: 20 },
  list: { paddingHorizontal: spacing.xl, marginTop: spacing.xl, gap: spacing.md },
  notice: {
    marginHorizontal: spacing.xl, marginTop: spacing.lg,
    flexDirection: "row", alignItems: "center", gap: spacing.sm,
    padding: spacing.md, borderRadius: radius.lg, borderWidth: 1,
  },
  noticeText: { flex: 1, fontFamily: typography.bodyBold, fontSize: 13, lineHeight: 18 },
  row: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    padding: spacing.md, borderRadius: radius.lg,
    backgroundColor: colors.surfaceSecondary, borderWidth: 1,
  },
  orb: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center" },
  name: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 15 },
  meta: { color: colors.muted, fontFamily: typography.body, fontSize: 11, marginTop: 2 },
  cta: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 12, height: 34, borderRadius: radius.pill, borderWidth: 1,
    minWidth: 88, justifyContent: "center",
  },
  ctaBrand: { backgroundColor: colors.brand, borderColor: colors.brand },
  ctaText: { fontFamily: typography.bodyBold, fontSize: 12 },
  note: {
    color: colors.muted, fontFamily: typography.body, fontSize: 11,
    textAlign: "center", marginTop: spacing.xl, paddingHorizontal: spacing.xxl, lineHeight: 16,
  },
  hintRow: {
    marginTop: spacing.md, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 5,
    paddingHorizontal: spacing.xl,
  },
  hintText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 0.5 },
}));
