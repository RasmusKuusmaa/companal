<script setup lang="ts">
/**
 * "3 / 5 this month · resets 1 Oct" - the one line a student needs to know
 * whether they're about to run out of AI feedback this month.
 *
 * Fetches its own data via the billing store so it can be dropped onto any
 * page (dashboard, pricing, the upgrade card) without the parent wiring up
 * a subscription fetch of its own. Renders nothing while loading or on
 * failure - like `ContinueLearningCard`, this is a convenience widget, not
 * something worth an error state of its own.
 *
 * The reset date falls back to the first of next calendar month when there
 * is no `currentPeriodEnd`: free tier has no Stripe period of its own (see
 * `billing.service.get_subscription_summary`), but its quota still resets
 * on the calendar month the backend actually counts against.
 */
import { computed, onMounted } from "vue";

import { useBillingStore } from "../stores/billing.store";

const store = useBillingStore();

function startOfNextMonth(): Date {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth() + 1, 1);
}

const resetLabel = computed(() => {
  const summary = store.subscription;
  const end = summary?.currentPeriodEnd ? new Date(summary.currentPeriodEnd) : startOfNextMonth();
  return end.toLocaleDateString(undefined, { day: "numeric", month: "short" });
});

onMounted(() => {
  if (!store.subscription) {
    store.fetchSubscription().catch(() => undefined);
  }
});
</script>

<template>
  <p v-if="store.subscription" class="text-xs font-medium tabular-nums text-slate-500">
    <template v-if="store.subscription.aiQuota === null">Unlimited AI feedback</template>
    <template v-else>
      {{ store.subscription.aiQuotaUsed }} / {{ store.subscription.aiQuota }} this month · resets
      {{ resetLabel }}
    </template>
  </p>
</template>
