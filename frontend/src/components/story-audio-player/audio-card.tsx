// PAUSE — Story audio player: the AudioCard (compact by default, expandable
// advanced controls) plus its internal chip helpers.

import React, { useState } from "react";
import { View, Text, Pressable, ActivityIndicator } from "react-native";
import Ionicons from "@react-native-vector-icons/ionicons";
import * as Haptics from "@/src/haptics";
import { LinearGradient } from "expo-linear-gradient";

import { useTheme } from "@/src/theme";
import { VoiceId, VOICES, FREE_VOICE } from "@/src/api";
import { useI18n } from "@/src/i18n";

import { useAudio } from "./context";
import { FREE_MAX_SPEED, SPEEDS, fmt, speedLabel } from "./constants";
import { useStyles } from "./styles";

// `dense`: versione stretta per la barra in alto del lettore (accanto a
// "Indietro"): mostra solo la voce, i tempi e la barra di avanzamento.
export function AudioCard({ compact = false, dense = false, testID }: { compact?: boolean; dense?: boolean; testID?: string }) {
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const a = useAudio();
  const [expanded, setExpanded] = useState(false);
  compact = compact || dense;
  if (!a.isPremium) return null;

  const voiceName = (v: VoiceId) => t[`voice_${v}` as const].split(" · ")[0];
  const subtitle = a.unavailable ? t.audio_unavailable
    : a.buffering && !a.isLoaded && !a.playing ? t.audio_preparing
    : a.resumeFrom !== null && !a.playing && a.position < a.resumeFrom + 1
    ? t.audio_resume_from(fmt(a.resumeFrom))
    : a.preview ? t.audio_preview_label : dense ? voiceName(a.voice) : `${t.audio_full} · ${voiceName(a.voice)}`;

  const toggleExpand = () => {
    Haptics.selectionAsync().catch(() => {});
    setExpanded((e) => {
      if (e) a.setPanel("none");
      return !e;
    });
  };

  return (
    <View style={[styles.wrap, compact && styles.wrapCompact, dense && styles.wrapDense]} testID={testID ?? "story-audio-player"}>
      {/* Compact row — always visible: play · title · progress · expand */}
      <View style={styles.mainRow}>
        <Pressable
          style={({ pressed }) => [styles.playBtn, compact && styles.playBtnCompact, dense && styles.playBtnDense, pressed && styles.pressed]}
          onPress={a.togglePlay}
          hitSlop={8}
          testID="audio-play-toggle"
        >
          <LinearGradient colors={colors.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.fill} />
          {a.buffering ? (
            <ActivityIndicator color={colors.onGradient} size="small" />
          ) : (
            <Ionicons
              name={a.playing ? "pause" : "play"}
              size={compact ? 18 : 20}
              color={colors.onGradient}
              style={!a.playing ? { marginLeft: 2 } : undefined}
            />
          )}
        </Pressable>

        <View style={styles.center}>
          {compact ? (
            // Una sola riga: titolo a sinistra, tempi a destra → footer basso.
            <View style={styles.compactHead}>
              <Text
                style={[styles.subtitle, { flex: 1 }, a.resumeFrom !== null && !a.playing && { color: colors.brand }]}
                numberOfLines={1}
                testID="audio-subtitle"
              >
                {subtitle}
              </Text>
              <Text style={styles.time}>
                <Text testID="audio-current">{fmt(a.position)}</Text> / <Text testID="audio-duration">{fmt(a.duration)}</Text>
              </Text>
            </View>
          ) : (
            <>
              <Text style={styles.eyebrow}>{t.audio_eyebrow}</Text>
              <Text
                style={[styles.subtitle, a.resumeFrom !== null && !a.playing && { color: colors.brand }]}
                numberOfLines={1}
                testID="audio-subtitle"
              >
                {subtitle}
              </Text>
            </>
          )}
          <View style={styles.progressTrack}>
            <LinearGradient
              colors={colors.gradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[styles.progressFill, { width: `${a.progress * 100}%` }]}
            />
          </View>
          {!compact ? (
            <View style={styles.timesRow}>
              <Text style={styles.time} testID="audio-current">{fmt(a.position)}</Text>
              <Text style={styles.time} testID="audio-duration">{fmt(a.duration)}</Text>
            </View>
          ) : null}
        </View>

        {!a.preview ? (
          <Pressable
            style={({ pressed }) => [styles.expandBtn, expanded && styles.expandBtnActive, pressed && styles.pressed]}
            onPress={toggleExpand}
            hitSlop={8}
            testID="audio-expand-toggle"
            accessibilityLabel="audio-options"
          >
            <Ionicons name={expanded ? "chevron-up" : "options-outline"} size={16} color={expanded ? colors.brand : colors.onSurfaceSecondary} />
          </Pressable>
        ) : null}
      </View>

      {/* Expanded — advanced controls */}
      {expanded && !a.preview ? (
        <View style={styles.expandedWrap} testID="audio-expanded">
          <View style={styles.transportRow}>
            <Pressable
              style={({ pressed }) => [styles.transportBtn, pressed && styles.pressed]}
              onPress={() => a.skip(-10)}
              disabled={!a.isLoaded}
              hitSlop={6}
              testID="audio-back-10"
            >
              <Ionicons name="play-back" size={14} color={colors.onSurface} />
              <Text style={styles.transportLabel}>10</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.speedBtn, a.panel === "speed" && styles.speedBtnActive, pressed && styles.pressed]}
              onPress={() => a.setPanel((p) => (p === "speed" ? "none" : "speed"))}
              hitSlop={6}
              testID="audio-speed-toggle"
            >
              <Ionicons name="speedometer-outline" size={13} color={colors.brand} />
              <Text style={styles.speedBtnLabel}>{speedLabel(a.rate)}</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.transportBtn, pressed && styles.pressed]}
              onPress={() => a.skip(10)}
              disabled={!a.isLoaded}
              hitSlop={6}
              testID="audio-fwd-10"
            >
              <Text style={styles.transportLabel}>10</Text>
              <Ionicons name="play-forward" size={14} color={colors.onSurface} />
            </Pressable>
          </View>

          <View style={styles.toolsRow}>
            <ToolChip
              icon="mic-outline"
              label={voiceName(a.voice)}
              active={a.panel === "voice"}
              onPress={() => a.setPanel((p) => (p === "voice" ? "none" : "voice"))}
              testID="audio-voice-toggle"
            />
            {a.offline !== "unsupported" ? (
              <ToolChip
                icon={a.offline === "ready" ? "cloud-done-outline" : "cloud-download-outline"}
                label={a.offline === "ready" ? t.audio_downloaded : a.offline === "downloading" ? t.audio_downloading : t.audio_download}
                active={a.offline === "ready"}
                loading={a.offline === "downloading"}
                onPress={() => (a.offline === "ready" ? a.removeDownload() : a.download())}
                testID="audio-download"
              />
            ) : null}
            {!a.isPremium ? (
              <View style={styles.premiumPill} testID="audio-premium-pill">
                <Ionicons name="diamond-outline" size={10} color={colors.brand} />
                <Text style={styles.premiumPillText}>{t.audio_premium_pill}</Text>
              </View>
            ) : null}
          </View>

          {a.panel === "speed" ? (
            <View style={styles.chipRow} testID="audio-speed-row">
              {SPEEDS.map((v) => (
                <OptionChip
                  key={v}
                  label={speedLabel(v)}
                  active={Math.abs(v - a.rate) < 0.001}
                  locked={!a.isPremium && v > FREE_MAX_SPEED}
                  onPress={() => { a.setRate(v); if (a.isPremium || v <= FREE_MAX_SPEED) a.setPanel("none"); }}
                  testID={`audio-speed-${v}`}
                />
              ))}
            </View>
          ) : null}

          {a.panel === "voice" ? (
            <View style={styles.voiceList} testID="audio-voice-row">
              {VOICES.map((v) => {
                const locked = !a.isPremium && v !== FREE_VOICE;
                const active = a.voice === v;
                return (
                  <View key={v} style={[styles.voiceRow, active && styles.voiceRowActive]}>
                    <Pressable style={styles.voiceMain} onPress={() => a.setVoice(v)} testID={`audio-voice-${v}`}>
                      <Ionicons
                        name={active ? "radio-button-on" : locked ? "lock-closed-outline" : "radio-button-off"}
                        size={16}
                        color={active ? colors.brand : colors.muted}
                      />
                      <Text style={[styles.voiceLabel, active && { color: colors.brand }]}>{t[`voice_${v}` as const]}</Text>
                    </Pressable>
                    <Pressable style={styles.sampleBtn} onPress={() => a.playSample(v)} hitSlop={6} testID={`audio-voice-sample-${v}`}>
                      <Ionicons name="volume-medium-outline" size={14} color={colors.onSurfaceSecondary} />
                      <Text style={styles.sampleLabel}>{t.voice_sample}</Text>
                    </Pressable>
                  </View>
                );
              })}
              {!a.isPremium ? <Text style={styles.hint}>{t.audio_premium_hint}</Text> : null}
            </View>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

function ToolChip({
  icon, label, active, loading, onPress, testID,
}: { icon: string; label: string; active?: boolean; loading?: boolean; onPress: () => void; testID: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <Pressable
      style={({ pressed }) => [styles.toolChip, active && styles.toolChipActive, pressed && styles.pressed]}
      onPress={onPress}
      hitSlop={4}
      testID={testID}
    >
      {loading ? (
        <ActivityIndicator size="small" color={colors.brand} />
      ) : (
        <Ionicons name={icon as any} size={13} color={active ? colors.brand : colors.onSurfaceSecondary} />
      )}
      <Text style={[styles.toolChipLabel, active && { color: colors.brand }]} numberOfLines={1}>{label}</Text>
    </Pressable>
  );
}

function OptionChip({
  label, active, locked, onPress, testID,
}: { label: string; active: boolean; locked?: boolean; onPress: () => void; testID: string }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <Pressable style={[styles.optChip, active && styles.optChipActive]} onPress={onPress} testID={testID}>
      {locked ? <Ionicons name="lock-closed" size={9} color={colors.muted} /> : null}
      <Text style={[styles.optChipLabel, active && styles.optChipLabelActive]}>{label}</Text>
    </Pressable>
  );
}
