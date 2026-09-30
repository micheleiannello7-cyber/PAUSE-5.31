// PAUSE — account (Google via Emergent Auth su tutte le piattaforme, Sign in
// with Apple solo iOS). Stati: loading → authenticated | guest.
// Il token di sessione (7 giorni) vive in SecureStore (nativo) / localStorage
// (web) e viaggia come Bearer; dopo il login l'app adotta lo `user_id`
// dell'account come identificativo per progressi e preferiti.
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Platform } from "react-native";
import * as Linking from "expo-linking";
import * as SecureStore from "expo-secure-store";
import * as WebBrowser from "expo-web-browser";
import * as AppleAuthentication from "expo-apple-authentication";

import { api, ApiError, AuthResult, AuthUser, setApiAuthToken } from "./api";
import { adoptUserId, resetUserId } from "./session";

WebBrowser.maybeCompleteAuthSession();

const TOKEN_KEY = "pause.session_token";
const AUTH_URL = "https://auth.emergentagent.com/";
const SESSION_RE = /[?#&]session_id=([^&#]+)/;
const isWeb = Platform.OS === "web";
// Catturato all'import: la pagina atterra su `/#session_id=…` e il router
// potrebbe riscrivere l'URL prima che i nostri effetti girino.
const initialWebUrl = isWeb && typeof window !== "undefined" ? window.location.href : null;
// A livello di modulo: lo stesso session_id non va mai scambiato due volte
// (rimontaggi, StrictMode, deep link + risultato del browser).
const usedSessionIds = new Set<string>();

async function readToken(): Promise<string | null> {
  try {
    return isWeb ? window.localStorage.getItem(TOKEN_KEY) : await SecureStore.getItemAsync(TOKEN_KEY);
  } catch {
    return null;
  }
}
async function writeToken(token: string | null) {
  try {
    if (isWeb) {
      if (token) window.localStorage.setItem(TOKEN_KEY, token);
      else window.localStorage.removeItem(TOKEN_KEY);
    } else if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
    else await SecureStore.deleteItemAsync(TOKEN_KEY);
  } catch {}
}

export function extractSessionId(url: string | null | undefined): string | null {
  if (!url) return null;
  const m = url.match(SESSION_RE);
  return m ? decodeURIComponent(m[1]) : null;
}

// Rimuove solo `session_id` dall'URL web, preservando gli altri parametri.
function cleanWebUrl() {
  if (!isWeb || typeof window === "undefined") return;
  const strip = (s: string, lead: string) => {
    const parts = s.replace(/^[?#]/, "").split("&").filter((p) => p && !p.startsWith("session_id="));
    return parts.length ? lead + parts.join("&") : "";
  };
  const next = window.location.pathname + strip(window.location.search, "?") + strip(window.location.hash, "#");
  window.history.replaceState(window.history.state, "", next);
}

export type AuthStatus = "loading" | "authenticated" | "guest";
export type SignInOutcome = "ok" | "cancelled" | "error" | "redirect";

type AuthCtx = {
  status: AuthStatus;
  user: AuthUser | null;
  busy: boolean;
  appleAvailable: boolean;
  signInWithGoogle: () => Promise<SignInOutcome>;
  signInWithApple: () => Promise<SignInOutcome>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [busy, setBusy] = useState(false);
  const [appleAvailable, setAppleAvailable] = useState(false);
  // Ultimo deep link ricevuto: su Android il browser può chiudersi con
  // `dismiss` anche quando l'OS ha già consegnato l'URL di ritorno.
  const lastLinkUrl = useRef<string | null>(null);

  const applyAuth = useCallback(async (res: AuthResult) => {
    await writeToken(res.session_token);
    setApiAuthToken(res.session_token);
    await adoptUserId(res.user.user_id);
    setUser(res.user);
    setStatus("authenticated");
  }, []);

  const clearAuth = useCallback(async () => {
    await writeToken(null);
    setApiAuthToken(null);
    setUser(null);
    setStatus("guest");
  }, []);

  // Scambia il session_id one-shot (una sola volta per valore) con il token.
  const exchange = useCallback(async (sessionId: string | null): Promise<boolean> => {
    if (!sessionId || usedSessionIds.has(sessionId)) return false;
    usedSessionIds.add(sessionId);
    try {
      const res = await api.authSession(sessionId);
      await applyAuth(res);
      if (isWeb) cleanWebUrl();
      return true;
    } catch (e) {
      console.warn("[PAUSE auth] session exchange failed", e);
      return false;
    }
  }, [applyAuth]);

  useEffect(() => {
    let alive = true;
    const sub = isWeb ? null : Linking.addEventListener("url", ({ url }) => {
      lastLinkUrl.current = url;
      const sid = extractSessionId(url);
      if (sid) exchange(sid);
    });
    (async () => {
      if (Platform.OS === "ios") {
        setAppleAvailable(await AppleAuthentication.isAvailableAsync().catch(() => false));
      }
      // 1) session_id nell'URL (redirect web / cold start nativo) ha la precedenza.
      const sid = extractSessionId(isWeb ? initialWebUrl : await Linking.getInitialURL().catch(() => null));
      if (sid && (await exchange(sid))) return;
      if (!alive) return;
      // 2) sessione esistente.
      const token = await readToken();
      if (!token) { setStatus("guest"); return; }
      setApiAuthToken(token);
      // Al cold boot la preview può rispondere 401 per la challenge edge prima
      // che il backend sia raggiungibile: un retry evita di buttare la sessione.
      for (let attempt = 0; attempt < 2; attempt++) {
        try {
          const me = await api.authMe();
          if (!alive) return;
          await adoptUserId(me.user_id);
          setUser(me);
          setStatus("authenticated");
          return;
        } catch (e) {
          if (!alive) return;
          const unauthorized = e instanceof ApiError && e.status === 401;
          if (unauthorized && attempt === 0) {
            await new Promise((r) => setTimeout(r, 1500));
            if (!alive) return;
            continue;
          }
          if (unauthorized) await clearAuth();
          else setStatus("guest"); // offline: si continua come ospite senza perdere il token
          return;
        }
      }
    })();
    return () => { alive = false; sub?.remove(); };
  }, [exchange, clearAuth]);

  const signInWithGoogle = useCallback(async (): Promise<SignInOutcome> => {
    const redirectUrl = isWeb ? window.location.origin + "/" : Linking.createURL("");
    const authUrl = `${AUTH_URL}?redirect=${encodeURIComponent(redirectUrl)}`;
    if (isWeb) {
      window.location.href = authUrl;
      return "redirect";
    }
    setBusy(true);
    try {
      lastLinkUrl.current = null;
      const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
      const fromResult = result.type === "success" ? result.url : null;
      const url = fromResult ?? lastLinkUrl.current ?? (await Linking.getInitialURL().catch(() => null));
      const sid = extractSessionId(url);
      if (!sid) return result.type === "cancel" || result.type === "dismiss" ? "cancelled" : "error";
      if (usedSessionIds.has(sid)) return "ok"; // già scambiato dal listener
      return (await exchange(sid)) ? "ok" : "error";
    } catch (e) {
      console.warn("[PAUSE auth] google sign-in failed", e);
      return "error";
    } finally {
      setBusy(false);
    }
  }, [exchange]);

  const signInWithApple = useCallback(async (): Promise<SignInOutcome> => {
    setBusy(true);
    try {
      const cred = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });
      if (!cred.identityToken) return "error";
      // Nome/email arrivano solo al primo accesso: vanno inviati subito.
      const name = [cred.fullName?.givenName, cred.fullName?.familyName].filter(Boolean).join(" ") || null;
      const res = await api.authApple(cred.identityToken, name, cred.email ?? null);
      await applyAuth(res);
      return "ok";
    } catch (e: any) {
      if (e?.code === "ERR_REQUEST_CANCELED" || e?.code === "ERR_CANCELED") return "cancelled";
      console.warn("[PAUSE auth] apple sign-in failed", e);
      return "error";
    } finally {
      setBusy(false);
    }
  }, [applyAuth]);

  const signOut = useCallback(async () => {
    try { await api.authLogout(); } catch {}
    await clearAuth();
    await resetUserId();
  }, [clearAuth]);

  const value = useMemo<AuthCtx>(
    () => ({ status, user, busy, appleAvailable, signInWithGoogle, signInWithApple, signOut }),
    [status, user, busy, appleAvailable, signInWithGoogle, signInWithApple, signOut],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
