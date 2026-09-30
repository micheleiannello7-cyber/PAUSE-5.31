// PAUSE — user id + local persistence.
// Storage calls are wrapped with a timeout so a blocked/hanging storage backend
// (some web browsers, private modes, embedded webviews) can never freeze the
// app: we degrade to an in-memory id for the session instead of waiting forever.
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useState } from "react";

const USER_KEY = "pause.user_id";
// Bump the version suffix to force everyone through the (new) onboarding flow
// again — existing devices carry the old key and would otherwise skip it.
const ONBOARDED_KEY = "pause.onboarded.v2";
const STORAGE_TIMEOUT_MS = 2000;

let memoryId: string | null = null;

function uuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function withTimeout<T>(p: Promise<T>, fallback: () => T): Promise<T> {
  return new Promise<T>((resolve) => {
    let settled = false;
    const finish = (value: T) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(value);
    };
    const timer = setTimeout(() => finish(fallback()), STORAGE_TIMEOUT_MS);
    p.then((v) => finish(v)).catch(() => finish(fallback()));
  });
}

export async function getOrCreateUserId(): Promise<string> {
  const existing = await withTimeout(AsyncStorage.getItem(USER_KEY), () => memoryId);
  if (existing) {
    memoryId = existing;
    return existing;
  }
  const id = memoryId ?? uuid();
  memoryId = id;
  await withTimeout(AsyncStorage.setItem(USER_KEY, id), () => false);
  return id;
}

// Dopo il login l'app lavora con l'id dell'account (progressi/preferiti legati
// all'account, non al dispositivo). Al logout si torna a un id ospite nuovo.
export async function adoptUserId(id: string) {
  memoryId = id;
  await withTimeout(AsyncStorage.setItem(USER_KEY, id), () => false);
}

export async function resetUserId(): Promise<string> {
  const id = uuid();
  memoryId = id;
  await withTimeout(AsyncStorage.setItem(USER_KEY, id), () => false);
  return id;
}

export async function isOnboarded(): Promise<boolean> {
  const v = await withTimeout(AsyncStorage.getItem(ONBOARDED_KEY), () => null);
  return v === "1";
}

export async function setOnboarded() {
  await withTimeout(AsyncStorage.setItem(ONBOARDED_KEY, "1"), () => false);
}

export function useUserId() {
  const [id, setId] = useState<string | null>(null);
  useEffect(() => {
    getOrCreateUserId().then(setId);
  }, []);
  return id;
}
