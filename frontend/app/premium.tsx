import { useState } from "react";
import { View, Text, Pressable, ScrollView, StyleSheet } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";

import { api, heroUrl } from "@/src/api";
import { spacing, radius, typography, useTheme, makeStyles, withAlpha } from "@/src/theme";
import { GradientButton } from "@/src/components/gradient-button";
import { HomeButton } from "@/src/components/home-button";
import { Screen } from "@/src/components/screen";
import { PLANS, PlanId, YEARLY_PER_MONTH, usePremium } from "@/src/premium";
import { useI18n } from "@/src/i18n";

// Paywall v3 — hero con le tre copertine a ventaglio (invariato), un claim
// unico "€2,49/mese", selettore dei tre piani in una riga (annuale in
// evidenza, con prova gratuita), e una tabella Gratis / Premium che elenca
// SOLO ciò che Premium sblocca davvero nell'app oggi (crediti e ricarica,
// mini lezioni, cronologia, audio, catalogo, statistiche, preferiti, accesso
// anticipato, colori accento). CTA fissa in basso che dice cosa succede oggi (niente).
export default function Premium() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t } = useI18n();
  const { colors } = useTheme();
  const styles = useStyles();
  const { isPremium, activate, cancel, isPending } = usePremium();
  const [selected, setSelected] = useState<PlanId>("yearly");
  const plan = PLANS.find((p) => p.id === selected)!;
  const yearly = PLANS.find((p) => p.id === "yearly")!;

  // Tre copertine reali per il ventaglio in alto (prima le più "cinematografiche").
  const { data: stories } = useQuery({ queryKey: ["paywall-covers"], queryFn: () => api.stories({ limit: 60 }) });
  const withCover = (stories ?? []).filter((s) => s.hero_image_generated);
  const preferred = ["aurora-borealis", "black-holes-basics", "how-stars-die", "moon-tides", "mars-red", "how-many-galaxies"];
  const covers = [
    ...preferred.map((id) => withCover.find((s) => s.id === id)).filter(Boolean),
    ...withCover.filter((s) => !preferred.includes(s.id)),
  ].slice(0, 3) as typeof withCover;

  const planLabel = (id: PlanId) => (id === "monthly" ? t.plan_month : id === "yearly" ? t.plan_year : t.plan_lifetime);
  const planPeriod = (id: PlanId) => (id === "monthly" ? t.per_month : id === "yearly" ? t.per_year : t.per_once);

  // Sotto al selettore: cosa comporta il piano scelto.
  const planHint = plan.trialDays
    ? t.trial_note.replace("{d}", String(plan.trialDays))
    : plan.id === "lifetime" ? t.pw_lifetime_hint : t.pw_month_hint;
  const ctaLabel = plan.trialDays ? t.pw_cta_trial : t.pw_cta_plan.replace("{plan}", planLabel(plan.id));
  const ctaNote = plan.trialDays
    ? `${t.pw_no_charge} · ${t.pw_then.replace("{price}", plan.price).replace("{period}", planPeriod(plan.id))}`
    : plan.id === "lifetime" ? t.pw_lifetime_hint : t.pw_no_charge;

  // Confronto Gratis / Premium: solo funzioni presenti nell'app (vedi backend
  // FREE_/PREMIUM_CAPACITY, HISTORY_FREE_DAYS, FREE_SAVED_LIMIT, EARLY_ACCESS_DAYS
  // e i gate `isPremium` di audio, browse, playlist, stats, accento).
  type Row = { icon: string; title: string; sub?: string; free: string | false; premium: string | true };
  const rows: Row[] = [
    { icon: "layers-outline", title: t.pw_r_sessions, sub: t.pw_r_sessions_sub, free: "4", premium: "5" },
    { icon: "flash-outline", title: t.pw_r_recharge, sub: t.pw_r_recharge_sub, free: t.pw_r_recharge_free, premium: t.pw_r_recharge_premium },
    { icon: "school-outline", title: t.pw_r_lessons, sub: t.pw_r_lessons_sub, free: false, premium: true },
    { icon: "time-outline", title: t.pw_r_history, sub: t.pw_r_history_sub, free: t.pw_r_history_free, premium: t.pw_r_history_premium },
    { icon: "headset-outline", title: t.pw_r_audio, sub: t.pw_r_audio_sub, free: false, premium: true },
    { icon: "albums-outline", title: t.pw_r_choose, sub: t.pw_r_choose_sub, free: false, premium: true },
    { icon: "stats-chart-outline", title: t.pw_r_stats, sub: t.pw_r_stats_sub, free: false, premium: true },
    { icon: "heart-outline", title: t.pw_r_saved, free: "20", premium: t.pw_unlimited },
    { icon: "sparkles-outline", title: t.pw_r_early, free: t.pw_r_early_free, premium: t.pw_r_early_premium },
    { icon: "color-palette-outline", title: t.pw_r_accent, free: "1", premium: "5" },
  ];

  const goBack = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/discover"));
  const onActivate = async () => {
    await activate();
    goBack();
  };

  return (
    <Screen style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: spacing.xl }}>
        {/* ---- Hero: ventaglio di copertine su sfondo sfocato (invariato) ---- */}
        <View style={[styles.hero, { paddingTop: insets.top + 48 }]} testID="paywall-hero">
          {covers[0] ? (
            <Image source={{ uri: heroUrl(covers[0], "thumb") }} style={StyleSheet.absoluteFill} contentFit="cover" blurRadius={30} cachePolicy="memory-disk" />
          ) : null}
          <LinearGradient
            colors={["rgba(5,7,12,0.35)", "rgba(5,7,12,0.55)", colors.surface]}
            locations={[0, 0.6, 1]}
            style={StyleSheet.absoluteFill}
          />
          <View style={styles.fan}>
            {covers.map((s, i) => (
              <View
                key={s.id}
                style={[
                  styles.fanCard,
                  i === 0 && { transform: [{ rotate: "-9deg" }, { translateX: -26 }, { translateY: 10 }] },
                  i === 1 && { zIndex: 2, transform: [{ scale: 1.08 }] },
                  i === 2 && { transform: [{ rotate: "9deg" }, { translateX: 26 }, { translateY: 10 }] },
                ]}
              >
                <Image source={{ uri: heroUrl(s, "thumb") }} style={StyleSheet.absoluteFill} contentFit="cover" transition={300} cachePolicy="memory-disk" />
                <LinearGradient colors={["transparent", "rgba(5,7,12,0.75)"]} style={StyleSheet.absoluteFill} />
                {i === 1 ? (
                  <View style={styles.fanPlay}>
                    <Ionicons name="headset" size={16} color="#FFFFFF" />
                  </View>
                ) : null}
              </View>
            ))}
          </View>
        </View>

        <View style={styles.body}>
          {/* ---- Claim: titolo + prezzo mensile equivalente ---- */}
          <View style={styles.pill} testID="paywall-trial-pill">
            <Ionicons name="sparkles" size={12} color={colors.brand} />
            <Text style={styles.pillText}>{t.pw_trial_pill.toUpperCase()}</Text>
          </View>
          <Text style={styles.title} testID="paywall-title">{t.pw_title}</Text>
          <View style={styles.claimRow} testID="paywall-claim">
            <Text style={styles.claimPrice}>{YEARLY_PER_MONTH}</Text>
            <Text style={styles.claimUnit}>{t.pw_claim_unit}</Text>
          </View>
          <Text style={styles.claimNote} testID="paywall-claim-note">
            {t.pw_claim_note.replace("{price}", yearly.price).replace("{period}", t.per_year)}
          </Text>

          {/* ---- Selettore piani: tre in una riga, annuale al centro in evidenza ---- */}
          <Text style={styles.sectionLabel}>{t.pw_choose_plan}</Text>
          <View style={styles.plans}>
            {(["monthly", "yearly", "lifetime"] as PlanId[]).map((id) => {
              const p = PLANS.find((x) => x.id === id)!;
              const active = selected === id;
              const tag = id === "yearly" ? t.badge_save : id === "lifetime" ? t.badge_best : undefined;
              return (
                <Pressable key={id} onPress={() => setSelected(id)} testID={`plan-${id}`} accessibilityRole="radio" accessibilityState={{ selected: active }} style={styles.planWrap}>
                  <LinearGradient
                    colors={active ? colors.gradient : [colors.border, colors.border]}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                    style={styles.planBorder}
                  >
                    <View style={[styles.plan, active && styles.planActive]}>
                      {tag ? (
                        <View style={[styles.planTag, id === "yearly" ? styles.planTagBrand : styles.planTagSuccess]}>
                          <Text style={[styles.planTagText, id === "yearly" ? styles.planTagTextBrand : styles.planTagTextSuccess]} numberOfLines={1}>{tag.toUpperCase()}</Text>
                        </View>
                      ) : <View style={styles.planTagSpacer} />}
                      <Text style={styles.planName} numberOfLines={1}>{planLabel(id)}</Text>
                      <Text style={styles.planPrice} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.8}>{p.price}</Text>
                      <Text style={styles.planPeriod} numberOfLines={1}>{planPeriod(id)}</Text>
                      <Radio active={active} />
                    </View>
                  </LinearGradient>
                </Pressable>
              );
            })}
          </View>
          <View style={styles.planHint} testID="plan-hint">
            <Ionicons name={plan.trialDays ? "gift-outline" : plan.id === "lifetime" ? "infinite-outline" : "refresh-outline"} size={14} color={colors.brand} />
            <Text style={styles.planHintText}>{planHint}</Text>
          </View>

          {/* ---- Confronto Gratis / Premium ---- */}
          <Text style={styles.compareTitle} testID="paywall-compare-title">{t.pw_compare_title}</Text>
          <View style={styles.table} testID="paywall-compare">
            <View style={styles.tableHead}>
              <View style={{ flex: 1 }} />
              <Text style={[styles.colLabel, styles.colFree]}>{t.pw_free_label}</Text>
              <View style={[styles.colPremiumHead]}>
                <Ionicons name="diamond" size={10} color={colors.onBrand} />
                <Text style={styles.colPremiumText}>{t.pw_premium_label}</Text>
              </View>
            </View>
            {rows.map((r, i) => (
              <View key={r.title} style={[styles.row, i === rows.length - 1 && styles.rowLast]} testID={`compare-${r.icon}`}>
                <View style={styles.rowIcon}>
                  <Ionicons name={r.icon as any} size={16} color={colors.onSurfaceSecondary} />
                </View>
                <View style={styles.rowText}>
                  <Text style={styles.rowTitle}>{r.title}</Text>
                  {r.sub ? <Text style={styles.rowSub}>{r.sub}</Text> : null}
                </View>
                <View style={styles.cellFree}>
                  {r.free === false
                    ? <Ionicons name="remove" size={16} color={colors.muted} />
                    : <Text style={styles.cellFreeText} numberOfLines={2}>{r.free}</Text>}
                </View>
                <View style={styles.cellPremium}>
                  {r.premium === true
                    ? <Ionicons name="checkmark-circle" size={18} color={colors.brand} />
                    : <Text style={styles.cellPremiumText} numberOfLines={2}>{r.premium}</Text>}
                </View>
              </View>
            ))}
            {/* Colonna Premium leggermente tinta, sotto alle celle. */}
            <View pointerEvents="none" style={styles.premiumColumnTint} />
          </View>

          {/* ---- Fiducia ---- */}
          <View style={styles.trust}>
            <Trust icon="shield-checkmark-outline" label={t.pw_trust_store} />
            <Trust icon="close-circle-outline" label={t.pw_trust_cancel} />
            <Trust icon="phone-portrait-outline" label={t.pw_trust_family} />
          </View>

          {isPremium ? (
            <Pressable style={styles.cancel} onPress={() => cancel()} testID="premium-cancel">
              <Text style={styles.cancelText}>{t.premium_cancel_preview}</Text>
            </Pressable>
          ) : null}
        </View>
      </ScrollView>

      {/* ---- Barra superiore sopra l'hero ---- */}
      <View style={[styles.topBar, { top: insets.top + spacing.xs }]}>
        <HomeButton testID="premium-home" />
        <Pressable style={styles.closeBtn} onPress={goBack} testID="premium-close" hitSlop={10}>
          <Ionicons name="close" size={20} color="#FFFFFF" />
        </Pressable>
      </View>

      {/* ---- CTA fissa ---- */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + spacing.sm }]}>
        {isPremium ? (
          <View style={styles.activeChip} testID="premium-active-chip">
            <Ionicons name="checkmark-done" size={18} color={colors.success} />
            <Text style={styles.activeChipText}>{t.premium_active}</Text>
          </View>
        ) : (
          <GradientButton label={ctaLabel} icon="arrow-forward" onPress={onActivate} loading={isPending} testID="premium-activate" />
        )}
        <Text style={styles.ctaNote} testID="paywall-cta-note">{ctaNote}</Text>
        <Pressable onPress={() => {}} testID="premium-restore" hitSlop={8}>
          <Text style={styles.restore}>{t.premium_restore}</Text>
        </Pressable>
      </View>
    </Screen>
  );
}

