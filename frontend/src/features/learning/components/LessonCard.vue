<script setup lang="ts">
/**
 * One lesson on the roadmap.
 *
 * Every card is a link, whatever its status. Nothing on this roadmap is
 * locked - a student who wants to read about augmented sixths on day one
 * is allowed to, and the status marker exists to tell them where they've
 * been, not where they may go.
 */
import { computed } from "vue";

import type { LessonSummary } from "../types";

const props = defineProps<{
  lesson: LessonSummary;
  index: number;
}>();

const isCompleted = computed(() => props.lesson.status === "completed");
const isInProgress = computed(() => props.lesson.status === "in_progress");

const statusLabel = computed(() => {
  if (isCompleted.value) return "Completed";
  if (isInProgress.value) return "In progress";
  return "Not started";
});
</script>

<template>
  <RouterLink
    :to="`/learn/${lesson.slug}`"
    class="flex items-start gap-4 rounded-lg border p-4 transition-colors hover:border-slate-400 hover:bg-slate-50"
    :class="
      isCompleted
        ? 'border-emerald-200 bg-emerald-50/40'
        : isInProgress
          ? 'border-slate-400 bg-white'
          : 'border-slate-200 bg-white'
    "
  >
    <span
      class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold"
      :class="
        isCompleted
          ? 'border-emerald-600 bg-emerald-600 text-white'
          : isInProgress
            ? 'border-slate-900 text-slate-900'
            : 'border-slate-300 text-slate-500'
      "
      :aria-label="statusLabel"
    >
      <svg v-if="isCompleted" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path
          fill-rule="evenodd"
          d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4l2.8 2.8 6.8-6.8a1 1 0 0 1 1.4 0Z"
          clip-rule="evenodd"
        />
      </svg>
      <template v-else>{{ index + 1 }}</template>
    </span>

    <div class="min-w-0 flex-1">
      <div class="flex flex-wrap items-baseline gap-x-2">
        <h3 class="text-sm font-semibold text-slate-900">{{ lesson.title }}</h3>
        <span v-if="isInProgress" class="text-xs font-medium text-slate-500">· in progress</span>
      </div>
      <p class="mt-0.5 text-sm text-slate-600">{{ lesson.summary }}</p>
      <p class="mt-2 text-xs text-slate-500">
        {{ lesson.stepCount }} {{ lesson.stepCount === 1 ? "step" : "steps" }} ·
        {{ lesson.estimatedMinutes }} min
      </p>
    </div>
  </RouterLink>
</template>
