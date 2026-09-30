import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable } from "react-native";
import Animated, { FadeInRight, FadeInLeft, FadeOut, LinearTransition, Easing } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Ionicons from "@react-native-vector-icons/ionicons";

import * as Haptics from "@/src/haptics";

import { api, ProfileInput } from "@/src/api";
import { makeStyles, useTheme, spacing, typography, radius, withAlpha } from "@/src/theme";
import { getOrCreateUserId, setOnboarded } from "@/src/session";
import { toggleInterest } from "@/src/components/category-grid";
import { PagerDots } from "@/src/components/pager";
import { OnboardingIntro } from "@/src/components/onboarding-intro";
import { OnboardingProfile, ProfileDraft, MIN_NAME } from "@/src/components/onboarding-profile";
import { ModeCards, toggleContentMode } from "@/src/components/onboarding-modes";
import { TopicPicker, TopicsBackdrop } from "@/src/components/topic-picker";
import { OnboardingSwipe, SwipeDir } from "@/src/components/onboarding-swipe";
import { OnboardingToast, OnboardingNotice } from "@/src/components/onboarding-toast";
import { ONB } from "@/src/components/onboarding-palette";
import { useI18n } from "@/src/i18n";
import { useAuth } from "@/src/auth";
import { usePremiumFlag } from "@/src/premium";

type Mode = "stories" | "lessons";

// Fasi: 0 intro · 1 profilo (account + nome/genere/età) · 2 scelta formato · 3 argomenti.
// Percorso ridotto: profilo (con accesso Google/Apple o ospite) → argomenti.
// Intro e scelta formato saltati (i formati restano modificabili dai chip in alto).
// Rimetti a 0 per ripristinare il percorso completo.
const START_STEP = 1;
const PROFILE_STEP = 1;
const TOPICS_STEP = 3;
const DEFAULT_MODES: Mode[] = ["stories", "lessons"];
const LAYOUT = LinearTransition.duration(340).easing(Easing.inOut(Easing.cubic));
const enterFrom = (dir: SwipeDir) => (dir > 0 ? FadeInRight : FadeInLeft).duration(380).easing(Easing.out(Easing.cubic));

