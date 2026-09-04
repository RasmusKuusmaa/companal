export type Tier = "free" | "premium";

export type SubscriptionStatus = "active" | "canceled" | "past_due";

/** `aiQuota`/`aiQuotaRemaining` of `null` means unlimited (premium). */
export interface SubscriptionSummary {
  tier: Tier;
  status: SubscriptionStatus;
  currentPeriodEnd: string | null;
  aiQuota: number | null;
  aiQuotaUsed: number;
  aiQuotaRemaining: number | null;
}
