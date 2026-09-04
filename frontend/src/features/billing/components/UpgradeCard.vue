<script setup lang="ts">
/**
 * Replaces the AI feedback panel once quota is spent - shown instead of a
 * bare 402 from the backend, so a free user sees why AI feedback stopped
 * and exactly what fixes it, not an error toast. Never blocks anything
 * deterministic: this only ever stands in for the AI half of a page.
 */
import { BaseButton, BaseCard } from "@/shared/components/base";

withDefaults(defineProps<{ feature?: string }>(), { feature: "AI feedback" });
</script>

<template>
  <BaseCard>
    <div class="space-y-3 text-center">
      <p class="text-sm font-medium text-slate-900">You've used this month's free {{ feature }}.</p>
      <p class="text-sm text-slate-600">
        Upgrade to Premium for unlimited AI feedback - every lesson and every deterministic grade
        stays free either way.
      </p>
      <RouterLink to="/pricing">
        <BaseButton>See Premium</BaseButton>
      </RouterLink>
    </div>
  </BaseCard>
</template>
