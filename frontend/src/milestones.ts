// PAUSE — traguardi di lettura (20, 40, 60… storie): memoria dell'ultimo
// traguardo festeggiato, per utente, così l'animazione appare una volta sola.
import { useCallback, useEffect, useRef, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

export const MILESTONE_STEP = 20;

const key = (uid: string) => `pause.milestone.${uid}`;

export function milestoneFor(count: number): number {
  return Math.floor(count / MILESTONE_STEP) * MILESTONE_STEP;
}

/** Restituisce il traguardo appena raggiunto (o null) e una funzione per archiviarlo.
 *  Al primo avvio il traguardo corrente viene registrato senza festeggiare: si
 *  celebrano solo i traguardi superati da qui in avanti. */
export function useReadingMilestone(uid: string | null, count: number | undefined) {
  const seen = useRef<number | null>(null);
  const [pending, setPending] = useState<number | null>(null);

  useEffect(() => {
    if (!uid || count === undefined) return;
    let cancelled = false;
    (async () => {
      if (seen.current === null) {
        const raw = await AsyncStorage.getItem(key(uid)).catch(() => null);
        if (cancelled) return;
        if (raw === null) {
          seen.current = milestoneFor(count);
          AsyncStorage.setItem(key(uid), String(seen.current)).catch(() => {});
          return;
        }
        seen.current = Number(raw) || 0;
      }
      const reached = milestoneFor(count);
      if (reached > 0 && reached > seen.current) setPending(reached);
    })();
    return () => { cancelled = true; };
  }, [uid, count]);

  const dismiss = useCallback(() => {
    if (!uid || pending === null) return;
    seen.current = pending;
    AsyncStorage.setItem(key(uid), String(pending)).catch(() => {});
    setPending(null);
  }, [uid, pending]);

  return { milestone: pending, dismiss };
}