export default function Onboarding() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [step, setStep] = useState(START_STEP);
  const [dir, setDir] = useState<SwipeDir>(1);
  const [notice, setNotice] = useState<OnboardingNotice | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [modes, setModes] = useState<Set<Mode>>(new Set<Mode>(DEFAULT_MODES));
  const [saving, setSaving] = useState(false);
  // Passo profilo: tutti i campi sono facoltativi (il nome non è obbligatorio).
  const [profile, setProfile] = useState<ProfileDraft>({ name: "", gender: null, age: null });
  const { t } = useI18n();
  const auth = useAuth();
  // Dopo l'accesso, il nome dell'account precompila il nickname (se vuoto).
  useEffect(() => {
    if (auth.user?.name) setProfile((p) => (p.name.trim() ? p : { ...p, name: auth.user!.name!.slice(0, 40) }));
  }, [auth.user]);
  const styles = useStyles();
  const { colors } = useTheme();
  const isPremium = usePremiumFlag();
  // Nessun limite di argomenti: si sceglie liberamente (ESPLORA inclusa).
  const onToggleCategory = (id: string) => {
    setSelected((prev) => toggleInterest(prev, id));
  };
  const qc = useQueryClient();
  const { data: categories, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["categories"],
    queryFn: api.categories,
  });

  const topics = step === 3;
  const canContinue = topics ? selected.size > 0 && modes.size > 0 : modes.size > 0;

  // Le mini lezioni sono solo Premium: per l'utente base un avviso breve.
  const toggleMode = (m: Mode) => {
    if (m === "lessons" && !isPremium) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
      setNotice({ title: t.lessons_locked_t, body: t.lessons_locked_b, icon: "lock-closed-outline" });
      return;
    }
    Haptics.selectionAsync().catch(() => {});
    setModes((prev) => toggleContentMode(prev, m, topics));
  };

  const goTo = (index: number) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    setDir(index >= step ? 1 : -1);
    setStep(index);
  };

  // Messaggio "ben fatto" quando manca una scelta obbligatoria.
  const explainMissing = () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    setNotice(
      step === 3 && modes.size > 0
        ? { title: t.onb_need_topic_t, body: t.onb_need_topic_b, icon: "grid-outline" }
        : { title: t.onb_need_mode_t, body: t.onb_need_mode_b, icon: "layers-outline" },
    );
  };

  const canSwipe = (d: SwipeDir) => (d < 0 ? step > START_STEP : step === 0 || canContinue);
  const onSwipe = (d: SwipeDir) => {
    // Dal passo argomenti si torna al profilo (la scelta formato è saltata).
    if (d < 0) { goTo(step === TOPICS_STEP ? PROFILE_STEP : step - 1); return; }
    if (step === 3) { onContinue(); return; }
    goTo(step + 1);
  };
  const onBlockedSwipe = (d: SwipeDir) => { if (d > 0) explainMissing(); };

  const onContinue = async () => {
    if (!canContinue) return;
    setSaving(true);
    try {
      const uid = await getOrCreateUserId();
      await api.setInterests(uid, Array.from(selected));
      await api.setContentModes(uid, Array.from(modes));
      // Profilo facoltativo: invia solo i campi effettivamente compilati.
      const prof: ProfileInput = {};
      const name = profile.name.trim();
      if (name.length >= MIN_NAME) prof.display_name = name;
      if (profile.gender) prof.gender = profile.gender;
      if (profile.age != null) prof.age = profile.age;
      if (Object.keys(prof).length > 0) {
        try { await api.setProfile(uid, prof); } catch {}
      }
      await setOnboarded();
      // La Home legge interessi e formati dalla query utente: va aggiornata subito.
      await qc.invalidateQueries({ queryKey: ["user", uid] });
      router.replace("/(tabs)/discover");
    } finally {
      setSaving(false);
    }
  };

  // Only the presentation changes; topic selection and persistence stay intact.
  if (step === 0) {
    return (
      <OnboardingSwipe canGo={canSwipe} onGo={onSwipe} onBlocked={onBlockedSwipe} testID="onboarding-swipe">
        <Animated.View key="intro" entering={enterFrom(dir)} style={styles.container}>
          <OnboardingIntro onContinue={() => goTo(1)} />
        </Animated.View>
      </OnboardingSwipe>
    );
  }

  // ------------------------------------------------------- STEP 1 profilo (facoltativo)
  if (step === 1) {
    return (
      <View style={styles.profileViewport} testID="onboarding-profile-viewport">
        <Animated.View key="profile" entering={enterFrom(dir)} style={styles.container}>
          <OnboardingProfile
            value={profile}
            onChange={setProfile}
            onBack={step > START_STEP ? () => goTo(0) : undefined}
            onContinue={() => goTo(TOPICS_STEP)}
            canContinue
            saving={false}
            ctaLabel={auth.status === "authenticated" ? t.onb_modes_next : t.auth_guest_cta}
          />
        </Animated.View>
      </View>
    );
  }

  // ------------------------------------------- STEP 1 formato · STEP 2 argomenti
  return (
    <View style={[styles.container, { paddingTop: insets.top }]} testID="onboarding-topics">
      <TopicsBackdrop />
      <OnboardingSwipe key={step} canGo={canSwipe} onGo={onSwipe} onBlocked={onBlockedSwipe} testID="onboarding-swipe">
      {isLoading ? (
        <ActivityIndicator color={colors.brand} style={{ marginTop: spacing.xxxl }} testID="onboarding-loading" />
      ) : isError || !categories ? (
        <View style={styles.errorWrap} testID="onboarding-error">
          <Ionicons name="cloud-offline-outline" size={44} color={colors.muted} />
          <Text style={styles.errorTitle}>{t.load_error}</Text>
          <Text style={styles.errorText}>{t.load_error_sub}</Text>
          <Pressable
            onPress={() => refetch()}
            style={({ pressed }) => [styles.retryBtn, { opacity: pressed ? 0.7 : 1 }]}
            testID="onboarding-retry"
          >
            {isFetching ? (
              <ActivityIndicator color={colors.brand} size="small" />
            ) : (
              <>
                <Ionicons name="refresh" size={16} color={colors.brand} />
                <Text style={styles.retryText}>{t.retry}</Text>
              </>
            )}
          </Pressable>
        </View>
      ) : topics ? (
        // Argomenti a schermo intero: nessuno scorrimento, la griglia si adatta all'altezza rimasta.
        <View style={styles.fitArea} testID="onboarding-selection-scroll">
          <Animated.View key="topics" entering={enterFrom(dir)} layout={LAYOUT} style={styles.fitArea}>
            <TopicPicker testID="onboarding-topics" categories={categories} selected={selected} modes={modes}
              onToggleMode={toggleMode} onToggleCategory={onToggleCategory} lockedModes={isPremium ? undefined : new Set(["lessons"])}
              disabled={saving} staggerIn columns={4} fit />
          </Animated.View>
        </View>
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[styles.content, styles.contentCentered]}
          showsVerticalScrollIndicator={false}
          bounces={false}
          testID="onboarding-selection-scroll"
        >
          <Animated.View key="modes" entering={enterFrom(dir)} exiting={FadeOut.duration(160)} layout={LAYOUT}>
            <Text style={styles.stepTitle} testID="onboarding-modes-title">{t.onb_content_q}</Text>
            <ModeCards modes={modes} onToggle={toggleMode} />
          </Animated.View>
        </ScrollView>
      )}
      </OnboardingSwipe>

      <OnboardingToast notice={notice} bottom={insets.bottom + 132} onHide={() => setNotice(null)} testID="topics-limit-toast" />

      <View style={[styles.footer, { paddingBottom: insets.bottom + spacing.sm + 2 }]}>
        {topics ? (
          <PagerDots count={2} index={1} color={ONB.cyan} onSelect={(i) => i === 0 && goTo(PROFILE_STEP)} style={styles.dots} testID="onboarding-dots" />
        ) : null}
        <Pressable
          onPress={() => {
            if (!canContinue) { explainMissing(); return; }
            if (!topics) { goTo(3); return; }
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
            onContinue();
          }}
          disabled={saving}
          testID="onboarding-continue"
          accessibilityRole="button"
          accessibilityState={{ disabled: !canContinue }}
          style={({ pressed }) => [
            styles.ctaBtn,
            { opacity: canContinue ? 1 : 0.45 },
            canContinue && styles.ctaBtnActive,
            pressed && styles.ctaPressed,
          ]}
        >
          {saving ? (
            <ActivityIndicator color={ONB.cyan} />
          ) : (
            <>
              <Text style={styles.ctaText}>{topics ? t.onb_cta : t.onb_modes_next}</Text>
              <Ionicons name="arrow-forward" size={18} color={ONB.cyan} />
            </>
          )}
        </Pressable>
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  container: { flex: 1, backgroundColor: ONB.bgTop },
  profileViewport: { flex: 1, backgroundColor: ONB.bgTop, overflow: "hidden" },
  scroll: { flex: 1 },
  fitArea: { flex: 1, minHeight: 0 },
  content: { paddingHorizontal: spacing.xl, paddingTop: spacing.lg, paddingBottom: spacing.lg },
  contentCentered: { flexGrow: 1, justifyContent: "center", paddingBottom: spacing.xxxl },
  stepTitle: {
    color: ONB.text, fontFamily: typography.displayBold, fontSize: 28, lineHeight: 34, marginBottom: spacing.lg,
    textShadowColor: "rgba(55,211,255,0.25)", textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 18,
  },
  dots: { alignSelf: "center", marginBottom: spacing.sm + 2 },
  ctaBtn: {
    minHeight: 56, borderRadius: radius.pill, overflow: "hidden",
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.sm,
    backgroundColor: "rgba(8,20,47,0.85)",
    borderWidth: 1.5, borderColor: ONB.glassBorder,
  },
  ctaBtnActive: {
    borderColor: withAlpha(ONB.cyan, 0.7),
    boxShadow: `0px 0px 22px ${withAlpha(ONB.cyan, 0.28)}, 0px 8px 30px rgba(31,75,255,0.25)` as any,
  },
  ctaPressed: { opacity: 0.86, transform: [{ scale: 0.99 }] },
  ctaText: { color: ONB.cyanSoft, fontFamily: typography.bodyBold, fontSize: 16 },
  footer: {
    paddingHorizontal: spacing.xl, paddingTop: spacing.sm + 2,
    backgroundColor: "transparent",
  },
  errorWrap: {
    flex: 1, alignItems: "center", justifyContent: "center",
    paddingHorizontal: spacing.xl, gap: spacing.md,
  },
  errorTitle: { color: colors.onSurface, fontFamily: typography.displayBold, fontSize: 18, textAlign: "center" },
  errorText: { color: colors.muted, fontFamily: typography.body, fontSize: 14, textAlign: "center", lineHeight: 20 },
  retryBtn: {
    marginTop: spacing.sm, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    minHeight: 48, paddingHorizontal: spacing.xl,
    borderRadius: radius.pill, borderWidth: 1, borderColor: colors.brand,
  },
  retryText: { color: colors.brand, fontFamily: typography.bodyBold, fontSize: 15 },
}));
