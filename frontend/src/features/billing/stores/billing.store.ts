import { defineStore } from "pinia";
import { ref } from "vue";

import { billingApi } from "../api/billing.api";
import type { SubscriptionSummary } from "../types";

export const useBillingStore = defineStore("billing", () => {
  const subscription = ref<SubscriptionSummary | null>(null);
  const isLoading = ref(false);

  async function fetchSubscription(): Promise<void> {
    isLoading.value = true;
    try {
      subscription.value = await billingApi.getSubscription();
    } finally {
      isLoading.value = false;
    }
  }

  return { subscription, isLoading, fetchSubscription };
});
