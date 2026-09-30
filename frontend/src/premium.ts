// PAUSE — Premium tier.
//
// Premium status is driven by the backend user state (`is_premium`), read from
// the shared ["user", userId] query. Activation here is a PLACEHOLDER unlock
// (no real payment): when RevenueCat is connected, replace `activate`/`cancel`
// with the SDK's `purchase()`/entitlement and gate on `customerInfo.entitlements`.
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api, UserState } from "@/src/api";
import { useUserId } from "@/src/session";

export type PlanId = "monthly" | "yearly" | "lifetime";

export type Plan = {
  id: PlanId;
  price: string;
  period: string; // short unit shown after the price
  badge?: "save" | "best";
  trialDays?: number; // free trial length (yearly only)
};

// Prices requested by the product owner. When RevenueCat is live these come
// from Offerings → Packages → product.priceString instead of being hardcoded.
export const PLANS: Plan[] = [
  { id: "monthly", price: "€3,99", period: "/mese" },
  { id: "yearly", price: "€29,99", period: "/anno", badge: "save", trialDays: 7 },
  { id: "lifetime", price: "€49,99", period: "una volta", badge: "best" },
];
// Prezzo mensile equivalente del piano annuale (€29,99 / 12): il claim del paywall.
export const YEARLY_PER_MONTH = "€2,49";

export function usePremium() {
  const userId = useUserId();
  const qc = useQueryClient();

  const { data: user, isLoading } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => api.user(userId!),
    enabled: !!userId,
  });

  const setPremium = useMutation({
    mutationFn: (active: boolean) => api.setPremium(userId!, active),
    onSuccess: (state: UserState) => {
      qc.setQueryData(["user", userId], state);
      qc.invalidateQueries({ queryKey: ["discover-next"] });
      qc.invalidateQueries({ queryKey: ["limit", userId] });
    },
  });

  return {
    isPremium: !!user?.is_premium,
    isLoading,
    activate: () => setPremium.mutateAsync(true),
    cancel: () => setPremium.mutateAsync(false),
    isPending: setPremium.isPending,
  };
}

// Lightweight read-only flag for components that only need to know the tier
// (e.g. the audio player deciding on background playback).
export function usePremiumFlag(): boolean {
  const userId = useUserId();
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => api.user(userId!),
    enabled: !!userId,
  });
  return !!user?.is_premium;
}