function Radio({ active }: { active: boolean }) {
  const styles = useStyles();
  return <View style={[styles.radio, active && styles.radioActive]}>{active ? <View style={styles.radioDot} /> : null}</View>;
}

function Trust({ icon, label }: { icon: string; label: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <View style={styles.trustItem}>
      <Ionicons name={icon as any} size={16} color={colors.muted} />
      <Text style={styles.trustText}>{label}</Text>
    </View>
  );
}

const FAN_W = 108;
const FAN_H = 144;
const COL_FREE_W = 62;
const COL_PREMIUM_W = 82;

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: colors.surface },
  topBar: {
    position: "absolute", left: spacing.xl, right: spacing.xl,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  closeBtn: {
    width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(5,7,12,0.45)", borderWidth: 1, borderColor: "rgba(255,255,255,0.18)",
  },
  // Hero (invariato)
  hero: { height: 300, overflow: "hidden", alignItems: "center", justifyContent: "flex-end", paddingBottom: spacing.lg },
  fan: { flexDirection: "row", alignItems: "center", justifyContent: "center", height: FAN_H + 24 },
  fanCard: {
    width: FAN_W, height: FAN_H, borderRadius: 18, overflow: "hidden", marginHorizontal: -22,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.22)",
    backgroundColor: colors.surfaceSecondary,
    boxShadow: "0px 14px 30px rgba(0,0,0,0.45)",
  },
  fanPlay: {
    position: "absolute", right: 10, bottom: 10, width: 30, height: 30, borderRadius: 15,
    backgroundColor: "rgba(255,255,255,0.22)", alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.35)",
  },
  body: { paddingHorizontal: spacing.xl, marginTop: -spacing.sm },
  // Claim
  pill: {
    alignSelf: "flex-start", flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: radius.pill,
    backgroundColor: withAlpha(colors.brand, 0.1), borderWidth: 1, borderColor: withAlpha(colors.brand, 0.27),
  },
  pillText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1.6 },
  title: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 30, lineHeight: 36, marginTop: spacing.md },
  claimRow: { flexDirection: "row", alignItems: "flex-end", gap: 4, marginTop: spacing.md },
  claimPrice: { color: colors.brand, fontFamily: typography.displayBold, fontSize: 44, lineHeight: 48, letterSpacing: -1 },
  claimUnit: { color: colors.onSurfaceSecondary, fontFamily: typography.bodyBold, fontSize: 18, lineHeight: 34 },
  claimNote: { color: colors.muted, fontFamily: typography.body, fontSize: 13, lineHeight: 18, marginTop: 2 },
  // Piani
  sectionLabel: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 10.5, letterSpacing: 1.6, marginTop: spacing.xl, marginBottom: spacing.sm },
  plans: { flexDirection: "row", gap: spacing.sm },
  planWrap: { flex: 1 },
  planBorder: { borderRadius: radius.lg + 2, padding: 1.5, flex: 1 },
  plan: {
    flex: 1, backgroundColor: colors.surfaceSecondary, borderRadius: radius.lg,
    paddingHorizontal: spacing.sm, paddingTop: spacing.sm, paddingBottom: spacing.md, alignItems: "center", gap: 2,
  },
  planActive: { backgroundColor: colors.surfaceTertiary },
  planTag: { paddingHorizontal: 7, height: 18, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", marginBottom: spacing.xs, maxWidth: "100%" },
  planTagSpacer: { height: 18, marginBottom: spacing.xs },
  planTagBrand: { backgroundColor: colors.brand },
  planTagSuccess: { backgroundColor: withAlpha(colors.success, 0.16) },
  planTagText: { fontFamily: typography.bodyBold, fontSize: 8.5, letterSpacing: 0.8 },
  planTagTextBrand: { color: colors.onBrand },
  planTagTextSuccess: { color: colors.success },
  planName: { color: colors.onSurfaceSecondary, fontFamily: typography.bodyMedium, fontSize: 12 },
  planPrice: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 19, lineHeight: 24, marginTop: 2 },
  planPeriod: { color: colors.muted, fontFamily: typography.body, fontSize: 11, marginBottom: spacing.sm },
  planHint: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, marginTop: spacing.md },
  planHintText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 12.5 },
  radio: {
    width: 18, height: 18, borderRadius: 9, borderWidth: 2, borderColor: colors.borderStrong,
    alignItems: "center", justifyContent: "center",
  },
  radioActive: { borderColor: colors.brand },
  radioDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.brand },
  // Tabella confronto
  compareTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 18, marginTop: spacing.xl + spacing.sm, marginBottom: spacing.md },
  table: {
    borderRadius: radius.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border,
    overflow: "hidden", position: "relative",
  },
  tableHead: { flexDirection: "row", alignItems: "center", paddingHorizontal: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.sm, zIndex: 1 },
  colLabel: { fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 0.8, textAlign: "center" },
  colFree: { width: COL_FREE_W, color: colors.muted },
  colPremiumHead: {
    width: COL_PREMIUM_W, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4,
    height: 22, borderRadius: radius.pill, backgroundColor: colors.brand, marginLeft: spacing.xs,
  },
  colPremiumText: { color: colors.onBrand, fontFamily: typography.bodyBold, fontSize: 10.5, letterSpacing: 0.8 },
  row: {
    flexDirection: "row", alignItems: "center", paddingHorizontal: spacing.md, paddingVertical: spacing.sm + 2,
    borderTopWidth: 1, borderTopColor: colors.divider, zIndex: 1,
  },
  rowLast: { paddingBottom: spacing.md },
  rowIcon: { width: 24, alignItems: "center", marginRight: spacing.sm },
  rowText: { flex: 1, minWidth: 0, paddingRight: spacing.xs },
  rowTitle: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 13.5, lineHeight: 18 },
  rowSub: { color: colors.muted, fontFamily: typography.body, fontSize: 11, lineHeight: 15, marginTop: 1 },
  cellFree: { width: COL_FREE_W, alignItems: "center", justifyContent: "center" },
  cellFreeText: { color: colors.muted, fontFamily: typography.bodyMedium, fontSize: 12, textAlign: "center", lineHeight: 15 },
  cellPremium: { width: COL_PREMIUM_W, marginLeft: spacing.xs, alignItems: "center", justifyContent: "center" },
  cellPremiumText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 12, textAlign: "center", lineHeight: 15 },
  premiumColumnTint: {
    position: "absolute", top: 0, bottom: 0, right: spacing.md, width: COL_PREMIUM_W,
    backgroundColor: withAlpha(colors.brand, 0.06), borderLeftWidth: 1, borderRightWidth: 1, borderColor: withAlpha(colors.brand, 0.12),
  },
  // Fiducia + resto
  trust: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm, marginTop: spacing.xl },
  trustItem: { flex: 1, alignItems: "center", gap: 4 },
  trustText: { color: colors.muted, fontFamily: typography.bodyMedium, fontSize: 10.5, textAlign: "center", lineHeight: 14 },
  cancel: { alignSelf: "center", padding: spacing.sm, marginTop: spacing.md },
  cancelText: { color: colors.muted, fontFamily: typography.bodyMedium, fontSize: 13 },
  footer: {
    paddingHorizontal: spacing.xl, paddingTop: spacing.md, alignItems: "center", gap: spacing.xs,
    backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: colors.divider,
  },
  ctaNote: { color: colors.muted, fontFamily: typography.body, fontSize: 11.5, lineHeight: 16, textAlign: "center" },
  restore: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 13, marginTop: 2 },
  activeChip: {
    flexDirection: "row", alignItems: "center", gap: spacing.sm, alignSelf: "stretch", justifyContent: "center",
    height: 52, borderRadius: radius.pill,
    backgroundColor: withAlpha(colors.success, 0.1), borderWidth: 1, borderColor: withAlpha(colors.success, 0.33),
  },
  activeChipText: { color: colors.success, fontFamily: typography.bodyBold, fontSize: 15 },
}));
