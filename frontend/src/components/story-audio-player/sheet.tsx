// PAUSE — Story audio player: bottom sheet con il player completo (si apre da
// "Ascolta" nell'introduzione o dal badge flottante).

import React from "react";
import { View, Text, Pressable, Modal, ScrollView } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Ionicons from "@react-native-vector-icons/ionicons";

import { spacing, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";

import { useAudio } from "./context";
import { AudioCard } from "./audio-card";
import { useStyles } from "./styles";

// Bottom sheet della narrazione: si apre dal tastino "cuffie" accanto al
// capitolo e contiene il player completo (voce, velocità, ±10s, offline).
export function AudioSheet({ visible, onClose, testID = "audio-sheet" }: { visible: boolean; onClose: () => void; testID?: string }) {
  const { t } = useI18n();
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { isPremium } = useAudio();
  if (!isPremium) return null;
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <Pressable style={styles.sheetBackdrop} onPress={onClose} testID="audio-sheet-backdrop" />
      <View style={[styles.sheet, { paddingBottom: insets.bottom + spacing.lg }]} testID={testID}>
        <View style={styles.sheetHandle} />
        <View style={styles.sheetHead}>
          <View style={styles.sheetTitleRow}>
            <Ionicons name="headset" size={16} color={colors.brand} />
            <Text style={styles.sheetTitle}>{t.audio_eyebrow}</Text>
          </View>
          <Pressable onPress={onClose} hitSlop={10} style={styles.sheetClose} testID="audio-sheet-close">
            <Ionicons name="close" size={18} color={colors.onSurface} />
          </Pressable>
        </View>
        <ScrollView bounces={false} showsVerticalScrollIndicator={false}>
          <AudioCard testID="deep-dive-audio-player" />
        </ScrollView>
      </View>
    </Modal>
  );
}
