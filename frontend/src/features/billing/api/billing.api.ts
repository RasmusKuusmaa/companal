/**
 * DTOs here mirror the backend's wire format (snake_case) on purpose, kept
 * separate from the camelCase domain types in ../types.ts - see
 * features/projects/api/projects.api.ts for the same pattern.
 */

import { httpClient } from "@/services/http";

import type { SubscriptionStatus, SubscriptionSummary, Tier } from "../types";

interface SubscriptionSummaryDto {
  tier: Tier;
  status: SubscriptionStatus;
  current_period_end: string | null;
  ai_quota: number | null;
  ai_quota_used: number;
  ai_quota_remaining: number | null;
}

function mapSubscriptionSummary(dto: SubscriptionSummaryDto): SubscriptionSummary {
  return {
    tier: dto.tier,
    status: dto.status,
    currentPeriodEnd: dto.current_period_end,
    aiQuota: dto.ai_quota,
    aiQuotaUsed: dto.ai_quota_used,
    aiQuotaRemaining: dto.ai_quota_remaining,
  };
}

export const billingApi = {
  async getSubscription(): Promise<SubscriptionSummary> {
    const { data } = await httpClient.get<SubscriptionSummaryDto>("/billing/subscription");
    return mapSubscriptionSummary(data);
  },
};
