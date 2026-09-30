import { View, Text, ScrollView, Pressable, Switch, Alert, StyleSheet } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LinearGradient } from "expo-linear-gradient";
import Ionicons from "@react-native-vector-icons/ionicons";
import MaterialDesignIcons from "@react-native-vector-icons/material-design-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";

import { api } from "@/src/api";
import * as Haptics from "@/src/haptics";
import { useHapticsEnabled } from "@/src/haptics";
import { spacing, radius, typography, ACCENTS, useTheme, ThemeMode, AccentId, makeStyles, withAlpha } from "@/src/theme";
import { AtmospherePreview } from "@/src/components/atmosphere-preview";

// Mini-anteprime dell'atmosfera di lettura nel selettore del colore accento.
const ACCENT_PREVIEW_W = 44, ACCENT_PREVIEW_H = 66;
import { useUserId } from "@/src/session";
import { usePremium, PLANS } from "@/src/premium";
import { savePrefs } from "@/src/prefs-sync";
import { PauseMark } from "@/src/components/pause-logo";
import { StreakCard } from "@/src/components/streak-card";
import { GlassSurface, AmbientGlow } from "@/src/components/glass";
import { useI18n, Lang } from "@/src/i18n";
import { useAuth } from "@/src/auth";

export default function Profile() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const qc = useQueryClient();
  const userId = useUserId();
  const { t, lang, setLang } = useI18n();
  const auth = useAuth();
  const { isPremium } = usePremium();
  const yearlyPlan = PLANS.find((p) => p.id === "yearly")!;
  const { mode, setMode, accent, setAccent, scheme, colors } = useTheme();
  const [hapticsOn, setHapticsOn] = useHapticsEnabled();
  const styles = useStyles();

  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => api.user(userId!),
    enabled: !!userId,
  });
  const { data: categories } = useQuery({ queryKey: ["categories"], queryFn: api.categories });

  const resetOnboarding = async () => {
    await AsyncStorage.removeItem("pause.onboarded.v2");
    router.replace("/onboarding");
  };

  // Esci: chiude la sessione, torna a un id ospite nuovo e riparte dal passo
  // profilo (dove si può accedere di nuovo). Accedi (ospite): stesso passo.
  const signOut = async () => {
    await auth.signOut();
    qc.clear();
    router.replace("/onboarding");
  };
  const accountName = auth.user?.name || auth.user?.email || t.anon;

  const interestsCount = user?.interests.includes("all") ? categories?.length ?? 0 : user?.interests.length ?? 0;

  // Theme / accent / language are persisted twice: locally (instant, offline)
  // and on the user's profile, so the choice survives reinstalls and devices.
  const changeMode = (m: ThemeMode) => { setMode(m); savePrefs({ theme_mode: m }); };
  const changeAccent = (a: AccentId) => { setAccent(a); savePrefs({ theme_accent: a }); };
  const changeLang = (l: Lang) => { setLang(l); savePrefs({ lang: l }); };

  const modes = user?.content_modes ?? ["stories", "lessons"];

  const toggleMode = async (mode: "stories" | "lessons") => {
    if (!userId || !user) return;
    // Le mini lezioni sono solo Premium: per l'utente base il tocco apre il paywall.
    if (mode === "lessons" && !isPremium) { router.push("/premium"); return; }
    if (modes.includes(mode) && modes.length === 1) return; // at least one stays on
    const next = modes.includes(mode) ? modes.filter((m) => m !== mode) : [...modes, mode];
    qc.setQueryData(["user", userId], (prev: typeof user) => (prev ? { ...prev, content_modes: next } : prev));
    const state = await api.setContentModes(userId, next);
    qc.setQueryData(["user", userId], state);
    qc.invalidateQueries({ queryKey: ["discover-next"] });
  };

  return (
    <View style={styles.container}>
      {/* Fondo notte + luce ambientale cyan in alto: profondità anche qui. */}
      <LinearGradient colors={[colors.surface, colors.surfaceDeep]} locations={[0.3, 1]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <AmbientGlow color={colors.cyan} alpha={0.12} size={300} style={{ top: -60, right: -120 }} />
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingTop: insets.top + spacing.md, paddingBottom: insets.bottom + spacing.xxl, paddingHorizontal: spacing.xl }}
        showsVerticalScrollIndicator={false}
      >
      <Text style={styles.title}>{t.profile}</Text>
      <View style={styles.avatarRow}>
        <View style={styles.avatar}>
          <PauseMark size={30} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.name} testID="profile-account-name">{accountName}</Text>
          <Text style={styles.sub}>{auth.user?.email && auth.user?.name ? `${auth.user.email} · ` : ""}{user?.completed_story_ids.length ?? 0} {t.stories_completed}</Text>
        </View>
      </View>

      <View style={{ marginTop: spacing.xl }}>
        <StreakCard user={user} />
      </View>

      <Pressable
        testID="premium-card"
        onPress={() => router.push("/premium")}
        style={{ marginTop: spacing.xl }}
      >
        <GlassSurface
          intensity="regular"
          glow
          glowColor={isPremium ? colors.success + "44" : colors.cyanGlow}
          borderColor={isPremium ? colors.success + "66" : withAlpha(colors.cyan, 0.40)}
        >
          {/* Luce del brand che entra dal vetro, in trasparenza. */}
          <LinearGradient
            pointerEvents="none"
            colors={isPremium ? [colors.success + "2E", "transparent"] : [colors.brandSecondary + "3D", colors.cyan + "1F"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill}
          />
          <View style={styles.premiumCard}>
            <LinearGradient colors={colors.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.premiumIcon}>
              <Ionicons name="diamond" size={20} color="#FFFFFF" />
            </LinearGradient>
            <View style={{ flex: 1 }}>
              <View style={styles.premiumTitleRow}>
                <Text style={styles.premiumTitle}>{isPremium ? t.premium_active : t.premium_cta}</Text>
                {!isPremium ? (
                  <View style={styles.premiumPill}>
                    <Text style={styles.premiumPillText}>{t.pw_trial_pill.toUpperCase()}</Text>
                  </View>
                ) : null}
              </View>
              <Text style={styles.premiumSub}>
                {isPremium
                  ? t.premium_manage
                  : `${t.pw_then.replace("{price}", yearlyPlan.price).replace("{period}", t.per_year)} · ${t.pw_trust_cancel}`}
              </Text>
            </View>
            {isPremium ? (
              <View style={styles.premiumBadge}>
                <Text style={styles.premiumBadgeText}>{t.premium_badge}</Text>
              </View>
            ) : (
              <Ionicons name="chevron-forward" size={18} color={colors.cyan} />
            )}
          </View>
        </GlassSurface>
      </Pressable>

      <Section title={t.content_section}>
        <ModeSwitchRow
          icon="sparkles-outline"
          label={t.mode_stories}
          sub={t.mode_stories_sub}
          value={modes.includes("stories")}
          onToggle={() => toggleMode("stories")}
          testID="mode-switch-stories"
        />
        <ModeSwitchRow
          icon="school-outline"
          label={t.mode_lessons}
          sub={isPremium ? t.mode_lessons_sub : t.premium_unlock_lessons}
          value={isPremium && modes.includes("lessons")}
          onToggle={() => toggleMode("lessons")}
          testID="mode-switch-lessons"
          last
        />
      </Section>

      <Section title={t.library_section}>
        <Pressable style={styles.row} onPress={() => router.push("/history")} testID="history-row">
          <Ionicons name="library-outline" size={20} color={colors.onSurface} />
          <Text style={styles.rowText}>{t.history_row}</Text>
          <Text style={styles.rowValue}>{user?.completed_story_ids?.length ?? 0}</Text>
          <Ionicons name="chevron-forward" size={18} color={colors.muted} />
        </Pressable>
      </Section>

      <Section title={t.my_interests}>
        <Pressable style={styles.row} onPress={() => router.push("/(tabs)/explore")} testID="edit-interests">
          <Ionicons name="compass-outline" size={20} color={colors.onSurface} />
          <Text style={styles.rowText}>{t.edit_interests}</Text>
          <Text style={styles.rowValue}>{interestsCount}</Text>
          <Ionicons name="chevron-forward" size={18} color={colors.muted} />
        </Pressable>
      </Section>

      <Section title={t.appearance}>
        <View style={[styles.row, { flexDirection: "column", alignItems: "stretch", gap: spacing.md }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
            <Ionicons name={scheme === "light" ? "sunny-outline" : "moon-outline"} size={20} color={colors.onSurface} />
            <View style={{ flex: 1 }}>
              <Text style={styles.rowText}>{t.theme_row}</Text>
              <Text style={styles.rowHint}>{t.theme_hint}</Text>
            </View>
          </View>
          <View style={styles.themeSwitch}>
            {(["light", "dark", "system"] as ThemeMode[]).map((m) => (
              <Pressable
                key={m}
                onPress={() => changeMode(m)}
                testID={`theme-${m}`}
                style={[styles.themeBtn, mode === m && styles.themeBtnActive]}
              >
                <Text style={[styles.themeBtnText, mode === m && styles.themeBtnTextActive]}>
                  {m === "light" ? t.theme_light : m === "dark" ? t.theme_dark : t.theme_system}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>
        <View style={[styles.row, styles.rowLast, { flexDirection: "column", alignItems: "stretch", gap: spacing.md }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
            <Ionicons name="color-palette-outline" size={20} color={colors.onSurface} />
            <View style={{ flex: 1 }}>
              <Text style={styles.rowText}>{t.accent_row}</Text>
              <Text style={styles.rowHint}>{isPremium ? t.accent_hint : t.accent_locked}</Text>
            </View>
            {!isPremium ? <Ionicons name="lock-closed" size={16} color={colors.muted} /> : null}
          </View>
          <View style={styles.accentRow}>
            {ACCENTS.map((a) => {
              const active = accent === a.id;
              const locked = !isPremium;
              return (
                <Pressable
                  key={a.id}
                  testID={`accent-${a.id}`}
                  accessibilityRole="button"
                  accessibilityState={{ selected: active }}
                  accessibilityLabel={t[`accent_${a.id}` as keyof typeof t] as string}
                  onPress={() => {
                    if (locked) return router.push("/premium");
                    changeAccent(a.id);
                  }}
                  style={[styles.accentTile, locked && !active && { opacity: 0.6 }]}
                >
                  {/* Mini-anteprima dell'atmosfera di lettura con questo tema. */}
                  <View style={[styles.accentPreview, { borderColor: active ? colors.onSurface : "transparent" }]}>
                    <AtmospherePreview accent={a} scheme={scheme} width={ACCENT_PREVIEW_W} height={ACCENT_PREVIEW_H} />
                    {active ? (
                      <View style={[styles.accentMark, { backgroundColor: a[scheme].brand }]}>
                        <Ionicons name="checkmark" size={12} color={colors.onBrand} />
                      </View>
                    ) : locked ? (
                      <View style={[styles.accentMark, { backgroundColor: colors.overlay }]}>
                        <Ionicons name="lock-closed" size={10} color={colors.onSurface} />
                      </View>
                    ) : null}
                  </View>
                  <Text style={[styles.accentName, active && { color: colors.onSurface }]} numberOfLines={1}>{t[`accent_${a.id}` as keyof typeof t] as string}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      </Section>

      <Section title={t.settings}>
        <View style={styles.row}>
          <Ionicons name="language-outline" size={20} color={colors.onSurface} />
          <View style={{ flex: 1 }}>
            <Text style={styles.rowText}>{t.language}</Text>
            <Text style={styles.rowHint}>{t.language_hint}</Text>
          </View>
          <View style={styles.langSwitch}>
            {(["it", "en"] as Lang[]).map((l) => (
              <Pressable
                key={l}
                onPress={() => changeLang(l)}
                testID={`lang-${l}`}
                style={[styles.langBtn, lang === l && styles.langBtnActive]}
              >
                <Text style={[styles.langText, lang === l && styles.langTextActive]}>{l.toUpperCase()}</Text>
              </Pressable>
            ))}
          </View>
        </View>
        <View style={styles.row}>
          <MaterialDesignIcons name="vibrate" size={20} color={colors.onSurface} />
          <View style={{ flex: 1 }}>
            <Text style={styles.rowText}>{t.haptics_row}</Text>
            <Text style={styles.rowHint}>{t.haptics_hint}</Text>
          </View>
          <Switch
            value={hapticsOn}
            aria-checked={hapticsOn}
            accessibilityLabel={t.haptics_row}
            onValueChange={(v) => { setHapticsOn(v); if (v) Haptics.selectionAsync().catch(() => {}); }}
            trackColor={{ true: colors.cyan, false: colors.glassBorderStrong }}
            thumbColor={hapticsOn ? colors.surface : colors.onSurface}
            testID="haptics-switch"
          />
        </View>
        <Pressable style={styles.row} onPress={resetOnboarding} testID="reset-onboarding">
          <Ionicons name="refresh-outline" size={20} color={colors.onSurface} />
          <Text style={styles.rowText}>{t.redo_onboarding}</Text>
          <Ionicons name="chevron-forward" size={18} color={colors.muted} />
        </Pressable>
        {auth.status === "authenticated" ? (
          <Pressable style={styles.row} onPress={signOut} testID="account-sign-out">
            <Ionicons name="log-out-outline" size={20} color={colors.onSurface} />
            <Text style={styles.rowText}>{t.auth_sign_out}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.muted} />
          </Pressable>
        ) : (
          <Pressable style={styles.row} onPress={() => router.replace("/onboarding")} testID="account-sign-in">
            <Ionicons name="log-in-outline" size={20} color={colors.onSurface} />
            <View style={{ flex: 1 }}>
              <Text style={styles.rowText}>{t.auth_sign_in}</Text>
              <Text style={styles.rowHint}>{t.auth_sign_in_hint}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.muted} />
          </Pressable>
        )}
        <Pressable
          style={[styles.row, styles.rowLast]}
          onPress={() => Alert.alert("PΛUSE", t.about_body)}
        >
          <Ionicons name="information-circle-outline" size={20} color={colors.onSurface} />
          <Text style={styles.rowText}>{t.about}</Text>
          <Ionicons name="chevron-forward" size={18} color={colors.muted} />
        </Pressable>
      </Section>

      <Text style={styles.footerNote}>{t.tagline}</Text>
      </ScrollView>
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const styles = useStyles();
  return (
    <View style={{ marginTop: spacing.xl }}>
      <Text style={styles.sectionTitle}>{title.toUpperCase()}</Text>
      <GlassSurface intensity="regular">{children}</GlassSurface>
    </View>
  );
}

// Toggle row for a content mode (curiosities / mini lessons) in the Profile
// "Contenuti" section. Mirrors the automatic-pause row styling.
function ModeSwitchRow({
  icon, label, sub, value, onToggle, testID, last,
}: {
  icon: string; label: string; sub: string; value: boolean;
  onToggle: () => void; testID: string; last?: boolean;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <View style={[styles.row, last && styles.rowLast]}>
      <Ionicons name={icon as any} size={20} color={colors.onSurface} />
      <View style={{ flex: 1 }}>
        <Text style={styles.rowText}>{label}</Text>
        <Text style={styles.rowHint}>{sub}</Text>
      </View>
      <Switch
        value={value}
        aria-checked={value}
        accessibilityLabel={label}
        onValueChange={onToggle}
        trackColor={{ true: colors.cyan, false: colors.glassBorderStrong }}
        thumbColor={value ? colors.surface : colors.onSurface}
        testID={testID}
      />
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: colors.surface },
  title: { color: colors.textWarm, fontFamily: typography.displayBold, fontSize: 30, letterSpacing: -0.5 },
  avatarRow: { flexDirection: "row", alignItems: "center", gap: spacing.md, marginTop: spacing.lg },
  avatar: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: colors.glassBgLit,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: withAlpha(colors.cyan, 0.45),
    boxShadow: `0px 0px 20px ${colors.cyanGlowSoft}, 0px 8px 18px ${colors.glassShadow}` as any,
  },
  name: { color: colors.onSurface, fontFamily: typography.bodyBold, fontSize: 16 },
  sub: { color: colors.muted, fontFamily: typography.body, fontSize: 13, marginTop: 2 },
  sectionTitle: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 11, letterSpacing: 2, marginBottom: spacing.sm },
  row: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    paddingHorizontal: spacing.lg, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: colors.glassBorder,
  },
  rowLast: { borderBottomWidth: 0 },
  rowText: { flex: 1, color: colors.onSurface, fontFamily: typography.bodyMedium, fontSize: 15 },
  rowHint: { color: colors.muted, fontFamily: typography.body, fontSize: 12, marginTop: 2 },
  rowValue: { color: colors.muted, fontFamily: typography.body, fontSize: 13, marginRight: 4 },
  // Segmented in vetro: traccia traslucida, segmento attivo illuminato cyan.
  langSwitch: {
    flexDirection: "row", padding: 3, borderRadius: radius.pill,
    backgroundColor: colors.glassBg, borderWidth: 1, borderColor: colors.glassBorder,
  },
  langBtn: { paddingHorizontal: 12, height: 30, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  langBtnActive: {
    backgroundColor: withAlpha(colors.cyan, 0.18), borderWidth: 1, borderColor: withAlpha(colors.cyan, 0.5),
    boxShadow: `0px 0px 12px ${colors.cyanGlowSoft}` as any,
  },
  langText: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 12 },
  langTextActive: { color: colors.textWarm },
  // Theme switch: full-width row so Chiaro / Scuro / Sistema labels fit.
  themeSwitch: {
    flexDirection: "row", padding: 3, borderRadius: radius.pill,
    backgroundColor: colors.glassBg, borderWidth: 1, borderColor: colors.glassBorder,
    marginLeft: 32,
  },
  themeBtn: { flex: 1, height: 34, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  themeBtnActive: {
    backgroundColor: withAlpha(colors.cyan, 0.18), borderWidth: 1, borderColor: withAlpha(colors.cyan, 0.5),
    boxShadow: `0px 0px 12px ${colors.cyanGlowSoft}` as any,
  },
  themeBtnText: { color: colors.muted, fontFamily: typography.bodyBold, fontSize: 12 },
  themeBtnTextActive: { color: colors.textWarm },
  footerNote: { color: colors.muted, fontFamily: typography.bodyMedium, fontSize: 10, letterSpacing: 2.5, textAlign: "center", marginTop: spacing.xxl },
  premiumCard: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    padding: spacing.lg,
  },
  premiumIcon: {
    width: 40, height: 40, borderRadius: 14, alignItems: "center", justifyContent: "center",
    boxShadow: `0px 0px 16px ${colors.cyanGlow}` as any,
  },
  premiumTitleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flexWrap: "wrap" },
  premiumTitle: { color: colors.textWarm, fontFamily: typography.bodyBold, fontSize: 16 },
  premiumPill: {
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: radius.pill,
    backgroundColor: withAlpha(colors.cyan, 0.12), borderWidth: 1, borderColor: withAlpha(colors.cyan, 0.4),
  },
  premiumPillText: { color: colors.cyan, fontFamily: typography.bodyBold, fontSize: 9, letterSpacing: 1.2 },
  premiumSub: { color: colors.onSurfaceTertiary, fontFamily: typography.body, fontSize: 12, marginTop: 3, lineHeight: 17 },
  premiumBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.pill, backgroundColor: colors.success + "22" },
  premiumBadgeText: { color: colors.success, fontFamily: typography.bodyBold, fontSize: 10, letterSpacing: 1 },
  accentRow: { flexDirection: "row", gap: spacing.xs, marginTop: spacing.xs, justifyContent: "space-between" },
  accentTile: { alignItems: "center", gap: 6, flexShrink: 1 },
  accentPreview: { borderRadius: 15, borderWidth: 2, padding: 2 },
  accentMark: {
    position: "absolute", right: 5, top: 5, width: 18, height: 18, borderRadius: 9,
    alignItems: "center", justifyContent: "center",
  },
  accentName: { color: colors.onSurfaceTertiary, fontFamily: typography.bodyMedium, fontSize: 11 },
}));
